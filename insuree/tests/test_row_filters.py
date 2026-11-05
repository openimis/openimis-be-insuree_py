"""get_queryset honours the OP-2029 validity contract (epic OP-3317, phase 1).

Explicit validity values return the expected rows; a caller asking for
nothing gets what it got before the contract existed.
"""

from django.test import TestCase

from core.models.row_filters import Audits, Validity
from core.test_helpers import assert_row_filters, create_test_interactive_user, mark_deleted
from insuree.models import Family, Insuree
from insuree.test_helpers import create_test_insuree


class InsureeRowFiltersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_interactive_user(username="insureerowfilters")

    def test_insuree(self):
        live = create_test_insuree()
        deleted = mark_deleted(create_test_insuree())
        assert_row_filters(
            self, Insuree, Insuree.objects.filter(id__in=[live.id, deleted.id]), self.user,
            live.id, deleted.id, default_hides_deleted=False,
        )

    def test_family(self):
        live = create_test_insuree().family
        deleted = mark_deleted(create_test_insuree().family)
        assert_row_filters(
            self, Family, Family.objects.filter(id__in=[live.id, deleted.id]), self.user,
            live.id, deleted.id, default_hides_deleted=False,
        )

    def test_audits_all_returns_the_history(self):
        insuree = create_test_insuree()
        copy_id = insuree.save_history()
        rows = Insuree.objects.filter(chf_id=insuree.chf_id)
        self.assertEqual(
            {insuree.id, copy_id},
            set(Insuree.get_queryset(rows, self.user, validity=Validity.NOW, audits=Audits.ALL)
                .values_list("id", flat=True)),
        )
        self.assertEqual(
            {insuree.id},
            set(Insuree.get_queryset(rows, self.user, validity=Validity.NOW).values_list("id", flat=True)),
        )
