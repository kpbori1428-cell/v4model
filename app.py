import streamlit as st
import pandas as pd
import json
import os
import requests
from typing import Any, Dict, Callable, Sequence, Iterable, TypedDict

# --- CONFIGURACIÓN DE PERSISTENCIA ---
TOOLS_FILE = "tools.json"
AGENTS_FILE = "agents.json"

def load_tools():
    if os.path.exists(TOOLS_FILE):
        try:
            with open(TOOLS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_tools(library):
    with open(TOOLS_FILE, "w") as f:
        json.dump(library, f, indent=4)

def load_agents():
    if os.path.exists(AGENTS_FILE):
        try:
            with open(AGENTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_agent(name, config):
    agents = load_agents()
    agents[name] = config
    with open(AGENTS_FILE, "w") as f:
        json.dump(agents, f, indent=4)

# --- SYSTEM TOOLS (AUTONOMOUS EVOLUTION) ---

def system_register_skill(name: str, description: str, params: list, code: str):
    """Permite al agente registrar una nueva habilidad técnica en la biblioteca."""
    library = load_tools()
    tool_data = {
        "code": generate_tool_code(name, description, params, code),
        "hitl": False # Por defecto, herramientas auto-generadas no tienen HITL a menos que se pida
    }
    library[name] = tool_data
    save_tools(library)
    return f"Habilidad '{name}' registrada con éxito en tools.json."

def system_define_agent(name: str, config: dict):
    """Permite al agente diseñar y guardar una nueva configuración de agente especializado."""
    save_agent(name, config)
    return f"Agente '{name}' guardado con éxito en agents.json."

# --- LÓGICA DE SIMULACIÓN Y CONEXIÓN REAL (PLAYGROUND) ---

def instantiate_agent_live(config, tools_library, access_token=None, system_tools=None):
    """
    Instancia un agente para el playground.
    Si access_token existe, intenta conexión real via REST.
    """
    selected_tools = config['tools']
    tool_defs = [tools_library[name] for name in selected_tools if name in tools_library]
    all_tools = {**(system_tools or {})}

    class RealAgent:
        def __init__(self, config, tool_defs, token, sys_tools):
            self.config = config
            self.tool_defs = tool_defs
            self.token = token
            self.sys_tools = sys_tools
            self.base_url = f"https://{config['location']}-aiplatform.googleapis.com/v1/projects/{config['project_id']}/locations/{config['location']}/publishers/google/models/{config['model_name']}:generateContent"

        def query(self, input_text):
            if not self.token:
                return self._mock_response(input_text)

            # Construir contexto de herramientas para el prompt real
            tool_ctx = ""
            if self.tool_defs:
                tool_ctx = "\n\n[HERRAMIENTAS DISPONIBLES]:\n"
                for t in self.tool_defs:
                    if isinstance(t, dict):
                        tool_ctx += f"- {t['code'].split('(')[0].replace('def ', '')}\n"
                    else:
                        tool_ctx += f"- Skill: {t[:50]}...\n"

            # Llamada Real via REST (Simplificada para Gemini)
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{self.config.get('system_prompt', 'Eres un asistente técnico.')}{tool_ctx}\n\nUser input: {input_text}"}]}
                ],
                "generationConfig": {
                    "temperature": self.config['temperature'],
                    "topP": self.config['top_p'],
                    "topK": self.config['top_k'],
                    "maxOutputTokens": self.config['max_tokens']
                }
            }

            try:
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    try:
                        text = data['candidates'][0]['content']['parts'][0]['text']
                        return {"output": text, "debug": json.dumps(data, indent=2)}
                    except (KeyError, IndexError):
                        return {"output": "Respuesta recibida pero con formato inesperado.", "debug": json.dumps(data, indent=2)}
                else:
                    return {
                        "output": f"❌ Error de API ({response.status_code}): {response.text}",
                        "debug": f"Status: {response.status_code}\nHeaders: {response.headers}"
                    }
            except Exception as e:
                return {"output": f"❌ Error de Conexión: {str(e)}", "debug": "Connection failed"}

        def _mock_response(self, input_text):
            tool_names = ", ".join(self.config['tools']) or "ninguna"
            sys_p = self.config['system_prompt']
            resp = f"**[MOCK]** Respondiendo como: {self.config['class_name']}\n\n"
            resp += f"Instrucciones: _{sys_p}_\n\n"
            resp += f"Respuesta a '{input_text}': Entendido. Utilizaré mi configuración (Temp: {self.config['temperature']}) para asistirte."

            debug_info = {
                "mode": "Simulated (No Token)",
                "model": self.config['model_name'],
                "params": {
                    "temperature": self.config['temperature'],
                    "top_p": self.config['top_p'],
                    "max_tokens": self.config['max_tokens']
                },
                "tools_active": tool_names
            }
            return {"output": resp, "debug": json.dumps(debug_info, indent=2)}

    return RealAgent(config, tool_defs, access_token, system_tools)

