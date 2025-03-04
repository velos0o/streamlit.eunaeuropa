"""Componente de dashboard para análise de responsáveis e funil do Bitrix24"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import io
import os
import re
import base64
from io import BytesIO
import sys
import warnings
import locale
import time

# Função para gerar link de download para Excel
def get_excel_download_link(df, filename="dados.xlsx", text="Baixar Excel"):
    """Gera um link para download de um DataFrame como arquivo Excel."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Ignorar warnings do pandas e openpyxl
        warnings.simplefilter("ignore")
        
        # Escrever o DataFrame para o Excel
        df.to_excel(writer, index=False, sheet_name="Dados")
        
        # Ajustar a largura das colunas automaticamente
        worksheet = writer.sheets["Dados"]
        for i, col in enumerate(df.columns):
            # Calcular a largura máxima baseada no conteúdo
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2  # Adiciona um pouco de espaço extra
            
            # Ajustar a largura da coluna
            worksheet.column_dimensions[chr(65 + i)].width = min(max_len, 50)  # Limita a largura a 50 caracteres
    
    # Obter o valor do BytesIO como base64
    b64 = base64.b64encode(output.getvalue()).decode()
    
    # Criar o link para download usando o estilo da classe excel-btn
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-btn excel-btn">{text}</a>'
    return href

# Ignorar avisos
warnings.filterwarnings('ignore')

# Tentar definir locale para o Brasil - para formatação de data
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass

# Função para formatar números com separador de milhar
def formatar_numero(valor):
    """Formata um número com separador de milhar."""
    try:
        if isinstance(valor, (int, float)):
            return locale.format_string("%d", valor, grouping=True)
        return str(valor)
    except:
        return str(valor)

# Definir um esquema de cores com melhor contraste
THEME_COLORS = {
    "primary": "#1E88E5",       # Azul principal mais escuro
    "secondary": "#0D47A1",     # Azul secundário ainda mais escuro
    "accent": "#FFC107",        # Amarelo para destaque
    "background": "#FFFFFF",    # Fundo branco
    "card": "#F8F9FA",          # Cinza muito claro para cartões
    "text": "#212121",          # Texto quase preto
    "text_secondary": "#424242" # Texto secundário cinza escuro
}

# Lista de fases em ordem cronológica
FASES_ORDEM = [
    "REUNIÃO AGENDADA",
    "REUNIÃO REALIZADA",
    "EM NEGOCIAÇÃO",
    "ORÇAMENTO",
    "CRIAR ADENDO",
    "VALIDANDO ADENDO",
    "CLAUSULAS ESPECIAS",
    "EM ASSINATURA",
    "ASSINADO",
    "VALIDADO ENVIAR FINANCEIRO",
    "ENV. NOVO ADM",
    "ASSINATURA INCOMPLETAS",
    "REVERSÃO",
    "DISTRATO APROVADO",
    "ENV.. NOVO ADM"
]

# Cores para as fases do funil
FASE_COLORS = {
    "REUNIÃO AGENDADA": "#4CAF50",     # Verde
    "REUNIÃO REALIZADA": "#8BC34A",    # Verde claro
    "EM NEGOCIAÇÃO": "#2196F3",        # Azul
    "ORÇAMENTO": "#03A9F4",            # Azul claro
    "CRIAR ADENDO": "#FF9800",
    "VALIDANDO ADENDO": "#FF9890",                # Laranja
    "CLAUSULAS ESPECIAS": "#FF5722",   # Laranja escuro
    "EM ASSINATURA": "#9C27B0",        # Roxo
    "ASSINADO": "#673AB7",             # Roxo escuro
    "VALIDADO ENVIAR FINANCEIRO": "#673AB7",              # Vermelho
    "ENV. NOVO ADM": "#3F51B5",
    "ASSINATURA INCOMPLETAS": "#3F51B5",
    "REVERSÃO": "#3F51B5",
    "DISTRATO APROVADO": "#3F51B5",
    "ENV.. NOVO ADM": "#3F51B5"
            # Azul escuro
}

