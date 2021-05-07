import logging
import uuid
import pathlib
import base64
from copy import copy
import graphene
from .apps import InsureeConfig
from core import filter_validity, assert_string_length
from core.schema import TinyInt, SmallInt, OpenIMISMutation
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext as _
from graphene import InputObjectType
from .models import Family, Insuree, InsureePhoto, InsureePolicy, FamilyMutation, InsureeMutation

logger = logging.getLogger(__name__)


class PhotoInputType(InputObjectType):
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    date = graphene.Date(required=False)
    officer_id = graphene.Int(required=False)
    photo = graphene.String(required=False)
    filename = graphene.String(required=False)
    folder = graphene.String(required=False)


class InsureeBase:
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    chf_id = graphene.String(max_length=12, required=False)
    last_name = graphene.String(max_length=100, required=True)
    other_names = graphene.String(max_length=100, required=True)
    gender_id = graphene.String(max_length=1, required=False)
    dob = graphene.Date(required=True)
    head = graphene.Boolean(required=False)
    marital = graphene.String(max_length=1, required=False)
    passport = graphene.String(max_length=25, required=False)
    phone = graphene.String(max_length=50, required=False)
    email = graphene.String(max_length=100, required=False)
    current_address = graphene.String(max_length=200, required=False)
    geolocation = graphene.String(max_length=250, required=False)
    current_village_id = graphene.Int(required=False)
    photo_id = graphene.Int(required=False)
    photo_date = graphene.Date(required=False)
    photo = graphene.Field(PhotoInputType, required=False)
    card_issued = graphene.Boolean(required=False)
    family_id = graphene.Int(required=False)
    relationship_id = graphene.Int(required=False)
    profession_id = graphene.Int(required=False)
    education_id = graphene.Int(required=False)
    type_of_id_id = graphene.String(max_length=1, required=False)
    health_facility_id = graphene.Int(required=False)
    offline = graphene.Boolean(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class CreateInsureeInputType(InsureeBase, OpenIMISMutation.Input):
    pass


class UpdateInsureeInputType(InsureeBase, OpenIMISMutation.Input):
    pass


class FamilyHeadInsureeInputType(InsureeBase, InputObjectType):
    pass


class FamilyBase:
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    location_id = graphene.Int(required=False)
    poverty = graphene.Boolean(required=False)
    family_type_id = graphene.String(max_length=1, required=False)
    address = graphene.String(max_length=200, required=False)
    is_offline = graphene.Boolean(required=False)
    ethnicity = graphene.String(max_length=1, required=False)
    confirmation_no = graphene.String(max_length=12, required=False)
    confirmation_type_id = graphene.String(max_length=3, required=False)
    json_ext = graphene.types.json.JSONString(required=False)

    head_insuree = graphene.Field(FamilyHeadInsureeInputType, required=False)


class FamilyInputType(FamilyBase, OpenIMISMutation.Input):
    pass


class CreateFamilyInputType(FamilyInputType):
    pass


class UpdateFamilyInputType(FamilyInputType):
    pass


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


def photo_changed(insuree_photo, data):
    return (not insuree_photo and data) or \
           (data and insuree_photo and insuree_photo.date != data.get('date', None)) or \
           (data and insuree_photo and insuree_photo.officer_id != data.get('officer_id', None)) or \
           (data and insuree_photo and insuree_photo.folder != data.get('folder', None)) or \
           (data and insuree_photo and insuree_photo.filename != data.get('filename', None)) or \
           (data and insuree_photo and insuree_photo.photo != data.get('photo', None))


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
        data.pop('photo')
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


def update_or_create_insuree(data, user):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    photo = data.pop('photo', None)
    from core import datetime
    now = datetime.datetime.now()
    data['audit_user_id'] = user.id_for_audit
    data['validity_from'] = now
    insuree_uuid = data.pop('uuid') if 'uuid' in data else None
    # update_or_create(uuid=insuree_uuid, ...)
    # doesn't work because of explicit attempt to set null to uuid!
    if insuree_uuid:
        insuree = Insuree.objects.prefetch_related("photo").get(uuid=insuree_uuid)
        insuree.save_history()
        # reset the non required fields
        # (each update is 'complete', necessary to be able to set 'null')
        reset_insuree_before_update(insuree)
        [setattr(insuree, key, data[key]) for key in data]
    else:
        insuree = Insuree.objects.create(**data)
    insuree.save()
    photo = handle_insuree_photo(user, now, insuree, photo)
    if photo:
        insuree.photo = photo
        insuree.photo_date = photo.date
        insuree.save()
    return insuree


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


def update_or_create_family(data, user):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    head_insuree_data = data.pop('head_insuree')
    head_insuree_data["head"] = True
    head_insuree = update_or_create_insuree(head_insuree_data, user)
    data["head_insuree"] = head_insuree
    family_uuid = data.pop('uuid') if 'uuid' in data else None
    # update_or_create(uuid=family_uuid, ...)
    # doesn't work because of explicit attempt to set null to uuid!
    if family_uuid:
        family = Family.objects.get(uuid=family_uuid)
        family.save_history()
        # reset the non required fields
        # (each update is 'complete', necessary to be able to set 'null')
        reset_family_before_update(family)
        [setattr(family, key, data[key]) for key in data]
    else:
        family = Family.objects.create(**data)
    family.save()
    head_insuree.family = family
    head_insuree.save()
    return family


class CreateFamilyMutation(OpenIMISMutation):
    """
    Create a new family, with its head insuree
    """
    _mutation_module = "insuree"
    _mutation_class = "CreateFamilyMutation"

    class Input(CreateFamilyInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                    _("mutation.authentication_required"))
            if not user.has_perms(InsureeConfig.gql_mutation_create_families_perms):
                raise PermissionDenied(_("unauthorized"))
            data['audit_user_id'] = user.id_for_audit
            from core.utils import TimeUtils
            data['validity_from'] = TimeUtils.now()
            client_mutation_id = data.get("client_mutation_id")
            family = update_or_create_family(data, user)
            FamilyMutation.object_mutated(user, client_mutation_id=client_mutation_id, family=family)
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_create_family"),
                'detail': str(exc)}
            ]


