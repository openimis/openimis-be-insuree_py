import graphene
from graphene_django import DjangoObjectType
from .models import Insuree, InsureePhoto, Education, Profession, Gender, IdentificationType, \
    Family, FamilyType, ConfirmationType, Relation, InsureePolicy, FamilyMutation, InsureeMutation
from location.schema import LocationGQLType
from policy.gql_queries import PolicyGQLType
from core import prefix_filterset, filter_validity, ExtendedConnection


class GenderGQLType(DjangoObjectType):
    class Meta:
        model = Gender
        filter_fields = {
            "code": ["exact"]
        }


class PhotoGQLType(DjangoObjectType):
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

class InsureeGQLType(DjangoObjectType):
    age = graphene.Int(source='age')
    client_mutation_id = graphene.String()

    class Meta:
        model = Insuree
        filter_fields = {
            "uuid": ["exact"],
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
            "validity_from": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "validity_to": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            **prefix_filterset("photo__", PhotoGQLType._meta.filter_fields),
            "photo": ["isnull"],
            **prefix_filterset("gender__", GenderGQLType._meta.filter_fields)
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    def resolve_client_mutation_id(self, info):
        insuree_mutation = self.mutations.select_related(
            'mutation').filter(mutation__status=0).first()
        return insuree_mutation.mutation.client_mutation_id if insuree_mutation else None

    @classmethod
    def get_queryset(cls, queryset, info):
        return Insuree.get_queryset(queryset, info)


class FamilyGQLType(DjangoObjectType):
    client_mutation_id = graphene.String()

    class Meta:
        model = Family
        filter_fields = {
            "uuid": ["exact"],
            "poverty": ["exact", "isnull"],
            "confirmation_no": ["exact", "istartswith", "icontains", "iexact"],
            "confirmation_type": ["exact"],
            "family_type": ["exact"],
            "address": ["exact", "istartswith", "icontains", "iexact"],
            "ethnicity": ["exact"],
            "is_offline": ["exact"],
            **prefix_filterset("location__", LocationGQLType._meta.filter_fields),
            **prefix_filterset("head_insuree__", InsureeGQLType._meta.filter_fields),
            ** prefix_filterset("members__", InsureeGQLType._meta.filter_fields)
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    def resolve_client_mutation_id(self, info):
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


class FamilyMutationGQLType(DjangoObjectType):
    class Meta:
        model = FamilyMutation


class InsureeMutationGQLType(DjangoObjectType):
    class Meta:
        model = InsureeMutation
