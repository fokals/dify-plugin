"""Find companies by signal: POST https://api.fokals.com/v1/find_companies. Written by scripts/generate.py."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import fokals_api

READINGS = {"agent_ready_min": "whole", "agent_ready_part_min": "whole", "project_days": "whole", "limit": "whole"}


class FindCompaniesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from fokals_api.answer(self, "find_companies", tool_parameters, READINGS)
