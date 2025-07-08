# streamlit run your_script.py

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide")
st.title("Visualización de Logs")

# Add device type selection dropdown
device_type = st.selectbox("Seleccione el tipo de dispositivo", ["mSafe", "mSafe 3 AC", "mSafe 3 BC"])


def detect_device_type(lines):
    """Detect the device type based on the file content."""
    # Check for mSafe 3 BC format (has Pline, P2, P3, Ppilot, Ppower columns)
    if any(
        ";" in line and len(line.split(";")) == 7 and all(x.strip().isdigit() for x in line.split(";")[2:7])
        for line in lines
    ):
        return "mSafe 3 BC"

    # Check for mSafe format (has WP, LP, T3, P4, AP, FLOW columns)
    if any(";" in line and len(line.split(";")) >= 8 and "MSCF" in line for line in lines):
        return "mSafe"

    return None


def parse_msafe3bc_data(lines):
    """Parse data for mSafe 3 BC device."""
    data_start_line = None
    events_line = None

    for i, line in enumerate(lines):
        if ";" in line and len(line.split(";")) >= 7:
            try:
                date_str = line.split(";")[0].strip()
                datetime.strptime(date_str, "%m/%d/%Y")
                data_start_line = i
                break
            except ValueError:
                continue

    for i, line in enumerate(lines):
        if "NUMBER OF EVENTS:" in line:
            events_line = i
            break

    if data_start_line is not None and events_line is not None:
        # Parse pressure data
        data_lines = lines[data_start_line:events_line]
        data = [line.strip().split(";") for line in data_lines]
        df = pd.DataFrame(data, columns=["DATE", "TIME", "Pline", "P2", "P3", "Ppilot", "Ppower"])

        # Convert columns to numeric
        numeric_cols = ["Pline", "P2", "P3", "Ppilot", "Ppower"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])

        df["DATE"] = pd.to_datetime(df["DATE"])

        # Parse battery data
        battery_lines = [line.strip().split(";") for line in lines if "BATTERY STATUS" in line]
        battery_data = []
        for entry in battery_lines:
            if len(entry) >= 5:  # Ensure we have enough columns
                try:
                    date = entry[0].strip()
                    time = entry[1].strip()
                    cb = float(entry[2].split(": ")[1])
                    pb1 = float(entry[3].split(": ")[1])
                    pb2 = float(entry[4].split(": ")[1])
                    battery_data.append([date, time, cb, pb1, pb2])
                except (ValueError, IndexError):
                    continue

        battery_df = pd.DataFrame(battery_data, columns=["DATE", "TIME", "CB", "PB1", "PB2"])
        battery_df["DATE"] = pd.to_datetime(battery_df["DATE"])

        # Parse temperature data
        temp_lines = [line.strip().split(";") for line in lines if "TEMPERATURE STATUS" in line]
        temp_data = []
        for entry in temp_lines:
            if len(entry) >= 3:
                try:
                    date = entry[0].strip()
                    time = entry[1].strip()
                    temp = float(entry[2].split(":")[1])
                    temp_data.append([date, time, temp])
                except (ValueError, IndexError):
                    continue

        temp_df = pd.DataFrame(temp_data, columns=["DATE", "TIME", "TEMPERATURE"])
        temp_df["DATE"] = pd.to_datetime(temp_df["DATE"])

        # Parse events
        events_start_line = None
        for i, line in enumerate(lines):
            if line.startswith("NUMBER OF EVENTS:"):
                events_start_line = i + 2
                break

        if events_start_line is not None:
            event_data = [line.strip().split(";") for line in lines[events_start_line:]]
            max_columns = max(len(event) for event in event_data)
            event_data = [event + [None] * (max_columns - len(event)) for event in event_data]
            header = event_data[0]
            events_df = pd.DataFrame(event_data[1:], columns=header)
            filtered_events = events_df[
                ~events_df["EVENT ID"].str.contains("BATTERY STATUS \\(CB\\)|TEMPERATURE STATUS", regex=True)
            ]
            event_counts = filtered_events["EVENT ID"].value_counts()
        else:
            event_counts = None

        return df, battery_df, temp_df, event_counts
    return None, None, None, None


