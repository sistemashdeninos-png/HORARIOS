import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Crear la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. LEER DATOS (Para mostrar el calendario)
df = conn.read(ttl="0") # ttl="0" para que no guarde cache y veas las reservas al instante

# 2. ESCRIBIR DATOS (Para cuando alguien reserva)
# Supongamos que tenés un nuevo renglón en un DataFrame llamado 'nuevo_df'
# conn.update(data=nuevo_df)