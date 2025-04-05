import pandas as pd
import numpy as np 
import sqlite3
import os
import sys
import boto3
import botocore
from tqdm import tqdm
from IPython.core.magic import register_line_magic

global __AWS_ACCESS_KEY
global __AWS_SECRET_KEY
global __S3_BUCKET_NAME

global connection
global cursor
global database_name
global s3_client
global _sqldf

_sqldf=None

print("Follow the below to use Persist SQL : \n 1. configure_aws(aws_key, aws_secret, aws_bucket) or configure_aws() using environment variables \n 2. connect_db(dbname) \n 3. %sql query to run any sql query with magic command \n 4. close_connection() to close the connection \n 5.If you want to use connection manually use variable 'connection'")

def configure_aws(*kargs):
    """Configure AWS Credentials from either from Environment Variables or manually passing
    AWS ACCESS KEY : aws_key
    AWS SECRET KEY : aws_secret
    AWS Bucket Name : aws_bucket"""
    global __AWS_ACCESS_KEY
    global __AWS_SECRET_KEY
    global __S3_BUCKET_NAME
    if len(kargs) == 3:
        __AWS_ACCESS_KEY = kargs[0]
        __AWS_SECRET_KEY = kargs[1]
        __S3_BUCKET_NAME = kargs[2]
    elif len(kargs)==0:   
        print('Getting AWS Credentials from Environment Variables, aws_key, aws_secret, aws_bucket')
        __AWS_ACCESS_KEY = os.getenv('aws_key')
        __AWS_SECRET_KEY = os.getenv('aws_secret')
        __S3_BUCKET_NAME =  os.getenv('aws_bucket')

def connect_db(dbname):
    """Connect to the database, if not present in local directory, download from S3"""
    global connection
    global cursor
    global database_name
    global s3_client
    global __AWS_ACCESS_KEY
    global __AWS_SECRET_KEY
    global __S3_BUCKET_NAME
    if __AWS_ACCESS_KEY==None or __AWS_SECRET_KEY==None or __S3_BUCKET_NAME==None:
        raise ValueError("AWS Credentials not configured, please configure using configure_aws(aws_key, aws_secret, aws_bucket)")
    database_name = dbname
   

    s3_client = boto3.client('s3', aws_access_key_id=__AWS_ACCESS_KEY, aws_secret_access_key=__AWS_SECRET_KEY)
    def get_s3_file_size(bucket_name, s3_key):
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_key)
        for obj in response.get('Contents', []):
            if obj['Key'] == s3_key:
                return obj['Size']  # File size in bytes

        raise FileNotFoundError(f"File '{s3_key}' not found in bucket '{bucket_name}'")
    file_size = get_s3_file_size(__S3_BUCKET_NAME, f"sql_db/{dbname}.db")
    progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Downloading")
    def progress_callback(bytes_transferred):
        progress_bar.update(bytes_transferred)
    if not os.path.exists("./.sqldb"):
        os.mkdir("./.sqldb")
    try:
        s3_client.download_file(__S3_BUCKET_NAME, f"sql_db/{dbname}.db", f"./.sqldb/{dbname}.db",Callback=progress_callback)
        os.chmod(f"./.sqldb/{dbname}.db", 0o666)
        progress_bar.close()
    except botocore.exceptions.ClientError as e:
        print(f"Database not found in S3, creating new database {dbname}")
    # Create Connection
    connection = sqlite3.connect(f'./.sqldb/{dbname}.db')
    cursor = connection.cursor()
    database_name = dbname
    print(f"Successfully connected to database : {dbname}")

def show_tables():
    """Show all tables in the database"""
    try:
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables_df = pd.read_sql(query, connection)
        return tables_df
    except Exception as e:
        print(e)

def describe_table(table_name):
    """Describe the table schema"""
    try:
        query = f"PRAGMA table_info({table_name});"
        table_info = pd.read_sql(query, connection)
        table_description = table_info[['name', 'type']].rename(columns={'name': 'Column', 'type': 'Data Type'})
        return table_description
    except Exception as e:
        print(e)

def run_sql_script(sql):
    """Run SQL script"""
    try:
        cursor.executescript(sql)
        connection.commit()  # Save changes to the database
    except Exception as e:
        print(e)

@register_line_magic
def sql(sqlquery):
    global _sqldf
    try:
        sqlquery_u = f"""{sqlquery}"""
        _sqldf = pd.read_sql(sqlquery_u, connection)
        connection.commit() 
        print("Result is stored in _sqldf")
        caller_module = sys.modules['__main__']
        setattr(caller_module, '_sqldf', _sqldf)
        return _sqldf
    except TypeError as e1:
        pass
    except Exception as e:
        print(e)
        
def run_sql(sqlquery):
    """Execute SQL Query """
    global _sqldf
    try:
        sqlquery_u = f"""{sqlquery}"""
        _sqldf = pd.read_sql(sqlquery_u, connection)
        connection.commit()
        caller_module = sys.modules['__main__']
        setattr(caller_module, '_sqldf', _sqldf)
        return _sqldf
    except Exception as e:
        print(e)

def run_sql_file(filename):
    """Run SQL script from file"""
    with open(filename, 'r') as file:
        sql_script = file.read()
    
    sql_script_ = f"""{sql_script}"""

    # Run the SQL script
    run_sql_script(sql_script_)

def create_table_from_csv(csv_file, table_name):
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_file)
        
        # Create the table in the database
        df.to_sql(table_name, connection, if_exists='replace', index=False)

        # Commit changes and close the connection
        connection.commit()
        print(f"Table '{table_name}' created successfully in database '{database_name}'.")
    except Exception as e:
        print(e)

# Example usage:
# create_table_from_csv('data.csv', 'example.db', 'example_table')

def close_connection():
    """Close the connection to the database and upload DB to S3 bucket"""
    cursor.close()
    connection.close()
    
    # Copy DB to S3 Bucket
    try:
        filepath = f"./.sqldb/{database_name}.db"
        file_size = os.path.getsize(filepath)
        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading")
        def progress_callback(bytes_transferred):
            progress_bar.update(bytes_transferred)
        s3_client.upload_file(filepath, __S3_BUCKET_NAME, f"sql_db/{database_name}.db",Callback=progress_callback)
        progress_bar.close()
        os.remove(f"./.sqldb/{database_name}.db")
        print('Connection Successfully Closed and Database uploaded to S3')
    except Exception as e:
        print(e)

# Restrict access to private attributes
def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(f"Module has no attribute {name}")
    raise AttributeError(f"{name} not found in module")