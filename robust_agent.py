import json
import pandas as pd
from typing import Any, Dict, Callable, Sequence, Iterable, TypedDict, Annotated, List, Union
from langchain_core.load.dump import dumpd

# --- HERRAMIENTAS (TOOLS) ---
def read_local_file(path: str):
    with open(path, "r") as f: return f.read()
def write_local_file(path: str, content: str):
    with open(path, "w") as f: f.write(content)
    return f"Escrito {path}"
import os
def list_local_dir(p="."): return os.listdir(p)

# schemas.py
class RunnableConfig(TypedDict, total=False):
    metadata: Dict[str, Any]
    configurable: Dict[str, Any]

class AgentState(TypedDict):
    messages: Annotated[List[Any], lambda x, y: x + y]
    context_bundle: Dict[str, Any]
    implementation_plan: Dict[str, Any]
from functools import wraps
import asyncio
import inspect

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


class RobustMultiAgent:
    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        tools: Sequence[Callable] = [read_local_file, write_local_file, list_local_dir],
        project: str = "your-project-id",
        location: str = "us-central1",
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.location = location
        self.nodes_config = [
            {'Nodo': 'Architect', 'Prompt': 'Eres el Arquitecto Principal. Tu objetivo es hablar con el usuario antes de empezar cualquier tarea técnica. Si el usuario solo quiere hablar o preguntar cosas generales, responde de forma conversacional. Si el usuario pide explícitamente crear, modificar o analizar una aplicación/código de forma técnica, responde con la palabra clave [START_MISSION] seguida de una breve confirmación.'},
            {'Nodo': 'Discovery', 'Prompt': 'Construye el mapa de verdad. Extrae definiciones y tipos vía LSP/Vectores. Genera un context_bundle: {"files": []}'},
            {'Nodo': 'Planning', 'Prompt': 'Genera un implementation_plan: {"steps": []} atómico. No generes código, solo lógica secuencial.'},
            {'Nodo': 'Execution', 'Prompt': 'Manipula archivos reales. Genera código y usa las herramientas de escritura.'},
            {'Nodo': 'Diagnostics', 'Prompt': 'Linter virtual. Busca errores. Responde con "Zero Errors" si todo está bien o explica el "Error".'},
            {'Nodo': 'Testing', 'Prompt': 'Simula ejecución de tests. Responde con "Éxito" o "Fallo".'},
            {'Nodo': 'Critique', 'Prompt': 'Auditoría de calidad. Responde con "Aprobado" o "Veto".'}
        ]

    def set_up(self):
        import vertexai
        from langchain_google_vertexai import ChatVertexAI
        from langgraph.graph import StateGraph, END
        from langgraph.checkpoint.memory import MemorySaver
        from langchain_core.messages import SystemMessage

        if hasattr(self, 'credentials'):
            vertexai.init(project=self.project, location=self.location, credentials=self.credentials)
        else:
            vertexai.init(project=self.project, location=self.location)

        # Modelo con parámetros avanzados
        self.llm = ChatVertexAI(
            model_name=self.model_name,
            temperature=0.1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=4096
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
                    context = state.get('context_bundle', {})
                    plan = state.get('implementation_plan', {})

                    artifact_prompt = f"\n\n[CONTEXTO ACTUAL]: {json.dumps(context)}\n[PLAN ACTUAL]: {json.dumps(plan)}"
                    messages = [SystemMessage(content=p + artifact_prompt)] + state['messages']

                    response = self.llm_with_tools.invoke(messages)

                    # Lógica de extracción de artefactos (Basada en etiquetas en el prompt)
                    updates = {"messages": [response]}
                    content = response.content
                    if "context_bundle:" in content.lower():
                        try:
                            # Ejemplo simplificado de extracción de JSON del texto
                            start = content.lower().find("context_bundle:") + len("context_bundle:")
                            end = content.find("}", start) + 1
                            updates["context_bundle"] = json.loads(content[start:end])
                        except: pass
                    if "implementation_plan:" in content.lower():
                        try:
                            start = content.lower().find("implementation_plan:") + len("implementation_plan:")
                            end = content.find("}", start) + 1
                            updates["implementation_plan"] = json.loads(content[start:end])
                        except: pass

                    return updates
                return _node

            workflow.add_node(node_name, make_node_func(node_prompt, node_name))

        workflow.set_entry_point("Architect")

        def router_architect(state):
            last_msg = state['messages'][-1].content.upper()
            if "[START_MISSION]" in last_msg:
                return "Discovery"
            return END
        workflow.add_conditional_edges("Architect", router_architect)

        workflow.add_edge("Discovery", "Planning")
        workflow.add_edge("Planning", "Execution")
        workflow.add_edge("Execution", "Diagnostics")
        def router_diagnostics(state):
            last_msg = state['messages'][-1].content.lower()
            if "error" in last_msg: return "Execution"
            if "zero errors" in last_msg: return "Testing"
            return END
        workflow.add_conditional_edges("Diagnostics", router_diagnostics)
        def router_testing(state):
            last_msg = state['messages'][-1].content.lower()
            if "fallo" in last_msg: return "Planning"
            return "Critique"
        workflow.add_conditional_edges("Testing", router_testing)
        def router_critique(state):
            last_msg = state['messages'][-1].content.lower()
            if "veto" in last_msg: return "Planning"
            if "aprobado" in last_msg: return END
            return END
        workflow.add_conditional_edges("Critique", router_critique)

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
        interrupt_tools = ['write_local_file']
        memory = MemorySaver() # Usar persistencia en memoria para el template

        if interrupt_tools:
            self.graph = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
        else:
            self.graph = workflow.compile(checkpointer=memory)

    @error_wrapper
    def query(self, config: RunnableConfig = None, **kwargs):
        return dumpd(self.graph.invoke(**kwargs))

    @error_wrapper
    async def async_query(self, config: RunnableConfig = None, **kwargs):
        result = await self.graph.ainvoke(**kwargs)
        return dumpd(result)

    @error_wrapper
    def get_state(self, config: RunnableConfig = None):
        return self.graph.get_state(config=config)._asdict()

    @error_wrapper
    def get_state_history(self, config: RunnableConfig = None) -> Iterable:
        for state_snapshot in self.graph.get_state_history(config=config):
            yield state_snapshot._asdict()

    def register_operations(self):
        return {
            "": ['query', 'async_query', 'get_state'],
            "stream": ['get_state_history'],
        }

    def set_credentials_json(self, json_path: str):
        from google.oauth2 import service_account
        self.credentials = service_account.Credentials.from_service_account_file(json_path)

"""
EJEMPLOS DE USO LOCAL (Basados en README.md):

# 1. Instanciar el agente
agent = RobustMultiAgent(
    project="your-project-id",
    location="us-central1"
)
agent.set_up()

# 2. Probar consulta síncrona
response = agent.query(messages=[{"role": "user", "content": "Hola, ¿qué puedes hacer?"}])
print(response)
"""
