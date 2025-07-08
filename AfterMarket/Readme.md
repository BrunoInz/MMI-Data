# Visualizador de Logs - mSafe Devices

Una aplicación web desarrollada con Streamlit para visualizar y analizar logs de dispositivos mSafe, incluyendo datos de presiones, temperatura, batería y eventos.

## Características

- **Soporte para múltiples dispositivos**: mSafe, mSafe 3 BC, y mSafe 3 AC (en desarrollo)
- **Visualizaciones interactivas**: Gráficos de presiones, temperatura, batería y flujo
- **Análisis de eventos**: Conteo y análisis de eventos más recurrentes
- **Interfaz intuitiva**: Selección de tipo de dispositivo y carga de archivos simple

## Tipos de Dispositivos Soportados

### mSafe 3 BC
- **Presiones**: Pline, P2, P3, Ppilot, Ppower
- **Batería**: CB, PB1, PB2
- **Temperatura**: Monitoreo de temperatura del dispositivo
- **Eventos**: Análisis de eventos excluyendo BATTERY STATUS y TEMPERATURE STATUS

### mSafe
- **Presiones**: WP (Presión de Pozo), LP (Presión de Línea), P4 (Presión 4), AP (Presión Absoluta)
- **Temperatura**: Monitoreo de temperatura del dispositivo
- **Batería**: Batería Principal
- **Flujo**: FLOW (Miles de pies cúbicos estándar - MSCF)
- **Eventos**: Análisis completo de eventos

### mSafe 3 AC
- Estado: En desarrollo

## Requisitos

```python
streamlit
pandas
plotly
datetime
re
```

## Instalación

1. Clona o descarga el repositorio
2. Instala las dependencias:
   ```bash
   pip install streamlit pandas plotly
   ```

## Uso

1. Ejecuta la aplicación:
   ```bash
   streamlit run applog.py
   ```

2. Selecciona el tipo de dispositivo desde el dropdown
3. Carga tu archivo de log (.txt) usando el botón de carga
4. Visualiza los gráficos y análisis generados automáticamente

## Formato de Archivos

### mSafe 3 BC
```
DATE;TIME;Pline;P2;P3;Ppilot;Ppower
mm/dd/yyyy;hh:mm:ss;valor;valor;valor;valor;valor
...
BATTERY STATUS (CB): valor; BATTERY STATUS (PB1): valor; BATTERY STATUS (PB2): valor
TEMPERATURE STATUS: valor
NUMBER OF EVENTS: n
```

### mSafe
```
DATE;TIME;WP;LP;T3;P4;AP;FLOW;UNIT
mm/dd/yyyy;hh:mm:ss;valor;valor;valor;valor;valor;valor;MSCF
...
BATTERY STATUS: (PB): valor
TEMPERATURE STATUS: +valor
NUMBER OF EVENTS: n
```

## Funcionalidades Principales

### Análisis de Datos
- **Detección automática**: El sistema puede detectar automáticamente el tipo de dispositivo basado en el contenido del archivo
- **Parsing inteligente**: Procesamiento robusto de diferentes formatos de fecha y separadores
- **Limpieza de datos**: Conversión automática de tipos de datos y manejo de valores faltantes

### Visualizaciones
- **Gráficos temporales**: Visualización de todas las variables a lo largo del tiempo
- **Gráficos interactivos**: Zoom, pan y selección de variables usando Plotly
- **Anotaciones informativas**: Explicaciones de cada variable directamente en los gráficos

### Análisis de Eventos
- **Conteo automático**: Identificación y conteo de eventos más frecuentes
- **Filtrado inteligente**: Exclusión de eventos de rutina como BATTERY STATUS y TEMPERATURE STATUS (mSafe 3 BC)
- **Presentación clara**: Tabla ordenada por frecuencia de eventos

## Estructura del Código

```
applog.py
├── detect_device_type()     # Detección automática del tipo de dispositivo
├── parse_msafe3bc_data()    # Parser para dispositivos mSafe 3 BC
├── parse_msafe_data()       # Parser para dispositivos mSafe
├── plot_msafe3bc_data()     # Generación de gráficos para mSafe 3 BC
└── plot_msafe_data()        # Generación de gráficos para mSafe
```

## Configuración

La aplicación utiliza configuración de página ancha por defecto:
```python
st.set_page_config(layout="wide")
```

Los gráficos tienen un ancho estándar de 1300px para optimizar la visualización.

---

**Nota**: Esta aplicación está optimizada para archivos de log generados por dispositivos mSafe. Para otros formatos de archivo, pueden ser necesarias modificaciones en los parsers.
