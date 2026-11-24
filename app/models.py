import json
import random
import re
import sqlite3
from dataclasses import dataclass

from .database import get_db


PIN_PATTERN = re.compile(r"^\d{4}$")


@dataclass(frozen=True)
class Registrant:
    id: int
    name: str
    pin: str
    is_admin: bool


def normalize_name(name):
    return " ".join(name.strip().split())


def create_registrant(name, pin):
    cleaned_name = normalize_name(name)
    if not cleaned_name:
        raise ValueError("Name is required.")

    if not PIN_PATTERN.match(pin):
        raise ValueError("PIN must be exactly 4 digits.")

    db = get_db()
    if assignments_started():
        raise ValueError("Registration is closed because assignments have started.")

    first_user = db.execute("SELECT COUNT(*) FROM registrants").fetchone()[0] == 0

    try:
        cursor = db.execute(
            "INSERT INTO registrants (name, pin, is_admin) VALUES (?, ?, ?)",
            (cleaned_name, pin, int(first_user)),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("That name is already registered.") from exc

    return get_registrant(cursor.lastrowid)


def login_or_create_registrant(name, pin):
    cleaned_name = normalize_name(name)
    if not cleaned_name:
        raise ValueError("Name is required.")

    if not PIN_PATTERN.match(pin):
        raise ValueError("PIN must be exactly 4 digits.")

    existing = get_registrant_by_name(cleaned_name)
    if existing is None:
        return create_registrant(cleaned_name, pin)

    if existing.pin != pin:
        raise ValueError("That name is already registered with a different PIN.")

    return existing


def get_registrant(registrant_id):
    row = get_db().execute(
        "SELECT id, name, pin, is_admin FROM registrants WHERE id = ?",
        (registrant_id,),
    ).fetchone()

    if row is None:
        return None

    return Registrant(
        id=row["id"],
        name=row["name"],
        pin=row["pin"],
        is_admin=bool(row["is_admin"]),
    )


def get_registrant_by_name(name):
    row = get_db().execute(
        "SELECT id, name, pin, is_admin FROM registrants WHERE name = ?",
        (name,),
    ).fetchone()

    if row is None:
        return None

    return Registrant(
        id=row["id"],
        name=row["name"],
        pin=row["pin"],
        is_admin=bool(row["is_admin"]),
    )


def list_registrants():
    return get_db().execute(
        """
        SELECT registrants.id, registrants.name, registrants.pin, registrants.is_admin,
               wishlists.completed_at,
               assignments.assigned_at
        FROM registrants
        LEFT JOIN wishlists
            ON wishlists.registrant_id = registrants.id
        LEFT JOIN assignments
            ON assignments.giver_id = registrants.id
        ORDER BY registrants.created_at ASC
        """
    ).fetchall()


def get_assignment_exclusions():
    rows = get_db().execute(
        "SELECT giver_id, recipient_id FROM assignment_exclusions"
    ).fetchall()
    return {(row["giver_id"], row["recipient_id"]) for row in rows}


def save_assignment_exclusions(exclusions):
    if assignments_started():
        raise ValueError("Restrictions cannot be changed after assignments have started.")

    db = get_db()
    db.execute("DELETE FROM assignment_exclusions")
    db.executemany(
        """
        INSERT INTO assignment_exclusions (giver_id, recipient_id)
        VALUES (?, ?)
        """,
        sorted(exclusions),
    )
    db.commit()


def assignments_started():
    row = get_db().execute("SELECT 1 FROM assignments LIMIT 1").fetchone()
    return row is not None


def create_secret_santa_assignments():
    db = get_db()
    if assignments_started():
        raise ValueError("Assignments have already started.")

    registrants = list_registrants()
    if len(registrants) < 2:
        raise ValueError("At least two registrants are required to start assignments.")

    exclusions = get_assignment_exclusions()
    assignment_pairs = build_assignment_pairs(registrants, exclusions)
    if assignment_pairs is None:
        raise ValueError("No valid assignments could be created with the current restrictions.")

    db.executemany(
        "INSERT INTO assignments (giver_id, recipient_id) VALUES (?, ?)",
        assignment_pairs,
    )
    db.commit()
    return assignment_pairs


def build_assignment_pairs(registrants, exclusions):
    giver_ids = [person["id"] for person in registrants]
    candidates_by_giver = {}

    for giver_id in giver_ids:
        candidates = [
            recipient_id
            for recipient_id in giver_ids
            if recipient_id != giver_id and (giver_id, recipient_id) not in exclusions
        ]
        random.shuffle(candidates)
        candidates_by_giver[giver_id] = candidates

    ordered_givers = sorted(giver_ids, key=lambda giver_id: len(candidates_by_giver[giver_id]))
    assignments = {}

    def assign_next(index, available_recipients):
        if index == len(ordered_givers):
            return True

        giver_id = ordered_givers[index]
        candidates = [
            recipient_id
            for recipient_id in candidates_by_giver[giver_id]
            if recipient_id in available_recipients
        ]

        for recipient_id in candidates:
            assignments[giver_id] = recipient_id
            if assign_next(index + 1, available_recipients - {recipient_id}):
                return True
            del assignments[giver_id]

        return False

    if not assign_next(0, set(giver_ids)):
        return None

    return [(giver_id, assignments[giver_id]) for giver_id in giver_ids]


def get_assignment_for_registrant(registrant_id):
    return get_db().execute(
        """
        SELECT recipients.id, recipients.name
        FROM assignments
        JOIN registrants AS recipients
            ON recipients.id = assignments.recipient_id
        WHERE assignments.giver_id = ?
        """,
        (registrant_id,),
    ).fetchone()


def get_wishlist_items(registrant_id):
    row = get_db().execute(
        """
        SELECT items_json
        FROM wishlists
        WHERE registrant_id = ?
        """,
        (registrant_id,),
    ).fetchone()

    if row is None:
        return []

    return json.loads(row["items_json"])


def list_assignments():
    return get_db().execute(
        """
        SELECT givers.id AS giver_id, givers.name AS giver_name,
               recipients.id AS recipient_id, recipients.name AS recipient_name,
               assignments.assigned_at
        FROM assignments
        JOIN registrants AS givers
            ON givers.id = assignments.giver_id
        JOIN registrants AS recipients
            ON recipients.id = assignments.recipient_id
        ORDER BY givers.created_at ASC
        """
    ).fetchall()


def save_wishlist(registrant_id, items):
    db = get_db()
    db.execute(
        """
        INSERT INTO wishlists (registrant_id, items_json)
        VALUES (?, ?)
        ON CONFLICT(registrant_id)
        DO UPDATE SET items_json = excluded.items_json,
                      completed_at = CURRENT_TIMESTAMP
        """,
        (registrant_id, json.dumps(items)),
    )
    db.commit()


def has_completed_wishlist(registrant_id):
    row = get_db().execute(
        "SELECT 1 FROM wishlists WHERE registrant_id = ?",
        (registrant_id,),
    ).fetchone()
    return row is not None


def get_spend_limit_cents():
    row = get_db().execute(
        "SELECT spend_limit_cents FROM event_settings WHERE id = 1"
    ).fetchone()
    return row["spend_limit_cents"]


def save_spend_limit_cents(spend_limit_cents):
    db = get_db()
    db.execute(
        "UPDATE event_settings SET spend_limit_cents = ? WHERE id = 1",
        (spend_limit_cents,),
    )
    db.commit()
