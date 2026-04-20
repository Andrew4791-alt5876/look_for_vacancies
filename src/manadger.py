import psycopg2
from psycopg2 import sql


class DBManager:
    """
    Класс для работы с базой данных PostgreSQL.
    Предполагается наличие таблиц:
    - companies (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL)
    - vacancies (id SERIAL PRIMARY KEY, company_id INTEGER REFERENCES companies(id),
                 title VARCHAR(255) NOT NULL, salary INTEGER, url VARCHAR(255))
    """

    def __init__(self, dbname: str, user: str, password: str, host: str = 'localhost', port: str = '5432'):
        """
        Инициализация подключения к БД.
        :param dbname: имя базы данных
        :param user: пользователь
        :param password: пароль
        :param host: хост (по умолчанию localhost)
        :param port: порт (по умолчанию 5432)
        """
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.conn.autocommit = True  # автоматическое подтверждение транзакций

    def _execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Вспомогательный метод для выполнения запросов и возврата результатов.
        :param query: SQL-запрос
        :param params: параметры для подстановки
        :return: список строк результата (list of tuples)
        """
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:  # если запрос возвращает данные
                return cur.fetchall()
            return []

    def get_companies_and_vacancies_count(self) -> list:
        """
        Получает список всех компаний и количество вакансий у каждой компании.
        :return: список кортежей (company_name, vacancies_count)
        """
        query = """
            SELECT c.name, COUNT(v.id) AS vacancy_count
            FROM companies c
            LEFT JOIN vacancies v ON c.id = v.company_id
            GROUP BY c.id, c.name
            ORDER BY vacancy_count DESC;
        """
        return self._execute_query(query)

    def get_all_vacancies(self) -> list:
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию.
        :return: список кортежей (company_name, vacancy_title, salary, vacancy_url)
        """
        query = """
            SELECT c.name, v.title, v.salary, v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.id;
        """
        return self._execute_query(query)

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по вакансиям.
        Учитываются только вакансии с указанной зарплатой (не NULL).
        :return: средняя зарплата (float)
        """
        query = """
            SELECT AVG(salary) FROM vacancies WHERE salary IS NOT NULL;
        """
        result = self._execute_query(query)
        if result and result[0][0] is not None:
            return float(result[0][0])
        return 0.0

    def get_vacancies_with_higher_salary(self) -> list:
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям.
        :return: список кортежей (company_name, vacancy_title, salary, vacancy_url)
        """
        query = """
            SELECT c.name, v.title, v.salary, v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.id
            WHERE v.salary > (SELECT AVG(salary) FROM vacancies WHERE salary IS NOT NULL)
            ORDER BY v.salary DESC;
        """
        return self._execute_query(query)

    def get_vacancies_with_keyword(self, keyword: str) -> list:
        """
        Получает список всех вакансий, в названии которых содержится переданное слово.
        :param keyword: ключевое слово для поиска (регистронезависимо)
        :return: список кортежей (company_name, vacancy_title, salary, vacancy_url)
        """
        query = """
            SELECT c.name, v.title, v.salary, v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.id
            WHERE v.title ILIKE %s;
        """
        # Добавляем символы % для поиска подстроки
        like_pattern = f'%{keyword}%'
        return self._execute_query(query, (like_pattern,))

    def close(self):
        """Закрывает соединение с БД."""
        if self.conn:
            self.conn.close()


