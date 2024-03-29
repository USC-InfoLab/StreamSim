import pandas as pd
from flask import Flask, jsonify, redirect, url_for
from sqlalchemy import create_engine
from loguru import logger
import urllib.parse

from conf import *
from utils import Singleton


app = Flask(__name__)
        

class DataLoader(metaclass=Singleton):
    """Singleton DataLoader class for loading and retrieving data in batches.

    This class provides functionality to load data and retrieve it in batches, maintaining a singleton
    instance throughout the application.

    Attributes:
        df (pandas.DataFrame): The underlying data in a pandas DataFrame.
        batch_size (int): The size of each data batch.
        row_ind (int): The current row index.

    """
    def __init__(self, df, batch_size=1, row_ind=0) -> None:
        """Initialize the DataLoader with data and parameters.

        Args:
            df (pandas.DataFrame): The underlying data in a pandas DataFrame.
            batch_size (int, optional): The size of each data batch. Defaults to 1.
            row_ind (int, optional): The initial row index. Defaults to 0.

        """
        self.df = df
        self.batch_size = batch_size
        self.row_ind = row_ind
        

        
    def get_next(self):
        """Get the next batch of data.

        This method retrieves the next batch of data from the underlying DataFrame based on the current
        row index and batch size. It also updates the row index for the next batch.

        Returns:
            pandas.DataFrame: The next batch of data.

        """
        res = self.df.iloc[self.row_ind:self.row_ind+self.batch_size]
        # res['timestamp'] = res['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        self.row_ind += self.batch_size
        if self.row_ind >= len(self.df):
            self.row_ind = 0
        return res
        
            

def get_db_engine():
    """
    Returns a SQLAlchemy engine for connecting to the database.

    Returns:
        engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine object.
    """
    db_pass_enc = urllib.parse.quote_plus(DB_PASS)
    return create_engine(f'{DBMS}://{DB_USER}:{db_pass_enc}@{DB_HOST}:{DB_PORT}/{DB_NAME}')


def get_query_result(query, db_conn, params=[]):
    """
    Executes a SQL query on the database connection and returns the result as a Pandas DataFrame.

    Args:
        query (str): SQL query to be executed.
        db_conn (sqlalchemy.engine.base.Connection): Database connection object.
        params (list, optional): Parameters to be passed to the SQL query. Defaults to [].

    Returns:
        result (pandas.DataFrame): Result of the SQL query as a Pandas DataFrame.
    """
    return pd.read_sql(query, db_conn, params=params)



def get_series_from_db(db_conn, table_name, ids=None, id_column=None, start_time=None):
    """
    Retrieves the series data for specific IDs from the database starting from the specified time.

    Args:
        db_conn (sqlalchemy.engine.base.Connection): Database connection object.
        table_name (str): Name of the table to retrieve the series data from.
        ids (list or None, optional): IDs for which to retrieve the series data. Defaults to None.
        id_column (str or None, optional): Name of the ID column in the database table. Defaults to None.
        start_time (str or None, optional): Start time from which to retrieve the series data. Defaults to None.

    Returns:
        result (pandas.DataFrame): Result of the SQL query as a Pandas DataFrame.
    """
    conditions = []

    if ids is not None:
        conditions.append(f"{id_column} IN ({','.join(['%s'] * len(ids))})")

    if start_time is not None:
        conditions.append(f"timestamp >= '{start_time}'")

    condition_str = " AND ".join(conditions)

    if condition_str:
        condition_str = "WHERE " + condition_str

    query = f'''
    SELECT * FROM {table_name}
    {condition_str}
    ORDER BY timestamp ASC;
    '''

    params = ids if ids is not None else []

    return get_query_result(query, db_conn, params=params)


def get_data(config):
    """
    Retrieves the data from either a database table or a CSV file based on the configuration.

    Args:
        config (dict): Configuration dictionary containing the 'DATA_TYPE', 'DATASET' path, 'IDs', and 'START_TIME', DB_TABLE, DATE_TIME_COL.

    Returns:
        result (pandas.DataFrame): Data retrieved from the database table or CSV file.
    """
    data_type = config.get('DATA_TYPE', None)
    dataset_path = config.get('DATASET', None)
    ids = config.get('IDS', None)
    start_time = config.get('START_TIME', None)
    db_table = config.get('DB_TABLE', None)
    date_time_col = config.get('DATE_TIME_COL', None)
    
    if date_time_col is None:
        raise ValueError('DATE_TIME_COL must be specified.')
    if data_type != 'DATABASE' and data_type != 'CSV':
        raise ValueError('DATA_TYPE must be either DATABASE or CSV.')
    if data_type == 'DATABASE':
        # Fetching data from database table
        db_conn = get_db_engine()
        return get_series_from_db(db_conn, table_name=db_table, ids=ids, start_time=start_time)
    elif data_type == 'CSV':
        # Fetching data from CSV file
        df = pd.read_csv(dataset_path)
        df[f'{date_time_col}'] = pd.to_datetime(df[f'{date_time_col}'])
        # sort by timestamp
        df = df.sort_values(by=[f'{date_time_col}'])

        # Apply conditions if they exist
        if ids:
            df = df[df['id'].isin(ids)]
        if start_time:
            df = df[df[f'{date_time_col}'] >= start_time]

        return df 


def init_dataloader():
    """
    Initializes the DataLoader with the fetched data based on the configuration.

    Returns:
        DataLoader: Initialized DataLoader instance.
    """
    config = {
        'DATA_TYPE': DATA_TYPE,
        'DATASET': DATASET,
        'IDS': get_ids(),
        'START_TIME': START_TIME,
        'DB_TABLE': DB_TABLE,
        'DATE_TIME_COL': DATE_TIME_COL
    }

    data = get_data(config)
    return DataLoader(data, batch_size=BATCH)


def get_ids():
    """
    Retrieves the target IDs.

    Returns:
        list or None: List of IDs or None if not specified in the config.
    """
    ids = None  # Default IDs if not specified in the config
    # You can implement your own logic to fetch IDs
    return ids


@app.route('/')
def root():
    """
    Redirects the root URL to the 'fetch_sensor_data' endpoint.

    Returns:
        Response: A redirection response to the 'fetch_sensor_data' endpoint.
    """
    return redirect(url_for('fetch_sensor_data'))


@app.route(f'/{URL_PATH}')
def fetch_sensor_data():
    """
    Fetches sensor data from the data loader and returns it as a JSON response.

    Returns:
        Response: A JSON response containing the fetched sensor data.
    """
    data_loader = init_dataloader()
    rows = data_loader.get_next()
    rows_with_strftime = rows.copy()
    rows_dict = rows_with_strftime.to_dict('records')
    resp = jsonify(rows_dict)
    logger.debug(resp)
    return resp


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)

