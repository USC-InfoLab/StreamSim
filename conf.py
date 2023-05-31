# Sensor API
HOST = '0.0.0.0'
URL_PATH = 'fetchdata'
PORT = '9977'
DATA_TYPE = 'DATABASE' # 'DATABASE' or 'CSV'
DATASET = '<dataset_path>' # Path of the CSV dataset. Leave empty if you want to stream from database table

# Database Config
DBMS = 'postgresql'
DB_HOST = '<database_host>'
DB_PORT = 5432 # replace with <database_port>
DB_USER = '<database_user>'
DB_PASS = '<database_password>'
DB_NAME = '<database_name>'
DB_TABLE = '<database_table>'

# After each TIMEOUT (seconds), BATCH number of data entries is sent by the API
# Start time is the time recorded data stream is simulated to start from
DATE_TIME_COL = 'timestamp'
BATCH = 1
TIMEOUT = 1
START_TIME = '2022-10-12 00:00:00'
