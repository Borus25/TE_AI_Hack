import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
from typing import Union, Optional, List, Dict, Any


class DatabaseManager:
    def __init__(self, db_config: Dict[str, Any], use_sqlalchemy: bool = True):
        """
        Инициализация менеджера базы данных

        Args:
            db_config: Словарь с параметрами подключения
            use_sqlalchemy: Если True - использует SQLAlchemy, False - psycopg2
        """
        self.db_config = db_config
        self.use_sqlalchemy = use_sqlalchemy

        # Атрибуты для SQLAlchemy
        self.engine = None
        self.SessionLocal = None
        self.Base = declarative_base()

        # Атрибуты для psycopg2
        self.connection = None

        self._setup_logging()

    def _setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def create_connect(self):
        """Создание подключения к базе данных"""
        try:
            if self.use_sqlalchemy:
                self._create_sqlalchemy_connection()
            else:
                self._create_psycopg2_connection()

            self.logger.info("Database connection established successfully")

        except Exception as e:
            self.logger.error(f"Error creating database connection: {e}")
            raise

    def _create_sqlalchemy_connection(self):
        """Создание подключения через SQLAlchemy"""
        connection_string = self._create_connection_string()

        self.engine = create_engine(
            connection_string,
            poolclass=NullPool,
            echo=False,
            future=True
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def _create_psycopg2_connection(self):
        """Создание подключения через psycopg2"""
        self.connection = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            cursor_factory=RealDictCursor
        )

    def _create_connection_string(self) -> str:
        """Создание строки подключения"""
        return (f"postgresql://{self.db_config['user']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}"
                f"/{self.db_config['database']}")

    @contextmanager
    def get_cursor(self):
        """
        Контекстный менеджер для работы с курсором

        Returns:
            Для SQLAlchemy: SQLAlchemy session
            Для psycopg2: psycopg2 cursor
        """
        if self.use_sqlalchemy:
            yield from self._get_sqlalchemy_session()
        else:
            yield from self._get_psycopg2_cursor()

    def _get_sqlalchemy_session(self):
        """Контекстный менеджер для SQLAlchemy сессии"""
        if not self.engine:
            self.create_connect()

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"SQLAlchemy session error: {e}")
            raise
        finally:
            session.close()

    def _get_psycopg2_cursor(self):
        """Контекстный менеджер для psycopg2 курсора"""
        if not self.connection or self.connection.closed:
            self.create_connect()

        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Psycopg2 cursor error: {e}")
            raise
        finally:
            cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Union[List[Dict], int]:
        """
        Выполнение SQL запроса

        Args:
            query: SQL запрос
            params: Параметры для запроса

        Returns:
            Для SELECT: список результатов
            Для других запросов: количество затронутых строк
        """
        if self.use_sqlalchemy:
            return self._execute_sqlalchemy_query(query, params)
        else:
            return self._execute_psycopg2_query(query, params)

    def _execute_sqlalchemy_query(self, query: str, params: Optional[tuple] = None) -> Union[List[Dict], int]:
        """Выполнение запроса через SQLAlchemy"""
        with self.get_cursor() as session:
            result = session.execute(query, params or {})

            if query.strip().lower().startswith('select'):
                # Преобразуем результат в список словарей
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
            else:
                session.commit()
                return result.rowcount

    def _execute_psycopg2_query(self, query: str, params: Optional[tuple] = None) -> Union[List[Dict], int]:
        """Выполнение запроса через psycopg2"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())

            if query.strip().lower().startswith('select'):
                return cursor.fetchall()
            else:
                return cursor.rowcount

    def close_connect(self):
        """Закрытие подключения к базе данных"""
        try:
            if self.use_sqlalchemy:
                self._close_sqlalchemy_connection()
            else:
                self._close_psycopg2_connection()

            self.logger.info("Database connection closed successfully")

        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}")
            raise

    def _close_sqlalchemy_connection(self):
        """Закрытие SQLAlchemy подключения"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None

    def _close_psycopg2_connection(self):
        """Закрытие psycopg2 подключения"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> bool:
        """Тестирование подключения к базе данных"""
        try:
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute("SELECT version()")
                    version = result.scalar()
                    self.logger.info(f"Connected to: {version}")
            else:
                with self.get_cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()['version']
                    self.logger.info(f"Connected to: {version}")

            return True

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


# Пример использования
if __name__ == "__main__":
    # Конфигурация базы данных
    db_config = {
        'host': 'localhost',
        'port': 5434,
        'database': 'task_db',
        'user': 'postgres',
        'password': 'postgres'
    }

    # Тестирование SQLAlchemy режима
    print("=== Testing SQLAlchemy mode ===")
    db_sqlalchemy = DatabaseManager(db_config, use_sqlalchemy=True)

    try:
        db_sqlalchemy.create_connect()
        db_sqlalchemy.test_connection()

        # Пример выполнения запроса
        result = db_sqlalchemy.execute_query("SELECT version()")
        print(f"Database version: {result}")

    except Exception as e:
        print(f"SQLAlchemy error: {e}")
    finally:
        db_sqlalchemy.close_connect()

    print("\n=== Testing psycopg2 mode ===")
    # Тестирование psycopg2 режима
    db_psycopg2 = DatabaseManager(db_config, use_sqlalchemy=False)

    try:
        db_psycopg2.create_connect()
        db_psycopg2.test_connection()

        # Пример выполнения запроса
        result = db_psycopg2.execute_query("SELECT version()")
        print(f"Database version: {result}")

        # Пример с параметрами
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        )
        """
        db_psycopg2.execute_query(create_table_query)
        print("Table created successfully")

    except Exception as e:
        print(f"Psycopg2 error: {e}")
    finally:
        db_psycopg2.close_connect()