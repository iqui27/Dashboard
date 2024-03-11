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
import plotly.graph_objs as godas
from sqlalchemy import create_engine, text, Column, Integer, String, Float, Date, Table, MetaData
from sqlalchemy.orm import sessionmaker
import numpy as np
import os
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from streamlit_card import card
import plotly.io as pio

# Definir configurações da página
st.set_page_config(
    page_title='Dashboard SECTI',
    layout='wide',  # Ativa o layout wide
    initial_sidebar_state='auto'  # Define o estado inicial da sidebar (pode ser 'auto', 'expanded', 'collapsed')
)

DATA_FILE_PATH = 'planetario2024.csv'

# Define your MySQL connection details
mysql_user = 'usr_sectidf'
mysql_password = 'DHS-14z4'
mysql_host = '10.233.209.2'  # Or your database server IP or hostname
mysql_database = 'db_sectidf'
mysql_port = '3306'  # Default MySQL port
table_name = 'Projetos' 

# Create the SQLAlchemy engine
engine = create_engine(f'mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}')
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Replace 'your_sql_query' with your actual SQL query
load_sql_query = f'SELECT * FROM {table_name}'

# Definição da tabela de pagamentos
pagamentos = Table('pagamentos', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('projeto', String(255)),
                   Column('data', Date),
                   Column('valor', Float))

metadata.create_all(engine)

# Função para validar e armazenar os dados de entrada única
def process_data(data):
    try:
        # Aqui você poderia adicionar validações adicionais se necessário
        df = pd.DataFrame([data])
        df.to_csv(DATA_FILE_PATH, mode='a', header=not os.path.exists(DATA_FILE_PATH), index=False)
        st.session_state['data_processed'] = True
    except Exception as e:
        st.error(f'Erro ao salvar os dados: {e}')

# Função para processar dados de múltiplas entradas
def process_multiple_entries(df):
    try:
        # Aqui você poderia adicionar validações adicionais se necessário
        # Concatenar o novo DataFrame com o existente, ignorando o índice para evitar duplicatas
        df.to_csv(DATA_FILE_PATH, mode='a', header=not os.path.exists(DATA_FILE_PATH), index=False)
        st.session_state['data_processed'] = True
    except Exception as e:
        st.error(f'Erro ao processar entradas múltiplas: {e}')

