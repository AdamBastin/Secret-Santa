import json

from flask import current_app


SUPPORTED_FIELD_TYPES = {"text", "textarea", "select", "checkboxes"}


def load_questionnaire():
    with open(current_app.config["QUESTIONNAIRE_PATH"], encoding="utf-8") as config:
        questionnaire = json.load(config)

    for field in questionnaire["questions"]:
        if field["type"] not in SUPPORTED_FIELD_TYPES:
            raise ValueError(f"Unsupported question type: {field['type']}")

    return questionnaire


def collect_answers(form, questionnaire):
    answers = {}
    errors = {}

    for question in questionnaire["questions"]:
        key = question["id"]
        if question["type"] == "checkboxes":
            value = form.getlist(key)
        else:
            value = form.get(key, "").strip()

        if question.get("required") and not value:
            errors[key] = "This question is required."

        answers[key] = value

    return answers, errors
