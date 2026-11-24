from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .models import (
    assignments_started,
    create_secret_santa_assignments,
    get_assignment_exclusions,
    get_assignment_for_registrant,
    get_spend_limit_cents,
    get_wishlist_items,
    get_registrant,
    has_completed_wishlist,
    list_assignments,
    list_registrants,
    login_or_create_registrant,
    save_assignment_exclusions,
    save_spend_limit_cents,
    save_wishlist,
)
from .spend_limit import format_spend_limit, parse_spend_limit, spend_limit_input_value
from .wishlist import collect_wishlist_items


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    registrant = current_registrant()
    return render_template("index.html", registrant=registrant)


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        try:
            registrant = login_or_create_registrant(
                request.form.get("name", ""),
                request.form.get("pin", ""),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            session["registrant_id"] = registrant.id
            if has_completed_wishlist(registrant.id):
                return redirect(url_for("main.waiting"))
            return redirect(url_for("main.wishlist"))

    return render_template("register.html")


@bp.route("/wishlist", methods=("GET", "POST"))
def wishlist():
    registrant = require_registrant()
    if registrant is None:
        return redirect(url_for("main.register"))

    items = get_wishlist_items(registrant.id)
    error = None

    if request.method == "POST":
        items, error = collect_wishlist_items(request.form)
        if error is None:
            save_wishlist(registrant.id, items)
            return redirect(url_for("main.waiting"))

    return render_template(
        "wishlist.html",
        error=error,
        items=items,
        registrant=registrant,
        spend_limit=format_spend_limit(get_spend_limit_cents()),
    )


@bp.route("/questionnaire")
def questionnaire():
    """Keep old bookmarks working after the setup flow changed."""
    return redirect(url_for("main.wishlist"))


@bp.route("/waiting")
def waiting():
    registrant = require_registrant()
    if registrant is None:
        return redirect(url_for("main.register"))

    if not has_completed_wishlist(registrant.id):
        return redirect(url_for("main.wishlist"))

    assignment = get_assignment_for_registrant(registrant.id)
    assignment_wishlist = []
    if assignment:
        assignment_wishlist = get_wishlist_items(assignment["id"])

    return render_template(
        "waiting.html",
        assignment=assignment,
        assignment_wishlist=assignment_wishlist,
        registrant=registrant,
        spend_limit=format_spend_limit(get_spend_limit_cents()),
    )


@bp.route("/admin", methods=("GET", "POST"))
def admin():
    registrant = require_admin()
    if not registrant:
        return admin_redirect()

    if request.method == "POST":
        try:
            spend_limit_cents = parse_spend_limit(
                request.form.get("spend_limit", "")
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            save_spend_limit_cents(spend_limit_cents)
            flash("Spending limit updated.", "success")
        return redirect(url_for("main.admin"))

    spend_limit_cents = get_spend_limit_cents()
    return render_template(
        "admin.html",
        assignments_started=assignments_started(),
        registrant=registrant,
        registrants=list_registrants(),
        spend_limit=format_spend_limit(spend_limit_cents),
        spend_limit_value=spend_limit_input_value(spend_limit_cents),
    )


@bp.route("/admin/assignments", methods=("GET", "POST"))
def assignment_settings():
    registrant = require_admin()
    if not registrant:
        return admin_redirect()

    registrants = list_registrants()
    started = assignments_started()

    if request.method == "POST":
        if started:
            flash("Restrictions cannot be changed after assignments have started.", "error")
            return redirect(url_for("main.assignment_settings"))

        valid_ids = {person["id"] for person in registrants}
        exclusions = set()

        for giver in registrants:
            for recipient_id in request.form.getlist(f"cannot_match_{giver['id']}"):
                if not recipient_id.isdigit():
                    continue
                recipient_id = int(recipient_id)
                if recipient_id in valid_ids and recipient_id != giver["id"]:
                    exclusions.add((giver["id"], recipient_id))

        save_assignment_exclusions(exclusions)
        flash("Assignment restrictions saved.", "success")
        return redirect(url_for("main.assignment_settings"))

    return render_template(
        "assignment_settings.html",
        assignments=list_assignments(),
        assignments_started=started,
        exclusions=get_assignment_exclusions(),
        registrant=registrant,
        registrants=registrants,
    )


@bp.post("/admin/assignments/start")
def start_assignments():
    registrant = require_admin()
    if not registrant:
        return admin_redirect()

    try:
        create_secret_santa_assignments()
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        flash("Assignments started. Registration is now closed.", "success")

    return redirect(url_for("main.assignment_settings"))


def current_registrant():
    registrant_id = session.get("registrant_id")
    if registrant_id is None:
        return None
    return get_registrant(registrant_id)


def require_registrant():
    registrant = current_registrant()
    if registrant is None:
        flash("Register first to continue.", "error")
    return registrant


def require_admin():
    registrant = require_registrant()
    if registrant is None:
        return None

    if not registrant.is_admin:
        flash("Only the first registered user can view admin pages.", "error")
        return None

    return registrant


def admin_redirect():
    if current_registrant() is None:
        return redirect(url_for("main.register"))
    return redirect(url_for("main.waiting"))
