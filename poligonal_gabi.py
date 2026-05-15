import math
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import folium
from streamlit_folium import st_folium
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Mundo Poligonal", layout="wide")
st.title("🌐Mapa com Poligonais Interativas")

# ✅ Passo a passo logo no início
with st.expander("ℹ️ Como usar o sistema", expanded=True):
    st.markdown("""
    ### 📝 Guia Completo de Uso

    #### 🌍 Navegação no Mapa
    1. **Buscar localização**:
       - Digite um endereço/cidade na barra de busca 🔍
       - Clique em "Buscar" para centralizar o mapa
    2. **Zoom/Navegação manual**:
       - Use scroll do mouse para zoom (+/-)
       - Arraste o mapa para navegar

    #### 🖱️ Criando Poligonais
    1. **Poligonal Principal (Rio)**:
       - Clique no mapa para adicionar pontos 🔴
       - Adicione pelo menos 3 pontos
       - Clique em 🔚 **Finalizar Poligonal do Rio**
    2. **Poligonais Secundárias (Ilhas)**:
       - Adicione novos pontos no mapa
       - Clique em 🔚 **Finalizar Poligonal da Ilha**
       - Repita para múltiplas ilhas

    #### 🛠️ Ferramentas de Edição
    - ❌ **Apagar Última Coordenada**: Remove o último ponto adicionado
    - 🗑️ **Remover Última Poligonal**: Exclui a última poligonal salva
    - 🔃 **Reiniciar Tudo** (com confirmação):
       - Volta para a posição inicial
       - Remove TODAS as poligonais

    #### 💾 Exportação de Dados
    **Excel (.xlsx)**
    1. Clique em 💾 **Salvar Todas as Poligonais**
    2. Visualize a tabela com todas as coordenadas
    3. Baixe o arquivo com 📥 **Baixar Arquivo Excel**

    **GMSH (.geo)**
    1. Clique em 🔷 **Exportar para GMSH (.geo)**
    2. Baixe o arquivo com 📥 **Baixar Arquivo .geo**
    - As coordenadas são convertidas automaticamente de lat/lon para **UTM (metros)**
    - A zona UTM é determinada automaticamente pela localização da poligonal
    - O arquivo pode ser aberto diretamente no GMSH para geração de malhas

    #### ⚠️ Boas Práticas
    - Sempre comece pela poligonal do rio
    - Use zoom próximo (nível 15+) para maior precisão

    ---
    🎦 **Dica**: Cliques acidentais? Use ❌ Apagar Última Coordenada para corrigir!
    """)

# Inicializar variáveis no session_state para armazenar dados ao longo da execução
if "coordenadas" not in st.session_state:
    st.session_state.coordenadas = []  # Lista de coordenadas temporárias para a poligonal atual

if "poligonal_principal" not in st.session_state:
    st.session_state.poligonal_principal = None  # Guarda a poligonal principal salva

if "poligonais_secundarias" not in st.session_state:
    st.session_state.poligonais_secundarias = []  # Lista de poligonais secundárias

if "ultimo_ponto" not in st.session_state:
    st.session_state.ultimo_ponto = [-15.608041311445879, -56.06389224529267]  # Ponto inicial no mapa (Liama)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []  # Lista para armazenar mensagens de status

# Barra de busca de cidades
st.sidebar.subheader("🔍 Buscar Localização")
cidade = st.sidebar.text_input("Digite uma cidade, endereço ou ponto de interesse:")

if st.sidebar.button("Buscar"):
    if cidade:
        try:
            with st.spinner("Buscando localização..."):
                geolocator = Nominatim(user_agent="streamlit_map_search")
                location = geolocator.geocode(cidade, timeout=10)

                if location:
                    # Atualiza os estados globais com a nova localização
                    st.session_state.ultimo_ponto = [location.latitude, location.longitude]
                    st.session_state.zoom_level = 10  # Ajuste de zoom ao buscar cidade

                    # Salva a última busca
                    st.session_state.local_buscado = {
                        "coords": [location.latitude, location.longitude],
                        "endereco": location.address
                    }

                    st.success(f"📍 Local encontrado: {location.address}")
                    st.rerun()  # Atualiza a interface para refletir a nova localização
                else:
                    st.sidebar.warning("🚫 Local não encontrado. Tente um termo mais específico.")
        except GeocoderTimedOut:
            st.sidebar.error("⏳ O serviço demorou muito para responder. Tente novamente.")
        except GeocoderServiceError:
            st.sidebar.error("⚠️ Serviço de geolocalização indisponível no momento.")
        except Exception as e:
            st.sidebar.error(f"❌ Erro inesperado: {str(e)}")

