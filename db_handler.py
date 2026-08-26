import streamlit as st
import psycopg2
import pandas as pd
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# def obtener_conexion():
#     """Establece la conexión a PostgreSQL o usa SQLite local si hay problemas de red"""
#     try:
#         # Intentamos conectar directamente usando la URL de Supabase sin pasar por los secretos de Streamlit
#         database_url = "postgresql://postgres.urrbamdurciddpqrewiy:OFoiJDOT8FTJXH6@aws-0-us-east-1.pooler.supabase.co:6543/postgres"
#         return psycopg2.connect(database_url)
#     except Exception as e:
#         st.warning(f"No se pudo conectar a Supabase, usando entorno local. Detalle: {e}")
#         # Aquí puedes retornar tu conexión SQLite anterior si prefieres mantener la app operativa localmente
#         import sqlite3
#         return sqlite3.connect("bordaclick.db")

def obtener_conexion():
    """Establece la conexión a PostgreSQL usando los secretos de Streamlit."""
    database_url = st.secrets["postgres"]["url"]
    return psycopg2.connect(database_url)

def crear_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordenes (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        telefono TEXT,
        correo TEXT,
        colegio TEXT,
        cantidad_total INTEGER,
        tipo_logo TEXT,
        nombre_bordado TEXT,
        cantidad_nombre INTEGER,
        delivery TEXT,
        zona_delivery TEXT,
        fecha_entrega TEXT,
        precio_bordado REAL,
        subtotal_bordado REAL,
        subtotal_nombres REAL,
        delivery_costo REAL,
        abono REAL,
        saldo_pendiente REAL,
        status TEXT,
        fecha_pago TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orden_detalle (
        id SERIAL PRIMARY KEY,
        orden_id INTEGER,
        colegio TEXT,
        tipo_prenda TEXT,
        talla TEXT,
        marca TEXT,
        color TEXT,
        cantidad INTEGER,
        FOREIGN KEY (orden_id) REFERENCES ordenes(id)
    )                   
    """)                   

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion_general (
        parametro TEXT PRIMARY KEY,
        valor REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colegios (
        id SERIAL PRIMARY KEY,
        nombre TEXT UNIQUE,
        precio_bordado REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tipos_prenda (
        id SERIAL PRIMARY KEY,
        nombre TEXT UNIQUE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marcas (
        id SERIAL PRIMARY KEY,
        nombre TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colores (
        id SERIAL PRIMARY KEY,
        nombre TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tallas (
        id SERIAL PRIMARY KEY,
        nombre TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zonas_delivery (
        nombre TEXT PRIMARY KEY,
        costo REAL
    )
    """)    

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_pagos (
        id SERIAL PRIMARY KEY,
        orden_id INTEGER,
        monto_usd REAL,
        tasa_cambio REAL,
        monto_bs REAL,
        fecha TEXT,
        FOREIGN KEY (orden_id) REFERENCES ordenes(id)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def guardar_orden(
    nombre, telefono, correo, colegio, cantidad_total, tipo_logo,
    nombre_bordado, cantidad_nombre, delivery, zona_delivery,
    fecha_entrega, precio_bordado, subtotal_bordado, subtotal_nombres,
    delivery_costo, abono, saldo_pendiente, status
):
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ordenes (
            nombre, telefono, correo, colegio, cantidad_total, tipo_logo,
            nombre_bordado, cantidad_nombre, delivery, zona_delivery, fecha_entrega,
            precio_bordado, subtotal_bordado, subtotal_nombres, delivery_costo,
            abono, saldo_pendiente, status, fecha_pago
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        nombre, telefono, correo, colegio, cantidad_total, tipo_logo,
        nombre_bordado, cantidad_nombre, delivery, zona_delivery, str(fecha_entrega),
        precio_bordado, subtotal_bordado, subtotal_nombres, delivery_costo,
        abono, saldo_pendiente, status, None
    ))

    orden_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return orden_id


def guardar_detalle(orden_id, colegio, tipo_prenda, talla, marca, color, cantidad):
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO orden_detalle (orden_id, colegio, tipo_prenda, talla, marca, color, cantidad)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (orden_id, colegio, tipo_prenda, talla, marca, color, cantidad))

    conn.commit()
    cursor.close()
    conn.close()


def guardar_parametro(parametro, valor):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO configuracion_general (parametro, valor) 
    VALUES (%s, %s)
    ON CONFLICT (parametro) DO UPDATE SET valor = EXCLUDED.valor
    """, (parametro, valor))
    conn.commit()
    cursor.close()
    conn.close()


def obtener_parametro(parametro):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion_general WHERE parametro = %s", (parametro,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado[0] if resultado else 0.0


# --- GESTIÓN DE COLEGIOS ---###
def guardar_colegio(nombre, precio_bordado):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO colegios (nombre, precio_bordado) 
    VALUES (%s, %s)
    ON CONFLICT (nombre) DO UPDATE SET precio_bordado = EXCLUDED.precio_bordado
    """, (nombre, precio_bordado))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_colegios():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT id, nombre, precio_bordado FROM colegios ORDER BY nombre", conn)
    conn.close()
    return df

