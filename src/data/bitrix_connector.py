import requests
import pandas as pd
import json
import os
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BitrixConnector")

class BitrixConnector:
    """
    Classe responsável por gerenciar a conexão com a API do Bitrix24
    e realizar as consultas necessárias.
    """
    
    def __init__(self, base_url=None, token=None):
        """
        Inicializa o conector com a URL base e o token de autenticação.
        
        Args:
            base_url: URL base da API do Bitrix24. Se None, será lido da variável de ambiente BITRIX_BASE_URL
            token: Token de autenticação. Se None, será lido da variável de ambiente BITRIX_TOKEN
        """
        self.base_url = base_url or os.environ.get("BITRIX_BASE_URL")
        self.token = token or os.environ.get("BITRIX_TOKEN")
        
        # Log das variáveis de ambiente para debug
        env_vars = {k: v for k, v in os.environ.items() if k.startswith("BITRIX")}
        logger.info(f"Variáveis de ambiente Bitrix disponíveis: {list(env_vars.keys())}")
        
        # Token manual como último recurso
        if not self.token:
            self.token = "RuUSETRkbFD3whitfgMbioX8qjLgcdPubr"
            logger.warning("Token não encontrado nas variáveis de ambiente! Usando token padrão definido no código.")
        
        if not self.base_url:
            self.base_url = "https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
            logger.warning("URL base não encontrada nas variáveis de ambiente! Usando URL padrão definida no código.")
            
        logger.info(f"BitrixConnector inicializado com URL base: {self.base_url}")
        logger.info(f"Token configurado: {'OK (não vazio)' if self.token else 'FALHA (vazio)'}")
    
    def _make_request(self, table, query_params):
        """
        Realiza uma requisição à API do Bitrix24.
        
        Args:
            table: Nome da tabela a ser consultada (ex: 'crm_deal')
            query_params: Parâmetros da consulta em formato JSON
            
        Returns:
            Uma lista com os dados da resposta ou None em caso de erro
        """
        # Construir a URL completa
        url = f"{self.base_url}?token={self.token}&table={table}"
        
        try:
            logger.info(f"Realizando requisição para {table}")
            logger.info(f"URL: {url}")
            
            # Registro dos parâmetros de consulta para debug
            logger.info(f"Parâmetros da consulta: {json.dumps(query_params, indent=2)}")
            
            # Construindo a requisição
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Diferentes formatos de requisição para testar
            payload = json.dumps(query_params)
            
            logger.info("Enviando requisição POST...")
            response = requests.post(url, headers=headers, data=payload)
            
            # Verificar status da resposta
            logger.info(f"Status da resposta: {response.status_code}")
            
            # Registrar os primeiros 1000 caracteres da resposta para debug
            response_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
            logger.info(f"Resposta: {response_text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Diagnóstico do tipo de resposta
                    logger.info(f"Tipo de resposta: {type(data)}")
                    
                    # Verificar formato de matriz (onde o primeiro elemento são os cabeçalhos)
                    if isinstance(data, list) and len(data) > 1 and isinstance(data[0], list):
                        logger.info("Resposta encontrada no formato de matriz (array de arrays)")
                        # Não fazemos conversão aqui, deixamos para os métodos específicos processarem
                        return data
                    
                    # Verificar se a resposta contém dados válidos (outros formatos)
                    if isinstance(data, list):
                        logger.info(f"Requisição bem-sucedida: {len(data)} registros obtidos")
                        # Mostrar amostra dos dados
                        if data and len(data) > 0:
                            sample = data[0]
                            logger.info(f"Amostra do primeiro registro: {json.dumps(sample, indent=2)}")
                        return data
                    elif isinstance(data, dict):
                        # A resposta pode ser um dicionário com uma chave contendo a lista
                        logger.info(f"Resposta contém um dicionário. Chaves: {list(data.keys())}")
                        
                        # Verificar se há uma chave 'result' ou 'data' que contenha os resultados
                        for key in ['result', 'data', 'items', 'deals', 'records']:
                            if key in data and isinstance(data[key], list):
                                logger.info(f"Encontrada lista na chave '{key}' com {len(data[key])} itens")
                                return data[key]
                        
                        # Tentar encontrar qualquer lista dentro do dicionário
                        for key, value in data.items():
                            if isinstance(value, list) and value:
                                logger.info(f"Encontrada lista na chave '{key}' com {len(value)} itens")
                                return value
                        
                        # Se não encontrou nenhuma lista, verificar se o próprio dicionário tem os dados
                        if 'ID' in data or 'id' in data:
                            logger.info("O próprio dicionário parece conter um único registro")
                            return [data]
                        
                        # Se chegou aqui, não encontrou listas úteis no dicionário
                        logger.warning(f"Estrutura de resposta não reconhecida: {data}")
                        return []
                    else:
                        logger.warning(f"Resposta não contém uma lista ou dicionário: {data}")
                        return []
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar resposta JSON: {str(e)}")
                    logger.error(f"Conteúdo da resposta: {response.text[:500]}...")
                    return None
            else:
                logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
                return None
        
        except requests.RequestException as e:
            logger.error(f"Erro de conexão: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_crm_deals(self, start_date, end_date, category_id=34, limit=1000, offset=0):
        """
        Obtém dados da tabela crm_deal com filtros de data e categoria.
        
        Args:
            start_date: Data inicial no formato 'YYYY-MM-DD'
            end_date: Data final no formato 'YYYY-MM-DD'
            category_id: ID da categoria para filtrar (padrão: 34)
            limit: Limite de registros a retornar (padrão: 1000)
            offset: Offset para paginação (padrão: 0)
            
        Returns:
            DataFrame com os dados ou um DataFrame vazio em caso de erro
        """
        # Formato de consulta baseado no exemplo fornecido
        query_params = {
            "dateRange": {
                "startDate": start_date,
                "endDate": end_date
            },
            "configParams": {
                "timeFilterColumn": "DATE_CREATE"
            },
            "dimensionsFilters": [
                [
                    {
                        "fieldName": "CATEGORY_ID",
                        "values": [category_id],
                        "type": "INCLUDE",
                        "operator": "EQUALS"
                    }
                ]
            ],
            "fields": [
                { "name": "ID" },
                { "name": "DATE_CREATE" },
                { "name": "DATE_MODIFY" },
                { "name": "CLOSEDATE" },
                { "name": "TITLE" },
                { "name": "STAGE_NAME" },
                { "name": "ASSIGNED_BY_NAME" }
            ],
            "limit": limit,
            "offset": offset
        }
        
        try:
            # Fazer a requisição à API
            logger.info(f"Buscando deals no período {start_date} a {end_date}, categoria {category_id}")
            response = self._make_request("crm_deal", query_params)
            
            # Se não obteve resposta, tentar um formato alternativo
            if not response:
                logger.warning("Formato principal falhou. Tentando formato alternativo...")
                alt_query_params = {
                    "filter": {
                        ">=DATE_CREATE": start_date,
                        "<=DATE_CREATE": end_date,
                        "CATEGORY_ID": category_id
                    },
                    "select": ["ID", "DATE_CREATE", "DATE_MODIFY", "CLOSEDATE", 
                              "TITLE", "STAGE_NAME", "ASSIGNED_BY_NAME"],
                    "limit": limit,
                    "start": offset
                }
                
                response = self._make_request("crm_deal", alt_query_params)
                
                # Se o formato alternativo também falhou, tentar um terceiro formato
                if not response:
                    logger.warning("Formato alternativo também falhou. Tentando terceiro formato...")
                    third_query_params = {
                        "select": ["ID", "DATE_CREATE", "DATE_MODIFY", "CLOSEDATE", 
                                  "TITLE", "STAGE_NAME", "ASSIGNED_BY_NAME"],
                        "filter": [
                            ["CATEGORY_ID", "=", category_id],
                            [">=DATE_CREATE", start_date],
                            ["<=DATE_CREATE", end_date]
                        ],
                        "limit": limit,
                        "offset": offset
                    }
                    
                    response = self._make_request("crm_deal", third_query_params)
            
            if not response:
                logger.warning("Nenhum dado retornado pela API do Bitrix24 após múltiplas tentativas")
                return pd.DataFrame()
            
            # Processar resposta em formato de matriz (array de arrays)
            if isinstance(response, list) and len(response) > 1:
                # Verificar se parece com matriz (primeiro elemento também é lista)
                if isinstance(response[0], list):
                    logger.info("Resposta encontrada no formato de matriz (array de arrays)")
                    headers = response[0]  # Primeiro array são os cabeçalhos
                    data = response[1:]    # Restante são os dados
                    
                    # Converter para lista de dicionários
                    records = []
                    for row in data:
                        if len(row) == len(headers):
                            record = dict(zip(headers, row))
                            records.append(record)
                    
                    logger.info(f"Convertido com sucesso para {len(records)} registros com {len(headers)} colunas")
                    return pd.DataFrame(records)
            
            # Converter para DataFrame (caso seja outro formato)
            logger.info(f"Dados obtidos com sucesso: {len(response)} registros")
            return pd.DataFrame(response)
            
        except Exception as e:
            logger.error(f"Erro ao obter dados da tabela crm_deal: {str(e)}")
            return pd.DataFrame()
    
    def get_crm_deal_uf(self, deal_ids):
        """
        Obtém campos personalizados (UF) para os IDs de negócios especificados.
        
        Args:
            deal_ids: Lista de IDs de negócios para obter campos personalizados
            
        Returns:
            DataFrame com os campos personalizados ou um DataFrame vazio em caso de erro
        """
        if not deal_ids or len(deal_ids) == 0:
            logger.warning("Nenhum ID de negócio fornecido para buscar campos personalizados")
            return pd.DataFrame()
        
        # Limitar a quantidade de IDs para evitar URLs muito longas
        chunk_size = 100
        all_results = []
        
        for i in range(0, len(deal_ids), chunk_size):
            chunk = deal_ids[i:i + chunk_size]
            
            # Formato de consulta baseado no exemplo fornecido, adaptado para crm_deal_uf
            query_params = {
                "dimensionsFilters": [
                    [
                        {
                            "fieldName": "DEAL_ID",
                            "values": chunk,
                            "type": "INCLUDE",
                            "operator": "EQUALS"
                        }
                    ]
                ],
                "fields": [
                    { "name": "DEAL_ID" },
                    { "name": "UF_CRM_1722605592778" }, # LINK_ARVORE
                    { "name": "UF_CRM_1737689240946" }, # REUNIAO
                    { "name": "UF_CRM_1740458137391" }  # DATA_FECHAMENTO
                ],
                "limit": 1000,
                "offset": 0
            }
            
            try:
                logger.info(f"Buscando campos personalizados para {len(chunk)} negócios")
                chunk_result = self._make_request("crm_deal_uf", query_params)
                
                if chunk_result:
                    # Processar resposta em formato de matriz (array de arrays)
                    if isinstance(chunk_result, list) and len(chunk_result) > 1:
                        # Verificar se parece com matriz (primeiro elemento também é lista)
                        if isinstance(chunk_result[0], list):
                            logger.info("Resposta campos personalizados encontrada no formato de matriz")
                            headers = chunk_result[0]  # Primeiro array são os cabeçalhos
                            data = chunk_result[1:]    # Restante são os dados
                            
                            # Converter para lista de dicionários
                            for row in data:
                                if len(row) == len(headers):
                                    record = dict(zip(headers, row))
                                    all_results.append(record)
                            
                            logger.info(f"Convertidos {len(data)} registros de campos personalizados")
                            continue  # Continuar para o próximo chunk
                            
                    # Se não for matriz, adicionar normalmente
                    all_results.extend(chunk_result)
                    logger.info(f"Obtidos {len(chunk_result)} registros de campos personalizados")
                else:
                    logger.warning(f"Nenhum campo personalizado encontrado para o chunk {i//chunk_size + 1}")
                
            except Exception as e:
                logger.error(f"Erro ao obter campos personalizados para o chunk {i//chunk_size + 1}: {str(e)}")
                # Continuar com o próximo chunk em caso de erro
        
        if all_results:
            return pd.DataFrame(all_results)
        else:
            logger.warning("Nenhum campo personalizado encontrado para todos os IDs fornecidos")
            return pd.DataFrame()
    
    def get_combined_data(self, start_date, end_date, category_id=34):
        """
        Combina dados das tabelas crm_deal e crm_deal_uf.
        
        Args:
            start_date: Data inicial no formato 'YYYY-MM-DD'
            end_date: Data final no formato 'YYYY-MM-DD'
            category_id: ID da categoria para filtrar (padrão: 34)
            
        Returns:
            DataFrame combinado ou None em caso de erro
        """
        try:
            # Obter dados da tabela crm_deal
            df_deals = self.get_crm_deals(start_date, end_date, category_id)
            
            # Verificar se temos o campo ID
            if df_deals.empty:
                logger.warning("Nenhum dado encontrado na tabela crm_deal")
                return pd.DataFrame()
                
            if "ID" not in df_deals.columns:
                logger.error("Campo ID não encontrado na tabela crm_deal")
                logger.info(f"Colunas disponíveis: {df_deals.columns.tolist()}")
                # Tentar usar outra coluna como ID, se existir
                if "id" in df_deals.columns:
                    logger.info("Usando coluna 'id' (minúsculo) como ID")
                    df_deals = df_deals.rename(columns={"id": "ID"})
                else:
                    return pd.DataFrame()
            
            # Exibir os primeiros registros para debug
            if not df_deals.empty and len(df_deals) > 0:
                logger.info(f"Primeiros 2 registros da tabela crm_deal: {df_deals.head(2).to_dict('records')}")
            
            # Extrair IDs dos negócios
            deal_ids = df_deals["ID"].tolist()
            
            # Obter dados da tabela crm_deal_uf para esses IDs
            logger.info(f"Buscando campos personalizados para {len(deal_ids)} IDs")
            df_uf = self.get_crm_deal_uf(deal_ids)
            
            if df_uf.empty:
                logger.warning("Nenhum dado encontrado na tabela crm_deal_uf para os IDs fornecidos")
                # Mesmo sem campos personalizados, podemos retornar os deals
                
                # Renomear colunas para manter compatibilidade com o formato atual
                rename_mapping = {
                    "ID": "ID",
                    "DATE_CREATE": "Criado",
                    "DATE_MODIFY": "Modificado",
                    "ASSIGNED_BY_NAME": "Responsável",
                    "STAGE_NAME": "Fase",
                    "TITLE": "TÍTULO"
                }
                
                # Aplicar apenas os renames para colunas que existem
                rename_mapping_filtered = {k: v for k, v in rename_mapping.items() if k in df_deals.columns}
                df_final = df_deals.rename(columns=rename_mapping_filtered)
                
                # Adicionar colunas vazias para os campos personalizados
                df_final["LINK ARVORE DA FAMÍLIA PLATAFORMA"] = ""
                df_final["REUNIÃO"] = ""
                df_final["FECHADO"] = ""
                
                return df_final
            
            # Verificar se existe o campo DEAL_ID
            if "DEAL_ID" not in df_uf.columns:
                logger.error("Campo DEAL_ID não encontrado na tabela crm_deal_uf")
                logger.info(f"Colunas disponíveis em df_uf: {df_uf.columns.tolist()}")
                
                # Tentar usar outra coluna como DEAL_ID, se existir
                deal_id_candidates = ["deal_id", "ID_DEAL", "id_deal", "Deal_ID"]
                for candidate in deal_id_candidates:
                    if candidate in df_uf.columns:
                        logger.info(f"Usando coluna '{candidate}' como DEAL_ID")
                        df_uf = df_uf.rename(columns={candidate: "DEAL_ID"})
                        break
                else:
                    # Se não encontrar, retornar apenas os deals sem os campos personalizados
                    logger.warning("Usando apenas dados da tabela deal sem campos personalizados")
                    rename_mapping = {
                        "ID": "ID",
                        "DATE_CREATE": "Criado",
                        "DATE_MODIFY": "Modificado",
                        "ASSIGNED_BY_NAME": "Responsável",
                        "STAGE_NAME": "Fase",
                        "TITLE": "TÍTULO"
                    }
                    rename_mapping_filtered = {k: v for k, v in rename_mapping.items() if k in df_deals.columns}
                    return df_deals.rename(columns=rename_mapping_filtered)
            
            # Renomear colunas para evitar conflitos
            uf_rename = {
                "UF_CRM_1722605592778": "LINK_ARVORE",
                "UF_CRM_1737689240946": "REUNIAO",
                "UF_CRM_1740458137391": "DATA_FECHAMENTO"
            }
            
            # Aplicar apenas renomeações para colunas que existem
            uf_rename_filtered = {k: v for k, v in uf_rename.items() if k in df_uf.columns}
            if uf_rename_filtered:
                df_uf = df_uf.rename(columns=uf_rename_filtered)
            
            # Exibir os primeiros registros dos campos personalizados para debug
            if not df_uf.empty and len(df_uf) > 0:
                logger.info(f"Primeiros 2 registros da tabela crm_deal_uf: {df_uf.head(2).to_dict('records')}")
            
            # Mesclar os DataFrames
            logger.info("Mesclando dados de deals com campos personalizados")
            
            # Garantir que os tipos de dados estejam corretos para o merge
            df_deals["ID"] = df_deals["ID"].astype(str)
            df_uf["DEAL_ID"] = df_uf["DEAL_ID"].astype(str)
            
            df_combined = pd.merge(
                df_deals,
                df_uf,
                left_on="ID",
                right_on="DEAL_ID",
                how="left",
                suffixes=("", "_uf")
            )
            
            logger.info(f"Dados combinados com sucesso: {len(df_combined)} registros")
            
            # Verificar se temos as colunas necessárias no DataFrame combinado
            expected_columns = ["ID", "DATE_CREATE", "DATE_MODIFY", "ASSIGNED_BY_NAME", "STAGE_NAME"]
            missing_columns = [col for col in expected_columns if col not in df_combined.columns]
            
            if missing_columns:
                logger.warning(f"Algumas colunas esperadas não foram encontradas no DataFrame combinado: {missing_columns}")
                logger.info(f"Colunas disponíveis: {df_combined.columns.tolist()}")
            
            # Formatação de datas para facilitar o uso posterior
            for date_col in ["DATE_CREATE", "DATE_MODIFY", "CLOSEDATE", "DATE_CREATE_uf", "CLOSEDATE_uf"]:
                if date_col in df_combined.columns:
                    df_combined[date_col] = pd.to_datetime(df_combined[date_col], errors='coerce')
            
            # Selecionar colunas para o DataFrame final
            columns_to_select = ["ID", "DATE_CREATE", "DATE_MODIFY", "ASSIGNED_BY_NAME", "STAGE_NAME"]
            if "TITLE" in df_combined.columns:
                columns_to_select.append("TITLE")
            
            # Adicionar colunas personalizadas apenas se existirem
            optional_columns = ["LINK_ARVORE", "REUNIAO", "DATA_FECHAMENTO"]
            for col in optional_columns:
                if col in df_combined.columns:
                    columns_to_select.append(col)
                elif f"{col}_uf" in df_combined.columns:
                    # Se estiver com sufixo _uf, também adicionar
                    columns_to_select.append(f"{col}_uf")
                else:
                    logger.warning(f"Coluna opcional {col} não encontrada")
            
            # Verificar se temos todas as colunas necessárias antes de criar o dataframe final
            available_cols = [col for col in columns_to_select if col in df_combined.columns]
            if not available_cols:
                logger.error("Nenhuma coluna selecionada está disponível no DataFrame combinado")
                return df_combined  # Retornar o DataFrame combinado completo como fallback
            
            # Criar dataframe somente com as colunas selecionadas
            df_final = df_combined[available_cols].copy()
            
            # Renomear colunas para manter compatibilidade com o formato atual
            rename_mapping = {
                "ID": "ID",
                "DATE_CREATE": "Criado",
                "DATE_MODIFY": "Modificado",
                "ASSIGNED_BY_NAME": "Responsável",
                "STAGE_NAME": "Fase",
                "TITLE": "TÍTULO",
                "LINK_ARVORE": "LINK ARVORE DA FAMÍLIA PLATAFORMA",
                "REUNIAO": "REUNIÃO",
                "DATA_FECHAMENTO": "FECHADO",
                "LINK_ARVORE_uf": "LINK ARVORE DA FAMÍLIA PLATAFORMA",
                "REUNIAO_uf": "REUNIÃO",
                "DATA_FECHAMENTO_uf": "FECHADO"
            }
            
            # Aplicar apenas os renames para colunas que existem
            rename_mapping_filtered = {k: v for k, v in rename_mapping.items() if k in df_final.columns}
            df_final = df_final.rename(columns=rename_mapping_filtered)
            
            # Formatar datas para string no formato DD/MM/YYYY HH:MM:SS
            for col in ["Criado", "Modificado"]:
                if col in df_final.columns and df_final[col].dtype == 'datetime64[ns]':
                    df_final[col] = df_final[col].dt.strftime("%d/%m/%Y %H:%M:%S")
            
            # Garantir que todas as colunas essenciais existam
            essential_columns = ["ID", "Responsável", "Fase"]
            for col in essential_columns:
                if col not in df_final.columns:
                    df_final[col] = ""  # Adicionar coluna vazia se não existir
            
            return df_final
            
        except Exception as e:
            logger.error(f"Erro ao combinar dados: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro 