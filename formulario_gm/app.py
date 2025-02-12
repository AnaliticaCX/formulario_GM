import streamlit as st
import pandas as pd
import random
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    theme="light"
)

# Estilo CSS personalizado con fuente Roboto
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

        .reportview-container {
            background: #f5f5f5;
            font-family: 'Roboto', sans-serif; /* Cambio de fuente */
        }
        .stButton>button {
            padding: 10px 22px;
            text-align: center;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #0056b3; /* Azul oscuro */
            color: white; /* Cambia el color de la letra al pasar el cursor */
        }
        .stTextInput>div>div>input {
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 10px;
            width: 100%;
        }
        .stMarkdown h1 {
            font-size: 36px;
            text-align: center;
            color: #202124;
        }
        .stMarkdown p {
            font-size: 18px;
            color: #202124;
        }
        .stRadio button {
            display: inline-block;
            margin-right: 10px;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background-color: #e9ecef;
            color: #202124;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .stRadio button:hover {
            background-color: #d1d7dc;
        }
        .stRadio button:checked {
            background-color: #007bff;
            color: white;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.5); /* Agrega una sombra */
        }
        .pregunta {
            font-size: 24px; /* Tamaño de letra más grande */
            font-weight: bold; /* Negrita */
            color: #007bff; /* Color azul */
            margin-bottom: 20px;
            text-align: center; /* Centra el texto */
        }

        /* Media Query para pantallas pequeñas */
        @media (max-width: 600px) {
            .stButton>button {
                width: 100%; /* Hace que los botones ocupen todo el ancho en pantallas pequeñas */
                margin: 10px 0;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# Definir opciones
opciones_prima = [
    "1. prima 3% con marca",
    "2. prima 3% sin marca",
    "3. prima 5% con marca",
    "4. prima 5% sin marca",
    "5. prima 10% con marca",
    "6. prima 10% sin marca"
]

# Reglas de opciones siguientes
reglas_siguiente_opcion = {
    "1. prima 3% con marca": [],
    "2. prima 3% sin marca": [],
    "3. prima 5% con marca": ["1. prima 3% con marca"],
    "4. prima 5% sin marca": ["2. prima 3% sin marca"],
    "5. prima 10% con marca": ["3. prima 5% con marca", "1. prima 3% con marca"],
    "6. prima 10% sin marca": ["4. prima 5% sin marca", "2. prima 3% sin marca"]
}


# Configuración de Google Sheets
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(st.secrets["GOOGLE_CREDS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    #creds = ServiceAccountCredentials.from_json_keyfile_name("formularios-analitica-4be838661560.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("formulario_GM_auteco").sheet1  # Cambia "Nombre de tu hoja de cálculo" por el nombre de tu hoja
    return sheet


# Guardar datos en Google Sheets
def guardar_datos_google_sheets(sheet, chasis, opcion1, respuesta1, aleatorio2, opcion2=None, respuesta2=None, opcion3=None, respuesta3=None):
    data = [chasis, opcion1, respuesta1, aleatorio2, opcion2 if opcion2 else "", respuesta2 if respuesta2 else "", opcion3 if opcion3 else "", respuesta3 if respuesta3 else ""]
    sheet.append_row(data)


# Manejo del formulario
def manejar_formulario():
    st.title("Formulario de Garantía Extendida")

    # Estado del formulario
    if "formulario_completado" not in st.session_state:
        st.session_state.formulario_completado = False
    if "opcion_actual" not in st.session_state:
        st.session_state.opcion_actual = None
    if "respuestas" not in st.session_state:
        st.session_state.respuestas = []
    if "aleatorio2" not in st.session_state:
        st.session_state.aleatorio2 = None
    if "chasis" not in st.session_state:
        st.session_state.chasis = ""

    # Si se completó el formulario
    if st.session_state.formulario_completado:
        st.success("✅ Gracias por completar el formulario.")
        if st.button("🔄 Volver al inicio"):
            st.session_state.formulario_completado = False
            st.session_state.opcion_actual = None
            st.session_state.respuestas = []
            st.session_state.aleatorio2 = None
            st.session_state.chasis = ""
            st.rerun()
        return

    # Input de chasis
    chasis = st.text_input("🔹 Ingresa el número de chasis:", value=st.session_state.chasis)

    # Validar chasis antes de continuar
    if chasis and not st.session_state.formulario_completado:
        if st.session_state.opcion_actual is None:
            st.session_state.opcion_actual = random.choice(opciones_prima)

        # Mostrar opción actual
        st.subheader(f"Opción {len(st.session_state.respuestas) + 1}: {st.session_state.opcion_actual}")
        st.write("¿Vas a tomar la garantía extendida por este valor?")

        # Botones de respuesta
        col1, col2 = st.columns(2)
        if col1.button("Sí"):
            # Guardar "Sí" y finalizar formulario
            sheet = setup_google_sheets()
            if len(st.session_state.respuestas) == 0:
                guardar_datos_google_sheets(sheet, chasis, st.session_state.opcion_actual, "Sí", st.session_state.aleatorio2 if st.session_state.aleatorio2 else "No")
            elif len(st.session_state.respuestas) == 1:
                guardar_datos_google_sheets(sheet, chasis, st.session_state.respuestas[0][0], st.session_state.respuestas[0][1], st.session_state.aleatorio2, st.session_state.opcion_actual, "Sí")
            elif len(st.session_state.respuestas) == 2:
                guardar_datos_google_sheets(sheet, chasis, st.session_state.respuestas[0][0], st.session_state.respuestas[0][1], st.session_state.aleatorio2, st.session_state.respuestas[1][0], st.session_state.respuestas[1][1], st.session_state.opcion_actual, "Sí")
            st.session_state.formulario_completado = True
            st.rerun()

        if col2.button("No"):
            # Guardar "No"
            st.session_state.respuestas.append((st.session_state.opcion_actual, "No"))

            # Determinar aleatorio2 solo si es la primera vez que se responde "No"
            if st.session_state.aleatorio2 is None:
                st.session_state.aleatorio2 = random.choice(["Sí", "No"])

            # Obtener la siguiente opción
            opciones_siguientes = reglas_siguiente_opcion[st.session_state.opcion_actual]

            if opciones_siguientes and st.session_state.aleatorio2 == "Sí":
                st.session_state.opcion_actual = opciones_siguientes[0]
                st.rerun()
            else:
                sheet = setup_google_sheets()
                guardar_datos_google_sheets(
                    sheet,
                    chasis,
                    st.session_state.respuestas[0][0], st.session_state.respuestas[0][1], st.session_state.aleatorio2,
                    st.session_state.respuestas[1][0] if len(st.session_state.respuestas) > 1 else None,
                    st.session_state.respuestas[1][1] if len(st.session_state.respuestas) > 1 else None,
                    st.session_state.respuestas[2][0] if len(st.session_state.respuestas) > 2 else None,
                    st.session_state.respuestas[2][1] if len(st.session_state.respuestas) > 2 else None
                )
                st.session_state.formulario_completado = True
                st.rerun()


if __name__ == "__main__":
    manejar_formulario()