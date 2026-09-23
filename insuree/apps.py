import os

from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration
from django.conf import settings


MODULE_NAME = "insuree"

# Rights, by entity then by action. Same structure as `core.apps.DJANGO_PERMS`: the
# identifiers live in one place only, and the hierarchy makes sharing visible.
#
# 101101 is shared by design: reading an insuree, their photo or the list of insurees is
# the same read of the registry, and the openIMIS catalogue expresses it that way
# (insuree.insuree / insuree.insuree_photo / insuree.insurees, all at 101101).
DJANGO_PERMS = {
    "insuree": {
        "query": ("insuree.view_insuree", 101101),
        "queryPhoto": ("insuree.view_insuree_photo", 101101),
        "queryOne": ("insuree.view_insuree_detail", 101101),
        "create": ("insuree.add_insuree", 101102),
        "update": ("insuree.change_insuree", 101103),
        "delete": ("insuree.delete_insuree", 101104),
        # Looking up an insuree across the whole territory, ignoring the caller's
        # districts. Its own identifier (101106): this is the one action that
        # deliberately leaves the geographical scope, so it has to be grantable - and
        # revocable - on its own.
        "queryNational": ("insuree.view_national_insuree", 101106),
        # Declared long ago and checked nowhere.
        "inquire": ("insuree.inquire_insuree", 101105),
        "queryPolicy": ("insuree.view_insuree_policy", 101500),
        # Enrolment officers read from the insuree screen: an alias of the read right.
        "queryOfficers": ("insuree.view_insuree_officer", 101101),
    },
    "family": {
        "query": ("insuree.view_family", 101001),
        "create": ("insuree.add_family", 101002),
        "update": ("insuree.change_family", 101003),
        "delete": ("insuree.delete_family", 101004),
    },
}

