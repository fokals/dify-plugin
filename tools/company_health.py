"""Company health: POST https://api.fokals.com/v1/company_health. Written by scripts/generate.py."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import fokals_api

READINGS = {"companies": "list", "weeks": "whole"}


class CompanyHealthTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from fokals_api.answer(self, "company_health", tool_parameters, READINGS)