def parse_msafe_data(lines):
    """Parse data for mSafe device."""
    data_start_line = None
    events_line = None

    for i, line in enumerate(lines):
        if ";" in line and len(line.split(";")) >= 8 and "MSCF" in line:
            try:
                date_str = line.split(";")[0].strip()
                datetime.strptime(date_str, "%m/%d/%Y")
                data_start_line = i
                break
            except ValueError:
                continue

    for i, line in enumerate(lines):
        if "NUMBER OF EVENTS:" in line:
            events_line = i
            break

    if data_start_line is not None and events_line is not None:
        data_lines = lines[data_start_line:events_line]
        data = [line.strip().split(";") for line in data_lines]
        df = pd.DataFrame(data, columns=["DATE", "TIME", "WP", "LP", "T3", "P4", "AP", "FLOW", "UNIT"])

        # Convert columns to numeric
        numeric_cols = ["WP", "LP", "T3", "P4", "AP", "FLOW"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])

        df["DATE"] = pd.to_datetime(df["DATE"])

        # Parse battery data
        battery_lines = [line.strip().split(";") for line in lines if "BATTERY STATUS" in line]
        battery_data = []
        for entry in battery_lines:
            if len(entry) >= 3:  # Ensure we have enough columns
                try:
                    date = entry[0].strip()
                    time = entry[1].strip()
                    battery_info = entry[2].strip()
                    # Extract battery value from format "BATTERY STATUS: (PB): 12,4"
                    battery_value = battery_info.split(":")[-1].strip()
                    # Convert comma to period for float conversion
                    battery_value = battery_value.replace(",", ".")
                    battery_data.append([date, time, battery_value])
                except (ValueError, IndexError):
                    continue

        battery_df = pd.DataFrame(battery_data, columns=["DATE", "TIME", "BATTERY"])
        battery_df["DATE"] = pd.to_datetime(battery_df["DATE"])

        # Convert battery values to float
        battery_df["BATTERY"] = pd.to_numeric(battery_df["BATTERY"])

        # Parse temperature data
        temp_lines = [line.strip().split(";") for line in lines if "TEMPERATURE STATUS" in line]
        temp_data = []
        for entry in temp_lines:
            if len(entry) >= 3:
                try:
                    date = entry[0].strip()
                    time = entry[1].strip()
                    temp_info = entry[2].strip()
                    # Extract temperature value from format "TEMPERATURE STATUS: +25"
                    temp_value = temp_info.split(":")[-1].strip().replace("+", "")
                    temp_data.append([date, time, temp_value])
                except (ValueError, IndexError):
                    continue

        temp_df = pd.DataFrame(temp_data, columns=["DATE", "TIME", "TEMPERATURE"])
        temp_df["DATE"] = pd.to_datetime(temp_df["DATE"])
        temp_df["TEMPERATURE"] = pd.to_numeric(temp_df["TEMPERATURE"])

        # Parse events
        events_start_line = None
        for i, line in enumerate(lines):
            if line.startswith("NUMBER OF EVENTS:"):
                events_start_line = i + 2
                break

        if events_start_line is not None:
            event_data = [line.strip().split(";") for line in lines[events_start_line:]]
            max_columns = max(len(event) for event in event_data)
            event_data = [event + [None] * (max_columns - len(event)) for event in event_data]
            header = event_data[0]
            events_df = pd.DataFrame(event_data[1:], columns=header)
            event_counts = events_df["EVENT ID"].value_counts()
        else:
            event_counts = None

        return df, battery_df, temp_df, event_counts
    return None, None, None, None


def plot_msafe3bc_data(df, battery_df, temp_df, event_counts):
    """Create plots for mSafe 3 BC data."""
    # Pressure plot
    fig_pressure = go.Figure()
    fig_pressure.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["Pline"], name="Pline"))
    fig_pressure.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["P2"], name="P2"))
    fig_pressure.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["P3"], name="P3"))
    fig_pressure.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["Ppilot"], name="Ppilot"))
    fig_pressure.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["Ppower"], name="Ppower"))

    fig_pressure.update_layout(
        title="Estado de las Presiones a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Presiones",
        showlegend=True,
        legend_title="Variables",
        width=1300,
    )

    # Battery plot
    fig_battery = go.Figure()
    fig_battery.add_trace(
        go.Scatter(x=battery_df["DATE"] + pd.to_timedelta(battery_df["TIME"]), y=battery_df["CB"], name="CB")
    )
    fig_battery.add_trace(
        go.Scatter(x=battery_df["DATE"] + pd.to_timedelta(battery_df["TIME"]), y=battery_df["PB1"], name="PB1")
    )
    fig_battery.add_trace(
        go.Scatter(x=battery_df["DATE"] + pd.to_timedelta(battery_df["TIME"]), y=battery_df["PB2"], name="PB2")
    )

    fig_battery.update_layout(
        title="Estado de la Batería a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Voltaje de Batería",
        showlegend=True,
        legend_title="Variables",
        width=1300,
    )

    # Temperature plot
    fig_temp = go.Figure()
    fig_temp.add_trace(
        go.Scatter(x=temp_df["DATE"] + pd.to_timedelta(temp_df["TIME"]), y=temp_df["TEMPERATURE"], name="Temperatura")
    )

    fig_temp.update_layout(
        title="Estado de la Temperatura a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Temperatura (°C)",
        showlegend=True,
        width=1300,
    )

    return fig_pressure, fig_battery, fig_temp, event_counts


