from django.db.models import Q
from django.core.exceptions import PermissionDenied
from graphene_django.filter import DjangoFilterConnectionField

from .apps import InsureeConfig
from django.utils.translation import gettext as _
from location.apps import LocationConfig

# We do need all queries and mutations in the namespace here.
from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]

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
    families = DjangoFilterConnectionField(
        FamilyGQLType,
        parent_location=graphene.String(),
        parent_location_level=graphene.Int()
    )

    @staticmethod
    def _resolve_insuree(info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        return Insuree.objects.get(
            Q(chf_id=kwargs.get('chfId')),
            *filter_validity(**kwargs)
        )

    def resolve_insurees(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        pass

    def resolve_insuree(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insuree_perms):
            raise PermissionDenied(_("unauthorized"))
        try:
            return Query._resolve_insuree(info=info, **kwargs)
        except Insuree.DoesNotExist:
            return None

    def resolve_insuree_family_members(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        insuree = Query._resolve_insuree(info=info, **kwargs)
        return Insuree.objects.filter(
            Q(family=insuree.family),
            *filter_validity(**kwargs)
        ).order_by('-head')

    def resolve_families(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_families_perms):
            raise PermissionDenied(_("unauthorized"))
        filters = []
        parent_location = kwargs.get('parent_location')
        if parent_location is not None:
            parent_location_level = kwargs.get('parent_location_level')
            kwargs.pop('parent_location')
            kwargs.pop('parent_location_level')
            if parent_location_level is None:
                raise NotImplementedError("Missing parentLocationLevel argument when filtering on parentLocation")
            f = "uuid"
            for i in range(len(LocationConfig.location_types) - parent_location_level - 1):
                f = "parent__" + f
            f = "location__" + f
            filters += [Q(**{f: parent_location})]
        return Family.objects.filter(*filters)

