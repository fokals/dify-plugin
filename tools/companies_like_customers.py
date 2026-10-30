"""Companies like my customers: POST https://api.fokals.com/v1/companies_like_customers. Written by scripts/generate.py."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import fokals_api

READINGS = {"customers": "records", "limit": "whole"}


class CompaniesLikeCustomersTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from fokals_api.answer(self, "companies_like_customers", tool_parameters, READINGS)
