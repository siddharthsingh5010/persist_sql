import pandas as pd
import numpy as np 
import sqlite3
import os
import boto3
import botocore
from IPython.core.magic import register_line_magic

global __AWS_ACCESS_KEY
global __AWS_SECRET_KEY
global __S3_BUCKET_NAME

global connection
global cursor
global database_name
global s3_client
global _sqldf

print("Follow the below to use Persistent SQL : \n 1. configure_aws(aws_key, aws_secret, aws_bucket) or configure_aws() using environment variables \n 2. connect_db(dbname) \n 3. %sql query to run any sql query with magic command \n 4. close_connection() to close the connection")

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
    if not os.path.exists("./.sqldb"):
        os.mkdir("./.sqldb")
    try:
        s3_client.download_file(__S3_BUCKET_NAME, f"sql_db/{dbname}.db", f"./.sqldb/{dbname}.db")
        os.chmod(f"./.sqldb/{dbname}.db", 0o666)
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

def close_connection():
    """Close the connection to the database and upload DB to S3 bucket"""
    cursor.close()
    connection.close()
    # Copy DB to S3 Bucket
    try:
        s3_client.upload_file(f"./.sqldb/{database_name}.db", __S3_BUCKET_NAME, f"sql_db/{database_name}.db")
        os.remove(f"./.sqldb/{database_name}.db")
        print('Connection Successfully Closed and Database uploaded to S3')
    except Exception as e:
        print(e)