class ResponsavelDashboard:
    """Classe para gerenciar a interface do dashboard de análise de responsáveis e funil"""

    @staticmethod
    def set_style():
        """Define o estilo CSS personalizado para o dashboard"""
        st.markdown("""
            <style>
            /* Variáveis de cores */
            :root {
                --cor-azul-claro: #E3F2FD;
                --cor-azul-medio: #1976D2;
                --cor-azul-escuro: #0D47A1;
                --cor-texto: #37474F;
                --cor-borda: #E0E0E0;
            }
            
            /* Estilo geral */
            .stApp {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            /* Estilo das abas de navegação */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0;
                background-color: #e3f2fd;
                padding: 8px 8px 0 8px;
                border-radius: 8px 8px 0 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #bbdefb;
                margin-bottom: 0;
                border-bottom: none;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 40px;
                white-space: pre;
                background-color: white;
                border-radius: 6px 6px 0 0;
                color: #495057;
                font-size: 14px;
                font-weight: 500;
                border: none;
                padding: 0 16px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                bottom: -1px;
                margin: 0 1px;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background-color: #bbdefb;
                color: #1976D2;
                transform: translateY(-2px);
            }
            
            .stTabs [aria-selected="true"] {
                background-color: white !important;
                color: #1976D2 !important;
                font-weight: 600;
                border-top: 3px solid #1976D2 !important;
                box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
                z-index: 1;
            }

            .stTabs [data-baseweb="tab-panel"] {
                background-color: white;
                padding: 15px;
                border-radius: 0 0 8px 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                animation: fadeIn 0.3s ease-in-out;
                border: 1px solid #bbdefb;
                border-top: none;
            }

            /* Redução de espaços em todo o dashboard */
            .stApp {
                margin: 0 !important;
                padding: 0 !important;
            }

            .main .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }

            h1, h2, h3, h4, h5, h6 {
                margin-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }

            .element-container {
                margin-bottom: 0.5rem !important;
            }

            .stButton, .stDownloadButton {
                margin-bottom: 0.5rem !important;
            }

            p {
                margin-bottom: 0.5rem !important;
            }

            hr {
                margin: 0.5rem 0 !important;
            }

            .divisor-azul {
                margin: 0.5rem 0 !important;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-5px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Estilo para os cards de métricas de duplicação */
            .duplicados-header {
                background-color: #fef2f2;
                padding: 10px 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                border: 1px solid #fee2e2;
            }

            .duplicados-header h3 {
                color: #dc2626;
                font-size: 16px;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .duplicados-metrics {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 10px 0;
            }
            
            .duplicados-metric {
                background: linear-gradient(135deg, #fff5f5 0%, #fef2f2 100%);
                padding: 12px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #fecaca;
                box-shadow: 0 2px 4px rgba(220, 38, 38, 0.1);
                transition: transform 0.2s ease;
            }
            
            .duplicados-metric-label {
                color: #991b1b;
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 5px;
                text-transform: uppercase;
            }
            
            .duplicados-metric-value {
                color: #dc2626;
                font-size: 28px;
                font-weight: 700;
                text-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
                margin: 0;
                line-height: 1;
            }

            .duplicados-metric-value:after {
                content: "";
                display: block;
                width: 30px;
                height: 2px;
                background-color: #dc2626;
                margin: 6px auto 0;
                border-radius: 2px;
            }

            /* Ajuste para as tabelas */
            .stDataFrame {
                margin-top: 5px !important;
                margin-bottom: 5px !important;
            }

            /* Ajuste para os gráficos */
            .js-plotly-plot {
                margin-top: 5px !important;
                margin-bottom: 5px !important;
            }

            /* Redução de espaço nas colunas */
            [data-testid="column"] {
                padding: 0 3px !important;
            }
            </style>
        """, unsafe_allow_html=True)
            
        # Remove margin-top from footer
        st.markdown("""
        <style>
        footer {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def upload_csv_file():
        """Permite ao usuário fazer upload de um novo arquivo CSV"""
        uploaded_file = st.file_uploader(
            "Selecione o arquivo CSV:", 
            type=["csv"], 
            help="O arquivo deve estar no formato CSV com separador de ponto e vírgula (;)"
        )
        
        if uploaded_file is not None:
            try:
                # Salvar o arquivo enviado no lugar do arquivo existente
                with open("extratacao_bitrix24.csv", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Mostrar mensagem de sucesso
                st.success("✅ Arquivo carregado com sucesso! O dashboard será atualizado.")
                
                # Adicionar botão para recarregar a página
                if st.button("Atualizar Dashboard"):
                    st.rerun()
                
                return True
            except Exception as e:
                st.error(f"❌ Erro ao salvar o arquivo: {e}")
                return False
        
        return False

    @staticmethod
    def show_upload_instructions():
        """Exibe instruções detalhadas para o upload de arquivos CSV"""
        st.markdown("""
        <div style="background-color: #f0f7ff; padding: 20px; border-radius: 10px; border-left: 6px solid #1976D2; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #1976D2; margin-top: 0; margin-bottom: 15px; font-weight: 600;">📤 Instruções para Upload de Dados</h2>
            
            <p style="margin-bottom: 15px; font-size: 16px; line-height: 1.5;">Para manter seu dashboard atualizado com as informações mais recentes de negociações, siga as instruções abaixo:</p>
            
            <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #1976D2;">
                <h3 style="color: #1976D2; margin-top: 0; margin-bottom: 10px; font-size: 18px;">1️⃣ Preparação do Arquivo CSV</h3>
                <ul style="margin-top: 5px; margin-bottom: 10px; padding-left: 20px;">
                    <li style="margin-bottom: 8px;">O arquivo deve estar no formato CSV (valores separados por ponto e vírgula)</li>
                    <li style="margin-bottom: 8px;">O separador de colunas deve ser <strong>ponto e vírgula (;)</strong></li>
                    <li style="margin-bottom: 8px;">A codificação recomendada é <strong>UTF-8</strong></li>
                    <li style="margin-bottom: 8px;">Mantenha os nomes das colunas originais do seu sistema</li>
                    <li style="margin-bottom: 8px;">Datas devem estar no formato <strong>DD/MM/AAAA HH:MM:SS</strong></li>
                </ul>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #1976D2;">
                <h3 style="color: #1976D2; margin-top: 0; margin-bottom: 10px; font-size: 18px;">2️⃣ Colunas Essenciais</h3>
                <p style="margin-bottom: 10px;">Para que o dashboard funcione corretamente, o arquivo deve conter as seguintes colunas:</p>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                    <tr style="background-color: #e3f2fd;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #bbdefb;">Coluna</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #bbdefb;">Descrição</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #bbdefb;">Formato</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #bbdefb;"><strong>ID</strong></td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Identificador único do negócio</td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Texto/Número</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 8px; border: 1px solid #bbdefb;"><strong>Responsável</strong></td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Nome do responsável pelo negócio</td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Texto</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #bbdefb;"><strong>Fase</strong></td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Estágio atual do negócio no funil</td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Texto</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 8px; border: 1px solid #bbdefb;"><strong>Criado</strong></td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Data de criação do negócio</td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">DD/MM/AAAA HH:MM:SS</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #bbdefb;"><strong>Modificado</strong></td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Data da última modificação</td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">DD/MM/AAAA HH:MM:SS</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 8px; border: 1px solid #bbdefb;"><strong>LINK ARVORE DA FAMÍLIA PLATAFORMA</strong></td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">Link identificador da família</td>
                        <td style="padding: 8px; border: 1px solid #bbdefb;">URL</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #1976D2;">
                <h3 style="color: #1976D2; margin-top: 0; margin-bottom: 10px; font-size: 18px;">3️⃣ Procedimento de Upload</h3>
                <ol style="margin-top: 5px; margin-bottom: 10px; padding-left: 20px;">
                    <li style="margin-bottom: 8px;">Clique no botão <strong>"Procurar arquivos"</strong> abaixo</li>
                    <li style="margin-bottom: 8px;">Selecione o arquivo CSV em seu computador</li>
                    <li style="margin-bottom: 8px;">Aguarde a mensagem de confirmação <strong>"Arquivo carregado com sucesso"</strong></li>
                    <li style="margin-bottom: 8px;">Clique em <strong>"Atualizar Dashboard"</strong> para ver os dados atualizados</li>
                </ol>
            </div>
            
            <div style="background-color: #fff8e1; padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #FFA000;">
                <p style="margin: 0; color: #FF6F00; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 10px;">💡</span>
                    <span><strong>Dica:</strong> Para garantir a compatibilidade, baixe o modelo de arquivo CSV abaixo e use-o como base para preparar seus dados.</span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
        # Botão para baixar modelo de CSV
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 20px;">
            <h3 style="color: #1976D2; margin-top: 0; margin-bottom: 15px;">📋 Modelo de Arquivo CSV</h3>
            <p style="margin-bottom: 15px;">Baixe o modelo de arquivo CSV no formato correto para preenchimento. Este modelo contém exemplos de dados que facilitarão a preparação do seu arquivo.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Criar DataFrame de exemplo mais completo
        df_exemplo = pd.DataFrame({
            "ID": ["1", "2", "3", "4", "5"],
            "Responsável": ["João Silva", "Maria Oliveira", "Carlos Santos", "Ana Pereira", "Roberto Almeida"],
            "Fase": ["REUNIÃO AGENDADA", "EM NEGOCIAÇÃO", "ASSINADO", "VALIDADO ENVIAR FINANCEIRO", "FECHADO"],
            "Criado": ["01/01/2023 10:00:00", "02/01/2023 14:30:00", "03/01/2023 09:15:00", "04/01/2023 11:20:00", "05/01/2023 16:45:00"],
            "Modificado": ["10/01/2023 15:30:00", "12/01/2023 09:45:00", "15/01/2023 14:20:00", "18/01/2023 10:10:00", "20/01/2023 11:30:00"],
            "LINK ARVORE DA FAMÍLIA PLATAFORMA": ["https://plataforma.com/familia/123", "https://plataforma.com/familia/456", "https://plataforma.com/familia/789", "https://plataforma.com/familia/101", "https://plataforma.com/familia/112"],
            "Nome": ["Negócio A", "Negócio B", "Negócio C", "Negócio D", "Negócio E"],
            "Status": ["Em andamento", "Em andamento", "Finalizado", "Finalizado", "Finalizado"],
            "REUNIÃO": ["05/01/2023 14:00:00", "07/01/2023 10:30:00", "08/01/2023 09:00:00", "", ""],
            "FECHADO": ["", "", "15/01/2023 16:45:00", "19/01/2023 14:30:00", "22/01/2023 10:15:00"]
        })
        
        # Gerar CSV e link para download
        csv = df_exemplo.to_csv(index=False, sep=';', encoding='utf-8-sig')
        b64 = base64.b64encode(csv.encode()).decode()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="📥 Baixar Modelo CSV",
                data=csv,
                file_name="modelo_bitrix24.csv",
                mime="text/csv",
                help="Clique para baixar um arquivo CSV de exemplo no formato correto",
                use_container_width=True,
            )
        
        # Formulário de upload
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-top: 20px; margin-bottom: 20px;">
            <h3 style="color: #1976D2; margin-top: 0; margin-bottom: 15px;">📤 Upload de Arquivo</h3>
            <p style="margin-bottom: 15px;">Selecione o arquivo CSV com os dados atualizados para carregar no dashboard:</p>
        </div>
        """, unsafe_allow_html=True)
        
        return ResponsavelDashboard.upload_csv_file()

    @staticmethod
    def load_data():
        """Carrega e processa os dados do CSV"""
        try:
            # Tentar diferentes caminhos de arquivo
            file_paths = ["extratacao_bitrix24.csv", "data/extracao_bitrix24.csv"]
            df = None
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    # Tentar diferentes codificações
                    encodings = ["utf-8", "latin1", "ISO-8859-1", "cp1252"]
                    for encoding in encodings:
                        try:
                            # Tentar ler o arquivo com diferentes separadores e encodings
                            df = pd.read_csv(file_path, sep=";", encoding=encoding)
                            break
                        except Exception as e:
                            continue
                    
                    if df is not None:
                        break
            
            if df is None:
                st.error("Não foi possível ler o arquivo CSV com nenhuma combinação de caminho e encoding.")
                return pd.DataFrame()
            
            # Limpar os nomes das colunas
            df.columns = [col.strip().replace('"', '') for col in df.columns]
            
            # Remover caracteres BOM (Byte Order Mark) do início das colunas
            if df.columns[0].startswith('\ufeff'):
                df.columns = [df.columns[0][1:]] + list(df.columns[1:])
            
            # Criar um mapeamento de nomes de colunas para padronizar
            column_mapping = {}
            
            # Detectar coluna ID
            id_column = None
            for col in df.columns:
                if 'ID' in col.upper():
                    id_column = col
                    column_mapping[col] = 'ID'
                    break
            
            # Detectar coluna de link da família
            link_column = None
            for col in df.columns:
                if 'LINK' in col.upper() and ('FAMILIA' in col.upper() or 'FAMÍLIA' in col.upper()):
                    link_column = col
                    column_mapping[col] = 'LINK ARVORE DA FAMÍLIA PLATAFORMA'
                    break
            
            # Detectar coluna de responsável
            resp_column = None
            for col in df.columns:
                if 'RESPONS' in col.upper():
                    resp_column = col
                    column_mapping[col] = 'Responsável'
                    break
            
            # Detectar coluna de fase
            fase_column = None
            for col in df.columns:
                if 'FASE' in col.upper():
                    fase_column = col
                    column_mapping[col] = 'Fase'
                    break
            
            # Detectar coluna de data de criação
            criado_column = None
            for col in df.columns:
                if 'CRIADO' in col.upper() or 'CRIAÇ' in col.upper() or 'DATA' in col.upper():
                    criado_column = col
                    column_mapping[col] = 'Criado'
                    break
            
            # Detectar coluna de reunião
            reuniao_column = None
            for col in df.columns:
                if 'REUNI' in col.upper():
                    reuniao_column = col
                    column_mapping[col] = 'REUNIÃO'
                    break
            
            # Detectar coluna de fechamento
            fechado_column = None
            for col in df.columns:
                if 'FECH' in col.upper():
                    fechado_column = col
                    column_mapping[col] = 'FECHADO'
                    break
            
            # Renomear colunas
            df = df.rename(columns=column_mapping)
            
            # Remover colunas vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Converter data de criação para datetime
            try:
                if 'Criado' in df.columns:
                    df['Criado'] = pd.to_datetime(df['Criado'], dayfirst=True, errors='coerce')
                else:
                    st.warning("Coluna 'Criado' não encontrada no arquivo CSV.")
            except Exception as e:
                st.warning(f"Erro ao converter coluna 'Criado' para datetime: {str(e)}")
            
            # Converter data de fechamento para datetime (se existir)
            try:
                if 'FECHADO' in df.columns:
                    df['FECHADO'] = pd.to_datetime(df['FECHADO'], dayfirst=True, errors='coerce')
            except Exception as e:
                st.warning(f"Erro ao converter coluna 'FECHADO' para datetime: {str(e)}")
            
            # Retirar espaços extras das strings
            for col in ['Responsável', 'Fase']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                else:
                    st.warning(f"Coluna '{col}' não encontrada no arquivo CSV.")
            
            return df
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro
    
    @staticmethod
    def calc_cards_sem_modificacao(df):
        """Calcula o número de cards que não tiveram modificação nos últimos 3 dias"""
        try:
            # Verificar se a coluna Modificado existe
            if "Modificado" not in df.columns:
                return "N/A"
            
            # Converter coluna Modificado para datetime se ainda não for
            df['Modificado'] = pd.to_datetime(df['Modificado'], dayfirst=True, errors='coerce')
            
            # Calcular a diferença entre a data atual e a data de modificação
            hoje = pd.Timestamp.now()
            df['Dias_Sem_Modificacao'] = (hoje - df['Modificado']).dt.days
            
            # Contar cards sem modificação nos últimos 3 dias
            cards_sem_modificacao = df[df['Dias_Sem_Modificacao'] > 3].shape[0]
            
            return cards_sem_modificacao
        except Exception as e:
            st.warning(f"Erro ao calcular cards sem modificação: {str(e)}")
            return "N/A"
    
    @staticmethod
    def show_cards_sem_modificacao(df):
        """Exibe análise detalhada dos cards sem modificação"""
        try:
            # Adicionar estilo de alerta com fundo amarelo para toda a seção
            st.markdown("""
            <style>
            .cards-sem-modificacao-container {
                background-color: #fff9c4;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #fbc02d;
                margin-bottom: 20px;
            }
            .alerta-titulo {
                color: #f57f17;
                font-weight: bold;
            }
            .alerta-metrica {
                background-color: #ffecb3;
                border-left: 4px solid #ffa000;
                border-radius: 5px;
                padding: 10px 15px;
                margin-bottom: 10px;
            }
            .alerta-metrica-grave {
                background-color: #ffccbc;
                border-left: 4px solid #e64a19;
                border-radius: 5px;
                padding: 10px 15px;
                margin-bottom: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.subheader("Análise de Cards sem Modificação")
            
            # Adicionar linha divisória amarela
            st.markdown('<hr style="border-color: #fbc02d; margin: 10px 0;" />', unsafe_allow_html=True)
            
            # Verificar se a coluna Modificado existe
            if "Modificado" not in df.columns:
                st.warning("Coluna 'Modificado' não encontrada no arquivo CSV. Não é possível gerar análise de cards sem modificação.")
                st.markdown('</div>', unsafe_allow_html=True)  # Fechar div container
                return
            
            # Converter coluna Modificado para datetime se ainda não for
            df['Modificado'] = pd.to_datetime(df['Modificado'], dayfirst=True, errors='coerce')
            
            # Calcular a diferença entre a data atual e a data de modificação
            hoje = pd.Timestamp.now()
            df['Dias_Sem_Modificacao'] = (hoje - df['Modificado']).dt.days
            
            # Filtrar cards sem modificação entre 3 e 32 dias
            df_sem_modificacao = df[(df['Dias_Sem_Modificacao'] >= 3) & (df['Dias_Sem_Modificacao'] <= 32)].copy()
            
            # Verificar se há cards sem modificação
            if len(df_sem_modificacao) == 0:
                st.info("Não foram encontrados cards sem modificação entre 3 e 32 dias.")
                st.markdown('</div>', unsafe_allow_html=True)  # Fechar div container
                return
            
            # Exibir total de cards sem modificação
            st.markdown(f"""
                <div style="background-color: #ffeeba; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #ffc107;">
                    <h4 style="margin: 0; color: #856404;" class="alerta-titulo">ALERTA: Total de cards sem modificação (3-32 dias): {len(df_sem_modificacao)}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # Criar métricas para diferentes períodos
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cards_3_dias = df[df['Dias_Sem_Modificacao'] == 3].shape[0]
                st.markdown(f"""
                    <div class="alerta-metrica">
                        <h5 style="margin: 0;">Cards parados 3 dias</h5>
                        <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #856404;">{cards_3_dias}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                cards_5_dias = df[(df['Dias_Sem_Modificacao'] >= 4) & (df['Dias_Sem_Modificacao'] <= 5)].shape[0]
                st.markdown(f"""
                    <div class="alerta-metrica">
                        <h5 style="margin: 0;">Cards parados 4-5 dias</h5>
                        <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #856404;">{cards_5_dias}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                cards_7_dias = df[(df['Dias_Sem_Modificacao'] >= 6) & (df['Dias_Sem_Modificacao'] <= 7)].shape[0]
                st.markdown(f"""
                    <div class="alerta-metrica">
                        <h5 style="margin: 0;">Cards parados 6-7 dias</h5>
                        <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #856404;">{cards_7_dias}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                cards_14_dias = df[(df['Dias_Sem_Modificacao'] >= 8) & (df['Dias_Sem_Modificacao'] <= 14)].shape[0]
                st.markdown(f"""
                    <div class="alerta-metrica-grave">
                        <h5 style="margin: 0;">Cards parados 8-14 dias</h5>
                        <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #bf360c;">{cards_14_dias}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                cards_30_dias = df[(df['Dias_Sem_Modificacao'] >= 15) & (df['Dias_Sem_Modificacao'] <= 30)].shape[0]
                st.markdown(f"""
                    <div class="alerta-metrica-grave">
                        <h5 style="margin: 0;">Cards parados 15-30 dias</h5>
                        <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #bf360c;">{cards_30_dias}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Análise por responsável
            st.subheader("Cards sem modificação por responsável")
            
            if "Responsável" in df_sem_modificacao.columns:
                # Agrupar por responsável e contar cards
                resp_count = df_sem_modificacao.groupby("Responsável").size().reset_index(name="Quantidade")
                resp_count = resp_count.sort_values("Quantidade", ascending=False)
                
                # Criar gráfico de barras
                fig = px.bar(
                    resp_count,
                    x="Responsável",
                    y="Quantidade",
                    title="Cards sem modificação por responsável",
                    color="Quantidade",
                    color_continuous_scale="YlOrRd",  # Escala de cores amarelo para vermelho
                    text="Quantidade"
                )
                
                fig.update_layout(
                    xaxis_title="Responsável",
                    yaxis_title="Quantidade de cards",
                    height=500,
                    margin=dict(l=40, r=40, t=50, b=40),
                    plot_bgcolor='rgba(255, 249, 196, 0.3)'  # Fundo levemente amarelado
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Coluna 'Responsável' não encontrada.")
            
            # Análise por dias sem modificação
            st.subheader("Distribuição por dias sem modificação")
            
            # Criar gráfico de histograma com métricas
            fig = px.histogram(
                df_sem_modificacao,
                x="Dias_Sem_Modificacao",
                nbins=30,
                title="Distribuição de cards por dias sem modificação",
                color_discrete_sequence=["#FF9800"],  # Cor laranja para alerta
                histnorm='',  # Mostrar contagens absolutas
            )
            
            # Adicionar linhas verticais para os marcos importantes
            fig.add_vline(x=3, line_width=2, line_dash="dash", line_color="#FBC02D", annotation_text="3 dias")
            fig.add_vline(x=5, line_width=2, line_dash="dash", line_color="#FFA000", annotation_text="5 dias")
            fig.add_vline(x=7, line_width=2, line_dash="dash", line_color="#F57C00", annotation_text="7 dias")
            fig.add_vline(x=14, line_width=2, line_dash="dash", line_color="#E65100", annotation_text="14 dias")
            fig.add_vline(x=30, line_width=2, line_dash="dash", line_color="#BF360C", annotation_text="30 dias")
            
            fig.update_layout(
                xaxis_title="Dias sem modificação",
                yaxis_title="Quantidade de cards",
                height=500,
                margin=dict(l=40, r=40, t=50, b=40),
                plot_bgcolor='rgba(255, 248, 196, 0.3)'  # Fundo levemente amarelado
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada com os cards sem modificação
            st.subheader("Lista detalhada de cards sem modificação")
            
            # Seleção de colunas relevantes para exibição
            colunas_exibir = ["Responsável", "Nome", "Dias_Sem_Modificacao", "Modificado"]
            colunas_disponiveis = [col for col in colunas_exibir if col in df_sem_modificacao.columns]
            
            # Adicionar mais colunas relevantes que possam existir
            colunas_adicionais = []
            for col in ["Fase", "Status", "Título", "ID"]:
                if col in df_sem_modificacao.columns and col not in colunas_disponiveis:
                    colunas_adicionais.append(col)
            
            colunas_exibir = colunas_disponiveis + colunas_adicionais
            
            # Verificar se há colunas para exibir
            if colunas_exibir:
                # Ordenar por dias sem modificação (decrescente)
                df_exibir = df_sem_modificacao[colunas_exibir].sort_values("Dias_Sem_Modificacao", ascending=False)
                
                # Formatar a coluna de data para melhor visualização
                if "Modificado" in df_exibir.columns:
                    df_exibir["Modificado"] = df_exibir["Modificado"].dt.strftime("%d/%m/%Y")
                
                st.dataframe(
                    df_exibir,
                    use_container_width=True,
                    height=400
                )
                
                # Opção para download dos dados
                csv = df_exibir.to_csv(index=False)
                st.download_button(
                    label="Baixar dados em CSV",
                    data=csv,
                    file_name="cards_sem_modificacao.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Não há colunas válidas para exibir na tabela detalhada.")
                
            # Fechar a div do container
            st.markdown('</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Erro ao exibir análise de cards sem modificação: {str(e)}")
            st.write("Detalhes do erro:", e)
            # Fechar a div do container em caso de erro
            st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def calc_metricas_assinatura_fechamento(df):
        """Calcula métricas relacionadas a assinaturas e fechamentos"""
        try:
            # Verificar se as colunas necessárias existem
            if "Fase" not in df.columns:
                return {"total_assinados": 0, "total_env_novo_adm": 0, "total_fechados": 0, "percentual_fechados": "0%"}
            
            # Contar total de assinados
            total_assinados = df[df["Fase"] == "ASSINADO"].shape[0]
            
            # Contar total de fase finais (ENV. NOVO ADM e suas variações)
            total_env_novo_adm = df[df["Fase"].isin(["ENV. NOVO ADM", "ENV.. NOVO ADM", "VALIDADO ENVIAR FINANCEIRO"])].shape[0]
            
            # Contar total de registros com data de fechamento preenchida
            if "FECHADO" in df.columns:
                # Filtrar apenas registros com data de fechamento válida (não vazia e não nula)
                df_fechados_data = df[df["FECHADO"].notna() & (df["FECHADO"] != '') & (df["FECHADO"] != 'nan') & (df["FECHADO"] != 'None')]
                
                # Considerar também negócios na fase "VALIDADO ENVIAR FINANCEIRO" como fechados
                df_validado_financeiro = df[df["Fase"] == "VALIDADO ENVIAR FINANCEIRO"]
                
                # União dos dois conjuntos (evitando duplicidades)
                ids_fechados = set(df_fechados_data.index).union(set(df_validado_financeiro.index))
                total_fechados = len(ids_fechados)
                
                # Calcular percentual de fechados em relação ao total de assinados + env_novo_adm
                total_finalizados = total_assinados + total_env_novo_adm
                
                # Calcular percentual apenas se houver negócios finalizados
                if total_finalizados > 0:
                    percentual_fechados = (total_fechados / total_finalizados) * 100
                    percentual_fechados_str = f"{percentual_fechados:.1f}%"
                else:
                    percentual_fechados_str = "0%"
                
                # Calcular percentual de negócios com data de fechamento em relação ao total geral
                total_geral = len(df)
                if total_geral > 0:
                    percentual_fechados_total = (total_fechados / total_geral) * 100
                else:
                    percentual_fechados_total = 0
            else:
                # Mesmo sem coluna FECHADO, considerar negócios na fase "VALIDADO ENVIAR FINANCEIRO" como fechados
                df_validado_financeiro = df[df["Fase"] == "VALIDADO ENVIAR FINANCEIRO"]
                total_fechados = len(df_validado_financeiro)
                
                # Calcular percentual em relação ao total
                total_geral = len(df)
                if total_geral > 0:
                    percentual_fechados_total = (total_fechados / total_geral) * 100
                else:
                    percentual_fechados_total = 0
                
                # Calcular percentual em relação aos finalizados
                total_finalizados = total_assinados + total_env_novo_adm
                if total_finalizados > 0:
                    percentual_fechados = (total_fechados / total_finalizados) * 100
                    percentual_fechados_str = f"{percentual_fechados:.1f}%"
                else:
                    percentual_fechados_str = "0%"
            
            return {
                "total_assinados": total_assinados,
                "total_env_novo_adm": total_env_novo_adm,
                "total_fechados": total_fechados,
                "percentual_fechados": percentual_fechados_str,
                "percentual_fechados_total": f"{percentual_fechados_total:.1f}%"
            }
        except Exception as e:
            st.warning(f"Erro ao calcular métricas de assinatura e fechamento: {str(e)}")
            return {
                "total_assinados": 0, 
                "total_env_novo_adm": 0, 
                "total_fechados": 0, 
                "percentual_fechados": "0%",
                "percentual_fechados_total": "0%"
            }
    
    @staticmethod
    def show_main_metrics(df):
        """Exibe métricas principais"""
        try:
            # Calcular métricas principais
            total_negocios = len(df)
            
            # Verificar se a coluna existe antes de usá-la
            if "LINK ARVORE DA FAMÍLIA PLATAFORMA" in df.columns:
                coluna_link = "LINK ARVORE DA FAMÍLIA PLATAFORMA"
            else:
                # Procurar colunas que possam conter o link da família
                possiveis_colunas = [col for col in df.columns if "LINK" in col or "FAMILIA" in col or "FAMÍLIA" in col]
                if possiveis_colunas:
                    coluna_link = possiveis_colunas[0]
                    st.info(f"Usando coluna '{coluna_link}' para análise de famílias.")
                else:
                    # Se não encontrar nenhuma coluna similar, usar uma coluna vazia
                    st.warning("Não foi encontrada coluna para análise de famílias. Usando valores padrão.")
                    df["Coluna_Link_Temporaria"] = "N/A"
                    coluna_link = "Coluna_Link_Temporaria"
            
            # Calcular métricas com a coluna correta
            # Famílias únicas (ignorando valores vazios ou 'nan')
            df_links_validos = df[df[coluna_link].notna() & (df[coluna_link] != '') & (df[coluna_link] != 'nan') & (df[coluna_link] != 'None')]
            total_familias = df_links_validos[coluna_link].nunique()
            
            # Total de responsáveis únicos
            if "Responsável" in df.columns:
                df_resp_validos = df[df["Responsável"].notna() & (df["Responsável"] != '') & (df["Responsável"] != 'nan') & (df["Responsável"] != 'None')]
                total_responsaveis = df_resp_validos["Responsável"].nunique()
            else:
                total_responsaveis = 0
                st.warning("Coluna 'Responsável' não encontrada.")
            
            # Calcular cards sem modificação nos últimos 3 dias
            cards_sem_modificacao = ResponsavelDashboard.calc_cards_sem_modificacao(df)
            
            # Calcular métricas de assinatura e fechamento
            metricas_assinatura = ResponsavelDashboard.calc_metricas_assinatura_fechamento(df)
            
            # Layout com 4 métricas em uma única linha (removendo as métricas que serão unificadas)
            col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card' style="margin: 0; padding: 1rem; background-color: white; border-left: 4px solid #1976D2; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
                        <div class='metric-label' style="margin-bottom: 0.3rem; font-size: 0.8rem; color: #1976D2;">Total de Famílias</div>
                        <div class='metric-value' style="margin: 0.1rem 0; font-size: 2rem; color: #1976D2;">{formatar_numero(total_familias)}</div>
                    </div>
            """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class='metric-card' style="margin: 0; padding: 0.8rem; background-color: white; border-left: 4px solid #1976D2; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
                        <div class='metric-label' style="margin-bottom: 0.2rem; font-size: 0.7rem; color: #1976D2;">Total de Responsáveis</div>
                        <div class='metric-value' style="margin: 0.1rem 0; font-size: 1.4rem; color: #1976D2;">{formatar_numero(total_responsaveis)}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class='metric-card' style="margin: 0; padding: 0.8rem; background-color: white; border-left: 4px solid #1976D2; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
                        <div class='metric-label' style="margin-bottom: 0.2rem; font-size: 0.7rem; color: #1976D2;">Sem Modificação (3+ dias)</div>
                        <div class='metric-value' style="margin: 0.1rem 0; font-size: 1.4rem; color: #1976D2;">{formatar_numero(cards_sem_modificacao)}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class='metric-card' style="margin: 0; padding: 1rem; background-color: white; border-left: 4px solid #2E7D32; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
                        <div style="display: flex; flex-direction: column;">
                            <div class='metric-label' style="margin-bottom: 0.3rem; font-size: 0.8rem; color: #2E7D32;">Negócios Fechados</div>
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <div style="flex: 2;">
                                    <div style="font-size: 2rem; color: #2E7D32; font-weight: 600;">{formatar_numero(metricas_assinatura["total_fechados"])}</div>
                                </div>
                                <div style="flex: 1; text-align: right; border-left: 1px solid #E8F5E9; padding-left: 1rem;">
                                    <div style="font-size: 0.75rem; color: #2E7D32; margin-bottom: 0.2rem;">% do Total</div>
                                    <div style="font-size: 1.2rem; color: #2E7D32; font-weight: 500;">{metricas_assinatura["percentual_fechados_total"]}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            # Adicionar linha divisória após as métricas com margem reduzida
            
        except Exception as e:
            st.error(f"Erro ao exibir métricas: {str(e)}")
            st.write("Detalhes do erro:", e)
    
    @staticmethod
    def calc_tempo_medio_fechamento(df):
        """Calcula o tempo médio até o fechamento em dias"""
        # Considerar negócios com data de fechamento
        df_fechados_data = df[df["FECHADO"].notna()].copy()
        
        # Considerar também negócios na fase "VALIDADO ENVIAR FINANCEIRO"
        df_validado_financeiro = df[df["Fase"] == "VALIDADO ENVIAR FINANCEIRO"].copy()
        
        # Combinar os dois conjuntos (evitando duplicidades)
        df_fechados = pd.concat([df_fechados_data, df_validado_financeiro]).drop_duplicates()
        
        if len(df_fechados) == 0:
            return "N/A"
        
        # Para negócios sem data de fechamento mas com fase "VALIDADO ENVIAR FINANCEIRO", usar a data de modificação
        for idx in df_fechados.index:
            if pd.isna(df_fechados.loc[idx, "FECHADO"]) and df_fechados.loc[idx, "Fase"] == "VALIDADO ENVIAR FINANCEIRO":
                if "Modificado" in df_fechados.columns:
                    df_fechados.loc[idx, "FECHADO"] = df_fechados.loc[idx, "Modificado"]
        
        df_fechados["Tempo_Fechamento"] = (df_fechados["FECHADO"] - df_fechados["Criado"]).dt.days
        tempo_medio = df_fechados["Tempo_Fechamento"].mean()
        
        if np.isnan(tempo_medio):
            return "N/A"
        
        return f"{formatar_numero(tempo_medio)} dias"
    
    @staticmethod
    def show_funil_chart(df):
        """Exibe gráfico de funil por fase"""
        try:
            # Verificar se a coluna Fase existe
            if "Fase" not in df.columns:
                st.warning("Coluna 'Fase' não encontrada no CSV. Não é possível gerar o gráfico de funil.")
                return
              
            # Adicionar título explícito usando st.subheader
            st.subheader("Distribuição de Negócios por Fase")
            
            # Obter contagem por fase e reorganizar conforme a ordem definida
            fase_counts = df["Fase"].value_counts().reset_index()
            fase_counts.columns = ["Fase", "Quantidade"]
            
            # Criar DataFrame completo com todas as fases, preenchendo com zeros onde necessário
            all_fases = pd.DataFrame({"Fase": FASES_ORDEM})
            fase_counts = pd.merge(all_fases, fase_counts, on="Fase", how="left").fillna(0)
            
            # Ordenar conforme a ordem definida
            fase_counts["Fase_Order"] = fase_counts["Fase"].apply(lambda x: FASES_ORDEM.index(x) if x in FASES_ORDEM else 999)
            fase_counts = fase_counts.sort_values("Fase_Order").drop("Fase_Order", axis=1)
            
            # Converter para inteiro
            fase_counts["Quantidade"] = fase_counts["Quantidade"].astype(int)
            
            # Criar gráfico de funil
            fig = go.Figure(go.Funnel(
                y=fase_counts["Fase"],
                x=fase_counts["Quantidade"],
                textposition="inside",
                textinfo="value+percent initial",
                marker={"color": [FASE_COLORS.get(fase, "#333333") for fase in fase_counts["Fase"]]},
                connector={"line": {"color": "royalblue", "width": 1}}
            ))
            
            fig.update_layout(
                title=None,  # Removido título interno do Plotly
                margin=dict(t=15, l=60, r=10, b=10),  # Reduzido ainda mais as margens
                height=350,  # Reduzido de 400                          
                font=dict(size=12, color="#212121")   # Adicionado cor explícita para o texto
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico de funil: {str(e)}")
            st.write("Detalhes do erro:", e)
    
    @staticmethod
    def show_responsavel_chart(df):
        """Exibe apenas o funil de vendas por responsável"""
        try:
            # Verificar se a coluna Responsável existe
            if "Responsável" not in df.columns:
                st.warning("Coluna 'Responsável' não encontrada no arquivo CSV.")
                return
            
            # Definir as cores para um tema mais clean
            cores_tema = {
                "azul_claro": "#E1F5FE",  # Azul muito claro
                "azul_medio": "#4FC3F7",  # Azul médio
                "azul_escuro": "#0288D1", # Azul escuro
                "cinza_claro": "#F5F5F5", # Cinza bem claro
                "cinza_medio": "#9E9E9E", # Cinza médio
                "texto": "#37474F"        # Cinza escuro para texto
            }
            
            # Custom CSS para esta seção
            st.markdown(f"""
            <style>
            .responsavel-card {{
                background-color: {cores_tema["azul_claro"]};
                border-radius: 10px;
                padding: 12px; /* Reduzido de 15px */
                margin-bottom: 12px; /* Reduzido de 15px */
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                border-bottom: 2px solid var(--cor-azul-medio);
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Criar seletor de responsável - sem usar tabs
            responsaveis = sorted(df["Responsável"].unique())
            selected_resp = st.selectbox("Selecione um responsável para análise detalhada:", responsaveis)
            
            # Filtrar dados para o responsável selecionado
            df_resp = df[df["Responsável"] == selected_resp].copy()
            
            # Calcular KPIs
            total_negocios_resp = len(df_resp)
            
            # Famílias únicas
            total_familias_resp = 0
            if "LINK ARVORE DA FAMÍLIA PLATAFORMA" in df.columns:
                df_links_validos = df_resp[df_resp["LINK ARVORE DA FAMÍLIA PLATAFORMA"].notna() & 
                                    (df_resp["LINK ARVORE DA FAMÍLIA PLATAFORMA"] != '') & 
                                    (df_resp["LINK ARVORE DA FAMÍLIA PLATAFORMA"] != 'nan') & 
                                    (df_resp["LINK ARVORE DA FAMÍLIA PLATAFORMA"] != 'None')]
                total_familias_resp = df_links_validos["LINK ARVORE DA FAMÍLIA PLATAFORMA"].nunique()
            
            # Calcular percentual da carga 
            percentual_carga = (total_negocios_resp / len(df)) * 100
            
            # Exibir KPIs em cartões - somente com o nome do responsável
            st.markdown(f"""
            <div class="responsavel-card" style="padding: 10px; background-color: white; border: 1px solid #E0E0E0;">
                <h3 style="color: {cores_tema['azul_escuro']}; margin-top: 0; margin-bottom: 3px; font-size: 18px; font-weight: 600;">{selected_resp}</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1; min-width: 160px; background-color: {cores_tema['azul_claro']}; padding: 8px; border-radius: 8px;">
                        <h4 style="margin-top: 0; margin-bottom: 3px; font-size: 14px; color: {cores_tema['texto']};">Total de Negócios</h4>
                        <p style="font-size: 20px; font-weight: bold; margin: 0; color: {cores_tema['azul_escuro']};">{formatar_numero(total_negocios_resp)}</p>
                        <p style="margin: 0; font-size: 12px; color: {cores_tema['texto']};">({formatar_numero(percentual_carga)}% do total)</p>
                    </div>
                    <div style="flex: 1; min-width: 160px; background-color: {cores_tema['azul_claro']}; padding: 8px; border-radius: 8px;">
                        <h4 style="margin-top: 0; margin-bottom: 3px; font-size: 14px; color: {cores_tema['texto']};">Famílias Únicas</h4>
                        <p style="font-size: 20px; font-weight: bold; margin: 0; color: {cores_tema['azul_escuro']};">{formatar_numero(total_familias_resp)}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Distribuição por fase para este responsável
            if "Fase" in df.columns:
                # Contagem por fase
                fase_counts = df_resp["Fase"].value_counts().reset_index()
                fase_counts.columns = ["Fase", "Quantidade"]
                
                # Criar DataFrame completo com todas as fases do FASES_ORDEM
                all_fases = pd.DataFrame({"Fase": FASES_ORDEM})
                fase_counts = pd.merge(all_fases, fase_counts, on="Fase", how="left").fillna(0)
                
                # Ordenar conforme a ordem definida
                fase_counts["Fase_Order"] = fase_counts["Fase"].apply(lambda x: FASES_ORDEM.index(x) if x in FASES_ORDEM else 999)
                fase_counts = fase_counts.sort_values("Fase_Order").drop("Fase_Order", axis=1)
                
                # Converter para inteiro
                fase_counts["Quantidade"] = fase_counts["Quantidade"].astype(int)
                
                # Calcular percentual
                if total_negocios_resp > 0:
                    fase_counts["Percentual"] = (fase_counts["Quantidade"] / total_negocios_resp * 100).round(1)
                else:
                    fase_counts["Percentual"] = 0
                
                # Criar funil com cores específicas
                st.subheader(f"Funil de Vendas: {selected_resp}")
                
                fig_funnel = go.Figure(go.Funnel(
                    y=fase_counts["Fase"],
                    x=fase_counts["Quantidade"],
                    textposition="inside",
                    textinfo="value+percent initial",
                    marker={"color": [FASE_COLORS.get(fase, "#333333") for fase in fase_counts["Fase"]]},
                    connector={"line": {"color": cores_tema["cinza_medio"], "width": 1}}
                ))
                
                fig_funnel.update_layout(
                    title=None,  # Removido título interno do Plotly
                    height=380,  # Reduzido de 450
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(color=cores_tema["texto"], size=12),
                    margin=dict(t=15, l=80, r=10, b=10)  # Reduzido t de 20 para 15
                )
                
                st.plotly_chart(fig_funnel, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao exibir gráficos de análise por responsável: {str(e)}")
            st.write("Detalhes do erro:", e)
            
    @staticmethod
    def show_duplicated_links(df):
        """Identifica e exibe Famílias duplicados de famílias para correção no Bitrix24"""
        try:
            st.subheader("Famílias Duplicados")
            
            # Adicionar linha divisória azul antes da seção
            st.markdown('<hr class="divisor-azul" />', unsafe_allow_html=True)
            
            # Verificar se a coluna existe
            if "LINK ARVORE DA FAMÍLIA PLATAFORMA" not in df.columns:
                st.warning("Coluna 'LINK ARVORE DA FAMÍLIA PLATAFORMA' não encontrada no arquivo CSV.")
                return
            
            # Filtrar apenas registros com links válidos
            df_links_validos = df[df["LINK ARVORE DA FAMÍLIA PLATAFORMA"].notna() & 
                                (df["LINK ARVORE DA FAMÍLIA PLATAFORMA"] != '') & 
                                (df["LINK ARVORE DA FAMÍLIA PLATAFORMA"] != 'nan') & 
                                (df["LINK ARVORE DA FAMÍLIA PLATAFORMA"] != 'None')]
            
            # Identificar links duplicados
            links_counts = df_links_validos["LINK ARVORE DA FAMÍLIA PLATAFORMA"].value_counts()
            links_duplicados = links_counts[links_counts > 1]
            links_unicos = links_counts[links_counts == 1]
            
            # Calcular métricas corretas
            total_links_unicos = len(links_unicos)
            total_links_duplicados = len(links_duplicados)
            total_registros_afetados = sum(links_duplicados.values)
            
            # Melhorar o CSS para as métricas
            st.markdown("""
            <style>
            .duplicados-metric-label {
                font-size: 14px;
                font-weight: 600;
                color: #b91c1c;
                margin-bottom: 5px;
            }
            
            .duplicados-metric-description {
                font-size: 12px;
                color: #64748b;
                margin-bottom: 5px;
                line-height: 1.2;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Exibir métricas com títulos e descrições mais claros
            st.markdown("""
            <div class="duplicados-header">
                <h3>⚠️ Análise de Famílias Duplicadas</h3>
            </div>
            <div class="duplicados-metrics">
                <div class="duplicados-metric">
                    <div class="duplicados-metric-label">Famílias Únicas</div>
                    <div class="duplicados-metric-description">
                        Quantidade de famílias que aparecem apenas uma vez no sistema (sem duplicação)
                    </div>
                    <div class="duplicados-metric-value">{}</div>
                </div>
                <div class="duplicados-metric">
                    <div class="duplicados-metric-label">Famílias Duplicadas</div>
                    <div class="duplicados-metric-description">
                        Quantidade de famílias que aparecem mais de uma vez (links duplicados)
                    </div>
                    <div class="duplicados-metric-value">{}</div>
                </div>
                <div class="duplicados-metric">
                    <div class="duplicados-metric-label">Total de Registros Duplicados</div>
                    <div class="duplicados-metric-description">
                        Número total de registros afetados por duplicação de famílias
                    </div>
                    <div class="duplicados-metric-value">{}</div>
                </div>
            </div>
            """.format(
                total_links_unicos,
                total_links_duplicados,
                total_registros_afetados
            ), unsafe_allow_html=True)
            
            if len(links_duplicados) == 0:
                st.success("Não foram encontrados Famílias duplicados! Todos os registros estão corretos.")
                return
            
            # Criar tabela completa com todos os registros que têm links duplicados
            df_duplicados = pd.DataFrame()
            
            for link, count in links_duplicados.items():
                # Obter todos os registros com este link
                registros_link = df_links_validos[df_links_validos["LINK ARVORE DA FAMÍLIA PLATAFORMA"] == link].copy()
                
                # Adicionar uma coluna indicando o total de duplicações
                registros_link["Total Duplicados"] = count
                
                # Adicionar ao DataFrame final
                df_duplicados = pd.concat([df_duplicados, registros_link])
            
            # Selecionar colunas para exibição na tabela
            colunas_exibicao = ["ID", "Responsável", "Fase", "LINK ARVORE DA FAMÍLIA PLATAFORMA", "Total Duplicados"]
            colunas_exibicao = [col for col in colunas_exibicao if col in df_duplicados.columns]
            
            if "Criado" in df_duplicados.columns:
                colunas_exibicao.insert(3, "Criado")
            
            # Formatar datas antes de exibir
            df_display = df_duplicados[colunas_exibicao].copy()
            if "Criado" in df_display.columns:
                if pd.api.types.is_datetime64_any_dtype(df_display["Criado"]):
                    df_display["Criado"] = df_display["Criado"].dt.strftime('%d/%m/%Y %H:%M')
            
            # Botões de download
            st.markdown("#### Exportar Dados para Correção")
            col1, col2 = st.columns(2)
            
            with col1:
                # Link para download CSV
                csv = df_display.to_csv(index=False, sep=';', encoding='utf-8-sig')
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="links_duplicados.csv" class="download-btn">Exportar CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                excel_link = get_excel_download_link(df_display, filename="links_duplicados.xlsx", text="Exportar Excel")
                st.markdown(excel_link, unsafe_allow_html=True)
            
            # Exibir a tabela
            st.markdown("#### Tabela de Links Duplicados")
            st.markdown("""<p style="color: #424242; font-size: 13px; margin-bottom: 10px;">
                Esta tabela mostra todos os registros com links duplicados. Exporte estes dados e faça as correções necessárias no Bitrix24.
            </p>""", unsafe_allow_html=True)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"Erro ao analisar links duplicados: {str(e)}")
    
    @staticmethod
    def show_detailed_table(df):
        """Exibe uma tabela detalhada com filtros e opções de download"""
        try:
            st.markdown("### Filtros")
            
            # Adicionar linha divisória azul antes da seção
            st.markdown('<hr class="divisor-azul" />', unsafe_allow_html=True)
            
            # Container para filtros
            st.markdown('<div class="filtros-container">', unsafe_allow_html=True)
            
            # Criar layout de colunas para os filtros
            col1, col2, col3 = st.columns(3)
            
            # Filtrar por responsável, se existir
            filtro_responsavel = None
            if "Responsável" in df.columns:
                with col1:
                    responsaveis = ["Todos"] + sorted(df["Responsável"].dropna().unique().tolist())
                    filtro_responsavel = st.selectbox("Responsável:", responsaveis)
            
            # Filtrar por fase, se existir
            filtro_fase = None
            if "Fase" in df.columns:
                with col2:
                    fases = ["Todas"] + sorted(df["Fase"].dropna().unique().tolist())
                    filtro_fase = st.selectbox("Fase:", fases)
            
            # Adicionar filtro de busca
            with col3:
                filtro_pesquisa = st.text_input("Pesquisar:")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            if filtro_responsavel and filtro_responsavel != "Todos":
                df_filtrado = df_filtrado[df_filtrado["Responsável"] == filtro_responsavel]
            
            if filtro_fase and filtro_fase != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Fase"] == filtro_fase]
            
            if filtro_pesquisa:
                df_filtrado = df_filtrado[df_filtrado.astype(str).apply(
                    lambda row: row.str.contains(filtro_pesquisa, case=False).any(), axis=1
                )]
            
            # Preparar colunas para exibição
            colunas_exibicao = []
            
            if "ID" in df_filtrado.columns:
                colunas_exibicao.append("ID")
            
            if "Criado" in df_filtrado.columns:
                colunas_exibicao.append("Criado")
            
            for col in ["Responsável", "Fase"]:
                if col in df_filtrado.columns and col not in colunas_exibicao:
                    colunas_exibicao.append(col)
            
            if "LINK ARVORE DA FAMÍLIA PLATAFORMA" in df_filtrado.columns:
                colunas_exibicao.append("LINK ARVORE DA FAMÍLIA PLATAFORMA")
            
            if "REUNIÃO" in df_filtrado.columns:
                colunas_exibicao.append("REUNIÃO")
            
            if "FECHADO" in df_filtrado.columns:
                colunas_exibicao.append("FECHADO")
            
            # Certificar que existem colunas para exibir
            if not colunas_exibicao:
                colunas_exibicao = df_filtrado.columns
            
            # Preparar DataFrame para exibição
            df_exibicao = df_filtrado[colunas_exibicao].copy()
            
            # Formatar as colunas de data
            for col in df_exibicao.columns:
                if col in ["Criado", "FECHADO"] and "date" in str(df_exibicao[col].dtype).lower():
                    df_exibicao[col] = df_exibicao[col].dt.strftime('%d/%m/%Y %H:%M')
            
            # Adicionar botões de download
            st.markdown("#### Opções de Download")
            col1, col2 = st.columns(2)
            
            with col1:
                # Link para download CSV
                csv = df_exibicao.to_csv(index=False, sep=';', encoding='utf-8-sig')
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="dados_filtrados.csv" class="download-btn">Exportar CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                excel_link = get_excel_download_link(df_exibicao, filename="dados_filtrados.xlsx", text="Exportar Excel")
                st.markdown(excel_link, unsafe_allow_html=True)
            
            # Exibir tabela com informação sobre o número de registros
            st.markdown(f"<p style='font-size: 13px; color: #424242; margin-bottom: 8px;'>Exibindo {len(df_exibicao)} registros filtrados de um total de {len(df)} registros.</p>", unsafe_allow_html=True)
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro ao exibir tabela detalhada: {str(e)}")
            st.write("Detalhes do erro:", e)
    
    @staticmethod
    def show_upload_instructions_section():
        """Exibe a seção de instruções para upload de dados no final da página"""
        try:
            # Adicionar instruções de upload em tamanho reduzido
            with st.expander("📤 Instruções para Upload de Dados", expanded=False):
                # Adicionar campo de senha
                senha = st.text_input("Digite a senha para acessar as instruções:", type="password")
                
                # Verificar se a senha está correta
                if senha == "132":
                    st.success("✅ Acesso autorizado!")
                    
                    st.markdown("### Como Atualizar os Dados do Dashboard")
                    
                    # Formato do arquivo
                    st.markdown("**Formato do arquivo:**")
                    st.markdown("CSV com separador ponto e vírgula (;), codificação UTF-8")
                    
                    # Colunas essenciais
                    st.markdown("**Colunas essenciais:**")
                    st.markdown("ID, Responsável, Fase, Criado, LINK ARVORE DA FAMÍLIA PLATAFORMA")
                    
                    # Procedimento
                    st.markdown("**Procedimento:**")
                    st.markdown("1. Selecione o arquivo CSV, renomei para extratacao_bitrix24.csv")
                    st.markdown("2. Aguarde a confirmação de upload")
                    st.markdown("3. Clique em \"Atualizar Dashboard\"")
                    
                    # Linha divisória
                    st.markdown('<hr style="margin: 10px 0;" />', unsafe_allow_html=True)
                    
                    # Upload de arquivo em formato reduzido
                    uploaded_file = st.file_uploader(
                        "Selecione o arquivo CSV:", 
                        type=["csv"], 
                        help="O arquivo deve estar no formato CSV com separador de ponto e vírgula (;)"
                    )
                    
                    if uploaded_file is not None:
                        try:
                            # Salvar o arquivo enviado no lugar do arquivo existente
                            with open("extratacao_bitrix24.csv", "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Mostrar mensagem de sucesso
                            st.success("✅ Arquivo carregado com sucesso! O dashboard será atualizado.")
                            
                            # Adicionar botão para recarregar a página
                            if st.button("Atualizar Dashboard"):
                                st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar o arquivo: {e}")
                elif senha and senha != "132":
                    st.error("❌ Senha incorreta. Tente novamente.")
                    
        except Exception as e:
            st.error(f"Erro ao exibir instruções de upload: {str(e)}")
                
    @staticmethod
    def show_timeline_chart(df):
        """Exibe gráficos de evolução temporal dos negócios"""
        try:
            st.subheader("Evolução Temporal")
            
            # Adicionar linha divisória azul antes da seção
            st.markdown('<hr class="divisor-azul" />', unsafe_allow_html=True)
            
            # Verificar se a coluna Criado existe e é do tipo datetime
            if "Criado" not in df.columns:
                st.warning("Coluna 'Criado' não encontrada no arquivo CSV. Não é possível gerar gráficos temporais.")
                return
                
            # Certifique-se que a coluna Criado é do tipo datetime
            if not pd.api.types.is_datetime64_any_dtype(df["Criado"]):
                st.warning("A coluna 'Criado' não está no formato de data/hora correto.")
                return
            
            # Configurar layout dos gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Novos Negócios por Mês")
            
            with col2:
                st.markdown("#### Total Acumulado de Negócios")
            
            # Gráfico de novos negócios por mês
            df_by_month = df.copy()
            df_by_month["Mês"] = df_by_month["Criado"].dt.strftime("%Y-%m")
            
            # Contagem por mês
            monthly_counts = df_by_month["Mês"].value_counts().reset_index()
            monthly_counts.columns = ["Mês", "Quantidade"]
            monthly_counts = monthly_counts.sort_values("Mês")
            
            # Gráfico de barras mensal
            fig_bar = px.bar(
                monthly_counts,
                x="Mês",
                y="Quantidade",
                title=None,  # Removido título interno do Plotly
                text="Quantidade",
                color="Quantidade",
                color_continuous_scale="viridis"
            )
            
            fig_bar.update_layout(
                height=300,  # Reduzido de 350
                xaxis_title="Mês",
                yaxis_title="Quantidade de Negócios",
                xaxis_tickangle=45,
                coloraxis_showscale=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=12, color="#212121"),  # Adicionado cor explícita para o texto
                margin=dict(l=40, r=30, t=15, b=40),  # Reduzido t de 20 para 15
                yaxis=dict(gridcolor="#F5F5F5")
            )
            
            col1.plotly_chart(fig_bar, use_container_width=True)
            
            # Gráfico cumulativo
            monthly_counts["Acumulado"] = monthly_counts["Quantidade"].cumsum()
            
            fig_line = px.line(
                monthly_counts,
                x="Mês",
                y="Acumulado",
                title=None,  # Removido título interno do Plotly
                markers=True,
                line_shape="spline"
            )
            
            fig_line.update_layout(
                height=300,  # Reduzido de 350
                xaxis_title="Mês",
                yaxis_title="Total Acumulado",
                xaxis_tickangle=45,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=12, color="#212121"),  # Adicionado cor explícita para o texto
                margin=dict(l=40, r=30, t=15, b=40),  # Reduzido t de 20 para 15
                yaxis=dict(gridcolor="#F5F5F5")
            )
            
            # Adicionar rótulos de dados
            fig_line.update_traces(
                textposition="top center",
                texttemplate="%{y}",
                line=dict(color="#0288D1", width=3),
                marker=dict(color="#0288D1", size=8)
            )
            
            col2.plotly_chart(fig_line, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao exibir gráficos temporais: {str(e)}")
            st.write("Detalhes do erro:", e)
    
    @staticmethod
    def show_assinatura_fechamento_analysis(df):
        """Exibe análise detalhada de assinaturas e fechamentos"""
        try:
            st.subheader("Análise de Assinaturas e Fechamentos")
            
            # Adicionar linha divisória azul antes da seção
            st.markdown('<hr class="divisor-azul" />', unsafe_allow_html=True)
            
            # Verificar se as colunas necessárias existem
            if "Fase" not in df.columns:
                st.warning("Coluna 'Fase' não encontrada no arquivo CSV. Não é possível gerar análise de assinaturas.")
                return
            
            # Filtrar negócios assinados e env. novo adm
            df_assinados = df[df["Fase"] == "ASSINADO"].copy()
            df_env_novo_adm = df[df["Fase"].isin(["ENV. NOVO ADM", "ENV.. NOVO ADM", "VALIDADO ENVIAR FINANCEIRO"])].copy()
            
            # Combinar os dois DataFrames para análise
            df_finalizados = pd.concat([df_assinados, df_env_novo_adm])
            
            # Verificar se há dados para análise
            if len(df_finalizados) == 0:
                st.info("Não foram encontrados negócios nas fases 'ASSINADO', 'ENV. NOVO ADM' ou 'VALIDADO ENVIAR FINANCEIRO'.")
                return
            
            # Verificar se a coluna FECHADO existe
            if "FECHADO" in df.columns:
                # Converter para datetime se ainda não for
                if not pd.api.types.is_datetime64_any_dtype(df_finalizados["FECHADO"]):
                    df_finalizados["FECHADO"] = pd.to_datetime(df_finalizados["FECHADO"], dayfirst=True, errors='coerce')
                
                # Marcar negócios na fase "VALIDADO ENVIAR FINANCEIRO" como fechados
                # Se não tiverem data de fechamento, usar a data de modificação
                for idx in df_finalizados.index:
                    if df_finalizados.loc[idx, "Fase"] == "VALIDADO ENVIAR FINANCEIRO" and pd.isna(df_finalizados.loc[idx, "FECHADO"]):
                        if "Modificado" in df_finalizados.columns:
                            df_finalizados.loc[idx, "FECHADO"] = df_finalizados.loc[idx, "Modificado"]
                
                # Separar negócios com e sem data de fechamento
                # Considerar todos os negócios na fase "VALIDADO ENVIAR FINANCEIRO" como fechados
                df_com_fechamento = df_finalizados[(df_finalizados["FECHADO"].notna()) | 
                                                  (df_finalizados["Fase"] == "VALIDADO ENVIAR FINANCEIRO")].copy()
                df_sem_fechamento = df_finalizados[(df_finalizados["FECHADO"].isna()) & 
                                                  (df_finalizados["Fase"] != "VALIDADO ENVIAR FINANCEIRO")].copy()
                
                # Calcular métricas
                total_finalizados = len(df_finalizados)
                total_assinados = len(df_assinados)
                total_env_novo_adm = len(df_env_novo_adm)
                total_com_fechamento = len(df_com_fechamento)
                total_sem_fechamento = len(df_sem_fechamento)
                
                # Calcular percentuais
                if total_finalizados > 0:
                    percentual_com_fechamento = (total_com_fechamento / total_finalizados) * 100
                    percentual_sem_fechamento = (total_sem_fechamento / total_finalizados) * 100
                else:
                    percentual_com_fechamento = 0
                    percentual_sem_fechamento = 0
                
                # Exibir métricas em cards
                st.markdown("### Visão Geral")
                
                # Criar layout com 3 colunas para os cards principais
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; border-left: 5px solid #673AB7; margin-bottom: 15px;">
                        <h3 style="color: #0D47A1; margin-top: 0; margin-bottom: 10px;">Negócios Assinados</h3>
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: #0D47A1; margin-right: 15px;">{formatar_numero(total_assinados)}</div>
                            <div style="font-size: 18px; color: #0D47A1;">{(total_assinados/total_finalizados*100):.1f}% do total</div>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
                with col2:
                    st.markdown(f"""
                    <div style="background-color: #E8EAF6; padding: 15px; border-radius: 8px; border-left: 5px solid #3F51B5; margin-bottom: 15px;">
                        <h3 style="color: #0D47A1; margin-top: 0; margin-bottom: 10px;">Env. Novo ADM</h3>
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: #0D47A1; margin-right: 15px;">{formatar_numero(total_env_novo_adm)}</div>
                            <div style="font-size: 18px; color: #0D47A1;">{(total_env_novo_adm/total_finalizados*100):.1f}% do total</div>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
                with col3:
                    st.markdown(f"""
                    <div style="background-color: #E0F7FA; padding: 15px; border-radius: 8px; border-left: 5px solid #00BCD4; margin-bottom: 15px;">
                        <h3 style="color: #0D47A1; margin-top: 0; margin-bottom: 10px;">Total Finalizados</h3>
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: #0D47A1; margin-right: 15px;">{formatar_numero(total_finalizados)}</div>
                            <div style="font-size: 18px; color: #0D47A1;">100% do total</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Adicionar linha divisória
                st.markdown('<hr class="divisor-azul" style="margin: 1rem 0;" />', unsafe_allow_html=True)
                
                # Seção de análise de fechamento
                st.markdown("### Análise de Fechamento")
                
                # Criar layout com 2 colunas para os cards de fechamento
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; border-left: 5px solid #4CAF50; margin-bottom: 15px;">
                        <h3 style="color: #2E7D32; margin-top: 0; margin-bottom: 10px;">Com Data de Fechamento</h3>
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: #2E7D32; margin-right: 15px;">{formatar_numero(total_com_fechamento)}</div>
                            <div style="font-size: 18px; color: #2E7D32;">{percentual_com_fechamento:.1f}% dos finalizados</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; border-left: 5px solid #F44336; margin-bottom: 15px;">
                        <h3 style="color: #C62828; margin-top: 0; margin-bottom: 10px;">Sem Data de Fechamento</h3>
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: #C62828; margin-right: 15px;">{formatar_numero(total_sem_fechamento)}</div>
                            <div style="font-size: 18px; color: #C62828;">{percentual_sem_fechamento:.1f}% dos finalizados</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gráfico de pizza para visualizar a proporção
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de pizza para fases
                    fig_fase = go.Figure(data=[go.Pie(
                        labels=['Assinados', 'Env. Novo ADM / Validado Financeiro'],
                        values=[total_assinados, total_env_novo_adm],
                        hole=.4,
                        marker_colors=['#673AB7', '#3F51B5']
                    )])
                    
                    fig_fase.update_layout(
                        title="Distribuição por Fase",
                        height=350,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                    )
                    
                    st.plotly_chart(fig_fase, use_container_width=True)
                
                with col2:
                    # Gráfico de pizza para fechamento
                    fig_fechamento = go.Figure(data=[go.Pie(
                        labels=['Com Data de Fechamento', 'Sem Data de Fechamento'],
                        values=[total_com_fechamento, total_sem_fechamento],
                        hole=.4,
                        marker_colors=['#4CAF50', '#F44336']
                    )])
                    
                    fig_fechamento.update_layout(
                        title="Status de Fechamento",
                        height=350,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                    )
                    
                    st.plotly_chart(fig_fechamento, use_container_width=True)
                
                # Análise detalhada por fase e fechamento
                st.markdown("### Análise Detalhada por Fase e Fechamento")
                
                # Criar DataFrame para análise cruzada
                df_assinados_com_fechamento = df_assinados[df_assinados["FECHADO"].notna()].shape[0]
                df_assinados_sem_fechamento = df_assinados[df_assinados["FECHADO"].isna()].shape[0]
                df_env_novo_adm_com_fechamento = df_env_novo_adm[df_env_novo_adm["FECHADO"].notna()].shape[0]
                df_env_novo_adm_sem_fechamento = df_env_novo_adm[df_env_novo_adm["FECHADO"].isna()].shape[0]
                
                # Calcular percentuais
                if total_assinados > 0:
                    perc_assinados_com_fechamento = (df_assinados_com_fechamento / total_assinados) * 100
                else:
                    perc_assinados_com_fechamento = 0
                    
                if total_env_novo_adm > 0:
                    perc_env_novo_adm_com_fechamento = (df_env_novo_adm_com_fechamento / total_env_novo_adm) * 100
                else:
                    perc_env_novo_adm_com_fechamento = 0
                
                # Criar DataFrame para o gráfico de barras
                data = {
                    'Fase': ['Assinados', 'Env. Novo ADM'],
                    'Com Fechamento': [df_assinados_com_fechamento, df_env_novo_adm_com_fechamento],
                    'Sem Fechamento': [df_assinados_sem_fechamento, df_env_novo_adm_sem_fechamento]
                }
                df_analise = pd.DataFrame(data)
                
                # Criar gráfico de barras empilhadas
                fig_barras = px.bar(
                    df_analise,
                    x='Fase',
                    y=['Com Fechamento', 'Sem Fechamento'],
                    title="Distribuição de Fechamento por Fase",
                    barmode='stack',
                    color_discrete_map={'Com Fechamento': '#4CAF50', 'Sem Fechamento': '#F44336'},
                    text_auto=True
                )
                
                fig_barras.update_layout(
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                
                st.plotly_chart(fig_barras, use_container_width=True)
                
                # Exibir tabela com os dados
                st.markdown("#### Tabela de Análise por Fase")
                
                # Criar DataFrame para a tabela
                data_tabela = {
                    'Fase': ['Assinados', 'Env. Novo ADM / Validado Financeiro', 'Total'],
                    'Total': [total_assinados, total_env_novo_adm, total_finalizados],
                    'Com Fechamento': [df_assinados_com_fechamento, df_env_novo_adm_com_fechamento, total_com_fechamento],
                    'Sem Fechamento': [df_assinados_sem_fechamento, df_env_novo_adm_sem_fechamento, total_sem_fechamento],
                    '% Com Fechamento': [f"{perc_assinados_com_fechamento:.1f}%", f"{perc_env_novo_adm_com_fechamento:.1f}%", f"{percentual_com_fechamento:.1f}%"]
                }
                df_tabela = pd.DataFrame(data_tabela)
                
                st.dataframe(df_tabela, use_container_width=True, hide_index=True)
                
                # Adicionar botão para download
                excel_link = get_excel_download_link(df_tabela, filename="analise_fechamento_fase.xlsx", text="Exportar Excel")
                st.markdown(excel_link, unsafe_allow_html=True)
                
                # Análise por responsável
                if "Responsável" in df_finalizados.columns:
                    st.markdown("### Análise por Responsável")
                    
                    # Agrupar por responsável
                    resp_analysis = df_finalizados.groupby("Responsável").agg(
                        Total_Finalizados=("ID", "count"),
                    ).reset_index()
                    
                    # Adicionar contagem de fechados por responsável
                    resp_fechados = df_com_fechamento.groupby("Responsável").agg(
                        Total_Com_Fechamento=("ID", "count")
                    ).reset_index()
                    
                    # Mesclar os DataFrames
                    resp_analysis = pd.merge(resp_analysis, resp_fechados, on="Responsável", how="left").fillna(0)
                    
                    # Calcular percentual de fechados
                    resp_analysis["Total_Com_Fechamento"] = resp_analysis["Total_Com_Fechamento"].astype(int)
                    resp_analysis["Percentual_Fechados"] = (resp_analysis["Total_Com_Fechamento"] / resp_analysis["Total_Finalizados"] * 100).round(1)
                    
                    # Calcular total sem fechamento
                    resp_analysis["Total_Sem_Fechamento"] = resp_analysis["Total_Finalizados"] - resp_analysis["Total_Com_Fechamento"]
                    
                    # Ordenar por total de finalizados (decrescente)
                    resp_analysis = resp_analysis.sort_values("Total_Finalizados", ascending=False)
                    
                    # Criar gráfico de barras
                    fig_bar = px.bar(
                        resp_analysis,
                        x="Responsável",
                        y=["Total_Com_Fechamento", "Total_Sem_Fechamento"],
                        title="Negócios Finalizados por Responsável",
                        barmode="stack",
                        color_discrete_map={"Total_Com_Fechamento": "#4CAF50", "Total_Sem_Fechamento": "#F44336"},
                        labels={
                            "value": "Quantidade",
                            "variable": "Status",
                            "Responsável": "Responsável"
                        },
                        text_auto=True
                    )
                    
                    fig_bar.update_layout(
                        height=400,
                        xaxis_tickangle=-45,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=20, r=20, t=60, b=80)
                    )
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # Exibir tabela com os dados
                    st.markdown("#### Tabela de Desempenho por Responsável")
                    
                    # Formatar tabela para exibição
                    resp_analysis_display = resp_analysis.copy()
                    resp_analysis_display["Percentual_Fechados"] = resp_analysis_display["Percentual_Fechados"].apply(lambda x: f"{x}%")
                    resp_analysis_display.columns = ["Responsável", "Total Finalizados", "Com Fechamento", "% Fechados", "Sem Fechamento"]
                    
                    # Reordenar colunas
                    resp_analysis_display = resp_analysis_display[["Responsável", "Total Finalizados", "Com Fechamento", "Sem Fechamento", "% Fechados"]]
                    
                    st.dataframe(resp_analysis_display, use_container_width=True, hide_index=True)
                    
                    # Adicionar botão para download
                    excel_link = get_excel_download_link(resp_analysis_display, filename="analise_fechamento_responsavel.xlsx", text="Exportar Excel")
                    st.markdown(excel_link, unsafe_allow_html=True)
                
                # Lista de negócios sem data de fechamento
                if len(df_sem_fechamento) > 0:
                    st.markdown("### Negócios sem Data de Fechamento")
                    
                    # Selecionar colunas para exibição
                    colunas_exibir = ["ID", "Responsável", "Fase", "Criado"]
                    colunas_disponiveis = [col for col in colunas_exibir if col in df_sem_fechamento.columns]
                    
                    # Formatar datas para exibição
                    df_sem_fechamento_display = df_sem_fechamento[colunas_disponiveis].copy()
                    if "Criado" in df_sem_fechamento_display.columns and pd.api.types.is_datetime64_any_dtype(df_sem_fechamento_display["Criado"]):
                        df_sem_fechamento_display["Criado"] = df_sem_fechamento_display["Criado"].dt.strftime('%d/%m/%Y')
                    
                    # Exibir tabela
                    st.dataframe(df_sem_fechamento_display, use_container_width=True, hide_index=True)
                    
                    # Adicionar botão para download
                    excel_link = get_excel_download_link(df_sem_fechamento_display, filename="negocios_sem_fechamento.xlsx", text="Exportar Excel")
                    st.markdown(excel_link, unsafe_allow_html=True)
            else:
                st.warning("Coluna 'FECHADO' não encontrada no arquivo CSV. Não é possível analisar datas de fechamento.")
        
        except Exception as e:
            st.error(f"Erro ao exibir análise de assinaturas e fechamentos: {str(e)}")
            st.write("Detalhes do erro:", e)
    
    @classmethod
    def render(cls):
        """Renderiza o dashboard completo"""
        try:
            # Carregar dados
            df = cls.load_data()
            
            # Definir estilo CSS
            cls.set_style()
            
            st.title("Dashboard de Análise de Negociações")
            
            # Verificar se o DataFrame está vazio
            if df.empty:
                st.error("Não foi possível carregar os dados. Verifique se o arquivo CSV está disponível e bem formatado.")
                return
            
            # Descrição do dashboard (versão reduzida)
            st.markdown("""
            <div style="background-color: var(--cor-azul-claro); padding: 8px; border-radius: 8px; margin-bottom: 5px; border: 2px solid var(--cor-azul-escuro);">
                <h5 style="color: var(--cor-azul-escuro); margin-top: 0; margin-bottom: 3px; font-weight: 600;">Análise do Progresso de Negócios</h5>
                <p style="color: var(--cor-texto); font-size: 13px; line-height: 1.2; margin-bottom: 0;">
                    Dashboard com análise detalhada do progresso dos negócios por responsável. Identifique duplicações e monitore o funil de vendas.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar métricas principais com margem reduzida
            st.markdown('<div class="chart-container" style="margin-bottom: 5px;">', unsafe_allow_html=True)
            cls.show_main_metrics(df)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Adicionar linha divisória antes da navegação com margem reduzida
            st.markdown('<hr class="divisor-azul" style="margin: 0.5rem 0;" />', unsafe_allow_html=True)
        
            # Definir as abas de navegação com novo estilo
            st.markdown("""
            <style>
            /* Estilo personalizado para as abas */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0;
                background-color: #e3f2fd;
                padding: 8px 8px 0 8px;
                border-radius: 8px 8px 0 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #bbdefb;
                margin-bottom: 0;
                border-bottom: none;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 40px;
                white-space: pre;
                background-color: white;
                border-radius: 6px 6px 0 0;
                color: #495057;
                font-size: 14px;
                font-weight: 500;
                border: none;
                padding: 0 16px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                bottom: -1px;
                margin: 0 1px;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background-color: #bbdefb;
                color: #1976D2;
                transform: translateY(-2px);
            }
            
            .stTabs [aria-selected="true"] {
                background-color: white !important;
                color: #1976D2 !important;
                font-weight: 600;
                border-top: 3px solid #1976D2 !important;
                box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
                z-index: 1;
            }

            .stTabs [data-baseweb="tab-panel"] {
                background-color: white;
                padding: 15px;
                border-radius: 0 0 8px 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                animation: fadeIn 0.3s ease-in-out;
                border: 1px solid #bbdefb;
                border-top: none;
            }

            /* Redução de espaços em todo o dashboard */
            .stApp {
                margin: 0 !important;
                padding: 0 !important;
            }

            .main .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }

            h1, h2, h3, h4, h5, h6 {
                margin-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }

            .element-container {
                margin-bottom: 0.5rem !important;
            }

            .stButton, .stDownloadButton {
                margin-bottom: 0.5rem !important;
            }

            p {
                margin-bottom: 0.5rem !important;
            }

            hr {
                margin: 0.5rem 0 !important;
            }

            .divisor-azul {
                margin: 0.5rem 0 !important;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-5px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Estilo para os cards de métricas de duplicação */
            .duplicados-header {
                background-color: #fef2f2;
                padding: 10px 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                border: 1px solid #fee2e2;
            }

            .duplicados-header h3 {
                color: #dc2626;
                font-size: 16px;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .duplicados-metrics {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 10px 0;
            }
            
            .duplicados-metric {
                background: linear-gradient(135deg, #fff5f5 0%, #fef2f2 100%);
                padding: 12px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #fecaca;
                box-shadow: 0 2px 4px rgba(220, 38, 38, 0.1);
                transition: transform 0.2s ease;
            }
            
            .duplicados-metric-label {
                color: #991b1b;
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 5px;
                text-transform: uppercase;
            }
            
            .duplicados-metric-value {
                color: #dc2626;
                font-size: 28px;
                font-weight: 700;
                text-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
                margin: 0;
                line-height: 1;
            }

            .duplicados-metric-value:after {
                content: "";
                display: block;
                width: 30px;
                height: 2px;
                background-color: #dc2626;
                margin: 6px auto 0;
                border-radius: 2px;
            }

            /* Ajuste para as tabelas */
            .stDataFrame {
                margin-top: 5px !important;
                margin-bottom: 5px !important;
            }

            /* Ajuste para os gráficos */
            .js-plotly-plot {
                margin-top: 5px !important;
                margin-bottom: 5px !important;
            }

            /* Redução de espaço nas colunas */
            [data-testid="column"] {
                padding: 0 3px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Remove margin-top from footer
            st.markdown("""
            <style>
            footer {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            tab_funil, tab_duplicados, tab_sem_modificacao, tab_upload = st.tabs([
                "Análise do Funil", 
                "Análise de Duplicados",
                "Cards sem modificação",
                "Upload de Arquivo"
            ])
            
            # Conteúdo da aba Análise do Funil
            with tab_funil:
                cls.show_funil_chart(df)
                cls.show_responsavel_chart(df)
                # Adicionar tabela de responsáveis com etapas do funil
                st.markdown('<hr style="margin: 20px 0;" />', unsafe_allow_html=True)
                cls.show_responsavel_table(df)
            
            # Conteúdo da aba Análise de Duplicados
            with tab_duplicados:
                cls.show_duplicated_links(df)
            
            # Conteúdo da aba Cards sem modificação
            with tab_sem_modificacao:
                cls.show_cards_sem_modificacao(df)
            
            # Conteúdo da aba Upload de Arquivo
            with tab_upload:
                cls.show_upload_instructions_section()
            
            # Adicionar linha divisória antes do footer
            st.markdown('<hr class="divisor-azul-grosso" />', unsafe_allow_html=True)
            
            # Adicionar footer com informações de fonte e atualização
            st.markdown("""
            <div class="footer" style="margin-top: 8px; border-top: 3px solid var(--cor-azul-medio); padding-top: 12px;">
                <p style="color: #666; font-size: 12px; text-align: center;">
                    Fonte: Dados extraídos do sistema Bitrix24 • Última atualização: {:%d/%m/%Y %H:%M}
                </p>
            </div>
            """.format(datetime.now()), unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao renderizar o dashboard de responsáveis: {str(e)}")
            
            # Exibir informações de debug para facilitar a resolução de problemas
            st.warning("Informações para debug:")
            debug_info = []
            
            # Verificar caminho do arquivo CSV
            csv_path = os.path.join('data', 'extratacao_bitrix24.csv')
            if os.path.exists(csv_path):
                debug_info.append(f"Arquivo CSV encontrado em: {csv_path}")
            else:
                debug_info.append(f"Arquivo CSV não encontrado em: {csv_path}")
                # Listar arquivos na pasta data
                if os.path.exists('data'):
                    files = os.listdir('data')
                    debug_info.append(f"Arquivos disponíveis na pasta 'data': {', '.join(files)}")
            
            # Verificar estrutura do dataframe
            debug_info.append(f"💻 Python version: {sys.version}")
            
            # Exibir informações de debug
            for info in debug_info:
                st.text(info)
    
    @staticmethod
    def show_responsavel_table(df):
        """Exibe tabela com responsáveis e etapas do funil de vendas"""
        try:
            # Verificar se as colunas Responsável e Fase existem
            if "Responsável" not in df.columns or "Fase" not in df.columns:
                st.warning("Colunas 'Responsável' ou 'Fase' não encontradas no arquivo CSV.")
                return
            
            st.subheader("Tabela de Responsáveis por Etapas do Funil")
            
            # Obter a contagem de negócios por responsável e fase
            tabela_pivot = pd.pivot_table(
                df, 
                values='ID', 
                index=['Responsável'], 
                columns=['Fase'], 
                aggfunc='count',
                fill_value=0
            ).reset_index()
            
            # Garantir que todas as fases em FASES_ORDEM estão presentes na tabela
            for fase in FASES_ORDEM:
                if fase not in tabela_pivot.columns:
                    tabela_pivot[fase] = 0
            
            # Reorganizar as colunas na ordem definida em FASES_ORDEM
            colunas_ordenadas = ['Responsável'] + [col for col in FASES_ORDEM if col in tabela_pivot.columns]
            tabela_pivot = tabela_pivot[colunas_ordenadas]
            
            # Adicionar coluna de total
            tabela_pivot['Total'] = tabela_pivot.iloc[:, 1:].sum(axis=1)
            
            # Ordenar por total (decrescente)
            tabela_pivot = tabela_pivot.sort_values(by='Total', ascending=False)
            
            # Formatar os valores numéricos para exibição
            for col in tabela_pivot.columns:
                if col != 'Responsável':
                    tabela_pivot[col] = tabela_pivot[col].astype(int)
            
            # Calcular totais por coluna
            totais_colunas = tabela_pivot.sum(numeric_only=True).to_frame().T
            totais_colunas.insert(0, 'Responsável', 'TOTAL')
            
            # Adicionar linha de totais ao DataFrame
            tabela_final = pd.concat([tabela_pivot, totais_colunas], ignore_index=True)
            
            # Formatar a linha de totais com estilo diferenciado
            def highlight_total(val):
                if val == 'TOTAL':
                    return 'background-color: #E1F5FE; font-weight: bold;'
                return ''
            
            # Exibir a tabela com destaque
            st.dataframe(
                tabela_final, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Responsável": st.column_config.TextColumn(
                        "Responsável",
                        width="medium",
                    ),
                    "Total": st.column_config.NumberColumn(
                        "Total",
                        format="%d",
                        width="small",
                    ),
                }
            )
            
            # Adicionar botão para download
            excel_link = get_excel_download_link(tabela_final, filename="responsaveis_funil.xlsx", text="Exportar Excel")
            st.markdown(excel_link, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao gerar tabela de responsáveis: {str(e)}")
            st.write("Detalhes do erro:", e)

if __name__ == "__main__":
    # Renderizar dashboard
    ResponsavelDashboard.render()
