import streamlit as st
import time
from datetime import datetime
import pytz
from src.ui.streamlit.dashboard import Dashboard
from src.ui.streamlit.bitrix_dashboard import BitrixDashboard
from src.ui.streamlit.responsavel_dashboard import ResponsavelDashboard
from src.services.familia_service import familia_service

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Negociação e Análise Funil Bitrix24",
    page_icon="src/assets/logo.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Global
st.markdown("""
    <style>
        /* Estilo geral */
        .main {
            background-color: #ffffff;
            font-family: 'Montserrat', sans-serif;
            color: #333333;
            padding-top: 1rem;  /* Reduzido o padding superior */
        }
        
        /* Cores da Eu na Europa */
        :root {
            --primary-color: #003399;
            --secondary-color: #FFD700;
            --text-color: #333333;
            --background-color: #ffffff;
            --accent-color: #1a73e8;
        }
        
        /* Métrica principal em super destaque */
        .metric-card.super-highlight {
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            color: white;
            padding: 1.5rem 2rem;  /* Reduzido o padding */
            margin-bottom: 1.5rem;  /* Reduzido a margem */
            text-align: left;  /* Alinhamento à esquerda */
            border-radius: 8px;  /* Borda menos arredondada */
            box-shadow: 0 4px 8px rgba(26,115,232,0.15);  /* Sombra mais sutil */
        }
        
        .metric-card.super-highlight .metric-label {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem;  /* Fonte menor */
            font-weight: 600;
            margin-bottom: 0.75rem;  /* Espaçamento reduzido */
        }
        
        .metric-card.super-highlight .metric-value {
            color: white;
            font-size: 2.75rem;  /* Fonte menor */
            font-weight: 700;
            margin-bottom: 0.75rem;  /* Espaçamento reduzido */
            line-height: 1;  /* Altura da linha reduzida */
        }
        
        .metric-card.super-highlight .metric-description {
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;  /* Fonte menor */
            line-height: 1.3;
        }
        
        /* Cards de métricas normais */
        .metric-card {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.25rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        /* Reduzir espaçamento do título principal */
        .stTitle {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #ffffff;
            border-right: 1px solid #e9ecef;
        }
        
        .sidebar-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1a73e8;
            margin: 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e9ecef;
        }
        
        /* Textos */
        .metric-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #1a73e8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1a1f36;
            line-height: 1.2;
        }
        
        .metric-description {
            font-size: 0.813rem;
            color: #697386;
            margin-top: 0.5rem;
            line-height: 1.4;
        }
        
        /* Tabelas */
        .stDataFrame {
            border: 1px solid #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            background: white;
        }
        
        .stDataFrame th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #1a1f36;
            padding: 1rem;
            font-size: 0.875rem;
        }
        
        .stDataFrame td {
            padding: 0.875rem 1rem;
            color: #697386;
            font-size: 0.875rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        /* Botões */
        .stButton>button {
            background-color: #1a73e8;
            border: none;
            padding: 0.5rem 1rem;
            color: white;
            font-weight: 500;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            background-color: #1557b0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            border-bottom: 2px solid #e9ecef;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 0;
            color: #697386;
            font-weight: 500;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #1a73e8;
            border-bottom-color: #1a73e8;
        }
        
        /* Headers */
        h1 {
            color: #1a1f36;
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 0;
        }
        
        h2 {
            color: #1a1f36;
            font-weight: 600;
            font-size: 1.5rem;
            margin: 2rem 0 1rem;
        }
        
        h3 {
            color: #1a1f36;
            font-weight: 600;
            font-size: 1.25rem;
            margin: 1.5rem 0 1rem;
        }
        
        /* Métricas no Sidebar */
        .sidebar .stMetric {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            margin-bottom: 0.5rem;
        }
        
        .sidebar .stMetric label {
            color: #1a73e8;
            font-size: 0.813rem;
            font-weight: 600;
        }
        
        .sidebar .stMetric .css-1wivap2 {
            color: #1a1f36;
            font-size: 1.25rem;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Configurar logo no sidebar
import base64
from PIL import Image
import io

def get_base64_logo():
    try:
        with open('src/assets/logo.svg', 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        return None

# Classe para gerenciar o estado da aplicação
class AppState:
    def __init__(self):
        # Inicializar variáveis de sessão
        if 'start_time' not in st.session_state:
            st.session_state.start_time = time.time()

        if 'cache_status' not in st.session_state:
            st.session_state.cache_status = {
                'last_update': datetime.now(),
                'cache_hits': 0,
                'requests': 0
            }
        
        # Atualizar métricas
        st.session_state.cache_status['requests'] += 1
        self.execution_time = time.time() - st.session_state.start_time

        # Converter para fuso horário de São Paulo
        sp_tz = pytz.timezone('America/Sao_Paulo')
        last_update = datetime.now(sp_tz)
        st.session_state.cache_status['last_update'] = last_update
    
    def setup_sidebar(self):
        # Configurar logo
        logo_base64 = get_base64_logo()
        if logo_base64:
            st.sidebar.markdown(f"""
                <div style='text-align: center; margin-bottom: 1rem; padding: 1rem;'>
                    <img src="data:image/svg+xml;base64,{logo_base64}" width="120" height="120" style="margin-bottom: 0.5rem;">
                </div>
            """, unsafe_allow_html=True)

        # Sidebar de navegação
        st.sidebar.markdown("""
            <div class="sidebar-title">
                Navegação
            </div>
        """, unsafe_allow_html=True)

        tipo_relatorio = st.sidebar.selectbox(
            "Dashboards",
            ["Selecione uma opção", "Dashboard de Negociação", "Análise Funil Bitrix24", "Análise Responsável"]
        )

        # Métricas de performance no sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
            <div class="sidebar-title">
                Performance
            </div>
        """, unsafe_allow_html=True)

        # Formatar tempo de execução
        execution_time_ms = self.execution_time * 1000  # Converter para milissegundos

        st.sidebar.metric("Cache Hits", st.session_state.cache_status['cache_hits'])
        st.sidebar.metric("Tempo de Execução", f"{execution_time_ms:.0f}ms")
        st.sidebar.metric("Última Atualização", st.session_state.cache_status['last_update'].strftime("%H:%M:%S"))
        st.sidebar.metric("Tempo de Cache", "5 minutos")
        
        return tipo_relatorio

def main():
    # Inicializar estado da aplicação
    app_state = AppState()
    
    # Configurar sidebar e obter tipo de relatório selecionado
    tipo_relatorio = app_state.setup_sidebar()
    
    try:
        if tipo_relatorio == "Dashboard de Negociação":
            Dashboard.render()
        elif tipo_relatorio == "Análise Funil Bitrix24":
            BitrixDashboard.render()
        elif tipo_relatorio == "Análise Responsável":
            ResponsavelDashboard.render()
        elif tipo_relatorio == "Selecione uma opção":
            st.info("👈 Selecione um dashboard no menu lateral para começar")
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()