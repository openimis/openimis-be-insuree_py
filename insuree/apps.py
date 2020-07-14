from django.apps import AppConfig

MODULE_NAME = "insuree"

DEFAULT_CFG = {
    "gql_query_insurees_perms": ["101101"],
    "gql_query_insuree_perms": ["101101"],
    "gql_insuree_family_members": ["101101"],
    "gql_query_families_perms": ["101001"],
}


class InsureeConfig(AppConfig):
    name = MODULE_NAME

    gql_query_insurees_perms = []
    gql_query_insuree_perms = []
    gql_insuree_family_members = []
    gql_query_families_perms = []

    def _configure_permissions(self, cfg):
        InsureeConfig.gql_query_insurees_perms = cfg[
            "gql_query_insurees_perms"]
        InsureeConfig.gql_query_insuree_perms = cfg[
            "gql_query_insuree_perms"]
        InsureeConfig.gql_insuree_family_members = cfg[
            "gql_insuree_family_members"]
        InsureeConfig.gql_query_families_perms = cfg[
            "gql_query_families_perms"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
