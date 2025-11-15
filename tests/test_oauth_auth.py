"""
Test OAuth 2.0 Authentication Flow
SPEC-AI-FACIL-001 Phase 1: OAuth Authentication
"""

import pytest
from unittest.mock import Mock, patch
import time


class TestOAuthHandler:
    """Tests for OAuth 2.0 authentication handler"""

    @pytest.fixture
    def oauth_handler(self):
        """Create OAuthHandler instance for testing"""
        from src.auth.oauth_handler import OAuthHandler
        return OAuthHandler(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8080/auth/callback"
        )

    def test_oauth_handler_initialization(self, oauth_handler):
        """Test OAuth handler initializes with credentials"""
        from src.auth.oauth_handler import OAuthHandler
        assert oauth_handler.client_id == "test-client-id"
        assert oauth_handler.client_secret == "test-client-secret"
        assert oauth_handler.redirect_uri == "http://localhost:8080/auth/callback"

    def test_generate_auth_url(self, oauth_handler):
        """Test authorization URL generation for OAuth consent flow"""
        auth_url = oauth_handler.get_auth_url(
            scope=["https://www.googleapis.com/auth/drive.readonly"]
        )
        assert "client_id=test-client-id" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=" in auth_url

    def test_exchange_code_for_token(self, oauth_handler):
        """Test exchanging authorization code for access token"""
        with patch('src.auth.oauth_handler.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
            mock_post.return_value = mock_response

            result = oauth_handler.exchange_code_for_token("test-auth-code")

            assert result["access_token"] == "test-access-token"
            assert result["refresh_token"] == "test-refresh-token"

    def test_token_encryption_decryption(self, oauth_handler):
        """Test encrypted storage of OAuth refresh tokens (AES-256)"""
        # Test with encryption enabled
        from src.auth.oauth_handler import OAuthHandler
        oauth_with_cipher = OAuthHandler(
            client_id="test",
            client_secret="test",
            redirect_uri="http://localhost/callback",
            encryption_key="test-encryption-key"
        )
        original_token = "test-refresh-token-secret"
        encrypted = oauth_with_cipher.encrypt_token(original_token)
        assert encrypted != original_token
        decrypted = oauth_with_cipher.decrypt_token(encrypted)
        assert decrypted == original_token

    def test_token_storage(self, oauth_handler, tmp_path):
        """Test secure storage of tokens to disk"""
        oauth_handler.token_storage_path = str(tmp_path / "tokens.json")
        tokens = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": int(time.time()) + 3600
        }
        oauth_handler.save_tokens(tokens)
        loaded_tokens = oauth_handler.load_tokens()
        assert loaded_tokens["access_token"] == "access-token"

    def test_is_token_expired(self, oauth_handler):
        """Test token expiration detection"""
        oauth_handler.token_expiry = time.time() - 100
        assert oauth_handler.is_token_expired() is True
        oauth_handler.token_expiry = time.time() + 3600
        assert oauth_handler.is_token_expired() is False

    def test_get_required_scopes(self, oauth_handler):
        """Test OAuth scopes for Drive and Docs API access"""
        scopes = oauth_handler.get_required_scopes()
        assert "https://www.googleapis.com/auth/drive.readonly" in scopes
        assert "https://www.googleapis.com/auth/documents" in scopes
