import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from io import BytesIO

# Título do aplicativo
st.title("Mapa com Poligonais Interativas")

# Inicializar session_state
if "coordenadas" not in st.session_state:
    st.session_state.coordenadas = []

if "poligonal_principal" not in st.session_state:
    st.session_state.poligonal_principal = None  # Guarda a poligonal principal

if "poligonais_secundarias" not in st.session_state:
    st.session_state.poligonais_secundarias = []  # Lista de poligonais secundárias

if "ultimo_ponto" not in st.session_state:
    st.session_state.ultimo_ponto = [-23.55052, -46.633308]  # Ponto inicial (São Paulo)

# Criando o mapa centralizado no último ponto adicionado
mapa = folium.Map(location=st.session_state.ultimo_ponto, zoom_start=30)

# Adicionando pontos (bolinhas vermelhas)
for coord in st.session_state.coordenadas:
    folium.CircleMarker(
        location=coord,
        radius=4,  # 🔴 Tamanho da bolinha pequena
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=1.0
    ).add_to(mapa)

# Adicionando a poligonal atual (em construção)
if len(st.session_state.coordenadas) > 2:
    folium.Polygon(
        locations=st.session_state.coordenadas,
        color="blue",
        weight=2,
        fill=True,
        fill_color="blue",
        fill_opacity=0.4
    ).add_to(mapa)

# Adicionando poligonal principal (se existir)
if st.session_state.poligonal_principal:
    folium.Polygon(
        locations=st.session_state.poligonal_principal,
        color="green",  # Verde para poligonal principal
        weight=3,
        fill=True,
        fill_color="green",
        fill_opacity=0.4
    ).add_to(mapa)

# Adicionando poligonais secundárias (se houver)
for poligono in st.session_state.poligonais_secundarias:
    folium.Polygon(
        locations=poligono,
        color="orange",  # Laranja para poligonais secundárias
        weight=2,
        fill=True,
        fill_color="orange",
        fill_opacity=0.4
    ).add_to(mapa)

# Renderizando o mapa e capturando interações do usuário
st.subheader("Mapa Interativo")
map_data = st_folium(mapa, height=500, width=700)

# Captura de clique no mapa
if map_data and "last_clicked" in map_data and map_data["last_clicked"] is not None:
    novo_ponto = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
    
    # Adicionar o novo ponto à lista se for único
    if novo_ponto not in st.session_state.coordenadas:
        st.session_state.coordenadas.append(novo_ponto)
        st.session_state.ultimo_ponto = novo_ponto  # Atualiza o centro do mapa
        st.rerun()  # Atualiza o mapa

# # Interface para adicionar pontos manualmente
# st.sidebar.header("Adicionar Pontos Manualmente")
# lat = st.sidebar.number_input("Latitude", format="%.6f", value=st.session_state.ultimo_ponto[0])
# lon = st.sidebar.number_input("Longitude", format="%.6f", value=st.session_state.ultimo_ponto[1])

# if st.sidebar.button("Adicionar Ponto"):
#     novo_ponto = [lat, lon]
#     st.session_state.coordenadas.append(novo_ponto)
#     st.session_state.ultimo_ponto = novo_ponto
#     st.rerun()

# Exibir as coordenadas utilizadas
st.subheader("Coordenadas da Poligonal Atual")
st.write(st.session_state.coordenadas if st.session_state.coordenadas else "Nenhuma coordenada definida.")

# Botão para limpar os pontos da poligonal atual
if st.sidebar.button("Limpar Poligonal"):
    st.session_state.coordenadas = []
    st.rerun()

# **🔹 Salvar a poligonal principal**
if st.sidebar.button("Salvar Poligonal do Rio"):
    if len(st.session_state.coordenadas) > 2:
        st.session_state.poligonal_principal = st.session_state.coordenadas.copy()
        st.session_state.coordenadas = []  # Limpar para próxima poligonal
        st.success("✅ Poligonal do rio Salva!")
        st.rerun()
    else:
        st.warning("⚠️ A poligonal deve ter pelo menos 3 pontos!")

# **🔹 Salvar poligonais secundárias**
if st.sidebar.button("Salvar Poligonal da Ilha"):
    if len(st.session_state.coordenadas) > 2:
        st.session_state.poligonais_secundarias.append(st.session_state.coordenadas.copy())
        st.session_state.coordenadas = []  # Limpar para próxima poligonal
        st.success("✅ Poligonal da ilha Salva!")
        st.rerun()
    else:
        st.warning("⚠️ A poligonal deve ter pelo menos 3 pontos!")

# **🔹 Criar e baixar o arquivo Excel**
def salvar_coordenadas():
    """Salva todas as poligonais em um arquivo Excel e gera um link para download."""
    data = []

    # Adicionar a poligonal principal
    if st.session_state.poligonal_principal:
        for ponto in st.session_state.poligonal_principal:
            data.append(["Rio", ponto[0], ponto[1]])

    # Adicionar poligonais secundárias
    for idx, poligono in enumerate(st.session_state.poligonais_secundarias):
        for ponto in poligono:
            data.append([f"Ilha_{idx+1}", ponto[0], ponto[1]])

    if data:
        # Criar DataFrame
        df = pd.DataFrame(data, columns=["Tipo", "Latitude", "Longitude"])
        
        # Criar um buffer de bytes para armazenar o Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Poligonais", index=False)
        
        output.seek(0)  # Retornar ao início do arquivo
        return output,df
    
    return None

# Botão para salvar todas as poligonais no Excel
if st.sidebar.button("Salvar Todas as Poligonais"):
    excel_file,df = salvar_coordenadas()
    st.dataframe(df)
    if excel_file:
        st.download_button(
            label="📥 Baixar Arquivo Excel",
            data=excel_file,
            file_name="poligonais.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Nenhuma poligonal disponível para salvar!")
