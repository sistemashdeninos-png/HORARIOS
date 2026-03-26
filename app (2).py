import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración básica de la página
st.set_page_config(page_title="Reservas Hospital", layout="wide")

st.title("🏥 Gestión de Espacios: Telemedicina y Biblioteca")

# 1. Establecer la conexión y leer los datos
conn = st.connection("gsheets", type=GSheetsConnection)

# Leemos la hoja (ttl=0 asegura que siempre traiga los datos más recientes)
try:
    df = conn.read(ttl=0)
    # Si la hoja está completamente vacía, creamos las columnas base
    if df.empty or len(df.columns) == 0:
        df = pd.DataFrame(columns=["Fecha", "Espacio", "Hora Inicio", "Hora Fin", "Actividad", "Responsable"])
except Exception as e:
    st.error(f"Error al leer la hoja: {e}")
    st.stop()

# 2. Selector de Espacio
espacio_elegido = st.selectbox("Seleccione el espacio a consultar/reservar:", ["Telemedicina", "Biblioteca"])

st.divider()

# 3. Mostrar la disponibilidad actual
st.subheader(f"📅 Horarios reservados para: {espacio_elegido}")

# Filtramos los datos para mostrar solo los del espacio elegido
df_filtrado = df[df["Espacio"] == espacio_elegido]

# Mostramos la tabla (si está vacía, mostramos un mensaje amigable)
if df_filtrado.empty:
    st.info("No hay reservas registradas para este espacio todavía.")
else:
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

st.divider()

# 4. Formulario para nueva reserva
st.subheader("✍️ Cargar nueva reserva")

with st.form("formulario_reserva", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nueva_fecha = st.date_input("Fecha de uso")
        nueva_hora_inicio = st.time_input("Hora de inicio")
        nueva_hora_fin = st.time_input("Hora de fin")
        
    with col2:
        nueva_actividad = st.text_input("Nombre del Servicio o Actividad")
        nuevo_responsable = st.text_input("Nombre de quien reserva")
        
    # Botón para enviar el formulario
    submit_button = st.form_submit_button("Confirmar Reserva")
    
    if submit_button:
        # Validamos que no dejen campos vacíos importantes
        if not nueva_actividad or not nuevo_responsable:
            st.warning("Por favor, completá la actividad y el responsable.")
        else:
            # Creamos un nuevo registro con los datos ingresados
            nuevo_registro = pd.DataFrame([{
                "Fecha": str(nueva_fecha),
                "Espacio": espacio_elegido,
                "Hora Inicio": str(nueva_hora_inicio),
                "Hora Fin": str(nueva_hora_fin),
                "Actividad": nueva_actividad,
                "Responsable": nuevo_responsable
            }])
            
            # Unimos el registro nuevo con los datos anteriores
            df_actualizado = pd.concat([df, nuevo_registro], ignore_index=True)
            
            # Guardamos en Google Sheets
            conn.update(data=df_actualizado)
            
            st.success("¡Reserva guardada con éxito!")
            # Recargamos la página para que se actualice la tabla
            st.rerun()