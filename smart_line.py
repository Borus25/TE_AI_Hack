import csv

from auth import User

import requests
import json
import os

from database import DatabaseManager

db_config = {
    'host': 'localhost',
    'port': 5434,
    'database': 'task_db',
    'user': 'postgres',
    'password': 'postgres'
}


def create_sql_plan(prompt: str, user: User):
    '''
        эта функция для того, чтобы составить список простых подзапросов на естественном языке и порядок их выполнения
        Для этого используется ИИ qwen2.5-vl-72b-instruct:free и запросы принимаются через url openrouter
    '''

    request = f'''
        Найти: {prompt}
        Структура базы данных:
            task_db structure:
            1. users(id, department_id, username,email, first_name, last_name, position, is_manager, is_active, created_at, 
                    updated_at)
            Indexes:
                "users_pkey" PRIMARY KEY, btree (id)
                "users_email_key" UNIQUE CONSTRAINT, btree (email)
                "users_username_key" UNIQUE CONSTRAINT, btree (username)
            2. companies(id, name, description, created_at, updated_at)
            Indexes:
                "companies_pkey" PRIMARY KEY, btree (id)
            3. departments(id, company_id, parent_department_id, name,description, created_at, updated_at)
            Indexes:
                "departments_pkey" PRIMARY KEY, btree (id)
            4. tasks(id, title, description, status, priority, assigned_user_id, assigned_department_id, created_by_user_id, 
                    due_date, start_date, completed_date, created_at,updated_at)
            Indexes:
                "tasks_pkey" PRIMARY KEY, btree (id)
            5. task_dependencies(id, task_id_1, task_id_2, created_at, created_by_user_id)
            Indexes:
                "task_dependencies_pkey" PRIMARY KEY, btree (id)
                "task_dependencies_task_id_1_task_id_2_key" UNIQUE CONSTRAINT, btree (task_id_1, task_id_2)
            6. task_history(id, task_id, changed_by_user_id, field_name, old_value, new_value, changed_at)
            Indexes:
                "task_history_pkey" PRIMARY KEY, btree (id)
            foreign_keys_relationship
                table_name     |      column_name       | foreign_table_name | foreign_column_name |              constraint_nam
            -------------------+------------------------+--------------------+---------------------+----------------------------
             departments       | company_id             | companies          | id                  | departments_company_id_fkey
             departments       | parent_department_id   | departments        | id                  | departments_parent_department_id_fkey
             task_dependencies | created_by_user_id     | users              | id                  | task_dependencies_created_by_user_id_fkey
             task_dependencies | task_id_1              | tasks              | id                  | task_dependencies_task_id_1_fkey
             task_dependencies | task_id_2              | tasks              | id                  | task_dependencies_task_id_2_fkey
             task_history      | changed_by_user_id     | users              | id                  | task_history_changed_by_user_id_fkey
             task_history      | task_id                | tasks              | id                  | task_history_task_id_fkey
             tasks             | assigned_department_id | departments        | id                  | tasks_assigned_department_id_fkey
             tasks             | assigned_user_id       | users              | id                  | tasks_assigned_user_id_fkey
             tasks             | created_by_user_id     | users              | id                  | tasks_created_by_user_id_fkey
             users             | department_id          | departments        | id                  | users_department_id_fkey
             
        Пользователь, который написал этот запрос:
            {user}
        
        Задача: написать только список подзапросов (на естественном языке, без SQL) и порядок их выполнения
                для их объединения в один "основной" SQL запрос (ничего более, никаких пояснений, ничего)
        
        Ожидаемый формат ответа:
            Подзапрос 1:
                Получить необходимые данные из таблицы X
                Применить базовые фильтры
                Выбрать ключевые поля
            Подзапрос 2:
                Получить связанные данные из таблицы Y
                Применить дополнительные условия
                Выбрать нужные поля
            Подзапрос 3:
                Получить дополнительные данные из таблицы Z
                Применить специфические фильтры
                Выбрать требуемые поля
            Порядок выполнения:
                Выполнить Подзапрос 1
                Использовать результаты Подзапроса 1 в Подзапросе 2
                Объединить результаты с Подзапросом 3
                Применить финальные условия
            Схема объединения:
                Соединить результаты всех подзапросов
                Указать условия объединения
                Выбрать итоговые поля
    '''

    # Настройка аутентификации
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = os.environ['LLAMA_API_KEY']
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Подготовка сообщений
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "user", "content": request}
        ],
        "max_tokens": 200
    }

    # Выполнение запроса
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))

    # Handle the response
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        print(f"Error: Request failed with status {response.status_code}")
        return ''


