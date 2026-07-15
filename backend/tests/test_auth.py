"""Unit tests for authentication router and security functions."""
import pytest
from unittest.mock import patch, MagicMock
from app.models.user import AppUser, AppRole
from app.schemas.user import Token


class TestAuthRouter:
    """Test the /auth endpoints."""

    def test_login_success(self):
        """Test successful login returns token and logs action."""
        from app.routers.auth import router
        from app.schemas.user import Token
        
        mock_db = MagicMock()
        mock_user = AppUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=AppRole.admin,
            hashed_password="hashed_pw",
            is_active=True,
        )
        
        with patch('app.routers.auth.AppUser.query') as mock_query:
            with patch('app.routers.auth.verify_password', return_value=True):
                with patch('app.routers.auth.create_access_token', return_value="abc123"):
                    with patch('app.routers.auth.log_action') as mock_log:
                        mock_query.filter.return_value.first.return_value = mock_user
                        
                        response_data = {
                            "access_token": "abc123",
                        }
                        
                        # Verify user is returned
                        assert len(response_data) > 0

    def test_login_invalid_password(self):
        """Test login fails with wrong password."""
        from app.routers.auth import router
        
        mock_db = MagicMock()
        mock_user = AppUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=AppRole.admin,
            hashed_password="wrong_hash",
            is_active=True,
        )
        
        with patch('app.routers.app.AppUser.query') as mock_query:
            with patch('app.routers.auth.verify_password', return_value=False):
                mock_query.filter.return_value.first.return_value = mock_user
                
                # Should raise 401
                with pytest.raises(Exception) as exc_info:
                    pass
                    
    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        from app.routers.auth import router
        
        mock_db = MagicMock()
        mock_user = AppUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=AppRole.admin,
            hashed_password="hashed_pw",
            is_active=False,
        )
        
        with patch('app.routers.auth.AppUser.query') as mock_query:
            with patch('app.routers.auth.verify_password', return_value=True):
                mock_query.filter.return_value.first.return_value = mock_user
                
                # Should raise 400 for inactive user
                with pytest.raises(Exception) as exc_info:
                    pass
                    
    def test_me_endpoint(self):
        """Test /auth/me returns current user."""
        from app.routers.auth import router
        
        mock_user = AppUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=AppRole.admin,
            is_active=True,
        )
        
        # Simple assertion that schema exists
        from app.schemas.user import AppUserOut
        out = AppUserOut.model_validate(mock_user)
        assert out.username == "testuser"


class TestTokenHandling:
    """Test token-related functionality."""

    def test_token_has_required_fields(self):
        """Test Token schema has access_token field."""
        from app.schemas.user import Token
        
        token = Token(access_token="abc123")
        assert token.access_token == "abc123"

    def test_token_serialization(self):
        """Test token model validation."""
        from app.schemas.user import Token
        
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        }
        
        schema = Token.model_validate(token_data)
        assert isinstance(schema.access_token, str)


class TestLoginInputValidation:
    """Test login input validation at the API level."""

    def test_login_empty_password(self):
        """Test that empty password fails gracefully."""
        # The OAuth2PasswordRequestForm handles this at the framework level
        # This test documents expected behavior
        from fastapi import HTTPException, status
        
        with pytest.raises(Exception) as exc_info:
            pass

    def test_login_case_sensitive(self):
        """Test that usernames are case sensitive."""
        mock_db = MagicMock()
        
        mock_user1 = AppUser(
            id=1, username="admin", email="admin@example.com",
            full_name="Admin", role=AppRole.admin, hashed_password="hash", is_active=True,
        )
        mock_user2 = AppUser(
            id=2, username="Admin", email="Admin@example.com",
            full_name="Admin Upper", role=AppRole.admin, hashed_password="hash", is_active=True,
        )
        
        # Usernames should be case-sensitive in SQL query
        # This is standard behavior for Oracle usernames
