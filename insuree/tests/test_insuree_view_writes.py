import datetime

from django.db import connection, transaction
from django.db.utils import DatabaseError
from django.test import TestCase

from core.models import User
from individual.models import Individual
from insuree.models import Insuree, InsureeIndividual
from insuree.test_helpers import create_test_insuree


def individual_of(insuree):
    return Individual.objects.get(
        id=InsureeIndividual.objects.get(insuree_id=insuree.pk).individual_id
    )


def history_types(individual):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT history_type FROM individual_historicalindividual"
            ' WHERE "UUID" = %s ORDER BY history_id',
            [individual.id],
        )
        return [row[0] for row in cursor.fetchall()]


class InsureeViewWriteTest(TestCase):
    def test_create_writes_an_individual_labelled_insuree(self):
        insuree = create_test_insuree()
        individual = individual_of(insuree)
        self.assertEqual(str(individual.id), insuree.uuid.lower())
        self.assertEqual(individual.labels, ["INSUREE"])
        self.assertEqual(individual.json_ext["chf_id"], insuree.chf_id)
        self.assertEqual(
            (individual.first_name, individual.last_name),
            (insuree.other_names, insuree.last_name),
        )
        self.assertEqual(history_types(individual)[0], "+")

    def test_every_field_reads_back_as_written(self):
        insuree = create_test_insuree(
            custom_props={
                "phone": "+123",
                "email": "a@b.c",
                "passport": "P1",
                "marital": "M",
                "card_issued": True,
            }
        )
        stored = Insuree.objects.get(pk=insuree.pk)
        for field in Insuree._meta.concrete_fields:
            if field.name in ("validity_from", "audit_user_id"):
                continue
            self.assertEqual(
                getattr(stored, field.attname),
                getattr(insuree, field.attname),
                field.name,
            )

    def test_save_history_puts_the_copy_in_the_history_table(self):
        insuree = create_test_insuree()
        copy_id = insuree.save_history()
        insuree.phone = "+999"
        insuree.save()
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "LegacyID", "ValidityTo" IS NOT NULL'
                ' FROM "tblInsuree_history" WHERE "InsureeID" = %s',
                [copy_id],
            )
            self.assertEqual(cursor.fetchone(), (insuree.pk, True))
        self.assertFalse(Insuree.objects.filter(pk=copy_id).exists())
        self.assertFalse(
            InsureeIndividual.objects.filter(insuree_id=copy_id).exists()
        )
        individual = individual_of(insuree)
        self.assertEqual(individual.json_ext["phone"], "+999")
        self.assertEqual(Insuree.objects.filter(uuid=insuree.uuid).count(), 1)

    def test_every_update_is_a_new_version_with_a_history_row(self):
        insuree = create_test_insuree()
        before = individual_of(insuree).version
        insuree.phone = "+1"
        insuree.save()
        insuree.save(update_fields=["phone"])
        individual = individual_of(insuree)
        self.assertEqual(individual.version, before + 2)
        self.assertEqual(history_types(individual)[-2:], ["~", "~"])

    def test_queryset_update_reports_the_row(self):
        insuree = create_test_insuree()
        self.assertEqual(
            Insuree.objects.filter(pk=insuree.pk).update(phone="+7"), 1
        )
        self.assertEqual(individual_of(insuree).json_ext["phone"], "+7")

    def test_saving_twice_never_duplicates(self):
        insuree = create_test_insuree()
        insuree.save()
        insuree.save()
        self.assertEqual(Insuree.objects.filter(uuid=insuree.uuid).count(), 1)
        self.assertEqual(
            InsureeIndividual.objects.filter(insuree_id=insuree.pk).count(), 1
        )

    def test_delete_history_marks_the_individual_deleted(self):
        insuree = create_test_insuree()
        insuree.delete_history()
        stored = Insuree.objects.get(pk=insuree.pk)
        self.assertIsNotNone(stored.validity_to)
        self.assertTrue(individual_of(insuree).is_deleted)

    def test_a_missing_uuid_is_generated(self):
        insuree = create_test_insuree()
        stored = Insuree.objects.get(pk=insuree.pk)
        stored.id = None
        stored.uuid = None
        stored.chf_id = "900000001"
        stored.save()
        self.assertEqual(len(Insuree.objects.get(pk=stored.pk).uuid), 36)

    def test_a_new_uuid_is_found_under_that_uuid(self):
        insuree = create_test_insuree()
        individual_id = individual_of(insuree).id
        insuree.uuid = "f8c56ada-d76d-4f6c-aad3-cfddc9fb38eb"
        insuree.save()
        self.assertEqual(Insuree.objects.get(uuid=insuree.uuid).pk, insuree.pk)
        self.assertEqual(individual_of(insuree).id, individual_id)

    def test_a_missing_birth_date_reads_back_as_missing(self):
        insuree = create_test_insuree(custom_props={"dob": None})
        self.assertIsNone(Insuree.objects.get(pk=insuree.pk).dob)
        self.assertEqual(individual_of(insuree).dob, datetime.date(1970, 1, 1))

    def test_an_unknown_audit_user_is_attributed_to_the_system_user(self):
        insuree = create_test_insuree(custom_props={"audit_user_id": -1})
        individual = individual_of(insuree)
        self.assertEqual(
            User.objects.get(id=individual.user_created_id).username,
            "insuree_legacy",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT history_change_reason"
                ' FROM individual_historicalindividual WHERE "UUID" = %s',
                [individual.id],
            )
            self.assertEqual(cursor.fetchone()[0], "tblInsuree AuditUserID=-1")

    def test_individual_keys_outside_the_insuree_fields_survive_an_update(
        self,
    ):
        insuree = create_test_insuree()
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('insuree.via_view', 'on', true)")
            cursor.execute(
                """UPDATE individual_individual
                SET "Json_ext" = "Json_ext" || '{"income": 5}'
                WHERE "UUID" = %s""",
                [individual_of(insuree).id],
            )
            cursor.execute(
                "SELECT set_config('insuree.via_view', 'off', true)"
            )
        insuree.phone = "+2"
        insuree.save()
        self.assertEqual(individual_of(insuree).json_ext["income"], 5)

    def test_a_current_insuree_cannot_be_deleted(self):
        insuree = create_test_insuree()
        with self.assertRaisesMessage(
            DatabaseError, "insuree_view: a current insuree is not deleted"
        ):
            with transaction.atomic():
                Insuree.objects.filter(pk=insuree.pk).delete()

    def test_a_reference_to_a_missing_row_fails_at_commit(self):
        insuree = create_test_insuree()
        with self.assertRaisesMessage(DatabaseError, "family_id=99999999"):
            with transaction.atomic():
                Insuree.objects.filter(pk=insuree.pk).update(
                    family_id=99999999
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET CONSTRAINTS insuree_references IMMEDIATE"
                    )

    def test_select_for_update_works_on_the_view(self):
        insuree = create_test_insuree()
        locked = Insuree.objects.select_for_update().filter(pk=insuree.pk)
        self.assertEqual(
            list(locked.values_list("pk", flat=True)), [insuree.pk]
        )

    def test_writing_through_the_view_keeps_the_callers_flag(self):
        insuree = create_test_insuree()
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('insuree.via_view', 'on', true)")
            insuree.phone = "+3"
            insuree.save()
            cursor.execute("SELECT current_setting('insuree.via_view', true)")
            self.assertEqual(cursor.fetchone()[0], "on")
            cursor.execute("SELECT set_config('insuree.via_view', '', true)")
