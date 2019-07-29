import re
from django.db.models import Q
import graphene
from graphene_django import DjangoObjectType
from .models import Insuree, Photo, Gender, Family, FamilyType
import core


class GenderGraphQLType(DjangoObjectType):
    class Meta:
        model = Gender


class PhotoGraphQLType(DjangoObjectType):
    class Meta:
        model = Photo


class FamilyTypeGraphQLType(DjangoObjectType):
    class Meta:
        model = FamilyType


class FamilyGraphQLType(DjangoObjectType):
    class Meta:
        model = Family


class InsureeGraphQLType(DjangoObjectType):
    age = graphene.Int(source='age')

    class Meta:
        model = Insuree


class Query(graphene.ObjectType):
    insuree = graphene.Field(
        InsureeGraphQLType,
        chfId=graphene.String(required=True),
        validity=graphene.String()
    )
    insuree_family_members = graphene.List(
        InsureeGraphQLType,
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
