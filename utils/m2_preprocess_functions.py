# -*- coding: utf-8 -*-
"""
Created on Wed May 14 21:28:34 2025

@author: Admin
"""


import pandas as pd
import numpy as np
from datetime import timedelta


RES2_FLAGS = {
    0: "overcurrent",
    1: "batt_mode_high",
    2: "output_off_overcurrent",
}

FLT_FLAGS = {
    0: "Fan_Locked",
    1: "Over_Temperature",
    2: "Battery_Voltage_High",
    3: "Battery_Voltage_Low",
    4: "Output_Shorted",
    5: "INV_Voltage_Over",
    6: "Over_Load",
    7: "Bus_Voltage_Over",
    8: "Bus_Soft_Failed",
    9: "Over_Current",
    10: "Bus_Voltage_Under",
    11: "INV_Soft_Failed",
    12: "DC_Voltage_Over",
    13: "CT_Fault",
    14: "INV_Voltage_Low",
    15: "PV_Voltage_High"
}

ALM_FLAGS ={
        0: "Fan Locked",
        1: "Over Temperature",
        2: "Battery Voltage Low",
        3: "Over Load",
        4: "Output Power Derating",
        5: "PV Energy Weak",
        6: "AC Voltage High",
        7: "Battery Equalization",
        8: "No Battery"
      }

BIN_STAT_FLAGS  = {
    0: "gps",
    1: "inverter comm fault",
    2: "Ac comm fault",
    3: "Sim detect",
    }

def parse_bitfield_flags(val: int or str, flag_map: dict, bit_width: int = 16) -> dict:
    """
    Converts an integer or binary string into a dictionary of flag names and their on/off states (0/1).
    Args:
        val: Integer or binary string.
        flag_map: A dict mapping bit positions (0 = LSB) to flag names.
        bit_width: Number of bits to pad binary representation to (default=16).
    Returns:
        Dict with flag names as keys and 0/1 as values.
    """
    try:
        if isinstance(val, str) and set(val) <= {'0', '1'}:
            bit_str = val.zfill(bit_width)
        else:
            bit_str = bin(int(val))[2:].zfill(bit_width)
        return {flag_map[i]: int(bit_str[-(i + 1)]) for i in range(bit_width) if i in flag_map}
    except Exception:
        return {flag_map[i]: None for i in range(bit_width) if i in flag_map}


def apply_bitfield_flags(df: pd.DataFrame, column_name: str, flag_map: dict, bit_width: int = 16) -> pd.DataFrame:
    """
    Applies flag parsing logic to a given bitfield column in a DataFrame.
    Args:
        df: DataFrame with raw data.
        column_name: The name of the column containing the bitfield value.
        flag_map: A dict mapping bit positions to flag names.
        bit_width: Total bits in the bitfield (default=16).
    Returns:
        Updated DataFrame with new columns for each flag.
    """
    flag_df = df[column_name].fillna(0).apply(lambda val: parse_bitfield_flags(val, flag_map, bit_width)).apply(pd.Series)
    flag_df = flag_df.add_prefix(column_name+"_")
    return pd.concat([df, flag_df], axis=1),  flag_df

