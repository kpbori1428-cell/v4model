Desarrollar un agente personalizado

Las plantillas de agentes de Vertex AI Agent Engine se definen como clases de Python. En los siguientes pasos se muestra cómo crear una plantilla personalizada para crear instancias de agentes que se puedan desplegar en Vertex AI:

Ejemplo básico
 Respuestas graduales
 Registrar métodos personalizados
 Proporcionar anotaciones de tipo
 Enviar trazas a Cloud Trace
 Trabajar con variables de entorno
 Integración con Secret Manager
 Gestión de credenciales
 Gestión de errores
Ejemplo básico
Por poner un ejemplo básico, la siguiente clase de Python es una plantilla para crear instancias de agentes que se pueden desplegar en Vertex AI (puedes asignar a la variable CLASS_NAME un valor como MyAgent):



from typing import Callable, Sequence

class CLASS_NAME:
    def __init__(
        self,
        model: str,
        tools: Sequence[Callable],
        project: str,
        location: str,
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.location = location

    def set_up(self):
        import vertexai
        from langchain_google_vertexai import ChatVertexAI
        from langgraph.prebuilt import create_react_agent

        vertexai.init(project=self.project, location=self.location)

        model = ChatVertexAI(model_name=self.model_name)
        self.graph = create_react_agent(model, tools=self.tools)

    def query(self, **kwargs):
        return self.graph.invoke(**kwargs)
Consideraciones sobre la implementación
Al escribir tu clase de Python, es importante que incluyas los tres métodos siguientes:

__init__():
Usa este método solo para los parámetros de configuración del agente. Por ejemplo, puedes usar este método para recoger los parámetros del modelo y los atributos de seguridad como argumentos de entrada de tus usuarios. También puedes usar este método para recoger parámetros como el ID de proyecto, la región, las credenciales de la aplicación y las claves de API.
El constructor devuelve un objeto que debe poder serializarse para poder desplegarse en Vertex AI Agent Engine. Por lo tanto, debes inicializar los clientes de servicio y establecer conexiones con las bases de datos en el método .set_up en lugar del método __init__.
Este método es opcional. Si no se especifica, Vertex AI usa el constructor de Python predeterminado de la clase.
set_up():
Debes usar este método para definir la lógica de inicialización del agente. Por ejemplo, puedes usar este método para establecer conexiones con bases de datos o servicios dependientes, importar paquetes dependientes o precalcular datos que se usen para responder a consultas.
Este método es opcional. Si no se especifica, Vertex AI asume que el agente no necesita llamar a un método .set_up antes de responder a las consultas de los usuarios.
query() / stream_query():
Usa query() para devolver la respuesta completa como un único resultado.
Usa stream_query() para devolver la respuesta en fragmentos a medida que esté disponible, lo que permite disfrutar de una experiencia de streaming. El método stream_query debe devolver un objeto iterable (por ejemplo, un generador) para habilitar la transmisión.
Puedes implementar ambos métodos si quieres admitir interacciones de respuesta única y de streaming con tu agente.
Debes asignar a este método una cadena de documentación clara que defina lo que hace, documente sus atributos y proporcione anotaciones de tipo para sus entradas. Evita los argumentos variables en los métodos query y stream_query.
Instanciar el agente de forma local
Puedes crear una instancia local de tu agente con el siguiente código:



agent = CLASS_NAME(
    model=model,  # Required.
    tools=[get_exchange_rate],  # Optional.
    project="PROJECT_ID",
    location="LOCATION",
)
agent.set_up()
Probar el método query
Puedes probar el agente enviando consultas a la instancia local:



response = agent.query(
    input="What is the exchange rate from US dollars to Swedish currency?"
)

print(response)
La respuesta es un diccionario similar al siguiente:



{"input": "What is the exchange rate from US dollars to Swedish currency?",
 # ...
 "output": "For 1 US dollar you will get 10.7345 Swedish Krona."}
Consultar de forma asíncrona
Para responder a las consultas de forma asíncrona, puedes definir un método (como async_query) que devuelva una corrutina de Python. Por ejemplo, la siguiente plantilla amplía el ejemplo básico para responder de forma asíncrona y se puede desplegar en Vertex AI:



class AsyncAgent(CLASS_NAME):

    async def async_query(self, **kwargs):
        from langchain.load.dump import dumpd

        for chunk in self.graph.ainvoke(**kwargs):
            yield dumpd(chunk)

agent = AsyncAgent(
    model=model,                # Required.
    tools=[get_exchange_rate],  # Optional.
    project="PROJECT_ID",
    location="LOCATION",
)
agent.set_up()
Probar el método async_query
Puedes probar el agente de forma local llamando al método async_query. Por ejemplo:



response = await agent.async_query(
    input="What is the exchange rate from US dollars to Swedish Krona today?"
)
print(response)
La respuesta es un diccionario similar al siguiente:



{"input": "What is the exchange rate from US dollars to Swedish currency?",
 # ...
 "output": "For 1 US dollar you will get 10.7345 Swedish Krona."}
Respuestas en streaming
Para transmitir respuestas a las consultas, puedes definir un método llamado stream_query que genere respuestas. Por ejemplo, la siguiente plantilla amplía el ejemplo básico para transmitir respuestas y se puede desplegar en Vertex AI:



from typing import Iterable

class StreamingAgent(CLASS_NAME):

    def stream_query(self, **kwargs) -> Iterable:
        from langchain.load.dump import dumpd

        for chunk in self.graph.stream(**kwargs):
            yield dumpd(chunk)

agent = StreamingAgent(
    model=model,                # Required.
    tools=[get_exchange_rate],  # Optional.
    project="PROJECT_ID",
    location="LOCATION",
)
agent.set_up()
A continuación, te indicamos algunos aspectos importantes que debes tener en cuenta al usar la API de streaming:

Tiempo de espera máximo: el tiempo de espera máximo para las respuestas de streaming es de 10 minutos. Si tu agente necesita más tiempo de procesamiento, considera la posibilidad de dividir la tarea en partes más pequeñas.
Modelos y cadenas de streaming: la interfaz Runnable de LangChain admite el streaming, por lo que puedes transmitir respuestas no solo de agentes, sino también de modelos y cadenas.
Compatibilidad con LangChain: ten en cuenta que, por el momento, no se admiten métodos asíncronos como el método astream_event de LangChain.
Limitar la generación de contenido: si tienes problemas de contrapresión (es decir, el productor genera datos más rápido de lo que el consumidor puede procesarlos), debes limitar la velocidad de generación de contenido. Esto puede ayudar a evitar desbordamientos de búfer y garantizar una experiencia de streaming fluida.
Probar el método stream_query
Puedes probar la consulta de streaming de forma local llamando al método stream_query e iterando los resultados. Veamos un ejemplo:



import pprint

for chunk in agent.stream_query(
    input="What is the exchange rate from US dollars to Swedish currency?"
):
    # Use pprint with depth=1 for a more concise, high-level view of the
    # streamed output.
    # To see the full content of the chunk, use:
    # print(chunk)
    pprint.pprint(chunk, depth=1)
Este código imprime cada fragmento de la respuesta a medida que se genera. La salida podría ser similar a esta:



{'actions': [...], 'messages': [...]}
{'messages': [...], 'steps': [...]}
{'messages': [...],
 'output': 'The exchange rate from US dollars to Swedish currency is 1 USD to '
           '10.5751 SEK. \n'}
En este ejemplo, cada fragmento contiene información diferente sobre la respuesta, como las acciones realizadas por el agente, los mensajes intercambiados y el resultado final.

Respuestas de streaming asíncronas
Para transmitir respuestas de forma asíncrona, puedes definir un método (por ejemplo, async_stream_query) que devuelva un generador asíncrono. Por ejemplo, la siguiente plantilla amplía el ejemplo básico para transmitir respuestas de forma asíncrona y se puede desplegar en Vertex AI:



class AsyncStreamingAgent(CLASS_NAME):

    async def async_stream_query(self, **kwargs):
        from langchain.load.dump import dumpd

        for chunk in self.graph.astream(**kwargs):
            yield dumpd(chunk)

agent = AsyncStreamingAgent(
    model=model,                # Required.
    tools=[get_exchange_rate],  # Optional.
    project="PROJECT_ID",
    location="LOCATION",
)
agent.set_up()
Probar el método async_stream_query
Al igual que con el código para probar las consultas de streaming, puedes probar el agente de forma local llamando al método async_stream_query e iterando los resultados. Veamos un ejemplo:



import pprint

async for chunk in agent.async_stream_query(
    input="What is the exchange rate from US dollars to Swedish currency?"
):
    # Use pprint with depth=1 for a more concise, high-level view of the
    # streamed output.
    # To see the full content of the chunk, use:
    # print(chunk)
    pprint.pprint(chunk, depth=1)
Este código imprime cada fragmento de la respuesta a medida que se genera. La salida podría ser similar a esta:



{'actions': [...], 'messages': [...]}
{'messages': [...], 'steps': [...]}
{'messages': [...],
 'output': 'The exchange rate from US dollars to Swedish currency is 1 USD to '
           '10.5751 SEK. \n'}
Registrar métodos personalizados
De forma predeterminada, los métodos query y stream_query se registran como operaciones en el agente implementado. Puedes anular el comportamiento predeterminado y definir el conjunto de operaciones que se van a registrar mediante el método register_operations. Las operaciones se pueden registrar en modo de ejecución estándar (representado por una cadena vacía "") o de streaming ("stream").

Para registrar varias operaciones, puedes definir un método llamado register_operations que enumere los métodos que se pondrán a disposición de los usuarios cuando se implemente el agente. En el siguiente ejemplo de código, el método register_operations provocará que el agente implementado registre query y get_state como operaciones que se ejecutan de forma síncrona, y stream_query y get_state_history como operaciones que transmiten las respuestas:



from typing import Iterable

class CustomAgent(StreamingAgent):

    def get_state(self) -> dict: # new synchronous method
        return self.graph.get_state(**kwargs)._asdict()

    def get_state_history(self) -> Iterable: # new streaming operation
        for state_snapshot in self.graph.get_state_history(**kwargs):
            yield state_snapshot._asdict()

    def register_operations(self):
        return {
            # The list of synchronous operations to be registered
            "": ["query", "get_state"],
            # The list of streaming operations to be registered
            "stream": ["stream_query", "get_state_history"],
        }
Nota: No es necesario registrar métodos para operaciones estándar y de streaming. Por ejemplo, para admitir solo operaciones estándar, puedes devolver {"": ["query", "get_state"]} en el método register_operations sin especificar una lista de métodos correspondiente para "stream".
Puedes probar los métodos personalizados llamándolos directamente en la instancia local del agente, de forma similar a como probarías los métodos query y stream_query.

Proporcionar anotaciones de tipo
Puedes usar anotaciones de tipo para especificar los tipos de entrada y salida esperados de los métodos de tu agente. Cuando se implementa el agente, solo se admiten tipos serializables en JSON en la entrada y la salida de las operaciones compatibles con el agente. Los esquemas de las entradas y salidas se pueden anotar con TypedDict o modelos de Pydantic.

En el siguiente ejemplo, anotamos la entrada como TypedDict y convertimos la salida sin procesar de .get_state (que es un NamedTuple) en un diccionario serializable mediante su método ._asdict():



from typing import Any, Dict, TypedDict

# schemas.py
class RunnableConfig(TypedDict, total=False):
    metadata: Dict[str, Any]
    configurable: Dict[str, Any]

# agents.py
class AnnotatedAgent(CLASS_NAME):

    def get_state(self, config: RunnableConfig) -> dict:
        return self.graph.get_state(config=config)._asdict()

    def register_operations(self):
        return {"": ["query", "get_state"]}
Enviar trazas a Cloud Trace
Para enviar trazas a Cloud Trace con bibliotecas de instrumentación compatibles con OpenTelemetry, puedes importarlas e inicializarlas en el método .set_up. En el caso de los frameworks de agentes comunes, puedes usar la integración de Open Telemetry Google Cloud junto con un framework de instrumentación como OpenInference u OpenLLMetry.

Por ejemplo, la siguiente plantilla es una modificación del ejemplo básico para exportar trazas a Cloud Trace:

OpenInference
OpenLLMetry
Primero, instala el paquete necesario con pip ejecutando



pip install openinference-instrumentation-langchain==0.1.34
A continuación, importa e inicializa el instrumentador:



from typing import Callable, Sequence

class CLASS_NAME:
    def __init__(
        self,
        model: str,
        tools: Sequence[Callable],
        project: str,
        location: str,
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.location = location

    def set_up(self):
        # The additional code required for tracing instrumentation.
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
        LangChainInstrumentor().instrument()
        # end of additional code required

        import vertexai
        from langchain_google_vertexai import ChatVertexAI
        from langgraph.prebuilt import create_react_agent

        vertexai.init(project=self.project, location=self.location)

        model = ChatVertexAI(model_name=self.model_name)
        self.graph = create_react_agent(model, tools=self.tools)

    def query(self, **kwargs):
        return self.graph.invoke(**kwargs)
Trabajar con variables de entorno
Para definir variables de entorno, asegúrate de que estén disponibles a través de os.environ durante el desarrollo y sigue las instrucciones de Definir variables de entorno al implementar el agente.

Integración con Secret Manager
Para integrarlo con Secret Manager, sigue estos pasos:

Instala la biblioteca de cliente ejecutando



pip install google-cloud-secret-manager
Sigue las instrucciones de Asignar roles a un agente implementado para asignar el rol "Permiso para acceder a los recursos de Secret Manager" (roles/secretmanager.secretAccessor) a la cuenta de servicio mediante la consola Google Cloud .

Importa e inicializa el cliente en el método .set_up y obtén el secreto correspondiente cuando sea necesario. Por ejemplo, la siguiente plantilla es una modificación del ejemplo básico para usar una clave de API de ChatAnthropic que se ha almacenado en Secret Manager:



from typing import Callable, Sequence

class CLASS_NAME:
    def __init__(
        self,
        model: str,
        tools: Sequence[Callable],
        project: str,
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.secret_id = secret_id # <- new

    def set_up(self):
        from google.cloud import secretmanager
        from langchain_anthropic import ChatAnthropic
        from langgraph.prebuilt import create_react_agent

        # Get the API Key from Secret Manager here.
        self.secret_manager_client = secretmanager.SecretManagerServiceClient()
        secret_version = self.secret_manager_client.access_secret_version(request={
            "name": "projects/PROJECT_ID/secrets/SECRET_ID/versions/SECRET_VERSION",
        })
        # Use the API Key from Secret Manager here.
        model = ChatAnthropic(
            model_name=self.model_name,
            model_kwargs={"api_key": secret_version.payload.data.decode()},  # <- new
        )
        self.graph = create_react_agent(model, tools=self.tools)

    def query(self, **kwargs):
        return self.graph.invoke(**kwargs)
Gestionar credenciales
Cuando se implementa el agente, es posible que tenga que gestionar diferentes tipos de credenciales:

Credenciales predeterminadas de la aplicación (ADC), que suelen proceder de cuentas de servicio.
OAuth, que suele producirse en las cuentas de usuario.
Proveedores de identidades para las credenciales de cuentas externas (federación de identidades de cargas de trabajo).
Credenciales predeterminadas de la aplicación


import google.auth

credentials, project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
Se puede usar en el código de la siguiente manera:



from typing import Callable, Sequence

class CLASS_NAME:
    def __init__(
        self,
        model: str = "meta/llama3-405b-instruct-maas",
        tools: Sequence[Callable],
        location: str,
        project: str,
    ):
        self.model_name = model
        self.tools = tools
        self.project = project
        self.endpoint = f"https://{location}-aiplatform.googleapis.com"
        self.base_url = f'{self.endpoint}/v1beta1/projects/{project}/locations/{location}/endpoints/openapi'

    def query(self, **kwargs):
        import google.auth
        from langchain_openai import ChatOpenAI
        from langgraph.prebuilt import create_react_agent

        # Note: the credential lives for 1 hour by default.
        # After expiration, it must be refreshed.
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(google.auth.transport.requests.Request())

        model = ChatOpenAI(
            model=self.model_name,
            base_url=self.base_url,
            api_key=creds.token,  # Use the token from the credentials here.
        )
        graph = create_react_agent(model, tools=self.tools)
        return graph.invoke(**kwargs)
Para obtener más información, consulta el artículo Cómo funcionan las credenciales predeterminadas de la aplicación.

OAuth
Las credenciales de usuario se suelen obtener mediante OAuth 2.0.

Si tienes un token de acceso (por ejemplo, de oauthlib), puedes crear una instancia de google.oauth2.credentials.Credentials. Además, si obtienes un token de actualización, también puedes especificar el token de actualización y el URI del token para que las credenciales se actualicen automáticamente:



credentials = google.oauth2.credentials.Credentials(
    token="ACCESS_TOKEN",
    refresh_token="REFRESH_TOKEN",  # Optional
    token_uri="TOKEN_URI",          # E.g. "https://oauth2.googleapis.com/token"
    client_id="CLIENT_ID",          # Optional
    client_secret="CLIENT_SECRET"   # Optional
)
Aquí, TOKEN_URI, CLIENT_ID y CLIENT_SECRET se basan en Crear una credencial de cliente de OAuth.

Si no tienes un token de acceso, puedes usar google_auth_oauthlib.flow para realizar el flujo de concesión de autorización de OAuth 2.0 y obtener una instancia de google.oauth2.credentials.Credentials correspondiente:



from google.cloud import secretmanager
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Get the client config from Secret Manager here.
secret_manager_client = secretmanager.SecretManagerServiceClient()
secret_version = client.access_secret_version(request={
    "name": "projects/PROJECT_ID/secrets/SECRET_ID/versions/SECRET_VERSION",
})
client_config = json.loads(secret_version.payload.data.decode())

# Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
flow = InstalledAppFlow.from_client_config(
    client_config,
    scopes=['https://www.googleapis.com/auth/cloud-platform'],
    state="OAUTH_FLOW_STATE"  # from flow.authorization_url(...)
)

# You can get the credentials from the flow object.
credentials: google.oauth2.credentials.Credentials = flow.credentials

# After obtaining the credentials, you can then authorize API requests on behalf
# of the given user or service account. For example, to authorize API requests
# to vertexai services, you'll specify it in vertexai.init(credentials=)
import vertexai

vertexai.init(
    project="PROJECT_ID",
    location="LOCATION",
    credentials=credentials, # specify the credentials here
)
Para obtener más información, consulta la documentación del módulo google_auth_oauthlib.flow.

Proveedor de identidades
Si quieres autenticar a los usuarios con correo electrónico y contraseña, número de teléfono, proveedores sociales como Google, Facebook o GitHub, o un mecanismo de autenticación personalizado, puedes usar Identity Platform o Firebase Authentication, o cualquier proveedor de identidades que admita OpenID Connect (OIDC).

Para obtener más información, consulta el artículo Acceder a recursos desde un proveedor de identidades OIDC.

Gestionar errores
Para asegurarte de que los errores de la API se devuelvan en un formato JSON estructurado, te recomendamos que implementes la gestión de errores en el código de tu agente mediante un bloque try...except, que se puede abstraer en un decorador.

Aunque Vertex AI Agent Engine puede gestionar varios códigos de estado internamente, Python no tiene una forma estandarizada de representar errores con códigos de estado HTTP asociados en todos los tipos de excepciones. Intentar asignar todas las excepciones de Python posibles a los estados HTTP del servicio subyacente sería complejo y difícil de mantener.

Un enfoque más escalable consiste en detectar explícitamente las excepciones pertinentes en los métodos de tu agente o mediante el uso de un decorador reutilizable como error_wrapper. Después, puede asociar los códigos de estado adecuados (por ejemplo, añadiendo los atributos code y error a las excepciones personalizadas o gestionando las excepciones estándar de forma específica) y dar formato al error como un diccionario JSON para el valor devuelto. Para ello, solo tienes que hacer un cambio mínimo en el código de los propios métodos del agente, que a menudo consiste en añadir el decorador.

A continuación, se muestra un ejemplo de cómo puedes implementar la gestión de errores en tu agente:



from functools import wraps
import json

def error_wrapper(func):
    @wraps(func)  # Preserve original function metadata
    def wrapper(*args, **kwargs):
        try:
            # Execute the original function with its arguments
            return func(*args, **kwargs)
        except Exception as err:
            error_code = getattr(err, 'code')
            error_message = getattr(err, 'error')

            # Construct the error response dictionary
            error_response = {
                "error": {
                    "code": error_code,
                    "message": f"'{func.__name__}': {error_message}"
                }
            }
            # Return the Python dictionary directly.
            return error_response

    return wrapper

# Example exception
class SessionNotFoundError(Exception):
    def __init__(self, session_id, message="Session not found"):
        self.code = 404
        self.error = f"{message}: {session_id}"
        super().__init__(self.error)

# Example Agent Class
class MyAgent:
    @error_wrapper
    def get_session(self, session_id: str):
        # Simulate the condition where the session isn't found
        raise SessionNotFoundError(session_id=session_id)


# Example Usage: Session Not Found
agent = MyAgent()
error_result = agent.get_session(session_id="nonexistent_session_123")
print(json.dumps(error_result, indent=2))
El código anterior genera el siguiente resultado: json { "error": { "code": 404, "message": "Invocation error in 'get_session': Session not found: nonexistent_session_123" } }

---

## 🤖 Vertex AI Agent Suite (Desktop & Web)

Esta suite proporciona una interfaz visual profesional para el desarrollo acelerado de agentes de Vertex AI.

### 🌟 Características
- **Constructor de Agentes**: Configuración visual de modelos Gemini, capacidades (sync/async/streaming) e integraciones (Cloud Trace, Secret Manager).
- **Diseñador de Herramientas**: Interfaz para crear, probar y gestionar una biblioteca de "habilidades" (funciones Python) que se inyectan automáticamente en el código del agente.
- **Generación de Código**: Descarga instantánea de plantillas de agentes listas para producción siguiendo las mejores prácticas de Google Cloud.

### 🛠️ Requisitos
- **Python 3.10+**: `pip install streamlit pandas langchain-google-vertexai langgraph opentelemetry-api opentelemetry-sdk`
- **Node.js 18+** (Solo para la versión de escritorio): `npm install`

### 🚀 Cómo empezar

#### Versión Web (Streamlit)
Ideal para desarrollo rápido en el navegador:
```bash
streamlit run app.py
```

#### Versión de Escritorio (Electron)
Para una experiencia de aplicación nativa:
1. Instala las dependencias de Node:
   ```bash
   npm install
   ```
2. Inicia la aplicación:
   ```bash
   npm start
   ```

### 📦 Estructura del Proyecto
- `app.py`: Lógica unificada de la interfaz visual y generador de código.
- `main.js`: Punto de entrada de Electron (Main Process).
- `launcher.py`: Script de arranque optimizado para el entorno de escritorio.
- `package.json`: Configuración de dependencias de Electron y scripts de empaquetado.
