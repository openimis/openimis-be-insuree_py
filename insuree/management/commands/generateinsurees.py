import random

from django.core.management.base import BaseCommand
from faker import Faker
from insuree.test_helpers import create_test_insuree


class Command(BaseCommand):
    help = "This command will generate test Insurees with some optional parameters. It is intended to simulate larger" \
           "databases for performance testing"
    insurees = None
    services = None
    items = None
    products = None

    def add_arguments(self, parser):
        parser.add_argument("nb_insurees", nargs=1, type=int)
        parser.add_argument("nb_members", nargs=1, type=int)
        parser.add_argument(
            '--policy',
            action='store_true',
            dest='policy',
            help='Create a policy for each family, it will be active',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Be verbose about what it is doing',
        )
        parser.add_argument(
            '--locale',
            default="fr_FR",
            help="Used to adapt the fake names generation to the locale, using Faker, by default fr_FR",
        )

    def handle(self, *args, **options):
        fake = Faker(options["locale"])
        nb_insurees = options["nb_insurees"][0]
        nb_members = options["nb_members"][0]
        verbose = options["verbose"]
        policy = options["policy"]
        for insuree_num in range(1, nb_insurees + 1):
            props = dict(
                last_name=fake.last_name(),
                other_names=fake.first_name(),
                dob=fake.date_between(start_date='-105y', end_date='today'),
                chf_id=random.randrange(100000000, 999999999),
            )
            insuree = create_test_insuree(custom_props=props)
            if verbose:
                print(insuree_num, "created head insuree and family", insuree.other_names, insuree.last_name,
                      insuree.chf_id)
            for member_num in range(1, nb_members + 1):
                props["other_names"] = fake.first_name()
                props["dob"] = fake.date_between(start_date='-105y', end_date='today')
                props["family_id"] = insuree.family_id
                props["chf_id"] = random.randrange(100000000, 999999999)
                member = create_test_insuree(with_family=False, custom_props=props)
                if verbose:
                    print("Created family member", member_num, member.other_names)

            if policy:
                from policy.test_helpers import create_test_policy_family
                product = self.get_random_product()
                policy = create_test_policy_family(product, insuree.family, link=True, valid=True)
                if verbose:
                    print("Generated policy for family", insuree.family_id, policy)

    def get_random_product(self):
        if not self.products:
            from product.models import Product
            self.products = Product.objects.filter(validity_to__isnull=True).values_list("pk", flat=True)
        return random.choice(self.products)
