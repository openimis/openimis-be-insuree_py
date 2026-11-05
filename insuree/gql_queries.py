import graphene
from graphene_django import DjangoObjectType

from .apps import InsureeConfig
from .models import Insuree, InsureePhoto, Education, Profession, Gender, IdentificationType, \
    Family, FamilyType, ConfirmationType, Relation, InsureePolicy, FamilyMutation, InsureeMutation, InsureeStatusReason
from location.schema import LocationGQLType
from policy.gql_queries import PolicyGQLType
from core import prefix_filterset, ExtendedConnection
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied

from .services import load_photo_file
from core.gql import ScopedQuerysetMixin


class GenderGQLType(DjangoObjectType):
    class Meta:
        model = Gender
        filter_fields = {
            "code": ["exact"]
        }


def may_read_insuree_fields(user):
    """Whether `user` may see the fields an insuree lookup displays.

    The register right (101101) is one way in. The enquiry right (101105) is the
    other: the CHFID picker and the enquiry dialog project the photo, the family, the
    first point of service and the current village, so a right that resolves an
    identifier and then cannot show anything about it would authorise nothing usable.
    What 101105 does *not* reach is the family's own fields (101001) or anything
    behind a mutation right - those are other grants, and they stay where they are.
    """
    return user.has_perms(InsureeConfig.gql_query_insuree_perms) or user.has_perms(
        InsureeConfig.gql_query_insuree_inquire_perms
    )


class PhotoGQLType(ScopedQuerysetMixin, DjangoObjectType):
    photo = graphene.String()

    def resolve_photo(self, info):
        if not info.context.user.has_perms(
            InsureeConfig.gql_query_insuree_photo_perms
        ) and not info.context.user.has_perms(
            InsureeConfig.gql_query_insuree_inquire_perms
        ):
            raise PermissionDenied(_("unauthorized"))
        if self.photo:
            return self.photo
        elif InsureeConfig.insuree_photos_root_path and self.folder and self.filename:
            return load_photo_file(self.folder, self.filename)
        return None

    class Meta:
        model = InsureePhoto
        filter_fields = {
            "id": ["exact"]
        }


class IdentificationTypeGQLType(DjangoObjectType):
    class Meta:
        model = IdentificationType
        filter_fields = {
            "code": ["exact"]
        }


class EducationGQLType(DjangoObjectType):
    class Meta:
        model = Education
        filter_fields = {
            "id": ["exact"]
        }

        exclude_fields = ('insurees',)


class ProfessionGQLType(DjangoObjectType):
    class Meta:
        model = Profession
        filter_fields = {
            "id": ["exact"]
        }


class FamilyTypeGQLType(DjangoObjectType):
    class Meta:
        model = FamilyType
        filter_fields = {
            "code": ["exact"]
        }


class ConfirmationTypeGQLType(DjangoObjectType):
    class Meta:
        model = ConfirmationType
        filter_fields = {
            "code": ["exact"]
        }


class RelationGQLType(DjangoObjectType):
    class Meta:
        model = Relation
        filter_fields = {
            "code": ["exact"]
        }


class InsureeStatusReasonGQLType(DjangoObjectType):
    status_type = graphene.String(required=False)

    class Meta:
        model = InsureeStatusReason
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "code": ["exact"],
            "insuree_status_reason": ["exact", 'icontains', 'istartswith'],
            "status_type": ["exact"]
        }
        connection_class = ExtendedConnection


