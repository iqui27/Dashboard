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
import io
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from Projetos import ra, relatorio2023, mes, process_data, process_multiple_entries  
import datetime
from dateutil import parser
import numpy as np
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials



st.set_page_config(
    layout='wide',  # Ativa o layout wide
    initial_sidebar_state='auto'  # Define o estado inicial da sidebar (pode ser 'auto', 'expanded', 'collapsed')
)
# Caminho para o arquivo JSON de credenciais
path_to_credentials = 'sheets.json'
# Escopos necessários
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
# Autenticar usando o arquivo de credenciais
creds = ServiceAccountCredentials.from_json_keyfile_name(path_to_credentials, scope)
client = gspread.authorize(creds)

# Define your MySQL connection details
mysql_user = 'usr_sectidf'
mysql_password = 'DHS-14z4'
mysql_host = '10.233.209.2'  # Or your database server IP or hostname
mysql_database = 'db_sectidf'
mysql_port = '3306'  # Default MySQL port
table_name = 'Projetos'

# Define your development MySQL connection details
dev_mysql_user = 'admin'
dev_mysql_password = '844612'
dev_mysql_host = 'localhost'  # Replace with your development server IP or hostname
dev_mysql_database = 'db_sectidf'
dev_mysql_port = '3306'  # Default MySQL port
dev_table_name = 'Projetos'

# Initialize session state
if 'use_dev_server' not in st.session_state:
    st.session_state.use_dev_server = False

# Function to switch to development server
def switch_to_development():
    st.session_state.use_dev_server = not st.session_state.use_dev_server

# Create a button to switch to development server
if st.sidebar.button('Switch to Development Server'):
    switch_to_development()
# Display the current mode
mode = "Development" if st.session_state.use_dev_server else "Production"
st.sidebar.markdown(f"**Current Mode:** {mode}")


# Use the appropriate server details based on the session state
if st.session_state.use_dev_server:
    mysql_user = dev_mysql_user
    mysql_password = dev_mysql_password
    mysql_host = dev_mysql_host
    mysql_database = dev_mysql_database
    mysql_port = dev_mysql_port
    table_name = dev_table_name

def clean_column_names(dataframe):
    # Strip trailing spaces from column names
    dataframe.columns = dataframe.columns.str.strip()
    # Replace spaces in column names with underscores and make them lowercase to ensure SQL compatibility
    dataframe.columns = dataframe.columns.str.replace(' ', '_').str.lower()
    return dataframe

# Função para ler e tratar o arquivo Excel
def read_and_process_file(uploaded_file, month):
    tabela_visitas = pd.read_excel(uploaded_file, sheet_name=month, skiprows=2, usecols="A:E", nrows=31)
    tabela_cupula = pd.read_excel(uploaded_file, sheet_name=month, skiprows=2, usecols="I:L", nrows=31)
    tabela_alunos = pd.read_excel(uploaded_file, sheet_name=month, skiprows=2, usecols="O:R", nrows=31)


    tabelas = {'visitas': tabela_visitas, 'cupula': tabela_cupula, 'alunos': tabela_alunos}

    for key, tabela in tabelas.items():
        tabela.rename(columns={tabela.columns[0]: 'DIA'}, inplace=True)
        tabela.replace('######', 0, inplace=True)
        tabela.replace('#####', 0, inplace=True)
        tabela.fillna(0, inplace=True)
        tabela['DIA'] = tabela['DIA'].astype(str).str.extract(r'(\d+)').astype(int)  # Extrai números e converte para int
        tabela = tabela[tabela['DIA'] != 0]
        tabela['DIA'] = pd.to_datetime(tabela['DIA'].astype(str) + ' ' + month + ' 2024', format='%d %B %Y')
        tabelas[key] = tabela  # Atualiza a tabela modificada no dicionário

    # Retorna as tabelas processadas
    return tabelas['visitas'], tabelas['cupula'], tabelas['alunos']

     
def create_mysql_engine(user, password, host, port, db):
    return create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}')
