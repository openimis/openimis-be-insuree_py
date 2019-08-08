import re
from django.db.models import Q
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Insuree, Photo, Gender, Family, FamilyType
import core


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
            "id": ["exact"],
            "last_name": ["exact", "istartswith", "icontains", "iexact"],
            "other_names": ["exact", "istartswith", "icontains", "iexact"],
        }
        interfaces = (graphene.relay.Node,)


class Query(graphene.ObjectType):
    insuree = graphene.relay.node.Field(
        InsureeGQLType,
        chfId=graphene.String(required=True),
        validity=graphene.String()
    )
    insuree_family_members = DjangoFilterConnectionField(
        InsureeGQLType,
        chfId=graphene.String(required=True),
        validity=graphene.String()
    )

    @staticmethod
    def _resolve_insuree(info, **kwargs):
        try:
            return Insuree.objects.get(
                Q(chf_id=kwargs.get('chfId')),
                *core.utils.filter_validity(**kwargs)
            )
        except Insuree.DoesNotExist:
            return None

    def resolve_insuree(self, info, **kwargs):
        return Query._resolve_insuree(info=info, **kwargs)

    def resolve_insuree_family_members(self, info, **kwargs):
        insuree = Query._resolve_insuree(info=info, **kwargs)
        return Insuree.objects.filter(
            Q(family=insuree.family),
            *core.utils.filter_validity(**kwargs)
        ).order_by('-head')
