from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .models import (
    assignments_started,
    create_secret_santa_assignments,
    get_assignment_exclusions,
    get_assignment_for_registrant,
    get_questionnaire_answers,
    get_registrant,
    has_completed_questionnaire,
    list_assignments,
    list_registrants,
    login_or_create_registrant,
    save_assignment_exclusions,
    save_questionnaire_response,
)
from .questionnaire import collect_answers, load_questionnaire


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
            if has_completed_questionnaire(registrant.id):
                return redirect(url_for("main.waiting"))
            return redirect(url_for("main.questionnaire"))

    return render_template("register.html")


@bp.route("/questionnaire", methods=("GET", "POST"))
def questionnaire():
    registrant = require_registrant()
    if registrant is None:
        return redirect(url_for("main.register"))

    questionnaire_config = load_questionnaire()
    answers = {}
    errors = {}

    if request.method == "POST":
        answers, errors = collect_answers(request.form, questionnaire_config)
        if not errors:
            save_questionnaire_response(registrant.id, answers)
            return redirect(url_for("main.waiting"))

    return render_template(
        "questionnaire.html",
        answers=answers,
        errors=errors,
        questionnaire=questionnaire_config,
        registrant=registrant,
    )


@bp.route("/waiting")
def waiting():
    registrant = require_registrant()
    if registrant is None:
        return redirect(url_for("main.register"))

    if not has_completed_questionnaire(registrant.id):
        return redirect(url_for("main.questionnaire"))

    assignment = get_assignment_for_registrant(registrant.id)
    assignment_answers = {}
    if assignment:
        assignment_answers = get_questionnaire_answers(assignment["id"])

    return render_template(
        "waiting.html",
        assignment=assignment,
        assignment_answers=assignment_answers,
        questionnaire=load_questionnaire(),
        registrant=registrant,
    )


@bp.route("/admin")
def admin():
    registrant = require_admin()
    if not registrant:
        return admin_redirect()

    return render_template(
        "admin.html",
        assignments_started=assignments_started(),
        registrant=registrant,
        registrants=list_registrants(),
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
