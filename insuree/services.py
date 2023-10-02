import base64
import logging
import pathlib
import shutil
import uuid
from os import path
import random
from core.apps import CoreConfig
from location.models import Location
from django.db.models import Q
from django.utils.translation import gettext as _

from core.signals import register_service_signal
from insuree.apps import InsureeConfig
from insuree.models import InsureePhoto, InsureeAttachment, PolicyRenewalDetail, Insuree, Family, InsureePolicy

logger = logging.getLogger(__name__)


def create_insuree_renewal_detail(policy_renewal):
    from core import datetime, datetimedelta
    now = datetime.datetime.now()
    adult_birth_date = now - datetimedelta(years=CoreConfig.age_of_majority)
    photo_renewal_date_adult = now - datetimedelta(months=InsureeConfig.renewal_photo_age_adult)  # 60
    photo_renewal_date_child = now - datetimedelta(months=InsureeConfig.renewal_photo_age_child)  # 12
    photos_to_renew = InsureePhoto.objects.filter(insuree__family=policy_renewal.insuree.family) \
        .filter(insuree__validity_to__isnull=True) \
        .filter(Q(insuree__photo_date__isnull=True)
                | Q(insuree__photo_date__lte=photo_renewal_date_adult)
                | (Q(insuree__photo_date__lte=photo_renewal_date_child)
                   & Q(insuree__dob__gt=adult_birth_date)
                   )
                )
    for photo in photos_to_renew:
        detail, detail_created = PolicyRenewalDetail.objects.get_or_create(
            policy_renewal=policy_renewal,
            insuree_id=photo.insuree_id,
            validity_from=now,
            audit_user_id=0,
        )
        logger.debug("Photo due for renewal for insuree %s, renewal detail %s, created an entry ? %s",
                     photo.insuree_id, detail.id, detail_created)


def validate_insuree_number(insuree_number, uuid=None):
    query = Insuree.objects.filter(chf_id=insuree_number, validity_to__isnull=True)
    insuree = query.first()
    if insuree and insuree.uuid != uuid:
        return [{"errorCode": InsureeConfig.validation_code_taken_insuree_number,
                 "message": "Insuree number has to be unique, %s exists in system" % insuree_number}]

    if InsureeConfig.get_insuree_number_validator():
        return InsureeConfig.get_insuree_number_validator()(insuree_number)
    if InsureeConfig.get_insuree_number_length():
        if not insuree_number:
            return [
                {
                    "errorCode": InsureeConfig.validation_code_no_insuree_number,
                    "message": "Invalid insuree number (empty), should be %s" %
                               (InsureeConfig.get_insuree_number_length(),)
                }
            ]
        if len(insuree_number) != InsureeConfig.get_insuree_number_length():
            return [
                {
                    "errorCode": InsureeConfig.validation_code_invalid_insuree_number_len,
                    "message": "Invalid insuree number length %s, should be %s" %
                               (len(insuree_number), InsureeConfig.get_insuree_number_length())
                }
            ]
    config_modulo = InsureeConfig.get_insuree_number_modulo_root()
    if config_modulo:
        try:
            if config_modulo == 10:
                if not is_modulo_10_number_valid(insuree_number):
                    return invalid_checksum()
            else:
                base = int(insuree_number[:-1])
                mod = int(insuree_number[-1])
                if base % config_modulo != mod:
                    return invalid_checksum()
        except Exception as exc:
            logger.exception("Failed insuree number validation", exc)
            return [{"errorCode": InsureeConfig.validation_code_invalid_insuree_number_exception,
                     "message": "Insuree number validation failed"}]
    return []


def is_modulo_10_number_valid(insuree_number: str) -> bool:
    """
    This function checks whether an insuree number is valid, according to the modulo 10 technique.
    Contrarily to its name, this technique does not simply check if number % 10 == 0.
    This function uses Luhn's algorithm (https://en.wikipedia.org/wiki/Luhn_algorithm).
    """
    return (sum(
        (element + (index % 2 == 0) * (element - 9 * (element > 4))
         for index, element in enumerate(map(int, insuree_number[:-1])))
    ) + int(insuree_number[-1])) % 10 == 0


def invalid_checksum():
    return [{"errorCode": InsureeConfig.validation_code_invalid_insuree_number_checksum,
             "message": "Invalid checksum"}]


def reset_insuree_before_update(insuree):
    insuree.family = None
    insuree.chf_id = None
    insuree.last_name = None
    insuree.other_names = None
    insuree.gender = None
    insuree.dob = None
    insuree.head = None
    insuree.marital = None
    insuree.passport = None
    insuree.phone = None
    insuree.email = None
    insuree.current_address = None
    insuree.geolocation = None
    insuree.current_village = None
    insuree.card_issued = None
    insuree.relationship = None
    insuree.profession = None
    insuree.education = None
    insuree.type_of_id = None
    insuree.health_facility = None
    insuree.offline = None
    insuree.json_ext = None


