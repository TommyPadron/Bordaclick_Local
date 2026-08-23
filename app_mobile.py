# ==============================================================================
# BORDACLICK - APLICACIÓN MÓVIL (ENTORNO DEV)
# Archivo Principal: app_mobile.py
# Descripción: Interfaz web en Streamlit para toma de pedidos y panel de administración.
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. IMPORTACIÓN DE LIBRERÍAS Y MÓDULOS DEL PROYECTO
# ------------------------------------------------------------------------------
import streamlit as st
import pandas as pd
from datetime import date, timedelta

# Funciones de la base de datos (SQLite)
try:
    from db_handler import (
        crear_bd,
        obtener_colegios,
        guardar_colegio,
        eliminar_colegio,
        obtener_tipos_prenda,
        guardar_tipo_prenda,
        eliminar_tipo_prenda,
        obtener_tallas,
        guardar_talla,
        eliminar_talla,
        obtener_marcas,
        guardar_marca,
        eliminar_marca,
        obtener_colores,
        guardar_color,
        eliminar_color,
        obtener_zonas_delivery,
        guardar_zona_delivery,
        eliminar_zona_delivery,
        obtener_costo_delivery,
        obtener_parametro,
        guardar_parametro,
        obtener_precio_colegio,
        guardar_orden,
        guardar_detalle,
        obtener_orden_por_id,
        obtener_detalle_orden,
        enviar_pdf_por_correo,
        enviar_confirmacion_solicitud,
        obtener_ordenes,
        registrar_pago,
        obtener_historico_pagos,
        actualizar_status_orden,
        enviar_notificacion_estado,
        eliminar_orden
    )
except ImportError as e:
    st.error(f"Error crítico al importar 'db_handler': {e}")

# Importación segura de herramientas de PDF y Excel con control de excepciones
try:
    from pdf_tools import (
        generar_pdf_orden,
        generar_excel_orden,
        generar_excel_historico
    )
    HERRAMIENTAS_REPORTES_DISPONIBLES = True
except ImportError:
    HERRAMIENTAS_REPORTES_DISPONIBLES = False

# ------------------------------------------------------------------------------
# 2. INICIALIZACIÓN DE BASE DE DATOS Y CONFIGURACIÓN DE PÁGINA
# ------------------------------------------------------------------------------
try:
    crear_bd()
except Exception:
    pass

st.set_page_config(
    page_title="Bordaclick Clientes (DEV)",
    page_icon="🧵",
    layout="centered"
)

# ------------------------------------------------------------------------------
# 3. CONTROL DE ACCESO (ADMINISTRADOR) Y BARRA LATERAL
# ------------------------------------------------------------------------------
clave_admin = st.sidebar.text_input("Clave Administrador", type="password")

opciones_menu = ["📝 Nueva Solicitud"]

# Lectura segura de la clave desde st.secrets con respaldo local de desarrollo
try:
    clave_correcta = st.secrets["admin"]["password"]
except Exception:
    clave_correcta = "BordaAdmin2026*"

if clave_admin == clave_correcta:
    opciones_menu.extend([
        "📋 Consultas",
        "📊 Reportes",
        "⚙️ Configuración",
        "🏫 Colegios",
        "🚚 Delivery",
        "📦 Prendas",
        "🏷️ Marcas",
        "📏 Tallas",
        "🎨 Colores",
        "💾 Respaldo"
    ])

pagina = st.sidebar.selectbox("Menú", opciones_menu)

# ------------------------------------------------------------------------------
# 4. MEMORIA DE SESIÓN (SESSION STATE)
# ------------------------------------------------------------------------------
if "paso" not in st.session_state:
    st.session_state.paso = 1

if "solicitud_enviada" not in st.session_state:
    st.session_state.solicitud_enviada = False

if "colegios_agregados" not in st.session_state:
    st.session_state.colegios_agregados = []

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# ------------------------------------------------------------------------------
# 5. ENCABEZADO PRINCIPAL DE LA APLICACIÓN
# ------------------------------------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    try:
        st.image("Logo Bordaclick.JPG", width=80)
    except Exception:
        st.write("🧵")

with col2:
    st.title("🧵 Bordaclick")
    st.caption("Solicitud desde Celular (Entorno DEV)")

st.divider()