# Cria o engine do SQLAlchemy para a conexão com o MySQL
mysql_engine = create_mysql_engine(mysql_user, mysql_password, mysql_host, mysql_port, mysql_database)
st.session_state['sql'] = False
st.session_state['Erro1'] = False
st.session_state['erro2'] = False
def update_data_to_db(engine, table_name, data):
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for index, row in data.iterrows():
                # Constrói a string de atualização com todas as colunas
                update_str = ', '.join(f'{col} = :{col}' for col in data.columns)
                row_dict = row.to_dict()
                if 'dia' in row_dict:
                    del row_dict['dia']
                stmt = text(f"UPDATE {table_name} SET {update_str} WHERE dia = :dia").bindparams(dia=index, **row_dict)
                st.write(stmt)
                conn.execute(stmt)
            trans.commit()
            st.session_state['sql'] = True
        except SQLAlchemyError as e:
            trans.rollback()
            st.error(f"Erro ao atualizar os dados: {str(e)}")


# Função para inserir dados no banco de dados
def insert_data_to_db(engine, table_name, data):
    try:
        with engine.connect() as conn:
            data.to_sql(table_name, conn, if_exists='append', index=False)
            st.session_state['sql'] = True

    except IntegrityError as e:
        st.session_state['erro2'] = True

        # Aqui você pode decidir o que fazer em caso de erro de integridade, como ignorar ou registrar
    except SQLAlchemyError as e:
        st.session_state['Erro1'] = True

        # Tratamento de outros erros do SQLAlchemy

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
# Nome da sua planilha
spreadsheet_name = 'Relatório de visitas escolares por RA - 2024'
# Abrir a planilha
sheet = client.open(spreadsheet_name).sheet1  # ou use .get_worksheet(0) para a primeira folha
sheet2 = client.open(spreadsheet_name).get_worksheet(1)
# Carregar os dados da planilha
data = sheet.get_all_values()
# Criar um DataFrame a partir dos dados
ra2 = pd.DataFrame(data[3:39], columns=data[2])
data2 = sheet2.get_all_values()
escola_nome = pd.DataFrame(data2[2:], columns=data2[1])
# Obter os nomes das colunas pelo índice
cols_to_drop = escola_nome.columns[[3, 6]]
# Excluir as colunas
escola_nome = escola_nome.drop(columns=cols_to_drop)





if st.sidebar.button('Adicionar Visita'):
                # Se o botão for clicado, mude o estado para mostrar o formulário
                st.session_state['show_form'] = True
                st.session_state['show_2023'] = False
                st.session_state['show_2024'] = False
                st.session_state['show_files'] = False
                st.session_state['show_elogios'] = False
if st.sidebar.button('Adicionar Arquivos'):
                st.session_state['show_form'] = False
                st.session_state['show_2023'] = False
                st.session_state['show_2024'] = False
                st.session_state['show_files'] = True
                st.session_state['show_elogios'] = False
                
st.sidebar.divider()
st.sidebar.title('Relatórios')
st.sidebar.write('Selecione o ano para visualizar o relatório')
if st.sidebar.button('2023'):
            st.session_state['show_2023'] = True
            st.session_state['show_2024'] = False
            st.session_state['show_form'] = False
            st.session_state['show_files'] = False
            st.session_state['show_elogios'] = False
if st.sidebar.button('2024'):
                st.session_state['show_2024'] = True
                st.session_state['show_2023'] = False
                st.session_state['show_form'] = False
                st.session_state['show_files'] = False
                st.session_state['show_elogios'] = False
