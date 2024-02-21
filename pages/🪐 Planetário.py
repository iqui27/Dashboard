import time
import streamlit as st
import pandas as pd
import locale
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader
import json
from datetime import datetime
import pytz
import yaml
from streamlit_elements import elements, mui
import plotly.express as px
import plotly.graph_objs as go
import os
from Projetos import ra, relatorio2023, mes, process_data, process_multiple_entries  


st.set_page_config(
   page_title='Planetário',
   layout='wide',  # Ativa o layout wide
   initial_sidebar_state='auto',  # Define o estado inicial da sidebar (pode ser 'auto', 'expanded', 'collapsed')
   page_icon="📓"
)
 # Lista de estados brasileiros
estados_brasil = [
        'Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal', 
        'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 
        'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 
        'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 
        'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins'
        ]
# Botão para adicionar visita
st.image('ID_SECTI.png', width=200)
if st.sidebar.button('Adicionar Visita'):
                # Se o botão for clicado, mude o estado para mostrar o formulário
                st.session_state['show_form'] = True
                st.session_state['show_2023'] = False
                st.session_state['show_2024'] = False
st.sidebar.divider()
st.sidebar.title('Relatórios')
st.sidebar.write('Selecione o ano para visualizar o relatório')
if st.sidebar.button('2023'):
            st.session_state['show_2023'] = True
            st.session_state['show_2024'] = False
            st.session_state['show_form'] = False
if st.sidebar.button('2024'):
                st.session_state['show_2024'] = True
                st.session_state['show_2023'] = False
                st.session_state['show_form'] = False
        

if st.session_state.get('show_form', False):            
                
         # Escolha para adicionar uma única entrada ou várias entradas
                tipo_visita = st.radio('Tipo de Visita', ['Escola', 'Normal'])

                if tipo_visita == 'Escola':
                    entry_choice = st.radio('Deseja adicionar quantas entradas?', ('Única', 'Múltiplas'))

                    # Se a escolha for única, mostrar formulário para entrada única
                    if entry_choice == 'Única':
                        with st.form('single_entry_form'):
                            school_name = st.text_input('Nome da Escola')
                            school_series = st.text_input('Série Escolar')
                            education_type = st.selectbox('Ensino', ['Maternal', 'Fundamental', 'Médio', 'Superior', 'Outros'])
                            institution_type = st.selectbox('Tipo', ['Privada', 'Pública'])
                            visit_month = st.date_input('Mês da Visita')
                            session_qty = st.number_input('Quantidade de Sessões', min_value=0)
                            visit_qty = st.number_input('Quantidade de Visitas', min_value=0)
                            ra2 = st.selectbox('Região Administrativa', ra['Localização'].unique())
                            submit_button = st.form_submit_button('Enviar')

                            if submit_button:
                                # Processar os dados da entrada única
                                data = {
                                    'Nome da Escola': school_name,
                                    'Série Escolar': school_series,
                                    'Ensino': education_type,
                                    'Tipo': institution_type,
                                    'Mês da Visita': visit_month,
                                    'Quantidade de Sessões': session_qty,
                                    'Quantidade de Visitas': visit_qty,
                                    'Ra': ra2
                                }
                                process_data(data)

                    # Se a escolha for múltiplas, mostrar opções para entradas múltiplas
                    elif entry_choice == 'Múltiplas':
                        with st.form('multiple_entry_form'):
                            # Opção para upload de arquivo CSV
                            uploaded_file = st.file_uploader('Escolha um arquivo CSV', type=['csv'])
                            # Área de texto para inserir dados em formato tabular
                            tabular_data = st.text_area('Ou cole os dados aqui (separados por tabulação):')
                            submit_button = st.form_submit_button('Enviar Dados em Lote')

                            if submit_button:
                                # Se um arquivo foi carregado, processar o arquivo CSV
                                if uploaded_file is not None:
                                    df = pd.read_csv(uploaded_file)
                                    process_multiple_entries(df)
                                # Se dados tabulares foram inseridos, processá-los
                                elif tabular_data:
                                    try:
                                        data = pd.read_csv(io.StringIO(tabular_data), sep='\t')
                                        process_multiple_entries(data)
                                    except Exception as e:
                                        st.error(f'Erro ao processar os dados tabulares: {e}')
                    if st.button('Fechar'):
                        st.session_state['show_form'] = False

                elif tipo_visita == 'Normal':
                   with st.form(key='normal_visit_form'):
                        visitor_name = st.text_input('Nome')
                        city = st.text_input('Cidade')
                        state = st.text_input('Estado')
                        visit_month = st.date_input('Mês da Visita')
                        country = st.text_input('Qual país?')                        
                        state = st.selectbox('Estado', estados_brasil)
                        dome_visit = st.checkbox('Visita na cúpula?')
                        submit_button = st.form_submit_button('Enviar')
                     
                        if submit_button: 
                            data = {
                                    'Nome da Escola': None,
                                    'Série Escolar': None,
                                    'Ensino': None,
                                    'Tipo': None,
                                    'Mês da Visita': visit_month,
                                    'Quantidade de Sessões': None,
                                    'Quantidade de Visitas': None,
                                    'Ra': None,
                                    'Nome': visitor_name,
                                    'Cidade': city,
                                    'Estado': state,
                                    'País': country,
                                    'Cúpula': dome_visit,
                            }
                            process_data(data)
                            

        
        # Feedback do usuário após o envio do formulário
