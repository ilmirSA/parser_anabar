import csv
import json
import os

import requests
from openpyxl import load_workbook


def extract_values(json_object):
    result_list = []
    if isinstance(json_object, dict):
        for key, value in json_object.items():
            if key == "category_name" and "subject_path_id" in json_object:
                result_list.append({str(value).lower(): json_object["subject_path_id"]})
            elif isinstance(value, (dict, list)):
                result_list.extend(extract_values(value))
    elif isinstance(json_object, list):
        for item in json_object:
            result_list.extend(extract_values(item))

    return result_list


def get_categories(session):
    params = {
        'marketplace': 'wb',
    }

    response = requests.get('https://anabar.ai/api/analytics/v1/categories/', params=params, cookies=session.cookies,
                            headers=session.headers)

    result_list = extract_values(response.json())


def get_statistics(session, catalog_id):
    json_data = {
        'marketplace': 'wb',
        'period': {
            'start_date': '2023-05-26',
            'end_date': '2023-06-29',
        },
        'subject_path_ids': [
            catalog_id,
        ],
        'params_groups': {
            'groups': [],
            'all_true': True,
        },
        'null_placeholder': '',
        'include_fbs': False,
        'table_state': {},
    }

    response = requests.post('https://anabar.ai/api/analytics/v1/dashboards-hist/', cookies=session.cookies,
                             headers=session.headers,
                             json=json_data)

    stats = []
    for i in response.json()['table']['rows']:
        stats.append(i)

    return stats


def write_to_csv(text, catalog, file_path):
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='', encoding='CP1251', ) as csv_file:
        # создаем объект writer для записи в CSV файл
        writer = csv.writer(csv_file, delimiter=',')

        # если файл не существует, записываем заголовки столбцов
        if not file_exists:
            csv_file.write('Каталоги, Выручка в ценовых сегментах"\n')

        # создаем новую строку со значениями из списка data_list

        # записываем данные в новую строку
        csv_file.write(f"{catalog},{text}\n")


def get_sorted_list(table):
    return table['earnings']


def main():
    print("Парсинг начался")
    file_path = 'data.csv'
    file_exists = os.path.isfile(file_path)

    if file_exists:
        os.remove(file_path)

    with open("result.json", "r") as f:
        result_list = json.load(f)

    logon = {
        'phone-code': '7',
        'phone': '9160197057',
        'password': "118607",
        'message': '**'
    }
    login_url = 'https://anabar.ai/login'
    session = requests.Session()
    login = session.post(login_url, data=logon)
    proccesed = []

    for catalog in result_list:
        for key,values in catalog.items():
            if values in proccesed:
                continue
            catalog_name = key
            catalog_id = values
            data_list = get_statistics(session, catalog_id)
            sorted_catalog = sorted(data_list, key=get_sorted_list, reverse=True)[:2]
            text = ''
            if len(sorted_catalog) == 2:

                if int(sorted_catalog[0]['price_group']) < int(sorted_catalog[1]['price_group']):
                    text = f"от {sorted_catalog[0]['price_group']} до {sorted_catalog[1]['price_group']}"  # {sorted_catalog[0]['earnings']} - {sorted_catalog[1]['earnings']}"
                else:
                    text = f"от {sorted_catalog[1]['price_group']} до {sorted_catalog[0]['price_group']}"  # {sorted_catalog[1]['earnings']} - {sorted_catalog[0]['earnings']}"
                write_to_csv(text, catalog_name, file_path)
            elif len(sorted_catalog) == 1 and int(sorted_catalog[0]['earnings']) != 0:
                text = f"от {sorted_catalog[0]['price_group']}"
                write_to_csv(text, catalog_name, file_path)
            proccesed.append(key)
            print(f"Спарсился каталог {key}")
    print("Парсинг закончился")



if __name__ == '__main__':
    main()
