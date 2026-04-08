import requests
import psycopg2
import time
from geopy.geocoders import Nominatim
from typing import List, Dict, Any, Optional, Tuple

# ================== НАСТРОЙКИ ==================
# --- Параметры подключения к PostgreSQL (измените под себя!) ---
DB_CONFIG = {
    'dbname': 'air_tracker',
    'user': 'postgres',
    'password': 'your_password_here',  # Замените на свой пароль
    'host': 'localhost',
    'port': 5432
}

# --- Список интересных стран (10 штук) ---
# Можно использовать как полное название, так и код (например, 'RU')
COUNTRIES_OF_INTEREST = [
    "Russia", "United States", "Germany", "France",
    "United Kingdom", "China", "Japan", "Canada",
    "Australia", "Brazil"
]

# --- Настройки User-Agent для Nominatim (обязательно замените на свой email) ---
GEOCODER_USER_AGENT = "YourAppName/1.0 (your_email@example.com)"

# --- Базовый URL API OpenSky ---
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

# --- Заголовки для запросов ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ================== ФУНКЦИИ ДЛЯ РАБОТЫ С API ==================
def get_countries_data() -> Dict[str, Dict]:
    """Получает данные о всех странах из REST Countries API."""
    url = "https://restcountries.com/v3.1/all"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        countries_data = response.json()

        # Создаём словарь для быстрого доступа по полному названию и по коду
        countries_dict = {}
        for country in countries_data:
            name = country.get('name', {}).get('common')
            code = country.get('cca2')
            if name and code:
                countries_dict[name] = {
                    'code': code,
                    'region': country.get('region'),
                    'subregion': country.get('subregion'),
                    'population': country.get('population'),
                    'area': country.get('area')
                }
        return countries_dict
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных о странах: {e}")
        return {}