_PERM_CFG = {
    "gql_query_insurees_perms": ("insuree", "query"),
    "gql_query_insuree_perms": ("insuree", "queryOne"),
    "gql_query_insuree_photo_perms": ("insuree", "queryPhoto"),
    "gql_query_insuree_officers_perms": ("insuree", "queryOfficers"),
    "gql_query_insuree_policy_perms": ("insuree", "queryPolicy"),
    "gql_query_insuree_inquire_perms": ("insuree", "inquire"),
    "gql_query_national_insuree_perms": ("insuree", "queryNational"),
    "gql_mutation_create_insurees_perms": ("insuree", "create"),
    "gql_mutation_update_insurees_perms": ("insuree", "update"),
    "gql_mutation_delete_insurees_perms": ("insuree", "delete"),
    "gql_query_families_perms": ("family", "query"),
    "gql_mutation_create_families_perms": ("family", "create"),
    "gql_mutation_update_families_perms": ("family", "update"),
    "gql_mutation_delete_families_perms": ("family", "delete"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


DEFAULT_CFG = {
    # Was [] - and `has_perms([])` returns True, so this query was open to every
    # authenticated user. Aliased onto gql_query_insurees_perms (101101), the read right for the
    # entity it belongs to: no new id and no role to grant, and it narrows the
    # query from everyone to that entity's readers. A dedicated id would narrow it
    # further and is the better end state.
    "gql_query_insuree_family_members": ["101101"],
    # Looking an insuree up by CHFID nationwide, ignoring the caller's districts.
    # A new right with an id of its own (101106, the next free slot in this block)
    # rather than an alias: this is the one operation that deliberately leaves the
    # location scope, so it has to be grantable - and revocable - on its own. It was
    # reachable with the claim create/update rights, which meant every claim clerk
    # could resolve any insuree in the country from a CHFID.
    "insuree_photos_root_path": os.path.abspath("./images/insurees"),
    # fake insurees (and bound families) used, for example, in 'funding'
    "excluded_insuree_chfids": ['999999999'],
    # age (in months) of a picture due for renewal for adults
    "renewal_photo_age_adult": 60,
    # age (in months) of a picture due for renewal for children
    "renewal_photo_age_child": 12,
    # Insuree number *function* that validates the insuree number for example
    "insuree_number_validator": None,
    # 'msystems.utils.is_valid_resident_identifier'
    "insuree_number_max_length": None,  # Insuree number length to validate
    "insuree_number_min_length": None,  # Insuree number length to validate
    # modulo base for checksum on last digit, requires length to be set too
    "insuree_number_modulo_root": None,
    "validation_code_taken_insuree_number": 1,
    "validation_code_no_insuree_number": 2,
    "validation_code_invalid_insuree_number_len": 3,
    "validation_code_invalid_insuree_number_checksum": 4,
    "validation_code_invalid_insuree_number_exception": 5,
    "validation_code_validator_import_error": 6,
    "validation_code_validator_function_error": 7,
    "insuree_fsp_mandatory": False,
    "insuree_as_worker": False,
    "is_insuree_photo_required": False,
    "use_contextual_enrolment_officer_selection": False
}


class InsureeConfig(AppConfig):
    name = MODULE_NAME

    # Rights: constants derived from DJANGO_PERMS, no longer overridable. They go
    # neither through DEFAULT_CFG nor through ready().
    gql_query_insurees_perms = RIGHTS.perms("insuree", "query")
    gql_query_insuree_perms = RIGHTS.perms("insuree", "queryOne")
    gql_query_insuree_family_members = []
    gql_query_families_perms = RIGHTS.perms("family", "query")
    gql_query_insuree_officers_perms = RIGHTS.perms("insuree", "queryOfficers")
    gql_query_insuree_policy_perms = RIGHTS.perms("insuree", "queryPolicy")
    gql_query_national_insuree_perms = RIGHTS.perms("insuree", "queryNational")
    # `__load_config` only assigns config keys that already exist as attributes here,
    # so a key declared in DEFAULT_CFG without one is silently never loaded:
    # gql_query_insuree_inquire_perms (101105) had no attribute, which is why reading
    # `InsureeConfig.gql_query_insuree_inquire_perms` raises AttributeError and why
    # nothing in the codebase checks it.
    gql_query_insuree_inquire_perms = RIGHTS.perms("insuree", "inquire")
    gql_query_insuree_photo_perms = RIGHTS.perms("insuree", "queryPhoto")
    gql_mutation_create_families_perms = RIGHTS.perms("family", "create")
    gql_mutation_update_families_perms = RIGHTS.perms("family", "update")
    gql_mutation_delete_families_perms = RIGHTS.perms("family", "delete")
    gql_mutation_create_insurees_perms = RIGHTS.perms("insuree", "create")
    gql_mutation_update_insurees_perms = RIGHTS.perms("insuree", "update")
    gql_mutation_delete_insurees_perms = RIGHTS.perms("insuree", "delete")
    validation_code_taken_insuree_number = None
    validation_code_no_insuree_number = None
    validation_code_invalid_insuree_number_len = None
    validation_code_invalid_insuree_number_checksum = None
    validation_code_invalid_insuree_number_exception = None
    validation_code_validator_import_error = None
    validation_code_validator_function_error = None
    insuree_photos_root_path = None
    excluded_insuree_chfids = []
    renewal_photo_age_adult = None
    renewal_photo_age_child = None
    insuree_number_validator = None
    insuree_number_max_length = None
    insuree_number_min_length = None
    insuree_number_modulo_root = None
    insuree_fsp_mandatory = None
    insuree_as_worker = None
    is_insuree_photo_required = None
    use_contextual_enrolment_officer_selection = None

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(InsureeConfig, field):
                setattr(InsureeConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
        self._configure_photo_root(cfg)

    def set_dataloaders(self, dataloaders):
        from .dataloaders import InsureeLoader, FamilyLoader

        dataloaders["insuree_loader"] = InsureeLoader()
        dataloaders["family_loader"] = FamilyLoader()

    @classmethod
    def __get_from_settings_or_default(cls, attribute_name, default=None):
        if hasattr(settings, attribute_name):
            value = getattr(settings, attribute_name) or default
        else:
            value = default
        return value

    def _configure_photo_root(self, cfg):
        # TODO: To be confirmed. I left loading from config for integrity reasons
        #  but it could be based on env variable only.
        #  Also we could determine global file root for all stored files across modules.
        if from_config := cfg.get("insuree_photos_root_path", None):
            InsureeConfig.insuree_photos_root_path = from_config
        elif from_env := os.getenv("PHOTO_ROOT_PATH", None):
            InsureeConfig.insuree_photos_root_path = from_env
