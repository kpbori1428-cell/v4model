import streamlit as st
import pandas as pd
from typing import Any, Dict, Callable, Sequence, Iterable, TypedDict

# --- LÓGICA DE GENERACIÓN ---

def generate_tool_code(name, description, params, body):
    args_str = ", ".join([f"{p['Nombre']}: {p['Tipo']}" for p in params])
    docstring = f'    """{description}\n\n    Args:\n'
    for p in params:
        docstring += f"        {p['Nombre']}: {p['Descripción']}\n"
    docstring += '    """'
    body_lines = body.strip().split('\n')
    indented_body = "\n".join([f"    {line}" for line in body_lines])
    return f"def {name}({args_str}):\n{docstring}\n{indented_body}\n"

def generate_agent_code(config, tools_library):
    class_name = config['class_name']
    project = config['project_id']
    location = config['location']
    model = config['model_name']
    selected_tool_names = config['tools']

    code = ["from typing import Any, Dict, Callable, Sequence, Iterable, TypedDict"]

    # Inyectar definiciones de herramientas seleccionadas
    if selected_tool_names:
        code.append("\n# --- HERRAMIENTAS (TOOLS) ---")
        for name in selected_tool_names:
            if name in tools_library:
                code.append(tools_library[name])
    else:
        code.append("""
# EJEMPLO DE CREACIÓN DE HERRAMIENTA (Tool):
# def get_weather(location: str):
#     \"\"\"Obtiene el clima actual para una ubicación específica.
#     Args:
#         location: Ciudad y país, ej. San Francisco, CA
#     \"\"\"
#     return f"El clima en {location} es de 22 grados Celsius y soleado."
""")

    if config['enable_type_annotations'] or config['enable_state_mgmt']:
        code.append("""
# schemas.py
class RunnableConfig(TypedDict, total=False):
    metadata: Dict[str, Any]
    configurable: Dict[str, Any]
""")

    if config['enable_error_handling']:
        code.append("from functools import wraps\nimport asyncio\nimport inspect")
        code.append("""
def error_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if inspect.iscoroutinefunction(func):
            async def async_wrapper():
                try:
                    return await func(*args, **kwargs)
                except Exception as err:
                    return _format_error(func, err)
            return async_wrapper()
        elif inspect.isasyncgenfunction(func):
            async def async_gen_wrapper():
                try:
                    async for chunk in func(*args, **kwargs):
                        yield chunk
                except Exception as err:
                    yield _format_error(func, err)
            return async_gen_wrapper()
        else:
            try:
                return func(*args, **kwargs)
            except Exception as err:
                return _format_error(func, err)
    return wrapper

def _format_error(func, err):
    error_code = getattr(err, 'code', 500)
    error_message = str(err)
    return {
        "error": {
            "code": error_code,
            "message": f"'{func.__name__}': {error_message}"
        }
    }
""")

    tools_str = ", ".join(selected_tool_names) if selected_tool_names else ""
    tools_list = f"[{tools_str}]" if tools_str else "[]"

    code.append(f"""
class {class_name}:
    def __init__(
        self,
        model: str = "{model}",
        tools: Sequence[Callable] = {tools_list},
        project: str = "{project}",
        location: str = "{location}",
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.location = location

    def set_up(self):""")

    if config['enable_tracing']:
        if config['tracing_provider'] == "OpenInference":
            code.append("""        # Tracing with OpenInference
        from opentelemetry import trace
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from openinference.instrumentation.langchain import LangChainInstrumentor
        import google.cloud.trace_v2 as cloud_trace_v2
        import google.auth

        credentials, _ = google.auth.default()
        trace.set_tracer_provider(TracerProvider())
        cloud_trace_exporter = CloudTraceSpanExporter(
            project_id=self.project,
            client=cloud_trace_v2.TraceServiceClient(
                credentials=credentials.with_quota_project(self.project),
            ),
        )
        trace.get_tracer_provider().add_span_processor(
            SimpleSpanProcessor(cloud_trace_exporter)
        )
        LangChainInstrumentor().instrument()""")
        else:
            code.append("""        # Tracing with OpenLLMetry
        from traceloop.sdk import Traceloop
        Traceloop.init(project_id=self.project, disable_batching=True)""")

    if config['enable_secrets']:
        code.append("""        from google.cloud import secretmanager
        self.secret_manager_client = secretmanager.SecretManagerServiceClient()""")

    if config['env_vars'].strip():
        code.append("        import os")
        for line in config['env_vars'].strip().split('\n'):
            if '=' in line:
                key, val = line.split('=', 1)
                code.append(f'        os.environ["{key.strip()}"] = "{val.strip()}"')

    code.append("""        import vertexai
        from langchain_google_vertexai import ChatVertexAI
        from langgraph.prebuilt import create_react_agent

        vertexai.init(project=self.project, location=self.location)
        model = ChatVertexAI(model_name=self.model_name)
        self.graph = create_react_agent(model, tools=self.tools)
""")

    query_decorator = "@error_wrapper\n    " if config['enable_error_handling'] else ""
    config_param = "config: RunnableConfig = None, " if (config['enable_type_annotations'] or config['enable_state_mgmt']) else ""

    code.insert(1, "from langchain.load.dump import dumpd")

    code.append(f"""    {query_decorator}def query(self, {config_param}**kwargs):
        return dumpd(self.graph.invoke(**kwargs))""")

    if config['enable_async']:
        code.append(f"""
    {query_decorator}async def async_query(self, {config_param}**kwargs):
        result = await self.graph.ainvoke(**kwargs)
        return dumpd(result)""")

    if config['enable_streaming']:
        code.append(f"""
    {query_decorator}def stream_query(self, {config_param}**kwargs) -> Iterable:
        for chunk in self.graph.stream(**kwargs):
            yield dumpd(chunk)""")

    if config['enable_async_streaming']:
        code.append(f"""
    {query_decorator}async def async_stream_query(self, {config_param}**kwargs):
        async for chunk in self.graph.astream(**kwargs):
            yield dumpd(chunk)""")

    if config['enable_state_mgmt']:
        code.append(f"""
    {query_decorator}def get_state(self, config: RunnableConfig = None):
        return self.graph.get_state(config=config)._asdict()

    {query_decorator}def get_state_history(self, config: RunnableConfig = None) -> Iterable:
        for state_snapshot in self.graph.get_state_history(config=config):
            yield state_snapshot._asdict()""")

    if config['enable_register_ops']:
        sync_ops = ["query"]
        if config['enable_async']: sync_ops.append("async_query")
        if config['enable_state_mgmt']: sync_ops.append("get_state")

        stream_ops = []
        if config['enable_streaming']: stream_ops.append("stream_query")
        if config['enable_async_streaming']: stream_ops.append("async_stream_query")
        if config['enable_state_mgmt']: stream_ops.append("get_state_history")

        code.append(f"""
    def register_operations(self):
        return {{
            "": {sync_ops},
            "stream": {stream_ops},
        }}""")

    if config['credential_type'] != "None":
        if config['credential_type'].startswith("ADC"):
            code.append("""
    def get_credentials(self):
        import google.auth
        import google.auth.transport.requests
        # Note: the credential lives for 1 hour by default.
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(google.auth.transport.requests.Request())
        return creds""")
        elif config['credential_type'].startswith("OAuth"):
            code.append("""
    def get_oauth_credentials(self, access_token, refresh_token=None):
        import google.oauth2.credentials
        return google.oauth2.credentials.Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token"
        )""")
        elif config['credential_type'].startswith("Identity"):
            code.append("""
    def setup_identity_platform(self, credentials):
        import vertexai
        vertexai.init(
            project=self.project,
            location=self.location,
            credentials=credentials,
        )""")

    code.append(f"""
\"\"\"
EJEMPLOS DE USO LOCAL (Basados en README.md):

# 1. Instanciar el agente
agent = {class_name}(
    project="{project}",
    location="{location}"
)
agent.set_up()

# 2. Probar consulta síncrona
response = agent.query(input="Hola, ¿qué puedes hacer?")
print(response)
\"\"\"""")

    return "\n".join(code)

