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


timezone = pytz.timezone("America/Sao_Paulo")

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

# Definir configurações da página
st.set_page_config(
   page_title='Dashboard SECTI',
   layout='wide',  # Ativa o layout wide
   initial_sidebar_state='auto'  # Define o estado inicial da sidebar (pode ser 'auto', 'expanded', 'collapsed')
)


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
    tab1, tab2, tab3, tab6, tab4, tab5 = st.tabs(["Home", "👥 Chat", "📓 Projetos","🪐 Planetário", "✏️ Editar", "❌ Sair"])
    css = '''
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1rem;
        }
    </style>
    '''

    st.markdown(css, unsafe_allow_html=True)
    
    # Setup a search box
    search_query = st.sidebar.text_input("Busca", "")

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

    # Inicializa o estado da sessão para armazenar as mensagens se ainda não existir
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = {}

    # Inicializa uma lista vazia para o projeto atual se ainda não existir
    if selected_project not in st.session_state.chat_messages:
        st.session_state.chat_messages[selected_project] = []
    numero_de_projetos = df['Projeto'].count()
    numero_de_projetos_em_andamento = df[df['classificacao'] == 'Em Andamento']['Projeto'].count()
    numero_de_projetos_emendas = df[df['classificacao'] == 'Emendas Parlamentares']['Projeto'].count()
    numero_de_projetos_eventos = df[df['classificacao'] == 'Eventos']['Projeto'].count()
    numero_de_projetos_novos = df[df['classificacao'] == 'Novos Projetos']['Projeto'].count()
    numero_de_projetos_concluidos = df[df['Situação atual'] == 'Concluído']['Projeto'].count()
