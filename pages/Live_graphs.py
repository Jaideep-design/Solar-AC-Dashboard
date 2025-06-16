# -*- coding: utf-8 -*-
"""
Streamlit Page: AC Data Visualization
Created on Mon Jun 16 11:30:00 2025
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import m0_SAC_api_functions as m0api
from utils import m2_preprocess_functions as ppf

# -------------------- UI Inputs --------------------
st.title("AC Analytics Dashboard")

# You can dynamically fetch these from a config or API too
device_list = [f"EZMCISAC{str(i).zfill(5)}" for i in range(1, 301)]
selected_device = st.selectbox("Select Device ID", device_list)

start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

submit = st.button("Fetch and Visualize Data")

# -------------------- Main Logic --------------------
if submit:
    with st.spinner("Fetching and processing data..."):
        paramList = (
            "TBN,W_STAT,GRID_V,GRID_F,PV_V,PV_W,BATT_V,BATT_CAP,BATT_CHG_I,"
            "BATT_DSCHG_I,OP_V,OP_F,OP_VA,OP_W,LOAD_PER,DUAL_OP_SW_V,DUAL_OP_SDN_V,"
            "CPU_VER,CELL_BAL_SW,BATT_PC,NOM_OP_VA,NOM_OP_W,NOM_GRID_V,NOM_GRID_I,"
            "RATED_BATT_V,NOM_OP_RATED_V,NOM_OP_RATED_F,NOM_OP_RATED_I,FLT,ALM,RSV,"
            "CHG_DSCHG_PRIO,OP_PRIO,MODE_SEL,BATT_TYPE,OP_F_1,MAX_CHG_I,OP_V_1,"
            "MAX_AC_CHG_I,BCK_TO_UTIL,Bat_Volt_Back_To_Bat,BATT_CV_V,BATT_FLOAT_V,"
            "BATT_V_SHUTOFF,EQ_V,EQ_TIME,EQ_TIMEOUT,EQ_INT,PV_CHG_STAT,NTC_MAX_T,"
            "PV_ON_PWR,GRID_OP,GRID_I,LED_PATT_LIGHT,EQ_ACT_IMM,PV_IP_V,PV_IP_W,"
            "BATT_I,AC_PWR_STAT,AC_MODE,AC_SET_TEMP,AC_IDU_STAT,AC_ROOM_TEMP,"
            "AC_ROOM_TEMP_FRACT,AC_FAN_L,AC_FAN_RPM,AC_SP_1,AC_ADJ_LVL,AC_SWING,"
            "AC_ERR_CODE,AC_SP3,AC_PWR,BATT_SOC,PV_KWH,BATT_KWH,LOAD_KWH,GRID_KWH,"
            "AC_PWR_4,FILE SIZE,BIN_STAT,INT TIME,SNG,SYS UPTIME,IOT_TEMP,APN,"
            "LOG INT,ET SWV,TSP,M66 BSV,ICCID,IMEI,NW_TYPE,RES1,RES2,N_AC_W,"
            "RES4,RES5,RES6"
        )

        try:
            df = m0api.getData(
                machineId=selected_device,
                startDate=start_date.strftime("%Y-%m-%d"),
                endDate=end_date.strftime("%Y-%m-%d"),
                paramList=paramList
            )

            if df.empty:
                st.warning("No data returned for selected device and date range.")
            else:
                df = ppf.preprocess_ac_dataframe(df)

                # -------------------- Plotting --------------------                
                df_plot = df.copy()
                x_colname = "createdAt"
                topic = df_plot.Topic.iloc[0]
                df_plot = df_plot.sort_values(x_colname).reset_index(drop=True)
                
                fig = make_subplots(
                    rows=8, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                    subplot_titles=(
                        "Power", "Battery Voltage", "Battery Current",
                        "AC Levels", "AC Temp", "AC Modes", "Grid and PV Voltages"
                    ),
                    row_heights=[0.15]*8
                )
                
                # Row 1: PV_W and OP_W
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.PV_W, mode='lines', name='PV_W'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.OP_W, mode='lines', name='total_load_W'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.ac_load_W, mode='lines', name='ac_load_W'), row=1, col=1)
                
                
                # Row 2: Battery Voltage and Shutoff
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_V, mode='lines+markers', name='BATT_V'), row=2, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_V_SHUTOFF, mode='lines', name='BATT_V_SHUTOFF'), row=2, col=1)
                
                # Row 3: Battery Current with zones
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_I, mode='lines+markers', name='BATT_I'), row=3, col=1)
                fig.add_hline(y=0, line_dash="dash", row=3, col=1)
                fig.add_hline(y=33, line_dash="dash", row=3, col=1)
                fig.add_shape(type="rect", xref="x", yref="y3", x0=df_plot[x_colname].iloc[0], x1=df_plot[x_colname].iloc[-1],
                              y0=-12, y1=4, fillcolor="red", opacity=0.3, line_width=0)
                fig.add_shape(type="rect", xref="x", yref="y3", x0=df_plot[x_colname].iloc[0], x1=df_plot[x_colname].iloc[-1],
                              y0=16, y1=24, fillcolor="green", opacity=0.3, line_width=0)
                
                # Row 4: AC Levels
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.AC_ADJ_LVL, mode='lines+markers', name='AC_ADJ_LVL'), row=4, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.AC_PWR_STAT, mode='lines', name='AC_ON_OFF'), row=4, col=1)
                
                # Row 5: AC Temperatures
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.AC_SET_TEMP, mode='lines', name='AC_Set_T'), row=5, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.AC_ROOM_TEMP, mode='lines+markers', name='AC_Room_T'), row=5, col=1)
                
                # Row 6: AC Modes
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.AC_FAN_L, mode='lines+markers', name='AC_FAN_L'), row=6, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.AC_MODE, mode='lines+markers', name='AC_MODE'), row=6, col=1)
                fig.add_hline(y=1, line_dash="dash", line_color="green", row=6, col=1)
                fig.add_hline(y=4, line_dash="dash", line_color="green", row=6, col=1)
                fig.add_hline(y=6, line_dash="dash", line_color="red", row=6, col=1)
                
                # Row 7: Grid and PV Voltages
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.OP_V, mode='lines',line=dict(color='blue'), name='OP_V'), row=7, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.GRID_V, mode='lines',line=dict(color='red'), name='GRID_V'), row=7, col=1)
                fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.PV_V, mode='lines',line=dict(color='green'), name='PV_V'), row=7, col=1)

                # --- Fault/Alarm/BIN Subplots (8–10) ---                
                for col in df_plot.columns:
                    if col.startswith("BIN_STAT_"):
                        fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot[col], mode='lines', line=dict(shape='hv'), visible='legendonly', name=col), row=8, col=1)

                  # Highlight high battery mode regions
                highmode_mask = df_plot.RES2_batt_mode_high == 1
                highmode_regions = []
                in_region = False
                for i in range(len(df_plot)):
                    if highmode_mask[i] and not in_region:
                        start = df_plot[x_colname][i]
                        in_region = True
                    elif not highmode_mask[i] and in_region:
                        end = df_plot[x_colname][i]
                        highmode_regions.append((start, end))
                        in_region = False
                if in_region:
                    highmode_regions.append((start, df_plot[x_colname].iloc[-1]))
                
                for start, end in highmode_regions:
                    for row in [2, 3]:
                        fig.add_vrect(
                            x0=start,
                            x1=end,
                            fillcolor="orange",
                            opacity=0.2,
                            layer="below",
                            line_width=0,
                            row=row, col=1
                        )
                
                # Enable X-axis on all subplots
                for i in range(1, 9):
                    fig.update_xaxes(showticklabels=True, row=i, col=1)
                
                # Layout
                fig.update_layout(
                    height=1500,
                    # width=1100,
                    title=f"{topic} - Multi-axis Visualization",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                    hovermode="x unified"
                )

                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error: No Data Available for selected device between the provided dates : {e}")
