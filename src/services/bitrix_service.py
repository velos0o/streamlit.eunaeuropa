"""Serviço para gerenciar dados do Bitrix24"""
import pandas as pd
import streamlit as st
import requests
import time
from typing import Optional, Dict, Any, Tuple, List, Union

class BitrixService:
    """Classe para gerenciar dados do Bitrix24"""
    
    # Configurações do Bitrix24
    BITRIX_BASE_URL = "https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
    BITRIX_TOKEN = "0z1rgUWgNbR0e53G7T88D9A1gkDWGly7br"
    
    def consultar_bitrix(self, table: str, filtros: Optional[Dict[str, Any]] = None, 
                         max_retries: int = 3, timeout: int = 30) -> Optional[List[List[Any]]]:
        """
        Função para consultar Bitrix24 com retry e timeout
        
        Args:
            table: Nome da tabela no Bitrix24
            filtros: Filtros para a consulta (opcional)
            max_retries: Número máximo de tentativas
            timeout: Tempo limite em segundos
            
        Returns:
            Dados da consulta ou None em caso de erro
        """
        for attempt in range(max_retries):
            try:
                url = f"{self.BITRIX_BASE_URL}?token={self.BITRIX_TOKEN}&table={table}"
                
                if filtros:
                    response = requests.post(url, json=filtros, timeout=timeout)
                else:
                    response = requests.get(url, timeout=timeout)
                
                response.raise_for_status()
                
                if response.status_code == 200:
                    return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    st.error(f"Timeout ao consultar {table} (tentativa {attempt + 1}/{max_retries})")
                    return None
                st.warning(f"Timeout, tentando novamente... ({attempt + 1}/{max_retries})")
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    st.error(f"Erro ao consultar {table}: {str(e)}")
                    return None
                st.warning(f"Erro, tentando novamente... ({attempt + 1}/{max_retries})")
                time.sleep(1)
        
        return None
    
    @st.cache_data(ttl=300)
    def analisar_deals(_self) -> Optional[Tuple[Dict[str, Union[int, str, float]], pd.DataFrame, pd.DataFrame]]:
        """
        Função para analisar deals do Bitrix24
        
        Returns:
            Tupla com métricas, dataframe de detalhamento e dataframe completo, ou None em caso de erro
        """
        try:
            # 1. Consultar crm_deal (categoria 32 - Negociação de Taxa)
            filtros_deal = {
                "dimensionsFilters": [[
                    {
                        "fieldName": "CATEGORY_ID",
                        "values": [32],
                        "type": "INCLUDE",
                        "operator": "EQUALS"
                    }
                ]],
                "select": [
                    "ID", "TITLE", "DATE_CREATE", "ASSIGNED_BY_NAME", 
                    "STAGE_ID", "STAGE_NAME", "CATEGORY_NAME"
                ]
            }
            
            deals_data = self.consultar_bitrix("crm_deal", filtros_deal)
            
            if not deals_data:
                st.error("Não foi possível obter os dados de negócios")
                return None
            
            # Converter para DataFrame
            deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
            
            if deals_df.empty:
                st.warning("Nenhum negócio encontrado na categoria 32")
                return None
            
            # 2. Consultar crm_deal_uf apenas para os IDs encontrados
            deal_ids = deals_df["ID"].tolist()
            
            filtros_uf = {
                "dimensionsFilters": [[
                    {
                        "fieldName": "DEAL_ID",
                        "values": deal_ids,
                        "type": "INCLUDE",
                        "operator": "EQUALS"
                    }
                ]],
                "select": ["DEAL_ID", "UF_CRM_1738699062493"]
            }
            
            deals_uf_data = self.consultar_bitrix("crm_deal_uf", filtros_uf)
            
            if not deals_uf_data:
                st.error("Não foi possível obter os dados complementares")
                return None
                
            deals_uf_df = pd.DataFrame(deals_uf_data[1:], columns=deals_uf_data[0])
            
            # 3. Mesclar os dataframes
            df_completo = pd.merge(
                deals_df,
                deals_uf_df[["DEAL_ID", "UF_CRM_1738699062493"]],
                left_on="ID",
                right_on="DEAL_ID",
                how="left"
            )
            
            # 4. Calcular métricas
            metricas = {
                "total_negocios": len(df_completo),
                "categoria_name": df_completo["CATEGORY_NAME"].iloc[0] if not df_completo.empty else "N/A",
                "com_conteudo": len(df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != ""]),
                "sem_conteudo": len(df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() == ""]),
                "stage_negociacao": df_completo[df_completo["STAGE_ID"] == "C32:UC_GBPN8V"]["STAGE_NAME"].iloc[0] if not df_completo.empty else "N/A",
                "total_stage_negociacao": len(df_completo[df_completo["STAGE_ID"] == "C32:UC_GBPN8V"]),
                "com_conteudo_em_negociacao": len(df_completo[
                    (df_completo["STAGE_ID"] == "C32:UC_GBPN8V") & 
                    (df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != "")
                ]),
                "com_conteudo_fora_negociacao": len(df_completo[
                    (df_completo["STAGE_ID"] != "C32:UC_GBPN8V") & 
                    (df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != "")
                ])
            }
            
            # 5. Preparar dados detalhados para tabela (apenas com conteúdo)
            detalhamento = []
            for _, row in df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != ""].iterrows():
                detalhamento.append({
                    "ID": row["ID"],
                    "Título": row["TITLE"],
                    "Data Criação": pd.to_datetime(row["DATE_CREATE"]).strftime("%d/%m/%Y"),
                    "Responsável": row["ASSIGNED_BY_NAME"],
                    "Etapa": row["STAGE_NAME"],
                    "Status": "GEROU O LINK"
                })
            
            df_detalhamento = pd.DataFrame(detalhamento)
            
            # Ordenar por ID
            df_detalhamento = df_detalhamento.sort_values(by="ID", ascending=False)
            
            return metricas, df_detalhamento, df_completo
            
        except Exception as e:
            st.error(f"Erro ao analisar dados: {str(e)}")
            return None
    
    def clear_cache(self):
        """Limpa o cache do serviço"""
        st.cache_data.clear()

# Instância global do serviço
bitrix_service = BitrixService()