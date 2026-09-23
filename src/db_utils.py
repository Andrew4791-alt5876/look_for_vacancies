import json
import psycopg2

conn_params = {
    "dbname": "vacancies",
    "user": "postgres",
    "password": "A12345!",
    "host": "localhost",
    "port": 5432,
    "client_encoding": "UTF8",
}


def create_tables():
    """Создает таблицы в базе данных"""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employers (
                employer_id INT PRIMARY KEY, 
                name VARCHAR(255) NOT NULL,
                url VARCHAR(255)
                );
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                vacancy_id INT PRIMARY KEY,
                employer_id INT REFERENCES employers(employer_id),
                name VARCHAR(255) NOT NULL,
                salary_from INT,
                salary_to INT,
                currency VARCHAR(10),
                url VARCHAR(255)
                );
                """)
        conn.commit()
    print("Таблицы успешно созданы!")


def insert_data_to_db():
    """Читает JSON и заполняет таблицы данными."""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            with open("data/hh_vacancies.json", "r", encoding="utf-8") as file:
                dict_of_response = json.load(file)
                dict_vacancy = dict_of_response["items"]
                for item in dict_vacancy:
                    # Данные работодателя
                    employer = item.get("employer")
                    employer_id = employer.get("id")
                    employer_name = employer.get("name")
                    employer_url = employer.get("alternate_url")
                    if employer_id:
                        cur.execute(
                            """
                            INSERT INTO employers (employer_id, name, url)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (employer_id) DO NOTHING;
                            """,
                            (employer_id, employer_name, employer_url),
                        )
                    # Данные вакансии
                    vacancy_id = item.get("id")
                    vacancy_name = item.get("name")
                    salary = item.get("salary") or {}
                    salary_from = salary.get("from")
                    salary_to = salary.get("to")
                    currency = salary.get("currency")
                    vacancy_url = item.get("alternate_url")
                    if vacancy_id:
                        cur.execute(
                            """
                            INSERT INTO vacancies(vacancy_id, employer_id, name, salary_from, salary_to, currency,url)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (vacancy_id) DO NOTHING;
                            """,
                            (vacancy_id, employer_id, vacancy_name, salary_from, salary_to, currency, vacancy_url),
                        )
        conn.commit()
    print("Данные успешно загружены в базу данных!")
