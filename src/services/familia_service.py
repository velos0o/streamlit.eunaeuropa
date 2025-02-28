"""Serviço para gerenciar dados das famílias"""
import pandas as pd
from typing import Optional, Dict, Any, Tuple
import streamlit as st
from ..data.database import db
from ..services.bitrix_service import bitrix_service
from datetime import datetime
from ..utils.constants import PAYMENT_OPTIONS, PAYMENT_OPTIONS_COLORS

class FamiliaService:
    """Classe para gerenciar dados das famílias"""

    @staticmethod
    @st.cache_data(ttl=300)
    def get_dashboard_metrics() -> Optional[Dict[str, Any]]:
        """
        Obtém métricas do dashboard a partir da view
        
        Returns:
            Dicionário com as métricas ou None em caso de erro
        """
        query = "SELECT * FROM vw_dashboard_metricas LIMIT 1"
        df = db.execute_query(query)
        
        if df is not None and not df.empty:
            # Converter para dicionário
            metrics = df.iloc[0].to_dict()
            return metrics
        return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_total_requerentes() -> Optional[int]:
        """Obtém o total de requerentes que preencheram o formulário"""
        metrics = FamiliaService.get_dashboard_metrics()
        if metrics:
            return int(metrics['total_requerentes'])
        
        # Fallback para a query original caso a view não funcione
        query = """
        SELECT COUNT(*) as total
        FROM whatsapp_euna_data.euna_familias
        WHERE is_menor = 0
        AND isSpecial = 0 
        AND hasTechnicalProblems = 0
        AND idfamilia IS NOT NULL 
        AND TRIM(idfamilia) != ''
        """
        df = db.execute_query(query)
        if df is not None and not df.empty:
            return int(df['total'].iloc[0])
        return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_familias_status() -> Optional[pd.DataFrame]:
        """
        Obtém o status das famílias com cache
        
        Returns:
            DataFrame com o status das famílias ou None em caso de erro
        """
        # Obter métricas da view
        metrics = FamiliaService.get_dashboard_metrics()
        
        if metrics:
            # Criar DataFrame com os totais
            total_row = {
                'ID_Familia': 'TOTAL',
                'Nome_Familia': 'Total',
                'A': int(metrics['opcao_a']),
                'B': int(metrics['opcao_b']),
                'C': int(metrics['opcao_c']),
                'D': int(metrics['opcao_d']),
                'E': int(metrics['opcao_e']),
                'F': int(metrics['opcao_f']),
                'Y': int(metrics['opcao_y']),
                'Condicao_Especial': int(metrics['condicao_especial']),
                'Requerentes_Continuar': int(metrics['requerentes_continuar']),
                'Requerentes_Cancelar': int(metrics['requerentes_cancelar']),
                'Sem_Opcao': int(metrics['sem_opcao']),
                'Total_Adendos_ID': int(metrics['total_adendos']),
                'Total_Adendos_Familia': int(metrics['familias_com_adendos']),
                'Requerentes_Maiores': int(metrics['total_requerentes']),
                'Requerentes_Menores': 0,  # Não temos essa informação na view
                'Total_Banco': int(metrics['total_requerentes'])
            }
            
            # Consulta para obter detalhes por família
            query_familias = """
            WITH FamiliaMetrics AS (
                SELECT 
                    e.idfamilia AS ID_Familia,
                    COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
                    SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
                    SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
                    SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
                    SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
                    SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
                    SUM(CASE WHEN e.paymentOption = 'F' THEN 1 ELSE 0 END) AS F,
                    SUM(CASE WHEN e.paymentOption = 'Y' THEN 1 ELSE 0 END) AS Y,
                    SUM(CASE WHEN e.specialConditionFamily = 1 THEN 1 ELSE 0 END) AS Condicao_Especial,
                    SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F','Y') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
                    SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
                    SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
                    COUNT(DISTINCT CASE WHEN e.lastEventsUpdate IS NOT NULL AND e.lastEventsUpdate != '' THEN e.id END) AS Total_Adendos_ID,
                    1 AS Total_Adendos_Familia,
                    COUNT(DISTINCT e.id) AS Requerentes_Maiores,
                    0 AS Requerentes_Menores,
                    COUNT(DISTINCT e.id) AS Total_Banco
                FROM whatsapp_euna_data.euna_familias e
                LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
                WHERE e.is_menor = 0 
                AND e.isSpecial = 0 
                AND e.hasTechnicalProblems = 0
                GROUP BY e.idfamilia, f.nome_familia
            )
            SELECT * FROM FamiliaMetrics
            ORDER BY Nome_Familia
            """
            
            df_familias = db.execute_query(query_familias)
            
            if df_familias is not None and not df_familias.empty:
                # Adicionar linha de totais
                df_totals = pd.DataFrame([total_row])
                df_status = pd.concat([df_familias, df_totals], ignore_index=True)
                return df_status
            
            # Se não conseguir obter detalhes por família, retorna apenas os totais
            return pd.DataFrame([total_row])
        
        # Fallback para a query original caso a view não funcione
        query = """
        WITH AdendoMetrics AS (
            SELECT 
                COUNT(DISTINCT CASE 
                    WHEN lastEventsUpdate IS NOT NULL 
                    AND lastEventsUpdate != ''
                    AND is_menor = 0
                    THEN id 
                END) as total_adendos_id,
                COUNT(DISTINCT CASE 
                    WHEN lastEventsUpdate IS NOT NULL 
                    AND lastEventsUpdate != ''
                    AND is_menor = 0
                    AND idfamilia IS NOT NULL 
                    AND TRIM(idfamilia) != ''
                    THEN idfamilia 
                END) as total_adendos_familia
            FROM whatsapp_euna_data.euna_familias
            WHERE isSpecial = 0 
            AND hasTechnicalProblems = 0
        ),
        FamiliaDetalhes AS (
            SELECT 
                e.idfamilia AS ID_Familia,
                COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
                SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
                SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
                SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
                SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
                SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
                SUM(CASE WHEN e.paymentOption = 'F' THEN 1 ELSE 0 END) AS F,
                SUM(CASE WHEN e.paymentOption = 'Y' THEN 1 ELSE 0 END) AS Y,
                SUM(CASE WHEN e.specialConditionFamily = 1 THEN 1 ELSE 0 END) AS Condicao_Especial,
                SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F','Y') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
                SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
                SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
                COUNT(DISTINCT e.id) AS Requerentes_Preencheram,
                (SELECT COUNT(DISTINCT unique_id) 
                 FROM whatsapp_euna_data.familiares f2 
                 WHERE f2.familia = e.idfamilia 
                 AND f2.is_conjuge = 0 
                 AND f2.is_italiano = 0
                 AND f2.is_menor = 0) AS Requerentes_Maiores,
                (SELECT COUNT(DISTINCT unique_id) 
                 FROM whatsapp_euna_data.familiares f2 
                 WHERE f2.familia = e.idfamilia 
                 AND f2.is_menor = 1) AS Requerentes_Menores,
                (SELECT COUNT(DISTINCT unique_id) 
                 FROM whatsapp_euna_data.familiares f2 
                 WHERE f2.familia = e.idfamilia) AS Total_Banco
            FROM whatsapp_euna_data.euna_familias e
            LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
            WHERE e.is_menor = 0 
            AND e.isSpecial = 0 
            AND e.hasTechnicalProblems = 0
            GROUP BY e.idfamilia, f.nome_familia
        ),
        TotalGeral AS (
            SELECT 
                'TOTAL' AS ID_Familia,
                'Total' AS Nome_Familia,
                SUM(A) AS A,
                SUM(B) AS B,
                SUM(C) AS C,
                SUM(D) AS D,
                SUM(E) AS E,
                SUM(F) AS F,
                SUM(Y) AS Y,
                SUM(Condicao_Especial) AS Condicao_Especial,
                SUM(Requerentes_Continuar) AS Requerentes_Continuar,
                SUM(Requerentes_Cancelar) AS Requerentes_Cancelar,
                SUM(Sem_Opcao) AS Sem_Opcao,
                SUM(Requerentes_Preencheram) AS Requerentes_Preencheram,
                SUM(Requerentes_Maiores) AS Requerentes_Maiores,
                SUM(Requerentes_Menores) AS Requerentes_Menores,
                SUM(Total_Banco) AS Total_Banco,
                (SELECT total_adendos_id FROM AdendoMetrics) AS Total_Adendos_ID,
                (SELECT total_adendos_familia FROM AdendoMetrics) AS Total_Adendos_Familia
            FROM FamiliaDetalhes
        )
        SELECT * FROM FamiliaDetalhes
        UNION ALL
        SELECT * FROM TotalGeral
        ORDER BY CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END, Nome_Familia
        """
        
        df = db.execute_query(query)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_dados_grafico() -> Optional[pd.DataFrame]:
        """Obtém dados do gráfico com cache"""
        query = """
        SELECT 
            DATE(createdAt) as data,
            HOUR(createdAt) as hora,
            COUNT(DISTINCT id) as total_ids
        FROM whatsapp_euna_data.euna_familias
        WHERE (idfamilia IS NOT NULL AND TRIM(idfamilia) <> '')
        AND (is_menor = 0 OR is_menor IS NULL)
        AND (isSpecial = 0 OR isSpecial IS NULL)
        AND (hasTechnicalProblems = 0 OR hasTechnicalProblems IS NULL)
        GROUP BY DATE(createdAt), HOUR(createdAt)
        ORDER BY data, hora
        """
        
        df = db.execute_query(query)
        
        # Garantir que os dados estão no formato correto
        if df is not None and not df.empty:
            # Converter a coluna 'data' para datetime se for string
            if df['data'].dtype == 'object':
                df['data'] = pd.to_datetime(df['data'])
            
            # Garantir que 'hora' é um inteiro
            df['hora'] = df['hora'].astype(int)
            
            # Garantir que 'total_ids' é um inteiro
            df['total_ids'] = df['total_ids'].astype(int)
        
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_option_details(option: str) -> pd.DataFrame:
        """Busca detalhes de uma opção de pagamento"""
        if option == 'Condicao_Especial':
            query = """
            SELECT 
                e.idfamilia,
                e.nome_completo,
                e.telefone,
                f.nome_familia,
                e.paymentOption,
                e.createdAt
            FROM whatsapp_euna_data.euna_familias e
            LEFT JOIN whatsapp_euna_data.familias f 
                ON TRIM(e.idfamilia) = TRIM(f.unique_id)
            WHERE e.specialConditionFamily = 1
            AND e.is_menor = 0 
            AND e.isSpecial = 0 
            AND e.hasTechnicalProblems = 0
            ORDER BY e.createdAt DESC
            """
            df = db.execute_query(query)
        else:
            query = """
            SELECT 
                e.idfamilia,
                e.nome_completo,
                e.telefone,
                f.nome_familia,
                e.paymentOption,
                e.createdAt
            FROM whatsapp_euna_data.euna_familias e
            LEFT JOIN whatsapp_euna_data.familias f 
                ON TRIM(e.idfamilia) = TRIM(f.unique_id)
            WHERE e.paymentOption = %s
            AND e.is_menor = 0 
            AND e.isSpecial = 0 
            AND e.hasTechnicalProblems = 0
            ORDER BY e.createdAt DESC
            """
            df = db.execute_query(query, params=[option])
        
        if df is not None and not df.empty:
            # Formatar datas
            df['createdAt'] = pd.to_datetime(df['createdAt']).dt.strftime('%d/%m/%Y %H:%M')
        else:
            # Criar DataFrame vazio com as colunas necessárias
            df = pd.DataFrame(columns=[
                'idfamilia', 'nome_completo', 'telefone', 'nome_familia', 'paymentOption', 'createdAt'
            ])
            
        return df

    def clear_cache(self):
        """Limpa o cache do serviço"""
        st.cache_data.clear()

# Instância global do serviço
familia_service = FamiliaService()