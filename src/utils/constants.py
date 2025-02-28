"""Constantes utilizadas no projeto"""

# Opções de pagamento
PAYMENT_OPTIONS = {
    'A': 'Pagamento no momento do protocolo junto ao tribunal competente',
    'B': 'Incorporação da taxa ao parcelamento do contrato vigente',
    'C': 'Pagamento flexível com entrada reduzida e saldo postergado',
    'D': 'Parcelamento em até 24 vezes fixas',
    'E': 'Cancelar',
    'F': 'Pagamento no momento do deferimento junto ao tribunal competente',
    'Y': 'Pagamento com desconto para grupos',
    'Z': 'Análise especial',
    'Condicao_Especial': 'Família em condição especial'
}

# Cores para cada opção de pagamento
PAYMENT_OPTIONS_COLORS = {
    'A': '#4CAF50',  # Verde
    'B': '#2196F3',  # Azul
    'C': '#9C27B0',  # Roxo
    'D': '#FF9800',  # Laranja
    'E': '#F44336',  # Vermelho
    'F': '#795548',  # Marrom
    'Y': '#009688',  # Verde-azulado
    'Z': '#607D8B',  # Cinza azulado
    'Condicao_Especial': '#E91E63'  # Rosa
}

# Cores do tema (Itália e União Europeia)
THEME_COLORS = {
    "verde": "#008C45",      # Verde Itália
    "branco": "#FFFFFF",     # Branco
    "vermelho": "#CD212A",   # Vermelho Itália
    "azul": "#003399",       # Azul UE
    "azul_claro": "#4267b2", # Azul secundário
    "cinza": "#F5F7FA",      # Fundo
    "texto": "#1E3A8A"       # Texto principal
}

# Configurações do banco de dados
DATABASE_CONFIG = {
    'host': 'database-1.cdqa6ywqs8pz.us-west-2.rds.amazonaws.com',
    'port': 3306,
    'database': 'whatsapp_euna_data',
    'user': 'lucas',
    'password': 'a9!o98Q80$MM',
    'connection_timeout': 60  # Aumentando o timeout para evitar perda de conexão
}

# Configurações do Bitrix24
BITRIX_CONFIG = {
    'base_url': 'https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php',
    'token': '0z1rgUWgNbR0e53G7T88D9A1gkDWGly7br',
    'timeout': 30,
    'max_retries': 3
}

# Cache TTL em segundos
CACHE_TTL = 300  # 5 minutos