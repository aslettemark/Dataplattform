import json
import urllib.request
import os
import pymysql

"""
This lambda gets raw data from the get_docs API and extracts only the valueable information and 
inserts that information into an aurora db. 
"""

# These types will be used if no other types are provided.
DEFAULT_TYPES = ["GithubType", "EventRatingType", "SlackType"]
DEFAULT_TIMESTAMP_FROM = 0
DEFAULT_TIMESTAMP_TO = 2147483647


def handler(event, context):
    types = DEFAULT_TYPES
    if "types" in event:
        types = event["types"]

    timestamp_from = DEFAULT_TIMESTAMP_FROM
    if "timestamp_from" in event:
        timestamp_from = event["timestamp_from"]

    timestamp_to = DEFAULT_TIMESTAMP_TO
    if "timestamp_to" in event:
        timestamp_to = event["timestamp_to"]

    counter = main(types, timestamp_from, timestamp_to)
    return {
        'statusCode': 200,
        'body': json.dumps(str(counter) + " records successfully inserted into Aurora.")
    }


def get_relevant_attrs(docs, type, sql_connection):
    """
    :param docs: Raw documents from get_docs API.
    :param type: which datatype this is.
    :return: only the most relevant attributes which are decided by the Type classes in the
    `data_types` folder.
    """
    # For example: if the type is GithubType we import data_types/GithubType.
    mod = __import__('data_types.' + type, fromlist=[type])
    output = []
    data_type_class = getattr(mod, type)
    data_type_object = data_type_class()

    # To make sure that we are able to insert records into the SQL table we run this now.
    check_table_exists(sql_connection, type, data_type_object)

    for doc in docs:
        if data_type_object.accept_data(doc):
            column_values = data_type_object.get_column_values(doc)
            output.append(column_values)
    return output


def check_table_exists(sql_connection, table_name, data_type_object):
    """
    This method checks if a table with name <table_name> already exists or not. If it doesn't
    then it will create a new table.
    :param sql_connection: A MySQL connection.
    :param table_name: Which table should be checked.
    :return:
    """
    # TODO: If the table exists it should check if all the columns are correct.
    cur = sql_connection.cursor()
    test_sql_query = "SELECT 1 FROM " + table_name + " LIMIT 1;"

    exists = True

    try:
        cur.execute(test_sql_query)
    except pymysql.err.ProgrammingError:
        exists = False
        print("No table found, will create new.")

    if not exists:
        sql = data_type_object.get_create_table_sql(table_name)
        cur.execute(sql)


def insert_data_into_db(sql_connection, datas, type):
    """
    :param sql_connection: A MySQL connection.
    :param datas: A list of dictionaries, these dictionaries are containing the key, value that
    make up a SQL record.
    :param type: Which datatype this is. example: GithubType
    :return: The number of records inserted.
    """
    # Just a simple counter to see how many records
    counter = 0
    for data in datas:
        cursor = sql_connection.cursor()

        # This list is just every column name.
        column_list = list(data.keys()).copy()
        # This list is containing every column name surrounded with %()s.
        param_list = ["%(" + column + ")s" for column in column_list]

        params = ", ".join(param_list)
        columns = ", ".join(column_list)
        sql = "INSERT INTO `" + type + "` (" + columns + ") VALUES (" + params + ");"
        try:
            res = cursor.execute(sql, data)
            counter += res
        except pymysql.err.IntegrityError:
            print("ID: " + data["id"] + " is a duplicate, skipping.")

    sql_connection.commit()

    return counter


def fetch_data_url(url):
    """
    :param url: URL for get_docs API
    :return: list of docs fetched from get_docs API.
    """
    fetch_key = os.getenv("DATAPLATTFORM_AURORA_FETCH_KEY")
    req = urllib.request.Request(url, headers={"x-api-key": fetch_key})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode())


def format_url(base_url, type, timestamp_from, timestamp_to):
    """
    :return: A formatted url.
    """
    return base_url + type + "?timestamp_from=" + str(timestamp_from) \
           + "&timestamp_to=" + str(timestamp_to)


def main(types, timestamp_from, timestamp_to):
    base_url = os.getenv("DATAPLATTFORM_AURORA_FETCH_API_URL")

    connection = pymysql.connect(
        host=os.getenv("DATAPLATTFORM_AURORA_HOST"),
        port=int(os.getenv("DATAPLATTFORM_AURORA_PORT")),
        user=os.getenv("DATAPLATTFORM_AURORA_USER"),
        password=os.getenv("DATAPLATTFORM_AURORA_PASSWORD"),
        db=os.getenv("DATAPLATTFORM_AURORA_DB_NAME"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
    counter = 0

    for type in types:
        url = format_url(base_url, type, timestamp_from, timestamp_to)
        docs = fetch_data_url(url)
        sql_format = get_relevant_attrs(docs, type, connection)
        n_records = insert_data_into_db(connection, sql_format, type)
        counter += n_records
    connection.close()
    return counter


if __name__ == '__main__':
    number_of_recs_inserted = main(DEFAULT_TYPES, DEFAULT_TIMESTAMP_FROM, DEFAULT_TIMESTAMP_TO)
    print("Number of records inserted", number_of_recs_inserted)