def reset_family_before_update(family):
    family.location = None
    family.poverty = None
    family.family_type = None
    family.address = None
    family.is_offline = None
    family.ethnicity = None
    family.confirmation_no = None
    family.confirmation_type = None
    family.json_ext = None


def handle_insuree_photo(user, now, insuree, data):
    insuree_photo = insuree.photo
    if not photo_changed(insuree_photo, data):
        return None
    data['audit_user_id'] = user.id_for_audit
    data['validity_from'] = now
    data['insuree_id'] = insuree.id
    photo_bin = data.get('photo', None)
    if photo_bin and InsureeConfig.insuree_photos_root_path \
            and (insuree_photo is None or insuree_photo.photo != photo_bin):
        (file_dir, file_name) = create_file(now, insuree.id, photo_bin)
        data.pop('photo', None)
        data['folder'] = file_dir
        data['filename'] = file_name

    if insuree_photo:
        insuree_photo.save_history()
        insuree_photo.date = None
        insuree_photo.officer_id = None
        insuree_photo.folder = None
        insuree_photo.filename = None
        insuree_photo.photo = None
        [setattr(insuree_photo, key, data[key]) for key in data if key != 'id']
    else:
        insuree_photo = InsureePhoto.objects.create(**data)
    insuree_photo.save()
    return insuree_photo

def handle_insuree_attachments(user, now, insuree, data):
    data['insuree_id'] = insuree.id
    document_bin = data.get('document', None)
    if document_bin and InsureeConfig.insuree_photos_root_path:
        (file_dir, file_name) = create_file(now, insuree.id, document_bin)
        data['folder'] = file_dir
        data['filename'] = file_name
    insuree_attachment = InsureeAttachment.objects.create(**data)
    insuree_attachment.save()
    return insuree_attachment

def photo_changed(insuree_photo, data):
    return (not insuree_photo and data) or \
        (data and insuree_photo and insuree_photo.date != data.get('date', None)) or \
        (data and insuree_photo and insuree_photo.officer_id != data.get('officer_id', None)) or \
        (data and insuree_photo and insuree_photo.folder != data.get('folder', None)) or \
        (data and insuree_photo and insuree_photo.filename != data.get('filename', None)) or \
        (data and insuree_photo and insuree_photo.photo != data.get('photo', None))


def _photo_dir(file_dir, file_name):
    root = InsureeConfig.insuree_photos_root_path
    return path.join(root, file_dir, file_name)


def _create_dir(file_dir):
    root = InsureeConfig.insuree_photos_root_path
    pathlib.Path(path.join(root, file_dir)) \
        .mkdir(parents=True, exist_ok=True)


def create_file(date, insuree_id, photo_bin):
    file_dir = path.join(str(date.year), str(date.month), str(date.day), str(insuree_id))
    file_name = str(uuid.uuid4())

    _create_dir(file_dir)
    with open(_photo_dir(file_dir, file_name), "xb") as f:
        f.write(base64.b64decode(photo_bin))
        f.close()
    return file_dir, file_name


def copy_file(date, insuree_id, original_file):
    file_dir = path.join(str(date.year), str(date.month), str(date.day), str(insuree_id))
    file_name = str(uuid.uuid4())

    _create_dir(file_dir)
    shutil.copy2(original_file, _photo_dir(file_dir, file_name))
    return file_dir, file_name


