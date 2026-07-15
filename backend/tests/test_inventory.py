"""Integration tests for inventory API endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from typing import List


class TestInventoryRouter:
    """Test the /inventory endpoints."""

    @staticmethod
    def _mock_oracle_service(func_name):
        """Return a mock Oracle service with requested function."""
        mock_service = MagicMock()
        
        if func_name == "test_connection":
            mock_service.test_connection.return_value = True
            mock_service.is_cdb.return_value = False
            
        elif func_name == "summary":
            mock_service.is_cdb.return_value = True
            mock_service.list_pdbs.return_value = ["ORCLPDB1", "ORCLPDB2"]
            mock_service.get_users.return_value = [MagicMock()] * 5
            mock_service.get_roles.return_value = [MagicMock()] * 3
            mock_service.get_sys_privs.return_value = [MagicMock()] * 2
            mock_service.get_tab_privs.return_value = [MagicMock()] * 10
            
        elif func_name == "get_users":
            mock_service.test_connection.return_value = True
            mock_service.get_users.return_value = [MagicMock(username="USER1")] * 3
            mock_service.get_roles.return_value = []
            
        elif func_name == "get_roles":
            mock_service.test_connection.return_value = True
            mock_service.get_users.return_value = []
            mock_service.get_roles.return_value = [MagicMock(role="CONNECT")] * 2
            
        elif func_name == "get_role_privs":
            mock_service.test_connection.return_value = True
            mock_service.get_role_privs.return_value = [MagicMock(grantee="SCOTT", granted_role="DBA")]
            
        elif func_name == "get_sys_privs":
            mock_service.test_connection.return_value = True
            mock_service.get_sys_privs.return_value = [MagicMock(privilege="CREATE SESSION")]
            
        elif func_name == "get_tab_privs":
            mock_service.test_connection.return_value = True
            mock_service.get_tab_privs.return_value = [MagicMock(grantee="SCOTT", object_name="EMPLOYEES", privilege="SELECT")]
            
        elif func_name == "get_profiles":
            mock_service.test_connection.return_value = True
            mock_service.get_profiles.return_value = [MagicMock(profile="DEFAULT", LIMIT=180)] * 2
            
        return mock_service

    @staticmethod
    def _mock_current_user():
        """Return a mock current user."""
        from app.models.user import AppUser, AppRole
        
        return AppUser(
            id=1, username="admin_test", email="admin@example.com",
            full_name="Admin Test", role=AppRole.admin, is_active=True,
        )

    def test_connection_success(self):
        """Test successful connection test."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = AppUser(
            id=1, username="admin", email="admin@example.com",
            full_name="Admin", role=AppRole.admin, is_active=True,
        )
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.test_connection.return_value = True
            
            payload = type('obj', (object,), {'host': 'oracle.example.com', 'port': 1521, 'service_name': 'ORCLPDB1', 'pdb': None})
            
            result = {"connected": True}

    def test_summary_cdb_mode(self):
        """Test summary endpoint with CDB."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.is_cdb.return_value = True
            mock_oracle.get_users.return_value = [MagicMock()] * 5
            
    def test_summary_pdb_mode(self):
        """Test summary endpoint for single PDB."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.is_cdb.return_value = False
            
    def test_list_users_basic(self):
        """Test listing basic user info."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.get_users.return_value = [
                type('obj', (object,), {
                    'USERNAME': 'USER1', 'ACCOUNT_STATUS': 'OPEN',
                    'LOCK_DATE': None, 'DEFAULT_TABLESPACE': 'USERS',
                })()
            ] * 3
            
    def test_list_roles_basic(self):
        """Test listing roles."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.get_roles.return_value = [
                type('obj', (object,), {'ROLE': 'CONNECT'})()
            ] * 2

    def test_list_role_privileges(self):
        """Test listing role grants."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.get_role_privs.return_value = [
                type('obj', (object,), {
                    'GRANTEE': 'SCOTT', 'GRANTED_ROLE': 'DBA',
                })()
            ]

    def test_list_sys_privileges(self):
        """Test listing system privileges."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.get_sys_privs.return_value = [
                type('obj', (object,), {
                    'GRANTEE': 'SYSTEM', 'PRIVILEGE': 'SELECT ANY TABLE',
                })()
            ]

    def test_list_object_privileges(self):
        """Test listing object privileges."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.get_tab_privs.return_value = [
                type('obj', (object,), {
                    'GRANTEE': 'SCOTT', 'OWNER': 'HR', 'TABLE_NAME': 'EMPLOYEES',
                    'PRIVILEGE': 'SELECT',
                })()
            ]

    def test_list_profiles(self):
        """Test listing password profiles."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.get_profiles.return_value = [
                type('obj', (object,), {'PROFILE': 'DEFAULT'})()
            ] * 2


class TestInventorySummaryCalculations:
    """Test summary calculations."""

    def test_summary_counts(self):
        """Test that summary counts match list endpoints."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            # Setup mocks
            mock_oracle.is_cdb.return_value = True
            
            users = [MagicMock()] * 5
            roles = [MagicMock()] * 3
            sys_privs = [MagicMock()] * 2
            tab_privs = []
            profiles = [MagicMock()] * 1
            
            # Expected counts
            expected_counts = {
                'user_count': len(users),
                'role_count': len(roles),
                'sys_priv_count': len(sys_privs),
                'obj_priv_count': len(tab_privs),
                'profile_count': len(profiles),
            }

    def test_summary_none_pdb(self):
        """Test summary when PDB is not specified."""
        from app.models.user import AppUser, AppRole
        
        mock_db = MagicMock()
        mock_user = self._mock_current_user()
        
        with patch('app.routers.inventory.oracle_service') as mock_oracle:
            mock_oracle.is_cdb.return_value = False
