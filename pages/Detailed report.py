# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 12:44:18 2025

@author: Admin
"""

# main.py

import streamlit as st
import pandas as pd
import base64
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# === CONFIG ===
SERVICE_ACCOUNT_FILE = r"C:\Users\Admin\Desktop\solar-ac-customer-mapping-905e295dd0db.json"
CSV_FILE_ID = '17o6xqWHYCTDCUAcRO-dLKGzmNPTuz___'  # Google Drive file ID of the raw CSV
CSV_FILE_ID_2 = '17HdsQxLB6GlDuxd5yYLKPOlw9JrbWl40' # Google Drive file ID of the latest CSV
COLUMNS_TO_DISPLAY = [
    'Topic', 'timestamp', 'PV_kWh', 'OP_kWh', 'BATT_V_min',
    'ac_on_duration_h', 'AC_ROOM_TEMP_avg', 'avg_?T', 'unfiltered_transitions_to_level_0'
]

# === AUTHENTICATION ===
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Decode and load credentials from Streamlit Secrets
key_json = base64.b64decode(st.secrets["gcp_service_account"]["key_b64"]).decode("utf-8")
service_account_info = json.loads(key_json)

creds = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=creds)

# === DOWNLOAD CSV FROM GOOGLE DRIVE ===
def download_csv(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    df = pd.read_csv(fh)
    return df

# # === STREAMLIT APP ===
# st.set_page_config(page_title="Ecozen Solar AC", layout="wide")
# st.title("📉 Solar AC reports")

# # Session state for data caching
# if "df" not in st.session_state:
#     st.session_state.df = pd.DataFrame()

# # Manual Refresh
# if st.button("🔄 Refresh Data"):
#     with st.spinner("Downloading latest CSV from Google Drive..."):
#         df = download_csv(CSV_FILE_ID)
#         df = df[COLUMNS_TO_DISPLAY]
#         df = df.rename(columns={
#             'avg_?T': 'avg_delta_temp',
#             'unfiltered_transitions_to_level_0': 'Trips'
#         })
#         st.session_state.df = df
#     st.success("✅ Data refreshed!")

# # Show dataframe
# if not st.session_state.df.empty:
#     st.subheader("📋 Metrics Data (From Google Drive CSV)")
#     st.dataframe(st.session_state.df, use_container_width=True)
# else:
#     st.info("Click '🔄 Refresh Data from Google Drive' to load data.")

# === STREAMLIT APP ===
st.set_page_config(page_title="Ecozen Solar AC", layout="wide")
st.title("📉 Solar AC reports")

# Session state for data caching
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

# Manual Refresh
if st.button("🔄 Refresh Data"):
    with st.spinner("Downloading latest CSV from Google Drive..."):
        df = download_csv(CSV_FILE_ID)
        df = df[COLUMNS_TO_DISPLAY]
        df = df.rename(columns={
            'avg_?T': 'avg_delta_temp',
            'unfiltered_transitions_to_level_0': 'Trips'
        })
        st.session_state.df = df
    st.success("✅ Data refreshed!")

# Show dataframe if available
if not st.session_state.df.empty:
    st.subheader("📋 Metrics Data (From Google Drive CSV)")

    # Dropdown to select Topic
    all_topics = st.session_state.df['Topic'].dropna().astype(str).unique().tolist()
    topic_options = ["All"] + sorted(all_topics)
    selected_topic = st.selectbox("Select a device (Topic):", topic_options)

    # Filter DataFrame based on selection
    if selected_topic == "All":
        filtered_df = st.session_state.df
    else:
        filtered_df = st.session_state.df[st.session_state.df['Topic'] == selected_topic]

    # Display filtered data
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("Click '🔄 Refresh Data from Google Drive' to load data.")

