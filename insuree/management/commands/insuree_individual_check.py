from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from insuree.individual_bridge import referenced_individuals

REFERENCING = (
    ("tblClaim", "InsureeID"),
    ("tblClaimDedRem", "InsureeID"),
    ("tblFamilies", "InsureeID"),
    ("tblHealthStatus", "InsureeID"),
    ("tblInsureePolicy", "InsureeID"),
    ("tblPolicyRenewalDetails", "InsureeID"),
    ("tblPolicyRenewals", "InsureeID"),
    ("insuree_InsureeMutation", "insuree_id"),
    ("tblPolicyHolderInsuree", "InsureeId"),
    ("tblContractDetails", "InsureeID"),
)
UUID_PATTERN = (
    "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    "[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
NEW_CONSTRAINTS = """
    SELECT conrelid::regclass::text, conname, convalidated FROM pg_constraint
    WHERE conname LIKE '%fk_insuree_individual'
       OR conname = 'tblInsuree_history_copies_only'
    ORDER BY 1
"""


class Command(BaseCommand):
    help = (
        "Checks a database before and after insurees become individuals"
        " (insuree migrations 0026-0028). --finalize validates the"
        " constraints 0028 adds and vacuums the moved tables."
    )

    def add_arguments(self, parser):
        parser.add_argument("--finalize", action="store_true")

    def handle(self, *args, **options):
        self.blockers = 0
        with connection.cursor() as cursor:
            self.cursor = cursor
            is_view = self.scalar(
                "SELECT relkind = 'v' FROM pg_class"
                " WHERE relname = 'tblInsuree'"
            )
            heads = '"tblInsuree_history"' if is_view else '"tblInsuree"'
            self.check_heads(heads, is_view)
            self.check_references(is_view)
            if is_view:
                if options["finalize"]:
                    self.finalize()
                self.check_moved()
                self.check_structure()
        if self.blockers:
            raise CommandError("%d blocking finding(s)" % self.blockers)
        self.stdout.write("no blocking findings")

    def scalar(self, sql, params=None):
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()[0]

    def report(self, blocking, count, message):
        if not count:
            return
        self.blockers += 1 if blocking else 0
        label = "BLOCKER" if blocking else "info"
        self.stdout.write("%s: %s — %s" % (label, count, message))

    def check_heads(self, heads, is_view):
        where = ' WHERE "LegacyID" IS NULL'
        source = "SELECT * FROM %s%s" % (heads, where)
        if is_view:
            self.report(
                True,
                self.scalar("SELECT count(*) FROM (%s) h" % source),
                "insurees still in the history table: run migrate insuree",
            )
        self.report(
            False,
            self.scalar(
                'SELECT count(*) FROM (%s) h WHERE "DOB" IS NULL' % source
            ),
            "insurees without birth date: stored as 1970-01-01, shown empty",
        )
        self.cursor.execute(
            'SELECT h."AuditUserID", count(*) FROM (%s) h'
            ' WHERE NOT EXISTS (SELECT 1 FROM "core_User" u'
            ' WHERE u.i_user_id = h."AuditUserID")'
            " GROUP BY 1 ORDER BY 2 DESC" % source
        )
        unresolved = self.cursor.fetchall()
        self.report(
            False,
            sum(count for _, count in unresolved),
            "rows whose AuditUserID has no user, attributed to insuree_legacy"
            " (AuditUserID: rows) %s"
            % ", ".join("%s: %s" % row for row in unresolved[:20]),
        )
        self.report(
            True,
            self.scalar(
                "SELECT count(*) FROM (%s) h"
                ' WHERE "InsureeUUID" IS NOT NULL AND "InsureeUUID" !~ %%s'
                % source,
                [UUID_PATTERN],
            ),
            "insurees whose InsureeUUID is not a uuid",
        )
        self.report(
            False,
            self.scalar(
                "SELECT count(*) FROM (%s) h"
                ' WHERE "InsureeUUID" <> lower("InsureeUUID")' % source
            ),
            "insurees with an uppercase InsureeUUID: kept as written",
        )
        self.report(
            True,
            self.scalar(
                "SELECT count(*) FROM (%s) h JOIN individual_individual i"
                ' ON i."UUID"::text = lower(h."InsureeUUID")'
                ' WHERE h."InsureeUUID" ~ %%s' % source,
                [UUID_PATTERN],
            ),
            "insurees whose uuid an individual already has",
        )
        self.report(
            False,
            self.scalar(
                'SELECT count(*) FROM (SELECT "CHFID" FROM (%s) h'
                ' WHERE "ValidityTo" IS NULL AND "CHFID" IS NOT NULL'
                " GROUP BY 1 HAVING count(*) > 1) d" % source
            ),
            "insurance numbers held by more than one current insuree",
        )

    def check_references(self, is_view):
        heads = (
            'SELECT 1 FROM "%s" h WHERE h."InsureeID" = r."%%s"'
            ' AND h."LegacyID" IS NULL'
            % ("tblInsuree_history" if is_view else "tblInsuree")
        )
        linked = (
            ' OR EXISTS (SELECT 1 FROM "insuree_InsureeIndividual" l'
            ' WHERE l."InsureeID" = r."%s")'
        )
        for referencing, column in REFERENCING:
            exists = "EXISTS (%s)" % (heads % column)
            if is_view:
                exists += linked % column
            self.report(
                True,
                self.scalar(
                    'SELECT count(*) FROM "%s" r WHERE r."%s" IS NOT NULL'
                    " AND NOT (%s)" % (referencing, column, exists)
                ),
                '%s."%s" pointing at no insuree or at an old version'
                % (referencing, column),
            )

    def check_moved(self):
        self.report(
            True,
            self.scalar(
                'SELECT count(*) FROM "insuree_InsureeIndividual" l'
                " WHERE NOT EXISTS (SELECT 1 FROM individual_individual i"
                ' WHERE i."UUID" = l.individual_id)'
            ),
            "insurees whose individual is missing",
        )
        self.report(
            True,
            self.scalar(
                'SELECT count(*) FROM "insuree_InsureeIndividual" l'
                ' JOIN individual_individual i ON i."UUID" = l.individual_id'
                " WHERE NOT 'INSUREE' = ANY (i.labels)"
            ),
            "insuree individuals without the INSUREE label",
        )
        self.report(
            False,
            self.scalar(
                "SELECT count(*) FROM individual_individual i"
                " WHERE 'INSUREE' = ANY (i.labels) AND NOT EXISTS ("
                'SELECT 1 FROM "insuree_InsureeIndividual" l'
                ' WHERE l.individual_id = i."UUID")'
            ),
            "individuals labelled INSUREE that are not insurees",
        )
        self.report(
            False,
            self.scalar(
                'SELECT count(*) FROM "tblInsuree" v'
                ' JOIN "insuree_InsureeIndividual" l USING ("InsureeID")'
                ' JOIN individual_individual i ON i."UUID" = l.individual_id'
                ' LEFT JOIN "tblFamilies" f ON f."FamilyID" = v."FamilyID"'
                " WHERE i.location_id IS DISTINCT FROM"
                ' COALESCE(v."CurrentVillage", f."LocationId")'
            ),
            "insuree individuals whose location is not their village or"
            " their family's (moved by a group)",
        )
        references = referenced_individuals(self.cursor)
        for reference, count in references.items():
            self.report(
                False,
                count,
                "%s rows point at insuree individuals: migrating back"
                " below 0027 is refused while they exist" % reference,
            )

    def check_structure(self):
        self.cursor.execute(NEW_CONSTRAINTS)
        constraints = self.cursor.fetchall()
        self.report(
            True,
            int(len(constraints) < len(REFERENCING) + 1),
            "the constraints of insuree 0028 are missing: run migrate insuree",
        )
        self.report(
            True,
            int(
                self.scalar(
                    "SELECT pg_get_serial_sequence("
                    "'\"insuree_InsureeIndividual\"', 'InsureeID')"
                )
                is None
            ),
            "the insuree id sequence is not owned by the link table",
        )
        self.report(
            True,
            self.scalar(
                "SELECT count(*) FROM pg_depend d"
                " JOIN pg_rewrite r ON r.oid = d.objid"
                " WHERE d.refobjid = '\"tblInsuree_history\"'::regclass"
                " AND r.ev_class <> d.refobjid"
            ),
            "views still reading the history table instead of the view",
        )
        if constraints:
            self.report(
                True,
                sum(1 for *_, valid in constraints if not valid),
                "constraints not validated yet: run with --finalize",
            )

    def finalize(self):
        self.cursor.execute(NEW_CONSTRAINTS)
        for table, name, valid in self.cursor.fetchall():
            if not valid:
                self.cursor.execute(
                    'ALTER TABLE %s VALIDATE CONSTRAINT "%s"' % (table, name)
                )
                self.stdout.write("validated %s" % name)
        if connection.in_atomic_block:
            self.stdout.write("VACUUM skipped: running inside a transaction")
            return
        for table in ('"tblInsuree_history"', "individual_individual"):
            # No parallel workers: their shared memory outgrows the 64 MB
            # /dev/shm a Postgres container gets by default.
            self.cursor.execute("VACUUM (ANALYZE, PARALLEL 0) %s" % table)
            self.stdout.write("vacuumed %s" % table)
