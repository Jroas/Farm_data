import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import json
from datetime import datetime
import pandas as pd


# Configuración de la página
st.set_page_config(
    page_title="Clima y Cultivos - California",
    page_icon="🌾",
    layout="wide"
)

# Título y descripción
st.title("🌾 Sistema de Información Meteorológica y Recomendación de Cultivos")
st.markdown("### California - Análisis por Condado")

# API Keys

# OpenAI API Key (obtén tu key en https://platform.openai.com/api-keys)
OPENAI_API_KEY = "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"

# Coordenadas centrales de algunos condados principales de California
CONDADOS_CALIFORNIA = {
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "San Francisco": {"lat": 37.7749, "lon": -122.4194},
    "San Diego": {"lat": 32.7157, "lon": -117.1611},
    "Sacramento": {"lat": 38.5816, "lon": -121.4944},
    "Fresno": {"lat": 36.7378, "lon": -119.7871},
    "Riverside": {"lat": 33.9533, "lon": -117.3962},
    "San Jose": {"lat": 37.3382, "lon": -121.8863},
    "Oakland": {"lat": 37.8044, "lon": -122.2712},
    "Bakersfield": {"lat": 35.3733, "lon": -119.0187},
    "Anaheim": {"lat": 33.8366, "lon": -117.9143},
    "Santa Barbara": {"lat": 34.4208, "lon": -119.6982},
    "Stockton": {"lat": 37.9577, "lon": -121.2908},
    "Modesto": {"lat": 37.6391, "lon": -120.9969},
    "Salinas": {"lat": 36.6777, "lon": -121.6555}
}

# Base de datos de cultivos y sus requisitos climáticos
CULTIVOS_DB = {
    "Almendras": {
        "temp_min": 15, "temp_max": 30,
        "precipitacion_min": 400, "precipitacion_max": 1000,
        "descripcion": "Clima mediterráneo, inviernos fríos y veranos calurosos y secos",
        "temporada": "Floración en febrero-marzo, cosecha en agosto-octubre",
        "emoji": "🌰"
    },
    "Uvas de Vino": {
        "temp_min": 15, "temp_max": 28,
        "precipitacion_min": 500, "precipitacion_max": 900,
        "descripcion": "Clima templado, con noches frescas y días cálidos",
        "temporada": "Cosecha en agosto-octubre",
        "emoji": "🍇"
    },
    "Fresas": {
        "temp_min": 10, "temp_max": 26,
        "precipitacion_min": 600, "precipitacion_max": 1200,
        "descripcion": "Clima fresco a templado, necesita humedad constante",
        "temporada": "Producción todo el año en zonas costeras",
        "emoji": "🍓"
    },
    "Tomates": {
        "temp_min": 18, "temp_max": 30,
        "precipitacion_min": 400, "precipitacion_max": 800,
        "descripcion": "Clima cálido, requiere mucho sol",
        "temporada": "Siembra en primavera, cosecha en verano-otoño",
        "emoji": "🍅"
    },
    "Lechuga": {
        "temp_min": 7, "temp_max": 24,
        "precipitacion_min": 400, "precipitacion_max": 800,
        "descripcion": "Clima fresco, no tolera altas temperaturas",
        "temporada": "Cultivo de temporada fresca",
        "emoji": "🥬"
    },
    "Aguacates": {
        "temp_min": 15, "temp_max": 29,
        "precipitacion_min": 800, "precipitacion_max": 1500,
        "descripcion": "Clima subtropical, sensible a heladas",
        "temporada": "Producción durante todo el año",
        "emoji": "🥑"
    },
    "Naranjas": {
        "temp_min": 13, "temp_max": 35,
        "precipitacion_min": 600, "precipitacion_max": 1200,
        "descripcion": "Clima subtropical a tropical, necesita inviernos suaves",
        "temporada": "Cosecha en invierno-primavera",
        "emoji": "🍊"
    },
    "Brócoli": {
        "temp_min": 7, "temp_max": 23,
        "precipitacion_min": 500, "precipitacion_max": 900,
        "descripcion": "Clima fresco, crece mejor en temperaturas moderadas",
        "temporada": "Cultivo de otoño-invierno",
        "emoji": "🥦"
    }
}

# Inicializar estado de la sesión para cultivos plantados
if 'cultivos_plantados' not in st.session_state:
    st.session_state.cultivos_plantados = []

if 'recomendaciones_cultivos' not in st.session_state:
    st.session_state.recomendaciones_cultivos = {}


