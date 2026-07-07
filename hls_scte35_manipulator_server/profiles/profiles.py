import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from threefive import Cue

from ..logger import logger


FilterClosure = Callable[[Cue], bool]
OverwriteClosure = Callable[[Cue], bool]
ConditionClosure = Callable[[Any], bool]

FIELD_ALIASES = {
    "command_type": "command.command_type",
    "command_name": "command.name",
}

CONDITION_PATTERN = re.compile(
    r"^(?:(?P<field>[A-Za-z_][\w\.\[\]]*)\s*)?"
    r"(?P<op>==|=|!=|>=|<=|>|<|equals|not_equals|gte|lte|gt|lt|not\s+in|in|contains|exists|not\s+exists)"
    r"\s*(?P<value>.*)$",
    re.IGNORECASE,
)


@dataclass
class Profile:
    path: str
    filters: list[FilterClosure] = field(default_factory=list, repr=False)
    overwrites: list[OverwriteClosure] = field(default_factory=list, repr=False)
    raw_filters: list[dict[str, Any]] = field(default_factory=list)
    raw_overwrites: list[dict[str, Any]] = field(default_factory=list)

    def matches_filter(self, cue: Cue) -> bool:
        return any(filter_rule(cue) for filter_rule in self.filters)

    def apply_overwrites(self, cue: Cue) -> bool:
        changed = False
        for overwrite_rule in self.overwrites:
            changed = overwrite_rule(cue) or changed
        return changed


def _format_condition_value(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value)


