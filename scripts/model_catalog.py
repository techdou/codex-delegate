#!/usr/bin/env python3
"""Model discovery and reasoning-profile helpers for the Codex delegation skill."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

REASONING_RANK = {
    "none": 0,
    "minimal": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "xhigh": 5,
    "max": 6,
    "ultra": 7,
}


def _effort_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("effort", "reasoningEffort", "reasoning_effort"):
            if isinstance(value.get(key), str):
                return value[key]
    return None


def _normalize_model(raw: dict[str, Any]) -> dict[str, Any]:
    model_id = raw.get("slug") or raw.get("model") or raw.get("id")
    efforts_raw = raw.get("supported_reasoning_levels")
    if efforts_raw is None:
        efforts_raw = raw.get("supportedReasoningEfforts")
    if efforts_raw is None:
        efforts_raw = raw.get("supported_reasoning_efforts")
    efforts: list[str] = []
    for item in efforts_raw or []:
        name = _effort_name(item)
        if name and name not in efforts:
            efforts.append(name)

    default_effort = (
        raw.get("default_reasoning_level")
        or raw.get("defaultReasoningEffort")
        or raw.get("default_reasoning_effort")
    )
    default_effort = _effort_name(default_effort) or (default_effort if isinstance(default_effort, str) else None)

    visible = raw.get("visibility") in (None, "list") and not bool(raw.get("hidden", False))
    if isinstance(raw.get("isVisible"), bool):
        visible = bool(raw["isVisible"])

    return {
        "id": model_id,
        "display_name": raw.get("display_name") or raw.get("displayName") or model_id,
        "description": raw.get("description") or "",
        "visible": visible,
        "is_default": bool(raw.get("isDefault") or raw.get("is_default", False)),
        "default_reasoning_effort": default_effort,
        "supported_reasoning_efforts": efforts,
        "input_modalities": raw.get("input_modalities") or raw.get("inputModalities") or [],
        "priority": raw.get("priority"),
        "model_specialty": raw.get("model_specialty") or raw.get("modelSpecialty"),
        "multi_agent_version": raw.get("multi_agent_version") or raw.get("multiAgentVersion"),
        "service_tiers": raw.get("service_tiers") or raw.get("serviceTiers") or [],
    }


def normalize_catalog(obj: Any) -> dict[str, Any]:
    models_raw: list[Any] = []
    if isinstance(obj, dict):
        if isinstance(obj.get("models"), list):
            models_raw = obj["models"]
        elif isinstance(obj.get("data"), list):
            models_raw = obj["data"]
        elif isinstance(obj.get("items"), list):
            models_raw = obj["items"]
    elif isinstance(obj, list):
        models_raw = obj

    models = [_normalize_model(x) for x in models_raw if isinstance(x, dict)]
    models = [m for m in models if m.get("id")]
    return {"source": "codex debug models", "models": models}


def fetch_catalog(cli: str, *, bundled: bool = False, timeout: int = 30) -> dict[str, Any]:
    cmd = [cli, "debug", "models"]
    if bundled:
        cmd.append("--bundled")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(detail or f"codex debug models exited with {proc.returncode}")
    try:
        obj = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("codex debug models did not return valid JSON") from exc
    data = normalize_catalog(obj)
    if not data["models"]:
        raise RuntimeError("codex debug models returned no recognizable models")
    data["bundled"] = bundled
    return data


def find_model(catalog: dict[str, Any], model_id: str | None) -> dict[str, Any] | None:
    if not model_id:
        defaults = [m for m in catalog.get("models", []) if m.get("is_default")]
        return defaults[0] if defaults else None
    for model in catalog.get("models", []):
        if model.get("id") == model_id:
            return model
    return None


def choose_reasoning(model: dict[str, Any] | None, profile: str) -> str | None:
    if not model:
        return None
    efforts = [x for x in model.get("supported_reasoning_efforts", []) if isinstance(x, str)]
    if not efforts:
        return None
    if profile == "balanced":
        default = model.get("default_reasoning_effort")
        return default if default in efforts else None
    ranked = [(REASONING_RANK[x], x) for x in efforts if x in REASONING_RANK]
    if not ranked:
        return None
    if profile == "fast":
        return min(ranked)[1]
    if profile == "deep":
        return max(ranked)[1]
    return None


def read_explicit_config(codex_home: Path) -> dict[str, Any]:
    config_path = codex_home / "config.toml"
    result: dict[str, Any] = {"path": str(config_path), "model": None, "reasoning_effort": None}
    if not config_path.is_file():
        return result
    try:
        import tomllib
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return result
    if isinstance(data, dict):
        if isinstance(data.get("model"), str):
            result["model"] = data["model"]
        if isinstance(data.get("model_reasoning_effort"), str):
            result["reasoning_effort"] = data["model_reasoning_effort"]
    return result


def probe_model(cli: str, cwd: Path, model: str, timeout: int = 60) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="codex-skill-probe-") as td:
        final = Path(td) / "final.txt"
        cmd = [
            cli,
            "--ask-for-approval",
            "never",
            "exec",
            "--model",
            model,
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--output-last-message",
            str(final),
            "Reply with exactly: OK",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd), stdin=subprocess.DEVNULL)
        result: dict[str, Any] = {"model": model, "available": False, "exit_code": proc.returncode}
        if proc.returncode != 0:
            result["error"] = (proc.stderr or proc.stdout).strip()
            return result
        text = final.read_text(encoding="utf-8").strip() if final.is_file() else ""
        result["available"] = bool(text)
        result["response"] = text
        return result
