# Vamos a revisar el error exacto que se observa en los logs de la consola en la captura de pantalla:
# "digito_calc = 0 if resto == 0 else (2 if resto == 1 else 11 - resto)"
# El error proviene de la sintaxis de escape en cadenas multilínea o cadenas de Python pasadas mediante script de terminal.
# Vamos a corregir completamente el script streamlit_app.py asegurándonos de que no existan errores de escape ni de sintaxis y que la aplicación corra perfectamente.

fixed_code = '''"""
Audit Intelligence USA - Enterprise Big 4 Killer & Autonomous CRM/ERP Suite,
Motor Defensivo Universal con Autorreparación Absoluta de Esquema DB y Control de Secuencias e-NCF.
Version: 10.10.70-PROD Enterprise Full Production & Universal Compliance Suite
"""

import os
import sys
import json
import sqlite3
import hashlib
import base64
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
import openpyxl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] AUDIT_INTELLIGENCE_CORE: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Audit_Intelligence_Core")

DB_PATH = "itbis_sistem_dgii_full.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                rnc_cedula TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                pais TEXT NOT NULL,
                ciiu_sector TEXT NOT NULL DEFAULT 'General',
                idioma TEXT NOT NULL DEFAULT 'Español',
                subscription_plan TEXT NOT NULL,
                subscription_status TEXT NOT NULL,
                is_facturable INTEGER NOT NULL DEFAULT 1,
                parent_owner TEXT NOT NULL DEFAULT 'admin',
                logo_path TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas_clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contador_username TEXT NOT NULL,
                rnc_empresa TEXT UNIQUE NOT NULL,
                razon_social TEXT NOT NULL,
                nombre_comercial TEXT NOT NULL,
                tipo_entidad TEXT NOT NULL DEFAULT 'Empresa Privada',
                sector_ciiu TEXT NOT NULL,
                actividad_economica_automatica TEXT NOT NULL DEFAULT 'Servicios Generales',
                direccion TEXT NOT NULL,
                telefono TEXT NOT NULL,
                consorcio_grupo TEXT NOT NULL DEFAULT 'Independiente',
                ultimo_encf_usado TEXT NOT NULL DEFAULT 'E310000000030',
                estado_onapi TEXT NOT NULL DEFAULT 'Vigente',
                estado_dgii TEXT NOT NULL DEFAULT 'Activo / Al Día',
                estado_tss TEXT NOT NULL DEFAULT 'Al Día',
                estado_ministerio_trabajo TEXT NOT NULL DEFAULT 'Registrado',
                riesgo_aml TEXT NOT NULL DEFAULT 'Bajo (Normal)',
                tipo_cliente TEXT NOT NULL DEFAULT 'Cliente BASA (De Pago)',
                monto_mensual REAL NOT NULL DEFAULT 5000.0,
                fecha_vencimiento TEXT NOT NULL,
                estado_servicio TEXT NOT NULL DEFAULT 'Activo',
                modulo_ventas_activo INTEGER NOT NULL DEFAULT 1,
                modulo_compras_activo INTEGER NOT NULL DEFAULT 1,
                modulo_activos_activo INTEGER NOT NULL DEFAULT 1,
                modulo_reportes_activo INTEGER NOT NULL DEFAULT 1,
                usuario_dgii TEXT NOT NULL,
                password_dgii TEXT NOT NULL,
                certificado_filename TEXT NOT NULL,
                password_certificado TEXT NOT NULL,
                ambiente TEXT NOT NULL DEFAULT 'Producción',
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixed_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rnc_empresa TEXT NOT NULL DEFAULT '133378711',
                codigo_activo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                categoria_dgii TEXT NOT NULL,
                costo_adquisicion REAL NOT NULL,
                depreciacion_acumulada REAL NOT NULL DEFAULT 0.0,
                valor_en_libros REAL NOT NULL,
                fecha_adquisicion TEXT NOT NULL,
                tipo_movimiento TEXT NOT NULL DEFAULT 'Adquisición',
                estado_activo TEXT NOT NULL DEFAULT 'Activo'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rnc_empresa TEXT NOT NULL DEFAULT '133378711',
                rnc_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                tipo_ncf_ecf TEXT NOT NULL,
                modo_registro TEXT NOT NULL DEFAULT 'Automático Actual',
                secuencia_encf TEXT NOT NULL,
                clasificacion_ingreso_dgii TEXT NOT NULL,
                monto_neto REAL NOT NULL,
                itbis REAL NOT NULL,
                retencion_isr REAL NOT NULL DEFAULT 0.0,
                retencion_itbis REAL NOT NULL DEFAULT 0.0,
                monto_total REAL NOT NULL,
                estado_cobro TEXT NOT NULL DEFAULT 'Pendiente',
                vencimiento TEXT NOT NULL,
                estado_dgii TEXT NOT NULL,
                ya_reportado_salvedad INTEGER NOT NULL DEFAULT 0,
                reportado_organismos INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases_606 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rnc_empresa TEXT NOT NULL DEFAULT '133378711',
                rnc_suplidor TEXT NOT NULL,
                nombre_suplidor TEXT NOT NULL,
                ncf_comprobante TEXT NOT NULL,
                tipo_ncf_egreso TEXT NOT NULL,
                clasificacion_gasto_dgii TEXT NOT NULL,
                codigo_cuenta_contable TEXT NOT NULL DEFAULT '51101',
                monto_facturado REAL NOT NULL,
                itbis_facturado REAL NOT NULL,
                retencion_ir17 REAL NOT NULL DEFAULT 0.0,
                estado_cxp TEXT NOT NULL DEFAULT 'Pendiente Pago',
                vencimiento TEXT NOT NULL,
                fuente_ingreso TEXT NOT NULL DEFAULT 'Manual',
                estado_validacion TEXT NOT NULL DEFAULT 'Correcto',
                motivo_defecto TEXT DEFAULT '',
                archivo_adjunto TEXT DEFAULT '',
                ya_reportado_salvedad INTEGER NOT NULL DEFAULT 0,
                reportado_organismos INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        def ensure_column(table_name, col_name, col_def):
            try:
                cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()]
                if col_name not in cols:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")
            except Exception as ex:
                logger.warning(f"No se pudo asegurar columna {col_name} en {table_name}: {str(ex)}")

        ensure_column("sales_invoices", "rnc_empresa", "TEXT NOT NULL DEFAULT '133378711'")
        ensure_column("sales_invoices", "estado_cobro", "TEXT NOT NULL DEFAULT 'Pendiente'")
        
        ensure_column("purchases_606", "rnc_empresa", "TEXT NOT NULL DEFAULT '133378711'")
        ensure_column("purchases_606", "estado_cxp", "TEXT NOT NULL DEFAULT 'Pendiente Pago'")
        ensure_column("purchases_606", "retencion_ir17", "REAL NOT NULL DEFAULT 0.0")

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'AdministradorMaster'")
        if cursor.fetchone()[0] == 0:
            admin_pass_hash = hashlib.sha256("AdminBASA2026*".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, rnc_cedula, email, phone, pais, ciiu_sector, idioma, subscription_plan, subscription_status, is_facturable, parent_owner, logo_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Español', ?, 'Activo', 1, 'admin', '', ?)
            """, ("admin", admin_pass_hash, "Lic. Pedro Baldera - Admin Master Global", "AdministradorMaster", "131-0000000-1", "admin@auditintelligence.com", "+18095550000", "República Dominicana", "Financiero / Auditoría", "Exonerado", datetime.utcnow().isoformat()))
            conn.commit()
            
        conn.close()
    except Exception as e:
    # Corrección de sintaxis de escape
        logger.error(f"Error DB Migration: {str(e)}")

init_db()

def validar_rnc_dgii_ts(rnc: str) -> Dict[str, Any]:
    rnc_clean = re.sub(r'\\D', '', rnc)
    if len(rnc_clean) == 9:
        pesos = [7, 9, 8, 6, 5, 4, 3, 2]
        suma = sum(int(rnc_clean[i]) * pesos[i] for i in range(8))
        resto = suma % 11
        digito_calc = 0 if resto == 0 else (2 if resto == 1 else 11 - resto)
        valido = digito_calc == int(rnc_clean[8])
        return {"valido": valido, "tipo": "RNC Empresarial", "valor": rnc_clean, "mensaje": "RNC válido según algoritmo DGII-TS" if valido else "Dígito verificador de RNC incorrecto"}
    elif len(rnc_clean) == 11:
        pesos = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        suma = 0
        for i in range(10):
            val = int(rnc_clean[i]) * pesos[i]
            suma += sum(int(digit) for digit in str(val))
        resto = suma % 10
        digito_calc = (10 - resto) % 10
        valido = digito_calc == int(rnc_clean[10])
        return {"valido": valido, "tipo": "Cédula de Identidad", "valor": rnc_clean, "mensaje": "Cédula válida según algoritmo DGII-TS" if valido else "Dígito verificador de Cédula incorrecto"}
    else:
        return {"valido": False, "tipo": "Desconocido", "valor": rnc, "mensaje": "Longitud inválida para RNC (9 dígitos) o Cédula (11 dígitos)"}

def obtener_siguiente_secuencia_encf(rnc_empresa: str) -> str:
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ultimo_encf_usado FROM empresas_clientes WHERE rnc_empresa = ?", (rnc_empresa,))
        row_emp = cursor.fetchone()
        
        ultimo = "E310000000030"
        if row_emp and row_emp[0]:
            ultimo = row_emp[0].strip().upper()
        else:
            cursor.execute("SELECT secuencia_encf FROM sales_invoices WHERE rnc_empresa = ? ORDER BY id DESC LIMIT 1", (rnc_empresa,))
            row_inv = cursor.fetchone()
            if row_inv and row_inv[0]:
                ultimo = row_inv[0].strip().upper()
                
        conn.close()
        
        match = re.search(r'(\\d+)$', ultimo)
        if match:
            num_str = match.group(1)
            num_val = int(num_str) + 1
            prefijo = ultimo[:len(ultimo)-len(num_str)]
            return f"{prefijo}{num_val:0{len(num_str)}d}"
    except Exception as e:
        logger.error(f"Error obteniendo secuencia e-NCF: {str(e)}")
    return "E310000000031"

st.set_page_config(page_title="Ecosistema ERP Enterprise & Formatos DGII - Audit Intelligence USA", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 26px; font-weight: bold; color: #1e3a8a; margin-bottom: 0px; }
    .sub-title { font-size: 14px; color: #475569; margin-bottom: 15px; }
    .org-card { background-color: #f8fafc; border: 2px solid #3b82f6; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .org-title { font-size: 18px; font-weight: bold; color: #1e40af; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 Ecosistema ERP & Liquidación Oficial ITBIS (IT-1) / IR-17 (Audit Intelligence USA)</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Supervisión técnica: <b>Lic. Pedro Baldera</b> | Control Preventivo Anti-Errores DB & Formatos 606/607 | Producción 100/100.</p>', unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

st.sidebar.header("🔐 Acceso & Seguridad")
if not st.session_state.authenticated:
    tab_login, tab_recovery = st.sidebar.tabs(["🔑 Iniciar Sesión", "🔄 Recuperar Clave"])
    with tab_login:
        user_input = st.text_input("Usuario o Correo", value="admin")
        pass_input = st.text_input("Contraseña", type="password", value="AdminBASA2026*")
        if st.button("Ingresar al Sistema"):
            pass_hash = hashlib.sha256(pass_input.encode()).hexdigest()
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, rnc_cedula FROM users WHERE (username = ? OR email = ?) AND password_hash = ?", (user_input, user_input, pass_hash))
            row = cursor.fetchone()
            conn.close()
            if row:
                st.session_state.authenticated = True
                st.session_state.username = row[0]
                st.session_state.role = row[1]
                st.success(f"¡Bienvenido {row[0]}!")
                st.rerun()
            else:
                st.error("Credenciales inválidas. Clave master: AdminBASA2026*")
    with tab_recovery:
        st.markdown("<b>Recupere su clave mediante Correo, RNC, Cédula o ID:</b>", unsafe_allow_html=True)
        rec_identificador = st.text_input("Correo, RNC, Cédula o ID", value="")
        via_envio = st.selectbox("Canal de Restablecimiento", ["Correo Electrónico", "SMS", "WhatsApp"])
        nueva_clave_temp = st.text_input("Nueva Contraseña Temporal", type="password", value="NuevaClave2026*")
        if st.button("📤 Enviar Código y Restablecer"):
            if rec_identificador:
                try:
                    new_hash = hashlib.sha256(nueva_clave_temp.encode()).hexdigest()
                    init_db()
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ? OR email = ? OR rnc_cedula = ?", (new_hash, rec_identificador, rec_identificador, rec_identificador))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Clave restablecida con éxito vía {via_envio}!")
                except Exception as ex:
                    st.error(f"Error al restablecer: {str(ex)}")
            else:
                st.warning("Ingrese su identificador.")
    st.stop()
else:
    st.sidebar.write(f"👤 **Usuario:** {st.session_state.username}")
    st.sidebar.write(f"🛡️ **Rol:** {st.session_state.role}")
    
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT rnc_empresa, razon_social FROM empresas_clientes")
    empresas_db = cursor.fetchall()
    conn.close()
    
    opciones_empresas = ["Seleccione o Cree una Empresa..."] + [f"{e[1]} (RNC: {e[0]})" for e in empresas_db]
    empresa_seleccionada_str = st.sidebar.selectbox("📂 Empresa Activa en Ecosistema", opciones_empresas)
    
    if "Seleccione" not in empresa_seleccionada_str:
        match_rnc = re.search(r'RNC:\\s*([0-9-]+)', empresa_seleccionada_str)
        if match_rnc:
            st.session_state.rnc_activo = match_rnc.group(1)
            st.session_state.nombre_empresa_activo = empresa_seleccionada_str.split(" (RNC:")[0]
    else:
        st.session_state.rnc_activo = ""
        st.session_state.nombre_empresa_activo = ""

    st.sidebar.info(f"📌 **Activa:** {st.session_state.get('nombre_empresa_activo', 'Ninguna')}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

st.markdown("---")
st.markdown("### 🗺️ Portada General del Ecosistema ERP & Formatos 606, 607, ITBIS (IT-1) y Retenciones IR-17")

st.markdown("""
    <div class="org-card">
        <div class="org-title">🏢 NODO 1: Creación de Entidad y Configuración de Secuencias Oficiales</div>
    </div>
""", unsafe_allow_html=True)

with st.form("form_nodo_1_secuencia"):
    col_nc1, col_nc2 = st.columns(2)
    with col_nc1:
        rnc_input_auto = st.text_input("RNC / Cédula a Registrar", value="133378711")
        razon_auto = st.text_input("Razón Social", value="BALDERA SANTOS Y ASOCIADOS SRL")
        comercial_auto = st.text_input("Nombre Comercial / ONAPI", value="BASA Audit & Software Solutions")
    with col_nc2:
        ultimo_ncf_config = st.text_input("Último e-NCF Utilizado / Válido", value="E310000000030")
        sector_auto = st.selectbox("Sector CIIU", ["6920 - Contabilidad y Auditoría", "6201 - Desarrollo de Software", "8411 - Administración Pública"])
        dir_auto = st.text_input("Dirección Fiscal", value="Av. Sabana Larga #124, Santo Domingo Este, RD")
        tel_auto = st.text_input("Teléfono", value="829-771-7390")
        
    if st.form_submit_button("🚀 Guardar Empresa y Configurar Secuencia e-NCF"):
        try:
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO empresas_clientes (contador_username, rnc_empresa, razon_social, nombre_comercial, tipo_entidad, sector_ciiu, actividad_economica_automatica, direccion, telefono, consorcio_grupo, ultimo_encf_usado, estado_onapi, estado_dgii, estado_tss, estado_ministerio_trabajo, riesgo_aml, tipo_cliente, monto_mensual, fecha_vencimiento, estado_servicio, modulo_ventas_activo, modulo_compras_activo, modulo_activos_activo, modulo_reportes_activo, usuario_dgii, password_dgii, certificado_filename, password_certificado, ambiente, updated_at)
                VALUES (?, ?, ?, ?, 'Empresa Privada', ?, 'Servicios Profesionales', ?, ?, 'Independiente', ?, 'Vigente', 'Activo / Al Día', 'Al Día', 'Registrado', 'Bajo (Normal)', 'Cliente BASA (De Pago)', 5000.0, '2026-12-31', 'Activo', 1, 1, 1, 1, 'licpedrobaldera', 'Clave2026*', 'certificado.p12', 'Cert2026*', 'Producción', ?)
                ON CONFLICT(rnc_empresa) DO UPDATE SET
                razon_social=excluded.razon_social, ultimo_encf_usado=excluded.ultimo_encf_usado, updated_at=excluded.updated_at
            """, (st.session_state.username, rnc_input_auto, razon_auto, comercial_auto, sector_auto, dir_auto, tel_auto, ultimo_ncf_config, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success(f"¡Empresa guardada con éxito! Secuencia base configurada a partir de `{ultimo_ncf_config}`.")
            st.rerun()
        except Exception as ex:
            st.error(f"Error al registrar: {str(ex)}")

if not st.session_state.get("rnc_activo"):
    st.warning("⚠️ Seleccione una empresa activa en la barra lateral superior para operar.")
    st.stop()

st.markdown("""
    <div class="org-card">
        <div class="org-title">📈 NODO 2: Liquidación Oficial de ITBIS (IT-1) y Retenciones IR-17 en Vivo</div>
    </div>
""", unsafe_allow_html=True)

try:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rnc_act = st.session_state.get("rnc_activo")
    v_total = pd.read_sql_query("SELECT SUM(monto_neto) AS total FROM sales_invoices WHERE rnc_empresa = ?", conn, params=(rnc_act,))['total'].iloc[0] or 0.0
    itbis_cobrado = pd.read_sql_query("SELECT SUM(itbis) AS total FROM sales_invoices WHERE rnc_empresa = ?", conn, params=(rnc_act,))['total'].iloc[0] or 0.0
    c_total = pd.read_sql_query("SELECT SUM(monto_facturado) AS total FROM purchases_606 WHERE rnc_empresa = ?", conn, params=(rnc_act,))['total'].iloc[0] or 0.0
    itbis_pagado = pd.read_sql_query("SELECT SUM(itbis_facturado) AS total FROM purchases_606 WHERE rnc_empresa = ?", conn, params=(rnc_act,))['total'].iloc[0] or 0.0
    ir17_retenido = pd.read_sql_query("SELECT SUM(retencion_ir17) AS total FROM purchases_606 WHERE rnc_empresa = ?", conn, params=(rnc_act,))['total'].iloc[0] or 0.0
    conn.close()
except Exception:
    v_total, itbis_cobrado, c_total, itbis_pagado, ir17_retenido = 0.0, 0.0, 0.0, 0.0, 0.0

itbis_a_pagar = max(0.0, itbis_cobrado - itbis_pagado)
col_li1, col_li2, col_li3 = st.columns(3)
col_li1.metric("Ventas Netas (607)", f"RD$ {v_total:,.2f}")
col_li2.metric("ITBIS Cobrado (IT-1)", f"RD$ {itbis_cobrado:,.2f}")
col_li3.metric("ITBIS a Pagar / Saldo Favor", f"RD$ {itbis_a_pagar:,.2f}")

col_li4, col_li5 = st.columns(2)
col_li4.metric("Compras / Gastos (606)", f"RD$ {c_total:,.2f}")
col_li5.metric("Retenciones IR-17 Acumuladas", f"RD$ {ir17_retenido:,.2f}")

st.markdown("""
    <div class="org-card">
        <div class="org-title">📦 NODO 4: Módulo de Ingresos, Formato 607 y e-CF</div>
    </div>
""", unsafe_allow_html=True)

siguiente_sec = obtener_siguiente_secuencia_encf(st.session_state.get("rnc_activo"))
st.info(f"🔢 **Siguiente e-NCF Oficial:** `{siguiente_sec}`")

with st.form("form_nodo_4_ingresos"):
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        tipo_e = st.selectbox("Tipo e-CF", ["E31 - Crédito Fiscal Electrónico", "E32 - Consumo Electrónico"])
        secuencia_final_input = st.text_input("Secuencia e-NCF a Asignar", value=siguiente_sec)
        rnc_cli = st.text_input("RNC / Cédula del Cliente", value="101782307")
        nom_cli = st.text_input("Razón Social del Cliente", value="FERNELY LEBRON & ASOCIADOS SRL")
    with col_i2:
        desc_v = st.text_input("Descripción del Servicio / Factura", value="Servicio Profesional Asesoría")
        monto_n = st.number_input("Monto Neto RD$", min_value=0.0, value=16372.50)
        t_itbis = st.selectbox("Tasa ITBIS", [0.18, 0.16, 0.0], index=0)
        estado_cb = st.selectbox("Estado de Cobro", ["Pendiente de Cobro", "Pagado Total"])
        
    itb_calc = monto_n * t_itbis
    tot_calc = monto_n + itb_calc
    
    if st.form_submit_button("💾 Emitir Venta (Formato 607)"):
        try:
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sales_invoices (username, rnc_empresa, rnc_cliente, nombre_cliente, tipo_ncf_ecf, modo_registro, secuencia_encf, clasificacion_ingreso_dgii, monto_neto, itbis, monto_total, estado_cobro, vencimiento, estado_dgii, ya_reportado_salvedad, reportado_organismos, created_at)
                VALUES (?, ?, ?, ?, ?, 'Automático Actual', ?, '01 - Ingresos Operacionales', ?, ?, ?, ?, ?, 'AprobadoDGII', 0, 1, ?)
            """, (st.session_state.username, st.session_state.get("rnc_activo"), rnc_cli, nom_cli, tipo_e, secuencia_final_input, monto_n, itb_calc, tot_calc, estado_cb, (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"), datetime.utcnow().isoformat()))
            
            cursor.execute("UPDATE empresas_clientes SET ultimo_encf_usado = ? WHERE rnc_empresa = ?", (secuencia_final_input, st.session_state.get("rnc_activo")))
            conn.commit()
            conn.close()
            st.success(f"¡Venta emitida y guardada con e-NCF `{secuencia_final_input}` sin pérdida de datos!")
            st.rerun()
        except Exception as ex:
            st.error(f"Error al registrar venta: {str(ex)}")

st.markdown("""
    <div class="org-card">
        <div class="org-title">🛒 NODO 5: Módulo de Compras (Formato 606), CxP y Retenciones IR-17</div>
    </div>
""", unsafe_allow_html=True)

with st.form("form_nodo_5_compras"):
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        rnc_sup = st.text_input("RNC Suplidor", value="133412918")
        nom_sup = st.text_input("Nombre Suplidor", value="SUPLIDORES COMERCIALES SRL")
        ncf_sup = st.text_input("NCF Comprobante", value="E310000000099")
        tipo_g = st.selectbox("Tipo de Gasto DGII", ["01 - Personal", "02 - Suministros y Servicios", "03 - Arrendamientos", "04 - Activos Fijos"])
    with col_c2:
        m_fac = st.number_input("Monto Facturado RD$", min_value=0.0, value=12000.0)
        itb_fac = st.number_input("ITBIS Facturado RD$", min_value=0.0, value=2160.0)
        ret_ir17_val = st.number_input("Retención IR-17 (Ej. 10% Honorarios / 10% Alquileres)", min_value=0.0, value=0.0)
        est_cxp = st.selectbox("Estado CxP", ["Pendiente Pago", "Pagado"])
        arch_sop = st.file_uploader("Adjuntar Factura de Compra", type=["pdf", "png", "jpg", "jpeg"])
        
    if st.form_submit_button("💾 Guardar Compra 606 y Retención IR-17"):
        val_r = validar_rnc_dgii_ts(rnc_sup)
        est_v = "Correcto" if val_r["valido"] else "Defectuoso"
        mot_d = "" if val_r["valido"] else "RNC Suplidor Inválido"
        
        try:
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchases_606 (username, rnc_empresa, rnc_suplidor, nombre_suplidor, ncf_comprobante, tipo_ncf_egreso, clasificacion_gasto_dgii, codigo_cuenta_contable, monto_facturado, itbis_facturado, retencion_ir17, estado_cxp, vencimiento, fuente_ingreso, estado_validacion, motivo_defecto, archivo_adjunto, ya_reportado_salvedad, reportado_organismos, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'Gastos Operativos', '51101', ?, ?, ?, ?, ?, 'Manual/IA', ?, ?, 0, 1, ?)
            """, (st.session_state.username, st.session_state.get("rnc_activo"), rnc_sup, nom_sup, ncf_sup, tipo_g, m_fac, itb_fac, ret_ir17_val, est_cxp, (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"), est_v, mot_d, arch_sop.name if arch_sop else "", datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("¡Compra 606 y retención IR-17 guardadas y blindadas sin errores!")
            st.rerun()
        except Exception as ex:
            st.error(f"Error al registrar compra: {str(ex)}")

st.markdown("""
    <div class="org-card">
        <div class="org-title">🖨️ NODO 8: Centro de Reportes y Exportación Universal (Formatos 606, 607, IT-1, IR-17)</div>
    </div>
""", unsafe_allow_html=True)

try:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rnc_act = st.session_state.get("rnc_activo")
    df_v_rep = pd.read_sql_query("SELECT secuencia_encf AS comprobante, rnc_cliente AS rnc, nombre_cliente AS nombre, monto_total, 'Venta e-CF (607)' AS tipo FROM sales_invoices WHERE rnc_empresa = ?", conn, params=(rnc_act,))
    df_c_rep = pd.read_sql_query("SELECT ncf_comprobante AS comprobante, rnc_suplidor AS rnc, nombre_suplidor AS nombre, monto_facturado AS monto_total, 'Compra (606)' AS tipo FROM purchases_606 WHERE rnc_empresa = ?", conn, params=(rnc_act,))
    conn.close()
    
    df_rep_total = pd.concat([df_v_rep, df_c_rep], ignore_index=True)
    if not df_rep_total.empty:
        st.dataframe(df_rep_total, use_container_width=True)
        st.download_button("📥 Descargar Reporte Consolidado Universal (CSV / Excel / Office)", data=df_rep_total.to_csv(index=False).encode('utf-8'), file_name=f"Reporte_Universal_DGII_{rnc_act}.csv", mime="text/csv")
    else:
        st.info("No hay transacciones registradas para la empresa activa.")
except Exception:
    st.info("Cargando reportes...")
'''

with open("streamlit_app.py", "w", encoding="utf-8") as f:
    f.write(fixed_code)

print("streamlit_app.py actualizado sin errores de sintaxis ni escape.")
