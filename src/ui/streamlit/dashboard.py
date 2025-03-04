"""Componente principal do dashboard"""
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time
import io
from ...services.familia_service import familia_service
from ...utils.constants import PAYMENT_OPTIONS, PAYMENT_OPTIONS_COLORS

class Dashboard:
    """Classe para gerenciar a interface do dashboard"""

    @staticmethod
    def show_cache_metrics():
        """Exibe métricas de cache"""
        pass  # Removido pois as métricas agora estão apenas no sidebar

    @staticmethod
    def show_main_metrics(df: pd.DataFrame):
        """Exibe métricas principais"""
        total_row = df[df['Nome_Familia'] == 'Total'].iloc[0]
        total_requerentes = familia_service.get_total_requerentes()
        
        # Métrica principal em destaque
        st.markdown(f"""
            <div class='metric-card super-highlight'>
                <div class='metric-label'>Total de Requerentes</div>
                <div class='metric-value'>{total_requerentes or 0}</div>
                <div class='metric-description'>
                    Total de requerentes maiores de idade que preencheram o formulário
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # Métricas de Adendos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card highlight'>
                    <div class='metric-label'>Total de Adendos</div>
                    <div class='metric-value'>{int(total_row['Total_Adendos_ID'])}</div>
                    <div class='metric-description'>
                        Número de requerentes maiores de idade que iniciaram o processo de adendo
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card highlight'>
                    <div class='metric-label'>Famílias com Adendos</div>
                    <div class='metric-value'>{int(total_row['Total_Adendos_Familia'])}</div>
                    <div class='metric-description'>
                        Quantidade de famílias distintas que possuem requerentes em processo de adendo
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # Demais métricas em linha
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Total de Famílias</div>
                    <div class='metric-value'>{len(df[df['Nome_Familia'] != 'Total'])}</div>
                    <div class='metric-description'>
                        Famílias cadastradas
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Requerentes Continuar</div>
                    <div class='metric-value'>{int(total_row['Requerentes_Continuar'])}</div>
                    <div class='metric-description'>
                        Opções A, B, C, D, F e Z
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Requerentes Cancelar</div>
                    <div class='metric-value'>{int(total_row['Requerentes_Cancelar'])}</div>
                    <div class='metric-description'>
                        Apenas opção E
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Sem Opção</div>
                    <div class='metric-value'>{int(total_row['Sem_Opcao'])}</div>
                    <div class='metric-description'>
                        Aguardando escolha
                    </div>
                </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def show_payment_options(df: pd.DataFrame):
        """Exibe distribuição por opção de pagamento"""
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        st.subheader("Distribuição por Opção de Pagamento")
        
        total_row = df[df['Nome_Familia'] == 'Total'].iloc[0]
        total_requerentes = total_row['Total_Banco']
        
        # Criar colunas para cada opção
        opcoes = ['A', 'B', 'C', 'D', 'E', 'F', 'Y', 'Condicao_Especial']
        num_colunas = len(opcoes)
        colunas = st.columns(num_colunas)
        
        for i, (opcao, col) in enumerate(zip(opcoes, colunas)):
            with col:
                valor = total_row[opcao]
                percentual = (valor / total_requerentes * 100) if total_requerentes > 0 else 0
                
                # Obter descrição e cor da opção
                descricao = PAYMENT_OPTIONS.get(opcao, "Desconhecida")
                cor = PAYMENT_OPTIONS_COLORS.get(opcao, "#CCCCCC")
                
                # Criar card com cor personalizada
                st.markdown(f"""
                    <div class='metric-card' style='border-left: 4px solid {cor};'>
                        <div class='metric-label'>Opção {opcao}</div>
                        <div class='metric-value' style='color: {cor};'>{int(valor)}</div>
                        <div class='metric-description' title="{descricao}">
                            {descricao[:30]}...
                        </div>
                        <div class='metric-percentage'>
                            {percentual:.1f}% do total
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    @staticmethod
    def show_timeline_chart(df: pd.DataFrame):
        """Exibe gráfico de evolução temporal"""
        st.subheader("Evolução do Preenchimento")
        
        if df is not None and not df.empty:
            # Adicionar métricas de resumo
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            # Calcular métricas importantes
            df_hora = df.copy()
            df_dia = df.copy()
            
            # Converter data para datetime se for string
            if df_dia['data'].dtype == 'object':
                df_dia['data'] = pd.to_datetime(df_dia['data'])
            
            # Adicionar dia da semana
            df_dia['dia_semana'] = df_dia['data'].dt.day_name()
            dias_semana_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_semana_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            mapa_dias = dict(zip(dias_semana_ordem, dias_semana_pt))
            df_dia['dia_semana_pt'] = df_dia['dia_semana'].map(mapa_dias)
            
            # Agrupar por dia da semana
            df_dia_semana = df_dia.groupby('dia_semana_pt')['total_ids'].sum().reset_index()
            
            # Encontrar horário mais ativo
            hora_mais_ativa = df_hora.loc[df_hora['total_ids'].idxmax()]['hora']
            total_hora_mais_ativa = df_hora.loc[df_hora['total_ids'].idxmax()]['total_ids']
            
            # Encontrar dia da semana mais ativo
            dia_semana_mais_ativo = df_dia_semana.loc[df_dia_semana['total_ids'].idxmax()]['dia_semana_pt']
            total_dia_semana_mais_ativo = df_dia_semana.loc[df_dia_semana['total_ids'].idxmax()]['total_ids']
            
            # Encontrar dia mais ativo
            dia_mais_ativo = df_dia.groupby('data')['total_ids'].sum().idxmax().strftime('%d/%m/%Y')
            total_dia_mais_ativo = df_dia.groupby('data')['total_ids'].sum().max()
            
            # Calcular média diária
            media_diaria = df_dia.groupby('data')['total_ids'].sum().mean()
            
            # Exibir métricas em cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Horário Mais Ativo</div>
                        <div class='metric-value'>{int(hora_mais_ativa):02d}:00</div>
                        <div class='metric-description'>
                            {int(total_hora_mais_ativa)} preenchimentos
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Dia da Semana Mais Ativo</div>
                        <div class='metric-value'>{dia_semana_mais_ativo}</div>
                        <div class='metric-description'>
                            {int(total_dia_semana_mais_ativo)} preenchimentos
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Dia Mais Ativo</div>
                        <div class='metric-value'>{dia_mais_ativo}</div>
                        <div class='metric-description'>
                            {int(total_dia_mais_ativo)} preenchimentos
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Média Diária</div>
                        <div class='metric-value'>{media_diaria:.1f}</div>
                        <div class='metric-description'>
                            Preenchimentos por dia
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            # Criar visualizações
            tab1, tab2, tab3 = st.tabs(["Por Hora", "Por Dia", "Por Dia da Semana"])
            
            with tab1:
                # Gráfico por hora
                fig_hora = px.bar(
                    df,
                    x='hora',
                    y='total_ids',
                    title='Distribuição por Hora do Dia',
                    labels={
                        'hora': 'Hora',
                        'total_ids': 'Total de Preenchimentos'
                    }
                )
                
                # Formatar eixo X para mostrar horas corretamente
                fig_hora.update_xaxes(
                    ticktext=[f"{h:02d}:00" for h in range(24)],
                    tickvals=list(range(24))
                )
                
                st.plotly_chart(fig_hora, use_container_width=True)
                
            with tab2:
                # Gráfico por dia
                fig_dia = px.bar(
                    df,
                    x='data',
                    y='total_ids',
                    title='Distribuição por Dia',
                    labels={
                        'data': 'Data',
                        'total_ids': 'Total de Preenchimentos'
                    }
                )
                
                fig_dia.update_xaxes(tickangle=45)
                st.plotly_chart(fig_dia, use_container_width=True)
                
            with tab3:
                # Criar coluna data_hora para o gráfico de linha do tempo
                df_timeline = df.copy()
                # Converter data para datetime se for string
                if df_timeline['data'].dtype == 'object':
                    df_timeline['data'] = pd.to_datetime(df_timeline['data'])
                
                # Criar coluna data_hora combinando data e hora
                df_timeline['data_hora'] = df_timeline.apply(
                    lambda row: row['data'] + pd.Timedelta(hours=int(row['hora'])), 
                    axis=1
                )
                
                # Gráfico de linha do tempo
                fig_timeline = px.line(
                    df_timeline,
                    x='data_hora',
                    y='total_ids',
                    title='Linha do Tempo de Preenchimentos',
                    labels={
                        'data_hora': 'Data/Hora',
                        'total_ids': 'Quantidade'
                    }
                )
                
                # Adicionar pontos
                fig_timeline.add_trace(px.scatter(df_timeline, x='data_hora', y='total_ids').data[0])
                
                # Melhorar o layout
                fig_timeline.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(size=14),
                    height=400,
                    xaxis=dict(
                        tickangle=45,
                        tickfont=dict(size=12),
                        gridcolor='lightgray'
                    ),
                    yaxis=dict(
                        gridcolor='lightgray',
                        zeroline=True,
                        zerolinecolor='lightgray'
                    ),
                    showlegend=False
                )
                
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Adicionar gráfico de dia da semana
                if 'dia_semana_pt' not in df_timeline.columns:
                    df_timeline['dia_semana'] = df_timeline['data'].dt.day_name()
                    dias_semana_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    dias_semana_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                    mapa_dias = dict(zip(dias_semana_ordem, dias_semana_pt))
                    df_timeline['dia_semana_pt'] = df_timeline['dia_semana'].map(mapa_dias)
                
                # Agrupar por dia da semana
                df_dia_semana = df_timeline.groupby('dia_semana_pt')['total_ids'].sum().reset_index()
                
                # Ordenar os dias da semana corretamente
                ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                df_dia_semana['ordem'] = df_dia_semana['dia_semana_pt'].map({dia: i for i, dia in enumerate(ordem_dias)})
                df_dia_semana = df_dia_semana.sort_values('ordem')
                
                # Gráfico de barras por dia da semana
                fig_dia_semana = px.bar(
                    df_dia_semana,
                    x='dia_semana_pt',
                    y='total_ids',
                    title='Distribuição por Dia da Semana',
                    labels={
                        'dia_semana_pt': 'Dia da Semana',
                        'total_ids': 'Total de Preenchimentos'
                    },
                    color='total_ids',
                    color_continuous_scale='Blues'
                )
                
                fig_dia_semana.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(size=14),
                    height=300,
                    xaxis=dict(
                        categoryorder='array',
                        categoryarray=ordem_dias,
                        gridcolor='lightgray'
                    ),
                    yaxis=dict(
                        gridcolor='lightgray',
                        zeroline=True,
                        zerolinecolor='lightgray'
                    ),
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig_dia_semana, use_container_width=True)

    @staticmethod
    @st.cache_data(ttl=300)
    def filter_familias(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
        """Filtra famílias com cache"""
        if not search_term:
            return df
        
        # Converter para minúsculas para busca case-insensitive
        search_term = search_term.lower()
        mask = df['Nome_Familia'].str.lower().str.contains(search_term, na=False)
        return df[mask]

    @staticmethod
    def show_detailed_table(df: pd.DataFrame):
        """Exibe tabela detalhada"""
        st.subheader("Detalhamento por Família")
        
        # Campo de busca
        search = st.text_input(
            "🔍 Buscar família",
            help="Digite o nome da família para filtrar",
            placeholder="Ex: Silva, Santos..."
        )
        
        # Remover linha de total e aplicar filtro
        df_display = df[df['Nome_Familia'] != 'Total'].copy()
        if search:
            df_display = Dashboard.filter_familias(df_display, search)
            if df_display.empty:
                st.warning("Nenhuma família encontrada com o termo de busca.")
                return
            st.success(f"Encontradas {len(df_display)} famílias.")
        
        # Dividir em duas tabelas
        tab1, tab2 = st.tabs(["Opções de Pagamento", "Resumo"])
        
        with tab1:
            # Tabela de opções
            columns_options = {
                'Nome_Familia': 'Família',
                'A': 'A',
                'B': 'B',
                'C': 'C',
                'D': 'D',
                'E': 'E',
                'F': 'F',
                'Condicao_Especial': 'Condição Especial'
            }
            
            df_options = df_display[columns_options.keys()].rename(columns=columns_options)
            
            # Estilo mais sutil
            styled_options = df_options.style\
                .format({col: '{:,.0f}' for col in df_options.columns if col != 'Família'})\
                .set_properties(**{
                    'background-color': 'white',
                    'color': '#666',
                    'font-size': '13px',
                    'border': '1px solid #eee'
                })\
                .apply(lambda x: ['font-weight: bold' if v > 0 else '' for v in x], 
                       subset=[col for col in df_options.columns if col != 'Família'])
            
            st.dataframe(
                styled_options,
                use_container_width=True,
                height=300
            )
        
        with tab2:
            # Tabela de resumo
            columns_summary = {
                'Nome_Familia': 'Família',
                'Requerentes_Continuar': 'Continuar',
                'Requerentes_Cancelar': 'Cancelar',
                'Total_Banco': 'Total'
            }
            
            df_summary = df_display[columns_summary.keys()].rename(columns=columns_summary)
            
            styled_summary = df_summary.style\
                .format({col: '{:,.0f}' for col in df_summary.columns if col != 'Família'})\
                .set_properties(**{
                    'background-color': 'white',
                    'color': '#333',
                    'font-size': '13px',
                    'border': '1px solid #eee'
                })\
                .apply(lambda x: ['font-weight: bold' if v > 0 else '' for v in x],
                       subset=[col for col in df_summary.columns if col != 'Família'])
            
            st.dataframe(
                styled_summary,
                use_container_width=True,
                height=300
            )

    @staticmethod
    def show_option_details(option: str):
        """Exibe detalhes de uma opção de pagamento"""
        df = familia_service.get_option_details(option)
        if df is not None and not df.empty:
            # Tabs para diferentes visualizações
            tab1, tab2, tab3 = st.tabs(["Visão Geral", "Por Família", "Download"])
            
            with tab1:
                st.markdown(f"""
                    ### Detalhes da {
                        'Opção ' + option if option != 'Condicao_Especial' 
                        else 'Condição Especial'
                    }
                    <div style='font-size: 0.9rem; color: {
                        PAYMENT_OPTIONS_COLORS.get(option, '#607D8B') if option != 'Condicao_Especial'
                        else '#607D8B'
                    }; margin-bottom: 1rem;'>
                        {
                            PAYMENT_OPTIONS.get(option, '') if option != 'Condicao_Especial'
                            else 'Famílias em condição especial'
                        }
                    </div>
                """, unsafe_allow_html=True)
                
                # Métricas da opção
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Pessoas", len(df))
                with col2:
                    st.metric("Famílias Diferentes", df['idfamilia'].nunique())
                with col3:
                    st.metric("Média por Família", f"{len(df)/df['idfamilia'].nunique():.1f}")
                
                # Tabela principal
                df_display = df.rename(columns={
                    'nome_completo': 'Nome',
                    'telefone': 'Telefone',
                    'nome_familia': 'Família',
                    'createdAt': 'Data'
                })
                
                st.dataframe(
                    df_display[['Nome', 'Telefone', 'Família', 'Data']],
                    use_container_width=True
                )
            
            with tab2:
                st.markdown("### Análise por Família")
                
                # Campo de busca
                search = st.text_input(
                    "🔍 Buscar família",
                    help="Digite o nome da família para filtrar",
                    placeholder="Ex: Silva, Santos...",
                    key=f"search_familia_{option}"  # Key única por opção
                )
                
                # Verificar se as colunas necessárias existem
                required_columns = ['nome_familia', 'nome_completo']
                optional_columns = ['telefone', 'createdAt']
                
                # Verificar se todas as colunas necessárias existem
                if not all(col in df.columns for col in required_columns):
                    st.warning("Não foi possível realizar a análise por família. Dados insuficientes.")
                    return
                
                # Abordagem mais simples: contar manualmente
                df_count = df.groupby('nome_familia').size().reset_index(name='Total Membros')
                
                # Adicionar outras métricas se disponíveis
                if 'telefone' in df.columns:
                    telefones = df.groupby('nome_familia')['telefone'].nunique().reset_index(name='Telefones Únicos')
                    df_count = pd.merge(df_count, telefones, on='nome_familia')
                
                if 'createdAt' in df.columns:
                    # Converter para datetime para operações min/max
                    df['createdAt'] = pd.to_datetime(df['createdAt'], format='%d/%m/%Y %H:%M', dayfirst=True)
                    
                    # Calcular primeiro e último preenchimento
                    primeiro = df.groupby('nome_familia')['createdAt'].min().reset_index(name='Primeiro Preenchimento')
                    ultimo = df.groupby('nome_familia')['createdAt'].max().reset_index(name='Último Preenchimento')
                    
                    # Mesclar com o DataFrame principal
                    df_count = pd.merge(df_count, primeiro, on='nome_familia')
                    df_count = pd.merge(df_count, ultimo, on='nome_familia')
                    
                    # Formatar datas de volta para string
                    df_count['Primeiro Preenchimento'] = df_count['Primeiro Preenchimento'].dt.strftime('%d/%m/%Y %H:%M')
                    df_count['Último Preenchimento'] = df_count['Último Preenchimento'].dt.strftime('%d/%m/%Y %H:%M')
                
                # Renomear a coluna nome_familia
                df_count = df_count.rename(columns={'nome_familia': 'Nome da Família'})
                
                # Aplicar filtro de busca
                if search:
                    df_count = df_count[df_count['Nome da Família'].str.contains(search, case=False, na=False)]
                    if df_count.empty:
                        st.warning("Nenhuma família encontrada com o termo de busca.")
                        return
                    st.success(f"Encontradas {len(df_count)} famílias.")
                
                # Criar visualizações
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Gráfico de barras por família
                    hover_data = []
                    if 'Telefones Únicos' in df_count.columns:
                        hover_data.append('Telefones Únicos')
                    
                    fig = px.bar(
                        df_count,
                        x='Nome da Família',
                        y='Total Membros',
                        title=f'Distribuição da Opção {option} por Família',
                        hover_data=hover_data
                    )
                    
                    fig.update_layout(
                        showlegend=True,
                        plot_bgcolor='white',
                        yaxis=dict(
                            title='Total de Membros',
                            gridcolor='#eee'
                        ),
                        xaxis=dict(
                            title='Família',
                            tickangle=45
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Métricas resumidas
                    st.metric(
                        "Média de Membros por Família",
                        f"{df_count['Total Membros'].mean():.1f}",
                        help="Média de membros por família"
                    )
                    
                    if 'Telefones Únicos' in df_count.columns:
                        st.metric(
                            "Total de Telefones Únicos",
                            df_count['Telefones Únicos'].sum(),
                            help="Total de telefones únicos registrados"
                        )
                
                # Tabela detalhada por família
                st.markdown("#### Detalhamento por Família")
                
                st.dataframe(
                    df_count,
                    use_container_width=True
                )
                
                # Detalhes dos membros
                if len(df_count) == 1:
                    familia_selecionada = df_count['Nome da Família'].iloc[0]
                    st.markdown(f"#### Membros da Família {familia_selecionada}")
                    
                    membros = df[df['nome_familia'] == familia_selecionada].copy()
                    
                    # Selecionar colunas disponíveis
                    cols_to_display = ['nome_completo']
                    if 'telefone' in membros.columns:
                        cols_to_display.append('telefone')
                    if 'createdAt' in membros.columns:
                        cols_to_display.append('createdAt')
                    
                    # Renomear colunas
                    rename_dict = {
                        'nome_completo': 'Nome',
                        'telefone': 'Telefone',
                        'createdAt': 'Data de Preenchimento'
                    }
                    
                    # Filtrar apenas as colunas que existem no rename_dict
                    rename_dict = {k: v for k, v in rename_dict.items() if k in cols_to_display}
                    
                    membros = membros[cols_to_display].rename(columns=rename_dict)
                    
                    st.dataframe(membros, use_container_width=True)
            
            with tab3:
                st.markdown("### Download dos Dados")
                
                # Preparar dados para download
                rename_dict = {
                    'nome_completo': 'Nome',
                    'telefone': 'Telefone',
                    'nome_familia': 'Família',
                    'createdAt': 'Data',
                    'idfamilia': 'ID Família'
                }
                
                # Filtrar apenas as colunas que existem no rename_dict
                rename_dict = {k: v for k, v in rename_dict.items() if k in df.columns}
                
                df_download = df.rename(columns=rename_dict)
                
                # Botões de download
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_download.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar CSV",
                        data=csv,
                        file_name=f"opcao_{option}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_download.to_excel(writer, sheet_name='Dados', index=False)
                        if 'df_count' in locals():
                            df_count.to_excel(writer, sheet_name='Por Família', index=False)
                    
                    st.download_button(
                        label="📊 Baixar Excel",
                        data=buffer.getvalue(),
                        file_name=f"opcao_{option}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info(f"Nenhum detalhe encontrado para a opção {option}")

    @staticmethod
    def render():
        """Renderiza o dashboard completo"""
        # Título e botão de atualização
        col1, col2 = st.columns([6, 1])
        with col1:
            st.title("Análise Formulário")
        with col2:
            if st.button("🔄 Atualizar"):
                familia_service.clear_cache()
                st.rerun()
        
        # Iniciar análise
        start_time = time.time()
        
        try:
            # Carregar dados
            with st.spinner("Carregando dados..."):
                df_status = familia_service.get_familias_status()
                df_timeline = familia_service.get_dados_grafico()
            
            if df_status is not None:
                # Mostrar componentes
                Dashboard.show_cache_metrics()
                st.markdown("<hr>", unsafe_allow_html=True)
                
                Dashboard.show_main_metrics(df_status)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                Dashboard.show_payment_options(df_status)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                if df_timeline is not None:
                    Dashboard.show_timeline_chart(df_timeline)
                    st.markdown("<hr>", unsafe_allow_html=True)
                
                Dashboard.show_detailed_table(df_status)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                # Detalhes por opção
                st.markdown("### 🔍 Explorar Opção")
                option = st.selectbox(
                    "Selecione uma opção para ver detalhes",
                    options=['A', 'B', 'C', 'D', 'E', 'F', 'Condicao_Especial'],
                    format_func=lambda x: (
                        f"{x} - {PAYMENT_OPTIONS[x]}" if x != 'Condicao_Especial' 
                        else "Condição Especial - Famílias em condição especial"
                    )
                )
                if option:
                    Dashboard.show_option_details(option)
            else:
                st.error("Erro ao carregar dados. Tente novamente mais tarde.")
            
        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
        finally:
            # Mostrar tempo de carregamento
            end_time = time.time()
            st.sidebar.metric(
                "Tempo de Carregamento",
                f"{(end_time - start_time):.2f}s",
                help="Tempo total de carregamento da página"
            )