def instantiate_agent_mock(config, tools_library, system_tools=None):
    """
    Simula la instanciación de un agente para el playground.
    En una versión real, esto usaría vertexai.init y ChatVertexAI.
    """
    selected_tools = config['tools']
    tool_defs = [tools_library[name] for name in selected_tools if name in tools_library]

    # Mock de respuesta del agente basado en la configuración
    class MockAgent:
        def __init__(self, config, tool_defs, sys_tools):
            self.config = config
            self.tool_defs = tool_defs
            self.sys_tools = sys_tools

        def query(self, input_text):
            # Lógica de simulación avanzada (Misión Multi-Agente)
            nodes = self.config.get('nodes', [])
            edges = self.config.get('edges', [])

            if not nodes:
                return {"output": "⚠️ Error: No hay nodos definidos.", "debug": "Architecture empty"}

            # Simular traza de ejecución de la Misión
            trace = []
            current_node = nodes[0]['Nodo']
            steps_limit = 15

            trace.append(f"🏁 Iniciando flujo en nodo: {current_node}")

            # Simulación de handoffs
            for _ in range(steps_limit):
                node_info = next((n for n in nodes if n['Nodo'] == current_node), None)
                if not node_info: break

                trace.append(f"➡️ [EJECUTANDO: {current_node}] -> Prompt: {node_info['Prompt'][:50]}...")

                # Buscar siguiente nodo
                next_edge = next((e for e in edges if e['Origen'] == current_node), None)
                if not next_edge:
                    trace.append(f"🔚 Fin de flujo (No hay más aristas desde {current_node})")
                    break

                current_node = next_edge['Destino']
                if current_node.upper() == "END":
                    trace.append("🔚 Fin de flujo alcanzado (END)")
                    break
                trace.append(f"📤 Handoff -> Siguiente nodo: {current_node}")

            resp = f"**[MOCK MULTI-AGENTE]**\n\nEjecución completada siguiendo el grafo de {len(nodes)} nodos.\n\n"
            resp += f"**Entrada:** {input_text}\n"
            resp += f"**Resultado Final:** El sistema ha procesado la consulta a través de {current_node}."

            debug_info = {
                "model": self.config['model_name'],
                "nodes": [n['Nodo'] for n in nodes],
                "execution_trace": trace,
                "edges_active": len(edges)
            }

            # Simular detección de llamada a herramienta de sistema
            if "register_skill" in input_text or "define_agent" in input_text:
                trace.append("🛠️ [SYSTEM TOOL DETECTED] Simulando ejecución de herramienta de evolución...")
                if "register_skill" in input_text:
                    trace.append("✅ Habilidad registrada en tools.json (Simulado)")
                if "define_agent" in input_text:
                    trace.append("✅ Nuevo agente guardado en agents.json (Simulado)")

            return {
                "output": resp,
                "debug": json.dumps(debug_info, indent=2)
            }

    return MockAgent(config, tool_defs, system_tools)

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
    model_name = config['model_name']
    selected_tool_names = config['tools']

    code = ["import json\nimport pandas as pd\nfrom typing import Any, Dict, Callable, Sequence, Iterable, TypedDict, Annotated, List, Union"]

    # Inyectar definiciones de herramientas seleccionadas
    hitl_tools_list_ref = []
    if selected_tool_names:
        code.append("\n# --- HERRAMIENTAS (TOOLS) ---")
        for name in selected_tool_names:
            if name in tools_library:
                t_data = tools_library[name]
                # Backward compatibility check
                if isinstance(t_data, str):
                    code.append(t_data)
                else:
                    code.append(t_data['code'])
                    if t_data.get('hitl'): hitl_tools_list_ref.append(name)
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

    # Generación dinámica del Estado (Soporte de Artefactos Estrictos)
    state_schema = config.get('state_schema', [])
    state_lines = ["class AgentState(TypedDict):"]
    if not any(v['Variable'] == 'messages' for v in state_schema):
        state_lines.append("    messages: Annotated[List[Any], lambda x, y: x + y]")

    # Inyectar artefactos obligatorios para misiones profesionales
    if not any(v['Variable'] == 'context_bundle' for v in state_schema):
        state_lines.append("    context_bundle: Dict[str, Any]")
    if not any(v['Variable'] == 'implementation_plan' for v in state_schema):
        state_lines.append("    implementation_plan: Dict[str, Any]")

    for var in state_schema:
        v_name = var['Variable']
        v_type = var['Tipo']
        if v_type == 'list': py_type = "List[Any]"
        elif v_type == 'dict': py_type = "Dict[str, Any]"
        elif v_type == 'int': py_type = "int"
        elif v_type == 'float': py_type = "float"
        else: py_type = "str"
        state_lines.append(f"    {v_name}: {py_type}")

    code.append("\n".join(state_lines))

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
        model: str = "{model_name}",
        tools: Sequence[Callable] = {tools_list},
        project: str = "{project}",
        location: str = "{location}",
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.location = location
        self.nodes_config = {config['nodes']}
        self.edges_config = {config['edges']}

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

    code.append(f"""        import vertexai
        from langchain_google_vertexai import ChatVertexAI
        from langgraph.graph import StateGraph, END
        from langgraph.checkpoint.memory import MemorySaver
        from langchain_core.messages import SystemMessage

        vertexai.init(project=self.project, location=self.location)

        # Modelo con parámetros avanzados
        self.llm = ChatVertexAI(
            model_name=self.model_name,
            temperature={config['temperature']},
            top_p={config['top_p']},
            top_k={config['top_k']},
            max_output_tokens={config['max_tokens']}
        )

        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        # Definición manual del Grafo (StateGraph Multi-Nodo)
        workflow = StateGraph(AgentState)

        # Generación dinámica de nodos
        for node in self.nodes_config:
            node_name = node['Nodo']
            node_prompt = node['Prompt']

            def make_node_func(p, name):
                def _node(state):
                    # Inyectar artefactos en el prompt para asegurar consistencia
                    context = state.get('context_bundle', {{}})
                    plan = state.get('implementation_plan', {{}})

                    artifact_prompt = f"\\n\\n[CONTEXTO ACTUAL]: {{json.dumps(context)}}\\n[PLAN ACTUAL]: {{json.dumps(plan)}}"
                    messages = [SystemMessage(content=p + artifact_prompt)] + state['messages']

                    response = self.llm_with_tools.invoke(messages)

                    # Lógica de extracción de artefactos (Simulada para el template)
                    # En producción, esto usaría Structured Output / Pydantic
                    return {{"messages": [response]}}
                return _node

            workflow.add_node(node_name, make_node_func(node_prompt, node_name))

        workflow.set_entry_point(self.nodes_config[0]['Nodo'])
""")

    # Configuración de Flujo Dinámico (Generación de Código en Tiempo de Diseño)
    code_transitions = []
    from collections import defaultdict
    node_transitions = defaultdict(list)
    for edge in config['edges']:
        node_transitions[edge['Origen']].append(edge)

    for s_node, transitions in node_transitions.items():
        if len(transitions) == 1 and transitions[0].get('Condición', 'Éxito') == 'Éxito':
            dest = transitions[0]['Destino']
            if dest.upper() == "END":
                code_transitions.append(f'        workflow.add_edge("{s_node}", END)')
            elif dest.upper() == s_node.upper():
                code_transitions.append(f'        workflow.add_edge("{s_node}", END) # Auto-loop prevent')
            else:
                code_transitions.append(f'        workflow.add_edge("{s_node}", "{dest}")')
        else:
            # Generar router dinámico para este nodo
            router_name = f"router_{s_node.lower()}"
            r_lines = [
                f"        def {router_name}(state):",
                "            last_msg = state['messages'][-1].content.lower()"
            ]

            # Prioridad condiciones
            for t in transitions:
                cond_val = t.get('Condición', 'Éxito')
                dest_val = t['Destino']
                if cond_val != 'Éxito':
                    target_code = "END" if dest_val.upper() == "END" else f'"{dest_val}"'
                    r_lines.append(f'            if "{cond_val.lower()}" in last_msg: return {target_code}')

            # Fallback éxito
            success_t = next((t for t in transitions if t.get('Condición', 'Éxito') == 'Éxito'), None)
            if success_t:
                dest_val = success_t['Destino']
                target_code = "END" if dest_val.upper() == "END" else f'"{dest_val}"'
                r_lines.append(f"            return {target_code}")
            else:
                r_lines.append("            return END")

            code_transitions.append("\n".join(r_lines))
            code_transitions.append(f'        workflow.add_conditional_edges("{s_node}", {router_name})')

    code.append("\n".join(code_transitions))

    code.append(f"""
        # Inyección de Herramientas (Si existen)
        if self.tools:
            from langgraph.prebuilt import ToolNode
            workflow.add_node("tools", ToolNode(self.tools))
            # Las herramientas suelen conectarse tras el nodo de ejecución o según el LLM decida
            # Aquí permitimos que cualquier nodo llame a herramientas si el LLM lo indica
            def tool_router(state):
                if hasattr(state['messages'][-1], "tool_calls") and state['messages'][-1].tool_calls:
                    return "tools"
                return "continue"

        workflow.set_entry_point(self.nodes_config[0]['Nodo'])

        # Implementación de HITL y Persistencia
        interrupt_tools = {hitl_tools_list_ref}
        memory = MemorySaver() # Usar persistencia en memoria para el template

        if interrupt_tools:
            self.graph = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
        else:
            self.graph = workflow.compile(checkpointer=memory)
""")

    # 4. Métodos de Consulta
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
        st.session_state.tools_library = load_tools()

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    agents_library = load_agents()

    # --- INYECTAR PRESET DE MISIÓN (SI NO EXISTE) ---
    MISSION_PRESET_NAME = "Misión: Multi-Agente Robusto"
    if MISSION_PRESET_NAME not in agents_library:
        agents_library[MISSION_PRESET_NAME] = {
            "class_name": "RobustMultiAgent",
            "project_id": "",
            "location": "us-central1",
            "model_name": "gemini-2.5-flash",
            "tools": [],
            "nodes": [
                {"Nodo": "Discovery", "Prompt": "Construye el mapa de verdad. Extrae definiciones y tipos vía LSP/Vectores. Responde con un Context Bundle (JSON)."},
                {"Nodo": "Planning", "Prompt": "Genera un Implementation Plan (JSON) atómico. No generes código, solo lógica secuencial."},
                {"Nodo": "Execution", "Prompt": "Manipula archivos. Genera Hunks (diffs) con contexto de 3 líneas. Usa Read/Write tools."},
                {"Nodo": "Diagnostics", "Prompt": "Linter/Compilador virtual. Busca errores de tipo o sintaxis. Devuelve 'Zero Errors' o falla."},
                {"Nodo": "Testing", "Prompt": "Ejecuta tests en Sandbox. Si falla un test lógico, devuelve el stack trace a Planning para re-ajuste."},
                {"Nodo": "Critique", "Prompt": "Auditoría final de calidad, seguridad y estándares. Emite Verdict (Aprobado o Veto)."}
            ],
            "edges": [
                {"Origen": "Discovery", "Destino": "Planning", "Condición": "Éxito"},
                {"Origen": "Planning", "Destino": "Execution", "Condición": "Éxito"},
                {"Origen": "Execution", "Destino": "Diagnostics", "Condición": "Éxito"},
                {"Origen": "Diagnostics", "Destino": "Execution", "Condición": "Error"},
                {"Origen": "Diagnostics", "Destino": "Testing", "Condición": "Zero Errors"},
                {"Origen": "Testing", "Destino": "Planning", "Condición": "Fallo"},
                {"Origen": "Testing", "Destino": "Critique", "Condición": "Éxito"},
                {"Origen": "Critique", "Destino": "Planning", "Condición": "Veto"},
                {"Origen": "Critique", "Destino": "END", "Condición": "Aprobado"}
            ],
            "temperature": 0.1, "top_p": 0.95, "top_k": 40, "max_tokens": 4096,
            "state_schema": [
                {"Variable": "context_bundle", "Tipo": "dict", "Default": "{}"},
                {"Variable": "plan", "Tipo": "dict", "Default": "{}"},
                {"Variable": "hunks", "Tipo": "list", "Default": "[]"},
                {"Variable": "diagnostics", "Tipo": "str", "Default": "''"}
            ],
            "enable_async": True, "enable_streaming": False, "enable_async_streaming": False,
            "enable_tracing": True, "tracing_provider": "OpenInference", "enable_secrets": True,
            "enable_error_handling": True, "credential_type": "OAuth", "enable_register_ops": True,
            "enable_type_annotations": True, "enable_state_mgmt": True, "env_vars": ""
        }

    META_PRESET_NAME = "🤖 Meta-Arquitecto (Evolución Autónoma)"
    if META_PRESET_NAME not in agents_library:
        agents_library[META_PRESET_NAME] = {
            "class_name": "MetaArchitect",
            "project_id": "",
            "location": "us-central1",
            "model_name": "gemini-2.5-flash",
            "tools": [],
            "nodes": [
                {"Nodo": "SelfAnalysis", "Prompt": "Analiza las capacidades actuales del sistema. Si falta una habilidad o un agente especializado para la tarea del usuario, utiliza 'register_skill' o 'define_agent'."},
                {"Nodo": "Orchestrator", "Prompt": "Una vez creadas las nuevas capacidades, delega la tarea final al nuevo agente o utiliza la nueva habilidad."}
            ],
            "edges": [
                {"Origen": "SelfAnalysis", "Destino": "Orchestrator", "Condición": "Éxito"},
                {"Origen": "Orchestrator", "Destino": "END", "Condición": "Éxito"}
            ],
            "temperature": 0.3, "top_p": 0.9, "top_k": 40, "max_tokens": 2048,
            "state_schema": [],
            "enable_async": True, "enable_streaming": False, "enable_async_streaming": False,
            "enable_tracing": False, "tracing_provider": "OpenInference", "enable_secrets": False,
            "enable_error_handling": True, "credential_type": "OAuth", "enable_register_ops": False,
            "enable_type_annotations": False, "enable_state_mgmt": True, "env_vars": ""
        }

    tab_agent, tab_tools, tab_play = st.tabs(["🚀 Constructor de Agentes", "🛠️ Diseñador de Herramientas", "🎮 Playground"])

    with tab_agent:
        col_side, col_main = st.columns([1, 2])

        with col_side:
            st.header("Versiones")
            if agents_library:
                selected_version = st.selectbox("Cargar Versión", [""] + list(agents_library.keys()))
                if selected_version:
                    v_config = agents_library[selected_version]
                    # Note: streamlit values are updated next run if we don't use keys,
                    # but for this simple tool we'll rely on session_state or default values.
                    st.info(f"Cargada versión: {selected_version}")
            else:
                st.caption("No hay versiones guardadas.")

            new_v_name = st.text_input("Nombre de Nueva Versión", "")

            st.divider()
            st.header("Configuración")

            # Default values logic based on selection
            def get_v(key, default):
                if agents_library and selected_version and key in agents_library[selected_version]:
                    return agents_library[selected_version][key]
                return default

            class_name = st.text_input("Nombre de la Clase", value=get_v('class_name', "MyAgent"))
            project_id = st.text_input("Project ID", value=get_v('project_id', ""), placeholder="your-project-id")
            location = st.text_input("Location", value=get_v('location', "us-central1"))
            model_name = st.text_input("Model Name", value=get_v('model_name', "gemini-2.5-flash"))

            st.subheader("Habilidades Seleccionadas")
            selected_tools = st.multiselect(
                "Elige herramientas de tu biblioteca",
                options=list(st.session_state.tools_library.keys()),
                default=get_v('tools', []),
                help="Las herramientas se definen en la pestaña 'Diseñador de Herramientas'."
            )

        with col_main:
            t_arch, t_params, t_state, t_integrations = st.tabs(["🏗️ Arquitectura", "🎚️ Parámetros", "🧠 Estado", "🔌 Integraciones"])

            with t_arch:
                st.subheader("Nodos (Agentes)")
                st.write("Define los roles que compondrán a tu sistema. Cada nodo es un agente independiente.")

                default_nodes = get_v('nodes', [{"Nodo": "manager", "Prompt": "Eres el coordinador central. Analiza la petición y delega."}])
                df_nodes = pd.DataFrame(default_nodes)
                nodes_config = st.data_editor(df_nodes, num_rows="dynamic", width="stretch")

                st.divider()
                st.subheader("Conexiones (Edges)")
                st.write("Define el flujo de control entre los agentes.")

                default_edges = get_v('edges', [{"Origen": "manager", "Destino": "END", "Condición": "Éxito"}])
                df_edges = pd.DataFrame(default_edges)
                edges_config = st.data_editor(df_edges, num_rows="dynamic", width="stretch")

                st.caption("Tip: Usa 'END' para finalizar el flujo. El primer nodo de la lista es la entrada.")

            with t_params:
                st.subheader("Configuración del Modelo")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    temperature = st.slider("Temperature", 0.0, 2.0, float(get_v('temperature', 0.5)), 0.1)
                    top_p = st.slider("Top P", 0.0, 1.0, float(get_v('top_p', 0.9)), 0.05)
                with col_p2:
                    top_k = st.number_input("Top K", 1, 100, int(get_v('top_k', 40)))
                    max_tokens = st.number_input("Max Output Tokens", 1, 8192, int(get_v('max_tokens', 2048)))

            with t_state:
                st.subheader("Esquema de Estado Personalizado")
                st.write("Define variables adicionales que el agente mantendrá en memoria.")
                default_state = get_v('state_schema', [{"Variable": "chat_history", "Tipo": "list", "Default": "[]"}])
                df_state = pd.DataFrame(default_state)
                state_schema = st.data_editor(df_state, num_rows="dynamic", width="stretch")

            with t_integrations:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Capacidades")
                    enable_async = st.checkbox("Consultas Asíncronas", value=get_v('enable_async', False))
                    enable_streaming = st.checkbox("Soportar Streaming", value=get_v('enable_streaming', False))
                    enable_async_streaming = st.checkbox("Streaming Asíncrono", value=get_v('enable_async_streaming', False))
                    enable_register_ops = st.checkbox("Registrar Operaciones", value=get_v('enable_register_ops', False))
                    enable_type_annotations = st.checkbox("TypedDict Annotations", value=get_v('enable_type_annotations', False))
                    enable_state_mgmt = st.checkbox("Gestión de Estado", value=get_v('enable_state_mgmt', True))

                with col2:
                    st.subheader("Integraciones de Cloud")
                    enable_tracing = st.checkbox("Habilitar Cloud Trace", value=get_v('enable_tracing', False))
                    provider_idx = ["OpenInference", "OpenLLMetry"].index(get_v('tracing_provider', "OpenInference"))
                    tracing_provider = st.selectbox("Proveedor", ["OpenInference", "OpenLLMetry"], index=provider_idx, disabled=not enable_tracing)
                    enable_secrets = st.checkbox("Secret Manager", value=get_v('enable_secrets', False))
                    enable_error_handling = st.checkbox("Error Wrapper", value=get_v('enable_error_handling', True))
                    env_vars = st.text_area("Vars de Entorno (K=V)", value=get_v('env_vars', ""))
                    cred_idx = ["None", "ADC", "OAuth", "Identity"].index(get_v('credential_type', "None"))
                    credential_type = st.selectbox("Credenciales", ["None", "ADC", "OAuth", "Identity"], index=cred_idx)

            st.divider()
            config = {
                'class_name': class_name, 'project_id': project_id, 'location': location,
                'model_name': model_name, 'tools': selected_tools,
                'nodes': nodes_config.to_dict('records'),
                'edges': edges_config.to_dict('records'),
                'temperature': temperature,
                'top_p': top_p, 'top_k': top_k, 'max_tokens': max_tokens,
                'state_schema': state_schema.to_dict('records'),
                'enable_async': enable_async, 'enable_streaming': enable_streaming,
                'enable_async_streaming': enable_async_streaming, 'enable_tracing': enable_tracing,
                'tracing_provider': tracing_provider, 'enable_secrets': enable_secrets,
                'enable_error_handling': enable_error_handling, 'credential_type': credential_type,
                'enable_register_ops': enable_register_ops, 'enable_type_annotations': enable_type_annotations,
                'enable_state_mgmt': enable_state_mgmt, 'env_vars': env_vars
            }

            generated_code = generate_agent_code(config, st.session_state.tools_library)

            c_code, c_save = st.columns([3, 1])
            with c_save:
                if st.button("💾 Guardar Versión", disabled=not new_v_name):
                    save_agent(new_v_name, config)
                    st.success(f"Versión '{new_v_name}' guardada.")
                    st.rerun()

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
            params_data = st.data_editor(df_params, num_rows="dynamic", width="stretch")

            st.subheader("Lógica y Control")
            t_body = st.text_area("Cuerpo (Python)", "return 'Resultado'", height=150)
            t_hitl = st.checkbox("Requiere aprobación humana (HITL)", value=False, help="El agente se detendrá antes de ejecutar esta herramienta.")

            if st.button("✅ Guardar en Biblioteca"):
                # Save as dict to keep metadata
                tool_data = {
                    "code": generate_tool_code(t_name, t_desc, params_data.to_dict('records'), t_body),
                    "hitl": t_hitl
                }
                st.session_state.tools_library[t_name] = tool_data
                save_tools(st.session_state.tools_library)
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
                        save_tools(st.session_state.tools_library)
                        st.rerun()

    with tab_play:
        st.header("🎮 Agent Playground")

        c_token, c_info = st.columns([1, 1])
        with c_token:
            mode = st.radio("Modo de Conexión", ["Simulación", "Token Directo", "OAuth Automático", "OAuth Manual (Código)"], horizontal=True)

            gcp_token = None
            if mode == "Token Directo":
                gcp_token = st.text_input("GCP Access Token", type="password")

            elif mode == "OAuth Automático":
                secrets_file = st.file_uploader("Sube tu client_secrets.json", type=["json"], key="auto_oauth")
                if secrets_file:
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    try:
                        if 'creds' not in st.session_state:
                            client_config = json.load(secrets_file)
                            flow = InstalledAppFlow.from_client_config(
                                client_config,
                                scopes=['https://www.googleapis.com/auth/cloud-platform']
                            )
                            st.warning("⚠️ Nota: El 'Modo Automático' abrirá una ventana en tu navegador y pausará esta interfaz hasta que completes el login. Si la app parece congelada, revisa tus pestañas abiertas.")
                            st.info("Iniciando flujo de autenticación...")
                            st.session_state.creds = flow.run_local_server(port=0, prompt='consent')
                        gcp_token = st.session_state.creds.token
                        st.success("✅ Autenticado correctamente.")
                    except Exception as e:
                        st.error(f"Error en OAuth Automático: {e}")

            elif mode == "OAuth Manual (Código)":
                secrets_file = st.file_uploader("Sube tu client_secrets.json", type=["json"], key="manual_oauth")
                if secrets_file:
                    from google_auth_oauthlib.flow import Flow
                    client_config = json.load(secrets_file)
                    flow = Flow.from_client_config(
                        client_config,
                        scopes=['https://www.googleapis.com/auth/cloud-platform'],
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    st.write(f"1. Abre esta URL: [Autorizar Google]({auth_url})")
                    code = st.text_input("2. Pega el código de autorización aquí:")
                    if code:
                        try:
                            flow.fetch_token(code=code)
                            st.session_state.creds = flow.credentials
                            gcp_token = st.session_state.creds.token
                            st.success("Token obtenido con éxito.")
                        except Exception as e:
                            st.error(f"Error al canjear código: {e}")

        with c_info:
            if gcp_token:
                st.success("🔥 MODO REAL ACTIVADO")
            else:
                st.info("🤖 Modo Simulación (Local)")

        c1, c2 = st.columns([3, 1])
        with c1:
            st.caption("Interactúa con tu agente. Si usas modo 'En Vivo', asegúrate que el Project ID y Location sean correctos.")
        with c2:
            c_clear, c_load = st.columns(2)
            if c_clear.button("🗑️ Limpiar"):
                st.session_state.messages = []
                st.rerun()

            uploaded_file = c_load.file_uploader("📂 Cargar Contexto", type=["json"], label_visibility="collapsed")
            if uploaded_file:
                st.session_state.messages = json.load(uploaded_file)
                st.rerun()

        # Sidebar-like debug panel in Playground
        with st.expander("🛠️ Panel de Depuración (Internals)", expanded=False):
            st.json(config)
            st.write(f"Herramientas activas: {len(config['tools'])}")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "debug" in message and message["role"] == "assistant":
                    with st.status("Ver traza de ejecución...", expanded=False):
                        st.write(message["debug"])

        # Chat input
        if prompt := st.chat_input("Escribe tu consulta..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response via Live/Mock Agent
            with st.spinner("🤖 El agente está pensando..."):
                # Inyectar herramientas de sistema para evolución autónoma
                sys_tools = {
                    "register_skill": system_register_skill,
                    "define_agent": system_define_agent
                }

                # Combinar biblioteca local con herramientas de sistema si el LLM las necesita
                # En modo real/REST esto requeriría un binding más complejo, pero para la demo
                # lo manejamos en la lógica de instanciación.

                # Usar Mock si no hay token, Real si lo hay
                if gcp_token:
                    agent = instantiate_agent_live(config, st.session_state.tools_library, access_token=gcp_token, system_tools=sys_tools)
                else:
                    agent = instantiate_agent_mock(config, st.session_state.tools_library, system_tools=sys_tools)

                response = agent.query(prompt)

            with st.chat_message("assistant"):
                st.markdown(response["output"])
                with st.status("Generando traza...", expanded=True):
                    st.write(response["debug"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": response["output"],
                "debug": response["debug"]
            })

if __name__ == "__main__":
    main()
