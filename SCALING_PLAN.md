# Hoja de Ruta: Escalabilidad de la Suite de Agentes Vertex AI

Este documento detalla los pasos necesarios para transformar los generadores individuales en una plataforma de desarrollo integral y profesional.

## 🟢 Fase 1: Unificación y Biblioteca de Habilidades
*Objetivo: Consolidar la experiencia de usuario en un solo Dashboard.*

- [ ] **Fusión de Interfaces**: Crear una aplicación raíz en `app.py` que utilice pestañas (`st.tabs`) para separar el "Constructor de Agentes" del "Diseñador de Herramientas".
- [ ] **Persistencia Local**: Implementar un sistema de guardado (JSON o base de datos ligera) para que las herramientas creadas se guarden en una biblioteca.
- [ ] **Inyección Dinámica**: Permitir que el constructor de agentes lea la biblioteca local y ofrezca un multiselect para añadir herramientas al agente sin copiar nombres manualmente.
- [ ] **Gestión de Versiones**: Capacidad de guardar diferentes versiones de un mismo agente.

## 🟡 Fase 2: Entorno de Pruebas (Playground) Integrado
*Objetivo: Validar el comportamiento del agente sin salir de la herramienta.*

- [ ] **Simulador de Grafo**: Crear una función que instancie el agente generado en la memoria de la aplicación.
- [ ] **Interfaz de Chat**: Implementar `st.chat_message` y `st.chat_input` para interactuar con el agente en tiempo real.
- [ ] **Consola de Debug**: Mostrar en un panel lateral qué herramientas está invocando el agente y qué errores (si los hay) están ocurriendo durante la prueba.
- [ ] **Carga de Contexto**: Poder "subir" un historial de chat previo para probar la memoria del agente.

## 🟠 Fase 3: Orquestación Multi-Agente (LangGraph Avanzado)
*Objetivo: Crear flujos de trabajo donde varios agentes colaboran.*

- [ ] **Diseñador de Roles**: Interfaz para definir múltiples agentes dentro de un mismo proyecto (ej. Supervisor vs. Ejecutor).
- [ ] **Mapeo de Transferencia**: Definir visualmente las reglas de "paso de estafeta" entre agentes.
- [ ] **Generación de Código de Grafo**: Actualizar el motor de generación para que soporte grafos complejos de LangGraph con múltiples nodos de agentes.
- [ ] **Visualización del Flujo**: (Opcional) Usar diagramas de flujo para mostrar la jerarquía y conexión entre agentes.

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
1. **Validación de Prioridades**: Revisar este documento y elegir la fase inicial (Recomendado: Fase 1).
2. **Setup de Dependencias**: Añadir `google-cloud-build` y `google-cloud-run` para futuras fases.
3. **Refactorización**: Comenzar el proceso de unificación de `tool_creator.py` dentro de `app.py`.