if st.sidebar.button('Elogios/Reclamações'):
                st.session_state['show_2024'] = False
                st.session_state['show_2023'] = False
                st.session_state['show_form'] = False
                st.session_state['show_files'] = False
                st.session_state['show_elogios'] = True

        

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
                            ra3 = st.selectbox('Região Administrativa', ra['Localização'].unique())
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
                                    'Ra': ra3
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
                selected_month_data = relatorio2023[relatorio2023['MonthYear'] == selected_month_year].copy()
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
                selected_month_data.loc[:, 'Dia da Semana'] = selected_month_data['Mês'].dt.strftime('%A')
                visitas_por_dia_da_semana = selected_month_data.groupby('Dia da Semana')['Quantidade Visitas'].sum().reset_index().copy()
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
    load_sql_query_alunos = f'SELECT * FROM {'Alunos'}'
    load_sql_query_Cupula = f'SELECT * FROM {'Cupula'}'
    load_sql_query_Visitas = f'SELECT * FROM {'Visitas'}'
    alunos = pd.read_sql_query(load_sql_query_alunos, mysql_engine)
    cupula = pd.read_sql_query(load_sql_query_Cupula, mysql_engine)
    visitas = pd.read_sql_query(load_sql_query_Visitas, mysql_engine)
    cupula['dia'] = pd.to_datetime(cupula['dia'])
    alunos['dia'] = pd.to_datetime(alunos['dia'])
    visitas['dia'] = pd.to_datetime(visitas['dia'])
    # Opção para selecionar os meses
    sorted_month_year = np.insert(cupula['dia'].dt.strftime('%B %Y').unique(), 0, "Todos os meses")
    selected_month = st.selectbox("Escolha o Mês:", sorted_month_year)
    # Supondo que selected_month seja uma string no formato "Mês Ano", por exemplo, "Janeiro 2024"
    meses = {
        "Todos os meses": 0,  # Adicionado como uma opção especial
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }

    # Dividindo a string para obter o mês e o ano separadamente, se aplicável
    if selected_month != "Todos os meses":
        mes_nome, ano = selected_month.split()
        mes_numero = meses[mes_nome]
        selected_month_datetime = datetime.datetime(year=int(ano), month=mes_numero, day=1)
    else:
        # Tratamento especial para "Todos os meses"
        selected_month_datetime = None  # Ou qualquer outra lógica que você deseja aplicar para este caso

    # Filtrando 'cupula' para o mês selecionado
    if selected_month_datetime:
        filtered_cupula = cupula[cupula['dia'].dt.month == selected_month_datetime.month]
    else:
        filtered_cupula = cupula

    #Processamenteo Cupula
    Total_visitante_cupula = filtered_cupula['total_visitantes'].sum()
    sessoes_publico = filtered_cupula['sessões_público'].sum()
    sessoes_escolas = filtered_cupula['sessões_escolas'].sum()
    total_sessoes = sessoes_publico + sessoes_escolas
    

    if selected_month_datetime:
        filtered_alunos = alunos[alunos['dia'].dt.month == selected_month_datetime.month]
    else:
        filtered_alunos = alunos

    if selected_month_datetime:
        filtered_visitas = visitas[visitas['dia'].dt.month == selected_month_datetime.month]
    else:
        filtered_visitas = visitas

    #Processamento Alunos
    total_alunos = filtered_alunos['total'].sum()
    escolas_publicas = filtered_alunos['pública'].sum()
    escolas_privadas = filtered_alunos['privada'].sum()
    total_escolas = escolas_publicas + escolas_privadas


    # Calculando a proporção de alunos por tipo de escola
    proporcao_publicas = escolas_publicas / total_escolas
    proporcao_privadas = escolas_privadas / total_escolas

    # Distribuindo os alunos conforme a proporção calculada
    if pd.isnull(total_alunos) or pd.isnull(proporcao_publicas):
        print("Erro: total_alunos ou proporcao_publicas é NaN")
        alunos_publicas = None
    else:
        alunos_publicas = round(total_alunos * proporcao_publicas)
        alunos_privadas = total_alunos - alunos_publicas

    #Processamento Visitantes
    visitantes_df = filtered_visitas['df'].sum()
    visitantes_oe = filtered_visitas['oe'].sum()
    visitantes_op = filtered_visitas['op'].sum()
    visitantes_total = visitantes_df + visitantes_oe + visitantes_op
    # Calculando o dia com mais visitas
    dia_com_mais_visitas = filtered_visitas.groupby('dia')['total_dia'].sum().idxmax()
    nome_dia_com_mais_visitas = dia_com_mais_visitas.strftime('%A')
    
    
    col1, col2, col3 = st.columns([3, 3,3])


            
    with col1:

                
                st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>Total de Visitantes na Cúpula:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #26D367;">{Total_visitante_cupula}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>Total de Visitantes de Outro Países:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #26D367;">{visitantes_op}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n") 
                st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>Total de Visitantes de Outros Estado:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: #26D367;">{visitantes_oe}</span>
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
                                    <span style="color: #db3e00;">{total_sessoes}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                            <div style="display: flex; align-items: right; gap: 10px;">
                                <span>Dia Mais Visitado:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                                    <span style="color: Yellow;">{nome_dia_com_mais_visitas}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")    

    
    # Gerando o gráfico de pizza para a comparação entre alunos de escolas públicas e privadas
    labels = ['Escolas Públicas', 'Escolas Privadas']
    values = [escolas_publicas, escolas_privadas]

    # Configuração do gráfico
    if alunos_publicas is None:
        st.divider()
        st.write("\n")
        st.write("Sem informações disponíveis sobre escolas nesse período")
        st.divider()
    else:
        fig_pizza = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        fig_pizza.update_layout(title_text='Proporção de Alunos: Escolas Públicas x Privadas')

        # Exibindo o gráfico no Streamlit
        st.plotly_chart(fig_pizza, use_container_width=True)

    # Gerar um treemap usando plotly express
    ra2['Total de alunos'] = ra2['Total de alunos'].replace(0, 0.1)
    fig10 = px.treemap(ra2, path=['DF','Localização'], values='Total de alunos',
                                color='Total de alunos', hover_data=['DF'],
                                color_continuous_scale='RdBu', title='Distribuição por Região Administrativa',)

    # Personalizar o tamanho da figura
    fig10.update_layout(
        autosize=False,
        #width=1000,  # Largura da figura em pixels
        height=600,#  Altura da figura em pixels
        paper_bgcolor='rgba(0,0,0,0)',  # RGBA para cor de fundo transparente
        plot_bgcolor='rgba(0,0,0,0)',     # Altura da figura em pixel
    )
    # Atualizar as propriedades do texto para os rótulos
    fig10.update_traces(
        textinfo="label+value",
        textfont_size=15,  # Tamanho da fonte dos rótulos 
    )

    fig10.update_traces(marker=dict(cornerradius=5))

    # Exibir o treemap no Streamlit
    st.plotly_chart(fig10, use_container_width=True)           


    # Opção para alternar entre visualização diária e mensal
    visualizacao = st.radio("Escolha o tipo de visualização:", ('Diária', 'Mensal'))

    if visualizacao == 'Diária':
        # Agrupando os dados por dia para visitas e alunos separadamente
        dados_por_dia_visitas = filtered_visitas.groupby(filtered_visitas['dia'].dt.date).agg({'total_dia': 'sum'}).reset_index().fillna(0)
        dados_por_dia_alunos = filtered_alunos.groupby(filtered_alunos['dia'].dt.date).agg({'total': 'sum'}).reset_index().fillna(0)
        
        # Renomeando colunas para melhor entendimento
        dados_por_dia_visitas.columns = ['Dia', 'Total de Visitas']
        dados_por_dia_alunos.columns = ['Dia', 'Total de Alunos']

        #Combinando os dataframes
        dados_por_dia_visitas['Categoria'] = 'Visitas'
        dados_por_dia_alunos['Categoria'] = 'Alunos'
        dados_combinados = pd.concat([dados_por_dia_visitas[['Dia', 'Total de Visitas', 'Categoria']],
                                    dados_por_dia_alunos.rename(columns={'Total de Alunos': 'Total de Visitas'})[['Dia', 'Total de Visitas', 'Categoria']]])
        
        #Criando o gráfico de barras empilhadas
        fig_dados_diarios = go.Figure()
        for categoria in dados_combinados['Categoria'].unique():
            df_filtrado = dados_combinados[dados_combinados['Categoria'] == categoria]
            fig_dados_diarios.add_trace(go.Bar(x=df_filtrado['Dia'], y=df_filtrado['Total de Visitas'], name=categoria))

        # Atualizando layout do gráfico para modo empilhado
        fig_dados_diarios.update_layout(
            title_text='Total de Visitas e Alunos por Dia',
            xaxis_tickangle=-45,
            yaxis=dict(title='Total'),
            barmode='stack'  # Modo empilhado
        )

        # Exibindo o gráfico
        # Aqui você usaria st.plotly_chart(fig_dados_diarios, use_container_width=True) se estiver usando Streamlit
        st.plotly_chart(fig_dados_diarios, use_container_width=True)
    else:
        # Agrupando os dados por mês
        visitas_por_mes = visitas.groupby(visitas['dia'].dt.to_period('M'))['total_dia'].sum().reset_index()
        st.write(visitas_por_mes)
        # Convertendo o índice de período para datetime para facilitar a visualização
        visitas_por_mes['dia'] = visitas_por_mes['dia'].dt.to_timestamp()
        st.write(visitas_por_mes)
        # Renomeando colunas para melhor entendimento
        visitas_por_mes.columns = ['Mês', 'Total de Visitas']
        
        st.write(visitas_por_mes)
        # Criando o gráfico de linha para visualização mensal com suavização e normalização
        fig_visitas_mensais = px.line(visitas_por_mes, x='Mês', y='Total de Visitas', title='Total de Visitas por Mês')
        fig_visitas_mensais.update_traces(line_shape='spline', line_smoothing=1.3)
        fig_visitas_mensais.update_yaxes(rangemode="tozero")
        st.plotly_chart(fig_visitas_mensais, use_container_width=True)
    
    st.dataframe(escola_nome)









