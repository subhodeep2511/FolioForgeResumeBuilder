import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    user, password, dsn = (
        os.getenv("ORACLE_USER"),
        os.getenv("ORACLE_PASSWORD"),
        os.getenv("ORACLE_DSN"),
    )
    if not all((user, password, dsn)):
        raise RuntimeError("Set ORACLE_USER, ORACLE_PASSWORD and ORACLE_DSN in .env")
    return oracledb.connect(user=user, password=password, dsn=dsn)

def dict_rows(cursor):
    names = [col[0].lower() for col in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]
