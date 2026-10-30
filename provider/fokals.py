from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools import fokals_api


class FokalsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        key = str(credentials.get("fokals_api_key") or "").strip()
        if not key:
            raise ToolProviderCredentialValidationError("A Fokals key is needed.")
        try:
            fokals_api.check_key(key)
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e)) from e
