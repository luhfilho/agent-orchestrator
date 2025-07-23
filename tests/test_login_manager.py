
import unittest
from unittest.mock import patch, mock_open
from agent_orchestrator.auth.login_manager import LoginManager
from agent_orchestrator.models.user import User

class TestLoginManager(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"testuser": {"username": "testuser", "password": "password"}}')
    def test_login_success(self, mock_file):
        login_manager = LoginManager()
        user = login_manager.login("testuser", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")

    @patch("builtins.open", new_callable=mock_open, read_data='{"testuser": {"username": "testuser", "password": "password"}}')
    def test_login_failure(self, mock_file):
        login_manager = LoginManager()
        user = login_manager.login("testuser", "wrongpassword")
        self.assertIsNone(user)

    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    @patch("json.dump")
    def test_register_success(self, mock_json_dump, mock_file):
        login_manager = LoginManager()
        user = User(username="newuser", password="newpassword")
        result = login_manager.register(user)
        self.assertTrue(result)
        mock_json_dump.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data='{"testuser": {"username": "testuser", "password": "password"}}')
    def test_register_failure_user_exists(self, mock_file):
        login_manager = LoginManager()
        user = User(username="testuser", password="password")
        result = login_manager.register(user)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
