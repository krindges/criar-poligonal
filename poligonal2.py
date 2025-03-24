import streamlit as st
from streamlit_folium import st_folium
import folium
import osmnx as ox
import geopandas as gpd

# Configuração da página
st.set_page_config(layout="wide")
st.title("🌍 Detecção Automática de Poligonais - Rios e Ilhas")

# Estado inicial
if "poligonal_principal" not in st.session_state:
    st.session_state.poligonal_principal = None

if "poligonais_secundarias" not in st.session_state:
    st.session_state.poligonais_secundarias = []

if "ultimo_centro" not in st.session_state:
    st.session_state.ultimo_centro = [-15.6, -56.06]  # Centro padrão

# Criar mapa
mapa = folium.Map(location=st.session_state.ultimo_centro, zoom_start=15, tiles="CartoDB positron")

# Adicionar poligonal principal
if st.session_state.poligonal_principal:
    folium.Polygon(
        locations=st.session_state.poligonal_principal,
        color="green",
        weight=3,
        fill=True,
        fill_opacity=0.5
    ).add_to(mapa)

# Adicionar poligonais secundárias
for pol in st.session_state.poligonais_secundarias:
    folium.Polygon(
        locations=pol,
        color="magenta",
        weight=2,
        fill=True,
        fill_opacity=0.4
    ).add_to(mapa)

# Mostrar mapa
st.subheader("🔍 Navegue e clique abaixo para detectar contornos hídricos")
map_data = st_folium(mapa, height=600, width=1000, returned_objects=["bounds", "center"])

# Atualizar centro atual do mapa
if map_data and "center" in map_data:
    st.session_state.ultimo_centro = [map_data["center"]["lat"], map_data["center"]["lng"]]

# Função para detectar feições aquáticas
@st.cache_data(show_spinner="Buscando feições aquáticas...")
def detectar_agua_por_bounding_box(bounds):
    try:
        north = bounds['north'] if 'north' in bounds else bounds['n']
        south = bounds['south'] if 'south' in bounds else bounds['s']
        east = bounds['east'] if 'east' in bounds else bounds['e']
        west = bounds['west'] if 'west' in bounds else bounds['w']

        tags = {"natural": "water"}
        gdf = ox.features_from_bbox(north, south, east, west, tags=tags)
        return gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].to_crs("EPSG:4326")
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

# Botão para detectar
if map_data and "bounds" in map_data:
    st.write("Limites do mapa:", map_data["bounds"])  # ✔ Ajuda a depurar

    if st.button("🔎 Detectar Poligonais da Área Enquadrada"):
        resultado = detectar_agua_por_bounding_box(map_data["bounds"])

        if resultado is not None and not resultado.empty:
            st.success(f"💧 {len(resultado)} poligonais d'água detectadas!")
            st.session_state.poligonal_principal = list(resultado.geometry.iloc[0].exterior.coords)
            st.session_state.poligonais_secundarias = []

            for i in range(1, len(resultado)):
                geom = resultado.geometry.iloc[i]
                if geom.geom_type == "Polygon":
                    coords = list(geom.exterior.coords)
                    st.session_state.poligonais_secundarias.append(coords)
            st.rerun()
        else:
            st.warning("Nenhuma feição hídrica encontrada nessa região.")