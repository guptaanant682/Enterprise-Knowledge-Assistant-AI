import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    verify_google_token,
    create_user_from_google
)
from models import User


class TestPasswordUtils:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing creates different hashes for same password."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "mypassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed)
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "mypassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert not verify_password(wrong_password, hashed)
    
    def test_verify_password_with_none_hash(self):
        """Test password verification with None hash returns None."""
        result = verify_password("password", None)
        assert result is None


class TestTokenUtils:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1
    
    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self):
        """Test verification of expired token."""
        with patch('auth_utils.datetime') as mock_datetime:
            # Mock datetime to create expired token
            mock_datetime.utcnow.return_value = Mock()
            mock_datetime.utcnow.return_value.timestamp.return_value = 0
            
            data = {"sub": "test@example.com"}
            token = create_access_token(data, expires_delta=timedelta(minutes=-1))
            
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            
            assert exc_info.value.status_code == 401


class TestGoogleAuth:
    """Test Google OAuth functionality."""
    
    @patch('auth_utils.google.oauth2.id_token.verify_oauth2_token')
    def test_verify_google_token_success(self, mock_verify):
        """Test successful Google token verification."""
        mock_verify.return_value = {
            'iss': 'accounts.google.com',
            'sub': '12345',
            'email': 'test@gmail.com',
            'name': 'Test User'
        }
        
        result = verify_google_token("valid_token")
        
        assert result['google_id'] == '12345'
        assert result['email'] == 'test@gmail.com'
        assert result['name'] == 'Test User'
    
    @patch('auth_utils.google.oauth2.id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_issuer(self, mock_verify):
        """Test Google token with invalid issuer."""
        mock_verify.return_value = {
            'iss': 'invalid.issuer.com',
            'sub': '12345',
            'email': 'test@gmail.com'
        }
        
        with pytest.raises(HTTPException) as exc_info:
            verify_google_token("invalid_token")
        
        assert exc_info.value.status_code == 400
        assert "Invalid token issuer" in str(exc_info.value.detail)
    
    @patch('auth_utils.google.oauth2.id_token.verify_oauth2_token')
    def test_verify_google_token_exception(self, mock_verify):
        """Test Google token verification with exception."""
        mock_verify.side_effect = Exception("Token verification failed")
        
        with pytest.raises(HTTPException) as exc_info:
            verify_google_token("invalid_token")
        
        assert exc_info.value.status_code == 400
        assert "Invalid Google token" in str(exc_info.value.detail)
    
    def test_create_user_from_google_new_user(self, client):
        """Test creating new user from Google OAuth."""
        db = next(override_get_db())
        
        google_info = {
            'google_id': '12345',
            'email': 'newuser@gmail.com',
            'name': 'New User'
        }
        
        user = create_user_from_google(db, google_info)
        
        assert user.email == 'newuser@gmail.com'
        assert user.name == 'New User'
        assert user.google_id == '12345'
        assert user.role == 'user'
    
    def test_create_user_from_google_existing_by_google_id(self, client):
        """Test updating existing user found by Google ID."""
        db = next(override_get_db())
        
        # Create existing user
        existing_user = User(
            email="old@gmail.com",
            name="Old Name",
            google_id="12345",
            department="Engineering"
        )
        db.add(existing_user)
        db.commit()
        
        google_info = {
            'google_id': '12345',
            'email': 'updated@gmail.com',
            'name': 'Updated Name'
        }
        
        user = create_user_from_google(db, google_info)
        
        assert user.email == 'updated@gmail.com'
        assert user.name == 'Updated Name'
        assert user.google_id == '12345'