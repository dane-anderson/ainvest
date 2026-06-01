import os
import streamlit as st
from sqlalchemy import create_engine


@st.cache_resource
def get_engine():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        try:
            database_url = st.secrets.get("DATABASE_URL")
        except Exception:
            database_url = None

    if not database_url:
        raise ValueError("DATABASE_URL not found in environment or secrets")

    engine = create_engine(database_url)

    return engine