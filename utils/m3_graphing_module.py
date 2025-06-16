# -*- coding: utf-8 -*-
"""
Created on Wed May 14 21:33:41 2025

@author: Admin
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def plot_solar_ac_multiplot(df_plot, filename, savepath):
    x_colname = "createdAt"
    topic = df_plot.Topic.iloc[0]
    df_plot = df_plot.sort_values(x_colname).reset_index(drop=True)

    fig = make_subplots(
        rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        subplot_titles=(
            "Power", "Battery Voltage", "Battery Current",
            "AC Levels", "AC Temp", "AC Modes", "Grid and PV Voltages"
        ),
        row_heights=[0.15]*7
    )

    # Row 1: PV_W and OP_W
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.PV_W, mode='lines', name='PV_W'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.OP_W, mode='lines', name='total_load_W'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.ac_load_W, mode='lines', name='ac_load_W'), row=1, col=1)
    

    # Row 2: Battery Voltage and Shutoff
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_V, mode='lines+markers', name='BATT_V'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_V_SHUTOFF, mode='lines', name='BATT_V_SHUTOFF'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_FLOAT_V, mode='lines', name='BATT_FLOAT_V'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_TYPE, mode='lines', name='BATT_TYPE'), row=2, col=1)

    # Row 3: Battery Current with zones
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.BATT_I, mode='lines+markers', name='BATT_I'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot.MAX_CHG_I, mode='lines+markers', name='MAX_CHG_I'), row=3, col=1)
    
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
    for i in range(1, 8):
        fig.update_xaxes(showticklabels=True, row=i, col=1)

    # Layout
    fig.update_layout(
        height=1500,
        width=1100,
        title=f"{topic} - Multi-axis Visualization",
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        hovermode="x unified"
    )

    # Save as HTML
    os.makedirs(savepath, exist_ok=True)
    full_path = os.path.join(savepath, filename)
    fig.write_html(full_path)
    print(f"Plot saved to: {full_path}")

def plot_fault_alarm_codes(df_plot, filename, savepath):
    x_colname = "createdAt"
    topic = df_plot.Topic.iloc[0]
    df_plot = df_plot.sort_values(x_colname).reset_index(drop=True)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Fault Codes", "Alarm Codes", "COM_faults"),row_heights=[0.15]*3)

    # Row 1: Fault Codes
    for col in df_plot.columns:
        if col.startswith("FLT_"):
            fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot[col], mode='lines',line=dict(shape='hv'), visible='legendonly', name=col), row=1, col=1)

    # Row 2: Alarm Codes
    for col in df_plot.columns:
        if col.startswith("ALM_"):
            fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot[col], mode='lines', line=dict(shape='hv'), visible='legendonly', name=col), row=2, col=1)
    
    # Row 3: Alarm Codes
    for col in df_plot.columns:
        if col.startswith("BIN_STAT_"):
            fig.add_trace(go.Scatter(x=df_plot[x_colname], y=df_plot[col], mode='lines', line=dict(shape='hv'), visible='legendonly', name=col), row=3, col=1)

    # Enable X-axis on all subplots
    for i in range(1, 3):
        fig.update_xaxes(showticklabels=True, row=i, col=1)

    # fig.update_layout(
    #     height=800,
    #     width=1000,
    #     title=f"{topic} - Fault and Alarm Codes",
    #     legend=dict(orientation="v", yanchor="auto", y=-0.2, xanchor="center", x=0.5),
    #     hovermode="x unified"
    # )
    # Format layout
    fig.update_layout(
        height=600,
        width=1200,
        title_text=f"{topic} - Fault & Alarm Flags Over Time",
        # xaxis_title="Timestamp",
        yaxis_title="Fault Flags",
        # xaxis2_title="Timestamp",
        yaxis2_title="Alarm Flags",
        xaxis3_title="Timestamp",
        yaxis3_title="COM_Faults",
        template="plotly_white",
        showlegend=True
    )

    # Save as HTML
    os.makedirs(savepath, exist_ok=True)
    full_path = os.path.join(savepath, filename)
    fig.write_html(full_path)
    print(f"Plot saved to: {full_path}")
