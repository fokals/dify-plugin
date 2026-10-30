"""The plugin as Dify loads it, and what each kind of answer from the API becomes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest import mock

import pytest
import yaml
from dify_plugin import Tool, ToolProvider
from dify_plugin.core.utils.class_loader import load_single_subclass_from_source

from tools import fokals_api

ROOT = Path(__file__).resolve().parent.parent
PROVIDER = yaml.safe_load((ROOT / "provider" / "fokals.yaml").read_text(encoding="utf-8"))
MANIFEST = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))
TOOL_FILES = PROVIDER["tools"]
PARAM_TYPES = {"string", "number", "boolean", "select"}


def tool_class(path: str) -> type:
    return load_single_subclass_from_source(
        module_name=f"tools.{Path(path).stem}", script_path=str(ROOT / path), parent_type=Tool
    )


def test_the_manifest_and_provider_name_the_plugin_and_every_tool():
    assert MANIFEST["author"] == "fokals" and MANIFEST["name"] == "fokals"
    assert MANIFEST["version"] == MANIFEST["meta"]["version"] == fokals_api.VERSION
    assert MANIFEST["privacy"] == "PRIVACY.md" and (ROOT / "PRIVACY.md").is_file()
    assert (ROOT / "_assets" / MANIFEST["icon"]).is_file()
    assert len(TOOL_FILES) == 28
    provider = load_single_subclass_from_source(
        module_name="provider.fokals", script_path=str(ROOT / "provider" / "fokals.py"), parent_type=ToolProvider
    )
    assert provider.__name__ == "FokalsProvider"


@pytest.mark.parametrize("path", TOOL_FILES)
def test_each_tool_is_one_class_dify_can_load_with_parameters_it_knows(path):
    spec = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    assert spec["identity"]["name"] == Path(path).stem
    assert tool_class(spec["extra"]["python"]["source"]).__name__.endswith("Tool")
    assert 0 < len(spec["description"]["llm"]) <= 1024
    # Prices change: the plugin points to them and never states one.
    assert not re.search(r"\$\d", spec["description"]["llm"])
    for p in spec["parameters"]:
        assert p["type"] in PARAM_TYPES, (path, p["name"])
        assert p["form"] == "llm"


def test_no_word_reads_as_moving_money():
    # The Marketplace sends a plugin that speaks of payments or transfers to extra review.
    banned = re.compile(
        r"\b(payments?|checkout|charge[sd]?|refunds?|payouts?|transactions?|withdraw\w*|deposits?|transfer\s+(funds?|money))\b",
        re.I,
    )
    for path in ["README.md", "PRIVACY.md", "manifest.yaml", "provider/fokals.yaml", "provider/fokals.py", "main.py"]:
        assert not banned.search((ROOT / path).read_text(encoding="utf-8")), path
    for path in (ROOT / "tools").glob("*.*"):
        assert not banned.search(path.read_text(encoding="utf-8")), path.name


def test_arguments_are_read_back_as_the_api_takes_them():
    body = fokals_api.read_back(
        {
            "companies": "stripe.com, shopify.com\nhubspot.com",
            "customers": "notion.so, figma.com",
            "limit": 10.0,
            "max_usd": 0.5,
            "hiring": True,
            "country": "",
            "industry": None,
        },
        {"companies": "list", "customers": "records", "limit": "whole"},
    )
    assert body == {
        "companies": ["stripe.com", "shopify.com", "hubspot.com"],
        "customers": [{"company": "notion.so"}, {"company": "figma.com"}],
        "limit": 10,
        "max_usd": 0.5,
        "hiring": True,
    }
    as_json = fokals_api.read_back(
        {"customers": '[{"company": "notion.so", "bought_on": "2026-09-15"}]'}, {"customers": "records"}
    )
    assert as_json == {"customers": [{"company": "notion.so", "bought_on": "2026-09-15"}]}


class Response:
    def __init__(self, status: int, body: object):
        self.status_code = status
        self._body = body

    def json(self):
        if isinstance(self._body, str):
            raise ValueError("not json")
        return self._body


def run(cls_path: str, params: dict, status: int, body: object):
    cls = tool_class(cls_path)
    tool = cls.from_credentials({"fokals_api_key": "test-key"})
    with mock.patch.object(fokals_api.requests, "post", return_value=Response(status, body)) as post:
        messages = list(tool.invoke(tool_parameters=params))
    return messages, post


def test_an_answer_is_text_for_an_agent_and_json_for_a_workflow():
    answer = {"message": "Found 2 companies.", "data": {"companies": [{"website": "acme.com"}]}}
    messages, post = run("tools/find_companies.py", {"technology": "HubSpot", "limit": 10.0}, 200, answer)
    url = post.call_args.args[0]
    sent = post.call_args.kwargs
    assert url == "https://api.fokals.com/v1/find_companies"
    assert sent["headers"]["Authorization"] == "Bearer test-key"
    assert sent["headers"]["User-Agent"] == f"fokals-dify/{fokals_api.VERSION}"
    assert sent["json"] == {"technology": "HubSpot", "limit": 10}
    texts = [m for m in messages if m.type.value == "text"]
    jsons = [m for m in messages if m.type.value == "json"]
    assert texts[0].message.text.startswith("Found 2 companies.\n")
    assert json.loads(texts[0].message.text.split("\n", 1)[1]) == answer["data"]
    assert jsons[0].message.json_object == {"message": "Found 2 companies.", "data": answer["data"]}


def test_a_price_to_agree_to_is_an_answer_and_a_refusal_is_an_error():
    price = {"error": {"code": "payment_required", "message": "This call costs $4.00. Call again with max_usd.", "cost_usd": 4}}
    messages, _ = run("tools/find_companies.py", {"technology": "HubSpot"}, 402, price)
    jsons = [m for m in messages if m.type.value == "json"]
    assert jsons[0].message.json_object["needs_approval"] is True
    assert jsons[0].message.json_object["details"]["cost_usd"] == 4
    with pytest.raises(Exception, match="That key or sign-in is not valid."):
        run("tools/company_profile.py", {"company": "x"}, 401, {"error": {"message": "That key or sign-in is not valid."}})
    with pytest.raises(Exception, match="Fokals answered 502."):
        run("tools/company_profile.py", {"company": "x"}, 502, "Bad gateway")


def test_a_key_is_checked_by_reading_its_account():
    with mock.patch.object(fokals_api.requests, "get", return_value=Response(200, {"data": {}})) as get:
        fokals_api.check_key("good")
    assert get.call_args.args[0] == "https://api.fokals.com/v1/account"
    with mock.patch.object(fokals_api.requests, "get", return_value=Response(401, {"error": {"message": "Not valid."}})):
        with pytest.raises(fokals_api.FokalsError, match="Not valid."):
            fokals_api.check_key("bad")
