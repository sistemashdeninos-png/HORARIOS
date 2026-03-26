import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Reservas")

st.title("Gestión de Espacios - Hospital")

# 1. Selección de espacio
espacio = st.sidebar.selectbox("Seleccione el espacio", ["Telemedicina", "Biblioteca"])

# 2. Mostrar calendario (simplificado como tabla de hoy)
st.subheader(f"Horarios ocupados en {espacio}")
reservas_hoy = df[df['Espacio'] == espacio]
st.table(reservas_hoy)

# 3. Formulario de reserva
with st.form("form_reserva"):
    fecha = st.date_input("Fecha")
    h_inicio = st.time_input("Hora de Inicio")
    h_fin = st.time_input("Hora de Fin")
    actividad = st.text_input("Actividad o Servicio")
    nombre = st.text_input("Nombre de quien reserva")
    
    enviar = st.form_submit_button("Confirmar Reserva")

    if enviar:
        # Aquí añadirías la lógica para verificar solapamientos
        # Si está disponible, se añade una fila al DF y se actualiza la hoja
        st.success(f"Reserva confirmada para {actividad} en {espacio}")