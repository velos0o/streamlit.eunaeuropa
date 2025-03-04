import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os

from .bitrix_connector import BitrixConnector
from .data_processor import DataProcessor
from .data_repository import DataRepository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BitrixIntegration")

class BitrixIntegration:
    """
    Classe de integração que unifica as funcionalidades de extração,
    processamento e armazenamento de dados do Bitrix24.
    """
    
    def __init__(
        self,
        base_url=None,
        token=None,
        cache_dir="./cache",
        cache_duration=12
    ):
        """
        Inicializa a integração com o Bitrix24.
        
        Args:
            base_url: URL base da API do Bitrix24 ou None para usar variável de ambiente
            token: Token de autenticação ou None para usar variável de ambiente
            cache_dir: Diretório onde os dados em cache serão armazenados
            cache_duration: Duração do cache em horas
        """
        # Inicializar componentes
        self.connector = BitrixConnector(base_url, token)
        self.repository = DataRepository(cache_dir, cache_duration)
        
        logger.info("BitrixIntegration inicializada")
    
    def get_data(
        self,
        start_date=None,
        end_date=None,
        category_id=34,
        use_cache=True,
        force_refresh=False,
        process_data=True
    ):
        """
        Obtém e processa dados do Bitrix24, com suporte a cache.
        
        Args:
            start_date: Data inicial no formato 'YYYY-MM-DD' ou None para 3 meses atrás
            end_date: Data final no formato 'YYYY-MM-DD' ou None para data atual
            category_id: ID da categoria para filtrar (padrão: 34)
            use_cache: Se True, tenta usar dados em cache primeiro
            force_refresh: Se True, ignora o cache e busca dados novos
            process_data: Se True, aplica processamento aos dados brutos
            
        Returns:
            DataFrame com os dados obtidos e processados
        """
        # Definir datas padrão se não fornecidas
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Gerar chave de cache
        cache_key = self.repository.generate_cache_key(
            "bitrix_data",
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            processed=process_data
        )
        
        # Tentar carregar do cache se permitido
        if use_cache and not force_refresh:
            cached_data = self.repository.load_from_cache(cache_key)
            if cached_data is not None:
                logger.info(f"Dados carregados do cache para o período {start_date} a {end_date}")
                return cached_data
        
        # Se não houver cache ou force_refresh=True, buscar dados novos
        logger.info(f"Buscando novos dados para o período {start_date} a {end_date}")
        df = self.connector.get_combined_data(start_date, end_date, category_id)
        
        # Aplicar processamento se solicitado
        if process_data and not df.empty:
            logger.info("Aplicando processamento aos dados")
            df = DataProcessor.process_data(df)
        
        # Salvar em cache para uso futuro
        if use_cache and not df.empty:
            self.repository.save_to_cache(df, cache_key)
        
        return df
    
    def export_to_csv(self, data, output_path=None):
        """
        Exporta os dados para um arquivo CSV.
        
        Args:
            data: DataFrame a ser exportado
            output_path: Caminho para salvar o arquivo ou None para usar caminho padrão
            
        Returns:
            str: Caminho do arquivo exportado ou None em caso de erro
        """
        if output_path is None:
            output_dir = Path("./outputs")
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d")
            output_path = output_dir / f"bitrix_data_{timestamp}.csv"
        
        success = self.repository.export_data(data, output_path, format="csv")
        return str(output_path) if success else None
    
    def backup_current_data(self, description=None):
        """
        Cria um backup dos dados atuais.
        
        Args:
            description: Descrição opcional para o backup
            
        Returns:
            str: Caminho do arquivo de backup ou None em caso de erro
        """
        # Obter dados atuais (últimos 3 meses)
        data = self.get_data(use_cache=True)
        
        if data is None or data.empty:
            logger.warning("Nenhum dado disponível para backup")
            return None
        
        # Definir descrição padrão se não fornecida
        if not description:
            description = f"bitrix_backup_{datetime.now().strftime('%Y%m%d')}"
        
        # Criar backup
        return self.repository.backup_data(data, description)
    
    def refresh_data(self, days_to_load=90):
        """
        Atualiza o cache de dados, buscando dados novos.
        
        Args:
            days_to_load: Número de dias no passado para carregar
            
        Returns:
            DataFrame com os dados atualizados
        """
        start_date = (datetime.now() - timedelta(days=days_to_load)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Atualizando dados para o período {start_date} a {end_date}")
        return self.get_data(
            start_date=start_date,
            end_date=end_date,
            force_refresh=True
        )
    
    def get_csv_path(self):
        """
        Retorna o caminho para o arquivo CSV mais recente com dados do Bitrix.
        Se o arquivo não existir ou estiver desatualizado, cria um novo.
        
        Returns:
            str: Caminho do arquivo CSV
        """
        output_dir = Path("./outputs")
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verificar se já existe um arquivo CSV do dia atual
        today = datetime.now().strftime("%Y%m%d")
        csv_path = output_dir / f"bitrix_data_{today}.csv"
        
        if csv_path.exists():
            # Verificar se o arquivo é recente (menos de 1 hora)
            file_time = datetime.fromtimestamp(os.path.getmtime(csv_path))
            if datetime.now() - file_time < timedelta(hours=1):
                logger.info(f"Usando arquivo CSV existente: {csv_path}")
                return str(csv_path)
        
        # Se não existir ou estiver desatualizado, criar um novo
        logger.info("Criando novo arquivo CSV com dados atualizados")
        data = self.refresh_data()
        if data is not None and not data.empty:
            self.export_to_csv(data, csv_path)
            return str(csv_path)
        
        return None 