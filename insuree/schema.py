from django.db.models import Q
from django.core.exceptions import PermissionDenied
from graphene_django.filter import DjangoFilterConnectionField
import graphene_django_optimizer as gql_optimizer

from .apps import InsureeConfig
from django.utils.translation import gettext as _
from location.apps import LocationConfig
from core.schema import OrderedDjangoFilterConnectionField

# We do need all queries and mutations in the namespace here.
from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]

class Query(graphene.ObjectType):
    insuree_genders = graphene.List(GenderGQLType)
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
    family_types = graphene.List(FamilyTypeGQLType)
    confirmation_types = graphene.List(ConfirmationTypeGQLType)
    families = OrderedDjangoFilterConnectionField(
        FamilyGQLType,
        null_as_false_poverty=graphene.Boolean(),
        show_history=graphene.Boolean(),
        parent_location=graphene.String(),
        parent_location_level=graphene.Int(),
        orderBy=graphene.List(of_type=graphene.String)
    )
    family_members = graphene.List(
        InsureeGQLType,
        family_uuid=graphene.String(required=True)
    )

    def resolve_insuree_genders(selfself, info, **kwargs):
        return Gender.objects.order_by('sort_order').all()

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
        return Insuree.objects.filter(*filter_validity(**kwargs))

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

    def resolve_family_members(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        family = Family.objects.get(Q(uuid=kwargs.get('family_uuid')))
        return Insuree.objects.filter(
            Q(family=family),
            *filter_validity(**kwargs)
        ).order_by('-head')

    def resolve_confirmation_types(selfself, info, **kwargs):
        return ConfirmationType.objects.order_by('sort_order').all()

    def resolve_family_types(selfself, info, **kwargs):
        return FamilyType.objects.order_by('sort_order').all()

    def resolve_families(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_families_perms):
            raise PermissionDenied(_("unauthorized"))
        filters = []
        null_as_false_poverty = kwargs.get('null_as_false_poverty')
        if null_as_false_poverty is not None:
            filters += [Q(poverty=True)] if null_as_false_poverty else [Q(poverty=False) | Q(poverty__isnull=True)]
        show_history = kwargs.get('show_history', False)
        if not show_history:
            filters += filter_validity(**kwargs)
        parent_location = kwargs.get('parent_location')
        if parent_location is not None:
            parent_location_level = kwargs.get('parent_location_level')
            if parent_location_level is None:
                raise NotImplementedError("Missing parentLocationLevel argument when filtering on parentLocation")
            f = "uuid"
            for i in range(len(LocationConfig.location_types) - parent_location_level - 1):
                f = "parent__" + f
            f = "location__" + f
            filters += [Q(**{f: parent_location})]
        return gql_optimizer.query(Family.objects.filter(*filters).all(), info)

