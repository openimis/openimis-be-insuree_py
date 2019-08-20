import re
from django.db.models import Q
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Insuree, Photo, Gender, Family, FamilyType
from core import filter_validity, ExtendedConnection


class GenderGQLType(DjangoObjectType):
    class Meta:
        model = Gender


class PhotoGQLType(DjangoObjectType):
    class Meta:
        model = Photo


class FamilyTypeGQLType(DjangoObjectType):
    class Meta:
        model = FamilyType


class FamilyGQLType(DjangoObjectType):
    class Meta:
        model = Family


class InsureeGQLType(DjangoObjectType):
    age = graphene.Int(source='age')

    class Meta:
        model = Insuree
        filter_fields = {
            "chf_id": ["exact", "istartswith"],
            "last_name": ["exact", "istartswith", "icontains", "iexact"],
            "other_names": ["exact", "istartswith", "icontains", "iexact"],
            "gender": ["exact"]
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection


class Query(graphene.ObjectType):
    insurees = DjangoFilterConnectionField(InsureeGQLType)
    insuree = graphene.relay.node.Field(
        InsureeGQLType,
        chfId=graphene.String(required=True),
        validity=graphene.Date()
    )
    insuree_family_members = graphene.List(
        InsureeGQLType,
        chfId=graphene.String(required=True),
        validity=graphene.Date()
    )

    @staticmethod
    def _resolve_insuree(info, **kwargs):
        return Insuree.objects.get(
            Q(chf_id=kwargs.get('chfId')),
            *filter_validity(**kwargs)
        )

    def resolve_insuree(self, info, **kwargs):
        try:
            return Query._resolve_insuree(info=info, **kwargs)
        except Insuree.DoesNotExist:
            return None

    def resolve_insuree_family_members(self, info, **kwargs):
        insuree = Query._resolve_insuree(info=info, **kwargs)
        return Insuree.objects.filter(
            Q(family=insuree.family),
            *filter_validity(**kwargs)
        ).order_by('-head')
