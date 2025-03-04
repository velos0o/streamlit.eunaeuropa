import pandas as pd
import os
import json
from datetime import datetime, timedelta
import logging
import pickle
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataRepository")

class DataRepository:
    """
    Classe responsável pelo armazenamento, cache e recuperação de dados.
    Gerencia o ciclo de vida dos dados, incluindo persistência e expiração de cache.
    """
    
    def __init__(self, cache_dir="./cache", cache_duration=12):
        """
        Inicializa o repositório de dados.
        
        Args:
            cache_dir: Diretório onde os dados em cache serão armazenados
            cache_duration: Duração do cache em horas
        """
        self.cache_dir = Path(cache_dir)
        self.cache_duration = cache_duration
        
        # Criar diretório de cache se não existir
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de cache criado: {self.cache_dir}")
    
    def save_to_cache(self, data, cache_key):
        """
        Salva os dados em cache com uma chave específica.
        
        Args:
            data: Dados a serem armazenados em cache (geralmente um DataFrame)
            cache_key: Chave única para identificar os dados em cache
            
        Returns:
            bool: True se os dados foram salvos com sucesso, False caso contrário
        """
        if data is None:
            logger.warning("Tentativa de salvar dados nulos em cache")
            return False
        
        try:
            # Caminho do arquivo de cache
            cache_path = self.cache_dir / f"{cache_key}.pkl"
            
            # Criar estrutura de dados com metadados
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # Salvar usando pickle para preservar tipos de dados do pandas
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Dados salvos em cache: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados em cache: {str(e)}")
            return False
    
    def load_from_cache(self, cache_key):
        """
        Carrega dados do cache se estiverem disponíveis e dentro do prazo de validade.
        
        Args:
            cache_key: Chave única para identificar os dados em cache
            
        Returns:
            Os dados armazenados em cache ou None se não estiverem disponíveis ou expirados
        """
        cache_path = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_path.exists():
            logger.info(f"Cache não encontrado: {cache_key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verificar validade do cache
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            expiration_time = cached_time + timedelta(hours=self.cache_duration)
            
            if datetime.now() > expiration_time:
                logger.info(f"Cache expirado: {cache_key}")
                return None
            
            logger.info(f"Dados carregados do cache: {cache_key}")
            return cache_data["data"]
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do cache: {str(e)}")
            return None
    
    def delete_cache(self, cache_key=None):
        """
        Remove dados específicos do cache ou limpa todo o cache.
        
        Args:
            cache_key: Chave específica para remover ou None para limpar todo o cache
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            if cache_key:
                # Remover um cache específico
                cache_path = self.cache_dir / f"{cache_key}.pkl"
                if cache_path.exists():
                    os.remove(cache_path)
                    logger.info(f"Cache removido: {cache_key}")
                return True
            else:
                # Limpar todo o diretório de cache
                for cache_file in self.cache_dir.glob("*.pkl"):
                    os.remove(cache_file)
                logger.info("Cache limpo completamente")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao remover cache: {str(e)}")
            return False
    
    def export_data(self, data, output_path, format="csv"):
        """
        Exporta os dados para um arquivo.
        
        Args:
            data: Dados a serem exportados (geralmente um DataFrame)
            output_path: Caminho onde o arquivo será salvo
            format: Formato do arquivo (csv, excel, json)
            
        Returns:
            bool: True se os dados foram exportados com sucesso, False caso contrário
        """
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            logger.warning("Tentativa de exportar dados vazios")
            return False
        
        try:
            output_path = Path(output_path)
            
            # Criar diretório se não existir
            output_dir = output_path.parent
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Exportar no formato especificado
            if format.lower() == "csv":
                data.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif format.lower() == "excel":
                data.to_excel(output_path, index=False)
            elif format.lower() == "json":
                if isinstance(data, pd.DataFrame):
                    data_json = data.to_json(orient="records", date_format="iso")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(data_json)
                else:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                logger.error(f"Formato de exportação não suportado: {format}")
                return False
            
            logger.info(f"Dados exportados para {output_path} no formato {format}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            return False
    
    def generate_cache_key(self, prefix, **params):
        """
        Gera uma chave de cache com base nos parâmetros fornecidos.
        
        Args:
            prefix: Prefixo para a chave
            **params: Parâmetros a serem incluídos na chave
            
        Returns:
            str: Chave de cache gerada
        """
        # Ordenar parâmetros para garantir consistência
        param_str = '_'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{prefix}_{param_str}"
    
    def backup_data(self, data, description=""):
        """
        Cria um backup completo dos dados com timestamp.
        
        Args:
            data: Dados a serem armazenados (geralmente um DataFrame)
            description: Descrição opcional do backup
            
        Returns:
            str: Caminho do arquivo de backup ou None em caso de erro
        """
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            logger.warning("Tentativa de backup de dados vazios")
            return None
        
        try:
            # Criar pasta de backups se não existir
            backup_dir = Path("./backups")
            if not backup_dir.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Gerar nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            description = description.replace(" ", "_") if description else "backup"
            backup_path = backup_dir / f"{description}_{timestamp}.pkl"
            
            # Salvar utilizando pickle
            with open(backup_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Backup criado: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}")
            return None 