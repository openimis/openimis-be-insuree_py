import logging
import uuid
import pathlib
import base64
from copy import copy
import graphene
from .apps import InsureeConfig
from claim.validations import validate_claim, get_claim_category, validate_assign_prod_to_claimitems_and_services, \
    process_dedrem, approved_amount
from core import filter_validity, assert_string_length
from core.schema import TinyInt, SmallInt, OpenIMISMutation
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import CharField
from django.db.models.functions import Cast
from django.utils.translation import gettext as _
from graphene import InputObjectType
from location.schema import UserDistrict
from .models import Family, Insuree
from product.models import ProductItemOrService

logger = logging.getLogger(__name__)


class InsureeInputType(InputObjectType):
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    chf_id = graphene.String(max_length=12, required=False)
    last_name = graphene.String(max_length=100, required=True)
    other_names = graphene.String(max_length=100, required=True)
    gender_code = graphene.String(max_length=1, required=False)
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
    card_issued = graphene.Boolean(required=False)
    relationship_id = graphene.Int(required=False)
    profession_id = graphene.Int(required=False)
    education_id = graphene.Int(required=False)
    type_of_id_code = graphene.String(max_length=1, required=False)
    health_facility_id = graphene.Int(required=False)
    offline = graphene.Boolean(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class FamilyInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    location_id = graphene.Int(required=False)
    poverty = graphene.Boolean(required=False)
    family_type_id = graphene.Int(required=False)
    address = graphene.String(max_length=200, required=False)
    is_offline = graphene.Boolean(required=False)
    ethnicity = graphene.String(max_length=1, required=False)
    confirmation_no = graphene.String(max_length=12, required=False)
    confirmation_type_id = graphene.Int(required=False)
    json_ext = graphene.types.json.JSONString(required=False)

    head_insuree = graphene.Field(InsureeInputType, required=False)


class CreateFamilyInputType(FamilyInputType):
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
    insuree.photo = None
    insuree.photo_date = None
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


def update_or_create_insuree(data, user):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    data['audit_user_id'] = user.id_for_audit
    insuree_uuid = data.pop('uuid') if 'uuid' in data else None
    # update_or_create(uuid=insuree_uuid, ...)
    # doesn't work because of explicit attempt to set null to uuid!
    if insuree_uuid:
        insuree = Insuree.objects.get(uuid=insuree_uuid)
        insuree.save_history()
        # reset the non required fields
        # (each update is 'complete', necessary to be able to set 'null')
        reset_insuree_before_update(insuree)
        [setattr(insuree, key, data[key]) for key in data]
    else:
        insuree = Insuree.objects.create(**data)
    insuree.save()
    return insuree


def update_or_create_family(data, user):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    head_insuree = update_or_create_insuree(data.pop('head_insuree'), user)
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
            update_or_create_family(data, user)
            return None
        except Exception as exc:
            return [{
                'message': _("insuree.mutation.failed_to_create_family"),
                'detail': str(exc)}]