def plot_msafe_data(df, battery_df, temp_df, event_counts):
    """Create plots for mSafe data."""
    # Pressure plot (WP, LP, P4, AP)
    fig_pressure = go.Figure()
    fig_pressure.add_trace(
        go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["WP"], name="WP (Presión de Pozo)")
    )
    fig_pressure.add_trace(
        go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["LP"], name="LP (Presión de Línea)")
    )
    fig_pressure.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["P4"], name="P4 (Presión 4)"))
    fig_pressure.add_trace(
        go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["AP"], name="AP (Presión Absoluta)")
    )

    fig_pressure.update_layout(
        title="Estado de las Presiones a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Presión (PSI)",
        showlegend=True,
        legend_title="Variables",
        width=1300,
        annotations=[
            dict(
                text="WP: Presión de Pozo del sistema\nLP: Presión en la línea principal\nP4: Presión en el punto 4\nAP: Presión absoluta del sistema",
                xref="paper",
                yref="paper",
                x=0,
                y=1.1,
                showarrow=False,
            )
        ],
    )

    # Temperature plot
    fig_temp = go.Figure()
    fig_temp.add_trace(
        go.Scatter(x=temp_df["DATE"] + pd.to_timedelta(temp_df["TIME"]), y=temp_df["TEMPERATURE"], name="Temperatura")
    )

    fig_temp.update_layout(
        title="Estado de la Temperatura a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Temperatura (°C)",
        showlegend=True,
        width=1300,
        annotations=[
            dict(text="Temperatura del dispositivo", xref="paper", yref="paper", x=0, y=1.1, showarrow=False)
        ],
    )

    # Battery plot
    fig_battery = go.Figure()
    fig_battery.add_trace(
        go.Scatter(
            x=battery_df["DATE"] + pd.to_timedelta(battery_df["TIME"]),
            y=battery_df["BATTERY"],
            name="Batería Principal",
        )
    )

    fig_battery.update_layout(
        title="Estado de la Batería Principal a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Voltaje de Batería (V)",
        showlegend=True,
        width=1300,
        annotations=[
            dict(
                text="Batería Principal: Voltaje de la batería del dispositivo",
                xref="paper",
                yref="paper",
                x=0,
                y=1.1,
                showarrow=False,
            )
        ],
    )

    # Flow plot
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["FLOW"], name="FLOW"))

    fig_flow.update_layout(
        title="Estado del Flujo a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Flujo (MSCF)",
        showlegend=True,
        width=1300,
        annotations=[
            dict(
                text="FLOW: Flujo de gas en MSCF (Miles de pies cúbicos estándar)",
                xref="paper",
                yref="paper",
                x=0,
                y=1.1,
                showarrow=False,
            )
        ],
    )

    return fig_pressure, fig_temp, fig_battery, fig_flow, event_counts


# Ruta del archivo de texto
archivo = st.file_uploader("Cargar archivo de texto (.txt)", type=["txt"])

# Verificar si se ha cargado un archivo
if archivo is not None:
    # Leer el contenido del archivo
    lines = archivo.read().decode("utf-8").splitlines()

    if device_type == "mSafe 3 BC":
        df, battery_df, temp_df, event_counts = parse_msafe3bc_data(lines)
        if df is not None:
            fig_pressure, fig_battery, fig_temp, event_counts = plot_msafe3bc_data(
                df, battery_df, temp_df, event_counts
            )
            st.plotly_chart(fig_pressure)
            st.plotly_chart(fig_battery)
            st.plotly_chart(fig_temp)
            if event_counts is not None:
                st.write("Eventos más recurrentes (excluyendo BATTERY STATUS y TEMPERATURE STATUS)")
                st.write(event_counts)
        else:
            st.write("No se encontraron datos válidos en el archivo.")

    elif device_type == "mSafe":
        df, battery_df, temp_df, event_counts = parse_msafe_data(lines)
        if df is not None:
            fig_pressure, fig_temp, fig_battery, fig_flow, event_counts = plot_msafe_data(
                df, battery_df, temp_df, event_counts
            )
            st.plotly_chart(fig_pressure)
            st.plotly_chart(fig_temp)
            st.plotly_chart(fig_battery)
            st.plotly_chart(fig_flow)
            if event_counts is not None:
                st.write("Eventos más recurrentes")
                st.write(event_counts)
        else:
            st.write("No se encontraron datos válidos en el archivo.")
    elif device_type == "mSafe 3 AC":
        st.write("Soporte para mSafe 3 AC está en desarrollo.")
else:
    st.write(" ")
