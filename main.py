# from src.get_info_from_hh import get_employer_data, get_vacancies_by_employe
#
#
# # Список ID интересующих компаний
# EMPLOYER_IDS = [
#     1740,    # Яндекс
#     3529,    # Сбер
#     78638,   # Тинькофф
#     41862,   # VK
#     2180,    # Ozon
#     36769,   # Wildberries
#     84585,   # Avito
#     1057,    # Kaspersky
#     64174,   # 2ГИС
#     29345    # Lamoda
# ]
#
#
#
# def fill_database():
#     """Основная функция: загружает данные по всем компаниям и сохраняет в БД"""
#     # conn = psycopg2.connect(**DB_CONFIG)
#     # create_tables(conn)
#
#     for employer_id in EMPLOYER_IDS:
#         print(f"Обработка компании {employer_id}...")
#         try:
#             employer = get_employer_data(employer_id)
#             print(employer)
#             # insert_employer(conn, employer)
#             vacancies = get_vacancies_by_employer(employer_id)
#             for vac in vacancies:
#                 print(vac)
#                 # insert_vacancy(conn, vac)
#             print(f"  Загружено {len(vacancies)} вакансий")
#         except Exception as e:
#             print(f"  Ошибка при загрузке компании {employer_id}: {e}")
#     return 'Успешно!'
#
#     # conn.close()
#     # print("База данных успешно заполнена!")
#
#
# if __name__ == '__main__':
#     fill_database()


import json
from src.db_utils import create_tables, insert_data_to_db


def main():
    create_tables()
    insert_data_to_db()

main()

    # insert_data_to_db('../data/hh_vacancies.json')