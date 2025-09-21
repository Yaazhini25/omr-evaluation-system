import pandas as pd
import streamlit as st

answer_file = st.file_uploader("Upload Answer Key (Excel)", type=["xlsx"])
ANSWER_KEY = None

if answer_file:
    df_key = pd.read_excel(answer_file, header=None)  # No header assumed
    ANSWER_KEY = df_key.values.flatten().tolist()    # Flatten to 1D list
    st.success("Answer key loaded successfully!")