class UpdateFamilyMutation(OpenIMISMutation):
    """
    Update an existing family, with its head insuree
    """
    _mutation_module = "insuree"
    _mutation_class = "UpdateFamilyMutation"

    class Input(UpdateFamilyInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                    _("mutation.authentication_required"))
            if not user.has_perms(InsureeConfig.gql_mutation_update_families_perms):
                raise PermissionDenied(_("unauthorized"))
            data['audit_user_id'] = user.id_for_audit
            client_mutation_id = data.get("client_mutation_id")
            family = update_or_create_family(data, user)
            FamilyMutation.object_mutated(user, client_mutation_id=client_mutation_id, family=family)
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_create_family"),
                'detail': str(exc)}
            ]


def handle_member_on_family_delete(member, delete_members):
    if delete_members:
        member.delete_history()
    else:
        member.save_history()
        member.family = None
        member.save()


def set_family_deleted(family, delete_members):
    try:
        [handle_member_on_family_delete(member, delete_members)
         for member in family.members.filter(validity_to__isnull=True).all()]
        family.delete_history()
        return []
    except Exception as exc:
        return {
            'title': family.uuid,
            'list': [{
                'message': _("insuree.mutation.failed_to_delete_family") % {'chfid': family.chfid},
                'detail': family.uuid}]
        }


class DeleteFamiliesMutation(OpenIMISMutation):
    """
    Delete one or several families (and all its insurees).
    """
    _mutation_module = "insuree"
    _mutation_class = "DeleteFamiliesMutation"

    class Input(OpenIMISMutation.Input):
        uuids = graphene.List(graphene.String)
        delete_members = graphene.Boolean(required=False, default_value=False)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(InsureeConfig.gql_mutation_delete_families_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = []
        for family_uuid in data["uuids"]:
            family = Family.objects \
                .prefetch_related('members') \
                .filter(uuid=family_uuid) \
                .first()
            if family is None:
                errors.append({
                    'title': family_uuid,
                    'list': [{'message': _("insuree.mutation.failed_to_delete_family") % {'uuid': family_uuid}}]
                })
                continue
            errors += set_family_deleted(family, data["delete_members"])
        if len(errors) == 1:
            errors = errors[0]['list']
        return errors


class CreateInsureeMutation(OpenIMISMutation):
    """
    Create a new insuree
    """
    _mutation_module = "insuree"
    _mutation_class = "CreateInsureeMutation"

    class Input(CreateInsureeInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                    _("mutation.authentication_required"))
            if not user.has_perms(InsureeConfig.gql_mutation_create_insurees_perms):
                raise PermissionDenied(_("unauthorized"))
            data['audit_user_id'] = user.id_for_audit
            from core.utils import TimeUtils
            data['validity_from'] = TimeUtils.now()
            client_mutation_id = data.get("client_mutation_id")
            insuree = update_or_create_insuree(data, user)
            InsureeMutation.object_mutated(user, client_mutation_id=client_mutation_id, insuree=insuree)
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_create_insuree"),
                'detail': str(exc)}
            ]


class UpdateInsureeMutation(OpenIMISMutation):
    """
    Update an existing insuree
    """
    _mutation_module = "insuree"
    _mutation_class = "UpdateInsureeMutation"

    class Input(CreateInsureeInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError(
                    _("mutation.authentication_required"))
            if not user.has_perms(InsureeConfig.gql_mutation_create_insurees_perms):
                raise PermissionDenied(_("unauthorized"))
            data['audit_user_id'] = user.id_for_audit
            client_mutation_id = data.get("client_mutation_id")
            insuree = update_or_create_insuree(data, user)
            InsureeMutation.object_mutated(user, client_mutation_id=client_mutation_id, insuree=insuree)
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_update_insuree"),
                'detail': str(exc)}
            ]


def set_insuree_deleted(insuree):
    try:
        insuree.delete_history()
        [ip.delete_history() for ip in insuree.insuree_policies.filter(validity_to__isnull=True)]
        return []
    except Exception as exc:
        return {
            'title': insuree.chf_id,
            'list': [{
                'message': _("insuree.mutation.failed_to_delete_insuree") % {'chfid': insuree.chf_id},
                'detail': insuree.uuid}]
        }


