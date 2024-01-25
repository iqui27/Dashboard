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

df = pd.read_csv("Dashboard.csv")
# Defina um caminho para o arquivo CSV
csv_file_path = "Dashboard.csv"

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv("Dashboard.csv")

# Verificação de status de login
if st.session_state["authentication_status"]:
    st.write(f'Bem-vindo *{st.session_state["name"]}*')
    # Configurar o locale para usar o formato de moeda brasileiro
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    # Initialize the Streamlit interface
    st.sidebar.title("Projetos")

    # Cria uma barra de navegação com abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", "Chat", "Projetos", "Editar", "Sair"])

    
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

    with tab1:
        st.header("Bem vindo ao Dashboard SECTI")
        st.write("Aqui você pode acompanhar os projetos da SECTI")
        st.write("Para começar, selecione um projeto na barra lateral")

        # Suponha que 'df' seja o seu DataFrame e que ele tem colunas 'Projeto' e 'Valor'
        # Certifique-se de que os valores estão em formato numérico e não há valores NaN
        df.dropna(subset=['Valor'], inplace=True)
        df['Valor'] = df['Valor'].astype(float)

        # Crie um gráfico de barras usando st.bar_chart
        st.bar_chart(df.set_index('Projeto')['Valor'], height=500)

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
            col1, col2, col3 = st.columns([3, 6, 3])

            # Main Area
            mais_info = project_details['Mais informações do fomento'].values[0]
                
            with col2:
                st.markdown("<h1 style='text-align: center;'>{}</h1>".format(selected_project), unsafe_allow_html=True)
                st.markdown("<h3 style='text-align: center;'>{}</h3>".format(project_details['Fomento'].values[0]), unsafe_allow_html=True)
                st.write("\n")
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="display: inline-block; margin: auto;">
                        <div style="font-size: 30px; color: white;">Valor</div>
                        <div style="font-size: 50px;">{valor_formatado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.write("\n")
                st.divider()
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Fonte de Custeio</h5>", unsafe_allow_html=True)
                st.markdown("<h5 style='text-align: center;'>{}</h5>".format(project_details['Fonte de Custeio'].values[0]), unsafe_allow_html=True)
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Situação Atual</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: Green;'>{project_details['Situação atual'].values[0]}</h6>", unsafe_allow_html=True)

                
            with col1:
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Primeiro Intituicao Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: yellow;'>{project_details['Instituição Parceira'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Primeiro Execução do Projeto</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: yellow;'>{project_details['Execução do Projeto'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Unidade SECTI</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: yellow;'>{project_details['Unidade SECTI Responsável'].values[0]}</h6>", unsafe_allow_html=True)
                
                st.write("\n")
                st.write("\n")
                with elements("card_container"):
                    with mui.Card(key="card1",style={"borderRadius": "10px","border": "1px solid #0e1117", "boxShadow": "none", "backgroundColor": "transparent"}):
                        mui.CardContent([
                            mui.Typography("Observações", style={"textAlign": "center","fontFamily": "'IBM Plex Sans', sans-serif", "fontWeight": "bold", "color": "white", "marginBottom": "20px"}),
                            mui.Typography(project_details['Observações'].values[0], style={"marginTop": "16px", "color": "gray", "fontFamily": "'IBM Plex Sans', sans-serif", "fontSize": "14px"}),
                        ])
            with col3:
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Encerramento de Parceria</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: yellow;'>{project_details['Encerramento da parceria'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Ponto Focal na Instituição Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color: yellow;'>{project_details['Ponto Focal na Instituição Parceira'].values[0]}</h6>", unsafe_allow_html=True)
                st.write("\n")
                st.write("\n")
                st.write("\n")
                with st.expander("Mais Informações sobre o fomento"):
                    st.text(project_details['Mais informações do fomento'].values[0])
      
                # Para centralizar os nomes e adicionar espaço
                nomes = project_details['Comissão Gestora da Parceria'].values[0].split(',')
                st.write("\n")
                st.write("\n")
                st.write("\n")
                with elements("card_container1"):
                                    # Incorporar uma fonte do Google
                    mui.CssBaseline(options={
                        "typography": {
                            "fontFamily": "'Roboto', sans-serif"  # Substitua 'Roboto' pela fonte que você deseja usar
                        }
                    })
                    # Cria um cartão com cantos arredondados e sombra
                    with mui.Card(key="nomes_card", style={"borderRadius": "10px", "backgroundColor": "#0e1117", "border": "1px solid #0e1117", "boxShadow": "none"}):
                        # Conteúdo do cartão
                        with mui.CardContent():
                            # Cabeçalho do cartão
                            mui.Typography("Comissão Gestora da Parceria", style={"textAlign": "center", "fontSize": "17px", "fontFamily": "'IBM Plex Sans', sans-serif" , "fontWeight": "bold", "color": "white", "marginBottom": "20px"})

                            # Lista de nomes
                            for nome in nomes:
                                # Cada nome é um item de lista com estilos aplicados
                                mui.Typography(nome, component="li", style={
                                    "background": "none",
                                    "borderRadius": "10px",
                                    "border": "0px",
                                    "padding": "5px 20px",
                                    "margin": "0px 0",
                                    "color": "white",
                                    "textAlign": "center",
                                    "display": "block",
                                    "fontSize": "12px",
                                    "fontFamily": "'IBM Plex Sans', sans-serif",
                                    "fontWeight": "bold",
                                })

                st.markdown("</ul>", unsafe_allow_html=True)
            
            
            col1, col2, col3 = st.columns([4, 4, 4])
    
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")

    with tab2: #Chat
        st.markdown("<h6 style='text-align: center;'>{}</h6>".format(selected_project), unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 4, 1])
        with col3:
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
                    # Cria campos de entrada para todos os dados, exceto 'classificacao'
                    new_project_data = {column: st.text_input(f"{column} (novo projeto)") for column in df.columns if column != 'classificacao'}

                    # Cria um selectbox para a classificação com as opções limitadas que você definiu
                    classificacao_options = ['Em Andamento', 'Eventos', 'Emendas Parlamentares', 'Novos Projetos']
                    new_project_data['classificacao'] = st.selectbox('Classificação (novo projeto)', classificacao_options)

                    # Botões para adicionar ou cancelar o novo projeto
                    submit_new_project = st.form_submit_button('Adicionar Projeto')
                    close_new_project_form = st.form_submit_button('Cancelar')

                    if submit_new_project:
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





# Display project details based on selection in the sidebar
# ... (You'll need to implement the logic to display the details)
# You can create placeholder widgets and update them later with the project details
# when a user clicks on a project name in the sidebar

# Run the Streamlit app using the command in the terminal:
# streamlit run your_app.py