def _safe_int(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip().lower()
        if text.startswith("0x"):
            try:
                return int(text, 16)
            except ValueError:
                return value
        try:
            return int(text)
        except ValueError:
            return value
    return value


def _parse_scalar(value: Any) -> Any:
    if isinstance(value, list):
        return [_parse_scalar(item) for item in value]
    if not isinstance(value, str):
        return _safe_int(value)

    text = value.strip()
    lower = text.lower()
    if lower in {"null", "none"}:
        return None
    if lower == "true":
        return True
    if lower == "false":
        return False
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return _safe_int(text)


def _normalize_path(path: str) -> str:
    text = path.strip()
    return FIELD_ALIASES.get(text, text)


def _split_path(path: str) -> list[str]:
    return [part.strip() for part in _normalize_path(path).split(".") if part.strip()]


def _lookup_member(target: Any, name: str) -> Any:
    if isinstance(target, dict):
        return target.get(name)
    return getattr(target, name, None)


def _resolve_values(target: Any, path: str) -> list[Any]:
    segments = _split_path(path)
    if not segments:
        return [target]

    values = [target]
    for raw_segment in segments:
        segment = raw_segment[:-2] if raw_segment.endswith("[]") else raw_segment
        next_values: list[Any] = []
        for value in values:
            current_items = value if isinstance(value, list) else [value]
            for item in current_items:
                next_value = _lookup_member(item, segment)
                if next_value is None:
                    continue
                if isinstance(next_value, list):
                    next_values.extend(next_value)
                else:
                    next_values.append(next_value)
        values = next_values
    return values


def _resolve_contexts(target: Any, path: str) -> list[Any]:
    segments = _split_path(path)
    if not segments:
        return [target]

    contexts = [target]
    for raw_segment in segments:
        segment = raw_segment[:-2] if raw_segment.endswith("[]") else raw_segment
        next_contexts: list[Any] = []
        for context in contexts:
            current_items = context if isinstance(context, list) else [context]
            for item in current_items:
                next_value = _lookup_member(item, segment)
                if next_value is None:
                    continue
                if isinstance(next_value, list):
                    next_contexts.extend(next_value)
                else:
                    next_contexts.append(next_value)
        contexts = next_contexts
    return contexts


def _assign_value(target: Any, field: str, value: Any) -> bool:
    if isinstance(target, dict):
        target[field] = value
        return True
    if hasattr(target, field):
        setattr(target, field, value)
        return True
    return False


def _iter_assignment_targets(target: Any, path: str) -> list[tuple[Any, str]]:
    segments = _split_path(path)
    if not segments:
        return []

    leaf = segments[-1]
    if leaf.endswith("[]"):
        return []

    parent_path = ".".join(segments[:-1])
    return [(context, leaf) for context in _resolve_contexts(target, parent_path)]


def _iter_collection_targets(target: Any, path: str) -> list[list[Any]]:
    segments = _split_path(path)
    if not segments:
        return []

    leaf = segments[-1]
    field_name = leaf[:-2] if leaf.endswith("[]") else leaf
    parent_path = ".".join(segments[:-1])
    collections: list[list[Any]] = []
    for context in _resolve_contexts(target, parent_path):
        collection = _lookup_member(context, field_name)
        if isinstance(collection, list):
            collections.append(collection)
    return collections


def _split_condition_groups(condition: str, separator: str) -> list[str]:
    return [part.strip() for part in condition.split(separator) if part.strip()]


def _normalize_operator(operator: str) -> str:
    operator = " ".join(operator.lower().split())
    aliases = {
        "=": "eq",
        "==": "eq",
        "equals": "eq",
        "!=": "ne",
        "not_equals": "ne",
        ">": "gt",
        "gt": "gt",
        ">=": "gte",
        "gte": "gte",
        "<": "lt",
        "lt": "lt",
        "<=": "lte",
        "lte": "lte",
        "in": "in",
        "not in": "not_in",
        "contains": "contains",
        "exists": "exists",
        "not exists": "not_exists",
    }
    return aliases.get(operator, operator)


def _parse_condition_clause(clause: str, default_field: str | None = None) -> tuple[str, str, Any]:
    match = CONDITION_PATTERN.match(clause.strip())
    if not match:
        raise ValueError(f"Unsupported condition syntax: {clause}")

    field = match.group("field") or default_field
    if not field:
        raise ValueError(f"Condition requires a field name: {clause}")

    operator = _normalize_operator(match.group("op"))
    value = _parse_scalar(match.group("value"))
    return _normalize_path(field), operator, value


def _matches_operator(actual: Any, operator: str, expected: Any) -> bool:
    actual = _safe_int(actual)
    expected = _parse_scalar(expected)

    if operator == "exists":
        return actual is not None
    if operator == "not_exists":
        return actual is None
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "gt":
        return actual is not None and expected is not None and actual > expected
    if operator == "gte":
        return actual is not None and expected is not None and actual >= expected
    if operator == "lt":
        return actual is not None and expected is not None and actual < expected
    if operator == "lte":
        return actual is not None and expected is not None and actual <= expected
    if operator == "in":
        expected_values = expected if isinstance(expected, list) else [expected]
        return actual in {_safe_int(value) for value in expected_values}
    if operator == "not_in":
        expected_values = expected if isinstance(expected, list) else [expected]
        return actual not in {_safe_int(value) for value in expected_values}
    if operator == "contains":
        if isinstance(actual, (list, tuple, set)):
            return expected in actual
        if isinstance(actual, str):
            return str(expected) in actual
        return False
    raise ValueError(f"Unsupported operator: {operator}")


def _compile_condition_text(condition: str, default_field: str | None = None) -> ConditionClosure:
    groups: list[list[tuple[str, str, Any]]] = []
    for raw_group in _split_condition_groups(condition, "|"):
        clauses = [
            _parse_condition_clause(raw_clause, default_field)
            for raw_clause in _split_condition_groups(raw_group, "&")
        ]
        groups.append(clauses)

    def matches(target: Any) -> bool:
        for group in groups:
            if all(
                any(_matches_operator(value, operator, expected) for value in _resolve_values(target, path))
                or (operator == "not_exists" and not _resolve_values(target, path))
                for path, operator, expected in group
            ):
                return True
        return False

    return matches


def _compile_predicate(spec: Any, default_field: str | None = None) -> ConditionClosure:
    if spec is None:
        return lambda _target: True
    if isinstance(spec, str):
        return _compile_condition_text(spec, default_field)
    if not isinstance(spec, dict):
        raise ValueError(f"Unsupported predicate spec: {spec!r}")

    if "all" in spec:
        predicates = [_compile_predicate(item) for item in spec.get("all", [])]
        return lambda target: all(predicate(target) for predicate in predicates)
    if "any" in spec:
        predicates = [_compile_predicate(item) for item in spec.get("any", [])]
        return lambda target: any(predicate(target) for predicate in predicates)
    if "not" in spec:
        predicate = _compile_predicate(spec["not"])
        return lambda target: not predicate(target)
    if "condition" in spec:
        field = str(spec.get("field") or spec.get("path") or default_field or "").strip() or None
        return _compile_condition_text(str(spec["condition"]), field)

    path = str(spec.get("path") or spec.get("field") or default_field or "").strip()
    if not path:
        raise ValueError(f"Predicate requires a path/field: {spec!r}")

    operator = _normalize_operator(str(spec.get("op") or spec.get("operator") or "eq"))
    expected = _parse_scalar(spec.get("value"))
    normalized_path = _normalize_path(path)

    def matches(target: Any) -> bool:
        values = _resolve_values(target, normalized_path)
        if operator == "not_exists":
            return not values
        return any(_matches_operator(value, operator, expected) for value in values)

    return matches


def _extract_condition_target_field(condition: str, default_field: str | None = None) -> str | None:
    first_group = _split_condition_groups(condition, "|")
    if not first_group:
        return default_field
    first_clause = _split_condition_groups(first_group[0], "&")
    if not first_clause:
        return default_field
    field, _operator, _value = _parse_condition_clause(first_clause[0], default_field)
    return field


def _compile_filter_rule(rule: dict[str, Any]) -> FilterClosure | None:
    if not isinstance(rule, dict):
        logger.warning("Ignoring invalid filter rule %r", rule)
        return None

    if "match" in rule:
        predicate = _compile_predicate(rule["match"])
        return lambda cue: predicate(cue)

    field = str(rule.get("field") or rule.get("path") or "").strip()
    condition = rule.get("condition")
    if condition is not None:
        if _normalize_path(field) in {"descriptors", "descriptors[]"}:
            descriptor_predicate = _compile_predicate(condition)
            return lambda cue: any(descriptor_predicate(descriptor) for descriptor in getattr(cue, "descriptors", []))
        predicate = _compile_predicate(condition, field or None)
        return lambda cue: predicate(cue)

    predicate = _compile_predicate(rule)
    return lambda cue: predicate(cue)


def _compile_overwrite_rule(rule: dict[str, Any]) -> OverwriteClosure | None:
    if not isinstance(rule, dict):
        logger.warning("Ignoring invalid overwrite rule %r", rule)
        return None

    operation = str(rule.get("op") or "").strip().lower()
    path = str(rule.get("path") or rule.get("field") or "").strip()
    if not operation or not path:
        logger.warning("Ignoring incomplete overwrite rule %r", rule)
        return None

    normalized_path = _normalize_path(path)
    where_spec = rule.get("where")
    legacy_condition = rule.get("condition")
    if where_spec is None and legacy_condition is not None:
        where_spec = legacy_condition
    where_predicate = _compile_predicate(where_spec) if where_spec is not None else (lambda _target: True)
    parsed_value = _parse_scalar(rule.get("value"))

    if operation == "remove":
        if normalized_path in {"descriptors", "descriptors[]"} and legacy_condition is not None:
            descriptor_predicate = _compile_predicate(legacy_condition)

            def remove_descriptors(cue: Cue) -> bool:
                kept = []
                changed = False
                for descriptor in getattr(cue, "descriptors", []):
                    if descriptor_predicate(descriptor):
                        changed = True
                        continue
                    kept.append(descriptor)
                if changed:
                    cue.descriptors = kept
                return changed

            return remove_descriptors

        def remove_values(cue: Cue) -> bool:
            changed = False
            collections = _iter_collection_targets(cue, normalized_path)
            if collections:
                for collection in collections:
                    kept = []
                    local_change = False
                    for item in collection:
                        if where_predicate(item):
                            local_change = True
                            continue
                        kept.append(item)
                    if local_change:
                        collection[:] = kept
                        changed = True
                if changed:
                    return True

            for owner, field_name in _iter_assignment_targets(cue, normalized_path):
                if where_predicate(owner):
                    changed = _assign_value(owner, field_name, None) or changed
            return changed

        return remove_values

    if operation == "update":
        legacy_target_field = None
        if normalized_path in {"descriptors", "descriptors[]"} and legacy_condition is not None:
            legacy_target_field = _extract_condition_target_field(str(legacy_condition))
            if legacy_target_field:
                normalized_path = f"descriptors[].{legacy_target_field}"

        def update_values(cue: Cue) -> bool:
            changed = False
            for owner, field_name in _iter_assignment_targets(cue, normalized_path):
                if where_predicate(owner):
                    changed = _assign_value(owner, field_name, parsed_value) or changed
            return changed

        return update_values

    if operation == "add":
        def add_values(cue: Cue) -> bool:
            changed = False
            collections = _iter_collection_targets(cue, normalized_path)
            if collections:
                for collection in collections:
                    collection.append(parsed_value)
                    changed = True
                return changed

            for owner, field_name in _iter_assignment_targets(cue, normalized_path):
                current_value = _lookup_member(owner, field_name)
                if current_value is None:
                    changed = _assign_value(owner, field_name, parsed_value) or changed
                elif isinstance(current_value, list):
                    current_value.append(parsed_value)
                    changed = True
                else:
                    logger.warning("Cannot add value to non-list field '%s'", normalized_path)
            return changed

        return add_values

    logger.warning("Unsupported overwrite operation '%s'", operation)
    return None


def _compile_filters(rules: list[dict[str, Any]]) -> list[FilterClosure]:
    compiled: list[FilterClosure] = []
    for rule in rules:
        try:
            filter_rule = _compile_filter_rule(rule)
        except Exception as error:
            logger.warning("Skipping invalid filter rule %r: %s", rule, error)
            continue
        if filter_rule is not None:
            compiled.append(filter_rule)
    return compiled


def _compile_overwrites(rules: list[dict[str, Any]]) -> list[OverwriteClosure]:
    compiled: list[OverwriteClosure] = []
    for rule in rules:
        try:
            overwrite_rule = _compile_overwrite_rule(rule)
        except Exception as error:
            logger.warning("Skipping invalid overwrite rule %r: %s", rule, error)
            continue
        if overwrite_rule is not None:
            compiled.append(overwrite_rule)
    return compiled


def _legacy_filter_condition_to_expression(key: str, expected: Any) -> str:
    if key.endswith("_in"):
        field = key[:-3]
        return f"{field} in {_format_condition_value(expected)}"
    if key.endswith("_not_in"):
        field = key[:-7]
        return f"{field} not in {_format_condition_value(expected)}"
    if key.endswith("_eq"):
        field = key[:-3]
        return f"{field} == {_format_condition_value(expected)}"
    if key.endswith("_ne"):
        field = key[:-3]
        return f"{field} != {_format_condition_value(expected)}"
    return f"{key} == {_format_condition_value(expected)}"


def _normalize_filters(profile: dict[str, Any]) -> list[dict[str, Any]]:
    filters = profile.get("filters")
    if isinstance(filters, list):
        return filters

    legacy_filter = profile.get("filter", {})
    if not isinstance(legacy_filter, dict):
        return []

    normalized: list[dict[str, Any]] = []

    for command_type in legacy_filter.get("command_types", []):
        normalized.append(
            {
                "field": "command_name",
                "condition": f"== {_format_condition_value(str(command_type).strip().lower())}",
            }
        )

    time_signal = legacy_filter.get("time_signal", {})
    if isinstance(time_signal, dict):
        for descriptor_filter in time_signal.get("descriptor_filters", []):
            if not isinstance(descriptor_filter, dict):
                continue
            clauses = [
                _legacy_filter_condition_to_expression(key, value)
                for key, value in descriptor_filter.items()
            ]
            normalized.append(
                {
                    "field": "descriptors",
                    "condition": " & ".join(clauses),
                }
            )

    return normalized


def _normalize_overwrites(profile: dict[str, Any]) -> list[dict[str, Any]]:
    overwrites = profile.get("overwrites")
    if isinstance(overwrites, list):
        return overwrites

    legacy_overwrite = profile.get("overwrite", {})
    if not isinstance(legacy_overwrite, dict):
        return []

    normalized: list[dict[str, Any]] = []
    segmentation_type_id = legacy_overwrite.get("segmentation_type_id")
    if segmentation_type_id is not None:
        normalized.append(
            {
                "op": "update",
                "field": "descriptors",
                "condition": "segmentation_type_id != null",
                "value": segmentation_type_id,
            }
        )
    return normalized


def load_profile(profile_path: str) -> Profile:
    path = Path(profile_path)
    if not path.exists():
        logger.warning(f"Profile {profile_path} does not exists. Passthrough everything")
        return Profile(path="default.json")

    with path.open("r", encoding="utf-8") as profile_file:
        profile = json.load(profile_file)

    raw_filters = _normalize_filters(profile)
    raw_overwrites = _normalize_overwrites(profile)
    return Profile(
        path=profile_path,
        filters=_compile_filters(raw_filters),
        overwrites=_compile_overwrites(raw_overwrites),
        raw_filters=raw_filters,
        raw_overwrites=raw_overwrites,
    )
