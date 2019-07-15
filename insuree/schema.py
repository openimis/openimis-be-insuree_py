import graphene
from graphene_django import DjangoObjectType
from .models import Insuree


class InsureeType(DjangoObjectType):
    class Meta:
        model = Insuree
        exclude_fields = ('row_id',)


class Query(graphene.ObjectType):
    all_insurees = graphene.List(InsureeType)

    def resolve_all_insurees(self, info, **kwargs):
        return Insuree.objects.all()
