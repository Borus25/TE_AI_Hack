import psycopg2
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
    def __init__(self, db_config: dict = None):
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'task_db',
            'user': 'postgres',
            'password': 'postgres'
        }

    def authenticate(self, first_name: str, last_name: str, email: str, username: str) -> Optional[User]:
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT * FROM users 
                        WHERE first_name = %s AND last_name = %s AND email = %s AND username = %s
                        AND is_active = TRUE
                    ''', (first_name, last_name, email, username))

                    user_row = cursor.fetchone()

                    if user_row:
                        colnames = [desc[0] for desc in cursor.description]
                        user_data = dict(zip(colnames, user_row))
                        user = User(user_data)
                        print(f"Пользователь найден: {first_name} {last_name} ({username})")
                        return user
                    else:
                        print(f"Пользователь не найден: {first_name} {last_name} ({username})")
                        return None

        except psycopg2.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return None


def authentication(db_config=None):
    print("Идентифицируйте себя, введя: имя, фамилию, email и username")

    first_name = input("Имя: ").strip()
    last_name = input("Фамилия: ").strip()
    email = input("Email: ").strip()
    username = input("Username: ").strip()

    authenticator = UserAuthenticator(db_config)
    user = authenticator.authenticate(first_name, last_name, email, username)

    if user is None:
        print("Проверьте данные")
        return None
    else:
        return user


if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'task_db',
        'user': 'postgres',
        'password': 'postgres'
    }

    user = authentication(db_config)
    if user:
        print(f"Успешная аутентификация: {user}")