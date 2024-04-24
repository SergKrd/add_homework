import datetime

from configparser import ConfigParser
import psycopg2


def bot_token():
    config = ConfigParser()
    config.read('config.ini')
    token = config['bot']['token']
    return token


def config(filename='config.ini', section='database'):
    # Создаем парсер для файла конфигурации
    parser = ConfigParser()
    # Читаем конфигурационный файл
    parser.read(filename)

    # Получаем секцию конфигурации
    db_params = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_params[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')

    return db_params


def connect():
    conn = None
    try:
        # Чтение параметров подключения из конфигурационного файла
        params = config()

        print('Connecting to the PostgreSQL database...')
        # Подключение к PostgreSQL
        conn = psycopg2.connect(**params)

        # Возвращаем соединение
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def select_all_lessons():
    """Выбор из БД всех доступных предметов
    :return: Список кортежей вида:
            [(4, 'Биология', '🌱'), (5, 'География', '🌍'), (6, 'Индивидуальный проект', '💡')]
    """
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        # Выполняем SQL-запрос для выбора всех значений из таблицы lessons_table
        cur.execute("SELECT * FROM lessons_table")

        # Получаем все строки результата
        rows = cur.fetchall()
        # print(rows)
        # # Выводим результат на экран
        # for row in rows:
        #     print(row)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')
        return rows


def select_all_admins():
    """Выбор из БД всех админов
    :return: Список
    """
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        # Выполняем SQL-запрос для выбора всех значений из таблицы lessons_table
        cur.execute("SELECT * FROM admins_table")

        # Получаем все строки результата
        rows = cur.fetchall()
        # print(rows)
        # # Выводим результат на экран
        # for row in rows:
        #     print(row)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')
        return rows


def select_all_main_admins():
    """Выбор из БД всех главных админов
    :return: Список
    """
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        # Выполняем SQL-запрос для выбора всех значений из таблицы lessons_table
        cur.execute("SELECT * FROM admins_table WHERE main_admin=1")

        # Получаем все строки результата
        rows = cur.fetchall()
        # print(rows)
        # # Выводим результат на экран
        # for row in rows:
        #     print(row)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')
        return rows


def add_new_admin(user_id, main_admin, phone, nick, full_name):
    """Добавление нового админ
    :return: True/False
    """
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        sql = "INSERT INTO admins_table (id, main_admin, phone, nick, full_name) VALUES (%s, %s, %s, %s, %s)"
        data = (user_id, main_admin, phone, nick, full_name)

        # Выполняем SQL-запрос для выбора всех значений из таблицы lessons_table
        cur.execute(sql, data)
        conn.commit()


    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return False
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')
        return True


def add_new_homework(date_on, date_off, lessons, homework, author):
    """Добавление нового домашнего задания
    :return: True/False
    """
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        sql = "INSERT INTO homework_table (date_on, date_off, lessons, homework, author) VALUES (%s, %s, %s, %s, %s)"
        data = (date_on, date_off, lessons, homework, author)

        # Выполняем SQL-запрос для выбора всех значений из таблицы lessons_table
        cur.execute(sql, data)
        conn.commit()


    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return False
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')
        return True


print(select_all_lessons())