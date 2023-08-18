import streamlit as st
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Authenticate 
import home

st.set_page_config(page_title="Email Reader App", page_icon="📧")
st.subheader("Welcome to Email Reader")

# Load configuration from YAML file
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize the authenticator
authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

col1, col2 = st.columns(2)
name, authentication_status, username = authenticator.login('Login', 'main')
if authentication_status:
    with col1:
        authenticator.logout('Logout', 'main')
    with col2:
        st.write(f'Welcome *{name}*')
    home.main()

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
