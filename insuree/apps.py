from django.apps import AppConfig
from django.conf import settings


MODULE_NAME = "insuree"

DEFAULT_CFG = {
    "gql_query_insurees_perms": ["101101"],
    "gql_query_insuree_perms": ["101101"],
    "gql_query_insuree_officers_perms": [],
    "gql_insuree_family_members": ["101101"],
    "gql_query_families_perms": ["101001"],
    "gql_query_insuree_policy_perms": ["101500"],
    "gql_mutation_create_families_perms": ["101002"],
    "gql_mutation_update_families_perms": ["101003"],
    "gql_mutation_delete_families_perms": ["101004"],
    "gql_mutation_create_insurees_perms": ["101102"],
    "gql_mutation_update_insurees_perms": ["101103"],
    "gql_mutation_delete_insurees_perms": ["101104"],
    "insuree_photos_root_path": None,
    "excluded_insuree_chfids": ['999999999'],  # fake insurees (and bound families) used, for example, in 'funding'
    "renewal_photo_age_adult": 60,  # age (in months) of a picture due for renewal for adults
    "renewal_photo_age_child": 12,  # age (in months) of a picture due for renewal for children
    "insuree_number_validator": None,  # Insuree number *function* that validates the insuree number
    "insuree_number_length": None,  # Insuree number length to validate
    "insuree_number_modulo_root": None,  # modulo base for checksum on last digit, requires length to be set too
}


class InsureeConfig(AppConfig):
    name = MODULE_NAME

    gql_query_insurees_perms = []
    gql_query_insuree_perms = []

    gql_insuree_family_members = []
    gql_query_families_perms = []
    gql_query_insuree_officers_perms = []
    gql_query_insuree_policy_perms = []
    gql_mutation_create_families_perms = []
    gql_mutation_update_families_perms = []
    gql_mutation_delete_families_perms = []
    gql_mutation_create_insurees_perms = []
    gql_mutation_update_insurees_perms = []
    gql_mutation_delete_insurees_perms = []
    insuree_photos_root_path = None
    excluded_insuree_chfids = ['999999999']
    renewal_photo_age_adult = 60
    renewal_photo_age_child = 12
    insuree_number_validator = None
    insuree_number_length = None
    insuree_number_modulo_root = None

    def _configure_permissions(self, cfg):
        InsureeConfig.gql_query_insurees_perms = cfg["gql_query_insurees_perms"]
        InsureeConfig.gql_query_insuree_perms = cfg["gql_query_insuree_perms"]
        InsureeConfig.gql_query_insuree_officers_perms = cfg["gql_query_insuree_officers_perms"]
        InsureeConfig.gql_insuree_family_members = cfg["gql_insuree_family_members"]
        InsureeConfig.gql_query_families_perms = cfg["gql_query_families_perms"]
        InsureeConfig.gql_query_insuree_policy_perms = cfg["gql_query_insuree_policy_perms"]
        InsureeConfig.gql_mutation_create_families_perms = cfg["gql_mutation_create_families_perms"]
        InsureeConfig.gql_mutation_update_families_perms = cfg["gql_mutation_update_families_perms"]
        InsureeConfig.gql_mutation_create_insurees_perms = cfg["gql_mutation_create_insurees_perms"]
        InsureeConfig.gql_mutation_update_insurees_perms = cfg["gql_mutation_update_insurees_perms"]
        InsureeConfig.gql_mutation_delete_insurees_perms = cfg["gql_mutation_delete_insurees_perms"]
        InsureeConfig.insuree_photos_root_path = cfg["insuree_photos_root_path"]
        InsureeConfig.insuree_number_validator = cfg["insuree_number_validator"]
        InsureeConfig.insuree_number_length = cfg["insuree_number_length"]
        InsureeConfig.insuree_number_modulo_root = cfg["insuree_number_modulo_root"]

    def _configure_fake_insurees(self, cfg):
        InsureeConfig.excluded_insuree_chfids = cfg["excluded_insuree_chfids"]

    def _configure_renewal(self, cfg):
        InsureeConfig.renewal_photo_age_adult = cfg["renewal_photo_age_adult"]
        InsureeConfig.renewal_photo_age_child = cfg["renewal_photo_age_child"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
        self._configure_fake_insurees(cfg)
        self._configure_renewal(cfg)

    # Getting these at runtime for easier testing
    @classmethod
    def get_insuree_number_validator(cls):
        return cls.insuree_number_validator or cls.__get_from_settings_or_default("INSUREE_NUMBER_VALIDATOR")

    @classmethod
    def get_insuree_number_length(cls):
        value = cls.insuree_number_length or cls.__get_from_settings_or_default("INSUREE_NUMBER_LENGTH")
        return int(value) if value else None

    @classmethod
    def get_insuree_number_modulo_root(cls):
        value = cls.insuree_number_modulo_root or cls.__get_from_settings_or_default("INSUREE_NUMBER_MODULE_ROOT")
        return int(value) if value else None

    def set_dataloaders(self, dataloaders):
        from .dataloaders import InsureeLoader, FamilyLoader

        dataloaders["insuree_loader"] = InsureeLoader()
        dataloaders["family_loader"] = FamilyLoader()

    @classmethod
    def __get_from_settings_or_default(cls, attribute_name, default=None):
        return getattr(settings, attribute_name) if hasattr(settings, attribute_name) else default
