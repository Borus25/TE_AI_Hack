from auth import authentication
from smart_line import execute_prompt, create_sql_plan
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': 'localhost',
    'port': 5434,
    'database': 'task_db',
    'user': 'postgres',
    'password': 'postgres'
}

if __name__ == "__main__":
    user = authentication(db_config)

    prompt = input(f'Какую информации хотели бы получить, {user.first_name} {user.last_name}?')

    file_or_console = input("Куда вам надо поместить полученные данные: в csv-файл или вывести в консоль?\nВведите: 'csv' или 'консоль'")
    while file_or_console != 'csv' and file_or_console != 'консоль':
        file_or_console = input("Введите: 'csv' или 'консоль'")


    create_sql_plan(prompt, user)
    if file_or_console:
        output_file = input('Введите, куда сохранять?')
        execute_prompt(prompt, user, output_file)
    else:
        execute_prompt(prompt, user)


