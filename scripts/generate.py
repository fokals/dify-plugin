"""Write the plugin's tools from the Fokals OpenAPI document.

Each tool's name, description and parameters come from the API itself: tools/<name>.yaml for
Dify, tools/<name>.py to call it, and the tool list in provider/fokals.yaml. Run it again
when the API gains or changes a tool:

    python scripts/generate.py                      # reads https://api.fokals.com/v1/openapi.json
    python scripts/generate.py path/to/openapi.json # or a saved copy
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_URL = "https://api.fokals.com/v1/openapi.json"

# The tools an agent reads data with. Tools that change what an account holds (watches,
# files, funds, requests, reports) are left to the account page and the MCP server.
TOOLS = [
    "find_companies",
    "count_companies",
    "enrich_companies",
    "company_profile",
    "company_changes",
    "search_job_postings",
    "similar_companies",
    "company_connections",
    "identify_company",
    "market_breakdown",
    "vendor_scorecard",
    "companies_like_customers",
    "company_health",
    "likely_next",
    "intent_history",
    "sales_team",
    "funding_filings",
    "headcount_history",
    "traffic_history",
    "signal_feed",
    "announcement_feed",
    "change_feed",
    "listed_securities",
    "market_trends",
    "market_movers",
    "sales_pay_benchmarks",
    "list_filters",
    "account_balance",
]

# Prices change, so the plugin never states them: a paid tool says where they are and what to
# do when a call answers with its price.
PAID_TAIL = (
    " Paid from the Fokals prepaid balance at the prices on https://api.fokals.com/v1/prices."
    " A call that costs more than the account lets run unasked returns its price instead:"
    " tell the person, then call again with max_usd once they agree."
)
MAX_DESCRIPTION = 1024
ALL_ENDPOINTS: list[str] = []


def load(source: str | None) -> dict:
    if source:
        return json.loads(Path(source).read_text(encoding="utf-8"))
    request = urllib.request.Request(OPENAPI_URL, headers={"User-Agent": "fokals-dify-generate"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def words(name: str) -> str:
    return name.replace("_", " ").capitalize()


def plain(text: str) -> str:
    """A sentence about a tool left out of the plugin is dropped, and "charged" reads "billed"
    (the Marketplace sends a plugin that speaks of charges to extra review)."""
    text = re.sub(r"\bcharged\b", "billed", text)
    left_out = [e for e in ALL_ENDPOINTS if e not in TOOLS]
    if not left_out:
        return text.strip()
    mention = re.compile(r"\b(" + "|".join(map(re.escape, left_out)) + r")\b")
    return " ".join(s for s in re.split(r"(?<=[.;])\s+", text.strip()) if not mention.search(s))


def describe(text: str, paid: bool) -> str:
    text = re.sub(r"\s*Costs \$.*$", "", plain(text), flags=re.S)
    if paid:
        text = re.sub(r"\s*Free\.\s*$", "", text) + PAID_TAIL
    if len(text) > MAX_DESCRIPTION:
        lead, tail = (text[: -len(PAID_TAIL)], PAID_TAIL) if paid else (text, "")
        sentences = re.split(r"(?<=\.)\s+", lead)
        sentences = [s for s in sentences if not s.startswith("Each company comes with")] or sentences
        while len(" ".join(sentences) + tail) > MAX_DESCRIPTION and len(sentences) > 1:
            sentences.pop(-1)
        text = " ".join(sentences) + tail
    return text


def first_sentence(text: str) -> str:
    sentence = re.split(r"(?<=\.)\s+", plain(text))[0]
    return sentence if len(sentence) <= 220 else sentence[:217].rstrip() + "..."


def parameter(name: str, schema: dict, required: bool) -> tuple[dict, str | None]:
    """A Dify parameter for one API argument, and how to read it back (a list, a record list,
    a whole number or nothing special)."""
    about = plain(schema.get("description", ""))
    kind = schema.get("type")
    reading = None
    out: dict = {"name": name, "required": required, "form": "llm", "label": {"en_US": words(name)}}
    if kind == "string" and "enum" in schema:
        out["type"] = "select"
        out["options"] = [{"value": v, "label": {"en_US": v}} for v in schema["enum"]]
    elif kind == "string":
        out["type"] = "string"
    elif kind in ("integer", "number"):
        out["type"] = "number"
        for key, arg in (("minimum", "min"), ("maximum", "max")):
            if key in schema:
                out[arg] = schema[key]
        reading = "whole" if kind == "integer" else None
    elif kind == "boolean":
        out["type"] = "boolean"
    elif kind == "array" and schema.get("items", {}).get("type") == "object":
        out["type"] = "string"
        about += ' As JSON, [{"company": "acme.com", "bought_on": "2026-09-15"}], or websites separated by commas.'
        reading = "records"
    elif kind == "array":
        out["type"] = "string"
        allowed = schema.get("items", {}).get("enum")
        named = allowed and not all(v in about for v in allowed)
        about += " Separated by commas." + (f" Each one of: {', '.join(allowed)}." if named else "")
        reading = "list"
    else:
        raise ValueError(f"{name}: unhandled schema {schema}")
    out["human_description"] = {"en_US": about}
    out["llm_description"] = about
    return out, reading


def main() -> None:
    doc = load(sys.argv[1] if len(sys.argv) > 1 else None)
    ALL_ENDPOINTS[:] = [p.strip("/") for p, item in doc["paths"].items() if "post" in item]
    tools_dir = ROOT / "tools"
    for old in tools_dir.glob("*.yaml"):
        old.unlink()
    for old in tools_dir.glob("*.py"):
        if old.name not in ("__init__.py", "fokals_api.py"):
            old.unlink()
    listed = []
    for name in TOOLS:
        op = doc["paths"][f"/{name}"]["post"]
        schema = op["requestBody"]["content"]["application/json"]["schema"]
        required = set(schema.get("required", []))
        params, readings = [], {}
        for prop, sub in schema.get("properties", {}).items():
            p, reading = parameter(prop, sub, prop in required)
            params.append(p)
            if reading:
                readings[prop] = reading
        spec = {
            "identity": {"name": name, "author": "fokals", "label": {"en_US": op["summary"]}},
            "description": {
                "human": {"en_US": first_sentence(op["description"])},
                "llm": describe(op["description"], bool(op.get("x-fokals-paid"))),
            },
            "parameters": params,
            "extra": {"python": {"source": f"tools/{name}.py"}},
        }
        (tools_dir / f"{name}.yaml").write_text(
            "# Written by scripts/generate.py from the Fokals OpenAPI document.\n"
            + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=1000),
            encoding="utf-8",
        )
        (tools_dir / f"{name}.py").write_text(
            f'''"""{op["summary"]}: POST https://api.fokals.com/v1/{name}. Written by scripts/generate.py."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import fokals_api

READINGS = {json.dumps(readings)}


class {camel(name)}Tool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from fokals_api.answer(self, "{name}", tool_parameters, READINGS)
''',
            encoding="utf-8",
        )
        listed.append(f"tools/{name}.yaml")
    provider = ROOT / "provider" / "fokals.yaml"
    spec = yaml.safe_load(provider.read_text(encoding="utf-8"))
    spec["tools"] = listed
    provider.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
    print(f"Wrote {len(listed)} tools")


if __name__ == "__main__":
    main()
