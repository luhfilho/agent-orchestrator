
import json
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')

def register_user(username, password):
    """Registers a new user."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

    with open(USERS_FILE, 'r+') as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            users = {}

        if username in users:
            return False, "Username already exists."
        
        users[username] = {'password': password}
        f.seek(0)
        json.dump(users, f, indent=4)
        return True, "User registered successfully."

def login_user(username, password):
    """Logs in a user."""
    if not os.path.exists(USERS_FILE):
        return False, "No users registered."

    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
        if username not in users or users[username]['password'] != password:
            return False, "Invalid username or password."
        
        return True, "Login successful."

