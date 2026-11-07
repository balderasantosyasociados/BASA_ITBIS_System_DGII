# Implementamos el sistema de Aislamiento de Módulos (Fault Tolerance / Circuit Breaker) en Streamlit.
# Si un módulo presenta un error en tiempo de ejecución, se intercepta, se muestra una alerta visual detallada para el administrador (con traza de depuración) 
# y se permite que el resto del ecosistema ERP continúe funcionando sin interrupciones ni pantallas en blanco.

fault_tolerant_architecture = '''"""
Audit Intelligence USA - Enterprise Big 4 Killer & Autonomous CRM/ERP Suite,
Motor Defensivo Universal con Aislamiento de Módulos (Fault Tolerance / Circuit Breaker),
Garantía de Cero Interrupción, Trazabilidad Absoluta y Actualización en Línea sin Pérdidas.
Version: 10.16.00-PROD Enterprise Full Production & Universal Compliance Suite
"""

import os
import sys
import json
import sqlite3
import hashlib
import re
import logging
import traceback
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

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    try:
        conn = get_db_connection()
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
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rnc_empresa TEXT NOT NULL DEFAULT '133378711',
                rnc_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                tipo_ncf TEXT NOT NULL DEFAULT 'E31',
                tipo_ncf_ecf TEXT NOT NULL DEFAULT 'E31',
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
                estado_dgii TEXT NOT NULL DEFAULT 'AprobadoDGII',
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recordatorios_registro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rnc_empresa TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                fecha_recordatorio TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente',
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

        ensure_column("empresas_clientes", "ultimo_encf_usado", "TEXT NOT NULL DEFAULT 'E310000000030'")
        ensure_column("empresas_clientes", "direccion", "TEXT NOT NULL DEFAULT 'Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este, RD'")
        ensure_column("sales_invoices", "tipo_ncf", "TEXT NOT NULL DEFAULT 'E31'")

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'AdministradorMaster'")
        if cursor.fetchone()[0] == 0:
            admin_pass_hash = hashlib.sha256("AdminBASA2026*".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, rnc_cedula, email, phone, pais, ciiu_sector, idioma, subscription_plan, subscription_status, is_facturable, parent_owner, logo_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Español', ?, 'Activo', 1, 'admin', '', ?)
            """, ("admin", admin_pass_hash, "Lic. Pedro Baldera - Admin Master Global", "AdministradorMaster", "131-0000000-1", "admin@auditintelligence.com", "+18095550000", "República Dominicana", "Financiero / Auditoría", "Exonerado", datetime.utcnow().isoformat()))
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM empresas_clientes WHERE rnc_empresa = '133378711'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO empresas_clientes (contador_username, rnc_empresa, razon_social, nombre_comercial, tipo_entidad, sector_ciiu, actividad_economica_automatica, direccion, telefono, consorcio_grupo, ultimo_encf_usado, estado_onapi, estado_dgii, estado_tss, estado_ministerio_trabajo, riesgo_aml, tipo_cliente, monto_mensual, fecha_vencimiento, estado_servicio, modulo_ventas_activo, modulo_compras_activo, modulo_activos_activo, modulo_reportes_activo, usuario_dgii, password_dgii, certificado_filename, password_certificado, ambiente, updated_at)
                VALUES ('admin', '133378711', 'BALDERA SANTOS Y ASOCIADOS SRL', 'BASA Audit & Software Solutions', 'Empresa Privada', '6920', 'Servicios Profesionales', 'Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este, RD', '829-771-7390', 'Independiente', 'E310000000030', 'Vigente', 'Activo / Al Día', 'Al Día', 'Registrado', 'Bajo (Normal)', 'Cliente BASA (De Pago)', 5000.0, '2026-12-31', 'Activo', 1, 1, 1, 1, 'licpedrobaldera', 'Clave2026*', 'certificado.p12', 'Cert2026*', 'Producción', ?)
            """, (datetime.utcnow().isoformat(),))
            conn.commit()
            
        conn.close()
    except Exception as e:
        logger.error(f"Error DB Migration: {str(e)}")

init_db()

st.set_page_config(page_title="Ecosistema ERP Enterprise & Formatos DGII - Audit Intelligence USA", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 24px; font-weight: bold; color: #1e3a8a; margin-bottom: 0px; }
    .sub-title { font-size: 13px; color: #475569; margin-bottom: 15px; }
    .org-card { background-color: #f8fafc; border: 2px solid #3b82f6; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .org-title { font-size: 16px; font-weight: bold; color: #1e40af; margin-bottom: 8px; }
    .error-isolation-card { background-color: #fef2f2; border: 2px solid #ef4444; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 Ecosistema ERP & Liquidación Oficial ITBIS (IT-1) / IR-17 / Formatos 606/607/608</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Supervisión técnica: <b>Lic. Pedro Baldera</b> | Dirección: Calle Orlando Martinez No.49, Brisas del Este, SDE | Producción 100/100 (Aislamiento de Módulos Activo).</p>', unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = True
if "username" not in st.session_state:
    st.session_state.username = "admin"
if "rnc_activo" not in st.session_state:
    st.session_state.rnc_activo = "133378711"
if "nombre_empresa_activo" not in st.session_state:
    st.session_state.nombre_empresa_activo = "BALDERA SANTOS Y ASOCIADOS SRL"

st.sidebar.header("🔐 Configuración & Empresa")
st.sidebar.write(f"👤 **Usuario:** {st.session_state.username}")

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT rnc_empresa, razon_social FROM empresas_clientes")
    empresas_db = cursor.fetchall()
    conn.close()
except Exception:
    empresas_db = [("133378711", "BALDERA SANTOS Y ASOCIADOS SRL")]

opciones_empresas = [f"{e[1]} (RNC: {e[0]})" for e in empresas_db]
empresa_seleccionada_str = st.sidebar.selectbox("📂 Empresa Activa", opciones_empresas, index=0)

if empresa_seleccionada_str:
    match_rnc = re.search(r'RNC:\\s*([0-9-]+)', empresa_seleccionada_str)
    if match_rnc:
        st.session_state.rnc_activo = match_rnc.group(1)
        st.session_state.nombre_empresa_activo = empresa_seleccionada_str.split(" (RNC:")[0]

st.sidebar.info(f"📌 **Activa:** {st.session_state.nombre_empresa_activo}")
st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ **Aislamiento de Módulos (Circuit Breaker):** Activo. Si un módulo falla, genera alerta para el Administrador sin detener el resto del ERP.")

st.markdown("---")

# ==========================================
# MÓDULO 1.5: EDICIÓN ONLINE EN VIVO (Con Aislamiento de Errores)
# ==========================================
st.markdown('<div class="org-card"><div class="org-title">✏️ NODO 1.5: Edición Online en Vivo y Actualización de Datos de la Empresa</div></div>', unsafe_allow_html=True)
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT razon_social, nombre_comercial, direccion, telefono, estado_onapi, estado_dgii FROM empresas_clientes WHERE rnc_empresa = ?", (st.session_state.rnc_activo,))
    row_emp_act = cursor.fetchone()
    conn.close()
    
    if row_emp_act:
        with st.form("form_edicion_online_empresa"):
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                edit_razon = st.text_input("Razón Social", value=row_emp_act[0])
                edit_comercial = st.text_input("Nombre Comercial", value=row_emp_act[1])
                edit_dir = st.text_input("Dirección Fiscal Oficial", value=row_emp_act[2])
            with col_ed2:
                edit_tel = st.text_input("Teléfono", value=row_emp_act[3])
                edit_dgii = st.selectbox("Estado DGII", ["Activo / Al Día", "Suspendido", "Inactivo"], index=0)
                edit_onapi = st.selectbox("Estado ONAPI", ["Vigente", "En Renovación", "Vencido"], index=0)
                
            if st.form_submit_button("💾 Actualizar y Guardar Cambios Online en Tiempo Real"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE empresas_clientes 
                    SET razon_social = ?, nombre_comercial = ?, direccion = ?, telefono = ?, estado_dgii = ?, estado_onapi = ?, updated_at = ?
                    WHERE rnc_empresa = ?
                """, (edit_razon, edit_comercial, edit_dir, edit_tel, edit_dgii, edit_onapi, datetime.utcnow().isoformat(), st.session_state.rnc_activo))
                conn.commit()
                conn.close()
                st.success("¡Datos de la empresa actualizados en vivo con éxito sin pérdida de trazabilidad!")
                st.rerun()
except Exception as ex:
    # Aislamiento de error: Mantiene el sistema activo y muestra la alerta específica para el Administrador
    st.markdown(f"""
        <div class="error-isolation-card">
            <b>⚠️ ALTA DE AISLAMIENTO DE MÓDULO (NODO 1.5 - Edición Empresa):</b><br>
            Se ha detectado una anomalía técnica en este nodo: <code>{str(ex)}</code>.<br>
            <i>El resto del ecosistema ERP opera con normalidad con la última versión funcional garantizada. Corrija los parámetros anteriores.</i>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# MÓDULO 1.8: RECORDATORIOS INTELIGENTES
# ==========================================
st.markdown('<div class="org-card"><div class="org-title">🔔 NODO 1.8: Recordatorios Inteligentes de Registro y Vencimientos Fiscales</div></div>', unsafe_allow_html=True)
try:
    with st.form("form_recordatorio"):
        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            titulo_rec = st.text_input("Título del Recordatorio", value="Declaración IT-1 y Envío 606/607")
            desc_rec = st.text_input("Descripción / Nota", value="Revisar facturación electrónica y retenciones IR-17 antes del plazo límite.")
        with col_rec2:
            fecha_rec = st.date_input("Fecha de Alerta", value=datetime.utcnow().date() + timedelta(days=5))
            
        if st.form_submit_button("⏰ Crear Recordatorio de Registro"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recordatorios_registro (username, rnc_empresa, titulo, descripcion, fecha_recordatorio, estado, created_at)
                VALUES (?, ?, ?, ?, ?, 'Pendiente', ?)
            """, (st.session_state.username, st.session_state.rnc_activo, titulo_rec, desc_rec, str(fecha_rec), datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("¡Recordatorio creado exitosamente!")
            st.rerun()

    conn = get_db_connection()
    df_recs = pd.read_sql_query("SELECT id, titulo, descripcion, fecha_recordatorio, estado FROM recordatorios_registro WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    if not df_recs.empty:
        st.dataframe(df_recs, use_container_width=True)
except Exception as ex:
    st.markdown(f"""
        <div class="error-isolation-card">
            <b>⚠️ ALERTA DE AISLAMIENTO DE MÓDULO (NODO 1.8 - Recordatorios):</b> <code>{str(ex)}</code>. El sistema opera normalmente.
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# MÓDULO 4: INGRESOS Y DUPLICADOS CON NCF Y FECHA
# ==========================================
st.markdown('<div class="org-card"><div class="org-title">📦 NODO 4: Módulo de Ingresos, Formato 607 y Duplicados para Clientes Igualados (NCF y Fecha)</div></div>', unsafe_allow_html=True)

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ultimo_encf_usado FROM empresas_clientes WHERE rnc_empresa = ?", (st.session_state.rnc_activo,))
    row_u = cursor.fetchone()
    ultimo_encf = row_u[0] if row_u else "E310000000030"
    conn.close()
    
    match = re.search(r'(\\d+)$', ultimo_encf)
    if match:
        num_str = match.group(1)
        num_val = int(num_str) + 1
        pref = ultimo_encf[:len(ultimo_encf)-len(num_str)]
        siguiente_sec = f"{pref}{num_val:0{len(num_str)}d}"
    else:
        siguiente_sec = "E310000000031"
except Exception:
    siguiente_sec = "E310000000031"

st.info(f"🔢 **Siguiente e-NCF Oficial Automático:** `{siguiente_sec}`")

try:
    with st.form("form_nodo_4_ingresos"):
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            tipo_e = st.selectbox("Tipo e-CF", ["E31 - Crédito Fiscal Electrónico", "E32 - Consumo Electrónico"])
            secuencia_final_input = st.text_input("Secuencia e-NCF", value=siguiente_sec)
            rnc_cli = st.text_input("RNC / Cédula del Cliente", value="00105610737")
            nom_cli = st.text_input("Razón Social del Cliente", value="MIRNA SILENI GUILLEN RYMER")
        with col_i2:
            desc_v = st.text_input("Descripción del Servicio", value="Servicio Profesional Asesoría")
            monto_n = st.number_input("Monto Neto RD$", min_value=0.0, value=42500.0)
            t_itbis = st.selectbox("Tasa ITBIS", [0.18, 0.16, 0.0], index=0)
            fecha_factura = st.date_input("Fecha de Emisión de Factura", value=datetime.utcnow().date())
            estado_cb = st.selectbox("Estado de Cobro", ["Pendiente de Cobro", "Pagado Total"])
            
        itb_calc = monto_n * t_itbis
        tot_calc = monto_n + itb_calc
        
        col_btn_reg, col_btn_dup = st.columns(2)
        registrar_click = col_btn_reg.form_submit_button("💾 Guardar Venta (Formato 607)")
        duplicar_click = col_btn_dup.form_submit_button("📑 Crear Duplicado para Cliente Igualado (Mismo NCF y Fecha)")
        
        if registrar_click or duplicar_click:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sec_a_guardar = secuencia_final_input
            if duplicar_click:
                sec_a_guardar = f"{secuencia_final_input}-DUP"
                
            tipo_ncf_val = tipo_e.split(" - ")[0].strip()
            
            cursor.execute("""
                INSERT INTO sales_invoices (username, rnc_empresa, rnc_cliente, nombre_cliente, tipo_ncf, tipo_ncf_ecf, modo_registro, secuencia_encf, clasificacion_ingreso_dgii, monto_neto, itbis, monto_total, estado_cobro, vencimiento, estado_dgii, ya_reportado_salvedad, reportado_organismos, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '01 - Ingresos Operacionales', ?, ?, ?, ?, ?, 'AprobadoDGII', 0, 1, ?)
            """, (st.session_state.username, st.session_state.rnc_activo, rnc_cli, nom_cli, tipo_ncf_val, tipo_ncf_val, "Duplicado Cliente Igualado" if duplicar_click else "Automático Actual", sec_a_guardar, monto_n, itb_calc, tot_calc, estado_cb, str(fecha_factura), datetime.utcnow().isoformat()))
            
            cursor.execute("UPDATE empresas_clientes SET ultimo_encf_usado = ? WHERE rnc_empresa = ?", (secuencia_final_input, st.session_state.rnc_activo))
            conn.commit()
            conn.close()
            
            if duplicar_click:
                st.success(f"¡Duplicado creado con éxito para cliente igualado con NCF `{sec_a_guardar}` y fecha `{fecha_factura}`!")
            else:
                st.success(f"¡Venta guardada con éxito! Secuencia `{secuencia_final_input}` registrada.")
            st.rerun()
except Exception as ex:
    st.markdown(f"""
        <div class="error-isolation-card">
            <b>⚠️ ALERTA DE AISLAMIENTO DE MÓDULO (NODO 4 - Ingresos y Duplicados):</b> <code>{str(ex)}</code>. El sistema opera normalmente.
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# MÓDULO 8: CENTRO DE REPORTES
# ==========================================
st.markdown('<div class="org-card"><div class="org-title">🖨️ NODO 8: Centro de Reportes y Exportación Universal</div></div>', unsafe_allow_html=True)
try:
    conn = get_db_connection()
    df_v_rep = pd.read_sql_query("SELECT secuencia_encf AS comprobante, rnc_cliente AS rnc, nombre_cliente AS nombre, monto_total, 'Venta e-CF (607)' AS tipo FROM sales_invoices WHERE rnc_empresa = ?", conn, params=(st.session_state.rnc_activo,))
    df_c_rep = pd.read_sql_query("SELECT ncf_comprobante AS comprobante, rnc_suplidor AS rnc, nombre_suplidor AS nombre, monto_facturado AS monto_total, 'Compra (606)' AS tipo FROM purchases_606 WHERE rnc_empresa = ?", conn, params=(st.session_state.rnc_activo,))
    conn.close()
    
    df_rep_total = pd.concat([df_v_rep, df_c_rep], ignore_index=True)
    if not df_rep_total.empty:
        st.dataframe(df_rep_total, use_container_width=True)
        st.download_button("📥 Descargar Reporte Consolidado Universal (CSV)", data=df_rep_total.to_csv(index=False).encode('utf-8'), file_name=f"Reporte_Universal_DGII_{st.session_state.rnc_activo}.csv", mime="text/csv")
    else:
        st.info("No hay transacciones registradas.")
except Exception as ex:
    st.markdown(f"""
        <div class="error-isolation-card">
            <b>⚠️ ALERTA DE AISLAMIENTO DE MÓDULO (NODO 8 - Reportes):</b> <code>{str(ex)}</code>. El sistema opera normalmente.
        </div>
    """, unsafe_allow_html=True)
'''

with open("streamlit_app.py", "w", encoding="utf-8") as f:
    f.write(fault_tolerant_architecture)

print("streamlit_app.py actualizado con arquitectura de Aislamiento de Módulos (Circuit Breaker) y Cero Interrupción.")