# Criando o mapa centralizado no último ponto adicionado
zoom = st.session_state.get("zoom_level", 12)  # Usa o zoom_level se existir, senão usa 30
mapa = folium.Map(location=st.session_state.ultimo_ponto, zoom_start=zoom)

# Adicionando os pontos individuais ao mapa como marcadores circulares vermelhos
for coord in st.session_state.coordenadas:
    folium.CircleMarker(
        location=coord,
        radius=4,  # 🔴 Tamanho do marcador
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=1.0
    ).add_to(mapa)

# Adicionando a poligonal atual (se houver mais de 2 pontos)
if len(st.session_state.coordenadas) > 2:
    folium.Polygon(
        locations=st.session_state.coordenadas,
        color="blue",
        weight=2,
        fill=True,
        fill_color="blue",
        fill_opacity=0.4
    ).add_to(mapa)

# Adicionando a poligonal principal, se já foi salva
if st.session_state.poligonal_principal:
    folium.Polygon(
        locations=st.session_state.poligonal_principal,
        color="green",  # Verde para a poligonal principal
        weight=3,
        fill=True,
        fill_color="green",
        fill_opacity=0.4
    ).add_to(mapa)

# Adicionando poligonais secundárias, se houver
for poligono in st.session_state.poligonais_secundarias:
    folium.Polygon(
        locations=poligono,
        color="magenta",  # Magenta para as poligonais secundárias
        weight=2,
        fill=True,
        fill_color="magenta",
        fill_opacity=0.4
    ).add_to(mapa)

# Renderizando o mapa interativo e capturando cliques do usuário
st.subheader("Mapa Interativo")
map_data = st_folium(
    mapa,
    height=500,
    width=700,
    returned_objects=["last_clicked", "zoom"]  # ← Captura também o zoom atual!
)

# Captura de cliques no mapa e adiciona novas coordenadas à lista
if map_data and "last_clicked" in map_data and map_data["last_clicked"] is not None:
    novo_ponto = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
    
    # Adiciona o novo ponto apenas se ele ainda não estiver na lista
    if novo_ponto not in st.session_state.coordenadas:
        st.session_state.coordenadas.append(novo_ponto)
        st.session_state.ultimo_ponto = novo_ponto  # Atualiza a centralização do mapa
        
        # ✅ Mantém o zoom atual (se disponível) em vez de resetar
        if "zoom" in map_data and map_data["zoom"] is not None:
            st.session_state.zoom_level = map_data["zoom"]
        
        st.rerun()  # Atualiza a interface

# Exibir as coordenadas utilizadas na poligonal atual
#st.subheader("Coordenadas da Poligonal Atual")
#st.write(st.session_state.coordenadas if st.session_state.coordenadas else "Nenhuma coordenada definida.")

# Botão para excluir a última poligonal salva
if st.sidebar.button("🗑️ Remover Última Poligonal"):
    if st.session_state.poligonais_secundarias:
        # Remove a última poligonal secundária e identifica qual foi removida
        index_removida = len(st.session_state.poligonais_secundarias)  # Índice da última ilha
        st.session_state.poligonais_secundarias.pop()
        st.session_state.mensagens.append(f"🗑️ Poligonal Ilha_{index_removida} removida com sucesso!")
        st.rerun()
    elif st.session_state.poligonal_principal:
        # Se não houver poligonais secundárias, remove a poligonal principal
        st.session_state.poligonal_principal = None
        st.session_state.mensagens.append("🗑️ Poligonal do Rio removida com sucesso!")
        st.rerun()
    else:
        st.warning("⚠️ Nenhuma poligonal para remover!")

