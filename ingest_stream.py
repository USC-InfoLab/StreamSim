import time
import requests
import pandas as pd

from conf import *

def get_data():
    """
    Retrieves new data from the Flask server.

    Returns:
        df (pandas.DataFrame): DataFrame containing the new data from the server.
    """
    response = requests.get(SERVER_URL)
    data = response.json()
    df = pd.DataFrame(data)
    df[f'{DATE_TIME_COL}'] = pd.to_datetime(df[f'{DATE_TIME_COL}'])
    df.set_index(f'{DATE_TIME_COL}', inplace=True)
    return df


def process_stream(new_data):
    """
    Processes the new data received from the stream.

    Args:
        new_data (pandas.DataFrame): DataFrame containing the new data.

    Returns:
        None
    """
    # User should implement their own processing logic here
    # This is just a placeholder to print the new data for demonstration purposes
    print(new_data)

if __name__ == '__main__':
    # Flask server API endpoint
    SERVER_URL = f"http://{HOST}:{PORT}"

    # Get new stream records
    new_data = get_data()

    # Process new stream records
    process_stream(new_data)

    # Sleep for the specified timeout
    time.sleep(TIMEOUT)
