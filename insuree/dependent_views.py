"""
Postgres binds a view to the relations it reads by oid, not by name, so a view
over "tblInsuree" would follow the table through a rename. These helpers take
every view built on a relation, directly or through other views, out of the way
and put it back afterwards, so it binds to whatever carries the name by then.
"""

_DEPENDENT_VIEWS = """
WITH RECURSIVE dependent(oid, depth) AS (
    SELECT r.ev_class, 1
    FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid
    WHERE d.classid = 'pg_rewrite'::regclass
      AND d.refobjid = %s::regclass AND r.ev_class <> d.refobjid
    UNION
    SELECT r.ev_class, dependent.depth + 1
    FROM dependent
    JOIN pg_depend d
      ON d.refobjid = dependent.oid AND d.classid = 'pg_rewrite'::regclass
    JOIN pg_rewrite r ON r.oid = d.objid
    WHERE r.ev_class <> dependent.oid
)
SELECT n.nspname, c.relname, c.relkind, max(dependent.depth),
       pg_get_viewdef(c.oid)
FROM dependent
JOIN pg_class c ON c.oid = dependent.oid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('v', 'm')
GROUP BY n.nspname, c.relname, c.relkind, c.oid
ORDER BY max(dependent.depth), c.relname
"""


def capture(cursor, relation):
    """Views over `relation`, in an order they can be created again in."""
    cursor.execute(_DEPENDENT_VIEWS, [relation])
    return [
        {
            "schema": schema,
            "name": name,
            "materialized": kind == "m",
            "definition": definition,
        }
        for schema, name, kind, _depth, definition in cursor.fetchall()
    ]


def _kind(view):
    return "MATERIALIZED VIEW" if view["materialized"] else "VIEW"


def drop(cursor, views):
    for view in reversed(views):
        cursor.execute(
            'DROP %s "%s"."%s"' % (_kind(view), view["schema"], view["name"])
        )


def recreate(cursor, views):
    for view in views:
        cursor.execute(
            'CREATE %s "%s"."%s" AS %s'
            % (_kind(view), view["schema"], view["name"], view["definition"])
        )
