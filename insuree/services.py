import base64
import logging
import pathlib
import uuid

from core.apps import CoreConfig
from django.db.models import Q
from django.utils.translation import gettext as _

from core.signals import register_service_signal
from insuree.apps import InsureeConfig
from insuree.models import InsureePhoto, PolicyRenewalDetail, Insuree, Family, InsureePolicy

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


def validate_insuree_number(insuree_number):
    if InsureeConfig.get_insuree_number_validator():
        return InsureeConfig.get_insuree_number_validator()(insuree_number)
    if InsureeConfig.get_insuree_number_length():
        if not insuree_number:
            return [
                {
                    "message": "Invalid insuree number (empty), should be %s" %
                               (InsureeConfig.get_insuree_number_length(),)
                }
            ]
        if len(insuree_number) != InsureeConfig.get_insuree_number_length():
            return [
                {
                    "message": "Invalid insuree number length %s, should be %s" %
                               (len(insuree_number), InsureeConfig.get_insuree_number_length())
                }
            ]
    if InsureeConfig.get_insuree_number_modulo_root():
        try:
            base = int(insuree_number[:-1])
            mod = int(insuree_number[-1])
            if base % InsureeConfig.get_insuree_number_modulo_root() != mod:
                return [{"message": "Invalid checksum"}]
        except Exception as exc:
            logger.exception("Failed insuree number validation", exc)
            return [{"message": "Insuree number validation failed"}]
    return []


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
    if photo_bin and InsureeConfig.insuree_photos_root_path and photo_bin != insuree_photo.photo:
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


def photo_changed(insuree_photo, data):
    return (not insuree_photo and data) or \
           (data and insuree_photo and insuree_photo.date != data.get('date', None)) or \
           (data and insuree_photo and insuree_photo.officer_id != data.get('officer_id', None)) or \
           (data and insuree_photo and insuree_photo.folder != data.get('folder', None)) or \
           (data and insuree_photo and insuree_photo.filename != data.get('filename', None)) or \
           (data and insuree_photo and insuree_photo.photo != data.get('photo', None))


def create_file(date, insuree_id, photo_bin):
    date_iso = date.isoformat()
    root = InsureeConfig.insuree_photos_root_path
    file_dir = '%s/%s/%s/%s' % (
        date_iso[0:4],
        date_iso[5:7],
        date_iso[8:10],
        insuree_id
    )
    file_name = uuid.uuid4()
    file_path = '%s/%s' % (file_dir, file_name)
    pathlib.Path('%s/%s' % (root, file_dir)).mkdir(parents=True, exist_ok=True)
    f = open('%s/%s' % (root, file_path), "xb")
    f.write(base64.b64decode(photo_bin))
    f.close()
    return file_dir, file_name


class InsureeService:
    def __init__(self, user):
        self.user = user

    @register_service_signal('insuree_service.create_or_update')
    def create_or_update(self, data):
        photo = data.pop('photo', None)
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
            errors = validate_insuree_number(data["chf_id"])
            if errors:
                raise Exception("Invalid insuree number")
            else:
                insuree = Insuree.objects.create(**data)
        insuree.save()
        photo = handle_insuree_photo(self.user, now, insuree, photo)
        if photo:
            insuree.photo = photo
            insuree.photo_date = photo.date
            insuree.save()
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