# Botão para remover o último ponto adicionado
if st.sidebar.button("❌ Apagar Última Coordenada"):
    if st.session_state.coordenadas:
        st.session_state.coordenadas.pop()  # Remove o último ponto da lista
        st.success("🗑️ Último ponto removido!")
        st.rerun()
    else:
        st.warning("⚠️ Nenhum ponto para remover!")

# Botão para salvar a poligonal principal
if not st.session_state.poligonal_principal:
    if st.sidebar.button("🔚 Finalizar Poligonal do Rio"):
        if len(st.session_state.coordenadas) > 2:  # Exige ao menos 3 pontos
            st.session_state.poligonal_principal = st.session_state.coordenadas.copy()
            st.session_state.coordenadas = []  # Reseta a poligonal temporária
            st.session_state.mensagens.append("✅ Poligonal do Rio finalizada com sucesso!")
            st.rerun()
        else:
            st.warning("⚠️ A poligonal deve ter pelo menos 3 pontos!")
else:
    st.sidebar.warning("⚠️ A poligonal do rio já foi finalizada e não pode ser alterada!")


# Botão para salvar poligonais secundárias (apenas se a poligonal principal foi salva)
if st.session_state.poligonal_principal:
    if st.sidebar.button("🔚 Finalizar Poligonal da Ilha"):
        if len(st.session_state.coordenadas) > 2:  # Exige ao menos 3 pontos
            st.session_state.poligonais_secundarias.append(st.session_state.coordenadas.copy())
            st.session_state.coordenadas = []  # Reseta a poligonal temporária
            st.session_state.mensagens.append(f"✅ Poligonal Ilha_{len(st.session_state.poligonais_secundarias)} finalizada com sucesso!")
            st.rerun()
        else:
            st.warning("⚠️ A poligonal deve ter pelo menos 3 pontos!")
else:
    st.sidebar.warning("⚠️ Salve a poligonal do rio primeiro!")

# Exibir mensagens de status na barra lateral
st.sidebar.subheader("Status das Poligonais")
for mensagem in st.session_state.mensagens:
    st.sidebar.success(mensagem)

