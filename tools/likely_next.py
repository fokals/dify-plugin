"""Likely next technologies: POST https://api.fokals.com/v1/likely_next. Written by scripts/generate.py."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import fokals_api

READINGS = {"companies": "list", "limit": "whole"}


class LikelyNextTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from fokals_api.answer(self, "likely_next", tool_parameters, READINGS)