class InsureeGQLType(DjangoObjectType):
    age = graphene.Int(source='age')
    client_mutation_id = graphene.String()
    photo = PhotoGQLType()

    def resolve_current_village(self, info):
        if not may_read_insuree_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        if "location_loader" in info.context.dataloaders and self.current_village_id:
            return info.context.dataloaders["location_loader"].load(
                self.current_village_id
            )
        return self.current_village

    def resolve_family(self, info):
        if not may_read_insuree_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        if "family_loader" in info.context.dataloaders and self.family_id:
            return info.context.dataloaders["family_loader"].load(self.family_id)
        return self.family

    def resolve_health_facility(self, info):
        if not may_read_insuree_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        if "health_facililty" in info.context.dataloaders and self.health_facility_id:
            return info.context.dataloaders["health_facility"].load(
                self.health_facility_id
            )
        return self.health_facility

    def resolve_photo(self, info):
        if not may_read_insuree_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        return self.photo

    class Meta:
        model = Insuree
        filter_fields = {
            "uuid": ["exact", "iexact"],
            "chf_id": ["exact", "istartswith", "icontains", "iexact"],
            "last_name": ["exact", "istartswith", "icontains", "iexact"],
            "other_names": ["exact", "istartswith", "icontains", "iexact"],
            "email": ["exact", "istartswith", "icontains", "iexact", "isnull"],
            "phone": ["exact", "istartswith", "icontains", "iexact", "isnull"],
            "dob": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "head": ["exact"],
            "passport": ["exact", "istartswith", "icontains", "iexact", "isnull"],
            "gender__code": ["exact", "isnull"],
            "marital": ["exact", "isnull"],
            "status": ["exact"],
            "validity_from": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "validity_to": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            **prefix_filterset("photo__", PhotoGQLType._meta.filter_fields),
            "photo": ["isnull"],
            "family": ["isnull"],
            **prefix_filterset("gender__", GenderGQLType._meta.filter_fields)
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    def resolve_client_mutation_id(self, info):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insuree_perms):
            raise PermissionDenied(_("unauthorized"))
        insuree_mutation = self.mutations.select_related(
            'mutation').filter(mutation__status=0).first()
        return insuree_mutation.mutation.client_mutation_id if insuree_mutation else None

    @classmethod
    def get_queryset(cls, queryset, info):
        return Insuree.get_queryset(queryset, info)


def may_read_family_fields(user):
    """Whether `user` may see the family fields an insuree lookup displays.

    The family register right (101001) is one way in; the enquiry right is the other.
    The picker projects the whole family - `fetchInsuree` sends
    `family{...FAMILY_FULL_PROJECTION}` - so without this an enquiry resolves the
    insuree and then fails field by field on their family. What this does *not* open
    is the `families` query or the Families page: both stay on 101001, which is the
    right the front-end route is guarded by.
    """
    return user.has_perms(InsureeConfig.gql_query_families_perms) or user.has_perms(
        InsureeConfig.gql_query_insuree_inquire_perms
    )


class FamilyGQLType(DjangoObjectType):
    client_mutation_id = graphene.String()

    def resolve_location(self, info):
        if not may_read_family_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        if "location_loader" in info.context.dataloaders:
            return info.context.dataloaders["location_loader"].load(self.location_id)

    def resolve_head_insuree(self, info):
        if not may_read_family_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        if "insuree_loader" in info.context.dataloaders:
            return info.context.dataloaders["insuree_loader"].load(self.head_insuree_id)

    class Meta:
        model = Family
        filter_fields = {
            "uuid": ["exact", "iexact"],
            "poverty": ["exact", "isnull"],
            "confirmation_no": ["exact", "istartswith", "icontains", "iexact"],
            "confirmation_type": ["exact"],
            "family_type": ["exact"],
            "address": ["exact", "istartswith", "icontains", "iexact"],
            "ethnicity": ["exact"],
            "is_offline": ["exact"],
            "parent__id": ["exact"],
            "parent__uuid": ["exact"],
            **prefix_filterset("location__", LocationGQLType._meta.filter_fields),
            **prefix_filterset("head_insuree__", InsureeGQLType._meta.filter_fields),
            **prefix_filterset("members__", InsureeGQLType._meta.filter_fields)
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    def resolve_client_mutation_id(self, info):
        if not may_read_family_fields(info.context.user):
            raise PermissionDenied(_("unauthorized"))
        family_mutation = self.mutations.select_related(
            'mutation').filter(mutation__status=0).first()
        return family_mutation.mutation.client_mutation_id if family_mutation else None

    @classmethod
    def get_queryset(cls, queryset, info):
        return Family.get_queryset(queryset, info)


class InsureePolicyGQLType(DjangoObjectType):
    class Meta:
        model = InsureePolicy
        filter_fields = {
            "enrollment_date": ["exact", "lt", "lte", "gt", "gte"],
            "start_date": ["exact", "lt", "lte", "gt", "gte"],
            "effective_date": ["exact", "lt", "lte", "gt", "gte"],
            "expiry_date": ["exact", "lt", "lte", "gt", "gte"],
            **prefix_filterset("insuree__", InsureeGQLType._meta.filter_fields),
            **prefix_filterset("policy__", PolicyGQLType._meta.filter_fields),
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return InsureePolicy.get_queryset(queryset, info)


class FamilyMutationGQLType(ScopedQuerysetMixin, DjangoObjectType):
    class Meta:
        model = FamilyMutation


class InsureeMutationGQLType(ScopedQuerysetMixin, DjangoObjectType):
    class Meta:
        model = InsureeMutation