# ==============================================================================
# MÓDULO 1: FORMULARIO CLIENTE (NUEVA SOLICITUD EN 4 PASOS)
# ==============================================================================
if pagina == "📝 Nueva Solicitud":

    # --------------------------------------------------------------------------
    # PASO 1: DATOS DEL CLIENTE
    # --------------------------------------------------------------------------
    if st.session_state.paso == 1:
        st.progress(25)
        st.subheader("👤 Datos de Contacto")
        st.caption("Por favor, ingresa tus datos para gestionar tu solicitud de bordado.")

        with st.container(border=True):
            nombre = st.text_input("Nombre y Apellido *", value=st.session_state.get("nombre", ""), placeholder="Ej. Ana Mendoza")
            telefono = st.text_input("Teléfono de Contacto (WhatsApp) *", value=st.session_state.get("telefono", ""), placeholder="Ej. 04121234567")
            correo = st.text_input("Correo Electrónico *", value=st.session_state.get("correo", ""), placeholder="ejemplo@correo.com")

        if st.button("Continuar a Selección de Prendas ➡️", use_container_width=True):
            if not nombre.strip():
                st.error("Debe ingresar el nombre.")
            elif not telefono.strip() or len(telefono.strip()) < 10:
                st.error("Debe ingresar un teléfono válido (mínimo 10 dígitos).")
            elif "@" not in correo or "." not in correo:
                st.error("Debe ingresar un correo electrónico válido.")
            else:
                st.session_state.nombre = nombre
                st.session_state.telefono = telefono
                st.session_state.correo = correo
                st.session_state.paso = 2
                st.rerun()

    # --------------------------------------------------------------------------
    # PASO 2: SELECCIÓN DE COLEGIO Y PRENDAS
    # --------------------------------------------------------------------------
    elif st.session_state.paso == 2:
        st.progress(50)
        st.subheader("🏫 Colegio y Prendas")

        es_admin = (clave_admin == "BordaAdmin2026*")

        df_col = obtener_colegios()
        lista_colegios = ["Seleccione un colegio..."] + (df_col["nombre"].dropna().tolist() if not df_col.empty else [])

        df_p = obtener_tipos_prenda()
        lista_tipos_prenda = ["Seleccione una prenda..."] + (df_p["nombre"].dropna().tolist() if not df_p.empty else [])

        df_t = obtener_tallas()
        lista_tallas = ["Seleccione una talla..."] + (df_t["nombre"].dropna().tolist() if not df_t.empty else [])

        df_m = obtener_marcas()
        lista_marcas = ["Seleccione una marca..."] + (df_m["nombre"].dropna().tolist() if not df_m.empty else [])

        df_c = obtener_colores()
        lista_colores = ["Seleccione un color..."] + (df_c["nombre"].dropna().tolist() if not df_c.empty else [])

        v = st.session_state.form_version

        with st.container(border=True):
            col_sel, col_btn = st.columns([4, 1] if es_admin else [1, 0.01])
            with col_sel:
                colegio = st.selectbox("Seleccione el Colegio *", lista_colegios, key=f"colegio_sel_{v}")
            
            if es_admin:
                with col_btn:
                    st.write("")
                    with st.popover("➕"):
                        st.markdown("**Nuevo Colegio**")
                        nuevo_col_nom = st.text_input("Nombre", key=f"quick_col_nom_{v}")
                        nuevo_col_prec = st.number_input("Precio Bordado", min_value=0.0, step=0.5, key=f"quick_col_prec_{v}")
                        if st.button("Guardar", key=f"btn_quick_col_{v}"):
                            if nuevo_col_nom.strip():
                                guardar_colegio(nuevo_col_nom.strip(), nuevo_col_prec)
                                st.success("¡Colegio agregado!")
                                st.rerun()

            if colegio != "Seleccione un colegio..." and not df_col.empty:
                precio_base = obtener_precio_colegio(colegio)
                st.info(f"💡 Precio base de bordado para **{colegio}**: **${precio_base:.2f}** por prenda.")

        st.subheader("👕 Detalle de la Prenda")

        with st.container(border=True):
            c_p1, c_p2 = st.columns([4, 1] if es_admin else [1, 0.01])
            with c_p1:
                tipo_prenda = st.selectbox("Tipo de Prenda *", lista_tipos_prenda, key=f"tipo_prenda_{v}")
            if es_admin:
                with c_p2:
                    st.write("")
                    with st.popover("➕"):
                        nuevo_p = st.text_input("Nueva Prenda", key=f"quick_p_{v}")
                        if st.button("Guardar", key=f"btn_quick_p_{v}") and nuevo_p.strip():
                            guardar_tipo_prenda(nuevo_p.strip())
                            st.rerun()

            col_a, col_b = st.columns(2)
            with col_a:
                c_t1, c_t2 = st.columns([3, 1] if es_admin else [1, 0.01])
                with c_t1:
                    talla = st.selectbox("Talla *", lista_tallas, key=f"talla_{v}")
                if es_admin:
                    with c_t2:
                        st.write("")
                        with st.popover("➕"):
                            nueva_t = st.text_input("Nueva Talla", key=f"quick_t_{v}")
                            if st.button("Guardar", key=f"btn_quick_t_{v}") and nueva_t.strip():
                                guardar_talla(nueva_t.strip())
                                st.rerun()

                c_c1, c_c2 = st.columns([3, 1] if es_admin else [1, 0.01])
                with c_c1:
                    color = st.selectbox("Color *", lista_colores, key=f"color_{v}")
                if es_admin:
                    with c_c2:
                        st.write("")
                        with st.popover("➕"):
                            nuevo_c = st.text_input("Nuevo Color", key=f"quick_c_{v}")
                            if st.button("Guardar", key=f"btn_quick_c_{v}") and nuevo_c.strip():
                                guardar_color(nuevo_c.strip())
                                st.rerun()

            with col_b:
                c_m1, c_m2 = st.columns([3, 1] if es_admin else [1, 0.01])
                with c_m1:
                    marca = st.selectbox("Marca *", lista_marcas, key=f"marca_{v}")
                if es_admin:
                    with c_m2:
                        st.write("")
                        with st.popover("➕"):
                            nueva_m = st.text_input("Nueva Marca", key=f"quick_m_{v}")
                            if st.button("Guardar", key=f"btn_quick_m_{v}") and nueva_m.strip():
                                guardar_marca(nueva_m.strip())
                                st.rerun()

                cantidad = st.number_input("Cantidad *", min_value=1, value=1, key=f"cantidad_{v}")

        if "prendas_actuales" not in st.session_state:
            st.session_state.prendas_actuales = []

        if st.button("➕ Agregar Prenda a este Colegio", use_container_width=True):
            if colegio == "Seleccione un colegio...":
                st.error("Debe seleccionar un colegio.")
            elif tipo_prenda == "Seleccione una prenda...":
                st.error("Debe seleccionar un tipo de prenda.")
            elif talla == "Seleccione una talla...":
                st.error("Debe seleccionar una talla.")
            elif marca == "Seleccione una marca...":
                st.error("Debe seleccionar una marca.")
            elif color == "Seleccione un color...":
                st.error("Debe seleccionar un color.")
            else:
                st.session_state.prendas_actuales.append({
                    "tipo": tipo_prenda,
                    "talla": talla,
                    "marca": marca,
                    "color": color,
                    "cantidad": cantidad
                })
                st.rerun()

        st.divider()
        st.subheader("📋 Prendas del colegio en turno")

        if not st.session_state.prendas_actuales:
            st.info("Aún no has agregado prendas para el colegio seleccionado arriba.")
        else:
            for i, prenda in enumerate(st.session_state.prendas_actuales):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.success(f"👕 {prenda['tipo']} | 📏 {prenda['talla']} | 🏷️ {prenda['marca']} | 🎨 {prenda['color']} | 🔢 Cantidad: {prenda['cantidad']}")
                with c2:
                    if st.button("🗑️", key=f"borrar_prenda_{i}"):
                        st.session_state.prendas_actuales.pop(i)
                        st.rerun()

        if st.button("💾 Guardar Colegio y sus Prendas", use_container_width=True):
            if not st.session_state.prendas_actuales:
                st.error("Debe agregar al menos una prenda antes de guardar el colegio.")
            else:
                if any(c["colegio"] == colegio for c in st.session_state.colegios_agregados):
                    st.error("Ese colegio ya fue agregado a la lista.")
                else:
                    st.session_state.colegios_agregados.append({
                        "colegio": colegio,
                        "prendas": st.session_state.prendas_actuales.copy()
                    })
                    st.session_state.prendas_actuales = []
                    st.session_state.form_version += 1
                    st.success("✅ Colegio y prendas guardados en tu solicitud.")
                    st.rerun()

        st.divider()

        st.subheader("🏫 Lista General de Colegios Agregados")
        if not st.session_state.colegios_agregados:
            st.info("Aún no hay colegios listos en tu solicitud.")
        else:
            for idx_col, colegio_data in enumerate(st.session_state.colegios_agregados):
                with st.container(border=True):
                    c_lbl, c_btn = st.columns([5, 1])
                    with c_lbl:
                        st.markdown(f"### 🏫 {colegio_data['colegio']}")
                    with c_btn:
                        if st.button("🗑️", key=f"del_col_agregado_{idx_col}"):
                            st.session_state.colegios_agregados.pop(idx_col)
                            st.rerun()

                    for prenda in colegio_data["prendas"]:
                        st.write(f"• **{prenda['tipo']}** ({prenda['talla']}) - {prenda['marca']} / {prenda['color']} x **{prenda['cantidad']} unid.**")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Volver a Datos", use_container_width=True):
                st.session_state.paso = 1
                st.rerun()
        with col2:
            if st.button("Continuar a Personalización ➡️", use_container_width=True):
                if not st.session_state.colegios_agregados:
                    st.error("Debe guardar al menos un colegio con prendas.")
                else:
                    st.session_state.paso = 3
                    st.rerun()

    # --------------------------------------------------------------------------
    # PASO 3: PERSONALIZACIÓN Y DELIVERY
    # --------------------------------------------------------------------------
    elif st.session_state.paso == 3:
        st.progress(75)
        st.subheader("🧵 Personalización y Entrega")

        df_del = obtener_zonas_delivery()
        lista_zonas = []

        if not df_del.empty:
            col_zona = None
            for col in ["zona", "nombre", "zona_delivery"]:
                if col in df_del.columns:
                    col_zona = col
                    break
            
            if not col_zona and len(df_del.columns) > 0:
                col_zona = df_del.columns[0]

            if col_zona:
                lista_zonas = df_del[col_zona].dropna().tolist()

        with st.container(border=True):
            st.markdown("### 🎨 Opciones de Bordado")
            tipo_logo = st.selectbox(
                "Tipo de Logo / Arte *",
                ["Bordado Estándar del Colegio", "Personalizado / Diseñado por Cliente"],
                key="input_tipo_logo"
            )

            bordar_nombre = st.radio(
                "¿Desea bordar nombre personalizado en las prendas?",
                ["No", "Sí"],
                horizontal=True,
                key="input_bordar_nombre"
            )

            nombre_bordado = ""
            cantidad_nombre = 0
            if bordar_nombre == "Sí":
                nombre_bordado = st.text_input("Nombre / Texto a bordar", placeholder="Ej. Juan Pérez", key="input_texto_nombre")
                cantidad_nombre = st.number_input("¿En cuántas prendas se aplicará el nombre?", min_value=1, value=1, key="input_cant_nombre")

        with st.container(border=True):
            st.markdown("### 🚚 Método de Entrega")
            delivery = st.radio(
                "¿Cómo desea recibir su pedido?",
                ["Retiro en Tienda", "Envío a Domicilio (Delivery)"],
                horizontal=True,
                key="input_delivery"
            )

            zona_delivery = "N/A"
            costo_delivery = 0.0

            if delivery == "Envío a Domicilio (Delivery)":
                if lista_zonas:
                    zona_delivery = st.selectbox("Seleccione su zona de delivery *", lista_zonas, key="input_zona")
                    costo_delivery = float(obtener_costo_delivery(zona_delivery) or 0.0)
                    st.info(f"🛵 Costo de envío a **{zona_delivery}**: **${costo_delivery:.2f}**")
                else:
                    st.warning("No hay zonas de delivery configuradas en el sistema.")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Volver a Prendas", use_container_width=True):
                st.session_state.paso = 2
                st.rerun()
        with col2:
            if st.button("Continuar al Resumen ➡️", use_container_width=True):
                if bordar_nombre == "Sí" and not nombre_bordado.strip():
                    st.error("Por favor, ingrese el nombre que desea bordar.")
                else:
                    st.session_state.tipo_logo = tipo_logo
                    st.session_state.bordar_nombre = bordar_nombre
                    st.session_state.nombre_bordado = nombre_bordado
                    st.session_state.cantidad_nombre = cantidad_nombre
                    st.session_state.delivery = "Sí" if delivery == "Envío a Domicilio (Delivery)" else "No"
                    st.session_state.zona_delivery = zona_delivery
                    st.session_state.costo_delivery = costo_delivery
                    
                    st.session_state.paso = 4
                    st.rerun()

    # --------------------------------------------------------------------------
    # PASO 4: RESUMEN Y CONFIRMACIÓN DE PEDIDO
    # --------------------------------------------------------------------------
    elif st.session_state.paso == 4:
        st.progress(100)
        st.subheader("📋 Resumen Final de tu Solicitud")

        with st.container(border=True):
            st.markdown(f"### 👤 {st.session_state.nombre}")
            st.write(f"📞 **Teléfono:** {st.session_state.telefono}")
            st.write(f"📧 **Correo:** {st.session_state.correo}")

        with st.container(border=True):
            st.markdown("### 🧵 Detalles de Personalización")
            st.write(f"• **Tipo de Logo:** {st.session_state.tipo_logo}")
            st.write(f"• **Bordado de Nombre:** {st.session_state.bordar_nombre}")
            if st.session_state.bordar_nombre == "Sí":
                st.write(f"• **Detalle:** {st.session_state.nombre_bordado}")
                st.write(f"• **Prendas con nombre:** {st.session_state.cantidad_nombre}")

        dias_produccion = int(obtener_parametro("dias_produccion") or 3)
        fecha_entrega = date.today() + timedelta(days=dias_produccion)

        with st.container(border=True):
            st.markdown("### 💰 Presupuesto Estimado")
            st.info(f"📅 **Fecha estimada de entrega:** {fecha_entrega.strftime('%d/%m/%Y')}")

            subtotal_bordado = 0.0
            for colegio_data in st.session_state.colegios_agregados:
                colegio_nombre = colegio_data["colegio"]
                cantidad_colegio = sum(p["cantidad"] for p in colegio_data["prendas"])
                precio_colegio = obtener_precio_colegio(colegio_nombre)

                if cantidad_colegio >= 6:
                    precio_colegio = max(0.0, precio_colegio - 0.50)

                subtotal_colegio = cantidad_colegio * precio_colegio
                subtotal_bordado += subtotal_colegio

                st.write(f"🏫 **{colegio_nombre}** {'🎉 *(Descuento de $0.50 aplicado por 6+ prendas)*' if cantidad_colegio >= 6 else ''}")
                st.write(f"   ↳ {cantidad_colegio} prendas x ${precio_colegio:.2f} = **${subtotal_colegio:.2f}**")

            precio_nombre = float(obtener_parametro("precio_nombre") or 0)
            subtotal_nombres = (st.session_state.cantidad_nombre * precio_nombre) if st.session_state.bordar_nombre == "Sí" else 0.0

            if st.session_state.bordar_nombre == "Sí":
                st.write(f"🔤 **Nombres:** {st.session_state.cantidad_nombre} x ${precio_nombre:.2f} = **${subtotal_nombres:.2f}**")

            st.write(f"🚚 **Delivery ({st.session_state.zona_delivery if st.session_state.delivery == 'Sí' else 'Retiro en Tienda'}):** **${st.session_state.costo_delivery:.2f}**")
            
            total_estimado = subtotal_bordado + subtotal_nombres + st.session_state.costo_delivery
            st.divider()
            st.metric(label="Monto Total Estimado ($ USD)", value=f"${total_estimado:.2f}")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Modificar Datos", use_container_width=True):
                st.session_state.paso = 3
                st.rerun()
        with col2:
            if st.button("✅ Confirmar y Enviar Solicitud", key="confirmar_solicitud_mobile", use_container_width=True, disabled=st.session_state.solicitud_enviada):
                colegio_orden = "Múltiples Colegios" if len(st.session_state.colegios_agregados) > 1 else st.session_state.colegios_agregados[0]["colegio"]
                cantidad_total = sum(p["cantidad"] for c in st.session_state.colegios_agregados for p in c["prendas"])

                orden_id = guardar_orden(
                    st.session_state.nombre,
                    st.session_state.telefono,
                    st.session_state.correo,
                    colegio_orden,
                    cantidad_total,
                    st.session_state.tipo_logo,
                    st.session_state.nombre_bordado,
                    st.session_state.cantidad_nombre,
                    st.session_state.delivery,
                    st.session_state.zona_delivery,
                    fecha_entrega,
                    0,
                    subtotal_bordado,
                    subtotal_nombres,
                    st.session_state.costo_delivery,
                    0,
                    total_estimado,
                    "Recibido"
                )

                for colegio_data in st.session_state.colegios_agregados:
                    for prenda in colegio_data["prendas"]:
                        guardar_detalle(
                            orden_id,
                            colegio_data["colegio"],
                            prenda["tipo"],
                            prenda["talla"],
                            prenda["marca"],
                            prenda["color"],
                            int(prenda["cantidad"])
                        )

                try:
                    enviar_confirmacion_solicitud(
                        st.session_state.correo,
                        st.session_state.nombre,
                        orden_id,
                        fecha_entrega
                    )
                except Exception as e:
                    st.error(f"Error enviando correo: {e}")

                st.session_state.solicitud_enviada = True
                st.session_state.ultimo_pedido = orden_id
                st.rerun()

        if st.session_state.solicitud_enviada:
            st.balloons()
            st.success(f"🎉 ¡Solicitud #{st.session_state.ultimo_pedido:04d} registrada con éxito!")
            st.info("Te hemos enviado un correo electrónico con la confirmación.")

            if st.button("➕ Crear otra Solicitud", key="nueva_solicitud_mobile", use_container_width=True):
                st.session_state.clear()
                st.rerun()

