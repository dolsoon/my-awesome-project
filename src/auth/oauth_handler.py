"""
OAuth 2.0 Authentication Handler
Handles Google Workspace OAuth flow with token encryption and refresh
"""

import json
import time
import base64
import requests
from typing import Dict, Optional, List
from cryptography.fernet import Fernet
import os


class OAuthHandler:
    """Manages OAuth 2.0 authentication with Google Workspace APIs"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        encryption_key: Optional[str] = None
    ):
        """Initialize OAuth handler with credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[float] = None
        self.token_storage_path: str = "tokens.json"

        # Setup encryption for token storage
        if encryption_key:
            self.cipher = self._create_cipher(encryption_key)
        else:
            self.cipher = None

    def _create_cipher(self, password: str) -> Fernet:
        """Create Fernet cipher from password"""
        # Simple encryption key derivation
        key_bytes = (password * 32)[:32].encode('utf-8')
        key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(key)

    def get_auth_url(self, scope: List[str]) -> str:
        """Generate Google OAuth consent screen URL"""
        scope_str = " ".join(scope)
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"scope={scope_str}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return auth_url

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, str]:
        """Exchange authorization code for access and refresh tokens"""
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": authorization_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        tokens = response.json()

        self.access_token = tokens["access_token"]
        self.refresh_token = tokens.get("refresh_token")
        self.token_expiry = time.time() + tokens.get("expires_in", 3600)

        return tokens

    def refresh_token_if_needed(self) -> str:
        """Refresh access token if expired"""
        if self.is_token_expired():
            return self.refresh_token_now()
        return self.access_token

    def refresh_token_now(self) -> str:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        tokens = response.json()

        self.access_token = tokens["access_token"]
        self.token_expiry = time.time() + tokens.get("expires_in", 3600)

        return self.access_token

    def encrypt_token(self, token: str) -> str:
        """Encrypt token for storage"""
        if not self.cipher:
            return token
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt stored token"""
        if not self.cipher:
            return encrypted_token
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    def save_tokens(self, tokens: Dict) -> None:
        """Save tokens to encrypted storage"""
        token_data = {
            "access_token": self.encrypt_token(tokens.get("access_token", "")),
            "refresh_token": self.encrypt_token(tokens.get("refresh_token", "")),
            "expires_at": tokens.get("expires_at", time.time() + 3600),
        }
        with open(self.token_storage_path, "w") as f:
            json.dump(token_data, f)

    def load_tokens(self) -> Dict:
        """Load tokens from encrypted storage"""
        if not os.path.exists(self.token_storage_path):
            return {}

        with open(self.token_storage_path, "r") as f:
            token_data = json.load(f)

        return {
            "access_token": self.decrypt_token(token_data.get("access_token", "")),
            "refresh_token": self.decrypt_token(token_data.get("refresh_token", "")),
            "expires_at": token_data.get("expires_at"),
        }

    def is_token_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.token_expiry:
            return True
        return time.time() >= self.token_expiry - 300  # Refresh 5 min before expiry

    def get_valid_token(self) -> str:
        """Get valid access token, refreshing if needed"""
        return self.refresh_token_if_needed()

    def get_required_scopes(self) -> List[str]:
        """Get required OAuth scopes for Drive and Docs APIs"""
        return [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/documents",
        ]

    def validate_token_response(self, token_dict: Dict) -> bool:
        """Validate token response structure"""
        required_fields = ["access_token", "refresh_token", "expires_in"]
        return all(field in token_dict for field in required_fields)
