import streamlit as st
import threading
import uvicorn
from fastapi import FastAPI
import psycopg2
import pandas as pd
import requests
from LLM import retrieve_and_answer

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

from typing import List
from fastapi import Query

@app.get("/get_metrics")
def get_metrics(metric_names: List[str] = Query(...)):
    placeholders = ', '.join(['%s'] * len(metric_names))
    query = f"SELECT * FROM public.metric_table WHERE metric_name IN ({placeholders})"
    conn = get_connection()
    df = pd.read_sql(query, conn, params=metric_names)
    conn.close()
    return df.to_dict(orient="records")


def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000)

threading.Thread(target=run_api, daemon=True).start()

st.title(" Metrics Table Viewer")

try:
    metric_names = requests.get("http://localhost:8000/get_metric_names").json()
except Exception as e:
    st.error(f"Failed to fetch metric names: {e}")
    st.stop()

selected_metrics = st.multiselect("Select Metrics to View:", metric_names)

if selected_metrics:
    params = "&".join([f"metric_names={m}" for m in selected_metrics])
    try:
        data = requests.get(f"http://localhost:8000/get_metrics?{params}").json()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.info("No data found.")
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")


st.header("Document Q&A Assistant")

user_question = st.text_input("Ask your question about the document here:")

if st.button("Get Answer"):
    if user_question.strip():
        with st.spinner("Fetching answer..."):
            try:
                response = retrieve_and_answer(user_question, top_k=3)
                st.success(response)
            except Exception as e:
                st.error(f"Error fetching answer: {e}")
    else:
        st.warning("Please enter a valid question.")