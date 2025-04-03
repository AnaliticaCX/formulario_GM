import streamlit as st
import pandas as pd
import random
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ofrece opciones desde la equivalente hacia abajo, por ejm opc1=10%, opc2=5%, opc3=3% ya sea con o sin marca

#st.set_page_config(
#    theme="light"
#)

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


# Separar opciones "con marca" y "sin marca"
opciones_con_marca2 = [
    "prima 3% con marca",
    "prima 5% con marca",
    "prima 10% con marca"
]

opciones_con_marca = [
    "prima 10% con marca"
]

# Reglas de opciones siguientes
reglas_siguiente_opcion_con_marca = {
    "prima 3% con marca": [],
    "prima 5% con marca": ["prima 3% con marca"],
    "prima 10% con marca": ["prima 5% con marca", "prima 3% con marca"]
}

reglas_siguiente_opcion_sin_marca = {
    "prima 3% sin marca": [],
    "prima 5% sin marca": ["prima 3% sin marca"],
    "prima 10% sin marca": ["prima 5% sin marca", "prima 3% sin marca"]
}

# Diccionario de equivalencias entre "con marca" y "sin marca"
equivalencias_opciones = {
    "prima 3% con marca": "prima 3% sin marca",
    "prima 5% con marca": "prima 5% sin marca",
    "prima 10% con marca": "prima 10% sin marca",
    "prima 3% sin marca": "prima 3% con marca",
    "prima 5% sin marca": "prima 5% con marca",
    "prima 10% sin marca": "prima 10% con marca"
}