def obtener_clima(lat, lon, condado):
    """Obtiene datos climáticos actuales usando la API de NASA POWER"""
    try:
        # Obtener fecha actual en formato YYYYMMDD
        fecha_hoy = "20250930"
        # Construir URL completa según documentación oficial
        url = (
            f"https://power.larc.nasa.gov/api/temporal/daily/point?"
            f"parameters=GWETTOP,T2M,RH2M,PS,WS2M&"
            f"community=AG&"
            f"longitude={lon}&"
            f"latitude={lat}&"
            f"start={fecha_hoy}&"
            f"end={fecha_hoy}&"
            f"format=JSON"
        )

        print(f"Consultando: {url}")
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Verificar que la respuesta tenga la estructura esperada
            if "properties" not in data or "parameter" not in data["properties"]:
                print(f"Respuesta inesperada de la API: {data}")
                return generar_datos_simulados(lat, lon, condado)

            parametros = data["properties"]["parameter"]

            # Los datos diarios usan la fecha como clave
            # Formato: {'YYYYMMDD': valor}
            fecha_key = fecha_hoy

            return {
                "main": {
                    "temp": parametros["T2M"].get(fecha_key, 22.0),
                    "humidity": parametros["RH2M"].get(fecha_key, 60.0),
                    "pressure": parametros["PS"].get(fecha_key, 101.3),  # Ya viene en kPa
                    "soil_moisture": parametros["GWETTOP"].get(fecha_key, 0.4)
                },
                "weather": [{"description": "Datos NASA POWER", "icon": "01d"}],
                "wind": {"speed": parametros["WS2M"].get(fecha_key, 3.5)},
                "name": condado,
                "coord": {"lat": lat, "lon": lon},
                "dt": int(datetime.now().timestamp())
            }
        else:
            print(f"Error en la solicitud ({response.status_code}): {response.text}")
            return generar_datos_simulados(lat, lon, condado)

    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return generar_datos_simulados(lat, lon, condado)

def generar_datos_simulados(lat, lon, condado):
    """Devuelve datos simulados en caso de fallo"""
    return {
        "main": {
            "temp": 22 + (lat - 35) * 0.5,
            "humidity": 60,
            "pressure": 1013,
            "soil_moisture": 0.4
        },
        "weather": [{"description": "datos simulados", "icon": "02d"}],
        "wind": {"speed": 3.5},
        "name": condado
    }

def obtener_recomendaciones_ia(cultivo, condado, clima_data, precipitacion_anual):
    """Obtiene recomendaciones personalizadas usando ChatGPT"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        prompt = f"""
Eres un experto agrónomo especializado en agricultura de California. Necesito recomendaciones específicas y concisas para cultivar {cultivo} en el condado de {condado}, California, quiero que tengas un tono amigable y no extiendas mucho en estas recomendaciones.

CONTEXTO DEL LUGAR:
- Condado: {condado}, California
- Temperatura actual: {clima_data['main']['temp']:.1f}°C
- Humedad: {clima_data['main']['humidity']}%
- Velocidad del viento: {clima_data['wind']['speed']} m/s
- Presión atmosférica: {clima_data['main']['pressure']} hPa
- Condición actual: {clima_data['weather'][0]['description']}
- Precipitación anual estimada: {precipitacion_anual} mm

CULTIVO A PLANTAR: {cultivo}

Por favor proporciona recomendaciones ESPECÍpiFICAS y PRÁCTICAS en formato claro y estructurado sobre:

1. **Calendario de Siembra**: Mejor época del año para plantar en esta zona específica

2. **Fertilización**: Tipo de fertilizante y frecuencia
3. **Cosecha**: Tiempo estimado hasta la primera cosecha


