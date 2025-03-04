"""Módulo para gerenciar conexões com o banco de dados"""
import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st
from typing import Optional, List, Dict, Any, Tuple, Union
from ..utils.constants import DATABASE_CONFIG

class Database:
    """Classe para gerenciar conexões com o banco de dados"""
    
    def __init__(self):
        """Inicializa a classe de banco de dados"""
        self.config = DATABASE_CONFIG
    
    def get_connection(self):
        """
        Cria uma conexão com o banco de dados
        
        Returns:
            Conexão com o banco de dados ou None em caso de erro
        """
        try:
            connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                connection_timeout=self.config.get('connection_timeout', 60),
                use_pure=True,  # Usar implementação pura Python para melhor estabilidade
                autocommit=True,  # Evitar problemas de transação
                buffered=True,    # Evitar problemas de cursor não consumido
                pool_name='euna_pool',  # Nome curto para o pool
                pool_size=5,      # Usar pool de conexões
                pool_reset_session=True  # Resetar sessão ao retornar para o pool
            )
            return connection
        except Error as e:
            st.error(f"Erro ao conectar ao banco de dados: {e}")
            return None
    
    def execute_query(self, query: str, params: Optional[List] = None) -> Optional[pd.DataFrame]:
        """
        Executa uma consulta SQL e retorna os resultados como DataFrame
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta (opcional)
            
        Returns:
            DataFrame com os resultados ou None em caso de erro
        """
        connection = self.get_connection()
        if connection is None:
            return None
        
        try:
            # Definir um timeout maior para consultas complexas
            try:
                connection.cmd_query(f"SET SESSION MAX_EXECUTION_TIME=30000")  # 30 segundos
            except:
                # Ignorar se o comando não for suportado
                pass
            
            # Executar a consulta
            if params:
                df = pd.read_sql(query, connection, params=params)
            else:
                df = pd.read_sql(query, connection)
            
            return df
        except Error as e:
            st.error(f"Erro ao executar query: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    
    def execute_raw_query(self, query: str, params: Optional[Tuple] = None) -> Optional[pd.DataFrame]:
        """
        Executa uma consulta SQL bruta usando cursor
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta (opcional)
            
        Returns:
            DataFrame com os resultados ou None em caso de erro
        """
        connection = self.get_connection()
        if connection is None:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Definir um timeout maior para consultas complexas
            try:
                cursor.execute("SET SESSION MAX_EXECUTION_TIME=30000")  # 30 segundos
            except:
                # Ignorar se o comando não for suportado
                pass
            
            # Executar a consulta
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Obter resultados
            results = cursor.fetchall()
            
            # Converter para DataFrame
            if results:
                df = pd.DataFrame(results)
                return df
            else:
                return pd.DataFrame()
        except Error as e:
            st.error(f"Erro ao executar query: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

# Instância global do banco de dados
db = Database()