def load_photo_file(file_dir, file_name):
    photo_path = _photo_dir(file_dir, file_name)
    with open(photo_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class InsureeService:
    def __init__(self, user):
        self.user = user

    def normalize_code(self, code, maxi=2):
        if len(code) <= 0:
            code = '00' if maxi == 2 else '000'
        if len(code) == 1:
            code = '0'+str(code) if maxi == 2 else '00'+str(code)
        if len(code) > maxi:
            code = code[:maxi]
        return code
    
    @register_service_signal('insuree_service.create_or_update')
    def create_or_update(self, data):
        photo = data.pop('photo', None)
        attachments = data.pop('attachments', [])
        from core import datetime
        now = datetime.datetime.now()
        data['audit_user_id'] = self.user.id_for_audit
        data['validity_from'] = now
        insuree_uuid = data.pop('uuid', None)
        if insuree_uuid:
            insuree = Insuree.objects.prefetch_related("photo").get(uuid=insuree_uuid)
            insuree.save_history()
            # reset the non required fields
            # (each update is 'complete', necessary to be able to set 'null')
            reset_insuree_before_update(insuree)
            [setattr(insuree, key, data[key]) for key in data]
        else:
            location_id = data.pop('location_id', False)
            gender = data.get('gender_id', False)
            family_id = data.get('family_id', False)
            # This function is designed to generate a random insuree ID with 5 characters, ranging from 1 to 99999. 
            # It returns a string of 9 characters for the insuree ID.
            min_num = 1
            max_num = 9999999999999
            val = 13
            first_part = ""
            if location_id or family_id:
                max_num = 99999
                val = 5
                if family_id:
                    family = Family.objects.get(id=family_id)
                    location = Location.objects.get(id=family.location_id)
                else:
                    location = Location.objects.get(id=location_id)
                municipality = location.parent.code
                district = location.parent.parent.code
                region = location.parent.parent.parent.code

                region = self.normalize_code(region)
                district = self.normalize_code(district)
                municipality = self.normalize_code(municipality, maxi=3)
                
                print("region ", region)
                print("district ", district)
                print("municipality ", municipality)
                gender_code = '1'
                if gender == 'F':
                    gender_code = '2'
                first_part = region + district + municipality + gender_code

            formatted_num = 0
            # We try if the insuree number and generate a new id till a unique insureeId is generated
            while formatted_num==0 or Insuree.objects.filter(chf_id=formatted_num).exists():
                random_num = random.randint(min_num, max_num)
                formatted_num = str(random_num).zfill(val)
                data["chf_id"] = first_part + formatted_num
            print(data["chf_id"])
            errors = validate_insuree_number(data["chf_id"], insuree_uuid)
            if errors:
                raise Exception("Invalid insuree number")
            insuree = Insuree.objects.create(**data)
        insuree.save()
        photo = handle_insuree_photo(self.user, now, insuree, photo)
        if photo:
            insuree.photo = photo
            insuree.photo_date = photo.date
            insuree.save()
        InsureeAttachment.objects.filter(
            insuree_id=insuree.id
        ).delete()
        for attachment in attachments:
            handle_insuree_attachments(
                self.user, now, insuree, attachment
            )
        return insuree

    def remove(self, insuree):
        try:
            insuree.save_history()
            insuree.family = None
            insuree.save()
            return []
        except Exception as exc:
            logger.exception("insuree.mutation.failed_to_remove_insuree")
            return {
                'title': insuree.chf_id,
                'list': [{
                    'message': _("insuree.mutation.failed_to_remove_insuree") % {'chfid': insuree.chfid},
                    'detail': insuree.uuid}]
            }

    @register_service_signal('insuree_service.delete')
    def set_deleted(self, insuree):
        try:
            insuree.delete_history()
            [ip.delete_history() for ip in insuree.insuree_policies.filter(validity_to__isnull=True)]
            return []
        except Exception as exc:
            logger.exception("insuree.mutation.failed_to_delete_insuree")
            return {
                'title': insuree.chf_id,
                'list': [{
                    'message': _("insuree.mutation.failed_to_delete_insuree") % {'chfid': insuree.chf_id},
                    'detail': insuree.uuid}]
            }

    def cancel_policies(self, insuree):
        try:
            from core import datetime
            now = datetime.datetime.now()
            ips = insuree.insuree_policies.filter(Q(expiry_date__isnull=True) | Q(expiry_date__gt=now))
            for ip in ips:
                ip.expiry_date = now
            InsureePolicy.objects.bulk_update(ips, ['expiry_date'])
            return []
        except Exception as exc:
            logger.exception("insuree.mutation.failed_to_cancel_insuree_policies")
            return {
                'title': insuree.chf_id,
                'list': [{
                    'message': _("insuree.mutation.failed_to_cancel_insuree_policies") % {'chfid': insuree.chfid},
                    'detail': insuree.uuid}]
            }


class FamilyService:
    def __init__(self, user):
        self.user = user

    def create_or_update(self, data):
        head_insuree_data = data.pop('head_insuree')
        head_insuree_data["head"] = True
        head_insuree_data["location_id"] = data.get('location_id', None)
        head_insuree = InsureeService(self.user).create_or_update(head_insuree_data)
        data["head_insuree"] = head_insuree
        family_uuid = data.pop('uuid', None)
        if family_uuid:
            family = Family.objects.get(uuid=family_uuid)
            family.save_history()
            # reset the non required fields
            # (each update is 'complete', necessary to be able to set 'null')
            reset_family_before_update(family)
            [setattr(family, key, data[key]) for key in data]
        else:
            data.pop('contribution', None)
            family = Family.objects.create(**data)
        family.save()
        head_insuree.family = family
        head_insuree.save()
        return family

    def set_deleted(self, family, delete_members):
        try:
            [self.handle_member_on_family_delete(member, delete_members)
             for member in family.members.filter(validity_to__isnull=True).all()]
            family.delete_history()
            return []
        except Exception as exc:
            logger.exception("insuree.mutation.failed_to_delete_family")
            return {
                'title': family.uuid,
                'list': [{
                    'message': _("insuree.mutation.failed_to_delete_family") % {'chfid': family.chfid},
                    'detail': family.uuid}]
            }

    def handle_member_on_family_delete(self, member, delete_members):
        insuree_service = InsureeService(self.user)
        if delete_members:
            insuree_service.set_deleted(member)
        else:
            insuree_service.remove(member)