if 'data_processed' in st.session_state and st.session_state['data_processed']:
            st.success('Dados enviados com sucesso!')
            st.balloons()  # Adicionar animação de balões como um toque especial
            st.session_state['data_processed'] = False  # Resetar o estado após mostrar a mensagem
            st.session_state['show_form'] = False  # Esconder o formulário após o envio

st.divider()
        
if st.session_state.get('show_2023', True):
            # Gerar um treemap usando plotly express
            ra['Total de alunos'] = ra['Total de alunos'].replace(0, 0.1)
            fig = px.treemap(ra, path=['DF','Localização'], values='Total de alunos',
                            color='Total de alunos', hover_data=['DF'],
                            color_continuous_scale='RdBu', title='Distribuição por Região Administrativa',)
                    # Create gauge charts
            total_sum = relatorio2023['Quantidade Visitas'].sum()
            # Convert 'Mês' to datetime if it's not already
            relatorio2023['Mês'] = pd.to_datetime(relatorio2023['Mês'])
            mes['Mês'] = pd.to_datetime(mes['Mês'])


            relatorio2023['YearMonth'] = relatorio2023['Mês'].dt.strftime('%Y%m')
            mes['YearMonth'] = mes['Mês'].dt.strftime('%Y%m')

            # Create a month-year string representation for the dropdown
            relatorio2023['MonthYear'] = relatorio2023['Mês'].dt.strftime('%B %Y')
            mes['MonthYear'] = mes['Mês'].dt.strftime('%B %Y')

            # Get the unique list of year-month pairs, sorted chronologically
            sorted_month_list = relatorio2023['YearMonth'].unique()
            sorted_month_list.sort()
            # Map the sorted year-month to the human-readable month-year strings
            sorted_month_year = [relatorio2023[relatorio2023['YearMonth'] == ym]['MonthYear'].iloc[0] for ym in sorted_month_list]
            

            # Adiciona "Todos os Meses" no início da lista de meses
            sorted_month_year = ["Todos os Meses"] + sorted_month_year

            # Usuário seleciona o mês-ano do dropdown
            selected_month_year = st.selectbox('Selecione o Mês', sorted_month_year)

            
            

            if selected_month_year == "Todos os Meses":
                mes['Cúpula'] = pd.to_numeric(mes['Cúpula'], errors='coerce')
                cupula_sum = mes['Cúpula'].sum()
                outros_paises_sum = mes['Outros Países'].sum()
                outros_estados_sum = mes['Outros Estados'].sum()
                numero_sessoes = mes['Número de sessões'].sum()
                total_students = mes['Estudantes'].sum()
                total_students2 = mes['Total de Atendimentos'].sum()
                max_value = relatorio2023['Quantidade Visitas'].sum().max()
                max_value2 = relatorio2023['Quantidade Visitas'].sum().max()
                private_sum = relatorio2023[relatorio2023['tipo'] == 'Privada']['Quantidade Visitas'].sum()
                public_sum = relatorio2023[relatorio2023['tipo'] == 'Pública']['Quantidade Visitas'].sum()
                relatorio2023['Dia da Semana'] = relatorio2023['Mês'].dt.strftime('%A')
                visitas_por_dia_da_semana = relatorio2023.groupby('Dia da Semana')['Quantidade Visitas'].sum().reset_index()
                visitas_por_dia_da_semana.sort_values(by='Quantidade Visitas', ascending=False, inplace=True)
                visitas_por_dia_da_semana = visitas_por_dia_da_semana.set_index('Dia da Semana')
                # Obter o dia da semana com mais visitas
                dia_com_mais_visitas = visitas_por_dia_da_semana.iloc[0]
                st.header(f"Relatório do Planetario - 2023")
                st.write("\n")
            else:
                mes['Cúpula'] = mes['Cúpula'].replace(0, 'Em Manutenção')
                # Filter the DataFrame based on the selected month-year
                selected_month_data = relatorio2023[relatorio2023['MonthYear'] == selected_month_year]
                selected_month_data2 = mes[mes['MonthYear'] == selected_month_year].copy()

                # Aplicar capitalize na coluna 'MonthYear'
                selected_month_data2['MonthYear'] = selected_month_data2['MonthYear'].apply(lambda x: x.capitalize())
                

                # Calculate the total number of students for the selected month
                total_students = selected_month_data['Quantidade Visitas'].sum()
                total_students2 = selected_month_data2['Total de Atendimentos'].sum()

                # Assuming you want to set the gauge max value to the max of any month to keep the scale consistent
                max_value = relatorio2023.groupby('MonthYear')['Quantidade Visitas'].sum().max()
                max_value2 = relatorio2023.groupby('MonthYear')['Quantidade Visitas'].sum().max()

                #Supondo que 'df_visitas' esteja ordenado cronologicamente
                mes['Variacao_Percentual'] = mes['Total de Atendimentos'].pct_change() * 100

                # Encontrando a variação percentual para o mês selecionado
                selected_month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
                variacao = mes[mes['Mês'] == selected_month_year_date]['Variacao_Percentual'].values[0]

                # Exibir o título do relatório
                st.header(f"Relatório do Planetario - {selected_month_data2['MonthYear'].iloc[0]}")
                st.write("\n")
                cupula_sum = selected_month_data2['Cúpula'].sum()
                outros_paises_sum = selected_month_data2['Outros Países'].sum()
                outros_estados_sum = selected_month_data2['Outros Estados'].sum()
                numero_sessoes = selected_month_data2['Número de sessões'].sum()
                private_sum = selected_month_data[selected_month_data['tipo'] == 'Privada']['Quantidade Visitas'].sum() 
                public_sum = selected_month_data[selected_month_data['tipo'] == 'Pública']['Quantidade Visitas'].sum()
                selected_month_data['Dia da Semana'] = selected_month_data['Mês'].dt.strftime('%A')
                visitas_por_dia_da_semana = selected_month_data.groupby('Dia da Semana')['Quantidade Visitas'].sum().reset_index()
                visitas_por_dia_da_semana.sort_values(by='Quantidade Visitas', ascending=False, inplace=True)
                visitas_por_dia_da_semana = visitas_por_dia_da_semana.set_index('Dia da Semana')
                # Obter o dia da semana com mais visitas
                dia_com_mais_visitas = visitas_por_dia_da_semana.iloc[0]

                # Verifica se a variação é um número (para evitar erros com NaN)
                if pd.notnull(variacao):
                    cor_texto = "green" if variacao >= 0 else "red"
                    variacao_formatada = f"{variacao:.2f}%"
                else:
                    cor_texto = "black"
                    variacao_formatada = "Dados indisponíveis"
            col1, col2, col3 = st.columns([3, 3,3])


            
            with col1:

                
                st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>Total de Visitantes na Cúpula:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #26D367;">{cupula_sum}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>Total de Visitantes de Outro Países:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #26D367;">{outros_paises_sum}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n") 
                st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>Total de Visitantes de Outros Estado:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #26D367;">{outros_estados_sum}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")   
                # Exibindo o card com a variação percentual
                
            with col3:
                st.markdown(f"""
                            <div style="display: flex; align-items: right; gap: 10px;">
                                <span>Número de Sessões:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #db3e00;">{numero_sessoes}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                            <div style="display: flex; align-items: right; gap: 10px;">
                                <span>Dia Mais Visitado:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: Yellow;">{dia_com_mais_visitas.name}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")    
            col1, col2, col3 = st.columns([3, 1, 3])
            with col1:

                # Personalizar o tamanho da figura
                fig.update_layout(
                    autosize=False,
                    #width=1000,  # Largura da figura em pixels
                    height=600,#  Altura da figura em pixels
                    paper_bgcolor='rgba(0,0,0,0)',  # RGBA para cor de fundo transparente
                    plot_bgcolor='rgba(0,0,0,0)',     # Altura da figura em pixel
                )
                # Atualizar as propriedades do texto para os rótulos
                fig.update_traces(
                    textinfo="label+value",
                    textfont_size=15,  # Tamanho da fonte dos rótulos 
                )

                fig.update_traces(marker=dict(cornerradius=5))
                # Exibir o treemap no Streamlit
    
                
                fig4 = go.Figure()
                # Criação do gráfico de donut

                fig4.add_trace(go.Indicator(
                mode="gauge+number",
                value=total_students,
                title={'text': f"Estudantes - {selected_month_year}"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, max_value], 'tickwidth': 1, 'tickcolor': "#0693e3"},
                    'bar': {'color': "#0693e3"},
                    'steps': [
                        {'range': [0, total_students], 'color': '#0693e3'},
                        {'range': [total_students, max_value], 'color': '#0693e3'}
                    ],
                }
            ))
                
                fig5 = go.Figure()
                # Criação do gráfico de donut

                fig5.add_trace(go.Indicator(
                mode="gauge+number",
                value=total_students2,
                title={'text': f"Visitantes - {selected_month_year}"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, max_value2], 'tickwidth': 1, 'tickcolor': "orange"},
                    'bar': {'color': "orange"},
                    'steps': [
                        {'range': [0, total_students2], 'color': 'orange'},
                        {'range': [total_students2, max_value2], 'color': 'lightgray'}
                    ],
                }
            ))
                fig5.update_layout(
                    margin=dict(t=100)  # Increase top margin to 100 pixels; adjust the number as needed
                )
                # Criação do gráfico de donut
                if selected_month_year == "Todos os Meses":
                    # Preparar os dados para o gráfico de donut
                    data_donut = {
                        'Tipo': ['Privada', 'Pública'],
                        'Quantidade Visitas': [public_sum, private_sum]
                    }
                    # Cria um DataFrame a partir dos dados
                    df_donut = pd.DataFrame(data_donut)

                    # Criar o gráfico de donut com Plotly
                    fig2 = go.Figure(data=[go.Pie(
                        labels=df_donut['Tipo'], 
                        values=df_donut['Quantidade Visitas'], 
                        hole=.3
                    )])
                    fig2.update_layout(
                        title_text='Distribuição das Visitas por Tipo de Escola',
                        annotations=[dict(text='', x=0.5, y=0.5, font_size=40, showarrow=False)]
                    )
                else:
                    fig2 = go.Figure(data=[go.Pie(labels=selected_month_data['tipo'], values=selected_month_data['Quantidade Visitas'], hole=.3)])

                # Personalização do gráfico
                fig2.update_traces(marker=dict(colors=['#f44336', '#c2185b'], line=dict(color='#FFFFFF', width=0)))
                fig2.update_layout(
                    title_text=f'Escolas Privadas e Escolas Públicas - {selected_month_year}',  # Título do gráfico
                    # Personalização da legenda
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1

                    ),
                    # Personalização do papel e da cor de fundo do gráfico
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True
                )
                st.plotly_chart(fig2,use_container_width=True)
                if selected_month_year == "Todos os Meses":
                    # Exibir a variação percentual
                    st.write("\n")
                else:
                    st.markdown(f"""
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px; margin: 10px 0;">
                            <h4 style="text-align: center;">Variação de Visitantes em Relação ao Mês Anterior</h4>
                            <p style="text-align: center; color: {cor_texto}; font-size: 24px;">{variacao_formatada}</p>
                        </div>
                    """, unsafe_allow_html=True)   
                    st.write("\n")
                    st.write("\n")
                    st.write("\n")


                # Assuming you want to set the gauge max value to the max of any month to keep the sca
                col4, col5 = st.columns([1, 1])
                with col4:
                    st.plotly_chart(fig4, use_container_width=True)
                with col5:
                    st.plotly_chart(fig5, use_container_width=True)
                
            with col3:
                    
            

                # Exibe o gráfico
                st.plotly_chart(fig, use_container_width=True)

                # Criação do gráfico de linha total de alunos escola
                mes['Mês'] = pd.to_datetime(mes['Mês'])
                relatorio_agrupado = mes.groupby(mes['Mês'].dt.to_period('M')).agg({
                    'Total de Atendimentos': 'sum'
                }).reset_index()
                # Agora, converter o índice de período para datetime para gráficos
                relatorio_agrupado['Mês'] = relatorio_agrupado['Mês'].dt.to_timestamp()
                # Criação do gráfico de linha
                fig3 = px.line(relatorio_agrupado, x='Mês', y='Total de Atendimentos', title='Visitas por Mês')

                # Personalização do gráfico
                fig3.update_layout(
                    xaxis_title='Mês',
                    yaxis_title='Quantidade de Visitas',
                    xaxis=dict(
                        tickmode='auto',
                        nticks=20,
                        tickformat='%b\n%Y'  # Formato do mês como 'Jan\n2020'
                    ),
                    yaxis=dict(
                        tickmode='auto',
                        nticks=15  # Ajuste conforme necessário para o seu conjunto de dados
                    ),
                    showlegend=True
                )

                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig3,use_container_width=True)

if st.session_state.get('show_2024', True):
    st.header(f"Relatório do Planetario - 2024")