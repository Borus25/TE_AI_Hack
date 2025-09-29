from database import DatabaseManager
from typing import Optional



class User:
    def __init__(self, user_data: dict):
        self.first_name = user_data['first_name']
        self.last_name = user_data['last_name']
        self.username = user_data['username']
        self.email = user_data['email']
        self.is_active = user_data.get('is_active', True)

    def __str__(self):
        return (f"{self.first_name} {self.last_name}\n"
                f"username: {self.username}\n"
                f"email: {self.email}\n")


class UserAuthenticator:
    def __init__(self, db_config: dict = None):
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'task_db',
            'user': 'postgres',
            'password': 'postgres'
        }
        # Используем DatabaseManager с psycopg2 (use_sqlalchemy=False)
        self.db_manager = DatabaseManager(self.db_config, use_sqlalchemy=False)

    def authenticate(self, first_name: str, last_name: str, email: str, username: str) -> Optional[User]:
        try:
            # Создаем подключение через DatabaseManager
            self.db_manager.create_connect()

            # Выполняем запрос через execute_query
            query = '''
                SELECT * FROM users 
                WHERE first_name = %s AND last_name = %s AND email = %s AND username = %s
                AND is_active = TRUE
            '''
            params = (first_name, last_name, email, username)

            result = self.db_manager.execute_query(query, params)

            if result:
                # result уже содержит словарь благодаря RealDictCursor
                user_data = result[0]  # Берем первую запись
                user = User(user_data)
                print(f"Пользователь найден: {first_name} {last_name} ({username})")
                return user
            else:
                print(f"Пользователь не найден: {first_name} {last_name} ({username})")
                return None

        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return None
        finally:
            # Закрываем подключение
            if hasattr(self, 'db_manager'):
                self.db_manager.close_connect()

def authentication(db_config=None):
    print("Идентифицируйте себя, введя: имя, фамилию, email и username")

    first_name = input("Имя: ").strip()
    last_name = input("Фамилия: ").strip()
    email = input("Email: ").strip()
    username = input("Username: ").strip()

    authenticator = UserAuthenticator(db_config)

    # Используем основной метод authenticate
    user = authenticator.authenticate(first_name, last_name, email, username)

    if user is None:
        print("Проверьте данные")
        return None
    else:
        return user


if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': 5434,
        'database': 'task_db',
        'user': 'postgres',
        'password': 'postgres'
    }

    print("\n=== Аутентификация пользователя ===")
    user = authentication(db_config)

    if user:
        print(f"Добро пожаловать, {user}!")