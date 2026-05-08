import streamlit as st
from sqlalchemy import create_engine


@st.cache_resource
def get_engine():

    database_url = st.secrets["DATABASE_URL"]

    engine = create_engine(database_url)

    return engine