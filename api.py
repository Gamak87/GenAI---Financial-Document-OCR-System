from fastapi import FastAPI, Query
from typing import List
import psycopg2
import pandas as pd

app = FastAPI()

def get_connection():
    return psycopg2.connect(
        dbname="metrics",
        user="postgres",
        password="akg@0187",
        host="localhost",
        port="5432"
    )

@app.get("/get_metric_names")
def get_metric_names():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT metric_name FROM metric_table")
    names = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return names

@app.get("/get_metrics")
def get_metrics(metric_names: List[str] = Query(...)):
    placeholders = ', '.join(['%s'] * len(metric_names))
    query = f"SELECT * FROM public.metric_table WHERE metric_name IN ({placeholders})"
    conn = get_connection()
    df = pd.read_sql(query, conn, params=metric_names)
    conn.close()
    return df.to_dict(orient="records")
