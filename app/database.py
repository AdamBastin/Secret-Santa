import sqlite3

from flask import current_app, g


SCHEMA = """
CREATE TABLE IF NOT EXISTS registrants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    pin TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registrant_id INTEGER NOT NULL UNIQUE,
    items_json TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (registrant_id) REFERENCES registrants (id)
);

CREATE TABLE IF NOT EXISTS event_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    spend_limit_cents INTEGER NOT NULL CHECK (spend_limit_cents > 0)
);

INSERT OR IGNORE INTO event_settings (id, spend_limit_cents) VALUES (1, 5000);

CREATE TABLE IF NOT EXISTS assignment_exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giver_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (giver_id) REFERENCES registrants (id),
    FOREIGN KEY (recipient_id) REFERENCES registrants (id),
    UNIQUE (giver_id, recipient_id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giver_id INTEGER NOT NULL UNIQUE,
    recipient_id INTEGER NOT NULL UNIQUE,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (giver_id) REFERENCES registrants (id),
    FOREIGN KEY (recipient_id) REFERENCES registrants (id)
);
"""


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        g.db = connection

    return g.db


def init_db(app):
    with app.app_context():
        get_db().executescript(SCHEMA)
        get_db().commit()


def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()
