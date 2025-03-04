import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataProcessor")

class DataProcessor:
    """
    Classe responsável pelo processamento dos dados extraídos do Bitrix24.
    Aplica transformações, limpeza e formatação dos dados.
    """
    
    @staticmethod
    def extract_meeting_details(df):
        """
        Extrai detalhes de reunião do campo 'REUNIÃO'.
        O formato esperado é: "DD/MM/YYYY, de HH:MM até HH:MM: DESCRIÇÃO, RESPONSÁVEL"
        
        Args:
            df: DataFrame com os dados extraídos
            
        Returns:
            DataFrame com colunas adicionais para data, hora e responsável da reunião
        """
        if 'REUNIÃO' not in df.columns:
            logger.warning("Coluna 'REUNIÃO' não encontrada no DataFrame")
            return df
        
        # Criar uma cópia para não modificar o original
        df_result = df.copy()
        
        # Extrair data, hora e responsável da reunião
        def extract_info(meeting_str):
            if not isinstance(meeting_str, str) or not meeting_str:
                return pd.Series([None, None, None], index=['data_reuniao', 'hora_reuniao', 'responsavel_reuniao'])
            
            # Padrão: "DD/MM/YYYY, de HH:MM até HH:MM: DESCRIÇÃO, RESPONSÁVEL"
            # Ou: "hoje/amanhã, de HH:MM até HH:MM: DESCRIÇÃO, RESPONSÁVEL"
            
            # Primeiro, tentar extrair a data
            date_match = re.search(r'(\d{2}/\d{2}/\d{4}|\bamanhã\b|\bhoje\b)', meeting_str)
            date = date_match.group(1) if date_match else None
            
            # Converter "hoje" e "amanhã" para datas reais
            if date == 'hoje':
                date = datetime.now().strftime('%d/%m/%Y')
            elif date == 'amanhã':
                date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
            
            # Extrair hora
            time_match = re.search(r'de\s+(\d{2}:\d{2})\s+até', meeting_str)
            time = time_match.group(1) if time_match else None
            
            # Extrair responsável
            resp_match = re.search(r'(?:REUNIÃO|:)\s*,\s*([^,]+)$', meeting_str)
            responsible = resp_match.group(1).strip() if resp_match else None
            
            return pd.Series([date, time, responsible], index=['data_reuniao', 'hora_reuniao', 'responsavel_reuniao'])
        
        # Aplicar a função em todas as linhas
        extracted_info = df_result['REUNIÃO'].apply(extract_info)
        
        # Adicionar as novas colunas ao DataFrame
        df_result = pd.concat([df_result, extracted_info], axis=1)
        
        logger.info("Extração de detalhes de reunião concluída")
        return df_result
    
    @staticmethod
    def clean_link_data(df):
        """
        Limpa e padroniza os dados da coluna 'LINK ARVORE DA FAMÍLIA PLATAFORMA'.
        
        Args:
            df: DataFrame com os dados extraídos
            
        Returns:
            DataFrame com a coluna de link limpa
        """
        if 'LINK ARVORE DA FAMÍLIA PLATAFORMA' not in df.columns:
            logger.warning("Coluna 'LINK ARVORE DA FAMÍLIA PLATAFORMA' não encontrada no DataFrame")
            return df
        
        # Criar uma cópia para não modificar o original
        df_result = df.copy()
        
        # Limpar links vazios ou inválidos
        df_result['LINK ARVORE DA FAMÍLIA PLATAFORMA'] = df_result['LINK ARVORE DA FAMÍLIA PLATAFORMA'].apply(
            lambda x: x if isinstance(x, str) and len(x) > 5 else ""
        )
        
        # Identificar links duplicados
        link_counts = df_result['LINK ARVORE DA FAMÍLIA PLATAFORMA'].value_counts()
        duplicated_links = link_counts[link_counts > 1].index.tolist()
        duplicated_links = [link for link in duplicated_links if link]  # Remover links vazios
        
        # Marcar links duplicados
        df_result['link_duplicado'] = df_result['LINK ARVORE DA FAMÍLIA PLATAFORMA'].apply(
            lambda x: True if x in duplicated_links else False
        )
        
        logger.info(f"Identificados {len(duplicated_links)} links duplicados")
        return df_result
    
    @staticmethod
    def create_stage_categories(df):
        """
        Categoriza as fases em grupos lógicos para análise.
        
        Args:
            df: DataFrame com os dados extraídos
            
        Returns:
            DataFrame com coluna adicional de categoria de fase
        """
        if 'Fase' not in df.columns:
            logger.warning("Coluna 'Fase' não encontrada no DataFrame")
            return df
        
        # Criar uma cópia para não modificar o original
        df_result = df.copy()
        
        # Definir categorias de fases
        assinatura_fases = ['ASSINADO', 'EM ASSINATURA', 'VALIDADO ENVIAR FINANCEIRO']
        negociacao_fases = ['EM NEGOCIAÇÃO', 'ORÇAMENTO', 'REUNIÃO REALIZADA', 'VALIDANDO ADENDO', 'CRIAR ADENDO']
        reuniao_fases = ['REUNIÃO AGENDADA']
        fechamento_fases = ['VALIDADO ENVIAR FINANCEIRO', 'ASSINADO']
        
        # Criar categorias
        df_result['categoria_fase'] = 'Outros'
        df_result.loc[df_result['Fase'].isin(assinatura_fases), 'categoria_fase'] = 'Assinatura'
        df_result.loc[df_result['Fase'].isin(negociacao_fases), 'categoria_fase'] = 'Negociação'
        df_result.loc[df_result['Fase'].isin(reuniao_fases), 'categoria_fase'] = 'Reunião'
        
        # Criar flag de fechamento
        df_result['tem_fechamento'] = df_result['FECHADO'].apply(lambda x: False if pd.isna(x) or x == '' else True)
        
        # Identificar registros em fases de fechamento
        df_result['fase_fechamento'] = df_result['Fase'].isin(fechamento_fases)
        
        logger.info("Categorização de fases concluída")
        return df_result
    
    @staticmethod
    def add_time_metrics(df):
        """
        Adiciona métricas de tempo como tempo em cada fase, etc.
        
        Args:
            df: DataFrame com os dados extraídos
            
        Returns:
            DataFrame com métricas de tempo adicionadas
        """
        if not all(col in df.columns for col in ['Criado', 'Modificado', 'FECHADO']):
            logger.warning("Colunas necessárias para métricas de tempo não encontradas")
            return df
        
        # Criar uma cópia para não modificar o original
        df_result = df.copy()
        
        # Converter colunas para datetime se ainda não estiverem
        for col in ['Criado', 'Modificado']:
            if df_result[col].dtype != 'datetime64[ns]':
                df_result[col] = pd.to_datetime(df_result[col], errors='coerce')
        
        # Converter FECHADO para datetime, tratando valores vazios
        df_result['FECHADO_dt'] = pd.to_datetime(df_result['FECHADO'], errors='coerce')
        
        # Calcular tempo desde a criação até agora (para negócios em andamento)
        now = datetime.now()
        df_result['dias_aberto'] = (now - df_result['Criado']).dt.total_seconds() / (24 * 3600)
        
        # Calcular tempo até o fechamento (para negócios fechados)
        mask_fechados = ~df_result['FECHADO_dt'].isna()
        df_result.loc[mask_fechados, 'dias_ate_fechamento'] = (
            df_result.loc[mask_fechados, 'FECHADO_dt'] - 
            df_result.loc[mask_fechados, 'Criado']
        ).dt.total_seconds() / (24 * 3600)
        
        # Arredondar para facilitar a leitura
        for col in ['dias_aberto', 'dias_ate_fechamento']:
            if col in df_result.columns:
                df_result[col] = df_result[col].round(1)
        
        logger.info("Adição de métricas de tempo concluída")
        return df_result
    
    @staticmethod
    def process_data(df):
        """
        Aplica todas as transformações necessárias aos dados.
        
        Args:
            df: DataFrame com os dados brutos extraídos do Bitrix24
            
        Returns:
            DataFrame processado e pronto para análise
        """
        if df.empty:
            logger.warning("DataFrame vazio, nenhum processamento será aplicado")
            return df
        
        logger.info("Iniciando processamento completo dos dados")
        
        # Aplicar todas as transformações em sequência
        df = DataProcessor.extract_meeting_details(df)
        df = DataProcessor.clean_link_data(df)
        df = DataProcessor.create_stage_categories(df)
        df = DataProcessor.add_time_metrics(df)
        
        logger.info("Processamento completo dos dados concluído")
        return df 