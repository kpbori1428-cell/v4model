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
    auth_mode = st.radio("Modo de Auth", ["Local (Solo Herramientas)", "Vertex AI (Service Account JSON)", "Vertex AI (API Key)", "Vertex AI (OAuth)"], index=0)

    api_key = None
    service_account_path = None
    if auth_mode == "Vertex AI (API Key)":
        api_key = st.text_input("Google API Key", type="password")
    elif auth_mode == "Vertex AI (Service Account JSON)":
        uploaded_json = st.file_uploader("Subir llave JSON", type=["json"])
        if uploaded_json:
            import tempfile
            # Guardar temporalmente para que el agente pueda leerlo
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                tmp.write(uploaded_json.getvalue())
                service_account_path = tmp.name

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
    with st.spinner("🤖 Inicializando Motor de Multi-Agentes..."):
        agent = RobustMultiAgent(project=project_id, location=location)
        if auth_mode == "Vertex AI (API Key)" and api_key:
            agent.set_api_key(api_key)
        elif auth_mode == "Vertex AI (Service Account JSON)" and service_account_path:
            agent.set_credentials_json(service_account_path)
        agent.set_up()

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        status_container = st.status("🚀 Ejecutando Flujo de Trabajo Local...", expanded=True)

        # Ejecución real mediante streaming
        try:
            input_state = {"messages": [{"role": "user", "content": prompt}]}
            final_response = ""
            mission_started = False

            for chunk in agent.graph.stream(input_state):
                for node_name, output in chunk.items():
                    if node_name == "Architect":
                        final_response = output["messages"][-1].content
                        if "[START_MISSION]" in final_response.upper():
                            mission_started = True
                            status_container.write("🚀 **El Arquitecto ha iniciado la misión técnica.**")
                        else:
                            status_container.update(label="💬 Consulta Finalizada", state="complete", expanded=False)
                    else:
                        status_container.write(f"**[Agente: {node_name}]** trabajando...")

                    # Actualizar UI con datos reales del estado
                    current_state = agent.graph.get_state()
                    if 'context_bundle' in current_state.values:
                        context_placeholder.json(current_state.values['context_bundle'])
                    if 'implementation_plan' in current_state.values:
                        plan_placeholder.json(current_state.values['implementation_plan'])

            if mission_started:
                status_container.update(label="✅ Misión Local Completada", state="complete", expanded=False)
                final_text = f"{final_response}\n\n**[Misión Finalizada]**\n\nLos agentes han completado la tarea técnica. Se han aplicado cambios reales en el sistema de archivos si fue solicitado."
            else:
                final_text = final_response

            response_placeholder.markdown(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})

        except Exception as e:
            status_container.error(f"Error en ejecución: {str(e)}")
            st.error("Asegúrate de configurar las credenciales correctas en el panel lateral.")

# --- PIE DE PÁGINA ---
st.divider()
st.caption("Esta aplicación utiliza LangGraph para la orquestación y Vertex AI para el razonamiento de los agentes.")
