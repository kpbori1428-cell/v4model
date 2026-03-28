import streamlit as st

def generate_agent_code(config):
    class_name = config['class_name']
    project = config['project_id']
    location = config['location']
    model = config['model_name']
    tools = config['tools']

    code = ["from typing import Any, Dict, Callable, Sequence, Iterable, TypedDict"]

    if config['enable_type_annotations']:
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

    code.append(f"""
class {class_name}:
    def __init__(
        self,
        model: str = "{model}",
        tools: Sequence[Callable] = [{tools}],
        project: str = "{project}",
        location: str = "{location}",
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.location = location

    def set_up(self):""")

    if config['enable_tracing']:
        code.append("""        from opentelemetry import trace
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

    if config['enable_secrets']:
        code.append("""        from google.cloud import secretmanager
        self.secret_manager_client = secretmanager.SecretManagerServiceClient()""")

    code.append("""        import vertexai
        from langchain_google_vertexai import ChatVertexAI
        from langgraph.prebuilt import create_react_agent

        vertexai.init(project=self.project, location=self.location)
        model = ChatVertexAI(model_name=self.model_name)
        self.graph = create_react_agent(model, tools=self.tools)
""")

    query_decorator = "@error_wrapper\n    " if config['enable_error_handling'] else ""
    config_param = "config: RunnableConfig = None, " if config['enable_type_annotations'] else ""

    code.append(f"""    {query_decorator}def query(self, {config_param}**kwargs):
        from langchain.load.dump import dumpd
        return dumpd(self.graph.invoke(**kwargs))""")

    if config['enable_async']:
        code.append(f"""
    {query_decorator}async def async_query(self, {config_param}**kwargs):
        from langchain.load.dump import dumpd
        result = await self.graph.ainvoke(**kwargs)
        return dumpd(result)""")

    if config['enable_streaming']:
        code.append(f"""
    {query_decorator}def stream_query(self, {config_param}**kwargs) -> Iterable:
        from langchain.load.dump import dumpd
        for chunk in self.graph.stream(**kwargs):
            yield dumpd(chunk)""")

    if config['enable_async_streaming']:
        code.append(f"""
    {query_decorator}async def async_stream_query(self, {config_param}**kwargs):
        from langchain.load.dump import dumpd
        async for chunk in self.graph.astream(**kwargs):
            yield dumpd(chunk)""")

    if config['enable_register_ops']:
        sync_ops = ["query"]
        if config['enable_async']: sync_ops.append("async_query")

        stream_ops = []
        if config['enable_streaming']: stream_ops.append("stream_query")
        if config['enable_async_streaming']: stream_ops.append("async_stream_query")

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

    return "\n".join(code)

def main():
    st.set_page_config(page_title="Vertex AI Agent Generator", layout="wide")
    st.title("Vertex AI Agent Generator")
    st.markdown("Crea un sistema que se base en una interfaz visual para el desarrollo de un agente basado en el `README.md`.")

    with st.sidebar:
        st.header("Configuración Básica")
        class_name = st.text_input("Nombre de la Clase del Agente", value="MyAgent")
        project_id = st.text_input("Project ID", placeholder="your-project-id")
        location = st.text_input("Location", value="us-central1")
        model_name = st.text_input("Model Name", value="gemini-1.5-flash-002")

    st.info("Configura los detalles del agente en la barra lateral y en las opciones de abajo.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Herramientas (Tools)")
        tools_input = st.text_area("Lista de funciones (separadas por coma)", "get_exchange_rate", help="Nombre de las funciones de herramientas definidas en tu código.")

        st.subheader("Capacidades")
        enable_async = st.checkbox("Soportar consultas asíncronas (`async_query`)", value=False)
        enable_streaming = st.checkbox("Soportar streaming (`stream_query`)", value=False)
        enable_async_streaming = st.checkbox("Soportar streaming asíncrono (`async_stream_query`)", value=False)
        enable_register_ops = st.checkbox("Registrar métodos personalizados (`register_operations`)", value=False)
        enable_type_annotations = st.checkbox("Anotaciones de tipo avanzado (`TypedDict`)", value=False)

    with col2:
        st.subheader("Integraciones y Avanzado")
        enable_tracing = st.checkbox("Habilitar Cloud Trace (OpenInference)", value=False)
        enable_secrets = st.checkbox("Integración con Secret Manager", value=False)
        enable_error_handling = st.checkbox("Incluir manejo de errores (`error_wrapper`)", value=True)

        credential_type = st.selectbox(
            "Gestión de Credenciales",
            ["None", "ADC (Application Default Credentials)", "OAuth 2.0 (User Credentials)", "Identity Provider (Federated)"]
        )

    config = {
        'class_name': class_name,
        'project_id': project_id,
        'location': location,
        'model_name': model_name,
        'tools': tools_input,
        'enable_async': enable_async,
        'enable_streaming': enable_streaming,
        'enable_async_streaming': enable_async_streaming,
        'enable_tracing': enable_tracing,
        'enable_secrets': enable_secrets,
        'enable_error_handling': enable_error_handling,
        'credential_type': credential_type,
        'enable_register_ops': enable_register_ops,
        'enable_type_annotations': enable_type_annotations
    }

    st.divider()
    st.subheader("Código Generado")

    generated_code = generate_agent_code(config)

    st.code(generated_code, language="python")

    st.download_button(
        label="Descargar agente (.py)",
        data=generated_code,
        file_name=f"{class_name.lower()}_agent.py",
        mime="text/x-python"
    )

if __name__ == "__main__":
    main()
