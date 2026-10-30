"""One call to the Fokals API, shared by every tool of the plugin.

A tool's arguments arrive as Dify gives them (lists as text, numbers as floats); they are read
back into what the API takes and posted to https://api.fokals.com/v1/<endpoint> with the key
from the plugin's settings. The answer is handed back as text for an agent and as JSON for a
workflow. A call the account must agree to the price of comes back as an answer with that
price, not as an error.
"""

from __future__ import annotations

import json
import re
from collections.abc import Generator
from typing import Any

import requests

API = "https://api.fokals.com/v1"
VERSION = "0.0.1"
TIMEOUT = 60


class FokalsError(Exception):
    """The API refused a call, in its own words."""


def headers(key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"fokals-dify/{VERSION}",
    }


def key_of(tool: Any) -> str:
    key = str((tool.runtime.credentials or {}).get("fokals_api_key") or "").strip()
    if not key:
        raise FokalsError("No Fokals key is set. Add one in the plugin's settings.")
    return key


def read_back(params: dict[str, Any], readings: dict[str, str]) -> dict[str, Any]:
    """The arguments as the API takes them: empty ones left out, lists split, whole numbers whole."""
    body: dict[str, Any] = {}
    for name, value in params.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        how = readings.get(name)
        if how == "list":
            body[name] = [v.strip() for v in re.split(r"[,\n]", str(value)) if v.strip()]
        elif how == "records":
            text = str(value).strip()
            try:
                parsed = json.loads(text)
                body[name] = parsed if isinstance(parsed, list) else [parsed]
            except ValueError:
                body[name] = [{"company": v.strip()} for v in re.split(r"[,\n]", text) if v.strip()]
        elif how == "whole" and isinstance(value, float) and value.is_integer():
            body[name] = int(value)
        else:
            body[name] = value
    return body


def call(key: str, endpoint: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    response = requests.post(f"{API}/{endpoint}", headers=headers(key), json=body, timeout=TIMEOUT)
    try:
        parsed = response.json()
    except ValueError:
        parsed = {}
    return response.status_code, parsed if isinstance(parsed, dict) else {}


def answer(tool: Any, endpoint: str, params: dict[str, Any], readings: dict[str, str]) -> Generator[Any, None, None]:
    status, body = call(key_of(tool), endpoint, read_back(params, readings))
    if status == 200:
        message = str(body.get("message") or "").strip()
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        yield tool.create_text_message(f"{message}\n{json.dumps(data, ensure_ascii=False)}".strip())
        yield tool.create_json_message({"message": message, "data": data})
        return
    error = body.get("error") if isinstance(body.get("error"), dict) else {}
    message = str(error.get("message") or f"Fokals answered {status}.")
    if status == 402:
        # The price, and what makes the call run: for the agent to put to the person.
        details = {k: v for k, v in error.items() if k != "message"}
        yield tool.create_text_message(message)
        yield tool.create_json_message({"needs_approval": True, "message": message, "details": details})
        return
    raise FokalsError(message)


def check_key(key: str) -> None:
    """A key is good when the account it opens can be read."""
    response = requests.get(f"{API}/account", headers=headers(key), timeout=TIMEOUT)
    if response.status_code != 200:
        try:
            message = response.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = f"Fokals answered {response.status_code}."
        raise FokalsError(message)