def obtener_precio_colegio(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT precio_bordado FROM colegios WHERE nombre = %s", (nombre,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado[0] if resultado else 0.0

def eliminar_colegio(id_col):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colegios WHERE id = %s", (id_col,))
    conn.commit()
    cursor.close()
    conn.close()


# --- GESTIÓN DE DELIVERY ---#
def guardar_zona_delivery(nombre, costo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO zonas_delivery (nombre, costo) 
    VALUES (%s, %s)
    ON CONFLICT (nombre) DO UPDATE SET costo = EXCLUDED.costo
    """, (nombre, costo))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_zonas_delivery():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT nombre, costo FROM zonas_delivery ORDER BY nombre", conn)
    conn.close()
    return df

def obtener_costo_delivery(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT costo FROM zonas_delivery WHERE nombre = %s", (nombre,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado[0] if resultado else 0.0

def eliminar_zona_delivery(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM zonas_delivery WHERE nombre = %s", (nombre,))
    conn.commit()
    cursor.close()
    conn.close()


# --- GESTIÓN DE CATÁLOGOS GENÉRICOS ---#
def guardar_tipo_prenda(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tipos_prenda (nombre) VALUES (%s)
    ON CONFLICT (nombre) DO NOTHING
    """, (nombre,))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_tipos_prenda():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT id, nombre FROM tipos_prenda ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_tipo_prenda(id_item):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tipos_prenda WHERE id = %s", (id_item,))
    conn.commit()
    cursor.close()
    conn.close()

def guardar_marca(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO marcas (nombre) VALUES (%s)
    ON CONFLICT (nombre) DO NOTHING
    """, (nombre,))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_marcas():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT id, nombre FROM marcas ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_marca(id_item):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM marcas WHERE id = %s", (id_item,))
    conn.commit()
    cursor.close()
    conn.close()

def guardar_color(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO colores (nombre) VALUES (%s)
    ON CONFLICT (nombre) DO NOTHING
    """, (nombre,))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_colores():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT id, nombre FROM colores ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_color(id_item):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colores WHERE id = %s", (id_item,))
    conn.commit()
    cursor.close()
    conn.close()

def guardar_talla(nombre):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tallas (nombre) VALUES (%s)
    ON CONFLICT (nombre) DO NOTHING
    """, (nombre,))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_tallas():
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT id, nombre FROM tallas ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_talla(id_item):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tallas WHERE id = %s", (id_item,))
    conn.commit()
    cursor.close()
    conn.close()


# --- CONSULTAS DE ÓRDENES Y PAGOS ---
def obtener_ordenes():
    conn = obtener_conexion()
    df = pd.read_sql_query("""
    SELECT id, nombre, telefono, correo, colegio, cantidad_total, delivery, zona_delivery, status, fecha_entrega, abono, saldo_pendiente, fecha_pago,
           subtotal_bordado, subtotal_nombres, delivery_costo, tipo_logo, nombre_bordado, cantidad_nombre
    FROM ordenes ORDER BY id DESC
    """, conn)
    conn.close()
    return df

def obtener_orden_por_id(orden_id):
    conn = obtener_conexion()
    df = pd.read_sql_query("SELECT * FROM ordenes WHERE id = %s", conn, params=(int(orden_id),))
    conn.close()
    return df

def obtener_detalle_orden(orden_id):
    conn = obtener_conexion()
    df = pd.read_sql_query("""
    SELECT colegio, tipo_prenda, talla, marca, color, cantidad
    FROM orden_detalle WHERE orden_id = %s
    """, conn, params=(int(orden_id),))
    df.columns = ["Colegio", "Tipo Prenda", "Talla", "Marca", "Color", "Cantidad"]
    conn.close()
    return df

def registrar_pago(orden_id, monto_pago_usd, tasa_cambio=0.0):
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    if tasa_cambio <= 0:
        cursor.execute("SELECT valor FROM configuracion_general WHERE parametro = 'tasa_cambio'")
        res_tasa = cursor.fetchone()
        tasa_cambio = res_tasa[0] if res_tasa else 0.0

    cursor.execute("SELECT abono, saldo_pendiente FROM ordenes WHERE id = %s", (orden_id,))
    resultado = cursor.fetchone()

    abono_actual, saldo_actual = resultado[0], resultado[1]
    nuevo_abono = abono_actual + monto_pago_usd
    nuevo_saldo = max(0.0, saldo_actual - monto_pago_usd)
    fecha_actual = str(date.today())

    cursor.execute("""
        UPDATE ordenes SET abono = %s, saldo_pendiente = %s, fecha_pago = %s WHERE id = %s
    """, (nuevo_abono, nuevo_saldo, fecha_actual, orden_id))

    monto_bs = round(monto_pago_usd * tasa_cambio, 2)
    cursor.execute("""
        INSERT INTO historico_pagos (orden_id, monto_usd, tasa_cambio, monto_bs, fecha)
        VALUES (%s, %s, %s, %s, %s)
    """, (orden_id, monto_pago_usd, tasa_cambio, monto_bs, fecha_actual))

    conn.commit()
    cursor.close()
    conn.close()

def obtener_historico_pagos(orden_id=None):
    conn = obtener_conexion()
    if orden_id:
        query = "SELECT * FROM historico_pagos WHERE orden_id = %s ORDER BY id DESC"
        df = pd.read_sql_query(query, conn, params=(int(orden_id),))
    else:
        query = "SELECT * FROM historico_pagos ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def actualizar_status_orden(orden_id, status):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE ordenes SET status = %s WHERE id = %s", (status, orden_id))
    conn.commit()
    cursor.close()
    conn.close()


# --- ENVIOS DE CORREO ---
def enviar_confirmacion_solicitud(destinatario, nombre_cliente, orden_id, fecha_entrega):
    remitente = "bordaclick@gmail.com"
    password = "niiv nskd qzox xwnr"

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = f"Bordaclick - Solicitud Recibida #{orden_id:04d}"

    cuerpo = f"""Hola {nombre_cliente},

Gracias por confiar en Bordaclick.
Hemos recibido correctamente tu solicitud.

Número de Solicitud: #{orden_id:04d}
Fecha estimada de entrega: {fecha_entrega}

Nuestro equipo revisará tu solicitud y comenzará el proceso de producción.

Saludos,
Equipo Bordaclick
"""
    mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    try:
        servidor.login(remitente, password)
        servidor.send_message(mensaje)
        servidor.quit()
    except Exception as e:
        print(f"❌ Error Gmail: {e}")
        raise

def enviar_pdf_por_correo(destinatario, nombre_cliente, orden_id, fecha_entrega, pdf_path):
    remitente = "bordaclick@gmail.com"
    password = "niiv nskd qzox xwnr"

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = f"Bordaclick - Confirmación de Pedido #{orden_id:04d}"

    cuerpo = f"""Hola {nombre_cliente},

Gracias por confiar en Bordaclick.
Adjunto encontrarás la Orden de Servicio correspondiente a tu pedido.

Número de Pedido: #{orden_id:04d}
Fecha de Entrega: {fecha_entrega}

Saludos,
Equipo Bordaclick
"""
    mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

    with open(pdf_path, "rb") as archivo:
        parte = MIMEBase("application", "octet-stream")
        parte.set_payload(archivo.read())

    encoders.encode_base64(parte)
    parte.add_header("Content-Disposition", f"attachment; filename={pdf_path}")
    mensaje.attach(parte)

    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    try:
        servidor.login(remitente, password)
        servidor.send_message(mensaje)
        servidor.quit()
    except Exception as e:
        print(f"❌ Error Gmail: {e}")
        raise

def enviar_notificacion_estado(destinatario, nombre_cliente, orden_id, fecha_entrega, estado, delivery):
    remitente = "bordaclick@gmail.com"
    password = "niiv nskd qzox xwnr"

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario

    if estado == "En Producción":
        mensaje["Subject"] = f"Bordaclick - Tu pedido #{orden_id:04d} está en producción"
        cuerpo = f"Hola {nombre_cliente},\n\nTu pedido #{orden_id:04d} ya se encuentra en producción.\nFecha estimada: {fecha_entrega}\n\nBordaclick."
    elif estado == "Listo para Entrega":
        if "Sí" in str(delivery):
            mensaje["Subject"] = f"Bordaclick - Tu pedido #{orden_id:04d} está listo para entrega"
            cuerpo = f"Hola {nombre_cliente},\n\nTu pedido #{orden_id:04d} está listo y se enviará por delivery.\n\nBordaclick."
        else:
            mensaje["Subject"] = f"Bordaclick - Tu pedido #{orden_id:04d} está listo para retiro"
            cuerpo = f"Hola {nombre_cliente},\n\nTu pedido #{orden_id:04d} está listo para retirar en tienda.\n\nBordaclick."
    else:
        return

    mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    servidor.login(remitente, password)
    servidor.send_message(mensaje)
    servidor.quit()

def eliminar_orden(orden_id):
    """
    Elimina una orden, sus detalles de prendas y su historial de pagos en Supabase.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM orden_detalle WHERE orden_id = %s", (orden_id,))
        cursor.execute("DELETE FROM historico_pagos WHERE orden_id = %s", (orden_id,))
        cursor.execute("DELETE FROM ordenes WHERE id = %s", (orden_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al eliminar la orden #{orden_id}: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False