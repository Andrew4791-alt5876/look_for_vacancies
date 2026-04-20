import requests
import json
from datetime import datetime


def get_info() -> list:
    # today = datetime.today()
    # from_date = today.strftime('%Y-%m-%d')
    # from_date = '2026-01-05'
    # URL = 'https://api.hh.ru/vacancies'
    # response = requests.get(url=URL, params=from_date)
    with open('../data/hh_vacancies.json', 'r', encoding="utf-8") as file:
        dict_of_response = json.load(file)
        # dict_of_response = response.json()
        dict_vacancy = dict_of_response['items']
        # final_list = []
        # for vacancy in dict_vacancy:
            # date_info = vacancy['published_at']
            # if date_info[:10] == from_date:
            # final_list.append(
            #     {
            #         'vacancy': vacancy.get('name'),
            #         'salary_range': vacancy.get('salary'),
            #         'url': vacancy.get('alternate_url')
            #     }
            # )
    return dict_vacancy

print(get_info())