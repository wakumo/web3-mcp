"""
Authentication module for Ankr API
"""

import os
from typing import Optional

from ankr import AnkrWeb3


class AnkrAuth:
    """Authentication handler for Ankr API"""

    def __init__(self, endpoint: Optional[str] = None, private_key: Optional[str] = None):
        """
        Initialize Ankr authentication

        Args:
            endpoint: Ankr RPC endpoint URL (optional, SDK uses default, currently unused)
            private_key: API key for authentication (defaults to env var ANKR_PRIVATE_KEY)
        """
        # Try private_key parameter first, then environment variables in order of preference
        self.private_key = (
            private_key
            or os.environ.get("ANKR_PRIVATE_KEY")
            or os.environ.get("ANKR_API_KEY")
            or os.environ.get("DOTENV_PRIVATE_KEY_DEVIN")
        )

        if not self.private_key:
            raise ValueError("Ankr API key not provided. Set ANKR_PRIVATE_KEY environment variable.")

        self._client = None

    @property
    def client(self) -> AnkrWeb3:
        """Return authenticated Ankr client"""
        if not self._client:
            self._client = AnkrWeb3(api_key=self.private_key)
        return self._client