def _latlon_para_utm(lat, lon):
    """Converte lat/lon WGS84 para coordenadas UTM (metros)."""
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2 * f - f ** 2
    e2l = e2 / (1 - e2)
    zona = int((lon + 180) / 6) + 1
    lon0 = math.radians(-183 + zona * 6)
    latr = math.radians(lat)
    lonr = math.radians(lon)
    N = a / math.sqrt(1 - e2 * math.sin(latr) ** 2)
    T = math.tan(latr) ** 2
    C = e2l * math.cos(latr) ** 2
    A = math.cos(latr) * (lonr - lon0)
    M = a * (
        (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * latr
        - (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * math.sin(2*latr)
        + (15*e2**2/256 + 45*e2**3/1024) * math.sin(4*latr)
        - (35*e2**3/3072) * math.sin(6*latr)
    )
    k0 = 0.9996
    x = k0 * N * (A + (1-T+C)*A**3/6 + (5-18*T+T**2+72*C-58*e2l)*A**5/120) + 500000
    y = k0 * (M + N * math.tan(latr) * (
        A**2/2 + (5-T+9*C+4*C**2)*A**4/24 + (61-58*T+T**2+600*C-330*e2l)*A**6/720
    ))
    if lat < 0:
        y += 10000000
    return x, y, zona


def gerar_gmsh():
    """Gera o arquivo .geo no formato GMSH para todas as poligonais."""
    if not st.session_state.poligonal_principal:
        return None, "Nenhuma poligonal disponível para exportar!"

    saida = []
    pid = 1
    lid = 1
    loops = []

    lat0, lon0_ref = st.session_state.poligonal_principal[0]
    _, _, zona = _latlon_para_utm(lat0, lon0_ref)
    hemi = "S" if lat0 < 0 else "N"
    saida.append(f"// Projeção: UTM Zona {zona}{hemi} (WGS84)")
    saida.append("")

    todas = [st.session_state.poligonal_principal] + st.session_state.poligonais_secundarias

    for idx, pontos in enumerate(todas):
        n = len(pontos)
        p_ini = pid
        l_ini = lid
        loop_num = idx + 1

        for lat, lon in pontos:
            x, y, _ = _latlon_para_utm(lat, lon)
            saida.append(f"Point({pid}) = {{ {x:.4f}, {y:.4f}, 0 }};")
            pid += 1

        for i in range(n):
            saida.append(f"Line({lid}) = {{ {p_ini + i}, {p_ini + (i + 1) % n} }};")
            lid += 1

        all_lines = list(range(l_ini, lid))
        saida.append(f"Line Loop({loop_num}) = {{ {', '.join(map(str, all_lines))} }};")
        saida.append("")
        loops.append(loop_num)

    saida.append(f"Plane Surface(1) = {{ {', '.join(map(str, loops))} }};")

    return "\n".join(saida).encode("utf-8"), None


# **Função para salvar todas as poligonais em um arquivo Excel**
def salvar_coordenadas():
    """Salva todas as poligonais em um arquivo Excel e gera um link para download."""
    data = []

    # Adiciona a poligonal principal ao conjunto de dados
    if st.session_state.poligonal_principal:
        for ponto in st.session_state.poligonal_principal:
            data.append(["Rio", ponto[0], ponto[1]])

    # Adiciona as poligonais secundárias ao conjunto de dados
    for idx, poligono in enumerate(st.session_state.poligonais_secundarias):
        for ponto in poligono:
            data.append([f"Ilha_{idx+1}", ponto[0], ponto[1]])

    if data:
        # Criar um DataFrame do Pandas para armazenar os dados
        df = pd.DataFrame(data, columns=["Tipo", "Latitude", "Longitude"])
        
        # Criar um buffer de bytes para armazenar o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Poligonais", index=False)
        
        output.seek(0)  # Retornar ao início do arquivo para o download
        return output, df

    return None

# Botão para salvar todas as poligonais em um arquivo Excel e disponibilizar para download
if st.sidebar.button("💾 Salvar Todas as Poligonais"):
    resultado = salvar_coordenadas()

    if resultado is None:
        st.warning("⚠️ Nenhuma poligonal disponível para salvar!")
    elif isinstance(resultado, tuple) and isinstance(resultado[1], str):
        # Caso retorne uma mensagem de texto (ex: erro ou aviso)
        st.warning(resultado[1])
    else:
        excel_file, df = resultado
        st.dataframe(df)
        if excel_file:
            st.success("✅ Poligonais salvas com sucesso! Agora você já pode fazer o download da sua planilha do Excel.")
            st.download_button(
                label="📥 Baixar Arquivo Excel",
                data=excel_file,
                file_name="poligonais.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# Botão para exportar no formato GMSH (.geo)
if st.sidebar.button("🔷 Exportar para GMSH (.geo)"):
    geo_bytes, erro = gerar_gmsh()
    if erro:
        st.warning(f"⚠️ {erro}")
    else:
        st.success("✅ Arquivo GMSH gerado com sucesso!")
        st.download_button(
            label="📥 Baixar Arquivo .geo",
            data=geo_bytes,
            file_name="poligonais.geo",
            mime="text/plain"
        )

# Lógica: define a checkbox, mas ainda não exibe
confirmar_remocao = st.session_state.get("confirmar_remocao", False)

# Botão para reset completo (poligonais + posição inicial)
if st.sidebar.button("🔃 Reiniciar Tudo"):
    if confirmar_remocao:
        # Limpa todos os dados
        st.session_state.coordenadas = []
        st.session_state.poligonal_principal = None
        st.session_state.poligonais_secundarias = []
        st.session_state.mensagens = []
        
        # Volta para posição inicial (Cuiabá/MT)
        st.session_state.ultimo_ponto = [-15.608041311445879, -56.06389224529267]  # Coordenadas iniciais
        
        # Mantém o zoom atual (opcional - remova esta linha se quiser resetar o zoom também)
        st.session_state.zoom_level = 12  # Descomente para definir um zoom padrão
        
        st.success("✅ Reset completo realizado! Voltando à posição inicial.")
        st.rerun()
    else:
        st.warning("⚠️ Confirme a exclusão para reiniciar")

st.sidebar.checkbox("Confirmar exclusão", key="confirmar_remocao")

