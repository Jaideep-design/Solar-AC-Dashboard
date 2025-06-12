# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 17:23:07 2025

@author: Admin
"""

# main.py

import streamlit as st
import pandas as pd
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# === CONFIG ===
SERVICE_ACCOUNT_FILE = r"C:\Users\Admin\Desktop\solar-ac-customer-mapping-905e295dd0db.json"
CSV_FILE_ID = '17o6xqWHYCTDCUAcRO-dLKGzmNPTuz___'    # raw data
CSV_FILE_ID_2 = '17HdsQxLB6GlDuxd5yYLKPOlw9JrbWl40'   # latest data
COLUMNS_RAW = ['Topic', 'timestamp', 'PV_kWh', 'OP_kWh', 'BATT_V_min',
               'ac_on_duration_h', 'AC_ROOM_TEMP_avg', 'avg_?T', 'unfiltered_transitions_to_level_0']
COLUMNS_LATEST = ['Topic', 'BATT_V_min']

# === AUTHENTICATION ===
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=creds)

# === DOWNLOAD CSV FILE FROM GOOGLE DRIVE ===
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

# === DATA PROCESSING FUNCTION ===
def process_data(df1_raw, df2_latest):
    df1 = df1_raw[COLUMNS_RAW].copy()
    df2 = df2_latest[COLUMNS_LATEST].copy()
    
    # Convert timestamp
    df1['timestamp'] = pd.to_datetime(df1['timestamp'], format='%d-%m-%Y')
    
    # Latest date per topic
    latest_dates = df1.groupby('Topic')['timestamp'].max().reset_index()
    latest_dates.columns = ['Topic', 'latest_date']
        
    # Merge and filter
    df1 = df1.merge(latest_dates, on='Topic')
    df_last7 = df1[df1['timestamp'] >= df1['latest_date'] - pd.Timedelta(days=6)]
    
    # Calculate average
    avg_last7 = df_last7.groupby('Topic')[[
        'PV_kWh', 'OP_kWh', 'ac_on_duration_h',
        'AC_ROOM_TEMP_avg', 'avg_?T', 'unfiltered_transitions_to_level_0'
    ]].mean().reset_index()
    avg_last7.columns = ['Topic'] + [col + '_last7_avg' for col in avg_last7.columns if col != 'Topic']
    
    avg_last7.iloc[:, 1:] = avg_last7.iloc[:, 1:].round(0)
    avg_last7 = avg_last7.merge(latest_dates, on='Topic', how='inner')
    avg_last7 = avg_last7.rename(columns={
        'latest_date': 'timestamp',
        'avg_?T_last7_avg': 'avg_delta_temp',
        'unfiltered_transitions_to_level_0_last7_avg': 'Trips'
    })
    avg_last7['timestamp'] = avg_last7['timestamp'].dt.strftime('%Y-%m-%d')


    # Merge with df2
    result_df = df2.merge(avg_last7, on='Topic', how='left')
    return result_df

# === STREAMLIT APP ===
# st.set_page_config(page_title="Ecozen Solar AC", layout="wide")
# st.title("📊 Dashboard")

# if st.button("🔄 Refresh & Process Data"):
#     with st.spinner("Fetching CSVs from Google Drive..."):
#         df_raw = download_csv(CSV_FILE_ID)
#         df_latest = download_csv(CSV_FILE_ID_2)
#         final_df = process_data(df_raw, df_latest)
#         st.session_state.final_df = final_df
#     st.success("✅ Data refreshed and processed!")

# # Show data
# if "final_df" in st.session_state:
#     st.subheader("📋 Final Merged Data")
#     st.dataframe(st.session_state.final_df, use_container_width=True)
# else:
#     st.info("Click '🔄 Refresh & Process Data' to begin.")

# === STREAMLIT APP ===
st.set_page_config(page_title="Ecozen Solar AC", layout="wide")
st.title("📊 Dashboard")

# Refresh button
if st.button("🔄 Refresh & Process Data"):
    with st.spinner("Fetching CSVs from Google Drive..."):
        df_raw = download_csv(CSV_FILE_ID)
        df_latest = download_csv(CSV_FILE_ID_2)
        final_df = process_data(df_raw, df_latest)
        st.session_state.final_df = final_df
    st.success("✅ Data refreshed and processed!")

# Show data if available
if "final_df" in st.session_state:
    st.subheader("📋 Final Merged Data")

    # Dropdown for Topic selection (with default "All" option)
    all_topics = st.session_state.final_df['Topic'].unique().tolist()
    topic_options = ["All"] + sorted(all_topics)
    selected_topic = st.selectbox("Select a device (Topic):", topic_options)

    # Filter DataFrame
    if selected_topic == "All":
        filtered_df = st.session_state.final_df
    else:
        filtered_df = st.session_state.final_df[st.session_state.final_df['Topic'] == selected_topic]

    # Display the filtered data
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("Click '🔄 Refresh & Process Data' to begin.")