class DeleteInsureesMutation(OpenIMISMutation):
    """
    Delete one or several insurees.
    """
    _mutation_module = "insuree"
    _mutation_class = "DeleteInsureesMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.String(required=False)  # family uuid, to 'lock' family while mutation is processed
        uuids = graphene.List(graphene.String)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(InsureeConfig.gql_mutation_delete_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = []
        for insuree_uuid in data["uuids"]:
            insuree = Insuree.objects \
                .prefetch_related('family') \
                .filter(uuid=insuree_uuid) \
                .first()
            if insuree is None:
                errors.append({
                    'title': insuree_uuid,
                    'list': [{'message': _(
                        "insuree.validation.id_does_not_exist") % {'id': insuree_uuid}}]
                })
                continue
            if insuree.family and insuree.family.head_insuree.id == insuree.id:
                errors.append({
                    'title': insuree_uuid,
                    'list': [{'message': _(
                        "insuree.validation.delete_head_insuree") % {'id': insuree_uuid}}]
                })
                continue
            errors += set_insuree_deleted(insuree)
        if len(errors) == 1:
            errors = errors[0]['list']
        return errors


def cancel_policies(insuree):
    try:
        from core import datetime
        now = datetime.datetime.now()
        ips = insuree.insuree_policies.filter(Q(expiry_date__isnull=True) | Q(expiry_date__gt=now))
        for ip in ips:
            ip.expiry_date = now
        InsureePolicy.objects.bulk_update(ips, ['expiry_date'])
        return []
    except Exception as exc:
        return {
            'title': insuree.chf_id,
            'list': [{
                'message': _("insuree.mutation.failed_to_cancel_insuree_policies") % {'chfid': insuree.chfid},
                'detail': insuree.uuid}]
    }


def remove_insuree(insuree):
    try:
        insuree.save_history()
        insuree.family = None
        insuree.save()
        return []
    except Exception as exc:
        return {
            'title': insuree.chf_id,
            'list': [{
                'message': _("insuree.mutation.failed_to_remove_insuree") % {'chfid': insuree.chfid},
                'detail': insuree.uuid}]
        }


class RemoveInsureesMutation(OpenIMISMutation):
    """
    Delete one or several insurees.
    """
    _mutation_module = "insuree"
    _mutation_class = "RemoveInsureesMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.String()
        uuids = graphene.List(graphene.String)
        cancel_policies = graphene.Boolean(default_value=False)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(InsureeConfig.gql_mutation_delete_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = []
        for insuree_uuid in data["uuids"]:
            insuree = Insuree.objects \
                .prefetch_related('family') \
                .filter(uuid=insuree_uuid) \
                .first()
            if insuree is None:
                errors += {
                    'title': insuree_uuid,
                    'list': [{'message': _(
                        "insuree.validation.id_does_not_exist") % {'id': insuree_uuid}}]
                }
                continue
            if insuree.family.head_insuree.id == insuree.id:
                errors.append({
                    'title': insuree_uuid,
                    'list': [{'message': _(
                        "insuree.validation.remove_head_insuree") % {'id': insuree_uuid}}]
                })
                continue
            if data['cancel_policies']:
                errors += cancel_policies(insuree)
            errors += remove_insuree(insuree)
        if len(errors) == 1:
            errors = errors[0]['list']
        return errors


class SetFamilyHeadMutation(OpenIMISMutation):
    """
    Set (change) the family head insuree
    """
    _mutation_module = "insuree"
    _mutation_class = "SetFamilyHeadMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.String()
        insuree_uuid = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(InsureeConfig.gql_mutation_update_families_perms):
            raise PermissionDenied(_("unauthorized"))
        try:
            family = Family.objects.get(uuid=data['uuid'])
            insuree = Insuree.objects.get(uuid=data['insuree_uuid'])
            family.save_history()
            prev_head = family.head_insuree
            if prev_head:
                prev_head.save_history()
                prev_head.head = False
                prev_head.save()
            family.head_insuree = insuree
            family.save()
            insuree.save_history()
            insuree.head = True
            insuree.save()
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_set_head_insuree"),
                'detail': str(exc)}
            ]


class ChangeInsureeFamilyMutation(OpenIMISMutation):
    """
    Set (change) the family of an insuree
    """
    _mutation_module = "insuree"
    _mutation_class = "ChangeInsureeFamilyMutation"

    class Input(OpenIMISMutation.Input):
        family_uuid = graphene.String()
        insuree_uuid = graphene.String()
        cancel_policies = graphene.Boolean(default_value=False)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(InsureeConfig.gql_mutation_update_families_perms) or \
                not user.has_perms(InsureeConfig.gql_mutation_update_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        try:
            family = Family.objects.get(uuid=data['family_uuid'])
            insuree = Insuree.objects.get(uuid=data['insuree_uuid'])
            insuree.save_history()
            insuree.family = family
            insuree.save()
            if data['cancel_policies']:
                return cancel_policies(insuree)
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_change_insuree_family"),
                'detail': str(exc)}
            ]