def get_aircraft_data() -> List[Dict]:
    """
    Получает данные о самолётах из OpenSky Network API.
    Возвращает список самолётов, у которых есть координаты.
    """
    print("Запрос данных о самолётах с OpenSky Network...")
    try:
        params = {
            "extended": 1,   # получаем больше данных, включая скорость и курс
        }
        response = requests.get(OPENSKY_API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        aircraft_list = []
        if 'states' in data and data['states']:
            for state in data['states']:
                # state[0] = icao24, state[1] = callsign, state[2] = origin_country,
                # state[5] = longitude, state[6] = latitude, state[7] = altitude,
                # state[9] = velocity (speed)
                icao24 = state[0]
                callsign = state[1] if state[1] else ""
                origin_country = state[2] if state[2] else "Unknown"
                longitude = state[5]
                latitude = state[6]
                altitude = state[7]          # высота в метрах
                speed = state[9]             # скорость в м/с

                # Пропускаем записи без координат
                if longitude is None or latitude is None:
                    continue

                aircraft_list.append({
                    'icao24': icao24,
                    'callsign': callsign,
                    'origin_country': origin_country,
                    'longitude': longitude,
                    'latitude': latitude,
                    'altitude': altitude,
                    'speed': speed
                })
        print(f"Получено {len(aircraft_list)} самолётов с координатами.")
        return aircraft_list
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных о самолётах: {e}")
        return []

def get_country_by_coordinates(lat: float, lon: float, geolocator: Nominatim) -> Optional[str]:
    """
    Определяет страну по координатам с помощью обратного геокодирования.
    Использует локальный кэш, чтобы не повторять запросы для одних и тех же координат.
    """
    # Простой кэш в виде словаря, хранящегося в атрибуте функции
    if not hasattr(get_country_by_coordinates, "cache"):
        get_country_by_coordinates.cache = {}

    coord_key = f"{lat:.2f},{lon:.2f}"  # округляем для экономии памяти
    if coord_key in get_country_by_coordinates.cache:
        return get_country_by_coordinates.cache[coord_key]

    try:
        location = geolocator.reverse((lat, lon), language='en', exactly_one=True)
        if location and 'country' in location.raw.get('address', {}):
            country = location.raw['address']['country']
        else:
            country = None
        get_country_by_coordinates.cache[coord_key] = country
        time.sleep(0.5)  # Соблюдаем лимиты Nominatim (1 запрос в секунду)
        return country
    except Exception as e:
        print(f"Ошибка геокодирования ({lat}, {lon}): {e}")
        get_country_by_coordinates.cache[coord_key] = None
        return None

def enrich_aircraft_with_country(aircraft_list: List[Dict], geolocator: Nominatim) -> List[Dict]:
    """Добавляет к каждому самолёту название страны, полученное по координатам."""
    enriched = []
    for aircraft in aircraft_list:
        lat = aircraft['latitude']
        lon = aircraft['longitude']
        country = get_country_by_coordinates(lat, lon, geolocator)
        if country:
            aircraft['country_detected'] = country
            enriched.append(aircraft)
    print(f"Определена страна для {len(enriched)} самолётов из {len(aircraft_list)}.")
    return enriched

# ================== РАБОТА С БАЗОЙ ДАННЫХ ==================
def create_tables(conn):
    """Создаёт таблицы countries и aircraft, если они не существуют."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                country_id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                code VARCHAR(2),
                region VARCHAR(50),
                subregion VARCHAR(50),
                population BIGINT,
                area FLOAT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS aircraft (
                aircraft_id SERIAL PRIMARY KEY,
                icao24 VARCHAR(6) NOT NULL,
                callsign VARCHAR(10),
                origin_country VARCHAR(100),
                country_id INTEGER REFERENCES countries(country_id),
                altitude FLOAT,
                speed FLOAT,
                longitude FLOAT,
                latitude FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def insert_countries(conn, countries_data: Dict[str, Dict]):
    """Вставляет данные о странах в таблицу countries."""
    with conn.cursor() as cur:
        for name, info in countries_data.items():
            cur.execute("""
                INSERT INTO countries (name, code, region, subregion, population, area)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, info['code'], info['region'], info['subregion'],
                  info['population'], info['area']))
        conn.commit()
    print(f"Добавлено/обновлено {len(countries_data)} стран.")

