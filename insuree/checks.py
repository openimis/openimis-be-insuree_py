from django.apps import apps
from django.core import checks
from django.db import connections

# The references to Insuree that existed when tblInsuree became a view;
# insuree 0028 points their database constraints at the link table.
KNOWN_REFERENCES = {
    "claim.Claim.insuree",
    "claim.ClaimDedRem.insuree",
    "contract.ContractDetails.insuree",
    "insuree.Family.head_insuree",
    "insuree.InsureeMutation.insuree",
    "insuree.InsureePhoto.insuree",
    "insuree.InsureePolicy.insuree",
    "insuree.PolicyRenewalDetail.insuree",
    "policy.PolicyRenewal.insuree",
    "policyholder.PolicyHolderInsuree.insuree",
}


@checks.register()
def check_individual_installed(app_configs=None, **kwargs):
    if apps.is_installed("individual"):
        return []
    return [
        checks.Error(
            "insuree stores insurees as individuals and needs the individual"
            " module in INSTALLED_APPS (openimis.json).",
            id="insuree.E001",
        )
    ]


@checks.register(checks.Tags.database)
def check_postgresql(app_configs=None, databases=None, **kwargs):
    if connections["default"].vendor == "postgresql":
        return []
    return [
        checks.Error(
            "insuree turns tblInsuree into a PostgreSQL view and needs a"
            " PostgreSQL database.",
            id="insuree.E002",
        )
    ]


def constrained_references(models):
    from insuree.models import Insuree

    for model in models:
        for field in model._meta.get_fields():
            if (
                getattr(field, "concrete", False)
                and field.is_relation
                and field.related_model is Insuree
                and field.db_constraint
            ):
                yield "%s.%s" % (model._meta.label, field.name)


@checks.register(checks.Tags.models)
def check_references_to_insuree(app_configs=None, **kwargs):
    return [
        checks.Error(
            "%s references Insuree with a database constraint; tblInsuree is"
            " a view and cannot be referenced." % reference,
            hint="Declare the field with db_constraint=False.",
            id="insuree.E003",
        )
        for reference in constrained_references(apps.get_models())
        if reference not in KNOWN_REFERENCES
    ]