# ==============================================================================
# MÓDULO 2: CONSULTA DE ÓRDENES Y GESTIÓN ADMINISTRATIVA
# ==============================================================================
elif pagina == "📋 Consultas":
    st.title("📋 Consulta de Órdenes")
    df_ordenes = obtener_ordenes()

    if df_ordenes.empty:
        st.info("ℹ️ No hay órdenes registradas en la base de datos.")
    else:
        if HERRAMIENTAS_REPORTES_DISPONIBLES:
            try:
                excel_hist_file = generar_excel_historico(df_ordenes)
                with open(excel_hist_file, "rb") as f:
                    st.download_button(
                        "📊 Descargar Histórico General de Órdenes (Excel)",
                        f,
                        file_name=excel_hist_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="btn_descarga_historico_top"
                    )
            except Exception:
                pass

        st.divider()

        df_consulta = df_ordenes[["id", "nombre", "colegio", "status", "fecha_entrega", "saldo_pendiente", "fecha_pago"]].copy()
        df_consulta.columns = ["ID", "Cliente", "Colegio", "Estado", "Entrega", "Saldo", "Último Pago"]
        st.dataframe(df_consulta, use_container_width=True)

        pedido_id = st.selectbox("Seleccione un pedido", df_ordenes["id"].tolist())
        st.info(f"📦 Pedido seleccionado: #{pedido_id:04d}")

        pedido = obtener_orden_por_id(pedido_id).iloc[0]
        st.write(f"👤 {pedido['nombre']} | 📞 {pedido['telefono']} | 📧 {pedido['correo']}")

        detalle_orden = obtener_detalle_orden(pedido_id)
        with st.expander("👕 Prendas", expanded=True):
            if not detalle_orden.empty:
                st.dataframe(detalle_orden, use_container_width=True)
                
                col_cantidad = next((col for col in detalle_orden.columns if col.lower() == "cantidad"), None)
                
                if col_cantidad:
                    total_prendas_pedido = int(pd.to_numeric(detalle_orden[col_cantidad], errors="coerce").fillna(0).sum())
                    st.metric(
                        label="Total de prendas en este pedido",
                        value=f"{total_prendas_pedido} unidades"
                    )
                else:
                    st.warning("No se encontró la columna de cantidad en el detalle del pedido.")
            else:
                st.info("No hay prendas registradas para este pedido.")

        with st.expander("💰 Pagos y Tasa de Cambio (USD / Bs.)"):
            saldo = float(pedido.get("saldo_pendiente", 0))
            st.metric("Saldo Pendiente ($ USD)", f"${saldo:.2f}")

            tasa_actual = float(obtener_parametro("tasa_cambio") or 0.0)
            tasa_input = st.number_input("Tasa de Cambio (Bs / $)", min_value=0.0, value=tasa_actual, step=0.10, format="%.2f", key=f"tasa_pago_{pedido_id}")
            
            if tasa_input > 0 and saldo > 0:
                saldo_bs = saldo * tasa_input
                st.info(f"💡 **Saldo equivalente en Bolívares:** {saldo_bs:,.2f} Bs.")

            if pedido.get("fecha_pago"):
                st.caption(f"📅 Fecha del último pago registrado: {pedido.get('fecha_pago')}")

            if saldo <= 0:
                st.success("💳 Estado Pago: ✅ Pagado")
            else:
                st.warning(f"💳 Estado Pago: 🔴 Pendiente (${saldo:.2f})")

            monto_pago = st.number_input("Monto recibido ($ USD)", min_value=0.0, step=1.0, key=f"monto_in_{pedido_id}")
            
            if monto_pago > 0 and tasa_input > 0:
                monto_bs = round(monto_pago * tasa_input, 2)
                st.write(f"💵 **Equivalente del pago:** {monto_bs:,.2f} Bs.")

            if st.button("💾 Registrar Pago", key=f"reg_pago_{pedido_id}"):
                if monto_pago > saldo and saldo > 0:
                    st.error("❌ El pago excede el saldo pendiente.")
                elif monto_pago <= 0:
                    st.error("❌ Monto inválido.")
                else:
                    registrar_pago(pedido_id, monto_pago, tasa_input)
                    st.success("✅ Pago y registro en Bolívares guardados correctamente.")
                    st.rerun()

            df_hist_pagos = obtener_historico_pagos(pedido_id)
            if not df_hist_pagos.empty:
                st.subheader("📜 Histórico de Pagos en Bolívares")
                st.dataframe(df_hist_pagos[["monto_usd", "tasa_cambio", "monto_bs", "fecha"]], use_container_width=True)

        with st.expander("📄 Documentos"):
            tasa_doc = st.number_input("Tasa para Comprobante PDF (Opcional)", min_value=0.0, value=float(obtener_parametro("tasa_cambio") or 0.0), step=0.10, key=f"tasa_pdf_{pedido_id}")
            
            if st.button("📄 Generar PDF"):
                if HERRAMIENTAS_REPORTES_DISPONIBLES:
                    pdf_file = generar_pdf_orden(pedido, detalle_orden, tasa_doc)
                    with open(pdf_file, "rb") as f:
                        st.download_button("📥 Descargar PDF", f, file_name=pdf_file, mime="application/pdf")
                else:
                    st.error("El módulo de generación de PDFs no está disponible.")

            if st.button("📊 Generar Excel Pedido"):
                if HERRAMIENTAS_REPORTES_DISPONIBLES:
                    excel_file = generar_excel_orden(pedido, detalle_orden)
                    with open(excel_file, "rb") as f:
                        st.download_button("📥 Descargar Excel Pedido", f, file_name=excel_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.error("El módulo de generación de Excel no está disponible.")

        with st.expander("📧 Comunicaciones"):
            if st.button("📧 Reenviar Correo"):
                pdf_file = "comprobante.pdf"
                if HERRAMIENTAS_REPORTES_DISPONIBLES:
                    pdf_file = generar_pdf_orden(pedido, detalle_orden)
                enviar_pdf_por_correo(pedido["correo"], pedido["nombre"], pedido["id"], pedido["fecha_entrega"], pdf_file)
                st.success("✅ Correo reenviado")

        with st.expander("🏭 Producción"):
            nuevo_estado = st.selectbox("Cambiar estado", ["Recibido", "En Producción", "Listo para Entrega", "Anulado"])
            if st.button("🔄 Actualizar Estado"):
                actualizar_status_orden(pedido_id, nuevo_estado)
                enviar_notificacion_estado(pedido["correo"], pedido["nombre"], pedido["id"], pedido["fecha_entrega"], nuevo_estado, pedido["delivery"])
                st.success("✅ Estado actualizado correctamente")
                st.rerun()

        with st.expander("🗑️ Zona de Peligro / Eliminar Pedido"):
            st.error("⚠️ **Atención:** Esta acción es permanente. Se eliminará la orden, sus ítems y sus pagos registrados.")
            
            confirmar = st.checkbox(f"Estoy seguro de que deseo eliminar la Orden #{pedido_id:04d}", key=f"chk_confirm_{pedido_id}")
            
            if st.button("🗑️ Eliminar Pedido Definitivamente", key=f"btn_del_{pedido_id}"):
                if confirmar:
                    if eliminar_orden(pedido_id):
                        st.success(f"✅ La Orden #{pedido_id:04d} ha sido eliminada correctamente.")
                        st.rerun()
                    else:
                        st.error("❌ Ocurrió un error al intentar borrar el pedido de la base de datos.")
                else:
                    st.warning("⚠️ Marca la casilla de verificación anterior para confirmar la eliminación.")

# ------------------------------------------------------------------------------
# SECCIONES ADMINISTRATIVAS: GESTIÓN DE CATÁLOGOS Y TABLAS##
# ------------------------------------------------------------------------------

elif pagina == "⚙️ Configuración":
    st.title("⚙️ Configuración General")
    
    try:
        precio_actual = obtener_parametro("precio_bordado_nombre") if 'obtener_parametro' in globals() else 2.0
        dias_actual = int(obtener_parametro("dias_produccion") if 'obtener_parametro' in globals() else 3)
    except Exception as e:
        st.error(f"Error al conectar con la base de datos para cargar parámetros: {e}")
        precio_actual = 2.0
        dias_actual = 3

    with st.container(border=True):
        precio_bordado_nombre = st.number_input(
            "Precio Bordado de Nombre",
            min_value=0.0,
            step=0.5,
            value=float(precio_actual if precio_actual is not None else 2.0),
            key="cfg_precio_nombre"
        )
        
        dias_produccion = st.number_input(
            "Días de Producción",
            min_value=1,
            step=1,
            value=int(dias_actual if dias_actual is not None else 3),
            key="cfg_dias_produccion"
        )
        
        if st.button("💾 Guardar Configuración", use_container_width=True, key="btn_save_config"):
            try:
                guardar_parametro("precio_bordado_nombre", str(precio_bordado_nombre))
                guardar_parametro("dias_produccion", str(dias_produccion))
                st.success("✅ Configuración guardada con éxito.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo guardar la configuración: {e}")

elif pagina == "🏫 Colegios":
    st.title("🏫 Gestión de Colegios")
    
    with st.container(border=True):
        nombre_colegio = st.text_input("Nombre del Colegio", key="admin_nom_colegio")
        precio_colegio = st.number_input("Precio Bordado Colegio ($ USD)", min_value=0.0, step=0.50, key="admin_precio_colegio")
        
        if st.button("💾 Guardar Colegio", use_container_width=True, key="btn_save_colegio"):
            if nombre_colegio.strip():
                guardar_colegio(nombre_colegio.strip(), precio_colegio)
                st.success(f"✅ Colegio '{nombre_colegio}' registrado con éxito.")
                st.rerun()
            else:
                st.warning("⚠️ El nombre del colegio no puede estar vacío.")

    st.divider()
    st.subheader("📋 Registros Actuales")
    
    df_colegios = obtener_colegios() if 'obtener_colegios' in globals() else pd.DataFrame()
    
    if not df_colegios.empty:
        st.dataframe(df_colegios, use_container_width=True)
        
        with st.expander("🗑️ Eliminar un Colegio"):
            opciones_col = {f"{row['nombre']} ($ {row['precio_bordado']})": row['id'] for _, row in df_colegios.iterrows()}
            seleccion_col = st.selectbox("Seleccione el colegio a eliminar:", list(opciones_col.keys()), key="del_col_select")
            
            if st.button("🗑️ Eliminar Colegio", key="btn_del_col"):
                eliminar_colegio(opciones_col[seleccion_col])
                st.success("✅ Colegio eliminado con éxito.")
                st.rerun()
    else:
        st.info("No hay colegios registrados o la tabla está vacía.")

elif pagina == "🚚 Delivery":
    st.title("🚚 Gestión de Zonas de Delivery")
    
    with st.container(border=True):
        zona = st.text_input("Nombre de la Zona / Sector", key="admin_zona_deliv")
        precio_delivery = st.number_input("Costo de Envío ($ USD)", min_value=0.0, step=0.50, key="admin_precio_deliv")
        if st.button("💾 Guardar Zona", use_container_width=True, key="btn_save_deliv"):
            if zona.strip():
                guardar_zona_delivery(zona, precio_delivery) if 'guardar_zona_delivery' in globals() else None
                st.success(f"✅ Zona '{zona}' guardada.")
                st.rerun()
            else:
                st.warning("⚠️ Ingrese el nombre de la zona.")

    st.divider()
    st.subheader("📋 Registros Actuales")
    df_delivery = obtener_zonas_delivery() if 'obtener_zonas_delivery' in globals() else pd.DataFrame()
    if not df_delivery.empty:
        st.dataframe(df_delivery, use_container_width=True)
        with st.expander("🗑️ Eliminar una Zona"):
            opciones = {f"{row.get('nombre', 'Zona')} (ID: {row.get('id', 0)})": row.get('id', 0) for _, row in df_delivery.iterrows()}
            seleccion = st.selectbox("Seleccione la zona a eliminar:", list(opciones.keys()), key="del_deliv_select")
            if st.button("🗑️ Eliminar Zona", key="btn_del_deliv"):
                if 'eliminar_zona_delivery' in globals():
                    eliminar_zona_delivery(opciones[seleccion])
                    st.success("✅ Zona eliminada con éxito.")
                    st.rerun()
    else:
        st.info("No hay zonas de delivery registradas.")

elif pagina == "📦 Prendas":
    st.title("📦 Gestión de Tipos de Prenda")
    
    with st.container(border=True):
        tipo_prenda = st.text_input("Nombre del Tipo de Prenda", key="admin_tipo_prenda")
        if st.button("💾 Guardar Tipo de Prenda", use_container_width=True, key="btn_save_prenda"):
            if tipo_prenda.strip():
                guardar_tipo_prenda(tipo_prenda) if 'guardar_tipo_prenda' in globals() else None
                st.success(f"✅ Prenda '{tipo_prenda}' guardada.")
                st.rerun()
            else:
                st.warning("⚠️ Ingrese el nombre de la prenda.")

    st.divider()
    st.subheader("📋 Registros Actuales")
    df_prendas = obtener_tipos_prenda() if 'obtener_tipos_prenda' in globals() else pd.DataFrame()
    if not df_prendas.empty:
        st.dataframe(df_prendas, use_container_width=True)
        with st.expander("🗑️ Eliminar un Tipo de Prenda"):
            opciones = {f"{row.get('nombre', 'Prenda')} (ID: {row.get('id', 0)})": row.get('id', 0) for _, row in df_prendas.iterrows()}
            seleccion = st.selectbox("Seleccione la prenda a eliminar:", list(opciones.keys()), key="del_prenda_select")
            if st.button("🗑️ Eliminar Prenda", key="btn_del_prenda"):
                if 'eliminar_tipo_prenda' in globals():
                    eliminar_tipo_prenda(opciones[seleccion])
                    st.success("✅ Prenda eliminada con éxito.")
                    st.rerun()
    else:
        st.info("No hay tipos de prenda registrados.")

elif pagina == "🏷️ Marcas":
    st.title("🏷️ Gestión de Marcas")
    
    with st.container(border=True):
        marca = st.text_input("Nombre de la Marca", key="admin_marca")
        if st.button("💾 Guardar Marca", use_container_width=True, key="btn_save_marca"):
            if marca.strip():
                guardar_marca(marca) if 'guardar_marca' in globals() else None
                st.success(f"✅ Marca '{marca}' guardada.")
                st.rerun()
            else:
                st.warning("⚠️ Ingrese el nombre de la marca.")

    st.divider()
    st.subheader("📋 Registros Actuales")
    df_marcas = obtener_marcas() if 'obtener_marcas' in globals() else pd.DataFrame()
    if not df_marcas.empty:
        st.dataframe(df_marcas, use_container_width=True)
        with st.expander("🗑️ Eliminar una Marca"):
            opciones = {f"{row.get('nombre', 'Marca')} (ID: {row.get('id', 0)})": row.get('id', 0) for _, row in df_marcas.iterrows()}
            seleccion = st.selectbox("Seleccione la marca a eliminar:", list(opciones.keys()), key="del_marca_select")
            if st.button("🗑️ Eliminar Marca", key="btn_del_marca"):
                if 'eliminar_marca' in globals():
                    eliminar_marca(opciones[seleccion])
                    st.success("✅ Marca eliminada con éxito.")
                    st.rerun()
    else:
        st.info("No hay marcas registradas.")

elif pagina == "📏 Tallas":
    st.title("📏 Gestión de Tallas")
    
    with st.container(border=True):
        talla = st.text_input("Identificador de Talla", key="admin_talla")
        if st.button("💾 Guardar Talla", use_container_width=True, key="btn_save_talla"):
            if talla.strip():
                guardar_talla(talla) if 'guardar_talla' in globals() else None
                st.success(f"✅ Talla '{talla}' guardada.")
                st.rerun()
            else:
                st.warning("⚠️ Ingrese una talla.")

    st.divider()
    st.subheader("📋 Registros Actuales")
    df_tallas = obtener_tallas() if 'obtener_tallas' in globals() else pd.DataFrame()
    if not df_tallas.empty:
        st.dataframe(df_tallas, use_container_width=True)
        with st.expander("🗑️ Eliminar una Talla"):
            opciones = {f"{row.get('nombre', 'Talla')} (ID: {row.get('id', 0)})": row.get('id', 0) for _, row in df_tallas.iterrows()}
            seleccion = st.selectbox("Seleccione la talla a eliminar:", list(opciones.keys()), key="del_talla_select")
            if st.button("🗑️ Eliminar Talla", key="btn_del_talla"):
                if 'eliminar_talla' in globals():
                    eliminar_talla(opciones[seleccion])
                    st.success("✅ Talla eliminada con éxito.")
                    st.rerun()
    else:
        st.info("No hay tallas registradas.")

elif pagina == "🎨 Colores":
    st.title("🎨 Gestión de Colores")
    
    with st.container(border=True):
        color = st.text_input("Nombre del Color", key="admin_color")
        if st.button("💾 Guardar Color", use_container_width=True, key="btn_save_color"):
            if color.strip():
                guardar_color(color) if 'guardar_color' in globals() else None
                st.success(f"✅ Color '{color}' guardado.")
                st.rerun()
            else:
                st.warning("⚠️ Ingrese un color.")

    st.divider()
    st.subheader("📋 Registros Actuales")
    df_colores = obtener_colores() if 'obtener_colores' in globals() else pd.DataFrame()
    if not df_colores.empty:
        st.dataframe(df_colores, use_container_width=True)
        with st.expander("🗑️ Eliminar un Color"):
            opciones = {f"{row.get('nombre', 'Color')} (ID: {row.get('id', 0)})": row.get('id', 0) for _, row in df_colores.iterrows()}
            seleccion = st.selectbox("Seleccione el color a eliminar:", list(opciones.keys()), key="del_color_select")
            if st.button("🗑️ Eliminar Color", key="btn_del_color"):
                if 'eliminar_color' in globals():
                    eliminar_color(opciones[seleccion])
                    st.success("✅ Color eliminado con éxito.")
                    st.rerun()
    else:
        st.info("No hay colores registrados.")

elif pagina == "💾 Respaldo":
    st.title("💾 Respaldo de Base de Datos")
    with st.container(border=True):
        try:
            with open("bordaclick_dev.db", "rb") as db_file:
                st.download_button(
                    label="📥 Descargar Base de Datos (bordaclick_dev.db)",
                    data=db_file,
                    file_name="bordaclick_dev_backup.db",
                    mime="application/x-sqlite3",
                    use_container_width=True,
                    key="btn_download_db"
                )
        except Exception as e:
            st.error(f"❌ Error al leer la base de datos: {e}")

elif pagina == "📊 Reportes":
    st.title("📊 Módulo de Reportes y Estadísticas")
    
    df_ordenes_rep = obtener_ordenes()
    
    if df_ordenes_rep.empty:
        st.info("ℹ️ No hay datos suficientes para generar reportes.")
    else:
        with st.container(border=True):
            st.subheader("🔍 Filtros de Reporte Avanzados")
            
            # Primera fila de filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                estados_disponibles = ["Todos"] + df_ordenes_rep["status"].dropna().unique().tolist()
                filtro_estado = st.selectbox("Filtrar por Estado", estados_disponibles)
                
            with col_f2:
                colegios_disponibles = ["Todos"] + df_ordenes_rep["colegio"].dropna().unique().tolist()
                filtro_colegio = st.selectbox("Filtrar por Colegio", colegios_disponibles)
                
            with col_f3:
                filtro_pago = st.selectbox("Estado de Pago", ["Todos", "Pagados (Sin deuda)", "Pendientes por Pagar"])

            # Segunda fila de filtros (Delivery y Nombres Bordados)
            col_f4, col_f5 = st.columns(2)
            with col_f4:
                filtro_delivery = st.selectbox("Tipo de Servicio", ["Todos", "Con Delivery", "Retiro en Tienda / Sin Delivery"])
                
            with col_f5:
                filtro_bordado = st.selectbox("Personalización", ["Todos", "Con Nombres Bordados", "Sin Nombres Bordados"])

        # Aplicación lógica de los filtros sobre el DataFrame
        df_filtrado = df_ordenes_rep.copy()
        
        # 1. Filtro por Estado
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["status"] == filtro_estado]
            
        # 2. Filtro por Colegio
        if filtro_colegio != "Todos":
            df_filtrado = df_filtrado[df_filtrado["colegio"] == filtro_colegio]
            
        # 3. Filtro por Estado de Pago
        if "saldo_pendiente" in df_filtrado.columns:
            if filtro_pago == "Pagados (Sin deuda)":
                df_filtrado = df_filtrado[df_filtrado["saldo_pendiente"] <= 0]
            elif filtro_pago == "Pendientes por Pagar":
                df_filtrado = df_filtrado[df_filtrado["saldo_pendiente"] > 0]
                
        # 4. Filtro por Delivery
        if "delivery" in df_filtrado.columns:
            if filtro_delivery == "Con Delivery":
                df_filtrado = df_filtrado[df_filtrado["delivery"].astype(str).str.lower().isin(["sí", "si", "true", "1", "delivery", "con delivery"])]
            elif filtro_delivery == "Retiro en Tienda / Sin Delivery":
                df_filtrado = df_filtrado[~df_filtrado["delivery"].astype(str).str.lower().isin(["sí", "si", "true", "1", "delivery", "con delivery"])]

        # 5. Filtro estricto por Nombres Bordados (Evita falsos positivos y filtrados masivos)
        col_nombre_bordado = next((c for c in df_filtrado.columns if "nombre" in c.lower() or "bordado" in c.lower()), None)
        
        if col_nombre_bordado:
            valores_limpios = df_filtrado[col_nombre_bordado].astype(str).str.strip().str.lower()
            es_vacio = (
                df_filtrado[col_nombre_bordado].isna() | 
                (valores_limpios == "") | 
                (valores_limpios == "nan") | 
                (valores_limpios == "none") | 
                (valores_limpios == "no") | 
                (valores_limpios == "n/a") |
                (valores_limpios == "-")
            )

            if filtro_bordado == "Con Nombres Bordados":
                df_filtrado = df_filtrado[~es_vacio]
            elif filtro_bordado == "Sin Nombres Bordados":
                df_filtrado = df_filtrado[es_vacio]
        else:
            if filtro_bordado == "Con Nombres Bordados":
                df_filtrado = df_filtrado.iloc[0:0]

        # Métricas actualizadas con base en los filtros aplicados
        st.metric(label="Total de Órdenes Filtradas", value=len(df_filtrado))
        
        total_recaudado = df_filtrado["abono"].sum() if "abono" in df_filtrado.columns else 0.0
        total_pendiente = df_filtrado["saldo_pendiente"].sum() if "saldo_pendiente" in df_filtrado.columns else 0.0
        
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            st.metric(label="💰 Total Abonado Filtrado", value=f"${total_recaudado:.2f}")
        with c_m2:
            st.metric(label="⚠️ Total Pendiente Filtrado", value=f"${total_pendiente:.2f}")
            
        st.divider()
        st.dataframe(df_filtrado, use_container_width=True)