import pandas as pd
import streamlit as st
import unicodedata

# ========================= CONFIGURAÇÃO DA PÁGINA ==========================
st.set_page_config(
    page_title='Entregas Cosmética',
    layout='wide'
)

# ======================= CSS Customizado ===========================
def css_personalizado():
    st.markdown("""
    <style>
    /* Fundo geral da página */
    .main {
        background-color: #F4F6FA;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #2E3B4E;
        padding: 20px;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] label {
        color: #D2D6DB !important;
        font-weight: 500;
    }

    /* Títulos padrões */
    h2, h3, h4 {
        color: #2E3B4E;
        font-weight: 700 !important;
    }

    /* KPIs com estilo */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #DDE1E4;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="metric-container"] > label {
        color: #2E3B4E;
    }

    /* DataFrame (cabeçalho) */
    .dataframe th {
        background-color: #2E62A3 !important;
        color: white !important;
    }

    /* Alertas */
    .stAlert {
        border-radius: 8px !important;
    }

    </style>
    """, unsafe_allow_html=True)

# ========================= FUNÇÕES AUXILIARES ==============================

colunas_entregas = [
    'Data','N_Pedido','N_NF','TV','N_Car','pos','Código','Cliente',
    'Cidade','Praca','RCA','Vlr_Atendido','Peso_Total'
]

def remover_acentos(texto: str) -> str:
    if pd.isna(texto):
        return ''
    texto = str(texto)
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.strip().upper()

def tratar_valor(valor):
    """Trata valores monetários para float (R$ 1.234,56 -> 1234.56)."""
    if pd.isna(valor):
        return 0.0
    valor = str(valor)
    valor = valor.replace("R$", "")
    valor = valor.replace(".", "")   # tira milhar
    valor = valor.replace(",", ".")  # vírgula decimal
    valor = valor.strip()
    try:
        return float(valor)
    except:
        return 0.0

def tratar_peso(peso):
    """Trata valores de peso para float (1.234,56 -> 1234.56)."""
    if pd.isna(peso):
        return 0.0
    peso = str(peso)
    peso = peso.replace(".", "")     # tira milhar
    peso = peso.replace(",", ".")    # vírgula decimal
    peso = peso.strip()
    try:
        return float(peso)
    except:
        return 0.0

def encontrar_coluna_municipio(df: pd.DataFrame):
    """
    Procura no dataframe a coluna que representa MUNICIPIO/CIDADE,
    comparando o nome normalizado (sem acento, maiúsculo).
    """
    for col in df.columns:
        nome_normalizado = remover_acentos(col)
        if nome_normalizado in ['MUNICIPIO', 'MUNICIPIOS', 'CIDADE', 'CIDADES']:
            return col
    return None

# ========================= FUNÇÕES DE CARGA ================================

def carregar_entrega():
    arquivo = st.file_uploader(
        'Carregar arquivo de entregas:',
        type=('txt', 'csv', 'xlsx'),
        key='upload_entregas'
    )

    if arquivo is not None:
        nome = arquivo.name.lower()

        if nome.endswith('.csv') or nome.endswith('.txt'):
            df = pd.read_csv(arquivo, header=None, names=colunas_entregas)
        elif nome.endswith('.xlsx'):
            df = pd.read_excel(arquivo, header=None, names=colunas_entregas)
        else:
            st.error("Formato não suportado para entregas.")
            return None

        # Normaliza a coluna Cidade
        df['Cidade'] = df['Cidade'].apply(remover_acentos)

        st.success("Arquivo de entregas carregado com sucesso!")
        return df

    return None

def carregar_regiao():
    arquivo = st.file_uploader(
        'Carregar arquivo de regiões:',
        type=('txt', 'csv', 'xlsx'),
        key='upload_regioes'
    )

    if arquivo is not None:
        nome = arquivo.name.lower()

        if nome.endswith('.csv') or nome.endswith('.txt'):
            df = pd.read_csv(arquivo)
        elif nome.endswith('.xlsx'):
            df = pd.read_excel(arquivo)
        else:
            st.error("Formato não suportado para regiões.")
            return None

        st.success("Arquivo de regiões carregado com sucesso!")
        return df

    return None

# ========================= MERGE ENTREGAS x REGIÃO =========================

def juncao_entrega_regiao(df_entregas, df_regiao):
    if df_entregas is None or df_regiao is None:
        return None

    col_mun = encontrar_coluna_municipio(df_regiao)

    if col_mun is None:
        st.error("Não foi possível identificar a coluna de município/cidade no arquivo de regiões.")
        st.write("Colunas encontradas no arquivo de regiões:", list(df_regiao.columns))
        return None

    df_e = df_entregas.copy()
    df_r = df_regiao.copy()

    df_e['CHAVE_CIDADE'] = df_e['Cidade'].apply(remover_acentos)
    df_r['CHAVE_MUNICIPIO'] = df_r[col_mun].apply(remover_acentos)

    df_merge = pd.merge(
        df_e,
        df_r,
        left_on='CHAVE_CIDADE',
        right_on='CHAVE_MUNICIPIO',
        how='left'
    )

    df_merge.drop(columns=['CHAVE_CIDADE', 'CHAVE_MUNICIPIO'], inplace=True)

    return df_merge