# Guardar datos en Excel
def guardar_datos(chasis, opcion1, respuesta1, aleatorio2, opcion2=None, respuesta2=None, opcion3=None, respuesta3=None, aleatorio_marcas=None):
    data = {
        "Chasis": [chasis],
        "Opcion1": [opcion1],
        "Respuesta1": [respuesta1],
        "Aleatorio2": [aleatorio2],
        "AleatorioMarcas": [aleatorio_marcas if aleatorio_marcas else ""],  # Nueva columna
        "Opcion2": [opcion2 if opcion2 else ""],
        "Respuesta2": [respuesta2 if respuesta2 else ""],
        "Opcion3": [opcion3 if opcion3 else ""],
        "Respuesta3": [respuesta3 if respuesta3 else ""]
    }
    df = pd.DataFrame(data)
    try:
        existing_data = pd.read_excel("respuestas2.xlsx")
        df = pd.concat([existing_data, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_excel("respuestas2.xlsx", index=False)


# Modificar el flujo del formulario
def manejar_formulario():
    st.title("Formulario de Rueda Seguro")

    # Estado del formulario
    if "formulario_completado" not in st.session_state:
        st.session_state.formulario_completado = False
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

    # Si se completó el formulario
    if st.session_state.formulario_completado:
        st.success("✅ Gracias por completar el formulario.")
        if st.button("🔄 Volver al inicio"):
            st.session_state.formulario_completado = False
            st.session_state.opcion_actual = None
            st.session_state.respuestas = []
            st.session_state.aleatorio_oportunidades = None
            st.session_state.aleatorio_marcas = None
            st.session_state.chasis = ""
            st.rerun()
        return

    # Input de chasis
    chasis = st.text_input("🔹 Ingresa el número de chasis:", value=st.session_state.chasis)

    # Validar sitiene chasis antes de continuar y asigna un valor aleatorio de opciones con marca a la opción actual
    if chasis and not st.session_state.formulario_completado:
        if st.session_state.opcion_actual is None:
            st.session_state.opcion_actual = random.choice(opciones_con_marca)

        # Mostrar opción actual
        st.subheader(f"Opción {len(st.session_state.respuestas) + 1}: {st.session_state.opcion_actual}")
        st.write("¿Vas a tomar la garantía extendida por este valor?")

        # Botones de respuesta
        col1, col2 = st.columns(2)
        if col1.button("Sí"):
            # Guardar "Sí" y finalizar formulario
            guardar_datos(
                chasis,
                st.session_state.opcion_actual,
                "Sí",
                st.session_state.aleatorio_oportunidades if st.session_state.aleatorio_oportunidades else "No",
                st.session_state.respuestas[1][0] if len(st.session_state.respuestas) > 1 else None,
                st.session_state.respuestas[1][1] if len(st.session_state.respuestas) > 1 else None,
                st.session_state.respuestas[2][0] if len(st.session_state.respuestas) > 2 else None,
                st.session_state.respuestas[2][1] if len(st.session_state.respuestas) > 2 else None,
                st.session_state.aleatorio_marcas
            )
            st.session_state.formulario_completado = True
            st.rerun()

        if col2.button("No"):
            # Guardar "No" en respuestas
            st.session_state.respuestas.append((st.session_state.opcion_actual, "No"))

            # Determinar aleatorio_oportunidades solo si es la primera vez que se responde "No"
            if st.session_state.aleatorio_oportunidades is None:
                st.session_state.aleatorio_oportunidades = random.choice(["Sí", "No"])
            print(f"oportunidades {st.session_state.aleatorio_oportunidades}")

            if st.session_state.aleatorio_oportunidades == "No":
                # Finalizar formulario si aleatorio_oportunidades es "No"
                guardar_datos(
                    chasis,
                    st.session_state.respuestas[0][0], st.session_state.respuestas[0][1], st.session_state.aleatorio_oportunidades,
                    aleatorio_marcas=st.session_state.aleatorio_marcas
                )
                st.session_state.formulario_completado = True
                st.rerun()

            # Determinar aleatorio_marcas solo si no ha sido calculado antes
            if st.session_state.aleatorio_marcas is None:
                st.session_state.aleatorio_marcas = random.choice(["con marca", "sin marca"])
            print(f"marca {st.session_state.aleatorio_marcas}")

            # Obtener la siguiente opción según aleatorio_marcas
            if st.session_state.aleatorio_marcas == "con marca":
                # Verificar si la opción actual está en las reglas "con marca"
                if st.session_state.opcion_actual in reglas_siguiente_opcion_con_marca:
                    opciones_siguientes = reglas_siguiente_opcion_con_marca[st.session_state.opcion_actual]
                    print(f"con marca {opciones_siguientes}")
                else:
                    opciones_siguientes = []
                    print("con marca no hay opciones siguientes")
            else:
                if st.session_state.opcion_actual in reglas_siguiente_opcion_sin_marca:
                    # Si ya está en "sin marca", usar directamente las reglas de "sin marca"
                    opciones_siguientes = reglas_siguiente_opcion_sin_marca[st.session_state.opcion_actual]
                    print(f"sin marca (ya en sin marca) {opciones_siguientes}")
                else:
                    # Si no está en "sin marca", convertirla usando el diccionario de equivalencias
                    opcion_sin_marca = equivalencias_opciones.get(st.session_state.opcion_actual, None)
                    print(f"sin marca (convertida) {opcion_sin_marca}")

                    if opcion_sin_marca and opcion_sin_marca in reglas_siguiente_opcion_sin_marca:
                        opciones_siguientes = reglas_siguiente_opcion_sin_marca[opcion_sin_marca]
                        print(f"sin marca {opciones_siguientes}")
                    else:
                        opciones_siguientes = []
                        print("sin marca no hay opciones siguientes")

            if opciones_siguientes:
                # Filtrar opciones ya utilizadas
                opciones_no_usadas = [opcion for opcion in opciones_siguientes if opcion not in [resp[0] for resp in st.session_state.respuestas]]
                if opciones_no_usadas:
                    st.session_state.opcion_actual = opciones_no_usadas[0]
                    print(f"nueva opcion {st.session_state.opcion_actual}")
                    st.rerun()
                else:
                    print("No hay opciones no usadas disponibles")
            else:
                # Finalizar formulario si no hay opciones siguientes
                guardar_datos(
                    chasis,
                    st.session_state.respuestas[0][0], st.session_state.respuestas[0][1], st.session_state.aleatorio_oportunidades,
                    st.session_state.respuestas[1][0] if len(st.session_state.respuestas) > 1 else None,
                    st.session_state.respuestas[1][1] if len(st.session_state.respuestas) > 1 else None,
                    st.session_state.respuestas[2][0] if len(st.session_state.respuestas) > 2 else None,
                    st.session_state.respuestas[2][1] if len(st.session_state.respuestas) > 2 else None,
                    aleatorio_marcas=st.session_state.aleatorio_marcas
                )
                st.session_state.formulario_completado = True
                st.rerun()


if __name__ == "__main__":
    manejar_formulario()