timezone = pytz.timezone("America/Sao_Paulo")
# Function to load projects from persistent storage
def load_projects():
    try:
        with open('projects.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return an empty dictionary if the file does not exist
        return {}
    # Function to save the entire projects state, including channels and messages
def save_projects():
    with open('projects.json', 'w') as f:
        json.dump(st.session_state['projects'], f, indent=4)


# Função para carregar mensagens salvas
def load_messages():
    try:
        with open('messages.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def exportar_PDF(figs):
    # Salve cada figura como uma imagem PNG
    for i, fig in enumerate(figs):
        pio.write_image(fig, f'fig{i}.png')

    # Crie um novo PDF
    c = canvas.Canvas("report.pdf", pagesize=landscape(letter))

    # Adicione cada imagem ao PDF
    for i, fig in enumerate(figs):
        c.drawImage(f'fig{i}.png', 50, 50, width=500, height=300)
        c.showPage()  # Inicie uma nova página para a próxima imagem

    # Salve o PDF
    c.save()
figs = []
# Função para salvar mensagens
def save_messages(messages):
    with open('messages.json', 'w') as f:
        json.dump(messages, f, indent=4)

# Carregar mensagens anteriores quando o aplicativo é iniciado
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = load_messages()

# Function to get or create channels for the selected project
def get_or_create_project_channels(project_name):
    project_exists = project_name in st.session_state['projects']
    if not project_exists:
        # Inicializa o projeto com um canal "Geral"
        st.session_state['projects'][project_name] = {'channels': ['Geral'], 'chat_messages': {'Geral': []}}
    elif 'Geral' not in st.session_state['projects'][project_name]['channels']:
        # Adiciona o canal "Geral" se não existir
        st.session_state['projects'][project_name]['channels'].append('Geral')
        if 'Geral' not in st.session_state['projects'][project_name]['chat_messages']:
            st.session_state['projects'][project_name]['chat_messages']['Geral'] = []
    save_projects()  # Salva o estado do projeto
    return st.session_state['projects'][project_name]

# Function to remove a channel from the selected project
def remove_channel(project_name, channel_name):
    if channel_name == 'Geral':
        # Retorna uma mensagem de erro ou aviso, não permite a exclusão do canal "Geral"
        st.warning("Aviso: O canal 'Geral' é essencial e não pode ser removido.")
        time.sleep(2)
        return
    if channel_name in st.session_state['projects'][project_name]['channels']:
        st.session_state['projects'][project_name]['channels'].remove(channel_name)
        del st.session_state['projects'][project_name]['chat_messages'][channel_name]
        save_projects()  # Salva o estado atualizado do projeto





with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# Criação da tela de login
authenticator.login()

# Dataframe com os dados dos projetos
df = pd.read_sql_query(load_sql_query, engine)
servidores = pd.read_sql_table('servidores', engine)
projetos_servidores = pd.read_sql_table('ProjetoParceiros', engine)
ra = pd.read_csv("RA.csv")
relatorio2023 = pd.read_csv("Relatorio2023.csv")
mes = pd.read_csv("mes.csv")
estado = pd.read_csv("outroestado.csv")

# Defina um caminho para o arquivo CSV
csv_file_path = "Dashboard.csv"

if 'df' not in st.session_state:
    st.session_state.df = df

# Verificação de status de login
if st.session_state["authentication_status"]:
    st.image('ID_SECTI.png', width=200)
    st.write(f'Bem-vindo *{st.session_state["name"]}*')   
    # Verificar o sistema operacional
    if sys.platform.startswith('win'):
        # Para Windows
        locale_str = 'Portuguese_Brazil'
    elif sys.platform.startswith('darwin'):
        # Para macOS
        locale_str = 'pt_BR.UTF-8'
    else:
        # Para outros sistemas operacionais, ajuste conforme necessário
        locale_str = 'pt_BR.UTF-8'

    # Tentar definir o locale
    try:
        locale.setlocale(locale.LC_ALL, locale_str)
    except locale.Error as e:
        print(f"Erro ao definir o locale: {e}")

    # Initialize the Streamlit interface
    st.sidebar.title("Projetos")

    # Cria uma barra de navegação com abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠Home", "👥 Chat", "📓 Projetos", "✏️ Editar", "❌ Sair"])
    css = '''
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1rem;
        }
    </style>
    '''

    st.markdown(css, unsafe_allow_html=True)
    
    # Setup a search box
    search_query = st.sidebar.text_input("Busca", "", autocomplete="on")

    # Filtrar projetos baseados na busca em todas as colunas se a busca não estiver vazia
    if search_query:  # Verifica se search_query não está vazio
        filtered_projects = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
    else:
        filtered_projects = df

    # Group filtered projects by classification
    grouped_filtered_projects = filtered_projects.groupby('classificacao')

    # Display filtered projects in the sidebar grouped by classification
    st.sidebar.subheader("Classificação")
    if not grouped_filtered_projects.groups.keys():
        st.sidebar.write("Nenhum projeto encontrado.")
    else:
        selected_classification = st.sidebar.selectbox("Selecione uma Classificação", grouped_filtered_projects.groups.keys())
        if selected_classification:
            projects = grouped_filtered_projects.get_group(selected_classification)
            selected_project = st.sidebar.radio("Selecione um Projeto", projects['Projeto'], index=0)
            if selected_project:
                project_details = projects[projects['Projeto'] == selected_project]
                valor = project_details['Valor'].values[0]
                # Convert the value to float
                valor = float(valor) if isinstance(valor, str) and valor.replace('.', '', 1).isdigit() else valor
                if valor is not None:
                    valor_formatado = locale.currency(valor, grouping=True)
                else:
                    valor_formatado = 0
                # Aqui você pode exibir os detalhes do projeto selecionado, incluindo valor_formatado
            else:
                project_details = None
                valor_formatado = None
                selected_project = "Nenhum projeto selecionado"

    # Ordenar o DataFrame pela coluna "classificacao"
    df_sorted = df.sort_values('classificacao')

    # Group projects by classification
    grouped_projects = df_sorted.groupby('classificacao')


    # Inicializa uma lista vazia para o projeto atual se ainda não existir
    numero_de_projetos = df['Projeto'].count()
    numero_de_projetos_em_andamento = df[df['classificacao'] == 'Termo de Fomento']['Projeto'].count()
    numero_de_projetos_emendas = df[df['classificacao'] == 'Termo de Colaboração']['Projeto'].count()
    numero_de_projetos_eventos = df[df['classificacao'] == 'Convênio']['Projeto'].count()
    numero_de_projetos_novos = df[df['classificacao'] == 'Novos Projetos']['Projeto'].count()
    numero_de_projetos_concluidos = df[df['Situação_atual'] == 'Concluído']['Projeto'].count()
    # Calculate the total value of projects in progress
    # Ensure the 'Valor' column is treated as float
    df['Valor'] = df['Valor'].astype(float)
    valor_total_projetos_andamento = df[df['classificacao'] == 'Termo de Fomento']['Valor'].sum()
    valor_total_projetos_andamento_emendas = df[df['classificacao'] == 'Termo de Colaboração']['Valor'].sum()
    valor_total_projetos_andamento_eventos = df[df['classificacao'] == 'Convênio']['Valor'].sum()
    valor_total_projetos_andamento_novos = df[df['classificacao'] == 'Novos Projetos']['Valor'].sum()
    valor_total_projetos_andamento_concluidos = df[df['Situação_atual'] == 'Concluído']['Valor'].sum()
    valor_total_projetos_andamento_formatado = locale.currency(valor_total_projetos_andamento, grouping=True)
    valor_total_projetos_andamento_emendas_formatado = locale.currency(valor_total_projetos_andamento_emendas, grouping=True)
    valor_total_projetos_andamento_eventos_formatado = locale.currency(valor_total_projetos_andamento_eventos, grouping=True)
    valor_total_projetos_andamento_novos_formatado = locale.currency(valor_total_projetos_andamento_novos, grouping=True)
    valor_total_projetos_andamento_concluidos_formatado = locale.currency(valor_total_projetos_andamento_concluidos, grouping=True)
    with tab1:

            col1, col2= st.columns([3, 3])
            with col1:
                style_container = """
                    <style>
                    .stats {
                        padding: 10px 0;
                        display: flex;
                        align-items: center;
                        justify-content: left;
                        gap: 10px;
                    }
                    .stats div {
                        padding: 5px 10px;
                        background-color: #1B1F23; /* Cor do fundo do número */
                        border-radius: 10px;
                        color: yellow; /* Cor do texto do número */
                        font-weight: bold;
                    }
                    </style>
                    """
                st.header("Bem vindo ao Dashboard SECTI")
                st.write("Aqui você pode acompanhar os projetos da SECTI")
                st.write("Para começar, selecione um projeto na barra lateral")
                # Utilize o estilo definido acima antes dos seus elementos
                st.markdown(style_container, unsafe_allow_html=True)

                # Cada linha de estatística é formatada com o estilo definido
                st.markdown(f"""
                <div class="stats">
                    <span>Projetos cadastrados:</span>
                    <div>{numero_de_projetos}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="stats">
                    <span>Projetos Termo de Fomento:</span>
                    <div>{numero_de_projetos_em_andamento}</div>
                </div>
                """, unsafe_allow_html=True)

                # Repita para as demais categorias
                st.markdown(f"""
                <div class="stats">
                    <span>Projetos de Termos de Colaboração:</span>
                    <div>{numero_de_projetos_emendas}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="stats">
                    <span>Projetos de Convênio:</span>
                    <div>{numero_de_projetos_eventos}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")


                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>Valor total dos projetos Termo de Fomento:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>Valor total dos projetos de Termo de Colaboração:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_emendas_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span>Valor total dos projetos de Convênio:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_eventos_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span>Valor total dos novos projetos:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_novos_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span>Valor total dos projetos concluídos:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_concluidos_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)


            
            


            # Suponha que 'df' seja o seu DataFrame e que ele tem colunas 'Projeto', 'Valor', 'Classificação' e 'Unidade_SECTI_Responsavel'
            # Certifique-se de que os valores estão em formato numérico e não há valores NaN
            st.divider()
            st.write("Pessoas envolvidas nos projetos")
            # Realizar a junção das tabelas
            lista_projetos = pd.merge(projetos_servidores, servidores, left_on='parceiro_id', right_on='id', how='inner')
            lista_projetos = pd.merge(lista_projetos, df, left_on='projeto_id', right_on='id', how='inner')
            # Criar um menu dropdown com os nomes das pessoas
            selected_name = st.selectbox('Escolha uma pessoa', lista_projetos['Nome'].unique())
            col1, col2, col3 = st.columns([3, 2, 3])
            with col2:
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
          
 
             
                
                # Filtrar os projetos da pessoa selecionada
                filtered_projects = lista_projetos[lista_projetos['Nome'] == selected_name]
                ## Supondo que 'nome' é a coluna que você deseja converter para uma lista
                list_of_names = filtered_projects['Projeto'].tolist()
                numero_projetos = filtered_projects['Projeto'].count()
                st.subheader(f'Projetos `{numero_projetos}` ')
                # Agora você pode usar list_of_names em seu código
                for name in list_of_names:
                    st.write(name)
          
            # Supondo que filtered_projects seja o seu DataFrame e você tenha selecionado um projeto específico
            nome = filtered_projects['Nome'].iloc[0]
            matricula = filtered_projects['Matricula'].iloc[0]
            telefone = filtered_projects['Telefone'].iloc[0]
            unidade_secti = filtered_projects['Unidade_SECTI_Responsavel'].iloc[0]

            with col3:
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")

                st.dataframe(filtered_projects)
            

            with col1:
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.write(f"<span style='color: yellow;'>{filtered_projects['Nome'].iloc[0]}</span>", unsafe_allow_html=True)
                st.write(f"Matrícula: {filtered_projects['Matricula'].iloc[0]}")
                st.write(f"Telefone: {filtered_projects['Telefone'].iloc[0]}")
                st.write(f"Unidade SECTI: {filtered_projects['Unidade_SECTI_Responsavel'].iloc[0]}")

            
            
            # Count the number of people in each project
            people_counts = lista_projetos['Projeto'].value_counts()
            

            # Convert the result to a DataFrame, which is required for st.bar_chart()
            people_df = pd.DataFrame({'Número de Pessoas': people_counts}).reset_index()
            # Criar o gráfico de barras horizontal
            fig_pessoas = px.bar(people_df, x='Número de Pessoas', y='Projeto', orientation='h',
                        title='Quantidade de Pessoas por Projeto',
                        color='Número de Pessoas',
                        labels={'Quantidade de Pessoas': 'Quantidade de Pessoas', 'Projeto': 'Projeto'})

            # Ajustar o layout para melhor visualização
            fig_pessoas.update_layout(xaxis_title='Quantidade de Pessoas',
                            yaxis_title='Projeto',
                            yaxis={'categoryorder': 'total ascending'},
                            height=800)  # Ajuste a altura conforme necessário

            # Mostrar o gráfico
            st.divider()
            st.plotly_chart(fig_pessoas)
            figs.append(fig_pessoas) 

            st.divider()    
            df.dropna(subset=['Valor'], inplace=True)
            df['Valor'] = df['Valor'].astype(float)

            # Toggle para habilitar ou desabilitar os filtros
            enable_classificacao_filter = st.checkbox("Filtrar por Classificação")
            enable_unidade_filter = st.checkbox("Filtrar por Unidade_SECTI_Responsavel")

            if enable_classificacao_filter:
                # Opções de classificação
                classificacoes = df['classificacao'].unique()

                # Widget de seleção de classificação
                selected_classificacao = st.selectbox('Selecione a Classificação', classificacoes)

            if enable_unidade_filter:
                # Opções de Unidade_SECTI_Responsavel
                unidades = df['Unidade_SECTI_Responsavel'].unique()

                # Widget de seleção de Unidade_SECTI_Responsavel
                selected_unidade = st.selectbox('Selecione a Unidade_SECTI_Responsavel', unidades)
                

            # Filtrar o DataFrame com base nos filtros selecionados
            if enable_classificacao_filter and enable_unidade_filter:
                filtered_df = df[(df['classificacao'] == selected_classificacao) & (df['Unidade_SECTI_Responsavel'] == selected_unidade)]
            elif enable_classificacao_filter:
                filtered_df = df[df['classificacao'] == selected_classificacao]
            elif enable_unidade_filter:
                filtered_df = df[df['Unidade_SECTI_Responsavel'] == selected_unidade]
            else:
                filtered_df = df

            import plotly.express as px

            # Normalize values above 6M to 6M
            filtered_df.loc[filtered_df['Valor'] > 6000000, 'Valor'] = 6000000

            # Create a bar chart using Plotly
            # Create a new column with truncated project names
            filtered_df['Projeto_truncated'] = filtered_df['Projeto'].apply(lambda x: x[:15])

            fig_projetos = px.bar(filtered_df, x='Projeto_truncated', y='Valor', title='Valores por Projeto', color='Valor', hover_name='Projeto_truncated', color_continuous_scale='oryel')

            fig_projetos.update_layout(
                xaxis=dict(showticklabels=True),
                title='')
            fig_projetos.update_traces( textposition='outside')
            fig_projetos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

            # Show the chart
            st.plotly_chart(fig_projetos, use_container_width=True)
            figs.append(fig_projetos) 


    

            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")

            # Agrupar projetos por Situação_atual e contar quantos projetos estão em cada categoria
            situacao_counts = df['Situação_atual'].value_counts()

            # Convertendo o resultado para um DataFrame, que é necessário para o st.bar_chart()
            situacao_df = pd.DataFrame({'Número de Projetos': situacao_counts})
            st.divider()
            col1, col2 = st.columns([1,2])
            with col1:
                
                st.write(situacao_df)

            # Exibir o gráfico de barras no Streamlit
            fig_situacao = px.bar(situacao_df, x='Número de Projetos', color='Número de Projetos', hover_name='Número de Projetos', color_continuous_scale='geyser', orientation='h')

            fig_situacao.update_layout(
                xaxis=dict(showticklabels=True),
                title='')
            fig_situacao.update_traces( textposition='outside')
            fig_situacao.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

            # Show the chart
            with col2:
                st.plotly_chart(fig_situacao, use_container_width=True)
                figs.append(fig_situacao) 

    with tab3:
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            col1, col2, col3 = st.columns([3, 6, 3])
            if st.button('Exportar PDF'):
                # Chame a função quando o botão for pressionado
                exportar_PDF(figs)

            # Main Area
            if project_details is not None and 'Fomento' in project_details and project_details['Fomento'].size > 0:
                fomento = project_details['Fomento'].values[0]
            else:
                fomento = None

            with col2:
                st.markdown("<h1 style='text-align: center;'>{}</h1>".format(selected_project), unsafe_allow_html=True)
                st.markdown("<h3 style='text-align: center;'>{}</h3>".format(fomento), unsafe_allow_html=True)
                st.write("\n")
                if valor_formatado == "R$ 0,00":
                    valor_formatado = "Nenhum Valor Informado"
                st.write("\n")
                if valor_formatado == "R$ 0,00":
                    valor_formatado = "Nenhum Valor Informado"

                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 1rem 0;">
                    <span style="font-size: 2.25rem; font-weight: bold; color: white; margin-bottom: 0.5rem;"></span>
                    <span style="background-color: #1B1F23 ; padding: 0.25rem 0.75rem; border-radius: 10px; color: #388e3c; font-weight: bold; font-size: 3.00rem;">{valor_formatado}</span>
                </div>
                """, unsafe_allow_html=True)
                
                #st.markdown(f"""
                #<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0rem 0;">
                #    <span style="font-size: 1.10rem; font-weight: light; color: white; margin-bottom: 0rem;">Processo_SEI</span>
                #    <span style="background-color: #1B1F23 ; padding: 0.25rem 3.75rem; border-radius: 10px; color: yellow; font-weight: light; font-size: 1.15rem;">{project_details['Processo_SEI'].values[0]}</span>
                #</div>
                #""", unsafe_allow_html=True)
                st.write("\n")
                
                
            with col1:
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Instituição Parceira</h5>", unsafe_allow_html=True)
                if project_details is not None and 'Instituição_Parceira' in project_details and project_details['Instituição_Parceira'].size > 0:
                    instituicao_parceira = project_details['Instituição_Parceira'].values[0] if project_details['Instituição_Parceira'].values[0] != '0' else 'Não informado'
                else:
                    instituicao_parceira = 'Não informado'

                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{instituicao_parceira}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Execução do Projeto</h5>", unsafe_allow_html=True)
                if project_details is not None and 'Execução_do_Projeto' in project_details and project_details['Execução_do_Projeto'].size > 0:
                    execucao_projeto = project_details['Execução_do_Projeto'].values[0] if project_details['Execução_do_Projeto'].values[0] != '0' else 'Não informado'
                else:
                    execucao_projeto = 'Não informado'

                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{execucao_projeto}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Unidade SECTI</h5>", unsafe_allow_html=True)
                #t.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Unidade_SECTI_Responsavel'].values[0] if project_details['Unidade_SECTI_Responsavel'].values[0] != '0' else 'Não informado'}</h6>", unsafe_allow_html=True)
                if project_details is not None and 'Unidade_SECTI_Responsavel' in project_details and project_details['Unidade_SECTI_Responsavel'].size > 0:
                    unidade_secti_responsavel = project_details['Unidade_SECTI_Responsavel'].values[0]
                else:
                    unidade_secti_responsavel = None
                if project_details is not None and 'Unidade_SECTI_adicional' in project_details and project_details['Unidade_SECTI_adicional'].size > 0:
                    unidade_secti_adicional = project_details['Unidade_SECTI_adicional'].values[0]
                else:
                    unidade_secti_adicional = None

                if unidade_secti_responsavel == 0 or unidade_secti_responsavel == '0':
                    unidade_secti_responsavel = 'Não informado'

                if unidade_secti_adicional == 'Sem Colaboração' or unidade_secti_adicional == 'None' or unidade_secti_adicional == None:
                    unidade_secti_adicional = ' '

                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{unidade_secti_responsavel} | {unidade_secti_adicional}</h6>", unsafe_allow_html=True)
                
                st.write("\n")
                st.write("\n")
    
            with col3:
                if project_details is not None and 'Encerramento_da_parceria' in project_details and project_details['Encerramento_da_parceria'].size > 0:
                    valor_encerramento = project_details['Encerramento_da_parceria'].values[0]
                else:
                    valor_encerramento = None
                if valor_encerramento == "0":
                    valor_encerramento = "Não informado"

                valor_ponto_focal = project_details['Ponto_Focal_na_Instituição_Parceira'].values[0]
                if valor_ponto_focal == "0":
                    valor_ponto_focal = "Não informado"

                valor_mais_informacoes = project_details['Mais_informações_do_fomento'].values[0]
                if valor_mais_informacoes == "0":
                    valor_mais_informacoes = "Não informado"

                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Encerramento de Parceria</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{valor_encerramento}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Ponto Focal Instituição Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{valor_ponto_focal}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Mais Informações sobre o fomento</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{valor_mais_informacoes}</h6>", unsafe_allow_html=True)
      
                # Para centralizar os nomes e adicionar espaço
                nomes = project_details['Comissão_Gestora_da_Parceria'].values[0].split(',')
                if nomes == ['0']:
                    nomes = ['Não informado']

               
            
            st.divider()   
            col1, col2, col3, col4, col5, col6 = st.columns([4, 1, 4, 4, 1, 4])
            with col1:
                with elements("card_container"):
                    with mui.Card(key="card1",style={"borderRadius": "10px","border": "1px solid #0e1117", "boxShadow": "none", "backgroundColor": "transparent"}):
                        mui.CardContent([
                            mui.Typography("Observações", style={"textAlign": "center","fontFamily": "'Roboto', sans-serif", "fontWeight": "bold", "color": "white", "marginBottom": "20px"}),
                            mui.Typography(project_details['Observações'].values[0] if project_details['Observações'].values[0] != "0" else "Não informado", style={"marginTop": "16px", "color": "gray", "fontFamily": "'sans serif', sans-serif", "fontSize": "14px"}),
                        ])
                    
            with col6:
                 with elements("card_container1"):
                                    # Incorporar uma fonte do Google
                    mui.CssBaseline(options={
                        "typography": {
                            "fontFamily": "'Roboto', sans-serif"  # Substitua 'Roboto' pela fonte que você deseja usar
                        }
                    })
                    # Cria um cartão com cantos arredondados e sombra
                    with mui.Card(key="nomes_card", style={"borderRadius": "10px", "backgroundColor": "transparent", "border": "1px solid #0e1117", "boxShadow": "none"}):
                        # Conteúdo do cartão
                        with mui.CardContent():
                            # Cabeçalho do cartão
                            mui.Typography("Comissão Gestora", style={"textAlign": "center", "fontSize": "17px", "fontFamily": "'sans serif', sans-serif" , "fontWeight": "bold", "color": "white", "marginBottom": "20px"})

                            # Lista de nomes
                            for nome in nomes:
                                # Cada nome é um item de lista com estilos aplicados
                                mui.Typography(nome, component="li", style={
                                    "background": "transparent",
                                    "borderRadius": "10px",
                                    "border": "2px",
                                    "padding": "5px 20px",
                                    "margin": "0px 0",
                                    "color": "#ff9800",
                                    "textAlign": "center",
                                    "display": "block",
                                    "fontSize": "12px",
                                    "fontFamily": "'Roboto', sans-serif",
                                    "fontWeight": "bold",
                                })

                        st.markdown("</ul>", unsafe_allow_html=True)
            
            
            valor_fonte_custeio = project_details['Fonte_de_Custeio'].values[0]
            if valor_fonte_custeio == "0":
                valor_fonte_custeio = "Não informado"

            valor_situacao_atual = project_details['Situação_atual'].values[0]
            if valor_situacao_atual == "0":
                valor_situacao_atual = "Não informado"

            with col4:
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 1rem 0;">
                    <span style="font-size: 1.35rem; font-weight: bold; color: white; margin-bottom: 0.5rem;">Fonte de Custeio</span>
                    <span style="background-color: #1B1F23 ; padding: 0.25rem 0.75rem; border-radius: 10px; color: gray; font-weight: bold; font-size: 1.25rem;">{valor_fonte_custeio}</span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 1rem 0;">
                    <span style="font-size: 1.35rem; font-weight: bold; color: white; margin-bottom: 0.5rem;">Situação Atual</span>
                    <span style="background-color: #1B1F23 ; padding: 0.25rem 0.75rem; border-radius: 10px; color: #388e3c; font-weight: bold; font-size: 1.25rem;">{valor_situacao_atual}</span>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            col10, col11, col12 = st.columns([3, 3, 3])
            with col10:
                st.markdown(f"""
                            <div style="display: block; align-items: center; gap: 10px;">
                                <span>Processo SEI:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 2px 10px;">
                                    <span style="color: #03a9f4;">{project_details['Processo_SEI'].values[0]}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
              
            with col11:
                st.markdown(f"""
                            <div style="display: block; align-items: center; gap: 10px;">
                                <span>Classificação:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 2px 10px;">
                                    <span style="color: #03a9f4;">{project_details['classificacao'].values[0]}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                
            with col12:
                valor_execucao_projeto = project_details['Execução_do_Projeto'].values[0]
                if valor_execucao_projeto == "0":
                    valor_execucao_projeto = "Não informado"

                st.markdown(f"""
                    <div style="display: block; align-items: center; gap: 10px;">
                        <span>Execução do Projeto:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 2px 10px;">
                            <span style="color: #03a9f4;">{valor_execucao_projeto}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.divider()           
            st.markdown("<h5 style='text-align: left;'>Finalidade do Projeto</h5>", unsafe_allow_html=True)
            st.markdown(f"<h6 style='text-align: left; color: #0097a7;'>{project_details['Objeto_Finalidade'].values[0]}</h6>", unsafe_allow_html=True)
            st.divider()
            def adicionar_pagamento(projeto, data, valor):
                """Adiciona um novo pagamento ao banco de dados."""
                novo_pagamento = pagamentos.insert().values(projeto=projeto, data=data, valor=valor)
                with engine.connect() as connection:
                    connection.execute(novo_pagamento)
                    connection.commit()
                    

            def listar_pagamentos(projeto):
                """Lista todos os pagamentos para um dado projeto."""
                selecao = pagamentos.select().where(pagamentos.c.projeto == projeto)
                with engine.connect() as connection:
                    result = connection.execute(selecao)
                return pd.DataFrame(result.fetchall(), columns=result.keys())

            def remover_pagamento(id):
                """Remove um pagamento específico pelo ID."""
                delete = pagamentos.delete().where(pagamentos.c.id == id)
                with engine.connect() as connection:
                    connection.execute(delete)
                    connection.commit()
    
            df_pagamentos_projeto = pd.read_sql_query("SELECT * FROM pagamentos", engine)

            
            st.subheader('Cronograma de Pagamentos')
                        # Botão para mostrar/esconder gerenciamento de pagamentos
            if st.button("Gerenciar Pagamentos"):
                mostrar_gerenciamento = not st.session_state.get('mostrar_gerenciamento', False)
                st.session_state['mostrar_gerenciamento'] = mostrar_gerenciamento
            st.write("""
                        <style>
                        p.small-text {
                            font-size: 12px; /* Tamanho da fonte */
                            font-weight: 100; /* Peso da fonte */ 
                        }
                        </style>
                        <p class="small-text">Clique no botão para mostrar ou esconder o gerenciamento de pagamentos.</p>
                        """, unsafe_allow_html=True)

            
            # Atualização do df_pagamentos_projeto para garantir que esteja sempre disponível
            #df_pagamentos_projeto = st.session_state.df_pagamentos[st.session_state.df_pagamentos['Projeto'] == selected_project]

            
            
           

            # Função para plotar o gráfico de barras
            def plot_pagamentos(df):
                fig_pagamento = px.bar(df, x='data', y='valor', title="Pagamentos por Mês",
                                    labels={'Valor': 'Valor Pago (RS)', 'Data': 'Data'},
                                    color='valor', color_continuous_scale='Viridis')
                fig_pagamento.update_xaxes(dtick="M1", tickformat="%b\n%Y")
                fig_pagamento.update_layout(xaxis_title='Mês', yaxis_title='Valor Pago (R$)')
                return fig_pagamento

            if st.session_state.get('mostrar_gerenciamento', False):
                # Interface para adicionar um pagamento
                with st.form("add_payment"):
                    projeto = selected_project
                    data_pagamento = st.date_input("Data do Pagamento")
                    valor_pagamento = st.number_input("Valor do Pagamento", min_value=0.0)
                    submitted = st.form_submit_button("Adicionar Pagamento")
                    if submitted:
                        adicionar_pagamento(projeto, data_pagamento, valor_pagamento)

                # Exibe os pagamentos
                df_pagamentos_projeto = listar_pagamentos(selected_project)
                st.write(df_pagamentos_projeto)

                # Interface para remover um pagamento
                id_para_remover = st.selectbox("Selecione o ID do Pagamento para Remover", df_pagamentos_projeto['id'].tolist())
                if st.button("Remover Pagamento"):
                    remover_pagamento(id_para_remover)

            
            st.divider()
            st.plotly_chart(plot_pagamentos(df_pagamentos_projeto), use_container_width=True)
            # Calculate the total value of projects
            valor_total_projetos = df_pagamentos_projeto['valor'].sum()
            # Format the total value as currency
            valor_total_projetos_formatado = locale.currency(valor_total_projetos, grouping=True, symbol=True)
            # Display the total value
            st.write(f"<span style='color: white;'>Valor total de desembolso: </span><span style='color: red;'>{valor_total_projetos_formatado}</span>", unsafe_allow_html=True)
            st.table(df_pagamentos_projeto.style.format({'valor': 'R${:,.2f}'}))
            
    with tab2: #Chat
        st.markdown("<h4 style='text-align: center;'>{}</h4>".format(selected_project), unsafe_allow_html=True)
        # Initialize session states if they are not already set
        # Initialize session states if they are not already set
        if 'projects' not in st.session_state:
            st.session_state['projects'] = load_projects()
        if 'selected_project' not in st.session_state:
            st.session_state['selected_project'] = None  # No project selected by default
        if 'selected_channel' not in st.session_state:
            st.session_state['selected_channel'] = 'Geral'  # Default channel


        # Ensure each project has at least a 'general' channel
        if selected_project not in st.session_state['projects']:
            st.session_state['projects'][selected_project] = {'channels': ['Geral'], 'chat_messages': {'Geral': []}}

        current_project_channels = st.session_state['projects'][selected_project]['channels']
        selected_channel = st.session_state.get('selected_channel', current_project_channels[0])
        col1, col2, col3 = st.columns([1, 4, 1])

        with col1:
            st.write("\n") 
            st.write("\n")   
           # Create new channel
            new_channel = st.text_input("Novo Canal", key=f"new_channel_{selected_project}").capitalize()
            if st.button("Adicionar Canal"):
                if new_channel and new_channel not in current_project_channels:
                    current_project_channels.append(new_channel)
                    st.session_state['projects'][selected_project]['chat_messages'][new_channel] = []
                    get_or_create_project_channels(selected_channel)
                    save_projects()
                    st.experimental_rerun()
                        
            # List channels for selection
            selected_channel = st.radio("Disponiveis", current_project_channels, key=f"radio_{selected_project}")

            #Remove channel button
            if st.button("Remover"):
                remove_channel(selected_project, selected_channel)
                # Optionally, reset the selected channel to 'general' or another default
                st.session_state['selected_channel'] = 'Geral'
                st.experimental_rerun()
        with col3:
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("Esse é o chat do projeto, todos os membros da equipe podem enviar mensagens aqui e ficará salvo no histórico do projeto")
            # Botão para limpar a conversa
            if 'confirm_clear' not in st.session_state:
                st.session_state.confirm_clear = False

            if st.button('Limpar Conversa'):
                st.session_state.confirm_clear = True

            if st.session_state.confirm_clear:
                if st.button('Sim, limpar mensagens'):
                        st.session_state['projects'][selected_project]['chat_messages'][selected_channel] = []
                        save_projects()  # Save the updated messages
                        st.session_state.confirm_clear = False
                        
                        st.experimental_rerun()

                if st.button('Não, manter mensagens'):
                    st.session_state.confirm_clear = False 
        with col2:
            st.header(f"Conversa no #{selected_channel}")
            chat_area = st.container()
            with chat_area:
                messages = st.session_state['projects'][selected_project]['chat_messages'].get(selected_channel, [])
                for msg in messages:
                    timestamp = datetime.fromtimestamp(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    #st.markdown(f"**{msg['user']}**: {msg['message']} _({timestamp})_")
                    st.markdown(f"""
                       <div style="border-left: 2px solid #dedede; margin-left: 10px; padding-left: 10px;">
                            <p style="font-size: 0.9em; color: #888;">{msg['user']} às {timestamp}</p>
                           <p>{msg['message']}</p>
                        </div>
                    """, unsafe_allow_html=True) 
                    

            # Message input for the selected channel
            with st.form(key='new_message_form'):
                new_message = st.text_area("Message", key=f"new_message_{selected_channel}")
                submit_message = st.form_submit_button("Send")
                if submit_message and new_message:
                     # Append the new message to the appropriate channel of the current project
                    st.session_state['projects'][selected_project]['chat_messages'][selected_channel].append({
                        'user': st.session_state["name"],  # Use the logged-in user or a default
                        'message': new_message,
                        'timestamp': time.time()  # Using time.time() for simplicity
                    })
                    save_projects()  # Save the updated messages
                    st.experimental_rerun()
            

                            
            # Exibe o chat (mensagens anteriores + nova mensagem)
            #st.write("Conversa:")
            # Inicie um container para o chat
            
            #chat_container = st.container()
            #with chat_container:
                #for msg in st.session_state.chat_messages[selected_project]:
                 #   # Converta o timestamp para datetime e ajuste o fuso horário conforme necessário
                  #  timestamp = datetime.fromtimestamp(msg["timestamp"], tz=pytz.timezone("America/Sao_Paulo"))
                   # # Formate a hora para exibir
                    #time_str = timestamp.strftime('%H:%M:%S')
                    ## Use st.markdown para exibir as mensagens de uma forma estilizada
                    #st.markdown(f"""
                       # <div style="border-left: 2px solid #dedede; margin-left: 10px; padding-left: 10px;">
                       #     <p style="font-size: 0.9em; color: #888;">{msg['name']} às {time_str}</p>
                      #      <p>{msg['message']}</p>
                     #   </div>
                    #""", unsafe_allow_html=True) 
            figs = [fig_situacao, fig_projetos, fig_pessoas]
            
    with tab4: #Editar Projetos
            col5, col6 = st.columns([6, 3])
            

            with col5:
                st.write("\n")
                st.markdown("<h5 style='text-align: left; color: white;'><i>Projeto Selecionado_</i></h5>", unsafe_allow_html=True)
                st.markdown("<h4 style='text-align: left; color: #2596be;'>{}</h4>".format(selected_project), unsafe_allow_html=True)
                st.divider()
                if 'show_table' not in st.session_state:
                    st.session_state.show_table = False
                    # Botão que alterna a visibilidade das observações
                if st.button('Abrir Planilha'):
                    st.session_state.show_table = not st.session_state.show_table

                    # Se a variável de estado 'show_observations' for True, mostre as observações
                if st.session_state.show_table:
                    st.write(df) 


            # Inicializar o estado (se ainda não estiver definido)
            if 'show_form' not in st.session_state:
                st.session_state.show_form = False
            with col6:
                # Botão para adicionar novo projeto
                if st.button('Novo Projeto'):
                    st.session_state.show_new_project_form = True
                if st.button('Editar Projeto'):
                    st.session_state.show_form = True
                if st.button('Deletar Projeto'):
                    st.session_state.show_delete_confirmation = True

            # Exibir formulário para novo projeto
            if st.session_state.get('show_new_project_form', False):
                   with st.form(key='new_project_form'):
                        # Inicializa um dicionário para os dados do novo projeto
                        new_project_data = {}
                        
                        # Loop pelos nomes das colunas para criar os widgets de entrada apropriados
                        for column in df.columns:
                            if column == 'Valor':
                                input_value = st.number_input(f"{column} (novo projeto)", step=1.0, format="%.2f")
                                new_project_data[column] = input_value if input_value else 0.0
                            elif column == 'id':
                                continue
                            elif column == 'Situação_atual':
                                situacao_options = ['Pre Produção', 'Produção', 'Pós Produção', 'Relatório da Comissão Gestora', 'Prestação de Contas', 'Encerrado']
                                new_project_data[column] = st.selectbox(f"{column} (novo projeto)", situacao_options)
                            elif column == 'Unidade_SECTI_Responsavel':
                                unidade_options = ['DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID']
                                new_project_data[column] = st.selectbox(f"{column} (novo projeto)", unidade_options)
                            elif column == 'Unidade_SECTI_adicional':
                                unidade_options = ['Sem Colaboração','DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID']
                                new_project_data[column] = st.selectbox(f"{column} (novo projeto)", unidade_options)
                            elif column == 'Processo_SEI':
                                sei_input = st.text_input(f"{column} (Adicione Apenas Números)", max_chars=19)
                                sei_formatted = f"{sei_input[:5]}-{sei_input[5:13]}/{sei_input[13:17]}-{sei_input[17:]}" if sei_input else "0"
                                new_project_data[column] = sei_formatted
                            elif column == 'classificacao':
                                classificacao_options = ['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos', 'Apoio', 'Edital de Credenciamente','Convênio/Acordo de Cooperação Técnica']
                                new_project_data[column] = st.selectbox(f"{column} (novo projeto)", classificacao_options)
                            else:
                                text_input = st.text_input(f"{column} (novo projeto)")
                                new_project_data[column] = text_input if text_input is not None else "0"

                            # Botões para adicionar ou cancelar o novo projeto
                        submit_new_project = st.form_submit_button('Adicionar Projeto')
                        close_new_project_form = st.form_submit_button('Cancelar')

                     
                        # Substitui campos vazios ou None por um traço ou 0 conforme necessário
                        for key, value in new_project_data.items():
                            if value == "" or value is None:
                                new_project_data[key] = "0" if key == 'Valor' else "-"

                        # Prepara os valores para a inserção, garantindo que todos os campos sejam tratados corretamente
                        # Remove a coluna 'Projeto_truncated', se existir, do dicionário
                        new_project_data.pop('Projeto_truncated', None)
                        placeholders = ", ".join([f":{key}" for key in new_project_data.keys()])
                        columns = ", ".join([f"{key}" for key in new_project_data.keys()])
                        insert_statement = f"INSERT INTO Projetos ({columns}) VALUES ({placeholders})"
                        if submit_new_project:
                            # Cria uma conexão com o banco de dados
                            with engine.connect() as conn:
                                trans = conn.begin()
                                try:
                                    # Executa a instrução de inserção
                                    conn.execute(text(insert_statement), new_project_data)
                                    trans.commit()
                                    st.success("Novo projeto adicionado com sucesso!")
                                    st.session_state.show_new_project_form = False  # Fecha o formulário de novo projeto
                                    # Considerar o uso de st.experimental_rerun() para recarregar a página/aplicativo
                                    st.write(new_project_data)
                                    st.write(list(new_project_data.keys()))
                                    st.write(insert_statement)
                                    st.write(placeholders)
                                    st.write(columns)
                                except Exception as e:
                                    trans.rollback()  # Reverte a transação em caso de erro
                                    st.error(f"Ocorreu um erro: {e}")

                        if close_new_project_form:
                            # Se cancelar, apenas fecha o formulário de novo projeto
                            st.session_state.show_new_project_form = False




            # Verificar se um projeto foi selecionado
            if selected_project:
                project_details = project_details

            # Botão para mostrar o formulário
                 
                if st.session_state.show_form:
                    with st.form(key='edit_form'):
                        # Use um dicionário de compreensão para criar os campos de entrada, exceto para 'classificação' e 'Situação_atual'
                        df.drop(['Projeto_truncated'], axis=1, inplace=True)
                        new_values = {column: st.text_input(column, project_details[column].iloc[0])
                                      for column in df.columns 
                                      if column not in ['id', 'classificacao', 'Situação_atual', 'Unidade_SECTI_Responsavel', 'Unidade_SECTI_adicional','Processo_SEI', 'Valor']}
                        
                        # Campo de entrada para o Processo_SEI com formatação
                        sei_input = st.text_input("Processo SEI (Adicione Apenas Números)", value=project_details['Processo_SEI'].iloc[0].replace("-", "").replace("/", ""), max_chars=19)
                        sei_formatted = f"{sei_input[:5]}-{sei_input[5:13]}/{sei_input[13:17]}-{sei_input[17:]}"
                        new_values['Processo_SEI'] = sei_formatted


                        # Adicione um selectbox para 'classificação' com as opções desejadas
                        new_values['Valor'] = st.number_input('Valor', value=int(float(project_details['Valor'].iloc[0])) if project_details['Valor'].iloc[0] is not None else 0)
                        new_values['classificacao'] = st.selectbox(
                            'Classificação',
                            ['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos', 'Apoio', 'Edital de Credenciamente','Convênio/Acordo de Cooperação Técnica'],
                            index=['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos', 'Apoio', 'Edital de Credenciamente','Convênio/Acordo de Cooperação Técnica'].index(project_details['classificacao'].iloc[0]) if project_details['classificacao'].iloc[0] in ['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos', 'Apoio', 'Edital de Credenciamente','Convênio/Acordo de Cooperação Técnica'] else 0
                        )
                        new_values['Situação_atual'] = st.selectbox('Situação_atual', ['Pre Produção', 'Produção', 'Pós Produção', 'Relatório da Comissão Gestora', 'Prestação de Contas', 'Encerrado'],
                             index=['Pre Produção', 'Produção', 'Pós Produção', 'Relatório da Comissão Gestora', 'Prestação de Contas', 'Encerrado' ].index(project_details['Situação_atual'].iloc[0]) if project_details['Situação_atual'].iloc[0] in ['Pre Produção', 'Produção', 'Pós Produção', 'Relatório da Comissão Gestora', 'Prestação de Contas','Encerrado'] else 0
                        )
                        new_values['Unidade_SECTI_Responsavel'] = st.selectbox('Unidade_SECTI_Responsavel', ['DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID'],
                            index=['DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID'].index(project_details['Unidade_SECTI_Responsavel'].iloc[0]) if project_details['Unidade_SECTI_Responsavel'].iloc[0] in ['DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID'] else 0
                        )
                        new_values['Unidade_SECTI_adicional'] = st.selectbox('Unidade_SECTI_adicional', ['Sem Colaboração','DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID'],
                            index=['Sem Colaboração','DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID'].index(project_details['Unidade_SECTI_adicional'].iloc[0]) if project_details['Unidade_SECTI_adicional'].iloc[0] in ['Sem Colaboração','DIDCI', 'DIJE', 'SUPCDT', 'DIEC', 'SICID'] else 0
                        )
                        submit_button = st.form_submit_button('Salvar Alterações')
                        close_form_button = st.form_submit_button('Fechar Formulário')

                        # Cria uma conexão com o banco de dados
                        with engine.connect() as conn:
                            # Inicia uma transação
                            trans = conn.begin()
                            try:
                                # Prepara os dados para a atualização
                                update_values = new_values.copy()
                                update_values['Valor'] = int(update_values['Valor'])
                                update_values['id'] = int(project_details['id'])

                                # Prepara a string de atualização SQL de forma segura para evitar SQL Injection
                                set_parts = ", ".join([f"{key} = :{key}" for key in update_values.keys() if key != 'id'])
                                update_statement = f"UPDATE Projetos SET {set_parts} WHERE id = :id"

                                if submit_button:
                                    # Executa a instrução de atualização
                                    result = conn.execute(text(update_statement), update_values)
                                    trans.commit()  # Commit apenas se não houver exceção
                                    st.success("Projeto atualizado com sucesso!")
                                    # Considerar o uso de st.experimental_rerun() ao invés de time.sleep() para recarregar a página
                                    time.sleep(2)
                                    st.experimental_rerun()
                            except Exception as e:
                                trans.rollback()  # Rollback em caso de erro
                                st.error(f"An error occurred: {e}")
                            

                        if close_form_button:
                            st.session_state.show_form = False

                # Botão para mostrar a opção de deletar

                # Se a opção de deletar foi selecionada, mostrar a confirmação
                if st.session_state.get('show_delete_confirmation', False):
                    # Mostrar mensagem de confirmação
                    st.warning("Você tem certeza de que deseja deletar este projeto?")
                    
                    # Botão para confirmar a ação de deletar
                    if st.button('Sim, deletar'):
                        delete_statement = text("DELETE FROM Projetos WHERE id = :id")  # Substitua 'table_name' pelo nome da sua tabela e 'id' pelo nome da coluna de identificação
                        st.session_state.show_delete_confirmation = True
                        # Executa a instrução DELETE SQL
                        # Executa a instrução DELETE SQL
                        with engine.connect() as conn:
                            trans = conn.begin()
                            id_value = int(project_details.id.values[0]) # Convert numpy.int64 to Python int
                            result = conn.execute(delete_statement, {'id': id_value})
                            trans.commit()                      
                        st.session_state.show_delete_confirmation = False  # Esconder a confirmação
                        st.session_state.show_success_message = True  # Mostrar mensagem de sucesso temporariamente
                        time.sleep(2)
                        st.experimental_rerun() # Recarregar a página para atualizar a tabela de projetos

                    # Botão para cancelar a ação de deletar
                    if st.button('Não, cancelar'):
                        st.session_state.show_delete_confirmation = False  # Esconder a confirmação

                # Se a mensagem de sucesso deve ser mostrada
                if st.session_state.get('show_success_message', False):
                    st.success("Projeto deletado com sucesso!")
                    # Aqui você pode usar um timer para esconder a mensagem após alguns segundos ou deixar que o usuário feche manualmente
                    # Por exemplo, para esconder após 5 segundos (não é uma função nativa do Streamlit, é apenas um exemplo hipotético)
                    st.session_state.show_success_message = False
                    time.sleep(2)
                    st.experimental_rerun()

                # (Opcional) Botão para o usuário fechar a mensagem de sucesso manualmente
                if st.session_state.get('show_success_message', False) and st.button('Fechar mensagem de sucesso'):
                    st.session_state.show_success_message = False



            elif st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')

            elif st.session_state["authentication_status"] is None:
                st.warning('Please enter your username and password')
    with tab5: #Logout
        authenticator.logout()
