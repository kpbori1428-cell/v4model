# Hoja de Ruta: Escalabilidad de la Suite de Agentes Vertex AI

Este documento detalla los pasos necesarios para transformar los generadores individuales en una plataforma de desarrollo integral y profesional.

## 🟢 Fase 1: Unificación y Biblioteca de Habilidades (COMPLETO ✅)
*Objetivo: Consolidar la experiencia de usuario en un solo Dashboard.*

- [x] **Fusión de Interfaces**: Aplicación raíz en `app.py` que utiliza `st.tabs` para separar el "Constructor de Agentes" del "Diseñador de Herramientas".
- [x] **Persistencia Local**: Sistema de guardado en `tools.json` para que las herramientas creadas se mantengan entre reinicios de la aplicación.
- [x] **Inyección Dinámica**: El constructor de agentes lee la biblioteca local y ofrece un multiselect para inyectar automáticamente el código fuente de las herramientas.
- [x] **Gestión de Versiones**: Capacidad de guardar y cargar diferentes configuraciones del agente (modelos, capacidades, herramientas seleccionadas) mediante `agents.json`.

## 🟡 Fase 2: Entorno de Pruebas (Playground) Integrado (COMPLETO ✅)
*Objetivo: Validar el comportamiento del agente sin salir de la herramienta.*

- [x] **Simulador de Grafo**: Función `instantiate_agent_mock` que simula la instanciación y respuesta del agente en memoria.
- [x] **Interfaz de Chat**: Implementación de `st.chat_message` y `st.chat_input` para un bucle de interacción fluido.
- [x] **Consola de Debug**: Panel expandible que muestra la configuración interna y trazas de ejecución mockeadas.
- [x] **Carga de Contexto**: Funcionalidad para limpiar el chat o cargar historiales previos desde archivos JSON.

## 🟠 Fase 3: Diseño Granular y Multi-Agente (COMPLETO ✅)
*Objetivo: Control total sobre el comportamiento y estado del agente.*

- [x] **Prompt Studio**: Interfaz para definir instrucciones de sistema y variables de contexto.
- [x] **Control de Hiperparámetros**: Configuración granular de temperatura, top_p, top_k y tokens.
- [x] **Esquema de Estado Personalizado**: Definición dinámica de variables en `TypedDict` para persistencia en el grafo.
- [x] **Refactorización a StateGraph**: Generación de código manual con nodos y aristas en lugar de plantillas preconfiguradas.
- [x] **Evolución Autónoma (Meta-Agentes)**: Capacidad de los agentes para auto-registrar herramientas (`register_skill`) y diseñar nuevos agentes especializados (`define_agent`) de forma persistente.
- [x] **Handoff de Artefactos Estrictos**: Implementación de `context_bundle` y `implementation_plan` como ciudadanos de primera clase en el estado del grafo, garantizando integridad entre nodos.

## 🔴 Fase 4: Despliegue Automatizado (Auto-Deploy)
*Objetivo: Eliminar la fricción entre el desarrollo local y la nube.*

- [ ] **Integración con Google Cloud SDK**: Configurar llamadas para autenticar al usuario directamente desde la app.
- [ ] **Containerización Automática**: Generar el archivo `Dockerfile` y `requirements.txt` necesarios para el despliegue.
- [ ] **Botón de Despliegue**:
    - [ ] Envío a **Artifact Registry**.
    - [ ] Despliegue en **Cloud Run** o **Vertex AI Agent Engine**.
- [ ] **Monitor de Estado**: Mostrar una barra de progreso del despliegue y entregar la URL final del endpoint al terminar.

---

## 📋 Resumen de Acción Inmediata
1. **Validación de Prioridades**: Revisar este documento y elegir la siguiente fase (Recomendado: Fase 4 - Auto-Deploy).
2. **Setup de Dependencias**: Añadir `google-cloud-build` y `google-cloud-run` para el despliegue.
3. **Pruebas de Desktop**: Asegurar que las configuraciones granulares se guarden correctamente en la versión de Electron.
