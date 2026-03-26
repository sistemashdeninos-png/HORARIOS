import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuración básica de la página
st.set_page_config(page_title="Reservas Hospital", layout="wide")

# 1. EL NUEVO TÍTULO
st.title("🗓️HORARIOS DE ESPACIOS🗓️")

# Establecer la conexión y leer los datos
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(ttl=0)
    if df.empty or len(df.columns) == 0:
        df = pd.DataFrame(columns=["Fecha", "Espacio", "Hora Inicio", "Hora Fin", "Actividad", "Responsable"])
except Exception as e:
    st.error(f"Error al leer la hoja: {e}")
    st.stop()

# Selector de Espacio
espacio_elegido = st.selectbox("Seleccione el espacio a consultar/reservar:", ["Telemedicina", "Biblioteca"])

st.divider()

st.subheader(f"📅 Disponibilidad de esta semana: {espacio_elegido}")

# Filtrar por espacio
df_filtrado = df[df["Espacio"] == espacio_elegido].copy()

# --- LÓGICA DEL CALENDARIO SEMANAL ---

# Obtener la fecha de hoy y calcular el inicio de la semana (Lunes)
hoy = datetime.date.today()
inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())

# Generar las fechas de los 7 días de esta semana
fechas_semana = [inicio_semana + datetime.timedelta(days=i) for i in range(7)]
fechas_str = [d.strftime("%Y-%m-%d") for d in fechas_semana]
nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Crear los títulos de las columnas (Ej: "Lunes 23-03")
columnas_grilla = [f"{nombres_dias[i]} {fechas_semana[i].strftime('%d-%m')}" for i in range(7)]

# Crear las filas (Horarios desde las 08:00 hasta las 20:00)
horarios = [f"{h:02d}:00" for h in range(8, 21)]

# Armar la grilla vacía
grilla = pd.DataFrame(index=horarios, columns=columnas_grilla, data="")

# Llenar la grilla con las reservas existentes
if not df_filtrado.empty:
    # Asegurarnos de que las fechas y horas sean texto para poder compararlas
    df_filtrado["Fecha"] = df_filtrado["Fecha"].astype(str)
    df_filtrado["Hora Inicio"] = df_filtrado["Hora Inicio"].astype(str)
    
    for _, fila in df_filtrado.iterrows():
        fecha_reserva = fila["Fecha"]
        
        # Si la reserva es de esta semana, la ubicamos en la columna correspondiente
        if fecha_reserva in fechas_str:
            indice_dia = fechas_str.index(fecha_reserva)
            columna_destino = columnas_grilla[indice_dia]
            
            # Extraemos la hora (ej. de "09:30:00" sacamos "09:00" para encajar en la grilla)
            hora_inicio_str = fila["Hora Inicio"][:2] + ":00" 
            
            # Si el horario está dentro de nuestra grilla (8 a 20hs), lo anotamos
            if hora_inicio_str in grilla.index:
                texto_reserva = f"{fila['Actividad']}\n({fila['Responsable']})"
                # Si ya hay algo escrito, lo sumamos (por si hay doble reserva)
                if grilla.at[hora_inicio_str, columna_destino] == "":
                    grilla.at[hora_inicio_str, columna_destino] = texto_reserva
                else:
                    grilla.at[hora_inicio_str, columna_destino] += f" | {texto_reserva}"

# Mostrar la grilla como un calendario
st.dataframe(grilla, use_container_width=True)

st.divider()

# --- FORMULARIO PARA NUEVA RESERVA ---
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
        
    submit_button = st.form_submit_button("Confirmar Reserva")
    
    if submit_button:
        if not nueva_actividad or not nuevo_responsable:
            st.warning("Por favor, completá la actividad y el responsable.")
        else:
            nuevo_registro = pd.DataFrame([{
                "Fecha": str(nueva_fecha),
                "Espacio": espacio_elegido,
                "Hora Inicio": str(nueva_hora_inicio),
                "Hora Fin": str(nueva_hora_fin),
                "Actividad": nueva_actividad,
                "Responsable": nuevo_responsable
            }])
            
            df_actualizado = pd.concat([df, nuevo_registro], ignore_index=True)
            conn.update(data=df_actualizado)
            
            st.success("¡Reserva guardada con éxito!")
            st.rerun()