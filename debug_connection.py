"""
Script de diagnóstico para testar a conexão com o Bitrix24

Este script tenta estabelecer uma conexão direta com o Bitrix24 usando
as credenciais configuradas e imprime informações detalhadas sobre
o resultado.

Para executar:
streamlit run debug_connection.py
"""
import streamlit as st
import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Configuração da página
st.set_page_config(
    page_title="Diagnóstico de Conexão - Bitrix24",
    page_icon="🔍",
    layout="wide"
)

st.title("Diagnóstico de Conexão com Bitrix24")
st.write("Esta ferramenta testa a conexão com o Bitrix24 e exibe informações detalhadas para ajudar a resolver problemas.")

# Carregar variáveis de ambiente
with st.expander("Carregamento de configurações", expanded=True):
    st.subheader("1. Verificando arquivo .env")
    dotenv_path = Path('.env')
    if dotenv_path.exists():
        st.success("Arquivo .env encontrado")
        load_dotenv(dotenv_path=dotenv_path)
        st.info("Variáveis carregadas do arquivo .env")
    else:
        st.warning("Arquivo .env não encontrado")
        alt_dotenv_path = Path('src/ui/streamlit/.env')
        if alt_dotenv_path.exists():
            st.success("Arquivo .env alternativo encontrado")
            load_dotenv(dotenv_path=alt_dotenv_path)
            st.info("Variáveis carregadas do arquivo .env alternativo")
        else:
            st.error("Nenhum arquivo .env encontrado!")

    st.subheader("2. Verificando secrets do Streamlit")
    try:
        if hasattr(st, 'secrets') and st.secrets:
            st.success("Secrets do Streamlit encontradas")
            
            # Listar as chaves disponíveis (sem mostrar valores sensíveis)
            secret_keys = list(st.secrets.keys())
            st.write("Seções/chaves disponíveis:", secret_keys)
            
            # Verificar seção 'bitrix'
            if "bitrix" in st.secrets:
                st.success("Seção 'bitrix' encontrada nas secrets")
                bitrix_keys = list(st.secrets['bitrix'].keys())
                st.write("Chaves na seção 'bitrix':", bitrix_keys)
                
                # Verificar os valores críticos (sem revelar completamente)
                if "base_url" in st.secrets['bitrix']:
                    url = st.secrets['bitrix']['base_url']
                    st.write("URL base:", url[:20] + "..." if len(url) > 20 else url)
                if "token" in st.secrets['bitrix']:
                    token = st.secrets['bitrix']['token']
                    st.write("Token configurado:", "✓" if token else "✗")
                    st.write("Primeiros 4 caracteres do token:", token[:4] + "..." if token else "N/A")
            else:
                st.warning("Seção 'bitrix' não encontrada nas secrets")
                
                # Verificar se as chaves estão no nível raiz
                if "BITRIX_BASE_URL" in st.secrets:
                    st.success("Chave 'BITRIX_BASE_URL' encontrada no nível raiz")
                    url = st.secrets['BITRIX_BASE_URL']
                    st.write("URL base:", url[:20] + "..." if len(url) > 20 else url)
                if "BITRIX_TOKEN" in st.secrets:
                    st.success("Chave 'BITRIX_TOKEN' encontrada no nível raiz")
                    token = st.secrets['BITRIX_TOKEN']
                    st.write("Token configurado:", "✓" if token else "✗")
                    st.write("Primeiros 4 caracteres do token:", token[:4] + "..." if token else "N/A")
        else:
            st.warning("Nenhuma secret configurada no Streamlit")
    except Exception as e:
        st.error(f"Erro ao acessar secrets do Streamlit: {str(e)}")

    st.subheader("3. Consolidação de configurações")
    
    # Determinar os valores finais após a consolidação de todas as fontes
    # Seguindo a mesma prioridade do código real
    final_base_url = None
    final_token = None
    
    # Primeiro, tentar nas secrets do Streamlit
    try:
        if "bitrix" in st.secrets:
            final_base_url = st.secrets["bitrix"]["base_url"]
            final_token = st.secrets["bitrix"]["token"]
        elif "BITRIX_BASE_URL" in st.secrets:
            final_base_url = st.secrets["BITRIX_BASE_URL"]
            final_token = st.secrets["BITRIX_TOKEN"]
    except Exception:
        pass
    
    # Se não encontrou nas secrets, tentar nas variáveis de ambiente
    if not final_base_url:
        final_base_url = os.environ.get("BITRIX_BASE_URL")
    if not final_token:
        final_token = os.environ.get("BITRIX_TOKEN")
    
    # Valores padrão como último recurso
    if not final_base_url:
        final_base_url = "https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
    if not final_token:
        final_token = "0z1rgUWgNbR0e53G7T88D9A1gkDWGly7br"
    
    st.write("URL base final:", final_base_url[:20] + "..." if len(final_base_url) > 20 else final_base_url)
    st.write("Token final:", "✓ Configurado" if final_token else "✗ Não configurado")
    st.write("Primeiros 4 caracteres do token final:", final_token[:4] + "..." if final_token else "N/A")

# Interface para testar conexão
st.subheader("Teste de Conexão com Bitrix24")

col1, col2 = st.columns(2)

with col1:
    # Permitir editar os valores para teste
    test_url = st.text_input("URL para teste:", value=final_base_url)
    test_token = st.text_input("Token para teste:", value=final_token)

