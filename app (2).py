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

# --- LÓGICA DEL CALENDARIO SEMANAL ---
hoy_real = datetime.date.today()
dia_referencia = hoy_real + datetime.timedelta(weeks=st.session_state.semana_offset)
inicio_semana = dia_referencia - datetime.timedelta(days=dia_referencia.weekday())

fechas_semana = [inicio_semana + datetime.timedelta(days=i) for i in range(7)]
fechas_str = [d.strftime("%Y-%m-%d") for d in fechas_semana]
nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

columnas_grilla = [f"{nombres_dias[i]} {fechas_semana[i].strftime('%d-%m')}" for i in range(7)]

horarios = []
for h in range(8, 21):
    horarios.append(f"{h:02d}:00")
    horarios.append(f"{h:02d}:30")

paleta_colores = ["#005f99", "#2e8b57", "#800080", "#b8860b", "#cd5c5c", "#4682b4", "#556b2f", "#d2691e"]
colores_asignados = {}

grilla_texto = pd.DataFrame(index=horarios, columns=columnas_grilla, data="")
grilla_color = pd.DataFrame(index=horarios, columns=columnas_grilla, data="")

if not df_filtrado.empty:
    df_filtrado["Fecha"] = df_filtrado["Fecha"].astype(str)
    df_filtrado["Hora Inicio"] = df_filtrado["Hora Inicio"].astype(str)
    df_filtrado["Hora Fin"] = df_filtrado["Hora Fin"].astype(str)
    
    for _, fila in df_filtrado.iterrows():
        fecha_reserva = fila["Fecha"]
        
        if fecha_reserva in fechas_str:
            indice_dia = fechas_str.index(fecha_reserva)
            columna_destino = columnas_grilla[indice_dia]
            
            actividad = str(fila['Actividad'])
            if actividad not in colores_asignados:
                colores_asignados[actividad] = paleta_colores[len(colores_asignados) % len(paleta_colores)]
            color_actual = colores_asignados[actividad]
            
            try:
                h_ini_str = str(fila["Hora Inicio"])[:5]
                h_fin_str = str(fila["Hora Fin"])[:5]
                inicio_min = int(h_ini_str.split(":")[0]) * 60 + int(h_ini_str.split(":")[1])
                fin_min = int(h_fin_str.split(":")[0]) * 60 + int(h_fin_str.split(":")[1])
            except (ValueError, IndexError):
                continue 
            
            slots_ocupados = []
            for slot in horarios:
                slot_min = int(slot.split(":")[0]) * 60 + int(slot.split(":")[1])
                if inicio_min <= slot_min < fin_min:
                    slots_ocupados.append(slot)
            
            if not slots_ocupados:
                continue
                
            medio_idx = len(slots_ocupados) // 2
            
            for i, slot in enumerate(slots_ocupados):
                grilla_color.at[slot, columna_destino] = color_actual
                if i == medio_idx:
                    if grilla_texto.at[slot, columna_destino] == "":
                        grilla_texto.at[slot, columna_destino] = actividad
                    else:
                        grilla_texto.at[slot, columna_destino] += f" | {actividad}"

# --- FUNCIÓN PARA APLICAR COLORES Y CENTRADO FORZADO ---
def aplicar_colores(df_base):
    df_estilos = pd.DataFrame(index=df_base.index, columns=df_base.columns, data="")
    for col in df_base.columns:
        for idx in df_base.index:
            color = grilla_color.at[idx, col]
            if color != "":
                df_estilos.at[idx, col] = f'background-color: {color}; color: white; font-weight: bold; text-align: center !important; vertical-align: middle !important;'
            else:
                df_estilos.at[idx, col] = 'text-align: center !important; vertical-align: middle !important;'
    return df_estilos

grilla_estilada = grilla_texto.style.apply(aplicar_colores, axis=None)

st.dataframe(grilla_estilada, use_container_width=True, height=600)

st.divider()

# --- FORMULARIO PARA NUEVA RESERVA ---
st.subheader("✍️ Cargar nueva reserva")

# Creamos listas de horarios fijos para los desplegables
opciones_inicio = [f"{h:02d}:{m:02d}" for h in range(8, 20) for m in (0, 30)] 
opciones_fin = [f"{h:02d}:{m:02d}" for h in range(8, 20) for m in (0, 30)][1:] + ["20:00"] 

with st.form("formulario_reserva", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nueva_fecha = st.date_input("Fecha de uso")
        nueva_hora_inicio = st.selectbox("Hora de inicio", opciones_inicio)
        nueva_hora_fin = st.selectbox("Hora de fin", opciones_fin)
        
    with col2:
        nueva_actividad = st.text_input("Nombre del Servicio o Actividad")
        nuevo_responsable = st.text_input("Nombre de quien reserva")
        # 👇 ¡Acá movimos el campo de repetir a la columna derecha! 👇
        semanas_repetir = st.number_input("Repetir por semanas adicionales", min_value=0, max_value=52, value=0, step=1, help="0 = Solo ese día. 2 = Ese día y las próximas 2 semanas.")
        
    submit_button = st.form_submit_button("Confirmar Reserva")
    
    # ... (A partir de acá sigue tu lógica del submit_button igual que antes) ...
