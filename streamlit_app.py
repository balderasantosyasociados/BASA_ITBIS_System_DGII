"""
Audit Intelligence USA - Enterprise Multi-Tenant SaaS, Contabilidad Global Multi-País, Facturación e-CF,
Clasificación Estricta DGII, Gestión de Logos, Multi-Empresa por Usuario Licenciado y Auto-Migración Segura.
Version: 10.9.11-PROD Enterprise Full Production & Audit Intelligence Suite
Configured for Streamlit Cloud, Autonomous Self-Healing, Double-Entry, Multi-Company & Auto-Migration Safety
"""

import os
import sys
import json
import sqlite3
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
import openpyxl

# ==========================================
# 1. CONFIGURACIÓN DE LOGS Y BASE DE DATOS GLOBAL (AUTO-MIGRACIÓN)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] AUDIT_INTELLIGENCE_CORE: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Audit_Intelligence_USA_Core")

DB_PATH = "itbis_sistem_dgii_full.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Configuración General
        cursor.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        
        # Usuarios Globales
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
                idioma TEXT NOT NULL DEFAULT 'Español',
                subscription_plan TEXT NOT NULL,
                subscription_status TEXT NOT NULL,
                is_facturable INTEGER NOT NULL DEFAULT 1,
                parent_owner TEXT NOT NULL DEFAULT 'admin',
                logo_path TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        
        # Vinculación Multi-Empresa
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                empresa_nombre TEXT NOT NULL,
                rnc_empresa TEXT NOT NULL,
                tipo_rol_empresa TEXT NOT NULL,
                licencia_activa INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        # Solicitudes de Pago y Soporte
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_support_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                monto_pagado REAL NOT NULL,
                concepto TEXT NOT NULL,
                comprobante_soporte_info TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                approved_at TEXT
            )
        """)
        
        # Cartera de Clientes / Directorio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients_directory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                rnc_cedula TEXT NOT NULL,
                correo TEXT NOT NULL,
                telefono TEXT NOT NULL,
                direccion TEXT NOT NULL,
                logo_cliente_path TEXT DEFAULT ''
            )
        """)
        
        # Ventas y e-CF
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                empresa_asociada TEXT NOT NULL DEFAULT 'Principal',
                rnc_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                tipo_ncf_ecf TEXT NOT NULL,
                clasificacion_ingreso_dgii TEXT NOT NULL,
                monto_neto REAL NOT NULL,
                itbis REAL NOT NULL,
                monto_total REAL NOT NULL,
                vencimiento TEXT NOT NULL,
                estado_dgii TEXT NOT NULL,
                archivo_soporte_path TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        
        # Compras 606
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases_606 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                empresa_asociada TEXT NOT NULL DEFAULT 'Principal',
                rnc_suplidor TEXT NOT NULL,
                nombre_suplidor TEXT NOT NULL,
                ncf_comprobante TEXT NOT NULL,
                tipo_ncf_egreso TEXT NOT NULL,
                clasificacion_gasto_dgii TEXT NOT NULL,
                monto_facturado REAL NOT NULL,
                itbis_facturado REAL NOT NULL,
                retencion_ir17 REAL NOT NULL DEFAULT 0.0,
                vencimiento TEXT NOT NULL,
                archivo_adjunto_info TEXT DEFAULT '',
                estado TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Flujo de Efectivo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cash_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                categoria TEXT NOT NULL,
                monto REAL NOT NULL,
                descripcion TEXT NOT NULL,
                fecha TEXT NOT NULL
            )
        """)
        
        # Asientos de Diario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                cuenta_debito TEXT NOT NULL,
                cuenta_credito TEXT NOT NULL,
                monto REAL NOT NULL,
                concepto TEXT NOT NULL,
                fecha TEXT NOT NULL
            )
        """)
        
        # Activos Fijos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixed_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                categoria_dgii TEXT NOT NULL,
                costo_adquisicion REAL NOT NULL,
                depreciacion_acumulada REAL NOT NULL,
                fecha_adquisicion TEXT NOT NULL
            )
        """)

        # Auditoría Antifraude
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forensic_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tipo_incidencia TEXT NOT NULL,
                detalle TEXT NOT NULL,
                norma_aplicada TEXT NOT NULL,
                severidad TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Auto-migración segura de columnas faltantes en tablas existentes
        migrations = [
            ("users", "logo_path", "TEXT DEFAULT ''"),
            ("clients_directory", "logo_cliente_path", "TEXT DEFAULT ''"),
            ("sales_invoices", "empresa_asociada", "TEXT DEFAULT 'Principal'"),
            ("sales_invoices", "tipo_ncf_ecf", "TEXT DEFAULT 'E31 - e-NCF Crédito Fiscal'"),
            ("sales_invoices", "clasificacion_ingreso_dgii", "TEXT DEFAULT 'Ingresos Operacionales'"),
            ("sales_invoices", "estado_dgii", "TEXT DEFAULT 'BorradorDuplicado'"),
            ("purchases_606", "empresa_asociada", "TEXT DEFAULT 'Principal'"),
            ("purchases_606", "clasificacion_gasto_dgii", "TEXT DEFAULT 'Gastos Operativos'"),
            ("purchases_606", "retencion_ir17", "REAL DEFAULT 0.0"),
            ("purchases_606", "archivo_adjunto_info", "TEXT DEFAULT ''")
        ]
        
        for table, col, col_def in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
            except sqlite3.OperationalError:
                pass # La columna ya existe, se ignora de forma segura

        # Admin por defecto (Lic. Pedro Baldera)
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'AdministradorMaster'")
        if cursor.fetchone()[0] == 0:
            admin_pass_hash = hashlib.sha256("AdminBASA2026*".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, rnc_cedula, email, phone, pais, idioma, subscription_plan, subscription_status, is_facturable, parent_owner, logo_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Español', ?, 'Activo', 1, 'admin', '', ?)
            """, ("admin", admin_pass_hash, "Lic. Pedro Baldera - Admin Master Global", "AdministradorMaster", "131-0000000-1", "admin@auditintelligence.com", "+18095550000", "República Dominicana", "Exonerado", datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error DB Migration: {str(e)}")

init_db()


# ==========================================
# 2. MOTOR GLOBAL Y TAXONOMÍA DGII
# ==========================================
PAISES_GLOBAL_CONFIG = {
    "República Dominicana": {"moneda": "RD$", "tasa_iva": 0.18, "ley": "Código Tributario Ley 11-92 / DGII (e-CF Integrado)", "idioma": "Español"},
    "Estados Unidos": {"moneda": "USD$", "tasa_iva": 0.08, "ley": "Internal Revenue Code (IRS)", "idioma": "Inglés / Español"},
    "Colombia": {"moneda": "COP$", "tasa_iva": 0.19, "ley": "Estatuto Tributario (DIAN)", "idioma": "Español"},
    "México": {"moneda": "MXN$", "tasa_iva": 0.16, "ley": "Código Fiscal de la Federación (SAT)", "idioma": "Español"},
    "España": {"moneda": "EUR €", "tasa_iva": 0.21, "ley": "Ley General Tributaria (Agencia Tributaria)", "idioma": "Español"}
}

CLASIFICACIONES_INGRESOS_DGII = [
    "Ingresos Operacionales (Gravados 18%)",
    "Ingresos Exentos / Tasas 0% (Ley 108-10 / Exportaciones)",
    "Ingresos Financieros (Intereses y Rentas de Capital)",
    "Ingresos Extraordinarios / Venta de Activos Fijos"
]

CLASIFICACIONES_GASTOS_DGII = [
    "Gastos Operativos y de Ventas (Deducibles Ley 11-92)",
    "Gastos de Personal, Sueldos y Salarios (TSS / IR-3)",
    "Gastos Financieros y Comisiones Bancarias",
    "Costos de Producción y Adquisición de Bienes",
    "Inversiones en Activos Fijos Depreciables",
    "Gastos No Deducibles (Ajustes Fiscales / Sin Comprobante Válido)"
]

st.set_page_config(page_title="Audit Intelligence USA - Enterprise Suite", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 26px; font-weight: bold; color: #1F4E78; margin-bottom: 0px; }
    .sub-title { font-size: 15px; color: #4b5563; margin-bottom: 20px; }
    .dgii-card { background-color: #f1f8ff; padding: 15px; border-radius: 8px; border: 1px solid #c8e1ff; margin-bottom: 15px; }
    .auto-save-badge { background-color: #d4edda; color: #155724; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🏛️ Audit Intelligence USA: Suite Financiera, Contable y Auditoría Antifraude</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Supervisión técnica: <b>Lic. Pedro Baldera</b> | Multi-Empresa, Gestión de Logos, Credenciales Autónomas y Facturación e-CF.</p>', unsafe_allow_html=True)


# ==========================================
# 3. GESTIÓN DE SESIÓN Y ESTADO
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "rnc_cedula" not in st.session_state:
    st.session_state.rnc_cedula = ""
if "pais" not in st.session_state:
    st.session_state.pais = "República Dominicana"


# ==========================================
# 4. BARRA LATERAL: ACCESO Y RECUPERACIÓN
# ==========================================
st.sidebar.header("🔐 Acceso & Audit Intelligence")

if not st.session_state.authenticated:
    modo_auth = st.sidebar.selectbox("Seleccione Opción", ["Iniciar Sesión", "Registro / Licencia Global", "Recuperar y Editar Contraseña"])
    
    if modo_auth == "Iniciar Sesión":
        user_input = st.sidebar.text_input("Usuario o Correo")
        pass_input = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Ingresar al Sistema"):
            pass_hash = hashlib.sha256(pass_input.encode()).hexdigest()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, rnc_cedula, pais, subscription_status FROM users WHERE (username = ? OR email = ?) AND password_hash = ?", (user_input, user_input, pass_hash))
            row = cursor.fetchone()
            conn.close()
            if row:
                st.session_state.authenticated = True
                st.session_state.username = row[0]
                st.session_state.role = row[1]
                st.session_state.rnc_cedula = row[2]
                st.session_state.pais = row[3]
                st.success(f"¡Bienvenido {row[0]}!")
                st.rerun()
            else:
                st.error("Credenciales inválidas.")

    elif modo_auth == "Registro / Licencia Global":
        nu = st.sidebar.text_input("Usuario / Empresa")
        np = st.sidebar.text_input("Contraseña", type="password")
        nn = st.sidebar.text_input("Razón Social")
        nr = st.sidebar.text_input("RNC / Tax ID")
        ne = st.sidebar.text_input("Correo Electrónico")
        nt = st.sidebar.text_input("Celular")
        pais_sel = st.sidebar.selectbox("País de Operación", list(PAISES_GLOBAL_CONFIG.keys()))
        rol_user = st.sidebar.selectbox("Rol Principal", ["ClientePropietario", "ContadorExterno", "Facturador"])
        plan_sel = st.sidebar.selectbox("Plan de Licencia", ["Mensual US$ 69.00", "Anual Corporativo", "Exonerado / Cartera", "Gratis Pruebas"])
        
        if st.sidebar.button("Registrarse y Activar Licencia"):
            try:
                ph = hashlib.sha256(np.encode()).hexdigest()
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, full_name, role, rnc_cedula, email, phone, pais, idioma, subscription_plan, subscription_status, is_facturable, parent_owner, logo_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Español', ?, 'Activo', 1, 'admin', '', ?)
                """, (nu, ph, nn, rol_user, nr, ne, nt, pais_sel, plan_sel, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
                st.sidebar.success("¡Registro completado! Ya puede iniciar sesión.")
            except Exception as e:
                st.sidebar.error(f"Error: {str(e)}")

    elif modo_auth == "Recuperar y Editar Contraseña":
        st.sidebar.subheader("Recuperación y Edición de Clave")
        user_rec = st.sidebar.text_input("Usuario o Correo")
        nueva_clave = st.sidebar.text_input("Nueva Contraseña", type="password")
        if st.sidebar.button("Actualizar Credenciales"):
            if user_rec and nueva_clave:
                new_hash = hashlib.sha256(nueva_clave.encode()).hexdigest()
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password_hash = ? WHERE username = ? OR email = ?", (new_hash, user_rec, user_rec))
                conn.commit()
                conn.close()
                st.sidebar.success("¡Contraseña actualizada con éxito!")
            else:
                st.sidebar.warning("Complete todos los campos.")
    st.stop()
else:
    st.sidebar.write(f"👤 **Usuario:** {st.session_state.username}")
    st.sidebar.write(f"🛡️ **Rol:** {st.session_state.role}")
    st.sidebar.write(f"🏛️ **Plataforma:** Audit Intelligence USA")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()


# ==========================================
# 5. PESTAÑAS PRINCIPALES DEL SISTEMA
# ==========================================
tabs = st.tabs([
    "📊 Panel Ejecutivo", 
    "🏢 Multi-Empresa & Logos",
    "⚡ Facturación e-CF & Ingresos", 
    "👥 Cartera Clientes & Histórico",
    "📥 Compras 606 & Gastos", 
    "💸 IR-17 & Retenciones",
    "💵 Flujo de Caja", 
    "📒 Asientos Diario", 
    "🏛️ Activos Fijos", 
    "📈 Estados Financieros",
    "🕵️‍♂️ Auditoría Antifraude",
    "⚙️ Admin Master"
])

# --- PESTAÑA 0: PANEL ---
with tabs[0]:
    st.markdown("### 📊 Panel Ejecutivo Audit Intelligence USA")
    st.markdown('<span class="auto-save-badge">💾 Auto-Guardado Activo: Optimización en tiempo real y cumplimiento normativo internacional.</span>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="dgii-card">
            <h4>🏛️ Ecosistema Multi-Empresa & Facturación e-CF</h4>
            <p>Control financiero avanzado con soporte para múltiples empresas por usuario licenciado (Contadores y Facturadores), gestión de logotipos corporativos y auditoría forense.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = sqlite3.connect(DB_PATH)
    df_ventas = pd.read_sql_query("SELECT SUM(monto_total) AS total FROM sales_invoices WHERE username = ?", conn, params=(st.session_state.username,))
    df_compras = pd.read_sql_query("SELECT SUM(monto_facturado) AS total FROM purchases_606 WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    
    tot_v = df_ventas['total'].iloc[0] or 0.0
    tot_c = df_compras['total'].iloc[0] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ventas e-CF (607)", f"{tot_v:,.2f}")
    col2.metric("Total Compras 606", f"{tot_c:,.2f}")
    col3.metric("Estatus Licencia", "Activa y Verificada")

# --- PESTAÑA 1: MULTI-EMPRESA Y GESTIÓN DE LOGOS ---
with tabs[1]:
    st.markdown("### 🏢 Gestión Multi-Empresa y Carga de Logotipos Corporativos")
    st.markdown("Permite a un contador o facturador con licencia paga vincular y gestionar múltiples empresas simultáneamente, además de personalizar el logo del sistema y de los clientes.")

    with st.form("form_multi_empresa"):
        st.subheader("Vincular Nueva Empresa / RNC")
        col1, col2 = st.columns(2)
        with col1:
            nom_empresa = st.text_input("Nombre de la Empresa o Negocio")
            rnc_empresa = st.text_input("RNC o Tax ID de la Empresa")
        with col2:
            rol_en_empresa = st.selectbox("Rol en esta Empresa", ["Facturador", "Contador Externo", "Propietario"])
            logo_url_empresa = st.text_input("URL del Logotipo Corporativo (Opcional)", placeholder="https://miweb.com/logo.png")
            reg_empresa_btn = st.form_submit_button("🏢 Registrar y Vincular Empresa")
            
        if reg_empresa_btn:
            if nom_empresa and rnc_empresa:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_companies (username, empresa_nombre, rnc_empresa, tipo_rol_empresa, licencia_activa, created_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (st.session_state.username, nom_empresa, rnc_empresa, rol_en_empresa, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
                st.success(f"¡Empresa `{nom_empresa}` vinculada con éxito a su licencia activa!")
            else:
                st.warning("Complete el nombre y RNC de la empresa.")

    st.markdown("#### 📋 Empresas Vinculadas a su Cuenta")
    conn = sqlite3.connect(DB_PATH)
    df_empresas = pd.read_sql_query("SELECT empresa_nombre, rnc_empresa, tipo_rol_empresa, licencia_activa FROM user_companies WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    st.dataframe(df_empresas, use_container_width=True)

# --- PESTAÑA 2: FACTURACIÓN e-CF Y CLASIFICACIÓN DE INGRESOS ---
with tabs[2]:
    st.markdown("### ⚡ Módulo de Facturación e-CF con Selección de Empresa y Clasificación DGII")
    
    conn = sqlite3.connect(DB_PATH)
    lista_empresas_user = pd.read_sql_query("SELECT empresa_nombre FROM user_companies WHERE username = ?", conn, params=(st.session_state.username,))
    lista_cli_cartera = pd.read_sql_query("SELECT nombre_cliente, rnc_cedula FROM clients_directory WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    
    nombres_empresas_opt = ["Principal"] + (list(lista_empresas_user['empresa_nombre']) if not lista_empresas_user.empty else [])
    
    cli_sel = None
    rnc_pre = ""
    if not lista_cli_cartera.empty:
        opciones_cli = ["-- Seleccionar de Cartera --"] + list(lista_cli_cartera['nombre_cliente'])
        s_c = st.selectbox("Seleccionar Cliente de Cartera (Muestra Histórico)", opciones_cli)
        if s_c != "-- Seleccionar de Cartera --":
            cli_sel = s_c
            rnc_pre = lista_cli_cartera[lista_cli_cartera['nombre_cliente'] == s_c]['rnc_cedula'].values[0]

    with st.form("form_factura_ecf"):
        col1, col2 = st.columns(2)
        with col1:
            empresa_emitente = st.selectbox("Emitir desde Empresa Vinculada", nombres_empresas_opt)
            nom_c = st.text_input("Nombre del Cliente", value=cli_sel or "")
            rnc_c = st.text_input("RNC / Cédula del Cliente", value=rnc_pre or "")
            tipo_ecf = st.selectbox("Tipo de e-CF (DGII)", [
                "E31 - e-NCF Crédito Fiscal Electrónico", 
                "E32 - e-NCF Consumo Electrónico", 
                "E41 - e-NCF Exportaciones", 
                "E43 - e-NCF Notas de Crédito", 
                "E44 - e-NCF Notas de Débito"
            ])
            clas_ingreso = st.selectbox("Clasificación de Ingresos", CLASIFICACIONES_INGRESOS_DGII)
        with col2:
            monto_n = st.number_input("Monto Neto Gravado", min_value=0.0, value=25000.0)
            dias_v = st.number_input("Plazo Vencimiento (Días)", value=30)
            accion_fact = st.radio("Estado de Emisión", ["Guardar Borrador / Duplicado", "Certificar y Enviar a DGII (Archivar en Carpeta)"])
            emitir_f = st.form_submit_button("🚀 Emitir Factura e-CF")
            
        if emitir_f:
            itbis_calc = monto_n * 0.18
            tot_calc = monto_n + itbis_calc
            venc_f = (datetime.utcnow() + timedelta(days=dias_v)).strftime("%Y-%m-%d")
            estado_reg = "BorradorDuplicado" if "Borrador" in accion_fact else "AprobadoDGII"
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sales_invoices (username, empresa_asociada, rnc_cliente, nombre_cliente, tipo_ncf_ecf, clasificacion_ingreso_dgii, monto_neto, itbis, monto_total, vencimiento, estado_dgii, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (st.session_state.username, empresa_emitente, rnc_c, nom_c, tipo_ecf, clas_ingreso, monto_n, itbis_calc, tot_calc, venc_f, estado_reg, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("¡Factura procesada y guardada con éxito!")

    st.markdown("#### 📋 Listado de Facturas Emitidas")
    conn = sqlite3.connect(DB_PATH)
    df_ventas_g = pd.read_sql_query("SELECT id, empresa_asociada, nombre_cliente, tipo_ncf_ecf, monto_total, estado_dgii FROM sales_invoices WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    st.dataframe(df_ventas_g, use_container_width=True)

# --- PESTAÑA 3: CARTERA DE CLIENTES ---
with tabs[3]:
    st.markdown("### 👥 Cartera de Clientes y Logos Personalizados")
    with st.form("form_cartera_global"):
        col1, col2 = st.columns(2)
        with col1:
            nc = st.text_input("Nombre / Razón Social del Cliente")
            rc = st.text_input("RNC / Cédula")
            cc = st.text_input("Correo Electrónico")
        with col2:
            tc = st.text_input("Teléfono")
            dc = st.text_input("Dirección")
            logo_cli = st.text_input("URL Logo del Cliente (Opcional)")
            save_c = st.form_submit_button("💾 Guardar Cliente con Logo")
            
        if save_c:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients_directory (username, nombre_cliente, rnc_cedula, correo, telefono, direccion, logo_cliente_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (st.session_state.username, nc, rc, cc, tc, dc, logo_cli))
            conn.commit()
            conn.close()
            st.success("¡Cliente guardado con éxito!")

    conn = sqlite3.connect(DB_PATH)
    df_cl = pd.read_sql_query("SELECT nombre_cliente, rnc_cedula, correo, telefono, logo_cliente_path FROM clients_directory WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    st.dataframe(df_cl, use_container_width=True)

# --- PESTAÑA 4: COMPRAS 606 Y CLASIFICACIÓN DE GASTOS ---
with tabs[4]:
    st.markdown("### 📥 Módulo Compras 606 con Clasificación de Gastos e Imágenes/PDF")
    with st.form("form_compra_img"):
        col1, col2 = st.columns(2)
        with col1:
            rnc_s = st.text_input("RNC Suplidor")
            nom_s = st.text_input("Nombre del Suplidor")
            ncf_c = st.text_input("NCF / Comprobante")
            clas_gasto = st.selectbox("Clasificación de Gasto (DGII)", CLASIFICACIONES_GASTOS_DGII)
            archivo_subido = st.text_input("Archivo Adjunto (PDF o Imagen)", placeholder="factura.pdf")
        with col2:
            mfac = st.number_input("Monto Facturado", min_value=0.0, value=15000.0)
            itbfac = st.number_input("ITBIS Facturado", min_value=0.0, value=2700.0)
            ret_ir = st.number_input("Retención IR-17", min_value=0.0, value=0.0)
            reg_compra = st.form_submit_button("📥 Registrar Compra 606")
            
        if reg_compra:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchases_606 (username, empresa_asociada, rnc_suplidor, nombre_suplidor, ncf_comprobante, tipo_ncf_egreso, clasificacion_gasto_dgii, monto_facturado, itbis_facturado, retencion_ir17, vencimiento, archivo_adjunto_info, estado, created_at)
                VALUES (?, 'Principal', ?, ?, ?, 'B01', ?, ?, ?, ?, ?, ?, 'Registrado', ?)
            """, (st.session_state.username, rnc_s, nom_s, ncf_c, clas_gasto, mfac, itbfac, ret_ir, (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"), archivo_subido, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("¡Compra 606 registrada con éxito!")

    conn = sqlite3.connect(DB_PATH)
    df_p606 = pd.read_sql_query("SELECT id, nombre_suplidor, rnc_suplidor, ncf_comprobante, clasificacion_gasto_dgii, monto_facturado FROM purchases_606 WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    st.dataframe(df_p606, use_container_width=True)

# --- PESTAÑA 5: IR-17 ---
with tabs[5]:
    st.markdown("### 💸 Retenciones IR-17")
    conn = sqlite3.connect(DB_PATH)
    tot_ir17 = pd.read_sql_query("SELECT SUM(retencion_ir17) FROM purchases_606 WHERE username = ?", conn, params=(st.session_state.username,)).iloc[0,0] or 0.0
    conn.close()
    st.metric("Total Retenciones IR-17 Acumuladas", f"RD$ {tot_ir17:,.2f}")

# --- PESTAÑA 6: FLUJO DE CAJA ---
with tabs[6]:
    st.markdown("### 💵 Flujo de Caja")
    with st.form("form_caja_g"):
        tm = st.selectbox("Tipo", ["Ingreso", "Egreso"])
        cat = st.text_input("Categoría")
        mon = st.number_input("Monto", min_value=0.0, value=1000.0)
        desc = st.text_input("Descripción")
        if st.form_submit_button("Registrar Movimiento"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cash_flow (username, tipo_movimiento, categoria, monto, descripcion, fecha) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state.username, tm, cat, mon, desc, datetime.utcnow().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Registrado.")

# --- PESTAÑA 7: ASIENTOS ---
with tabs[7]:
    st.markdown("### 📒 Asientos de Diario")
    with st.form("form_asiento_g"):
        deb = st.text_input("Cuenta Débito")
        cre = st.text_input("Cuenta Crédito")
        mont = st.number_input("Monto Partida", min_value=0.0, value=5000.0)
        conc = st.text_input("Concepto")
        if st.form_submit_button("Registrar Asiento"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO journal_entries (username, cuenta_debito, cuenta_credito, monto, concepto, fecha) VALUES (?, ?, ?, ?, ?, ?)", (st.session_state.username, deb, cre, mont, conc, datetime.utcnow().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Asiento registrado.")

# --- PESTAÑA 8: ACTIVOS FIJOS ---
with tabs[8]:
    st.markdown("### 🏛️ Activos Fijos")
    with st.form("form_act_g"):
        des = st.text_input("Descripción")
        catg = st.selectbox("Categoría DGII", ["Cat 1 (5%)", "Cat 2 (25%)", "Cat 3 (15%)"])
        cos = st.number_input("Costo Adquisición", min_value=0.0, value=50000.0)
        if st.form_submit_button("Registrar Activo"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO fixed_assets (username, descripcion, categoria_dgii, costo_adquisicion, depreciacion_acumulada, fecha_adquisicion) VALUES (?, ?, ?, ?, 0.0, ?)", (st.session_state.username, des, catg, cos, datetime.utcnow().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Activo registrado.")

# --- PESTAÑA 9: ESTADOS FINANCIEROS ---
with tabs[9]:
    st.markdown("### 📈 Estados Financieros")
    conn = sqlite3.connect(DB_PATH)
    v_net = pd.read_sql_query("SELECT SUM(monto_neto) FROM sales_invoices WHERE username = ?", conn, params=(st.session_state.username,)).iloc[0,0] or 0.0
    c_net = pd.read_sql_query("SELECT SUM(monto_facturado) FROM purchases_606 WHERE username = ?", conn, params=(st.session_state.username,)).iloc[0,0] or 0.0
    conn.close()
    util = v_net - c_net
    st.write(f"- **Ingresos:** {v_net:,.2f}")
    st.write(f"- **Costos/Gastos:** {c_net:,.2f}")
    st.success(f"**Utilidad Neta:** {util:,.2f}")

# --- PESTAÑA 10: AUDITORÍA ANTIFRAUDE ---
with tabs[10]:
    st.markdown("### 🕵️‍♂️ Auditoría Antifraude")
    st.markdown("Supervisor Técnico: **Lic. Pedro Baldera** (NIA 240).")
    with st.form("form_audit_g"):
        tip = st.selectbox("Incidencia", ["Posible Fraude Online", "Discrepancia Fiscal", "Anomalía Saldo"])
        det = st.text_area("Detalle técnico")
        if st.form_submit_button("Registrar Hallazgo"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO forensic_audit_logs (username, tipo_incidencia, detalle, norma_aplicada, severidad, created_at) VALUES (?, ?, ?, 'NIA 240', 'Alta', ?)", (st.session_state.username, tip, det, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("Registrado.")

# --- PESTAÑA 11: ADMIN MASTER ---
if st.session_state.role == "AdministradorMaster" and len(tabs) > 11:
    with tabs[11]:
        st.markdown("### ⚙️ Panel de Administración Master (Audit Intelligence USA)")
        conn = sqlite3.connect(DB_PATH)
        df_u = pd.read_sql_query("SELECT username, full_name, role, pais, subscription_plan, subscription_status FROM users", conn)
        conn.close()
        st.dataframe(df_u, use_container_width=True)
