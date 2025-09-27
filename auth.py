import sqlite3
from typing import Optional

class User:
    def __init__(self, user_data: dict):
        self.first_name = user_data['first_name']
        self.last_name = user_data['last_name']
        self.username = user_data['username']
        self.email = user_data['email']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"


class UserAuthenticator:
    def __init__(self, db_path: str = "task_management.db"):
        self.db_path = db_path

    def authenticate(self, first_name: str, last_name: str, email: str, username: str) -> Optional[User]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM users 
                WHERE first_name = ? AND last_name = ? AND email = ? AND username = ?
                AND is_active = TRUE
            ''', (first_name, last_name, email, username))

            user_row = cursor.fetchone()

            if user_row:
                user_data = dict(user_row)
                user = User(user_data)
                print(f"Пользователь найден: {first_name} {last_name} ({username})")
                return user
            else:
                print(f"Пользователь не найден: {first_name} {last_name} ({username})")
                return None


def authentication(bdway):
    print("Идентифицируйте себя, введя: имя, фамилию, email и username")

    first_name = input("Имя: ").strip()
    last_name = input("Фамилия: ").strip()
    email = input("Email: ").strip()
    username = input("Username: ").strip()

    authenticator = UserAuthenticator(bdway)
    user = authenticator.authenticate(first_name, last_name, email, username)

    if(user == None):
        print("проверьте данные")
        return None
    else:
        return user