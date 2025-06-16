# -*- coding: utf-8 -*-
"""
Created on Thu May 29 13:06:09 2025

@author: Admin
"""

import requests
import urllib.parse
import pandas as pd

def get_auth_token():
    """Get bearer token from Ecozen auth server"""
    token_url = 'https://openid.ecozen.ai/realms/ecozen/protocol/openid-connect/token'
    payload = {
        'client_id': 'solar-ac-internal',
        'client_secret': 'BEASk36yeoKx7YkEQe42RCl6RuSlUxX5',
        'grant_type': 'client_credentials'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response.status_code}, {response.text}")
    return response.json()['access_token']

def getData(machineId, startDate, endDate, paramList="Topic,createdAt,TBN,W_STAT,GRID_V,PV_W", limit=200000):
    """
    Fetches device data for a given machine ID and date range.

    machineId: str (e.g. 'EZMCISAC00013')
    startDate, endDate: str in 'YYYY-MM-DD' format
    paramList: comma-separated string of fields to fetch
    limit: int, number of records to fetch
    """
    token = get_auth_token()

    base_url = 'http://services.ecozen.ai/solar_ac/api/v2/device/between-dates/'
    download = 'N'
    fileFormat = 'JSON'
    
    # Final POST URL
    final_url = base_url + f"{machineId}/{startDate}/{endDate}/{download}/{fileFormat}"

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    form_data = {
        'paramList': paramList,
        'limit': limit
    }

    response = requests.post(final_url, headers=headers, data=form_data)
    print(f"Request status code: {response.status_code}")

    if response.status_code != 200:
        print("Error:", response.text)
        return None

    data = response.json()
    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
     df = pd.DataFrame(data['data'])
     if not df.empty and 'createdAt' in df.columns:
         df['createdAt'] = pd.to_datetime(df['createdAt'])
         df = datetimeProcessingafterDownload(df)
     return df
    else:
        print("Unexpected data format returned.")
        return None
def datetimeProcessingafterDownload(data):
    df = data.copy()
    col_list = ['deviceTime','timestamp','starttime','endtime','rundate', 'startTime', 'endTime', 'createdAt']
    for col in col_list:
        if col in df:
            df[col] = pd.to_datetime(df[col])
            df[col] = df[col].dt.tz_convert('Asia/Kolkata')
    return df  

# df = getData(
#     machineId='EZMCISAC00013',
#     startDate='2025-05-28',
#     endDate='2025-05-29',
#     paramList="Topic,createdAt,TBN,W_STAT,GRID_V,PV_W"
# )
# paramList="TBN,W_STAT,GRID_V,GRID_F,PV_V,PV_W,BATT_V,BATT_CAP,BATT_CHG_I,BATT_DSCHG_I,OP_V,OP_F,OP_VA,OP_W,LOAD_PER,DUAL_OP_SW_V,DUAL_OP_SDN_V,CPU_VER,CELL_BAL_SW,BATT_PC,NOM_OP_VA,NOM_OP_W,NOM_GRID_V,NOM_GRID_I,RATED_BATT_V,NOM_OP_RATED_V,NOM_OP_RATED_F,NOM_OP_RATED_I,FLT,ALM,RSV,CHG_DSCHG_PRIO,OP_PRIO,MODE_SEL,BATT_TYPE,OP_F_1,MAX_CHG_I,OP_V_1,MAX_AC_CHG_I,BCK_TO_UTIL,Bat_Volt_Back_To_Bat,BATT_CV_V,BATT_FLOAT_V,BATT_V_SHUTOFF,EQ_V,EQ_TIME,EQ_TIMEOUT,EQ_INT,PV_CHG_STAT,NTC_MAX_T,PV_ON_PWR,GRID_OP,GRID_I,LED_PATT_LIGHT,EQ_ACT_IMM,PV_IP_V,PV_IP_W,BATT_I,AC_PWR_STAT,AC_MODE,AC_SET_TEMP,AC_IDU_STAT,AC_ROOM_TEMP,AC_ROOM_TEMP_FRACT,AC_FAN_L,AC_FAN_RPM,AC_SP_1,AC_ADJ_LVL,AC_SWING,AC_ERR_CODE,AC_SP3,AC_PWR,BATT_SOC,PV_KWH,BATT_KWH,LOAD_KWH,GRID_KWH,AC_PWR_4,FILE SIZE,BIN_STAT,INT TIME,SNG,SYS UPTIME,IOT_TEMP,APN,LOG INT,ET SWV,TSP,M66 BSV,ICCID,IMEI,NW_TYPE,RES1,RES2,N_AC_W,RES4,RES5,RES6"

# plt.plot(df.createdAt, df.PV_W)