Sé específico con números y unidades. Adapta las recomendaciones al clima actual de {condado}.
"""
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Eres un experto agrónomo con amplia experiencia en agricultura californiana. Proporcionas recomendaciones prácticas, específicas y basadas en datos."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error al obtener recomendaciones: {response.status_code}. Verifica tu API key de OpenAI."
            
    except Exception as e:
        return f"No se pudieron obtener recomendaciones de IA: {str(e)}\n\nVerifica que tu API key de OpenAI esté configurada correctamente."

def recomendar_cultivos(temp, precipitacion_anual=600):
    """Recomienda cultivos basándose en temperatura y precipitación"""
    recomendaciones = []
    
    for cultivo, requisitos in CULTIVOS_DB.items():
        if (requisitos["temp_min"] <= temp <= requisitos["temp_max"] and
            requisitos["precipitacion_min"] <= precipitacion_anual <= requisitos["precipitacion_max"]):
            recomendaciones.append({
                "cultivo": cultivo,
                "idoneidad": "Alta",
                **requisitos
            })
        elif (requisitos["temp_min"] - 3 <= temp <= requisitos["temp_max"] + 3):
            recomendaciones.append({
                "cultivo": cultivo,
                "idoneidad": "Media",
                **requisitos
            })
    
    # Ordenar por idoneidad
    recomendaciones.sort(key=lambda x: 0 if x["idoneidad"] == "Alta" else 1)
    return recomendaciones

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.markdown("---")
  
    st.subheader("📊 Parámetros de Cultivo")
    precipitacion_anual = st.slider(
        "Precipitación anual estimada (mm)",
        min_value=200,
        max_value=1500,
        value=600,
        step=50,
        help="Ajusta según la zona seleccionada"
    )
    
    st.markdown("---")
    st.subheader("🗺️ Información")
    st.markdown("""
    **Cómo usar:**
    1. Selecciona un condado del mapa o del menú
    2. Visualiza las condiciones meteorológicas actuales
    3. Recibe recomendaciones de cultivos apropiados
    """)

# Selector de condado
col1, col2 = st.columns([2, 1])

with col1:
    condado_seleccionado = st.selectbox(
        "🏛️ Selecciona un condado:",
        options=list(CONDADOS_CALIFORNIA.keys()),
        index=0
    )

# Obtener coordenadas del condado seleccionado
coords = CONDADOS_CALIFORNIA[condado_seleccionado]
lat, lon = coords["lat"], coords["lon"]

# Obtener datos climáticos
clima_data = obtener_clima(lat, lon, condado_seleccionado)

# Mostrar información meteorológica
st.markdown("---")
st.header(f"🌤️ Condiciones Meteorológicas - {condado_seleccionado}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🌡️ Temperatura",
        f"{clima_data['main']['temp']:.1f}°C"
    )

with col2:
    st.metric(
        "💧 Humedad",
        f"{clima_data['main']['humidity']}%"
    )

with col3:
    st.metric(
        "💨 Viento",
        f"{clima_data['wind']['speed']:.1f} m/s"
    )

with col4:
    st.metric(
        "🌡️ Presión",
        f"{clima_data['main']['pressure']} hPa"
    )

# Crear dos columnas para mapa y recomendaciones
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🗺️ Mapa Interactivo")
    
    # Crear mapa centrado en California
    m = folium.Map(
        location=[36.7783, -119.4179],
        zoom_start=6,
        tiles="OpenStreetMap"
    )
    
    # Añadir marcadores para cada condado
    for condado, coord in CONDADOS_CALIFORNIA.items():
        clima = obtener_clima(coord["lat"], coord["lon"], condado)
        
        # Color del marcador según temperatura
        temp = clima['main']['temp']
        if temp < 15:
            color = 'blue'
        elif temp < 25:
            color = 'green'
        else:
            color = 'red'
        
        popup_text = f"""
        <b>{condado}</b><br>
        🌡️ Temp: {temp:.1f}°C<br>
        💧 Humedad: {clima['main']['humidity']}%<br>
        {clima['weather'][0]['description'].capitalize()}
        """
        
        folium.Marker(
            location=[coord["lat"], coord["lon"]],
            popup=folium.Popup(popup_text, max_width=200),
            tooltip=condado,
            icon=folium.Icon(color=color, icon='cloud')
        ).add_to(m)
    
    # Destacar condado seleccionado con círculo amarillo
    folium.CircleMarker(
        location=[lat, lon],
        radius=15,
        popup=f"<b>{condado_seleccionado}</b><br>Seleccionado",
        color='yellow',
        fill=True,
        fillColor='yellow',
        fillOpacity=0.3
    ).add_to(m)
    
    # Añadir marcadores de cultivos plantados
    for cultivo_info in st.session_state.cultivos_plantados:
        if cultivo_info['condado'] == condado_seleccionado:
            # Crear icono HTML personalizado con emoji
            icon_html = f"""
            <div style="font-size: 30px; text-align: center;">
                {cultivo_info['emoji']}
            </div>
            """
            
            folium.Marker(
                location=[cultivo_info['lat'], cultivo_info['lon']],
                popup=folium.Popup(
                    f"<b>{cultivo_info['emoji']} {cultivo_info['nombre']}</b><br>"
                    f"Condado: {cultivo_info['condado']}<br>"
                    f"Plantado",
                    max_width=200
                ),
                tooltip=f"{cultivo_info['emoji']} {cultivo_info['nombre']}",
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)
    
    folium_static(m, width=500, height=400)

with col2:
    st.subheader("🌾 Recomendaciones de Cultivos")
    
    # Obtener recomendaciones
    recomendaciones = recomendar_cultivos(
        clima_data['main']['temp'],
        precipitacion_anual
    )
    
    if recomendaciones:
        for rec in recomendaciones[:5]:  # Mostrar top 5
            with st.expander(f"{'🌟' if rec['idoneidad'] == 'Alta' else '⭐'} {rec['emoji']} {rec['cultivo']} - Idoneidad: {rec['idoneidad']}"):
                st.markdown(f"**Descripción:** {rec['descripcion']}")
                st.markdown(f"**Temporada:** {rec['temporada']}")
                st.markdown(f"**Rango de temperatura óptimo:** {rec['temp_min']}°C - {rec['temp_max']}°C")
                st.markdown(f"**Precipitación anual:** {rec['precipitacion_min']}-{rec['precipitacion_max']} mm")
                
                # Calcular compatibilidad
                temp_actual = clima_data['main']['temp']
                temp_centro = (rec['temp_min'] + rec['temp_max']) / 2
                diferencia = abs(temp_actual - temp_centro)
                compatibilidad = max(0, 100 - (diferencia * 5))
                
                st.progress(compatibilidad / 100)
                st.caption(f"Compatibilidad: {compatibilidad:.0f}%")
                
                # Botón para obtener recomendaciones de IA
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"🤖 Recomendaciones IA", key=f"ia_{rec['cultivo']}_{condado_seleccionado}"):
                        with st.spinner(f"Consultando al experto agrónomo para {rec['cultivo']}..."):
                            recomendacion_ia = obtener_recomendaciones_ia(
                                rec['cultivo'],
                                condado_seleccionado,
                                clima_data,
                                precipitacion_anual
                            )
                            st.session_state[f"rec_ia_{rec['cultivo']}"] = recomendacion_ia
                
                with col_btn2:
                    if st.button(f"🌱 Plantar {rec['emoji']}", key=f"plantar_{rec['cultivo']}_{condado_seleccionado}"):
                        # Agregar cultivo a la lista de plantados
                        cultivo_plantado = {
                            'nombre': rec['cultivo'],
                            'emoji': rec['emoji'],
                            'condado': condado_seleccionado,
                            'lat': lat,
                            'lon': lon,
                            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.cultivos_plantados.append(cultivo_plantado)
                        st.success(f"¡{rec['emoji']} {rec['cultivo']} plantado en {condado_seleccionado}!")
                        st.rerun()
                
                # Mostrar recomendaciones de IA si existen
                if f"rec_ia_{rec['cultivo']}" in st.session_state:
                    st.markdown("---")
                    st.markdown("### 🤖 Recomendaciones del Experto Agrónomo")
                    st.markdown(st.session_state[f"rec_ia_{rec['cultivo']}"])
    else:
        st.warning("No se encontraron cultivos adecuados para estas condiciones.")
    
    # Mostrar cultivos plantados en este condado
    cultivos_en_condado = [c for c in st.session_state.cultivos_plantados if c['condado'] == condado_seleccionado]
    if cultivos_en_condado:
        st.markdown("---")
        st.subheader(f"🌱 Cultivos Plantados en {condado_seleccionado}")
        for cultivo in cultivos_en_condado:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"{cultivo['emoji']} **{cultivo['nombre']}** - Plantado: {cultivo['fecha']}")
            with col_b:
                if st.button("🗑️", key=f"eliminar_{cultivo['nombre']}_{cultivo['fecha']}", help="Eliminar cultivo"):
                    st.session_state.cultivos_plantados.remove(cultivo)
                    st.rerun()

# Información adicional
st.markdown("---")
st.header("📈 Análisis Detallado")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌡️ Análisis de Temperatura")
    temp_actual = clima_data['main']['temp']
    
    if temp_actual < 10:
        st.info("**Temperatura Baja**: Ideal para cultivos de clima frío como lechugas, brócoli y vegetales de hoja.")
    elif temp_actual < 20:
        st.success("**Temperatura Moderada**: Excelente para una amplia variedad de cultivos.")
    elif temp_actual < 30:
        st.warning("**Temperatura Cálida**: Ideal para cultivos de verano como tomates, melones y cultivos tropicales.")
    else:
        st.error("**Temperatura Alta**: Solo cultivos muy resistentes al calor. Requiere irrigación intensiva.")

with col2:
    st.subheader("💧 Gestión del Agua")
    st.markdown(f"""
    - **Precipitación anual estimada**: {precipitacion_anual} mm
    - **Humedad actual**: {clima_data['main']['humidity']}%
    - **Recomendación**: {'Sistema de irrigación necesario' if precipitacion_anual < 500 else 'Precipitación adecuada, irrigación complementaria'}
    """)

# Footer
st.markdown("---")
st.caption("💡 Desarrollado con Streamlit | Datos meteorológicos: OpenWeatherMap | 🌾 Sistema de Recomendación Agrícola")
st.caption("⚠️ Esta es una versión de demostración. Para producción, obtén tu API key en https://openweathermap.org/api")