# Calculate the total value of projects in progress
    valor_total_projetos_andamento = df[df['classificacao'] == 'Em Andamento']['Valor'].sum()
    valor_total_projetos_andamento_emendas = df[df['classificacao'] == 'Emendas Parlamentares']['Valor'].sum()
    valor_total_projetos_andamento_eventos = df[df['classificacao'] == 'Eventos']['Valor'].sum()
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
                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Instituição Parceira'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Primeiro Execução do Projeto</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Execução do Projeto'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Unidade SECTI</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #0097a7;'>{project_details['Unidade SECTI Responsável'].values[0]}</h6>", unsafe_allow_html=True)
                
                st.write("\n")
                st.write("\n")
    
            with col3:
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Encerramento de Parceria</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{project_details['Encerramento da parceria'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Ponto Focal na Instituição Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{project_details['Ponto Focal na Instituição Parceira'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Mais Informações sobre o fomento</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: #ffb74d;'>{project_details['Mais informações do fomento'].values[0]}</h6>", unsafe_allow_html=True)
      
                # Para centralizar os nomes e adicionar espaço
                nomes = project_details['Comissão Gestora da Parceria'].values[0].split(',')

               
            
            st.divider()   
            col1, col2, col3, col4, col5, col6 = st.columns([4, 1, 4, 4, 1, 4])
            with col1:
                with elements("card_container"):
                    with mui.Card(key="card1",style={"borderRadius": "10px","border": "1px solid #0e1117", "boxShadow": "none", "backgroundColor": "transparent"}):
                        mui.CardContent([
                        mui.Typography("Observações", style={"textAlign": "center","fontFamily": "'Roboto', sans-serif", "fontWeight": "bold", "color": "white", "marginBottom": "20px"}),
                        mui.Typography(project_details['Observações'].values[0], style={"marginTop": "16px", "color": "gray", "fontFamily": "'sans serif', sans-serif", "fontSize": "14px"}),
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
            
            
            with col4:
                    st.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 1rem 0;">
                        <span style="font-size: 1.35rem; font-weight: bold; color: white; margin-bottom: 0.5rem;">Fonte de Custeio</span>
                        <span style="background-color: #1B1F23 ; padding: 0.25rem 0.75rem; border-radius: 10px; color: gray; font-weight: bold; font-size: 1.25rem;">{project_details['Fonte de Custeio'].values[0]}</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                    st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 1rem 0;">
                    <span style="font-size: 1.35rem; font-weight: bold; color: white; margin-bottom: 0.5rem;">Situação Atual</span>
                    <span style="background-color: #1B1F23 ; padding: 0.25rem 0.75rem; border-radius: 10px; color: #388e3c; font-weight: bold; font-size: 1.25rem;">{project_details['Situação atual'].values[0]}</span>
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
                st.markdown(f"""
                            <div style="display: block; align-items: center; gap: 10px;">
                                <span>Execução do Projeto:</span>
                                <div style="background-color: #1B1F23; border-radius: 10px; padding: 2px 10px;">
                                    <span style="color: #03a9f4;">{project_details['Execução do Projeto'].values[0]}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            st.divider()           
            st.markdown("<h5 style='text-align: left;'>Finalidade do Projeto</h5>", unsafe_allow_html=True)
            st.markdown(f"<h6 style='text-align: left; color: #0097a7;'>{project_details['Objeto/Finalidade'].values[0]}</h6>", unsafe_allow_html=True)
                
    with tab2: #Chat
        st.markdown("<h4 style='text-align: center;'>{}</h4>".format(selected_project), unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 4, 1])
        with col3:
            st.write("Esse é o chat do projeto, todos os membros da equipe podem enviar mensagens aqui e ficará salvo no histórico do projeto")
            # Botão para limpar a conversa
            if 'confirm_clear' not in st.session_state:
                st.session_state.confirm_clear = False

            if st.button('Limpar Conversa'):
                st.session_state.confirm_clear = True

            if st.session_state.confirm_clear:
                if st.button('Sim, limpar mensagens'):
                        st.session_state.chat_messages[selected_project] = []
                        st.session_state.confirm_clear = False
                        st.experimental_rerun()

                if st.button('Não, manter mensagens'):
                    st.session_state.confirm_clear = False 
        with col2:
            # Crie um formulário para o input de mensagem e botão de envio
            with st.form(key=f"form_message_{selected_project}"):
                new_message = st.text_input("Digite sua mensagem", key=f"message_input_{selected_project}")
                submit_button = st.form_submit_button("Enviar")
                                    
            # Adiciona nova mensagem à lista de mensagens do projeto atual
            if submit_button and new_message:
                # Certifique-se de que cada projeto tem sua lista de mensagens
                if selected_project not in st.session_state.chat_messages:
                    st.session_state.chat_messages[selected_project] = []

                st.session_state.chat_messages[selected_project].append({
                    "user": st.session_state.username,  # Supondo que você armazene o nome de usuário em st.session_state.username
                    "name": st.session_state.name,  # Supondo que você armazene o nome do usuário em st.session_state.name
                    "message": new_message,
                    "timestamp": time.time()  # Adiciona um timestamp para cada mensagem
                })
                
                # Salva as mensagens após adicionar a nova
                save_messages(st.session_state.chat_messages)
                
                # Limpa o campo de input após o envio da mensagem
                st.experimental_rerun()
            

                            
            # Exibe o chat (mensagens anteriores + nova mensagem)
            st.write("Conversa:")
            # Inicie um container para o chat
            
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.chat_messages[selected_project]:
                    # Converta o timestamp para datetime e ajuste o fuso horário conforme necessário
                    timestamp = datetime.fromtimestamp(msg["timestamp"], tz=pytz.timezone("America/Sao_Paulo"))
                    # Formate a hora para exibir
                    time_str = timestamp.strftime('%H:%M:%S')
                    # Use st.markdown para exibir as mensagens de uma forma estilizada
                    st.markdown(f"""
                        <div style="border-left: 2px solid #dedede; margin-left: 10px; padding-left: 10px;">
                            <p style="font-size: 0.9em; color: #888;">{msg['name']} às {time_str}</p>
                            <p>{msg['message']}</p>
                        </div>
                    """, unsafe_allow_html=True) 

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
                                classificacao_options = ['Em Andamento', 'Eventos', 'Emendas Parlamentares', 'Novos Projetos']
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
                            ['Em Andamento', 'Eventos', 'Emendas Parlamentares', 'Novos Projetos'],
                            index=['Em Andamento', 'Eventos', 'Emendas Parlamentares', 'Novos Projetos'].index(project_details['classificacao']) if project_details['classificacao'] in ['Em Andamento', 'Eventos', 'Emendas Parlamentares', 'Novos Projetos'] else 0
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
    with tab6: #Planetário
       
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
        # Adicionar uma nova coluna que representa o dia da semana
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
        
        

        if selected_month_year == "Todos os Meses":
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
        else:
            mes['Cúpula'] = mes['Cúpula'].replace(0, 'Em Manutenção')
            # Filter the DataFrame based on the selected month-year
            selected_month_data = relatorio2023[relatorio2023['MonthYear'] == selected_month_year]
            selected_month_data2 = mes[mes['MonthYear'] == selected_month_year]

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
                    annotations=[dict(text='Visitas', x=0.5, y=0.5, font_size=20, showarrow=False)]
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
            




# Display project details based on selection in the sidebar
# ... (You'll need to implement the logic to display the details)
# You can create placeholder widgets and update them later with the project details
# when a user clicks on a project name in the sidebar

# Run the Streamlit app using the command in the terminal:
# streamlit run your_app.py