# =============================== APLICAÇÃO ==================================

def main():
    css_personalizado()

    # Cabeçalho principal
    st.markdown("""
    <div style='padding: 15px; background-color: #2E62A3; border-radius: 8px; margin-bottom: 15px;'>
        <h1 style='color: white; text-align: center;'>
            🚚 Entregas - Cosmética Distribuidora
        </h1>
        <p style='color: #E3EAF2; text-align: center; font-size: 16px; margin-top: -10px;'>
            Rotina 335 • Integração com Inteligência Artificial
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------- SEÇÃO DE UPLOAD (TOPO) -------------------------
    with st.container(border=True):
        st.subheader("📂 Carga de Arquivos")

        load1, load2 = st.columns(2)

        with load1:
            st.markdown("**Arquivo de Entregas**")
            df_entregas = carregar_entrega()

        with load2:
            st.markdown("**Arquivo de Regiões**")
            df_regiao = carregar_regiao()

    df_final = None

    if df_entregas is not None and df_regiao is not None:
        df_final = juncao_entrega_regiao(df_entregas, df_regiao)

    # ---------------------- SEÇÃO DE FILTROS (SIDEBAR) ---------------------
    sel_car = []
    sel_regiao = []

    if df_final is not None:
        with st.sidebar:
            st.header("🔍 Filtros")

            if 'N_Car' in df_final.columns:
                carregamentos = sorted(df_final['N_Car'].dropna().unique())
                sel_car = st.multiselect(
                    'Carregamento:',
                    options=carregamentos
                )

            if 'Região' in df_final.columns:
                regioes = sorted(df_final['Região'].dropna().unique())
                sel_regiao = st.multiselect(
                    'Região:',
                    options=regioes
                )

            st.markdown("---")
            st.caption("Cosmética Distribuidora • IA Aplicada • 2025")

    # ---------------------- SEÇÃO CENTRAL: KPIs + TABELAS ------------------
    if df_final is not None:
        # Aplica filtros
        df_filtrado = df_final.copy()

        if sel_car:
            df_filtrado = df_filtrado[df_filtrado['N_Car'].isin(sel_car)]

        if sel_regiao:
            df_filtrado = df_filtrado[df_filtrado['Região'].isin(sel_regiao)]

        # ---------- TRATAMENTO NUMÉRICO PARA KPI ----------
        df_kpi = df_filtrado.copy()

        if 'Vlr_Atendido' in df_kpi.columns:
            df_kpi['Vlr_Atendido'] = df_kpi['Vlr_Atendido'].apply(tratar_valor)
        else:
            df_kpi['Vlr_Atendido'] = 0.0

        if 'Peso_Total' in df_kpi.columns:
            df_kpi['Peso_Total'] = df_kpi['Peso_Total'].apply(tratar_peso)
        else:
            df_kpi['Peso_Total'] = 0.0

        qt_entregas = len(df_kpi)
        total_valor = df_kpi['Vlr_Atendido'].sum(min_count=1)
        total_peso = df_kpi['Peso_Total'].sum(min_count=1)

        if pd.isna(total_valor):
            total_valor = 0.0
        if pd.isna(total_peso):
            total_peso = 0.0

        valor_formatado = f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        peso_formatado = f"{total_peso:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # ---------------------- KPIs (LINHA SUPERIOR) ----------------------
        st.subheader("📊 Indicadores Gerais")

        kpi1, kpi2, kpi3 = st.columns(3)

        with kpi1:
            st.metric("Quantidade de Entregas", value=int(qt_entregas))

        with kpi2:
            st.metric("Valor Atendido", value=valor_formatado)

        with kpi3:
            st.metric("Peso Total (kg)", value=peso_formatado)

        st.markdown("---")

        # ---------------------- TABELA FILTRADA ----------------------------
        st.subheader("📦 Tabela de Entregas (Filtrada)")
        st.dataframe(df_filtrado, use_container_width=True)

        # ---------------------- RESUMO POR REGIÃO --------------------------
        if 'Região' in df_kpi.columns:
            df_resumo = (
                df_kpi
                .groupby('Região', as_index=False)['Vlr_Atendido']
                .sum()
                .rename(columns={'Vlr_Atendido': 'Total_Atendido'})
            )

            # Formata como moeda
            df_resumo['Total_Atendido'] = df_resumo['Total_Atendido'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )

            st.subheader("🌎 Resumo por Região (Valor Atendido)")
            st.dataframe(df_resumo, use_container_width=True)

    else:
        st.info("Carregue os arquivos de entregas e regiões para visualizar o dashboard.")

# =============================== EXECUÇÃO ===================================

if __name__ == '__main__':
    main()
