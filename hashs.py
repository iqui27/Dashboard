import streamlit_authenticator as stauth


# Criação dos hashes de senha
hashed_passwords = stauth.Hasher(['844612', 'secti2024']).generate()

# Imprime os hashes gerados para uso no seu aplicativo
print(hashed_passwords)