import streamlit as st
import pandas as pd

def generate_tool_code(name, description, params, body):
    # Formatear argumentos
    args_str = ", ".join([f"{p['Nombre']}: {p['Tipo']}" for p in params])

    # Formatear docstring (Google Style)
    docstring = f'    """{description}\n\n    Args:\n'
    for p in params:
        docstring += f"        {p['Nombre']}: {p['Descripción']}\n"
    docstring += '    """'

    # Formatear cuerpo (indentar)
    body_lines = body.strip().split('\n')
    indented_body = "\n".join([f"    {line}" for line in body_lines])

    code = f"""def {name}({args_str}):
{docstring}
{indented_body}
"""
    return code

def main():
    st.set_page_config(page_title="Generador de Habilidades (Tools)", layout="wide")
    st.title("🛠️ Generador de Habilidades (Tools)")
    st.markdown("Diseña tus propias habilidades para que tu agente pueda ejecutar acciones personalizadas.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Configuración de la Habilidad")
        tool_name = st.text_input("Nombre de la Función", value="consultar_inventario")
        tool_desc = st.text_area("Descripción (¿Qué hace y cuándo usarla?)",
                                "Consulta la cantidad disponible de un producto específico en la base de datos central.")

        st.subheader("Parámetros de Entrada")
        df_params = pd.DataFrame([
            {"Nombre": "producto_id", "Tipo": "str", "Descripción": "ID alfanumérico del producto"},
            {"Nombre": "sucursal", "Tipo": "str", "Descripción": "Nombre de la sucursal (opcional)"}
        ])
        params_data = st.data_editor(df_params, num_rows="dynamic", use_container_width=True)

        st.subheader("Lógica de la Función (Python)")
        tool_body = st.text_area("Cuerpo de la función (sin def ni indentación inicial)",
                                "# Ejemplo:\n# resultado = mi_base_de_datos.query(producto_id)\nreturn f'Hay 15 unidades del producto {producto_id}.'",
                                height=200)

    with col2:
        st.header("Código Python Generado")

        # Convertir dataframe a lista de dicts para el generador
        params_list = params_data.to_dict('records')

        if tool_name:
            generated_code = generate_tool_code(tool_name, tool_desc, params_list, tool_body)
            st.code(generated_code, language="python")

            st.download_button(
                label="Descargar herramienta (.py)",
                data=generated_code,
                file_name=f"{tool_name}.py",
                mime="text/x-python"
            )
        else:
            st.warning("Escribe un nombre para la función para generar el código.")

    st.divider()
    st.info("💡 Una vez descargado el archivo, puedes importar esta función en tu código principal y poner su nombre en el generador de agentes.")

if __name__ == "__main__":
    main()