with col2:
    # Opções de teste
    test_table = st.selectbox(
        "Tabela para teste:", 
        ["crm_deal", "user", "crm_deal_fields", "crm_deal_uf"]
    )
    
    test_limit = st.number_input("Limite de registros:", min_value=1, max_value=10, value=1)

# Botão para testar a conexão
if st.button("Testar Conexão", type="primary"):
    st.write("---")
    st.subheader("Resultados do Teste")
    
    # Construir URL e parâmetros
    url = f"{test_url}?token={test_token}&table={test_table}"
    
    params = {
        "FILTER": {},
        "SELECT": ["*"],
        "limit": test_limit
    }
    
    # Adicionar a categoria de negócios se for crm_deal
    if test_table == "crm_deal":
        category_id = os.environ.get("BITRIX_CATEGORY_ID", 34)
        try:
            category_id = int(category_id)
        except:
            category_id = 34
        params["FILTER"]["CATEGORY_ID"] = category_id
    
    # Mostrar a requisição
    st.write("URL da requisição:", url.replace(test_token, "TOKEN_OCULTADO"))
    st.write("Parâmetros:")
    st.json(params)
    
    # Fazer a requisição
    try:
        with st.spinner("Conectando ao Bitrix24..."):
            headers = {
                'Content-Type': 'application/json'
            }
            payload = json.dumps(params)
            
            response = requests.post(url, headers=headers, data=payload, timeout=30)
        
        # Exibir resultados
        st.write("Status da resposta:", response.status_code)
        
        if response.status_code == 200:
            st.success("Conexão estabelecida com sucesso!")
            
            try:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    st.success(f"Dados obtidos com sucesso! ({len(data)} registros)")
                    
                    # Transformar em DataFrame para melhor visualização
                    if len(data) > 0:
                        if isinstance(data[0], list) and len(data) > 1:
                            # Caso 1: Resposta em formato de matriz (cabeçalhos + dados)
                            headers = data[0]
                            rows = data[1:]
                            df = pd.DataFrame(rows, columns=headers)
                        else:
                            # Caso 2: Lista de dicionários
                            df = pd.DataFrame(data)
                        
                        st.dataframe(df)
                    else:
                        st.warning("A resposta está vazia (lista sem elementos).")
                elif isinstance(data, dict):
                    if "error" in data:
                        st.error(f"Erro retornado pela API: {data['error']}")
                        if "error_description" in data:
                            st.error(f"Descrição: {data['error_description']}")
                    else:
                        st.success("Resposta obtida com sucesso (formato de dicionário)")
                        st.json(data)
                else:
                    st.warning(f"Formato de resposta inesperado: {type(data)}")
                    st.json(data)
                    
            except json.JSONDecodeError:
                st.error("A resposta não é um JSON válido.")
                st.code(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
        else:
            st.error(f"Falha na conexão: {response.status_code} - {response.reason}")
            st.code(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
    
    except requests.exceptions.Timeout:
        st.error("Erro: A conexão excedeu o tempo limite (timeout)")
    except requests.exceptions.ConnectionError:
        st.error("Erro: Não foi possível conectar ao servidor")
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# Instruções para resolução de problemas
with st.expander("Dicas para Resolução de Problemas"):
    st.markdown("""
    ### Problemas Comuns e Soluções
    
    1. **Erro de autenticação (401/403)**
       - Verifique se o token está correto
       - Confirme se o token ainda é válido (não expirou)
       - Verifique se o token tem as permissões necessárias
    
    2. **Timeout ou falha de conexão**
       - Verifique sua conexão com a internet
       - Confirme se a URL do Bitrix24 está correta
       - Verifique se o Bitrix24 não está bloqueando sua conexão
    
    3. **Dados vazios**
       - Verifique os filtros utilizados (ex: categoria incorreta)
       - Confirme se realmente existem dados para o período/filtro especificado
    
    4. **Resposta com erro de formato**
       - Verifique se a estrutura da requisição está correta
       - Confirme se os parâmetros estão no formato esperado pela API
    
    ### Como Corrigir no Streamlit Cloud
    
    1. Acesse a configuração do seu aplicativo no Streamlit Cloud
    2. Vá para a seção "Secrets"
    3. Configure as secrets no formato:
    
    ```toml
    [bitrix]
    base_url = "https://seudominio.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
    token = "seu_token_aqui"
    category_id = 34
    
    # Ou no formato direto
    BITRIX_BASE_URL = "https://seudominio.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
    BITRIX_TOKEN = "seu_token_aqui"
    BITRIX_CATEGORY_ID = 34
    ```
    """)

# Adicionar informações do sistema
with st.expander("Informações do Sistema"):
    st.write("Python:", sys.version)
    st.write("Streamlit:", st.__version__)
    st.write("Requests:", requests.__version__)
    st.write("Pandas:", pd.__version__)
    
    st.write("Variáveis de ambiente relacionadas ao Bitrix24:")
    env_vars = {k: v[:4] + "..." if k.endswith("TOKEN") and v else v for k, v in os.environ.items() if k.startswith("BITRIX")}
    if env_vars:
        st.json(env_vars)
    else:
        st.write("Nenhuma variável de ambiente relacionada ao Bitrix24 encontrada")
    
    st.write("Caminho de execução:", os.getcwd()) 