def preprocess_ac_dataframe(df):
    """
    Preprocesses the AC dataframe to:
    - Compute deltatime and cumulative time in seconds
    - Normalize AC room temperature
    - Parse RES2 binary status bits into individual flag columns
    - Filter out long time gaps (> 120 sec)

    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with columns: 'createdAt', 'AC_ROOM_TEMP', 'RES2'

    Returns:
    --------
    df : pd.DataFrame
        Cleaned and preprocessed dataframe
    """
    df = df.copy()

    # Time delta and cumulative time
    df = df.sort_values(by="createdAt", ascending=True)
    df["deltatime"] = df["createdAt"].diff().dt.total_seconds()
    df["time_sec"] = df["deltatime"].cumsum()

    # Room temperature correction
    df["AC_ROOM_TEMP"] = df["AC_ROOM_TEMP"] - 64
    df["AC_ROOM_TEMP"] = df["AC_ROOM_TEMP"].apply(lambda x: x if x > 0 else 0)

    df, _ = apply_bitfield_flags(df, "RES2", RES2_FLAGS, bit_width=3) 
    df, _ = apply_bitfield_flags(df, "FLT", FLT_FLAGS)
    df, _ = apply_bitfield_flags(df, "ALM", ALM_FLAGS)
    df, _ = apply_bitfield_flags(df, "BIN_STAT", BIN_STAT_FLAGS)
    # # Ensure RES2 is a 16-bit binary string
    # df["RES2"] = df["RES2"].astype(str).str.zfill(16)
    # df["FLT"] = df["FLT"].astype(int).apply(lambda x: format(x, '016b'))
    # df["ALM"] = df["ALM"].astype(int).apply(lambda x: format(x, '016b'))


    # # Extract binary status bits (from right to left)
    # df["Bit0_overcurrent"]    = df["RES2"].str[-1].astype(int)
    # df["Bit1_batt_mode_high"] = df["RES2"].str[-2].astype(int)
    # df["Bit2_output_off_oc"]  = df["RES2"].str[-3].astype(int)

    # Filter out rows with long time gaps
    df = df[df["deltatime"] <= 120].reset_index(drop=True)
    df["ΔT"] = df["AC_ROOM_TEMP"] - df["AC_SET_TEMP"]
    
    ######
    # ac_load_dict = {0:50, 1: 766, 2:971, 3: 1175, 4: 1459, 5: 1680 }
    # buffer_load = 0
    # df["non_ac_load_W"] = df.apply(lambda row: max(0, row["OP_W"]-ac_load_dict.get(row["AC_ADJ_LVL"], 0) + buffer_load), axis=1)
    # df["ac_load_W"] = df["OP_W"] - df["non_ac_load_W"]
    df = calculate_ac_and_non_ac_loads_with_wait(df)
    ########
    return df

def calculate_ac_and_non_ac_loads_with_wait(df):
    """
    Calculates non-AC and AC load power with a wait time after level changes.

    Parameters:
    -----------
    df : pd.DataFrame
        Must contain 'createdAt', 'AC_ADJ_LVL', and 'OP_W' columns.
    ac_load_dict : dict, optional
        Mapping of AC_ADJ_LVL to power in watts.
    buffer_load : float, optional
        Buffer to be added to AC load power during subtraction.

    Returns:
    --------
    df : pd.DataFrame
        Updated with 'non_ac_load_W' and 'ac_load_W' columns.
    """
    
    ac_load_dict = {0: 50, 1: 766, 2: 971, 3: 1175, 4: 1459, 5: 1680}
    buffer_load=0
    
    df = df.sort_values("createdAt").reset_index(drop=True)
    df["non_ac_load_W"] = np.nan
    df["ac_load_W"] = np.nan

    last_valid_time = df["createdAt"].iloc[0]
    last_level = df["AC_ADJ_LVL"].iloc[0]

    for i in range(len(df)):
        current_time = df.loc[i, "createdAt"]
        current_level = df.loc[i, "AC_ADJ_LVL"]

        # Detect level change and set appropriate wait time
        if current_level != last_level:
            if last_level == 0 and current_level == 1:
                wait_duration = timedelta(minutes=5)
            else:
                wait_duration = timedelta(minutes=1)
            last_valid_time = current_time + wait_duration
            last_level = current_level

        # Skip calculation during wait time
        if current_time < last_valid_time:
            continue

        # Compute loads
        ac_power = ac_load_dict.get(current_level, 0)
        op_power = df.loc[i, "OP_W"]
        non_ac = max(0, op_power - ac_power + buffer_load)

        df.loc[i, "non_ac_load_W"] = non_ac
        df.loc[i, "ac_load_W"] = op_power - non_ac

    return df
