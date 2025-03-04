import os
from pathlib import Path

# Configurações do Bitrix24
BITRIX_BASE_URL = os.environ.get("BITRIX_BASE_URL", "https://g7assessoriaprevidenciaria.bitrix24.com.br/bitrix/tools/biconnector/pbi.php")
BITRIX_TOKEN = os.environ.get("BITRIX_TOKEN", "")  # Token deve ser configurado no ambiente ou .env

# ID da categoria de negócios no CRM
BITRIX_CATEGORY_ID = 34  # Categoria padrão para consulta

# Configurações de dados
DEFAULT_DATA_DAYS = 90  # Número de dias de dados a serem carregados
CACHE_DURATION_HOURS = 12  # Duração do cache em horas

# Caminhos para arquivos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "outputs"
BACKUP_DIR = BASE_DIR / "backups"

# Configurações de campo personalizado do Bitrix24
CUSTOM_FIELDS = {
    "LINK_ARVORE": "UF_CRM_1722605592778",
    "REUNIAO": "UF_CRM_1737689240946",
    "DATA_FECHAMENTO": "UF_CRM_1740458137391"
}

# Mapeamento de colunas para padronização
COLUMN_MAPPING = {
    "ID": "ID",
    "LINK_ARVORE": "LINK ARVORE DA FAMÍLIA PLATAFORMA",
    "ASSIGNED_BY_NAME": "Responsável",
    "STAGE_NAME": "Fase",
    "DATE_CREATE": "Criado",
    "REUNIAO": "REUNIÃO",
    "DATA_FECHAMENTO": "FECHADO",
    "DATE_MODIFY": "Modificado"
}

# Lista de fases para análise
FASES_ASSINATURA = ['ASSINADO', 'EM ASSINATURA', 'VALIDADO ENVIAR FINANCEIRO']
FASES_NEGOCIACAO = ['EM NEGOCIAÇÃO', 'ORÇAMENTO', 'REUNIÃO REALIZADA', 'VALIDANDO ADENDO', 'CRIAR ADENDO']
FASES_REUNIAO = ['REUNIÃO AGENDADA']
FASES_FECHAMENTO = ['VALIDADO ENVIAR FINANCEIRO', 'ASSINADO'] 