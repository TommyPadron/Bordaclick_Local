import sqlite3
import pandas as pd
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

DATABASE = "bordaclick_dev.db"

def crear_bd():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        precio_bordado REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tipos_prenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marcas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tallas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER,
        monto_usd REAL,
        tasa_cambio REAL,
        monto_bs REAL,
        fecha TEXT,
        FOREIGN KEY (orden_id) REFERENCES ordenes(id)
    )
    """)

    conn.commit()
    conn.close()


def guardar_orden(
    nombre, telefono, correo, colegio, cantidad_total, tipo_logo,
    nombre_bordado, cantidad_nombre, delivery, zona_delivery,
    fecha_entrega, precio_bordado, subtotal_bordado, subtotal_nombres,
    delivery_costo, abono, saldo_pendiente, status
):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ordenes (
            nombre, telefono, correo, colegio, cantidad_total, tipo_logo,
            nombre_bordado, cantidad_nombre, delivery, zona_delivery, fecha_entrega,
            precio_bordado, subtotal_bordado, subtotal_nombres, delivery_costo,
            abono, saldo_pendiente, status, fecha_pago
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nombre, telefono, correo, colegio, cantidad_total, tipo_logo,
        nombre_bordado, cantidad_nombre, delivery, zona_delivery, str(fecha_entrega),
        precio_bordado, subtotal_bordado, subtotal_nombres, delivery_costo,
        abono, saldo_pendiente, status, None
    ))

    conn.commit()
    orden_id = cursor.lastrowid
    conn.close()
    return orden_id


def guardar_detalle(orden_id, colegio, tipo_prenda, talla, marca, color, cantidad):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO orden_detalle (orden_id, colegio, tipo_prenda, talla, marca, color, cantidad)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (orden_id, colegio, tipo_prenda, talla, marca, color, cantidad))

    conn.commit()
    conn.close()


def guardar_parametro(parametro, valor):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO configuracion_general (parametro, valor) VALUES (?, ?)
    """, (parametro, valor))
    conn.commit()
    conn.close()


def obtener_parametro(parametro):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion_general WHERE parametro = ?", (parametro,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0.0


# --- GESTIÓN DE COLEGIOS ---###
def guardar_colegio(nombre, precio_bordado):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO colegios (nombre, precio_bordado) VALUES (?, ?)", (nombre, precio_bordado))
    conn.commit()
    conn.close()

def obtener_colegios():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT id, nombre, precio_bordado FROM colegios ORDER BY nombre", conn)
    conn.close()
    return df

