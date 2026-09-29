"""
Moves the head of every insuree version chain (the row other tables reference)
from the history table into the individual table, and back. Each batch commits
on its own when called outside a transaction, so a large move can be resumed:
rows already moved are no longer in the history table.
"""

from django.db import transaction

from insuree.sql import read_sql

_NEXT_HEADS = """
    SELECT "InsureeID" FROM "tblInsuree_history"
    WHERE "LegacyID" IS NULL AND "InsureeID" > %s
    ORDER BY "InsureeID" LIMIT %s FOR UPDATE
"""
_NEXT_LINKED = """
    SELECT "InsureeID" FROM "insuree_InsureeIndividual" WHERE "InsureeID" > %s
    ORDER BY "InsureeID" LIMIT %s FOR UPDATE
"""
_COUNT_REFERENCES = """
    SELECT count(*) FROM %s WHERE "%s" IN (
        SELECT individual_id FROM "insuree_InsureeIndividual")
"""


def _batches(connection, next_ids_sql, batch_size, work):
    # Paged from the last id handled: rows already moved are deleted, and a
    # scan from the start would walk past all of them on every batch.
    moved, last = 0, -1
    while True:
        with transaction.atomic(using=connection.alias):
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '5s'")
                cursor.execute(next_ids_sql, [last, batch_size])
                ids = [row[0] for row in cursor.fetchall()]
                if not ids:
                    return moved
                work(cursor, {"ids": ids})
                moved += len(ids)
                last = ids[-1]


def move_insuree_heads(connection, batch_size=5000):
    def move(cursor, params):
        cursor.execute(read_sql("bridge_move.sql"), params)
        cursor.execute(read_sql("bridge_move_history.sql"), params)
        cursor.execute(
            'DELETE FROM "tblInsuree_history"'
            ' WHERE "InsureeID" = ANY(%(ids)s)',
            params,
        )

    return _batches(connection, _NEXT_HEADS, batch_size, move)


def referenced_individuals(cursor):
    """Rows elsewhere that point at moved insurees, by table and column:
    moving those insurees back would leave them pointing at nothing."""
    cursor.execute(read_sql("bridge_references.sql"))
    counts = {}
    for table, column in cursor.fetchall():
        cursor.execute(_COUNT_REFERENCES % (table, column))
        count = cursor.fetchone()[0]
        if count:
            counts["%s.%s" % (table, column)] = count
    return counts


def restore_insuree_heads(connection, batch_size=5000):
    with connection.cursor() as cursor:
        references = referenced_individuals(cursor)
    if references:
        raise RuntimeError(
            "Insurees cannot be moved back while other records point at"
            " them as individuals: %s"
            % ", ".join("%s (%s)" % item for item in references.items())
        )

    def restore(cursor, params):
        cursor.execute(read_sql("bridge_restore.sql"), params)

    return _batches(connection, _NEXT_LINKED, batch_size, restore)
