import re
from django.db.models import Q
import graphene
from graphene_django import DjangoObjectType
from .models import Insuree, Photo
from core import datetime


class PhotoType(DjangoObjectType):
    class Meta:
        model = Photo


class InsureeType(DjangoObjectType):
    class Meta:
        model = Insuree


class Query(graphene.ObjectType):
    insuree = graphene.Field(
        InsureeType, chfId=graphene.String(), validity=graphene.String()
    )
    all_insurees = graphene.List(InsureeType)

    def resolve_insuree(self, info, **kwargs):        
        validity = kwargs.get('validity')
        if validity is None:
            validity = datetime.datetime.now()
        else:
            d = re.split('\D', validity)
            validity = datetime.datetime(*[int('0'+x) for x in d][:6])

        chf_id = kwargs.get('chfId')            
        if chf_id is not None:
            return Insuree.objects.get(
                Q(chf_id=chf_id),
                Q(validity_from=None) | Q(validity_from__lte=validity),
                Q(validity_to=None) | Q(validity_to__gte=validity)
            )

        return None

    def resolve_all_insurees(self, info, **kwargs):
        return Insuree.objects.all()
