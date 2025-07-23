
import json
from typing import Optional
from agent_orchestrator.models.user import User

class LoginManager:
    """Manages user login and registration"""

    def __init__(self, storage_path: str = "data/users.json"):
        self.storage_path = storage_path
        self.users = self._load_users()

    def _load_users(self) -> dict[str, User]:
        try:
            with open(self.storage_path, "r") as f:
                users_data = json.load(f)
            return {username: User(**data) for username, data in users_data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_users(self):
        with open(self.storage_path, "w") as f:
            json.dump({username: user.dict() for username, user in self.users.items()}, f, indent=4)

    def register(self, user: User) -> bool:
        """Registers a new user"""
        if user.username in self.users:
            return False  # User already exists
        self.users[user.username] = user
        self._save_users()
        return True

    def login(self, username: str, password: str) -> Optional[User]:
        """Logs in a user"""
        user = self.users.get(username)
        if user and user.password == password:
            return user
        return None
