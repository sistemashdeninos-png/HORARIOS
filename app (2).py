import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuración básica de la página
st.set_page_config(page_title="Reservas Hospital", layout="wide")

st.title("🗓️HORARIOS DE ESPACIOS🗓️")

# --- NAVEGACIÓN DE SEMANAS ---
if 'semana_offset' not in st.session_state:
    st.session_state.semana_offset = 0

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(ttl=0)
    if df.empty or len(df.columns) == 0:
        df = pd.DataFrame(columns=["Fecha", "Espacio", "Hora Inicio", "Hora Fin", "Actividad", "Responsable"])
except Exception as e:
    st.error(f"Error al leer la hoja: {e}")
    st.stop()

espacio_elegido = st.selectbox("Seleccione el espacio a consultar/reservar:", ["Telemedicina", "Biblioteca"])

st.divider()

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

df_filtrado = df[df["Espacio"] == espacio_elegido].copy()

# --- LÓGICA DEL CALENDARIO SEMANAL (INTERVALOS DE 30 MIN) ---
hoy_real = datetime.date.today()
dia_referencia = hoy_real + datetime.timedelta(weeks=st.session_state.semana_offset)
inicio_semana = dia_referencia - datetime.timedelta(days=dia_referencia.weekday())

fechas_semana = [inicio_semana + datetime.timedelta(days=i) for i in range(7)]
fechas_str = [d.strftime("%Y-%m-%d") for d in fechas_semana]
nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

columnas_grilla = [f"{nombres_dias[i]} {fechas_semana[i].strftime('%d-%m')}" for i in range(7)]

# Generamos intervalos cada 30 minutos desde las 08:00 hasta las 20:30
horarios = []
for h in range(8, 21):
    horarios.append(f"{h:02d}:00")
    horarios.append(f"{h:02d}:30")

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
            
            # Convertimos las horas a "minutos desde las 00:00" para calcular franjas exactas
            try:
                # Nos quedamos con los primeros 5 caracteres (ej. "10:30" de "10:30:00")
                h_ini_str = str(fila["Hora Inicio"])[:5]
                h_fin_str = str(fila["Hora Fin"])[:5]
                
                inicio_min = int(h_ini_str.split(":")[0]) * 60 + int(h_ini_str.split(":")[1])
                fin_min = int(h_fin_str.split(":")[0]) * 60 + int(h_fin_str.split(":")[1])
            except (ValueError, IndexError):
                continue 
            
            # Evaluamos cada bloque de 30 minutos de nuestra grilla
            for slot in horarios:
                slot_min = int(slot.split(":")[0]) * 60 + int(slot.split(":")[1])
                
                # Si el bloque está dentro del horario de la reserva (incluye el inicio, no pinta el final)
                if inicio_min <= slot_min < fin_min:
                    texto_reserva = str(fila['Actividad'])
                    
                    if grilla.at[slot, columna_destino] == "":
                        grilla.at[slot, columna_destino] = texto_reserva
                    else:
                        # Si ya hay algo escrito (solapamiento), lo mostramos también
                        if texto_reserva not in grilla.at[slot, columna_destino]:
                            grilla.at[slot, columna_destino] += f" | {texto_reserva}"

# --- FUNCIÓN PARA DAR COLOR ---
def pintar_celdas(val):
    if val != "":
        return 'background-color: #005f99; color: white; font-weight: bold; text-align: center;'
    return ''

try:
    grilla_estilada = grilla.style.map(pintar_celdas)
except AttributeError:
    grilla_estilada = grilla.style.applymap(pintar_celdas)

# Aumentamos un poco la altura de la tabla para que se vean bien todos los bloques de 30 min
st.dataframe(grilla_estilada, use_container_width=True, height=600)

st.divider()

# --- FORMULARIO PARA NUEVA RESERVA ---
st.subheader("✍️ Cargar nueva reserva")

with st.form("formulario_reserva", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nueva_fecha = st.date_input("Fecha de uso")
        nueva_hora_inicio = st.time_input("Hora de inicio (ej. 10:00, 10:30)", step=1800) # step=1800 fuerza saltos de 30 min
        nueva_hora_fin = st.time_input("Hora de fin (ej. 11:00, 11:30)", step=1800)
        
    with col2:
        nueva_actividad = st.text_input("Nombre del Servicio o Actividad")
        nuevo_responsable = st.text_input("Nombre de quien reserva")
        
    submit_button = st.form_submit_button("Confirmar Reserva")
    
    if submit_button:
        if not nueva_actividad or not nuevo_responsable:
            st.warning("Por favor, completá la actividad y el responsable.")
        elif nueva_hora_inicio >= nueva_hora_fin:
            st.error("La hora de fin debe ser posterior a la hora de inicio.")
        else:
            nuevo_registro = pd.DataFrame([{
                "Fecha": str(nueva_fecha),
                "Espacio": espacio_elegido,
                "Hora Inicio": str(nueva_hora_inicio)[:5], # Guardamos solo HH:MM
                "Hora Fin": str(nueva_hora_fin)[:5],
                "Actividad": nueva_actividad,
                "Responsable": nuevo_responsable
            }])
            
            df_actualizado = pd.concat([df, nuevo_registro], ignore_index=True)
            conn.update(data=df_actualizado)
            
            st.success("¡Reserva guardada con éxito!")
            st.rerun()