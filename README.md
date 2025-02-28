# Dashboard de Análise por Responsável - Sistema Estável

Este dashboard fornece uma análise detalhada dos dados por responsável, com ênfase em estabilidade e monitoramento de performance.

## Melhorias de Estabilidade Implementadas

### 1. Carregamento de Dados Robusto
- Implementação de múltiplas tentativas de carregamento com diferentes configurações
- Tratamento adequado do BOM UTF-8 (`encoding='utf-8-sig'`)
- Limpeza automática de nomes de colunas (remoção de aspas)
- Limitação de registros (100 linhas) para garantir desempenho

### 2. Monitoramento Avançado
- Thread dedicada para monitoramento contínuo do uso de recursos
- Métricas de memória, CPU e tempo de execução
- Registros detalhados de operações e possíveis erros
- Script de monitoramento externo (`monitor_streamlit.py`) para verificação de saúde

### 3. Sistema de Recuperação
- Reinicialização automática em caso de falhas (até 3 tentativas)
- Coleta de lixo periódica para evitar vazamentos de memória
- Degradação graciosa em caso de erros (alternativas de visualização simplificadas)
- Diagnóstico detalhado para facilitar a identificação de problemas

### 4. Interface Otimizada
- Dashboard organizado em abas (Métricas, Dados Detalhados, Diagnóstico)
- Limitação de dados exibidos para evitar sobrecarga
- Filtros de dados para análises específicas
- Indicadores visuais de status do sistema

## Como Usar

1. **Iniciar o Dashboard**:
   ```
   python -m streamlit run app.py
   ```

2. **Monitorar a Saúde do Sistema**:
   ```
   python monitor_streamlit.py
   ```
   O script de monitoramento verificará automaticamente a cada 30 segundos se o servidor está respondendo e tentará reiniciá-lo caso necessário.

3. **Acessar o Dashboard**:
   - Acesse no navegador: http://localhost:8503
   - Selecione "Análise Responsável" no menu lateral

## Logs e Diagnóstico

- **Logs do Dashboard**: `dashboard_responsavel.log`
- **Logs de Monitoramento**: `streamlit_monitor.log`
- **Erros Detalhados**: `error_log.txt`
- **Checkpoints**: `last_successful_render.txt`

## Requisitos

- Python 3.7+
- Streamlit
- Pandas
- psutil
- requests

## Solução de Problemas

Se encontrar problemas com o dashboard:

1. Verifique a aba "Diagnóstico" para informações sobre o estado do sistema
2. Consulte os arquivos de log para detalhes sobre erros
3. Reinicie o servidor manualmente se necessário
4. Ajuste o valor `MAX_ROWS` em `src/ui/streamlit/responsavel_dashboard.py` se o carregamento de dados for muito lento