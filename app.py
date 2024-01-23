import streamlit as st
import pandas as pd

st.write("DASHBOARD")

df = pd.read_csv("Dashboard.csv")

# Initialize the Streamlit interface
st.sidebar.title("Projetos")

# Setup a search box
search_query = st.sidebar.text_input("Busca", "")

# Filter data based on the search query
filtered_data = df[df['Projeto'].str.contains(search_query, case=False)]

# Display the filtered project names in the sidebar
selected_project = st.sidebar.radio("Selecione um projeto", filtered_data['Projeto'])

# Display project details based on selection in the sidebar
st.title("Project Details")
if selected_project:
    project_details = df[df['Projeto'] == selected_project]
    st.write(project_details)

# Main Area
st.title("Project Details")
# Display project details based on selection in the sidebar
# ... (You'll need to implement the logic to display the details)

# You can create placeholder widgets and update them later with the project details
# when a user clicks on a project name in the sidebar

# Run the Streamlit app using the command in the terminal:
# streamlit run your_app.py