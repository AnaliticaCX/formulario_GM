import streamlit as st
import pandas as pd
import random
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from zoneinfo import ZoneInfo

# Estilo CSS personalizado con fuente Roboto
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

        .reportview-container {
            background: #f5f5f5;
            font-family: 'Roboto', sans-serif;
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
            background-color: #0056b3;
            color: white;
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
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
        }
        .pregunta {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 20px;
            text-align: center;
        }

        @media (max-width: 600px) {
            .stButton>button {
                width: 100%;
                margin: 10px 0;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# Configuración de Google Sheets
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(st.secrets["GOOGLE_CREDS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    sheet = client.open("formulario_GM_auteco").sheet1
    return sheet


# Validar si el chasis ya fue registrado
def chasis_ya_registrado(sheet, chasis):
    registros = sheet.col_values(2)
    return chasis in registros


# Guardar los datos
def guardar_datos(sheet, asesor, chasis, respuestas, aleatorio_oportunidades, aleatorio_marcas):
    fecha_hora = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S")
    fila = [asesor, chasis]

    if len(respuestas) > 0:
        fila.extend(respuestas[0])
    else:
        fila.extend(["", ""])

    fila.append(aleatorio_oportunidades if aleatorio_oportunidades else "")

    for i in range(1, 4):
        if i < len(respuestas):
            fila.extend(respuestas[i])
        else:
            fila.extend(["", ""])

    fila.append(aleatorio_marcas if aleatorio_marcas else "")
    fila.append(fecha_hora)

    sheet.append_row(fila)


# Opciones
opciones_con_marca = ["Prima 10% respaldo Auteco", "Prima 5% respaldo Auteco", "Prima 3% respaldo Auteco"]
opciones_sin_marca = ["Prima 5% respaldo Aliado", "Prima 3% respaldo Aliado"]

reglas_con_marca = {
    "Prima 10% respaldo Auteco": ["Prima 5% respaldo Auteco"],
    "Prima 5% respaldo Auteco": ["Prima 3% respaldo Auteco"],
    "Prima 3% respaldo Auteco": []
}

reglas_sin_marca = {
    "Prima 5% respaldo Aliado": ["Prima 3% respaldo Aliado"],
    "Prima 3% respaldo Aliado": []
}

equivalencias = {
    "Prima 10% respaldo Auteco": "Prima 5% respaldo Aliado",
    "Prima 5% respaldo Auteco": "Prima 3% respaldo Aliado"
}


# Manejo del formulario
def manejar_formulario():
    st.title("Formulario Rueda Seguro")

    if "asesor" not in st.session_state:
        st.session_state.asesor = ""



    if "formulario_completado" not in st.session_state:
        st.session_state.formulario_completado = False

    if st.session_state.formulario_completado:
        st.success("✅ Gracias por completar el formulario.")
        if st.button("🔄 Volver al inicio"):
            for key in ["formulario_completado", "opcion_actual", "respuestas", "aleatorio_oportunidades", "aleatorio_marcas", "chasis", "asesor", "cedula_temp"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        return

    st.text_input("🔹 Digita tu cédula como asesor:", key="asesor")

    if not st.session_state.asesor.strip():
        st.warning("Por favor, ingresa tu cédula para continuar.")
        return
    if "opcion_actual" not in st.session_state:
        st.session_state.opcion_actual = None
    if "respuestas" not in st.session_state:
        st.session_state.respuestas = []
    if "aleatorio_oportunidades" not in st.session_state:
        st.session_state.aleatorio_oportunidades = None
    if "aleatorio_marcas" not in st.session_state:
        st.session_state.aleatorio_marcas = None
    if "chasis" not in st.session_state:
        st.session_state.chasis = ""

    if st.session_state.formulario_completado:
        st.success("✅ Gracias por completar el formulario.")
        if st.button("🔄 Volver al inicio"):
            for key in ["formulario_completado", "opcion_actual", "respuestas", "aleatorio_oportunidades", "aleatorio_marcas", "chasis", "asesor", "cedula_temp"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        return

    if "chasis" not in st.session_state:
        st.session_state.chasis = ""
    st.text_input("🔹 Ingresa el número de chasis:", key="chasis")
    chasis = st.session_state.chasis

    if chasis:
        sheet = setup_google_sheets()
        if chasis_ya_registrado(sheet, chasis):
            st.error("❌ Este chasis ya ha sido registrado. No puedes continuar con el formulario.")
            return

        if st.session_state.opcion_actual is None:
            st.session_state.opcion_actual = random.choice(opciones_con_marca)

        porcentaje = st.session_state.opcion_actual.split()[1]
        tipo_marca = st.session_state.opcion_actual.split()[-1]

        if tipo_marca == "Auteco":
            pregunta = f"¿Deseas tomar rueda seguro respaldado por Auteco por valor del {porcentaje} sobre el valor de la moto?"
        else:
            pregunta = f"¿Deseas tomar rueda seguro respaldado por “Moto Experience” por valor del {porcentaje} sobre el valor de la moto?"

        st.subheader(f"{st.session_state.opcion_actual}")
        st.write(pregunta)

        col1, col2 = st.columns(2)
        if col1.button("Sí"):
            st.session_state.respuestas.append((st.session_state.opcion_actual, "Sí"))
            guardar_datos(sheet, st.session_state.asesor, chasis, st.session_state.respuestas,
                          st.session_state.aleatorio_oportunidades, st.session_state.aleatorio_marcas)
            st.session_state.formulario_completado = True
            st.rerun()

        if col2.button("No"):
            st.session_state.respuestas.append((st.session_state.opcion_actual, "No"))

            if st.session_state.aleatorio_oportunidades is None:
                st.session_state.aleatorio_oportunidades = random.choices(["Sí", "No"], weights=[0.8, 0.2])[0]

            if st.session_state.aleatorio_oportunidades == "No":
                guardar_datos(sheet, st.session_state.asesor, chasis, st.session_state.respuestas,
                              st.session_state.aleatorio_oportunidades, st.session_state.aleatorio_marcas)
                st.session_state.formulario_completado = True
                st.rerun()

            if st.session_state.aleatorio_marcas is None:
                st.session_state.aleatorio_marcas = random.choices(["con marca", "sin marca"], weights=[0.5, 0.5])[0]

            siguiente_opcion = None
            if st.session_state.aleatorio_marcas == "con marca":
                opciones_sig = reglas_con_marca.get(st.session_state.opcion_actual, [])
                for o in opciones_sig:
                    if o not in [r[0] for r in st.session_state.respuestas]:
                        siguiente_opcion = o
                        break
            else:
                base = equivalencias.get(st.session_state.opcion_actual)
                if base and base not in [r[0] for r in st.session_state.respuestas]:
                    siguiente_opcion = base
                else:
                    opciones_sig = reglas_sin_marca.get(base, []) if base else []
                    for o in opciones_sig:
                        if o not in [r[0] for r in st.session_state.respuestas]:
                            siguiente_opcion = o
                            break

            if siguiente_opcion:
                st.session_state.opcion_actual = siguiente_opcion
                st.rerun()
            else:
                guardar_datos(sheet, st.session_state.asesor, chasis, st.session_state.respuestas,
                              st.session_state.aleatorio_oportunidades, st.session_state.aleatorio_marcas)
                st.session_state.formulario_completado = True
                st.rerun()


if __name__ == "__main__":
    manejar_formulario()
