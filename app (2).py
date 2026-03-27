import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuración básica de la página
st.set_page_config(page_title="Reservas Hospital", layout="wide")

st.title("🗓️HORARIOS DE ESPACIOS🗓️")

# --- NAVEGACIÓN DE SEMANAS (MEMORIA DE STREAMLIT) ---
# Inicializamos el contador de semanas en 0 (semana actual)
if 'semana_offset' not in st.session_state:
    st.session_state.semana_offset = 0

# Conexión y lectura de datos
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

# --- BOTONES PARA MOVERSE ENTRE SEMANAS ---
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

with col_nav1:
    if st.button("⬅️ Semana Anterior", use_container_width=True):
        st.session_state.semana_offset -= 1
        st.rerun()

with col_nav2:
    st.markdown(f"<h3 style='text-align: center;'>📅 Disponibilidad: {espacio_elegido}</h3>", unsafe_allow_html=True)

with col_nav3:
    if st.button("Semana Siguiente ➡️", use_container_width=True):
        st.session_state.semana_offset += 1
        st.rerun()

# Filtramos por el espacio elegido
df_filtrado = df[df["Espacio"] == espacio_elegido].copy()

# --- LÓGICA DEL CALENDARIO SEMANAL ---
hoy_real = datetime.date.today()
# Calculamos la fecha base sumando o restando semanas según los botones
dia_referencia = hoy_real + datetime.timedelta(weeks=st.session_state.semana_offset)
inicio_semana = dia_referencia - datetime.timedelta(days=dia_referencia.weekday())

fechas_semana = [inicio_semana + datetime.timedelta(days=i) for i in range(7)]
fechas_str = [d.strftime("%Y-%m-%d") for d in fechas_semana]
nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

columnas_grilla = [f"{nombres_dias[i]} {fechas_semana[i].strftime('%d-%m')}" for i in range(7)]
horarios = [f"{h:02d}:00" for h in range(8, 21)] # Rango de 08:00 a 20:00

# Armar la grilla vacía
grilla = pd.DataFrame(index=horarios, columns=columnas_grilla, data="")

if not df_filtrado.empty:
    df_filtrado["Fecha"] = df_filtrado["Fecha"].astype(str)
    df_filtrado["Hora Inicio"] = df_filtrado["Hora Inicio"].astype(str)
    df_filtrado["Hora Fin"] = df_filtrado["Hora Fin"].astype(str)
    
    for _, fila in df_filtrado.iterrows():
        fecha_reserva = fila["Fecha"]
        
        if fecha_reserva in fechas_str:
            indice_dia = fechas_str.index(fecha_reserva)
            columna_destino = columnas_grilla[indice_dia]
            
            # Extraemos la hora de inicio y fin como números (Ej: de "10:00:00" sacamos el 10)
            try:
                h_inicio = int(fila["Hora Inicio"].split(":")[0])
                h_fin = int(fila["Hora Fin"].split(":")[0])
            except ValueError:
                continue 
            
            # Pintamos TODA la franja horaria
            for h in range(h_inicio, h_fin):
                hora_str = f"{h:02d}:00"
                
                if hora_str in grilla.index:
                    # SOLO MOSTRAMOS EL SERVICIO, SIN EL RESPONSABLE
                    texto_reserva = str(fila['Actividad'])
                    
                    if grilla.at[hora_str, columna_destino] == "":
                        grilla.at[hora_str, columna_destino] = texto_reserva
                    else:
                        grilla.at[hora_str, columna_destino] += f" | {texto_reserva}"

# --- FUNCIÓN PARA DAR COLOR ---
def pintar_celdas(val):
    if val != "":
        # Si la celda tiene texto, la pintamos de azul hospitalario con texto blanco
        return 'background-color: #005f99; color: white; font-weight: bold; text-align: center;'
    return ''

# Aplicamos el estilo de color a la tabla (usamos try/except por compatibilidad de versiones de Pandas)
try:
    grilla_estilada = grilla.style.map(pintar_celdas)
except AttributeError:
    grilla_estilada = grilla.style.applymap(pintar_celdas)

st.dataframe(grilla_estilada, use_container_width=True)

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
        # Validamos que la hora de fin sea mayor a la de inicio
        elif nueva_hora_inicio >= nueva_hora_fin:
            st.error("La hora de fin debe ser posterior a la hora de inicio.")
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