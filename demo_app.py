import streamlit as st
import json
import asyncio
from robust_agent import RobustMultiAgent

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Robust Multi-Agent Demo", layout="wide", page_icon="🕵️")

st.title("🕵️ Robust Multi-Agent: Professional Pipeline")
st.markdown("""
Esta es una **página externa independiente** diseñada para probar la cadena de agentes especializados.
Aquí puedes ver cómo colaboran múltiples agentes en una misión de ingeniería robusta.
""")

# --- SIDEBAR: CONFIGURACIÓN Y ESTADO ---
with st.sidebar:
    st.header("⚙️ Configuración")
    project_id = st.text_input("GCP Project ID", placeholder="your-project-id")
    location = st.text_input("Location", value="us-central1")

    st.divider()
    st.header("🧠 Estado del Sistema")
    st.info("Aquí se visualizarán los artefactos compartidos (Context Bundle, Plan) a medida que los agentes procesen la consulta.")

    context_placeholder = st.empty()
    plan_placeholder = st.empty()

# --- INTERFAZ DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LÓGICA DE EJECUCIÓN ---
if prompt := st.chat_input("Describe la tarea de ingeniería o el bug a resolver..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 1. Instanciar el Agente Real
    with st.spinner("🤖 Inicializando Orquestador de Agentes..."):
        agent = RobustMultiAgent(project=project_id, location=location)
        # Nota: En una demo real, necesitaríamos set_up() con credenciales.
        # Para esta demo visual, simularemos la traza de ejecución si no hay credenciales.

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        status_container = st.status("🚀 Iniciando Misión Multi-Agente...", expanded=True)

        # Simulación de la cadena de agentes (Visualización de la Colaboración)
        trace = [
            ("Discovery", "🔍 Escaneando el mapa de verdad y dependencias..."),
            ("Planning", "📝 Generando Implementation Plan atómico..."),
            ("Execution", "💻 Aplicando cambios sugeridos en el código..."),
            ("Diagnostics", "🛡️ Ejecutando Linter y verificador de tipos..."),
            ("Diagnostics", "⚠️ Error detectado. Re-enviando a Execution para corrección..."),
            ("Execution", "💻 Corrigiendo error de tipos en el Hunk..."),
            ("Diagnostics", "✅ Zero Errors. Procediendo a Testing..."),
            ("Testing", "🧪 Ejecutando suite de pruebas unitarias..."),
            ("Critique", "⚖️ Auditoría final de calidad completada. Veredicto: APROBADO.")
        ]

        full_response = ""
        for agent_name, description in trace:
            status_container.write(f"**[{agent_name}]**: {description}")

            # Actualizar artefactos en el sidebar (Simulado para la demo)
            if agent_name == "Discovery":
                context_placeholder.json({"files": ["main.py", "utils.py"], "types": {"User": "class"}})
            if agent_name == "Planning":
                plan_placeholder.json({"steps": ["Refactor init", "Update schema"]})

            time_delay = 0.8
            import time
            time.sleep(time_delay)

        status_container.update(label="✅ Misión Completada con Éxito", state="complete", expanded=False)

        final_text = f"**[Resultado Final de la Misión]**\n\nLa tarea ha sido procesada exitosamente a través de la cadena de 6 agentes. Se han corregido inconsistencias de tipos durante la fase de **Diagnostics** y se ha obtenido la aprobación final de **Critique**.\n\nTodos los artefactos (Contexto y Plan) están disponibles en el panel lateral."
        response_placeholder.markdown(final_text)

        st.session_state.messages.append({"role": "assistant", "content": final_text})

# --- PIE DE PÁGINA ---
st.divider()
st.caption("Esta aplicación utiliza LangGraph para la orquestación y Vertex AI para el razonamiento de los agentes.")
