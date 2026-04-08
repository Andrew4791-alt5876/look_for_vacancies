# import requests
# import json
# from datetime import datetime


# def get_info() -> list:
#     today = datetime.today()
#     from_date = today.strftime('%Y-%m-%d')
#     # from_date = '2026-01-05'
#     URL = 'https://api.hh.ru/vacancies'
#     response = requests.get(url=URL, params=from_date)
#     dict_of_response = response.json()
#     dict_vacancy = dict_of_response['items']
#     final_list = []
#     for vacancy in dict_vacancy:
#         date_info = vacancy['published_at']
#         if date_info[:10] == from_date:
#             final_list.append(
#                 {
#                     'vacancy': vacancy.get('name'),
#                     'salary_range': vacancy.get('salary'),
#                     'url': vacancy.get('apply_alternate_url')
#                 }
#             )
# def get_employer_data(employer_id):
#     """Получение данных о работодателе с hh.ru"""
#     url = f"https://api.hh.ru/employers/{employer_id}"
#     response = requests.get(url, headers=HEADERS)
#     response.raise_for_status()
#     data = response.json()
#     return {
#         'employer_id': data['id'],
#         'name': data['name'],
#         'url': data.get('alternate_url'),
#         'open_vacancies': data.get('open_vacancies', 0)
#     }
#
#
# def get_vacancies_by_employer(employer_id):
#     """Получение списка вакансий для указанного работодателя"""
#     vacancies = []
#     page = 0
#     per_page = 100
#     while True:
#         url = f"https://api.hh.ru/vacancies"
#         params = {
#             'employer_id': employer_id,
#             'per_page': per_page,
#             'page': page
#         }
#         response = requests.get(url, headers=HEADERS, params=params)
#         response.raise_for_status()
#         data = response.json()
#         for item in data['items']:
#             salary = item.get('salary')
#             salary_from = None
#             salary_to = None
#             currency = None
#             if salary:
#                 salary_from = salary.get('from')
#                 salary_to = salary.get('to')
#                 currency = salary.get('currency')
#             vacancy = {
#                 'vacancy_id': item['id'],
#                 'employer_id': employer_id,
#                 'name': item['name'],
#                 'salary_from': salary_from,
#                 'salary_to': salary_to,
#                 'currency': currency,
#                 'url': item['alternate_url'],
#                 'requirement': item.get('snippet', {}).get('requirement', '')
#             }
#             vacancies.append(vacancy)
#         if data.get('pages') and page >= data['pages'] - 1:
#             break
#         page += 1
#     return vacancies
#
# HEADERS = {'User-Agent': 'HH-User-Agent/1.0 (tyrandr@list.ru)'}  # Замените на свой email
# print(get_employer_data([1740]))

# def insert_employer(conn, employer_data):
#     """Вставка или обновление данных работодателя"""
#     with conn.cursor() as cur:
#         cur.execute("""
#             INSERT INTO employers (employer_id, name, url, open_vacancies)
#             VALUES (%(employer_id)s, %(name)s, %(url)s, %(open_vacancies)s)
#             ON CONFLICT (employer_id) DO UPDATE SET
#                 name = EXCLUDED.name,
#                 url = EXCLUDED.url,
#                 open_vacancies = EXCLUDED.open_vacancies
#         """, employer_data)
#         conn.commit()
#
#
# def insert_vacancy(conn, vacancy_data):
#     """Вставка вакансии, если её ещё нет"""
#     with conn.cursor() as cur:
#         cur.execute("""
#             INSERT INTO vacancies (
#                 vacancy_id, employer_id, name, salary_from, salary_to, currency, url, requirement
#             ) VALUES (
#                 %(vacancy_id)s, %(employer_id)s, %(name)s, %(salary_from)s,
#                 %(salary_to)s, %(currency)s, %(url)s, %(requirement)s
#             )
#             ON CONFLICT (vacancy_id) DO NOTHING
#         """, vacancy_data)
#         conn.commit()

import requests
import json
import time
from typing import List, Dict, Any

# ================== НАСТРОЙКИ ==================
# ID компаний (Яндекс, Сбер, Тинькофф, VK, Ozon, Wildberries, Avito, Kaspersky, 2ГИС, Lamoda)
EMPLOYER_IDS: List[int] = [
    1740,  # Яндекс
    3529,  # Сбер
    78638,  # Тинькофф
    41862,  # VK
    2180,  # Ozon
    36769,  # Wildberries
    84585,  # Avito
    1057,  # Kaspersky
    64174,  # 2ГИС
    29345  # Lamoda
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


# ================== ФУНКЦИИ ДЛЯ РАБОТЫ С API ==================
def get_employer(employer_id: int) -> Dict[str, Any]:
    """Получить данные о работодателе по ID"""
    url = f"https://api.hh.ru/employers/{employer_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return {
        'id': data['id'],
        'name': data['name'],
        'url': data.get('alternate_url'),
        'open_vacancies': data.get('open_vacancies', 0)
    }


def get_vacancies(employer_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
    """Получить все вакансии работодателя (с пагинацией)"""
    vacancies = []
    page = 0
    while True:
        params = {
            'employer_id': employer_id,
            'per_page': per_page,
            'page': page
        }
        response = requests.get('https://api.hh.ru/vacancies', headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        for item in data['items']:
            salary = item.get('salary')
            vacancy = {
                'id': item['id'],
                'name': item['name'],
                'url': item['alternate_url'],
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'currency': salary.get('currency') if salary else None,
                'requirement': item.get('snippet', {}).get('requirement', ''),
                'responsibility': item.get('snippet', {}).get('responsibility', '')
            }
            vacancies.append(vacancy)

        if page >= data.get('pages', 1) - 1:
            break
        page += 1
        time.sleep(0.2)  # небольшая задержка, чтобы не нагружать API
    return vacancies


# ================== ОСНОВНАЯ ЛОГИКА ==================
def collect_data() -> Dict[str, Any]:
    """Собрать данные по всем работодателям и их вакансиям"""
    result = {}
    for eid in EMPLOYER_IDS:
        print(f"Загрузка компании {eid}...")
        try:
            employer = get_employer(eid)
            vacancies = get_vacancies(eid)
            result[employer['name']] = {
                'employer_info': employer,
                'vacancies_count': len(vacancies),
                'vacancies': vacancies
            }
            print(f"  -> Найдено вакансий: {len(vacancies)}")
        except Exception as e:
            print(f"  -> Ошибка: {e}")
            result[f"company_{eid}"] = {'error': str(e)}
        time.sleep(0.3)
    return result


def save_to_json(data: Dict[str, Any], filename: str = 'hh_data.json'):
    """Сохранить данные в JSON-файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nДанные сохранены в {filename}")


def print_summary(data: Dict[str, Any]):
    """Вывести краткую сводку в консоль"""
    print("\n" + "=" * 60)
    print("СВОДКА ПО КОМПАНИЯМ")
    print("=" * 60)
    for company_name, info in data.items():
        if 'error' in info:
            print(f"{company_name}: Ошибка - {info['error']}")
        else:
            emp = info['employer_info']
            print(f"{emp['name']} (ID: {emp['id']})")
            print(f"  Открытых вакансий по данным API: {emp['open_vacancies']}")
            print(f"  Загружено вакансий: {info['vacancies_count']}")
            print()


# ================== ЗАПУСК ==================
if __name__ == '__main__':
    print("Начинаем сбор данных с hh.ru...")
    all_data = collect_data()
    print_summary(all_data)
    save_to_json(all_data)