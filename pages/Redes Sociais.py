import streamlit as st
import requests
import pandas as pd

# Defina suas credenciais do Instagram
CLIENT_ID = "SUA_CLIENT_ID"
CLIENT_SECRET = "SUA_CLIENT_SECRET"

# Obtenha um token de acesso
access_token = requests.post(
    "https://api.instagram.com/oauth/access_token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": "SEU_CODIGO_DE_AUTORIZAÇÃO",
    },
).json()["access_token"]

# Obtenha informações do usuário
user_info = requests.get(
    "https://api.instagram.com/v1/users/self",
    params={"access_token": access_token},
).json()

# Obtenha as últimas 10 postagens do usuário
media = requests.get(
    "https://api.instagram.com/v1/users/self/media/recent",
    params={"access_token": access_token, "count": 10},
).json()

# Crie um DataFrame com as informações das postagens
df = pd.DataFrame(
    {
        "Postagem": [m["caption"]["text"] for m in media["data"]],
        "Curtidas": [m["likes"]["count"] for m in media["data"]],
        "Comentários": [m["comments"]["count"] for m in media["data"]],
        "Data": [m["created_time"] for m in media["data"]],
    }
)

# Exiba o nome do usuário e o número de seguidores
st.header(f"Olá, {user_info['username']}")
st.write(f"Você tem {user_info['counts']['followed_by']} seguidores")

# Exiba a tabela com as informações das postagens
st.table(df)

# Exiba um gráfico de curtidas e comentários
st.line_chart(
    data=df,
    x="Data",
    y=["Curtidas", "Comentários"],
)