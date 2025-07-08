#streamlit run your_script.py

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title('Visualización de Logs')

# Ruta del archivo de texto
archivo = st.file_uploader("Cargar archivo de texto (.txt)", type=["txt"])

# Verificar si se ha cargado un archivo
if archivo is not None:
    # Leer el contenido del archivo
    lines = archivo.read().decode('utf-8').splitlines()

    # Encontrar la línea que contiene los encabezados de los datos
    for i, line in enumerate(lines):
        if line.startswith("   DATE   ;  TIME  ;Pline; P2 ; P3 ;Ppilot;Ppower"):
            data_start_line = i + 1  # Línea siguiente a los encabezados
            break

    # Encontrar la línea que contiene "NUMBER OF EVENTS: 2724"
    events_line = None
    for i, line in enumerate(lines):
        if "NUMBER OF EVENTS:" in line:
            events_line = i
            break

    # Obtener los datos de interés
    data_lines = lines[data_start_line:events_line]
    data = [line.strip().split(";") for line in data_lines]
    df = pd.DataFrame(data, columns=["DATE", "TIME", "Pline", "P2", "P3", "Ppilot", "Ppower"])

    # Convertir las columnas relevantes a tipos numéricos
    df["Pline"] = pd.to_numeric(df["Pline"])
    df["P2"] = pd.to_numeric(df["P2"])
    df["P3"] = pd.to_numeric(df["P3"])
    df["Ppilot"] = pd.to_numeric(df["Ppilot"])
    df["Ppower"] = pd.to_numeric(df["Ppower"])

    # Convertir la columna "DATE" a formato de fecha
    df["DATE"] = pd.to_datetime(df["DATE"])

    # Crear la visualización con Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["Pline"], name="Pline"))
    fig.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["P2"], name="P2"))
    fig.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["P3"], name="P3"))
    fig.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["Ppilot"], name="Ppilot"))
    fig.add_trace(go.Scatter(x=df["DATE"] + pd.to_timedelta(df["TIME"]), y=df["Ppower"], name="Ppower"))

    fig.update_layout(
        title="Estado de las Presiones a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Presiones",
        showlegend=True,
        legend_title="Variables",
        width=1300  # Ajustar el ancho de la figura
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)


    # Encontrar las líneas que contienen los datos de battery status
    battery_lines = [line.strip().split(";") for line in lines if "BATTERY STATUS" in line]

    # Extraer fechas y tiempos
    dates = [datetime.strptime(entry[0] + ' ' + entry[1], '%m/%d/%Y %H:%M:%S') for entry in battery_lines]

    # Extraer valores de CB, PB1 y PB2
    cb_values = [float(entry[2].split(': ')[1]) for entry in battery_lines]
    pb1_values = [float(entry[3].split(': ')[1]) for entry in battery_lines]
    pb2_values = [float(entry[4].split(': ')[1]) for entry in battery_lines]

    # Crear el gráfico con Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=cb_values, name='CB'))
    fig.add_trace(go.Scatter(x=dates, y=pb1_values, name='PB1'))
    fig.add_trace(go.Scatter(x=dates, y=pb2_values, name='PB2'))

    fig.update_layout(
        title="Estado de la Batería a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Estado de la Batería",
        showlegend=True,
        legend_title="Variables",
        width=1300  # Ajustar el ancho de la figura
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)

    # Encontrar las líneas que contienen los datos de temperatura
    temperature_lines = [line.strip().split(";") for line in lines if "TEMPERATURE STATUS" in line]

    # Extraer fechas y tiempos
    dates_temperatures = [datetime.strptime(entry[0] + ' ' + entry[1], '%m/%d/%Y %H:%M:%S') for entry in temperature_lines]

    # Extraer valores de temperatura
    temperature_values = [float(entry[2].split(':')[1]) for entry in temperature_lines]

    # Crear el gráfico con Plotly
    fig_temperatures = go.Figure()
    fig_temperatures.add_trace(go.Scatter(x=dates_temperatures, y=temperature_values, name='Temperatura'))

    fig_temperatures.update_layout(
        title="Estado de las Temperaturas a lo largo del tiempo",
        xaxis_title="Fecha y Hora",
        yaxis_title="Temperaturas",
        showlegend=True,
        legend_title="Variables",
        width=1300  # Ajustar el ancho de la figura
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig_temperatures)

    # Encontrar la línea que contiene los eventos
    for i, line in enumerate(lines):
        if line.startswith("NUMBER OF EVENTS:"):
            events_start_line = i + 2  # Línea siguiente a "NUMBER OF EVENTS:"
            break

    # Obtener los eventos a partir de la línea encontrada
    event_data = [line.strip().split(";") for line in lines[events_start_line:]]

    # Obtener el número máximo de columnas en los eventos
    max_columns = max(len(event) for event in event_data)

    # Rellenar los eventos con menos columnas con valores nulos
    event_data = [event + [None] * (max_columns - len(event)) for event in event_data]

    # Obtener el encabezado del DataFrame a partir de la primera fila
    header = event_data[0]

    # Crear un DataFrame de pandas con los datos de eventos, utilizando el encabezado como columnas
    df = pd.DataFrame(event_data[1:], columns=header)

    # Excluir los eventos que contienen "BATTERY STATUS (CB)" en la columna 'EVENT ID'
    filtered_df = df[~df['EVENT ID'].str.contains("BATTERY STATUS \(CB\)|TEMPERATURE STATUS", regex=True)]

    # Obtener el top 10 de eventos más recurrentes
    todos_los_eventos = filtered_df['EVENT ID'].value_counts()

    # Mostrar el top 10 de eventos en Streamlit
    st.write("Eventos más recurrentes (excluyendo BATTERY STATUS y TEMPERATURE STATUS)")
    st.write(todos_los_eventos)

else:
    st.write(" ")