def insert_aircraft(conn, aircraft_data: List[Dict], countries_dict: Dict[str, int]):
    """Вставляет данные о самолётах в таблицу aircraft."""
    with conn.cursor() as cur:
        for aircraft in aircraft_data:
            country_name = aircraft.get('country_detected')
            country_id = countries_dict.get(country_name) if country_name else None
            cur.execute("""
                INSERT INTO aircraft (icao24, callsign, origin_country, country_id,
                                      altitude, speed, longitude, latitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (aircraft['icao24'], aircraft['callsign'], aircraft['origin_country'],
                  country_id, aircraft['altitude'], aircraft['speed'],
                  aircraft['longitude'], aircraft['latitude']))
        conn.commit()
    print(f"Добавлено {len(aircraft_data)} самолётов.")

def fill_database():
    """Главная функция: загружает все данные и заполняет БД."""
    print("=== Заполнение базы данных ===")

    # 1. Получаем данные о странах из REST Countries
    print("Загрузка данных о странах...")
    all_countries = get_countries_data()
    if not all_countries:
        print("Не удалось получить данные о странах. Проверьте подключение к интернету.")
        return

    # 2. Подключаемся к БД и создаём таблицы
    conn = psycopg2.connect(**DB_CONFIG)
    create_tables(conn)

    # 3. Вставляем страны
    insert_countries(conn, all_countries)

    # 4. Получаем данные о самолётах из OpenSky
    aircraft_raw = get_aircraft_data()
    if not aircraft_raw:
        print("Не удалось получить данные о самолётах. Возможно, API OpenSky недоступен.")
        conn.close()
        return

    # 5. Инициализируем геокодер Nominatim
    geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT)

    # 6. Обогащаем данные о самолётах странами по координатам
    aircraft_enriched = enrich_aircraft_with_country(aircraft_raw, geolocator)

    # 7. Получаем словарь соответствий названия страны и её ID в БД
    with conn.cursor() as cur:
        cur.execute("SELECT name, country_id FROM countries")
        country_id_map = {row[0]: row[1] for row in cur.fetchall()}

    # 8. Вставляем данные о самолётах
    insert_aircraft(conn, aircraft_enriched, country_id_map)

    conn.close()
    print("База данных успешно заполнена!")

# ================== КЛАСС DBManager ==================
class DBManager:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config

    def _execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """Выполняет SELECT-запрос и возвращает результат."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def get_info_countries_and_planes(self) -> List[Tuple]:
        """Возвращает список всех стран и количество самолётов в каждой."""
        query = """
            SELECT c.name, COUNT(a.aircraft_id)
            FROM countries c
            LEFT JOIN aircraft a ON c.country_id = a.country_id
            GROUP BY c.country_id, c.name
            ORDER BY COUNT DESC
        """
        return self._execute_query(query)

    def get_all_planes(self) -> List[Tuple]:
        """Возвращает список всех самолётов с указанием страны регистрации, номера, скорости и высоты."""
        query = """
            SELECT c.name, a.icao24, a.speed, a.altitude
            FROM aircraft a
            JOIN countries c ON a.country_id = c.country_id
        """
        return self._execute_query(query)

    def get_avg_height(self) -> float:
        """Возвращает среднюю высоту полёта всех самолётов (в метрах)."""
        query = "SELECT AVG(altitude) FROM aircraft WHERE altitude IS NOT NULL"
        result = self._execute_query(query)
        return result[0][0] if result and result[0][0] else 0.0

    def get_max_height(self) -> List[Tuple]:
        """Возвращает список самолётов, у которых высота полёта выше средней."""
        avg = self.get_avg_height()
        if avg == 0.0:
            return []
        query = """
            SELECT c.name, a.icao24, a.altitude
            FROM aircraft a
            JOIN countries c ON a.country_id = c.country_id
            WHERE a.altitude > %s
            ORDER BY a.altitude DESC
        """
        return self._execute_query(query, (avg,))

    def get_planes_by_countries(self, country_names: List[str]) -> List[Tuple]:
        """
        Возвращает список самолётов, зарегистрированных в странах,
        названия которых переданы в списке (например, ['Russia', 'United States']).
        """
        placeholders = ','.join(['%s'] * len(country_names))
        query = f"""
            SELECT c.name, a.icao24, a.speed, a.altitude
            FROM aircraft a
            JOIN countries c ON a.country_id = c.country_id
            WHERE c.name IN ({placeholders})
        """
        return self._execute_query(query, tuple(country_names))

# ================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ==================
if __name__ == '__main__':
    # 1. Заполняем базу данных
    fill_database()

    # 2. Создаём экземпляр DBManager
    db_manager = DBManager(DB_CONFIG)

    # 3. Выполняем методы класса
    print("\n=== Статистика по странам ===")
    for row in db_manager.get_info_countries_and_planes():
        print(f"{row[0]}: {row[1]} самолётов")

    print("\n=== Первые 5 самолётов (страна, номер, скорость, высота) ===")
    for row in db_manager.get_all_planes()[:5]:
        print(row)

    print(f"\n=== Средняя высота полёта: {db_manager.get_avg_height():.2f} м")

    print("\n=== Самолёты, летящие выше среднего (первые 3) ===")
    for row in db_manager.get_max_height()[:3]:
        print(f"{row[0]}: {row[1]} на высоте {row[2]} м")

    print("\n=== Самолёты в выбранных странах (Russia, United States) ===")
    for row in db_manager.get_planes_by_countries(['Russia', 'United States'])[:5]:
        print(row)