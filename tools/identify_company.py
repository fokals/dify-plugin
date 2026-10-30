"""Which company is meant: POST https://api.fokals.com/v1/identify_company. Written by scripts/generate.py."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import fokals_api

READINGS = {}


class IdentifyCompanyTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from fokals_api.answer(self, "identify_company", tool_parameters, READINGS)