def make_sql_query(prompt: str, sql_plan: str, user: User) -> str:
    '''
        эта функция для создания запроса SQL из списка подзапросов, которые были созданы в функции create_sql_plan
        Для этого используется ИИ deepseek/deepseek-r1-0528:free и запросы принимаются через url openrouter
    '''
    request = f'''
            Найти: {prompt}
            Структура базы данных:
                task_db structure:
                1. users(id, department_id, username,email, first_name, last_name, position, is_manager, is_active, created_at, 
                        updated_at)
                Indexes:
                    "users_pkey" PRIMARY KEY, btree (id)
                    "users_email_key" UNIQUE CONSTRAINT, btree (email)
                    "users_username_key" UNIQUE CONSTRAINT, btree (username)
                2. companies(id, name, description, created_at, updated_at)
                Indexes:
                    "companies_pkey" PRIMARY KEY, btree (id)
                3. departments(id, company_id, parent_department_id, name,description, created_at, updated_at)
                Indexes:
                    "departments_pkey" PRIMARY KEY, btree (id)
                4. tasks(id, title, description, status, priority, assigned_user_id, assigned_department_id, created_by_user_id, 
                        due_date, start_date, completed_date, created_at,updated_at)
                Indexes:
                    "tasks_pkey" PRIMARY KEY, btree (id)
                5. task_dependencies(id, task_id_1, task_id_2, created_at, created_by_user_id)
                Indexes:
                    "task_dependencies_pkey" PRIMARY KEY, btree (id)
                    "task_dependencies_task_id_1_task_id_2_key" UNIQUE CONSTRAINT, btree (task_id_1, task_id_2)
                6. task_history(id, task_id, changed_by_user_id, field_name, old_value, new_value, changed_at)
                Indexes:
                    "task_history_pkey" PRIMARY KEY, btree (id)
                foreign_keys_relationship
                    table_name     |      column_name       | foreign_table_name | foreign_column_name |              constraint_nam
                -------------------+------------------------+--------------------+---------------------+----------------------------
                 departments       | company_id             | companies          | id                  | departments_company_id_fkey
                 departments       | parent_department_id   | departments        | id                  | departments_parent_department_id_fkey
                 task_dependencies | created_by_user_id     | users              | id                  | task_dependencies_created_by_user_id_fkey
                 task_dependencies | task_id_1              | tasks              | id                  | task_dependencies_task_id_1_fkey
                 task_dependencies | task_id_2              | tasks              | id                  | task_dependencies_task_id_2_fkey
                 task_history      | changed_by_user_id     | users              | id                  | task_history_changed_by_user_id_fkey
                 task_history      | task_id                | tasks              | id                  | task_history_task_id_fkey
                 tasks             | assigned_department_id | departments        | id                  | tasks_assigned_department_id_fkey
                 tasks             | assigned_user_id       | users              | id                  | tasks_assigned_user_id_fkey
                 tasks             | created_by_user_id     | users              | id                  | tasks_created_by_user_id_fkey
                 users             | department_id          | departments        | id                  | users_department_id_fkey

            Пользователь, который написал этот запрос:
                {user}

            Список подзапросов на естественном языке и их порядок:
                {sql_plan}
            
            Задача: имея структуру БД, данные текущего пользователся и список подзапросов, написать основной запрос SQL, нужные для изначального промпта.
                
            Ожидаемый формат ответа (без комментариев, ):
                SQL-запрос
        '''
    # Настройка аутентификации
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = os.environ['LLAMA_API_KEY']
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Подготовка сообщений
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "user", "content": request}
        ],
        "max_tokens": 400
    }

    # Выполнение запроса
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))

    # Handle the response
    if response.status_code == 200:
        result = response.json()
        print(result["choices"][0]["message"]["content"])
        return result["choices"][0]["message"]["content"]
    else:
        print(f"Error: Request failed with status {response.status_code}")
        return ''



def execute_prompt(prompt: str, user: User, csvfile: str = None) -> None:
    sql_plan = create_sql_plan(prompt, user)
    sql_query = make_sql_query(prompt, sql_plan, user)

    db_manager = DatabaseManager(db_config, use_sqlalchemy=False)

    if not sql_query[6:len(sql_query)-3]:
        print("Ничего не нашлось")
        return

    result = db_manager.execute_query(sql_query[6:len(sql_query)-3])

    if not result:
        print("Ничего не нашлось")
        return

    if csvfile:
        with open(csvfile, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(result)
    else:
        print(result)



