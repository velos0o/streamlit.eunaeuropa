# Dashboard de Análise de Negociações do Bitrix24

Um dashboard interativo para análise de negociações do Bitrix24, desenvolvido com Streamlit. Este projeto permite visualizar e analisar dados de negócios, responsáveis e funil de vendas.

## Funcionalidades

- **Análise do Funil**: Visualização do funil de negociações por fase e responsável
- **Análise de Duplicados**: Identificação de links duplicados para evitar duplicação de esforços
- **Cards sem Modificação**: Monitoramento de negócios que não são atualizados há muito tempo
- **Múltiplas Fontes de Dados**: Suporte para extração de dados diretamente da API do Bitrix24 ou via arquivo CSV

## Nova Arquitetura

O projeto foi reestruturado para suportar a extração de dados diretamente da API do Bitrix24, oferecendo mais flexibilidade e dados em tempo real:

```
projeto/
├── src/
│   ├── config/               # Configurações da aplicação
│   │   ├── __init__.py
│   │   └── bitrix_config.py  # Configurações do Bitrix24
│   ├── data/                 # Camada de dados
│   │   ├── __init__.py
│   │   ├── bitrix_connector.py    # Conexão com a API do Bitrix24
│   │   ├── data_processor.py      # Processamento de dados
│   │   ├── data_repository.py     # Cache e persistência
│   │   └── bitrix_integration.py  # Integração unificada
│   └── ui/
│       └── streamlit/        # Interface do usuário
│           └── responsavel_dashboard.py # Dashboard principal
├── cache/                    # Cache de dados
├── outputs/                  # Saídas geradas (CSV, Excel, etc.)
├── backups/                  # Backups de dados
└── .env                      # Variáveis de ambiente (não versionado)
```

## Requisitos

- Python 3.8 ou superior
- Pacotes Python listados em `requirements.txt`
- Acesso à API do Bitrix24 (token de acesso)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/bitrix-dashboard.git
   cd bitrix-dashboard
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env`
   - Preencha as configurações do Bitrix24 no arquivo `.env`

## Executando o Dashboard

```bash
streamlit run src/ui/streamlit/responsavel_dashboard.py
```

## Configuração das Fontes de Dados

### Opção 1: API do Bitrix24 (Recomendado)

Para usar a API do Bitrix24, você precisa:
1. Ter um token de acesso válido (`BITRIX_TOKEN`)
2. Configurar a URL base da API (`BITRIX_BASE_URL`)
3. Opcional: Configurar o ID da categoria (`BITRIX_CATEGORY_ID`, default: 34)

Essas configurações podem ser definidas no arquivo `.env`:

```
BITRIX_BASE_URL=https://seudominio.bitrix24.com.br/bitrix/tools/biconnector/pbi.php
BITRIX_TOKEN=seu_token_aqui
BITRIX_CATEGORY_ID=34
```

### Opção 2: Arquivo CSV Local

Você também pode usar um arquivo CSV local com os dados exportados do Bitrix24:

1. Prepare um arquivo CSV com o formato exigido (veja a aba "Upload de Arquivo" no dashboard)
2. Coloque o arquivo como `extratacao_bitrix24.csv` na raiz do projeto ou na pasta `data/`
3. Configure a variável de ambiente `USE_BITRIX_CSV=True` ou selecione "Arquivo CSV local" na interface

## Campos Personalizados

O dashboard está configurado para trabalhar com os seguintes campos personalizados do Bitrix24:

- `UF_CRM_1722605592778`: Link da Árvore da Família
- `UF_CRM_1737689240946`: Campos Reunião
- `UF_CRM_1740458137391`: Data de Fechamento

Você pode personalizar esses campos editando o arquivo `src/config/bitrix_config.py`.

## Cache e Desempenho

Por padrão, os dados extraídos da API são armazenados em cache por 12 horas para melhorar o desempenho. Você pode:

- Alterar a duração do cache através da variável `CACHE_DURATION_HOURS`
- Forçar a atualização dos dados clicando no botão "Atualizar dados do Bitrix24"
- Limpar manualmente o cache excluindo os arquivos na pasta `cache/`

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença

Este projeto está licenciado sob a licença MIT.

## Configuração do Ambiente

Para configurar corretamente o ambiente e garantir o funcionamento do dashboard, siga estas etapas:

1. **Instale as dependências**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure as variáveis de ambiente**:
   - Crie um arquivo `.env` na raiz do projeto baseado no arquivo `.env.example`
   - Preencha as seguintes variáveis obrigatórias:
     ```
     BITRIX_BASE_URL="https://seudominio.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
     BITRIX_TOKEN="seu_token_do_bitrix24"
     BITRIX_CATEGORY_ID=34
     ```

3. **Obtenha um token do Bitrix24**:
   - Acesse o painel de administração do Bitrix24
   - Vá para Aplicativos > Outros > Webhooks/REST API
   - Crie um novo webhook com as permissões necessárias (crm.deal.list, etc.)
   - Copie o token gerado e adicione ao seu arquivo `.env`

4. **Execute a aplicação**:
   ```
   streamlit run app.py
   ```

## Solução de Problemas

- **Erro: "Token do Bitrix24 não configurado"**
  - Verifique se o arquivo `.env` existe na raiz do projeto
  - Certifique-se de que a variável `BITRIX_TOKEN` está configurada corretamente

- **Erro ao carregar dados**
  - Verifique se o URL do Bitrix24 está correto
  - Confirme se o token tem as permissões necessárias para acessar os dados do CRM