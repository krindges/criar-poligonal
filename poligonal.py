import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from io import BytesIO
from pyproj import Transformer

# Função para converter coordenadas geodésicas para UTM
def geodetic_to_utm(lat, lon):
    utm_zone = int((lon + 180) / 6) + 1
    proj_string = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
    transformer = Transformer.from_crs("EPSG:4326", proj_string, always_xy=True)
    easting, northing = transformer.transform(lon, lat)
    return utm_zone, easting, northing

# Função para gerar arquivo GMSH
def criar_gmsh(df):
    df['num_no'] = range(1, len(df)+1)
    df = df[['num_no', 'Tipo', 'Latitude', 'Longitude']]
    df[["UTM_Zone", "x", "y"]] = df.apply(lambda row: geodetic_to_utm(row["Latitude"], row["Longitude"]), axis=1, result_type="expand")
    df["UTM_Zone"] = df["UTM_Zone"].astype(int)

    df_rio = df[df['Tipo'] == 'Rio'].reset_index(drop=True)
    fim_rio = df_rio.at[df_rio.index[-1], 'num_no']
    gmsh = []

    for i in range(1, fim_rio+1):
        no = f'Point({i})={{ {df_rio.at[i-1, "x"]}, {df_rio.at[i-1, "y"]}, 0}};'
        gmsh.append(no)

    loop = '{'
    for i in range(1, fim_rio+1):
        linha = f'Line({i})={{ {i}, {i+1 if i+1 != fim_rio+1 else 1} }};'
        gmsh.append(linha)
        loop += f'{i},'
    loop = loop[:-1]
    gmsh.append(f'Line Loop(1) = {loop}}};')

    qtd_ilhas = len(df['Tipo'].unique()) - 1
    loop2 = '{1,'
    for ilha in range(1, qtd_ilhas+1):
        nome_ilha = f'Ilha_{ilha}'
        df_ilha = df[df['Tipo'] == nome_ilha].reset_index(drop=True)
        for i in range(df_ilha.at[0, 'num_no'], df_ilha.at[df_ilha.index[-1], 'num_no']+1):
            no = f'Point({i})={{ {df.at[i-1, "x"]}, {df.at[i-1, "y"]}, 0}};'
            gmsh.append(no)

        loop = '{'
        for i in range(df_ilha.at[0, 'num_no'], df_ilha.at[df_ilha.index[-1], 'num_no']+1):
            linha = f'Line({i})={{ {i}, {i+1 if i+1 != df_ilha.at[df_ilha.index[-1], "num_no"]+1 else df_ilha.at[0, "num_no"]} }};'
            gmsh.append(linha)
            loop += f'{i},'
        loop = loop[:-1]
        gmsh.append(f'Line Loop({ilha+1}) = {loop}}};')
        loop2 += f'{-ilha-1},'
    loop2 = loop2[:-1]
    gmsh.append(f'Plane Surface(1) = {loop2}}};')

    gmsh_text = '\n'.join(gmsh)
    buffer = BytesIO()
    buffer.write(gmsh_text.encode('utf-8'))
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Mundo Poligonal", layout="wide")
st.title("🧭 Mapa Interativo com Cursor Personalizado")

# Inicializa os dados no estado
if "pontos" not in st.session_state:
    st.session_state.pontos = []
if "tipo_atual" not in st.session_state:
    st.session_state.tipo_atual = "Rio"

# Componente HTML do mapa com Leaflet direto
coords_js_array = str(st.session_state.pontos).replace("'", "")
map_html = f"""
<!DOCTYPE html>
<html>  
<head>
<meta charset='utf-8' />
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<style>
  html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
  .leaflet-container {{ cursor: default !important; }}
</style>
<link rel='stylesheet' href='https://unpkg.com/leaflet/dist/leaflet.css' />
</head>
<body>
<div id='map'></div>
<script src='https://unpkg.com/leaflet/dist/leaflet.js'></script>
<script>
var coords = {coords_js_array};
var map = L.map('map').setView([-15.6, -56.06], 12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19 }}).addTo(map);

coords.forEach(p => {{
  L.circleMarker(p, {{radius: 5, color: 'red', fillColor: 'red', fillOpacity: 0.8}}).addTo(map);
}});

map.on('click', function(e) {{
  const lat = e.latlng.lat.toFixed(6);
  const lng = e.latlng.lng.toFixed(6);
  const iframe = window.parent.document.querySelector('iframe');
  iframe.contentWindow.postMessage({{lat: lat, lng: lng}}, '*');
}});
</script>
</body>
</html>
"""

components.html(map_html, height=500)

# JavaScript bridge
coords = st.query_params

# Captura coordenada do frontend
msg = st.query_params.get("coord")

# Simula recebimento manual (dev mode)
if st.button("🧪 Simular Clique (Dev)"):
    st.session_state.pontos.append([-15.6, -56.06])
    st.rerun()

# Botões
st.sidebar.subheader("Tipo de Poligonal")
st.session_state.tipo_atual = st.sidebar.radio("Escolha", ["Rio", "Ilha"])

if st.sidebar.button("Finalizar Poligonal"):
    st.success(f"✅ {st.session_state.tipo_atual} com {len(st.session_state.pontos)} ponto(s) finalizada.")
    st.session_state.pontos.append("NEW")  # separador

if st.sidebar.button("Apagar último ponto") and st.session_state.pontos:
    st.session_state.pontos.pop()
    st.rerun()

# Exporta dados
if st.sidebar.button("📥 Baixar Excel e GMSH"):
    data = []
    tipo = "Rio"
    for p in st.session_state.pontos:
        if p == "NEW":
            tipo = f"Ilha_{len([x for x in data if x[0].startswith('Ilha')])+1}"
        else:
            data.append([tipo, float(p[0]), float(p[1])])
    df = pd.DataFrame(data, columns=["Tipo", "Latitude", "Longitude"])
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Poligonais", index=False)
    excel_buffer.seek(0)
    st.sidebar.download_button("📥 Excel", data=excel_buffer, file_name="poligonais.xlsx")
    st.sidebar.download_button("📥 GMSH", data=criar_gmsh(df), file_name="malha.txt")