#!/usr/bin/env python3
"""Validate and advance a spec-delivery-lite change stored in change.yaml."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys
import tempfile

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


LEVELS = {"direct": 0, "tracked": 1, "high": 2}
STATES = {
    "planned": {"implementing", "blocked"},
    "implementing": {"ready_for_acceptance", "blocked"},
    "ready_for_acceptance": {"accepting", "blocked"},
    "accepting": {"accepted", "changes_requested", "blocked"},
    "changes_requested": {"implementing", "blocked"},
    "accepted": set(),
    "blocked": set(),
}
AC_STATES = {"pending", "passed", "failed", "waived"}
PLACEHOLDER = re.compile(r"<[^<>]+>")


class WorkflowError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def change_file(path: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    return resolved / "change.yaml" if resolved.is_dir() else resolved


def load(path: Path) -> dict:
    if not path.is_file():
        raise WorkflowError(f"Missing state file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise WorkflowError("change.yaml must contain a mapping")
    return data


def save(path: Path, data: dict) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".change-", delete=False
    ) as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
        temporary = Path(handle.name)
    temporary.replace(path)


def entries(data: dict, key: str, prefix: str, errors: list[str]) -> dict[str, dict]:
    items = data.get(key)
    if not isinstance(items, list):
        errors.append(f"{key} must be a list")
        return {}
    indexed = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append(f"{key} entries need an id")
            continue
        identifier = item["id"]
        if not identifier.startswith(prefix) or not identifier[len(prefix):].isdigit():
            errors.append(f"Invalid {key} id: {identifier}")
        if identifier in indexed:
            errors.append(f"Duplicate {key} id: {identifier}")
        indexed[identifier] = item
    return indexed


def validate(data: dict, directory: Path) -> list[str]:
    errors: list[str] = []
    if data.get("format_version") != 2:
        return ["Expected format_version: 2; migrate older changes deliberately"]
    requirements = entries(data, "requirements", "R-", errors)
    tasks = entries(data, "tasks", "T-", errors)
    acceptance = entries(data, "acceptance", "AC-", errors)
    if not requirements:
        errors.append("At least one requirement is required")
    if not acceptance:
        errors.append("At least one acceptance criterion is required")
    if not isinstance(data.get("history"), list):
        errors.append("history must be a list")

    for requirement_id, requirement in requirements.items():
        level = requirement.get("level")
        state = requirement.get("state")
        if level not in LEVELS:
            errors.append(f"{requirement_id}: invalid level")
            continue
        reasons = requirement.get("level_reasons")
        title = requirement.get("title")
        if not isinstance(title, str) or not title.strip() or not isinstance(reasons, list) or not reasons or not all(isinstance(reason, str) and reason.strip() for reason in reasons):
            errors.append(f"{requirement_id}: title and level_reasons are required")
        elif PLACEHOLDER.search(title) or any(PLACEHOLDER.search(reason) for reason in reasons):
            errors.append(f"{requirement_id}: replace template placeholders")
        if state not in STATES:
            errors.append(f"{requirement_id}: invalid state")
            continue
        if state == "blocked":
            if requirement.get("blocked_from") not in STATES or requirement.get("blocked_from") in {"blocked", "accepted"}:
                errors.append(f"{requirement_id}: blocked_from is required")
            if not requirement.get("blocked_reason"):
                errors.append(f"{requirement_id}: blocked_reason is required")
        elif requirement.get("blocked_from") or requirement.get("blocked_reason"):
            errors.append(f"{requirement_id}: blocked fields must be empty outside blocked")
        ids = requirement.get("acceptance_ids")
        if not isinstance(ids, list) or not ids:
            errors.append(f"{requirement_id}: acceptance_ids are required")
            ids = []
        for criterion_id in ids:
            if criterion_id not in acceptance or acceptance[criterion_id].get("requirement_id") != requirement_id:
                errors.append(f"{requirement_id}: invalid acceptance link {criterion_id}")
        if state in {"planned", "implementing", "ready_for_acceptance"} and any(
            acceptance.get(ac_id, {}).get("status") in {"passed", "failed"} for ac_id in ids
        ):
            errors.append(f"{requirement_id}: stale acceptance result before review")
        if level == "high":
            approval = requirement.get("approval")
            if not isinstance(approval, dict) or approval.get("required") is not True:
                errors.append(f"{requirement_id}: high-risk approval.required must be true")
            elif state not in {"planned", "blocked"} and not (approval.get("confirmed_by") and approval.get("confirmed_at")):
                errors.append(f"{requirement_id}: high-risk approval is missing")
        if state in {"ready_for_acceptance", "accepting", "accepted"} and not requirement.get("developer"):
            errors.append(f"{requirement_id}: developer is required after handoff")
        if state in {"accepting", "accepted"} and not requirement.get("reviewer"):
            errors.append(f"{requirement_id}: reviewer is required during acceptance")
        if state in {"accepting", "accepted"} and requirement.get("reviewer") == requirement.get("developer") and not requirement.get("self_review_reason"):
            errors.append(f"{requirement_id}: self-review limitation must be recorded")
        if state == "accepted":
            if any(acceptance.get(ac_id, {}).get("status") not in {"passed", "waived"} for ac_id in ids):
                errors.append(f"{requirement_id}: acceptance is incomplete")
            if level != "direct":
                verification = directory / "verification.md"
                if not verification.is_file():
                    errors.append(f"{requirement_id}: verification.md is required before acceptance")
                else:
                    content = verification.read_text(encoding="utf-8")
                    for ac_id in ids:
                        if ac_id not in content:
                            errors.append(f"{requirement_id}: verification.md omits {ac_id}")

    for task_id, task in tasks.items():
        if task.get("status") not in {"pending", "done"}:
            errors.append(f"{task_id}: invalid task status")
        links = task.get("requirement_ids")
        if not isinstance(links, list) or not links or any(link not in requirements for link in links):
            errors.append(f"{task_id}: invalid requirement_ids")
    for requirement_id, requirement in requirements.items():
        if requirement.get("level") != "direct" and not any(
            requirement_id in task.get("requirement_ids", []) for task in tasks.values()
        ):
            errors.append(f"{requirement_id}: tracked/high requirement needs a task")
        if requirement.get("state") in {"ready_for_acceptance", "accepting", "accepted"} and any(
            requirement_id in task.get("requirement_ids", []) and task.get("status") != "done"
            for task in tasks.values()
        ):
            errors.append(f"{requirement_id}: implementation tasks are incomplete")

    for criterion_id, criterion in acceptance.items():
        owner = criterion.get("requirement_id")
        if owner not in requirements or criterion_id not in requirements[owner].get("acceptance_ids", []):
            errors.append(f"{criterion_id}: invalid requirement link")
        description = criterion.get("criterion")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{criterion_id}: criterion is required")
        elif PLACEHOLDER.search(description):
            errors.append(f"{criterion_id}: replace template placeholders")
        status = criterion.get("status")
        if status not in AC_STATES:
            errors.append(f"{criterion_id}: invalid status")
        if status in {"passed", "failed"} and not criterion.get("evidence"):
            errors.append(f"{criterion_id}: evidence is required")
        if status == "waived" and not (
            criterion.get("waiver_reason") and criterion.get("waiver_approved_by")
        ):
            errors.append(f"{criterion_id}: waiver reason and approver are required")

    if any(req.get("level") != "direct" for req in requirements.values()):
        for file_name in ("brief.md", "tasks.md"):
            if not (directory / file_name).is_file():
                errors.append(f"{file_name} is required for tracked/high changes")
    if any(req.get("level") == "high" and req.get("state") not in {"planned", "blocked"} for req in requirements.values()):
        if not (directory / "design.md").is_file():
            errors.append("design.md is required before high-risk implementation")
    return errors


def require_valid(data: dict, directory: Path) -> None:
    errors = validate(data, directory)
    if errors:
        raise WorkflowError("Invalid change:\n- " + "\n- ".join(errors))


def one(data: dict, key: str, identifier: str) -> dict:
    return next((item for item in data[key] if item["id"] == identifier), None) or _missing(identifier)


def _missing(identifier: str):
    raise WorkflowError(f"Unknown ID: {identifier}")


def event(data: dict, message: str) -> None:
    data.setdefault("history", []).append({"at": now(), "event": message})


def transition(data: dict, directory: Path, identifier: str, target: str, actor: str | None, reason: str | None) -> None:
    requirement = one(data, "requirements", identifier)
    source = requirement["state"]
    if source == "blocked":
        if target != requirement["blocked_from"]:
            raise WorkflowError(f"{identifier}: unblock only to {requirement['blocked_from']}")
        requirement["blocked_from"] = None
        requirement["blocked_reason"] = None
    elif target not in STATES[source]:
        raise WorkflowError(f"Illegal transition: {source} -> {target}")
    if target == "blocked":
        if not reason:
            raise WorkflowError("Blocking requires --reason")
        requirement["blocked_from"] = source
        requirement["blocked_reason"] = reason
    if target == "implementing":
        if requirement["level"] == "high":
            approval = requirement.get("approval", {})
            if not (approval.get("confirmed_by") and approval.get("confirmed_at") and (directory / "design.md").is_file()):
                raise WorkflowError("High-risk work needs recorded approval and design.md")
        if source == "planned" and not actor:
            raise WorkflowError("Starting implementation requires --actor")
        requirement["developer"] = actor or requirement.get("developer")
        if source == "changes_requested":
            for criterion in data["acceptance"]:
                if criterion["id"] in requirement["acceptance_ids"] and criterion["status"] in {"failed", "passed"}:
                    criterion["status"] = "pending"
                    criterion["evidence"] = None
            requirement["reviewer"] = None
            requirement["self_review_reason"] = None
    if target == "ready_for_acceptance":
        if not requirement.get("developer"):
            raise WorkflowError("Handoff requires a recorded developer")
        if any(identifier in task["requirement_ids"] and task["status"] != "done" for task in data["tasks"]):
            raise WorkflowError("Complete linked tasks before handoff")
    if target == "accepting":
        actor = actor or (requirement.get("reviewer") if source == "blocked" else None)
        if not actor:
            raise WorkflowError("Acceptance requires --actor for the reviewer")
        requirement["reviewer"] = actor
        if actor == requirement.get("developer"):
            if not (reason or requirement.get("self_review_reason")):
                raise WorkflowError("Self-review requires --reason describing the independence limit")
            requirement["self_review_reason"] = reason or requirement["self_review_reason"]
    if target == "changes_requested" and not reason:
        raise WorkflowError("Requesting changes requires --reason")
    if target == "accepted":
        criteria = [one(data, "acceptance", ac_id) for ac_id in requirement["acceptance_ids"]]
        if any(ac["status"] not in {"passed", "waived"} for ac in criteria):
            raise WorkflowError("Every linked acceptance criterion must pass or be explicitly waived")
        if requirement["level"] != "direct" and not (directory / "verification.md").is_file():
            raise WorkflowError("Write verification.md before acceptance")
    requirement["state"] = target
    event(data, f"{identifier}: {source} -> {target}" + (f" ({reason})" if reason else ""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "status", "transition", "task", "acceptance", "archive"))
    parser.add_argument("path", help="Change directory or change.yaml")
    parser.add_argument("identifier", nargs="?", help="R-##, T-## or AC-##")
    parser.add_argument("value", nargs="?", help="Target state, done, passed, failed or waived")
    parser.add_argument("--actor", help="Developer or reviewer identity")
    parser.add_argument("--reason", help="Block/change-request/self-review or waiver reason")
    parser.add_argument("--evidence", help="Observed result and evidence reference")
    parser.add_argument("--waiver-approved-by", help="User who explicitly accepted a waiver")
    args = parser.parse_args()
    path = change_file(args.path)
    try:
        data = load(path)
        require_valid(data, path.parent)
        if args.command == "validate":
            print("Valid change")
            return 0
        if args.command == "status":
            for requirement in data["requirements"]:
                print(f"{requirement['id']} [{requirement['level']}] {requirement['state']}: {requirement['title']}")
            for task in data["tasks"]:
                print(f"{task['id']} {task['status']}: {', '.join(task['requirement_ids'])}")
            for criterion in data["acceptance"]:
                print(f"{criterion['id']} {criterion['status']}: {criterion['requirement_id']}")
            return 0
        data = copy.deepcopy(data)
        if args.command == "transition":
            if not args.identifier or not args.value:
                raise WorkflowError("transition needs R-## and target state")
            transition(data, path.parent, args.identifier, args.value, args.actor, args.reason)
        elif args.command == "task":
            if args.value != "done" or not args.identifier:
                raise WorkflowError("task needs T-## done")
            task = one(data, "tasks", args.identifier)
            if task["status"] != "pending":
                raise WorkflowError("Task is already done")
            if any(one(data, "requirements", rid)["state"] != "implementing" for rid in task["requirement_ids"]):
                raise WorkflowError("Linked requirements must be implementing")
            task["status"] = "done"
            event(data, f"{args.identifier}: task done")
        elif args.command == "acceptance":
            if args.value not in {"passed", "failed", "waived"} or not args.identifier:
                raise WorkflowError("acceptance needs AC-## passed|failed|waived")
            criterion = one(data, "acceptance", args.identifier)
            requirement = one(data, "requirements", criterion["requirement_id"])
            if requirement["state"] != "accepting":
                raise WorkflowError("Requirement must be in accepting state")
            if args.value == "waived":
                if not (args.reason and args.waiver_approved_by):
                    raise WorkflowError("Waiver needs --reason and --waiver-approved-by")
                criterion["waiver_reason"] = args.reason
                criterion["waiver_approved_by"] = args.waiver_approved_by
            elif not args.evidence:
                raise WorkflowError("Pass/fail needs --evidence")
            criterion["status"] = args.value
            criterion["evidence"] = args.evidence if args.value != "waived" else None
            event(data, f"{args.identifier}: {args.value}")
        elif args.command == "archive":
            if path.parent.parent.name != "changes" or path.parent.parent.parent.name != ".spec-delivery-lite":
                raise WorkflowError("Archive requires .spec-delivery-lite/changes/<change-name>/change.yaml")
            if any(req["state"] != "accepted" for req in data["requirements"]):
                raise WorkflowError("Every requirement must be accepted before archive")
            if any(task["status"] != "done" for task in data["tasks"]):
                raise WorkflowError("Unfinished tasks prevent archive")
            destination = path.parent.parent.parent / "archive" / f"{datetime.now().date()}-{path.parent.name}"
            if destination.exists():
                raise WorkflowError(f"Archive already exists: {destination}")
            event(data, "Change archived")
            save(path, data)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path.parent), str(destination))
            print(f"Archived to {destination}")
            return 0
        require_valid(data, path.parent)
        save(path, data)
        print("Updated", path)
        return 0
    except (WorkflowError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