def obtener_precio_colegio(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT precio_bordado FROM colegios WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0.0

def eliminar_colegio(id_col):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colegios WHERE id = ?", (id_col,))
    conn.commit()
    conn.close()


# --- GESTIÓN DE DELIVERY ---#
def guardar_zona_delivery(nombre, costo):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO zonas_delivery (nombre, costo) VALUES (?, ?)", (nombre, costo))
    conn.commit()
    conn.close()

def obtener_zonas_delivery():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT nombre, costo FROM zonas_delivery ORDER BY nombre", conn)
    conn.close()
    return df

def obtener_costo_delivery(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT costo FROM zonas_delivery WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0.0

def eliminar_zona_delivery(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM zonas_delivery WHERE nombre = ?", (nombre,))
    conn.commit()
    conn.close()


# --- GESTIÓN DE CATÁLOGOS GENÉRICOS ---#
def guardar_tipo_prenda(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO tipos_prenda (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()

def obtener_tipos_prenda():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT id, nombre FROM tipos_prenda ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_tipo_prenda(id_item):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tipos_prenda WHERE id = ?", (id_item,))
    conn.commit()
    conn.close()

def guardar_marca(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO marcas (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()

def obtener_marcas():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT id, nombre FROM marcas ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_marca(id_item):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM marcas WHERE id = ?", (id_item,))
    conn.commit()
    conn.close()

def guardar_color(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO colores (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()

def obtener_colores():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT id, nombre FROM colores ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_color(id_item):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colores WHERE id = ?", (id_item,))
    conn.commit()
    conn.close()

def guardar_talla(nombre):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO tallas (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()

def obtener_tallas():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT id, nombre FROM tallas ORDER BY nombre", conn)
    conn.close()
    return df

def eliminar_talla(id_item):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tallas WHERE id = ?", (id_item,))
    conn.commit()
    conn.close()


# --- CONSULTAS DE ÓRDENES Y PAGOS ---
def obtener_ordenes():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("""
    SELECT id, nombre, telefono, correo, colegio, cantidad_total, delivery, zona_delivery, status, fecha_entrega, abono, saldo_pendiente, fecha_pago,
           subtotal_bordado, subtotal_nombres, delivery_costo, tipo_logo, nombre_bordado, cantidad_nombre
    FROM ordenes ORDER BY id DESC
    """, conn)
    conn.close()
    return df

def obtener_orden_por_id(orden_id):
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query(f"SELECT * FROM ordenes WHERE id = {int(orden_id)}", conn)
    conn.close()
    return df

def obtener_detalle_orden(orden_id):
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query(f"""
    SELECT colegio, tipo_prenda, talla, marca, color, cantidad
    FROM orden_detalle WHERE orden_id = {int(orden_id)}
    """, conn)
    df.columns = ["Colegio", "Tipo Prenda", "Talla", "Marca", "Color", "Cantidad"]
    conn.close()
    return df

def registrar_pago(orden_id, monto_pago_usd, tasa_cambio=0.0):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Si no nos pasan una tasa, buscamos la que está guardada globalmente
    if tasa_cambio <= 0:
        cursor.execute("SELECT valor FROM configuracion_general WHERE parametro = 'tasa_cambio'")
        res_tasa = cursor.fetchone()
        tasa_cambio = res_tasa[0] if res_tasa else 0.0

    cursor.execute("SELECT abono, saldo_pendiente FROM ordenes WHERE id = ?", (orden_id,))
    resultado = cursor.fetchone()

    abono_actual, saldo_actual = resultado[0], resultado[1]
    nuevo_abono = abono_actual + monto_pago_usd
    nuevo_saldo = max(0.0, saldo_actual - monto_pago_usd)
    fecha_actual = str(date.today())

    cursor.execute("""
        UPDATE ordenes SET abono = ?, saldo_pendiente = ?, fecha_pago = ? WHERE id = ?
    """, (nuevo_abono, nuevo_saldo, fecha_actual, orden_id))

    # Guardar SIEMPRE en el histórico de pagos con el cálculo equivalente en Bs.
    monto_bs = round(monto_pago_usd * tasa_cambio, 2)
    cursor.execute("""
        INSERT INTO historico_pagos (orden_id, monto_usd, tasa_cambio, monto_bs, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (orden_id, monto_pago_usd, tasa_cambio, monto_bs, fecha_actual))

    conn.commit()
    conn.close()

def obtener_historico_pagos(orden_id=None):
    conn = sqlite3.connect(DATABASE)
    if orden_id:
        query = f"SELECT * FROM historico_pagos WHERE orden_id = {int(orden_id)} ORDER BY id DESC"
    else:
        query = "SELECT * FROM historico_pagos ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def actualizar_status_orden(orden_id, status):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE ordenes SET status = ? WHERE id = ?", (status, orden_id))
    conn.commit()
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

import sqlite3

def eliminar_orden(orden_id):
    """
    Elimina una orden, sus detalles de prendas y su historial de pagos.
    """
    conn = sqlite3.connect("bordaclick_dev.db")
    cursor = conn.cursor()
    try:
        # 1. Eliminar los detalles de prendas (Tabla: orden_detalle)
        cursor.execute("DELETE FROM orden_detalle WHERE orden_id = ?", (orden_id,))

        # 2. Eliminar el historial de pagos (Tabla: historico_pagos)
        cursor.execute("DELETE FROM historico_pagos WHERE orden_id = ?", (orden_id,))

        # 3. Eliminar el registro principal (Tabla: ordenes)
        cursor.execute("DELETE FROM ordenes WHERE id = ?", (orden_id,))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error al eliminar la orden #{orden_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()



import sqlite3

def eliminar_orden(orden_id):
    """
    Elimina una orden, sus detalles de prendas y su historial de pagos.
    """
    conn = sqlite3.connect("bordaclick_dev.db")
    cursor = conn.cursor()
    try:
        # 1. Eliminar los detalles de prendas (Tabla: orden_detalle)###
        cursor.execute("DELETE FROM orden_detalle WHERE orden_id = ?", (orden_id,))

        # 2. Eliminar el historial de pagos (Tabla: historico_pagos)
        cursor.execute("DELETE FROM historico_pagos WHERE orden_id = ?", (orden_id,))

        # 3. Eliminar el registro principal (Tabla: ordenes)
        cursor.execute("DELETE FROM ordenes WHERE id = ?", (orden_id,))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error al eliminar la orden #{orden_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()



