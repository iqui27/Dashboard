import time
import streamlit as st
import pandas as pd
import locale
from streamlit_authenticator import Authenticate
import yaml
from yaml.loader import SafeLoader

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
    locale.setlocale(locale.LC_ALL, 'pt_BR')

    # Initialize the Streamlit interface
    st.sidebar.title("Projetos")

    # Cria uma barra de navegação com abas
    tab1, tab2, tab3 = st.tabs(["Home", "Projetos", "Sair"])

    with tab2:
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
                    selected_project = "Nenhum projeto selecionado"

            # Ordenar o DataFrame pela coluna "classificacao"
            df_sorted = df.sort_values('classificacao')

            # Group projects by classification
            grouped_projects = df_sorted.groupby('classificacao')

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
                st.write("\n")
                st.write("\n")
                st.markdown("<h5 style='text-align: center;'>Fonte de Custeio</h5>", unsafe_allow_html=True)
                st.markdown("<h5 style='text-align: center;'>{}</h5>".format(project_details['Fonte de Custeio'].values[0]), unsafe_allow_html=True)

                
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
            with col3:
                if 'show_observations' not in st.session_state:
                    st.session_state.show_observations = False
                # Botão que alterna a visibilidade das observações
                if st.button('Observações'):
                    st.session_state.show_observations = not st.session_state.show_observations

                # Se a variável de estado 'show_observations' for True, mostre as observações
                if st.session_state.show_observations:
                    st.text(project_details['Observações'].values[0])

                st.markdown("<h5 style='text-align: left;'>Encerramento de Parceria</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: left; color: yellow;'>{project_details['Encerramento da parceria'].values[0]}</h6>", unsafe_allow_html=True)
                st.markdown("<h5 style='text-align: left;'>Ponto Focal na Instituição Parceira</h5>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: left; color: yellow;'>{project_details['Ponto Focal na Instituição Parceira'].values[0]}</h6>", unsafe_allow_html=True)
                if st.button('Mais Informações sobre o fomento'):
                    if 'show_info' not in st.session_state:
                        st.session_state.show_info = False

                    if st.session_state.show_info:
                        st.session_state.show_info = False
                    else:
                        st.session_state.show_info = True
                        st.text(project_details['Mais informações do fomento'].values[0])


            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.markdown("<h5 style='text-align: center;'>Situação Atual</h5>", unsafe_allow_html=True)
            st.markdown(f"<h6 style='text-align: center; color: Green;'>{project_details['Situação atual'].values[0]}</h6>", unsafe_allow_html=True)
            st.write("\n")
            st.markdown("<h5 style='text-align: center;'>Comissão Gestora da Parceria</h5>", unsafe_allow_html=True)
            st.markdown(f"<h6 style='text-align: center; color: Green;'>{project_details['Comissão Gestora da Parceria'].values[0]}</h6>", unsafe_allow_html=True)
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")
            st.write("\n")


            col4, col5, col6 = st.columns([3, 6, 3])

            with col5:
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
                    new_project_data = {column: st.text_input(f"{column} (novo projeto)") for column in df.columns}
                    submit_new_project = st.form_submit_button('Adicionar Projeto')
                    close_new_project_form = st.form_submit_button('Cancelar')

                    if submit_new_project:
                        new_row = pd.DataFrame([new_project_data])
                        df = pd.concat([df, new_row], ignore_index=True)
                        st.session_state.show_new_project_form = False
                        df.to_csv(csv_file_path, index=False)
                        st.success("Novo projeto adicionado com sucesso!")
                        time.sleep(2)  # Sleep for 1 second to show the success message
                        st.experimental_rerun()

                    if close_new_project_form:
                        st.session_state.show_new_project_form = False



            # Verificar se um projeto foi selecionado
            if selected_project:
                project_details = df[df['Projeto'] == selected_project].iloc[0]

            # Botão para mostrar o formulário
                    
                if st.session_state.show_form:
                    with st.form(key='edit_form'):
                        new_values = {column: st.text_input(column, project_details[column]) for column in df.columns}
                        
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
    with tab3:
        authenticator.logout()


# Display project details based on selection in the sidebar
# ... (You'll need to implement the logic to display the details)
# You can create placeholder widgets and update them later with the project details
# when a user clicks on a project name in the sidebar

# Run the Streamlit app using the command in the terminal:
# streamlit run your_app.py