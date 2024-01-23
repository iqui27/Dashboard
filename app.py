import streamlit as st
import pandas as pd
import locale
from streamlit_elements import elements, mui, html

df = pd.read_csv("Dashboard.csv")


# Configurar o locale para usar o formato de moeda brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Initialize the Streamlit interface
st.sidebar.title("Projetos")

# Setup a search box
search_query = st.sidebar.text_input("Busca", "")

# Filter data based on the search query
filtered_data = df[df['Projeto'].str.contains(search_query, case=False)]
selected_project_id = st.sidebar.selectbox('Numero SEI', df['Processo SEI'].unique())
# Display the filtered project names in the sidebar
selected_project = st.sidebar.radio("Selecione um Projeto", filtered_data['Projeto'])

# Display project details based on selection in the sidebar
if selected_project:
    project_details = df[df['Projeto'] == selected_project]

# Formatar o valor para o formato de moeda brasileiro
valor_formatado = locale.currency(project_details['Valor'].values[0], grouping=True)

col1, col2 = st.columns([1, 2])

# Main Area
    
with col2:
    st.title(selected_project)
    st.write(project_details['Fomento'].values[0])
    st.metric("Valor", valor_formatado)
    if st.button('Mais Informações sobre o fomento'):
        st.text(project_details['Mais informações do fomento'].values[0])
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
st.write("\n")
st.write(df)

with st.form(key='my_form'):
    st.write("Editar Projeto")

    new_data = []

    for column in df.columns:
        new_col_data = []
        for i in range(len(df[column])):
            new_val = st.text_input(f"{column} {i+1}", df[column][i])
            new_col_data.append(new_val)
        new_data.append(new_col_data)
    
    submit_button = st.form_submit_button(label='Submit')

# Display project details based on selection in the sidebar
# ... (You'll need to implement the logic to display the details)
# You can create placeholder widgets and update them later with the project details
# when a user clicks on a project name in the sidebar

# Run the Streamlit app using the command in the terminal:
# streamlit run your_app.py