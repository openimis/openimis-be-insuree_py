from core.schema import signal_mutation_module_validate
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from graphene_django.filter import DjangoFilterConnectionField
import graphene_django_optimizer as gql_optimizer

from .apps import InsureeConfig
from .models import FamilyMutation, InsureeMutation
from django.utils.translation import gettext as _
from location.apps import LocationConfig
from core.schema import OrderedDjangoFilterConnectionField

# We do need all queries and mutations in the namespace here.
from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]


def family_fk(arg):
    return arg.startswith("members_") or arg.startswith("head_insuree_")


class FamiliesConnectionField(OrderedDjangoFilterConnectionField):
    @classmethod
    def resolve_queryset(
            cls, connection, iterable, info, args, filtering_args, filterset_class
    ):
        qs = super(FamiliesConnectionField, cls).resolve_queryset(
            connection, iterable, info,
            {k: args[k] for k in args.keys() if not k.startswith("members_") and not k.startswith("head_insuree_")},
            filtering_args,
            filterset_class
        )
        head_insuree_filters = {k: args[k] for k in args.keys() if k.startswith("head_insuree__")}
        members_filters = {k: args[k] for k in args.keys() if k.startswith("members__")}
        if len(head_insuree_filters) or len(members_filters):
            qs = qs._next_is_sticky()
        if len(head_insuree_filters):
            qs = qs.filter(Q(head_insuree__validity_to__isnull=True), **head_insuree_filters)
        if len(members_filters):
            qs = qs.filter(Q(members__validity_to__isnull=True), **members_filters)
        return OrderedDjangoFilterConnectionField.orderBy(qs, args)


class Query(graphene.ObjectType):
    insuree_genders = graphene.List(GenderGQLType)
    insurees = OrderedDjangoFilterConnectionField(
        InsureeGQLType,
        show_history=graphene.Boolean(),
        parent_location=graphene.String(),
        parent_location_level=graphene.Int(),
        orderBy=graphene.List(of_type=graphene.String),
    )
    insuree_family_members = graphene.List(
        InsureeGQLType,
        chfId=graphene.String(required=True),
        validity=graphene.Date(),
        orderBy=graphene.List(of_type=graphene.String),
    )
    identification_types = graphene.List(IdentificationTypeGQLType)
    educations = graphene.List(EducationGQLType)
    professions = graphene.List(ProfessionGQLType)
    family_types = graphene.List(FamilyTypeGQLType)
    confirmation_types = graphene.List(ConfirmationTypeGQLType)
    families = FamiliesConnectionField(
        FamilyGQLType,
        null_as_false_poverty=graphene.Boolean(),
        show_history=graphene.Boolean(),
        parent_location=graphene.String(),
        parent_location_level=graphene.Int(),
        orderBy=graphene.List(of_type=graphene.String),
    )
    family_members = OrderedDjangoFilterConnectionField(
        InsureeGQLType,
        family_uuid=graphene.String(required=True),
        orderBy=graphene.List(of_type=graphene.String),
    )

    def resolve_insuree_genders(selfself, info, **kwargs):
        return Gender.objects.order_by('sort_order').all()

    def resolve_insurees(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        filters = []
        show_history = kwargs.get('show_history', False)
        if not show_history:
            filters += filter_validity(**kwargs)
        gql_optimizer.query(Family.objects.filter(*filters).all(), info)

    def resolve_insuree_family_members(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        insuree = Insuree.objects.get(
            Q(chf_id=kwargs.get('chfId')),
            *filter_validity(**kwargs)
        )
        return Insuree.objects.filter(
            Q(family=insuree.family),
            *filter_validity(**kwargs)
        ).order_by('-head', 'dob')

    def resolve_family_members(self, info, **kwargs):
        if not info.context.user.has_perms(InsureeConfig.gql_query_insurees_perms):
            raise PermissionDenied(_("unauthorized"))
        family = Family.objects.get(Q(uuid=kwargs.get('family_uuid')))
        return Insuree.objects.filter(
            Q(family=family),
            *filter_validity(**kwargs)
        ).order_by('-head', 'dob')

    def resolve_educations(selfself, info, **kwargs):
        return Education.objects.order_by('sort_order').all()

    def resolve_professions(selfself, info, **kwargs):
        return Profession.objects.order_by('sort_order').all()

    def resolve_identification_types(selfself, info, **kwargs):
        return IdentificationType.objects.order_by('sort_order').all()

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


class Mutation(graphene.ObjectType):
    create_family = CreateFamilyMutation.Field()
    # update_family = UpdateFamilyMutation.Field()
    create_insuree = CreateInsureeMutation.Field()
    # update_insuree = UpdateInsureeMutation.Field()


def on_family_mutation(kwargs):
    family_uuid = kwargs['data'].get('uuid', None)
    if not family_uuid:
        return []
    impacted_family = Family.objects.get(Q(uuid=family_uuid))
    FamilyMutation.objects.create(family=impacted_family, mutation_id=kwargs['mutation_log_id'])
    return []


def on_insuree_mutation(kwargs):
    insuree_uuid = kwargs['data'].get('uuid', None)
    if not insuree_uuid:
        return []
    impacted_insuree = Insuree.objects.get(Q(uuid=insuree_uuid))
    InsureeMutation.objects.create(insuree=impacted_insuree, mutation_id=kwargs['mutation_log_id'])
    return []


def on_mutation(sender, **kwargs):
    return {
        CreateFamilyMutation._mutation_class: lambda x: on_family_mutation(x),
        CreateInsureeMutation._mutation_class: lambda x: on_insuree_mutation(x),
    }.get(sender._mutation_class, lambda x: [])(kwargs)


def bind_signals():
    signal_mutation_module_validate["insuree"].connect(on_mutation)