# --- APLICACIÓN PRINCIPAL ---

def main():
    st.set_page_config(page_title="Vertex AI Agent Suite", layout="wide")
    st.title("🤖 Vertex AI Agent Suite")

    if 'tools_library' not in st.session_state:
        st.session_state.tools_library = {}

    tab_agent, tab_tools = st.tabs(["🚀 Constructor de Agentes", "🛠️ Diseñador de Herramientas"])

    with tab_agent:
        col_side, col_main = st.columns([1, 2])

        with col_side:
            st.header("Configuración")
            class_name = st.text_input("Nombre de la Clase", value="MyAgent")
            project_id = st.text_input("Project ID", placeholder="your-project-id")
            location = st.text_input("Location", value="us-central1")
            model_name = st.text_input("Model Name", value="gemini-1.5-flash-002")

            st.subheader("Habilidades Seleccionadas")
            selected_tools = st.multiselect(
                "Elige herramientas de tu biblioteca",
                options=list(st.session_state.tools_library.keys()),
                help="Las herramientas se definen en la pestaña 'Diseñador de Herramientas'."
            )

        with col_main:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Capacidades")
                enable_async = st.checkbox("Consultas Asíncronas", value=False)
                enable_streaming = st.checkbox("Soportar Streaming", value=False)
                enable_async_streaming = st.checkbox("Streaming Asíncrono", value=False)
                enable_register_ops = st.checkbox("Registrar Operaciones", value=False)
                enable_type_annotations = st.checkbox("TypedDict Annotations", value=False)
                enable_state_mgmt = st.checkbox("Gestión de Estado", value=False)

            with col2:
                st.subheader("Integraciones")
                enable_tracing = st.checkbox("Habilitar Cloud Trace", value=False)
                tracing_provider = st.selectbox("Proveedor", ["OpenInference", "OpenLLMetry"], disabled=not enable_tracing)
                enable_secrets = st.checkbox("Secret Manager", value=False)
                enable_error_handling = st.checkbox("Error Wrapper", value=True)
                env_vars = st.text_area("Vars de Entorno (K=V)", "")
                credential_type = st.selectbox("Credenciales", ["None", "ADC", "OAuth", "Identity"])

            st.divider()
            config = {
                'class_name': class_name, 'project_id': project_id, 'location': location,
                'model_name': model_name, 'tools': selected_tools,
                'enable_async': enable_async, 'enable_streaming': enable_streaming,
                'enable_async_streaming': enable_async_streaming, 'enable_tracing': enable_tracing,
                'tracing_provider': tracing_provider, 'enable_secrets': enable_secrets,
                'enable_error_handling': enable_error_handling, 'credential_type': credential_type,
                'enable_register_ops': enable_register_ops, 'enable_type_annotations': enable_type_annotations,
                'enable_state_mgmt': enable_state_mgmt, 'env_vars': env_vars
            }

            generated_code = generate_agent_code(config, st.session_state.tools_library)
            st.code(generated_code, language="python")
            st.download_button("Descargar Agente (.py)", generated_code, f"{class_name.lower()}.py")

    with tab_tools:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.header("Nueva Herramienta")
            t_name = st.text_input("Nombre de la Función", value="nueva_herramienta")
            t_desc = st.text_area("Descripción", "Explica qué hace la herramienta.")

            st.subheader("Parámetros")
            df_params = pd.DataFrame([{"Nombre": "param1", "Tipo": "str", "Descripción": "descripción"}])
            params_data = st.data_editor(df_params, num_rows="dynamic", use_container_width=True)

            st.subheader("Lógica")
            t_body = st.text_area("Cuerpo (Python)", "return 'Resultado'", height=150)

            if st.button("✅ Guardar en Biblioteca"):
                tool_code = generate_tool_code(t_name, t_desc, params_data.to_dict('records'), t_body)
                st.session_state.tools_library[t_name] = tool_code
                st.success(f"Herramienta '{t_name}' guardada correctamente.")

        with col_t2:
            st.header("Biblioteca")
            if not st.session_state.tools_library:
                st.info("Aún no has guardado ninguna herramienta.")
            for name, code in st.session_state.tools_library.items():
                with st.expander(f"📦 {name}"):
                    st.code(code, language="python")
                    if st.button(f"Eliminar {name}"):
                        del st.session_state.tools_library[name]
                        st.rerun()

if __name__ == "__main__":
    main()
