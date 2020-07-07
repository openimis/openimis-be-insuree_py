import graphene
from graphene_django import DjangoObjectType
from .models import Insuree, Photo, Gender, Family, FamilyType
from location.schema import LocationGQLType
from core import prefix_filterset, filter_validity, ExtendedConnection

class GenderGQLType(DjangoObjectType):
    class Meta:
        model = Gender
        filter_fields = {
            "code": ["exact"]
        }

class PhotoGQLType(DjangoObjectType):
    class Meta:
        model = Photo


class FamilyTypeGQLType(DjangoObjectType):
    class Meta:
        model = FamilyType


class InsureeGQLType(DjangoObjectType):
    age = graphene.Int(source='age')

    class Meta:
        model = Insuree
        filter_fields = {
            "chf_id": ["exact", "istartswith"],
            "last_name": ["exact", "istartswith", "icontains", "iexact"],
            "other_names": ["exact", "istartswith", "icontains", "iexact"],
            **prefix_filterset("gender__", GenderGQLType._meta.filter_fields)
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return Insuree.filter_queryset(queryset)


class FamilyGQLType(DjangoObjectType):
    class Meta:
        model = Family
        filter_fields = {
            **prefix_filterset("location__", LocationGQLType._meta.filter_fields),
            **prefix_filterset("head_insuree__", InsureeGQLType._meta.filter_fields)
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return Family.filter_queryset(queryset)