if st.session_state.get('show_files', True):
    st.title('Upload e Processamento de Dados')
    # Criar um toggle para inserir ou atualizar dados
    # Criar um toggle para inserir ou atualizar dados
    update_data = st.checkbox("Atualizar dados")


    # Seleção do mês pelo usuário
    month = st.selectbox("Escolha o Mês:", ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"])


    if 'processing_done' not in st.session_state:
        st.session_state['processing_done'] = False

    # Upload do arquivo Excel
    uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx'])
    data = pd.DataFrame()
    if uploaded_file is not None:
        # Salva o arquivo carregado em um estado de sessão para reuso após rerun
        st.session_state['uploaded_file'] = uploaded_file

        process_button = st.button('Processar arquivo')
        # Crie um dicionário que mapeia os nomes dos meses para números
        month_to_number = {
            'JANEIRO': '1',
            'FEVEREIRO': '2',
            'MARÇO': '3',
            'ABRIL': '4',
            'MAIO': '5',
            'JUNHO': '6',
            'JULHO': '7',
            'AGOSTO': '8',
            'SETEMBRO': '9',
            'OUTUBRO': '10',
            'NOVEMBRO': '11',
            'DEZEMBRO': '12'
        }

        # Transforme o mês em um número
        month_number = month_to_number[month]
    # Verifica se um arquivo foi carregado e um mês foi selecionado
        if process_button:  
            # Processamento do arquivo
            tabela_visitas, tabela_cupula, tabela_alunos = read_and_process_file(uploaded_file, month)
            # Mostrar o DataFrame
           
            tabela_visitas['DIA'] = tabela_visitas['DIA'].dt.strftime('%Y-%m-%d')
            tabela_cupula['DIA'] = tabela_cupula['DIA'].dt.strftime('%Y-%m-%d')
            tabela_alunos['DIA'] = tabela_alunos['DIA'].dt.strftime('%Y-%m-%d')
            tabela_cupula.columns = ['dia', 'total_visitantes', 'sessões_público', 'sessões_escolas']
            tabela_alunos.columns = ['dia', 'total', 'pública', 'privada']
            tabela_visitas.columns = ['dia', 'df', 'oe', 'op', 'total_dia']
            st.write(tabela_visitas)
            st.write(tabela_cupula)
            st.write(tabela_alunos)
            

            # Inserir ou atualizar dados no banco de dados
            if update_data:
                update_data_to_db(mysql_engine, 'Visitas', tabela_visitas)
                update_data_to_db(mysql_engine, 'Cupula', tabela_cupula)
                update_data_to_db(mysql_engine, 'Alunos', tabela_alunos)
            else:
                insert_data_to_db(mysql_engine, 'Visitas', tabela_visitas)
                insert_data_to_db(mysql_engine, 'Cupula', tabela_cupula)
                insert_data_to_db(mysql_engine, 'Alunos', tabela_alunos)
            if st.session_state['sql']:
                st.success('Dados adicionados com sucesso ao banco de dados!')
                time.sleep(2)
            elif st.session_state['erro2']:
                st.warning('Erro de integridade ao tentar inserir dados na tabela')
                time.sleep(2)
            elif st.session_state['Erro1']:
                st.error('Erro ao tentar inserir dados na tabela')
                time.sleep(2)
        # Considere adicionar um botão para "limpar" ou reiniciar o estado após a inserção de dados
    if st.button('Reiniciar'):
        st.session_state['sql'] = False
        st.session_state['Erro1'] = False
        st.session_state['erro2'] = False


if st.session_state.get('show_elogios', True):
    st.title("Relatório de Avaliação do Planetário - Fevereiro 2024")
    st.write("Este relatório sumariza as respostas dos visitantes sobre sua experiência no Planetário em Fevereiro de 2024, destacando expectativas, atendimento, oferta de visitas guiadas, qualidade do acervo e feedback geral.")


    # Exemplo de dados
    data20 = {
        "Categoria": ["Expectativas Atendidas", "Atendimento", "Visita Guiada", "Qualidade dos Monitores", "Sinalização do Acervo"],
        "QR Code": [76, 70, 100, 100, 79],
        "Papel": [64, 77, 82, 57, 77]
    }

    df20 = pd.DataFrame(data20)
    df20 = df20.set_index("Categoria")
    categorias = ['Cúpula', 'Acervo', 'Atendimento', 'Ar condicionado']
    reclamacoes = [21, 3, 1, 5]
    fig10 = go.Figure([go.Bar(x=categorias, y=reclamacoes, marker_color='skyblue')])
    fig10.update_layout(title_text='Reclamações por Categoria',
                    xaxis_title="Categoria",
                    yaxis_title="Número de Reclamações")
    
    categorias_sugestoes = ['Telescópio', 'Divulgação', 'Acervo', 'Visita Interativa Infantil', 'Tecnologia']
    quantidade_sugestoes = [2, 1, 4, 1, 1]

    fig20 = go.Figure([go.Bar(x=categorias_sugestoes, y=quantidade_sugestoes, marker_color='lightgreen')])
    fig20.update_layout(title_text='Sugestões por Categoria',
                    xaxis_title="Categoria",
                    yaxis_title="Quantidade de Sugestões")
    
    categorias_elogios = ['Limpeza/Organização', 'Funcionários', 'Prazeroso']
    quantidade_elogios = [1, 4, 14]

    fig30 = go.Figure(data=[go.Pie(labels=categorias_elogios, values=quantidade_elogios, pull=[0, 0.1, 0])])
    fig30.update_layout(title_text='Elogios por Categoria')

    # Plot
    st.write("### Avaliações Gerais")
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.bar_chart(df20, height=500)
        st.plotly_chart(fig20)
        st.plotly_chart(fig10)
        st.plotly_chart(fig30)

         

    



    

    

    


    st.write("### Feedback Detalhado")

    with st.expander("Reclamações"):
        st.write("""
        - Mais vídeos sobre o espaço.
        - Acesso a roupas e capacetes de astronauta.
        - Uso de telescópio pelo público.
        """)

    with st.expander("Sugestões"):
        st.write("""
        - Uso de mais vídeos e tecnologias digitais.
        - Divulgação ampliada do espaço.
        - Inclusão de um telescópio para uso dos visitantes.
        """)

    with st.expander("Elogios"):
        st.write("""
        - Bom atendimento e organização.
        - Qualidade informativa e educativa das exposições.
        """)

    st.write("### Conclusão")
    st.write("O feedback dos visitantes é crucial para continuarmos melhorando a experiência no Planetário. As sugestões e elogios recebidos serão levados em consideração nas futuras melhorias do espaço e das atividades oferecidas.")



        

        

