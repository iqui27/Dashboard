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

DATA_FILE_PATH = 'planetario2024.csv'


timezone = pytz.timezone("America/Sao_Paulo")
# Definir configurações da página
st.set_page_config(
   page_title='Dashboard SECTI',
   layout='wide',  # Ativa o layout wide
   initial_sidebar_state='auto',  # Define o estado inicial da sidebar (pode ser 'auto', 'expanded', 'collapsed')
   page_icon='📓 '  # Ícone da barra lateral
)



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

        # Função para adicionar estilos personalizados ao aplicativo
def add_custom_css():
    # Você pode personalizar esses estilos conforme necessário
    st.markdown("""
        <style>
        .stTextInput, .stSelectbox, .stDateInput, .stNumberInput, .stTextarea {
            margin-bottom: 10px;
        }
        .stButton > button {
            width: 100%;
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Adicionar estilos personalizados
add_custom_css()

# Função para carregar mensagens salvas
def load_messages():
    try:
        with open('messages.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

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
df = pd.read_csv("Dashboard.csv")
ra = pd.read_csv("RA.csv")
relatorio2023 = pd.read_csv("Relatorio2023.csv")
mes = pd.read_csv("mes.csv")
estado = pd.read_csv("outroestado.csv")

# Defina um caminho para o arquivo CSV
csv_file_path = "Dashboard.csv"

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv("Dashboard.csv")
    

# Verificação de status de login
if st.session_state["authentication_status"]:
    st.image('ID_SECTI.png', width=200)
    st.write(f'Bem-vindo *{st.session_state["name"]}*')   
    # Configurar o locale para usar o formato de moeda brasileiro
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    # Initialize the Streamlit interface
    st.sidebar.title("Projetos")

    # Cria uma barra de navegação com abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", "👥 Chat", "📊 Dashboard","✏️ Editar", "❌ Sair"])
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

    # Filter projects based on search query
    filtered_projects = df[df['Projeto'].str.contains(search_query, case=False)]

    # Group filtered projects by classification
    grouped_filtered_projects = filtered_projects.groupby('classificacao')

    # Display filtered projects in the sidebar grouped by classification
    st.sidebar.subheader("Classificação")
    selected_classification = st.sidebar.selectbox("Selecione uma Classificação", grouped_filtered_projects.groups.keys())
    if selected_classification:
        projects = grouped_filtered_projects.get_group(selected_classification)
        selected_project = st.sidebar.radio("Selecione um Projeto", projects['Projeto'], index=0)
        if selected_project:
            project_details = projects[projects['Projeto'] == selected_project]
            valor_formatado = locale.currency(project_details['Valor'].values[0], grouping=True)

        else:
            project_details = None
            valor_formatado = None
            elected_project = "Nenhum projeto selecionado"

    # Ordenar o DataFrame pela coluna "classificacao"
    df_sorted = df.sort_values('classificacao')

    # Group projects by classification
    grouped_projects = df_sorted.groupby('classificacao')

    # Lista de estados brasileiros
    estados_brasil = [
        'Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal', 
        'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 
        'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 
        'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 
        'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins'
        ]


    # Inicializa uma lista vazia para o projeto atual se ainda não existir
    numero_de_projetos = df['Projeto'].count()
    numero_de_projetos_em_andamento = df[df['classificacao'] == 'Termo de Fomento']['Projeto'].count()
    numero_de_projetos_emendas = df[df['classificacao'] == 'Termo de Colaboração']['Projeto'].count()
    numero_de_projetos_eventos = df[df['classificacao'] == 'Convênio']['Projeto'].count()
    numero_de_projetos_novos = df[df['classificacao'] == 'Novos Projetos']['Projeto'].count()
    numero_de_projetos_concluidos = df[df['Situação atual'] == 'Concluído']['Projeto'].count()
    # Calculate the total value of projects in progress
    valor_total_projetos_andamento = df[df['classificacao'] == 'Termo de Fomento']['Valor'].sum()
    valor_total_projetos_andamento_emendas = df[df['classificacao'] == 'Termo de Colaboração']['Valor'].sum()
    valor_total_projetos_andamento_eventos = df[df['classificacao'] == 'Convênio']['Valor'].sum()
    valor_total_projetos_andamento_novos = df[df['classificacao'] == 'Novos Projetos']['Valor'].sum()
    valor_total_projetos_andamento_concluidos = df[df['Situação atual'] == 'Concluído']['Valor'].sum()
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
                    <span>Projetos em andamento:</span>
                    <div>{numero_de_projetos_em_andamento}</div>
                </div>
                """, unsafe_allow_html=True)

                # Repita para as demais categorias
                st.markdown(f"""
                <div class="stats">
                    <span>Projetos de emendas parlamentares:</span>
                    <div>{numero_de_projetos_emendas}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="stats">
                    <span>Projetos de eventos:</span>
                    <div>{numero_de_projetos_eventos}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="stats">
                    <span>Projetos novos:</span>
                    <div>{numero_de_projetos_novos}</div>
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
                        <span>Valor total dos projetos em andamento:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>Valor total dos projetos de emendas parlamentares:</span>
                        <div style="background-color: #1B1F23; border-radius: 10px; padding: 4px 12px;">
                            <span style="color: #26D367;">{valor_total_projetos_andamento_emendas_formatado}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span>Valor total dos projetos de eventos:</span>
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


               
            


            # Suponha que 'df' seja o seu DataFrame e que ele tem colunas 'Projeto', 'Valor', 'Classificação' e 'Unidade SECTI Responsável'
            # Certifique-se de que os valores estão em formato numérico e não há valores NaN
            st.divider()
            df.dropna(subset=['Valor'], inplace=True)
            df['Valor'] = df['Valor'].astype(float)

            # Toggle para habilitar ou desabilitar os filtros
            enable_classificacao_filter = st.checkbox("Filtrar por Classificação")
            enable_unidade_filter = st.checkbox("Filtrar por Unidade SECTI Responsável")

            if enable_classificacao_filter:
                # Opções de classificação
                classificacoes = df['classificacao'].unique()

                # Widget de seleção de classificação
                selected_classificacao = st.selectbox('Selecione a Classificação', classificacoes)

            if enable_unidade_filter:
                # Opções de Unidade SECTI Responsável
                unidades = df['Unidade SECTI Responsável'].unique()

                # Widget de seleção de Unidade SECTI Responsável
                selected_unidade = st.selectbox('Selecione a Unidade SECTI Responsável', unidades)

            # Filtrar o DataFrame com base nos filtros selecionados
            if enable_classificacao_filter and enable_unidade_filter:
                filtered_df = df[(df['classificacao'] == selected_classificacao) & (df['Unidade SECTI Responsável'] == selected_unidade)]
            elif enable_classificacao_filter:
                filtered_df = df[df['classificacao'] == selected_classificacao]
            elif enable_unidade_filter:
                filtered_df = df[df['Unidade SECTI Responsável'] == selected_unidade]
            else:
                filtered_df = df

            # Crie um gráfico de barras usando st.bar_chart
            st.bar_chart(filtered_df.set_index('Projeto')['Valor'], height=500)


    

            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")

            # Agrupar projetos por situação atual e contar quantos projetos estão em cada categoria
            situacao_counts = df['Situação atual'].value_counts()

            # Convertendo o resultado para um DataFrame, que é necessário para o st.bar_chart()
            situacao_df = pd.DataFrame({'Número de Projetos': situacao_counts})

            # Exibir o gráfico de barras no Streamlit
            st.bar_chart(situacao_df,height=400, color='#fd0')

    with tab3:
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            col1, col2, col3 = st.columns([3, 6, 3])
           

            # Main Area
            mais_info = project_details['Mais informações do fomento'].values[0]
            
            with col2:
                st.markdown("<h1 style='text-align: center;'>{}</h1>".format(selected_project), unsafe_allow_html=True)
                st.markdown("<h3 style='text-align: center;'>{}</h3>".format(project_details['Fomento'].values[0]), unsafe_allow_html=True)
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
                #    <span style="font-size: 1.10rem; font-weight: light; color: white; margin-bottom: 0rem;">Processo SEI</span>
                #    <span style="background-color: #1B1F23 ; padding: 0.25rem 3.75rem; border-radius: 10px; color: yellow; font-weight: light; font-size: 1.15rem;">{project_details['Processo SEI'].values[0]}</span>
                #</div>
                #""", unsafe_allow_html=True)
                st.write("\n")
                
                
            with col1:
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Primeiro Intituicao Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Instituição Parceira'].values[0] if project_details['Instituição Parceira'].values[0] != '0' else 'Não informado'}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Primeiro Execução do Projeto</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Execução do Projeto'].values[0] if project_details['Execução do Projeto'].values[0] != '0' else 'Não informado'}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Unidade SECTI</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Unidade SECTI Responsável'].values[0] if project_details['Unidade SECTI Responsável'].values[0] != '0' else 'Não informado'}</h6>", unsafe_allow_html=True)
                
                st.write("\n")
                st.write("\n")
    
            with col3:
                valor_encerramento = project_details['Encerramento da parceria'].values[0]
                if valor_encerramento == "0":
                    valor_encerramento = "Não informado"

                valor_ponto_focal = project_details['Ponto Focal na Instituição Parceira'].values[0]
                if valor_ponto_focal == "0":
                    valor_ponto_focal = "Não informado"

                valor_mais_informacoes = project_details['Mais informações do fomento'].values[0]
                if valor_mais_informacoes == "0":
                    valor_mais_informacoes = "Não informado"

                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Encerramento de Parceria</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{valor_encerramento}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Ponto Focal na Instituição Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{valor_ponto_focal}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Mais Informações sobre o fomento</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{valor_mais_informacoes}</h6>", unsafe_allow_html=True)
      
                # Para centralizar os nomes e adicionar espaço
                nomes = project_details['Comissão Gestora da Parceria'].values[0].split(',')
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
                            mui.Typography("Comissão Gestora da Parceria", style={"textAlign": "center", "fontSize": "17px", "fontFamily": "'sans serif', sans-serif" , "fontWeight": "bold", "color": "white", "marginBottom": "20px"})

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
            
            
            valor_fonte_custeio = project_details['Fonte de Custeio'].values[0]
            if valor_fonte_custeio == "0":
                valor_fonte_custeio = "Não informado"

            valor_situacao_atual = project_details['Situação atual'].values[0]
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
                                    <span style="color: #03a9f4;">{project_details['Processo SEI'].values[0]}</span>
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
                valor_execucao_projeto = project_details['Execução do Projeto'].values[0]
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
            st.markdown(f"<h6 style='text-align: left; color: #0097a7;'>{project_details['Objeto/Finalidade'].values[0]}</h6>", unsafe_allow_html=True)
                
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
            if st.button("Adicionar"):
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

    with tab4: #Editar Projetos
            col5, col6 = st.columns([6, 3])
            

            with col5:
                st.markdown("<h3 style='text-align: left; color: yellow;'>{}</h3>".format(selected_project), unsafe_allow_html=True)
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
                                # Campo para valor com entrada numérica
                                new_project_data[column] = st.number_input(f"{column} (novo projeto)", step=1.0, format="%.2f")
                            elif column == 'Processo SEI':
                                # Campo para processo SEI com preenchimento automático do padrão
                                sei_input = st.text_input(f"{column} (Adicione Apenas Números)", max_chars=17)
                                sei_formatted = f"{sei_input[:5]}-{sei_input[5:13]}/{sei_input[13:17]}-{sei_input[17:]}"
                                new_project_data[column] = sei_formatted
                            elif column == 'classificacao':
                                # Campo de seleção para classificação com opções pré-definidas
                                classificacao_options = ['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos']
                                new_project_data[column] = st.selectbox(f"{column} (novo projeto)", classificacao_options)
                            else:
                                # Campo de texto padrão para as outras colunas
                                new_project_data[column] = st.text_input(f"{column} (novo projeto)")

                            # Botões para adicionar ou cancelar o novo projeto
                        submit_new_project = st.form_submit_button('Adicionar Projeto')
                        close_new_project_form = st.form_submit_button('Cancelar')

                        if submit_new_project:
                             # Replace empty fields with a dash
                            for key, value in new_project_data.items():
                                if value == "":
                                    new_project_data[key] = "-"

                            # Adiciona o novo projeto ao dataframe
                            new_row = pd.DataFrame([new_project_data])
                            df = pd.concat([df, new_row], ignore_index=True)
                            
                            # Salva o dataframe atualizado no arquivo CSV
                            df.to_csv(csv_file_path, index=False)
                            
                            # Informa sucesso e reinicia a aplicação
                            st.success("Novo projeto adicionado com sucesso!")
                            st.session_state.show_new_project_form = False  # Fecha o formulário de novo projeto
                            time.sleep(2)  # Dá uma pausa para mostrar a mensagem de sucesso
                            st.experimental_rerun()  # Reinicia a aplicação para mostrar as mudanças

                        if close_new_project_form:
                            # Se cancelar, apenas fecha o formulário de novo projeto
                            st.session_state.show_new_project_form = False




            # Verificar se um projeto foi selecionado
            if selected_project:
                project_details = df[df['Projeto'] == selected_project].iloc[0]

            # Botão para mostrar o formulário
                    
                if st.session_state.show_form:
                    with st.form(key='edit_form'):
                        # Use um dicionário de compreensão para criar os campos de entrada, exceto para 'classificação'
                        new_values = {column: st.text_input(column, project_details[column]) for column in df.columns if column != 'classificacao'}
                        
                        # Adicione um selectbox para 'classificação' com as opções desejadas
                        new_values['classificacao'] = st.selectbox(
                            'Classificação',
                            ['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos'],
                            index=['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos'].index(project_details['classificacao']) if project_details['classificacao'] in ['Termo de Fomento', 'Convênio', 'Termo de Colaboração', 'Novos Projetos'] else 0
                        )
    
                        submit_button = st.form_submit_button('Salvar Alterações')
                        close_form_button = st.form_submit_button('Fechar Formulário')

                        if submit_button:
                            for column in df.columns:
                                df.at[project_details.name, column] = new_values[column]
                            st.session_state.show_form = False
                            df.to_csv(csv_file_path, index=False)
                            st.success("Projeto atualizado com sucesso!")
                            time.sleep(2)  # Sleep for 1 second to show the success message
                            st.experimental_rerun()

                        if close_form_button:
                            st.session_state.show_form = False

                # Botão para mostrar a opção de deletar

                # Se a opção de deletar foi selecionada, mostrar a confirmação
                if st.session_state.get('show_delete_confirmation', False):
                    # Mostrar mensagem de confirmação
                    st.warning("Você tem certeza de que deseja deletar este projeto?")
                    
                    # Botão para confirmar a ação de deletar
                    if st.button('Sim, deletar'):
                        df.drop(project_details.name, inplace=True)
                        st.session_state.show_delete_confirmation = True
                        df.to_csv(csv_file_path, index=False)
                        st.session_state.show_delete_confirmation = False  # Esconder a confirmação
                        st.session_state.show_success_message = True  # Mostrar mensagem de sucesso temporariamente

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
