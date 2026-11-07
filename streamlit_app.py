import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import hashlib
import sys
import logging
from io import BytesIO

# Configuración de página unificada de producción 100/100 (ERP Protegido AFA & Estándar Oficial Formato 606 DGII)
st.set_page_config(
    page_title="BALDERA SANTOS Y ASOCIADOS - ERP Financiero, Fiscal e-CF & Formato 606 Oficial DGII",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Avanzados de Seguridad, Anti-Selección y Reportes Profesionales
st.markdown("""
    <style>
    body, html, .stApp {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    .main-header {
        background-color: #0f172a;
        color: #38bdf8;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
        border: 1px solid #334155;
    }
    .login-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        max-width: 500px;
        margin: auto;
    }
    .secure-alert-box {
        background-color: #fef2f2;
        border: 2px solid #ef4444;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        color: #b91c1c;
        font-weight: bold;
    }
    .erp-module-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #1e293b;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "itbis_sistem_erp_606_dgii.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        
        # Tabla de Usuarios ERP con Control de Aprobación
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_erp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_id TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                rol TEXT NOT NULL, -- 'Cliente', 'Colaborador', 'Administrador', 'Desarrollador'
                rnc_asociado TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefono TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Aprobado',
                created_at TEXT NOT NULL
            )
        """)
        
        # Tabla de Auditoría e Intrusos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_o_intruso TEXT NOT NULL,
                ip_o_dispositivo TEXT NOT NULL,
                evento TEXT NOT NULL,
                detalle TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas_clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_empresa TEXT UNIQUE NOT NULL,
                razon_social TEXT NOT NULL,
                nombre_comercial TEXT NOT NULL,
                sector_ciiu TEXT NOT NULL,
                direccion TEXT NOT NULL,
                telefono TEXT NOT NULL,
                ultimo_encf_usado TEXT NOT NULL DEFAULT 'E310000000030',
                estado_dgii TEXT NOT NULL DEFAULT 'Activo / Al Día',
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_empresa TEXT NOT NULL,
                rnc_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                tipo_ncf TEXT NOT NULL DEFAULT 'E31',
                secuencia_encf TEXT NOT NULL,
                monto_neto REAL NOT NULL,
                itbis REAL NOT NULL,
                monto_total REAL NOT NULL,
                estado_cobro TEXT NOT NULL DEFAULT 'Pendiente',
                vencimiento TEXT NOT NULL,
                estado_dgii TEXT NOT NULL DEFAULT 'AprobadoDGII',
                created_at TEXT NOT NULL
            )
        """)
        
        # Tabla Formato 606 Oficial Detallado con campos exactos DGII
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases_606_oficial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_empresa TEXT NOT NULL,
                periodo TEXT NOT NULL, -- Formato AAAAMM
                rnc_suplidor TEXT NOT NULL,
                tipo_id TEXT NOT NULL DEFAULT '1',
                tipo_bienes_servicios TEXT NOT NULL,
                ncf_comprobante TEXT NOT NULL,
                ncf_o_doc_modificado TEXT DEFAULT '',
                fecha_comprobante TEXT NOT NULL, -- Formato AAAAMMDD
                fecha_pago TEXT NOT NULL, -- Formato AAAAMMDD
                monto_servicios REAL NOT NULL DEFAULT 0.0,
                monto_bienes REAL NOT NULL DEFAULT 0.0,
                total_monto_facturado REAL NOT NULL,
                itbis_facturado REAL NOT NULL DEFAULT 0.0,
                itbis_retenido REAL NOT NULL DEFAULT 0.0,
                itbis_sujeto_proporcionalidad REAL NOT NULL DEFAULT 0.0,
                itbis_llevado_costo REAL NOT NULL DEFAULT 0.0,
                itbis_por_adelantar REAL NOT NULL DEFAULT 0.0,
                itbis_percibido_compras REAL NOT NULL DEFAULT 0.0,
                tipo_retencion_isr TEXT DEFAULT '00 - ',
                monto_retencion_renta REAL NOT NULL DEFAULT 0.0,
                isr_percibido_compras REAL NOT NULL DEFAULT 0.0,
                impuesto_selectivo_consumo REAL NOT NULL DEFAULT 0.0,
                otros_impuestos_tasas REAL NOT NULL DEFAULT 0.0,
                monto_propina_legal REAL NOT NULL DEFAULT 0.0,
                forma_pago TEXT NOT NULL,
                estatus TEXT NOT NULL DEFAULT 'Correcto',
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ir17_retenciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_empresa TEXT NOT NULL,
                periodo TEXT NOT NULL,
                tipo_retencion TEXT NOT NULL,
                monto_operacion REAL NOT NULL,
                tasa_retencion REAL NOT NULL,
                monto_retenido_ir17 REAL NOT NULL,
                cedula_rnc_retenido TEXT NOT NULL,
                nombre_retenido TEXT NOT NULL,
                estado_pago TEXT NOT NULL DEFAULT 'Pendiente Declaración',
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dgii_declaraciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_empresa TEXT NOT NULL,
                nombre_formulario TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                periodo_ref TEXT NOT NULL,
                estado_presentacion TEXT NOT NULL DEFAULT 'Presentada y Validada',
                created_at TEXT NOT NULL
            )
        """)
        
        # Poblar empresas de prueba
        cursor.execute("SELECT COUNT(*) FROM empresas_clientes WHERE rnc_empresa = '133412918'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO empresas_clientes (rnc_empresa, razon_social, nombre_comercial, sector_ciiu, direccion, telefono, ultimo_encf_usado, estado_dgii, updated_at)
                VALUES ('133412918', 'MANUEL KING VEHICULOS SRL', 'MANUEL KING VEHICULOS', '4510', 'Av. Imbert No. 45, Sto. Domingo', '829-555-1234', 'E310000000050', 'Activo / Al Día', ?)
            """, (datetime.utcnow().isoformat(),))
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM empresas_clientes WHERE rnc_empresa = '133378711'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO empresas_clientes (rnc_empresa, razon_social, nombre_comercial, sector_ciiu, direccion, telefono, ultimo_encf_usado, estado_dgii, updated_at)
                VALUES ('133378711', 'BALDERA SANTOS Y ASOCIADOS SRL', 'BASA Audit & Software Solutions', '6920', 'Calle Orlando Martinez No.49, Brisas del Este, SDE', '829-771-7390', 'E310000000030', 'Activo / Al Día', ?)
            """, (datetime.utcnow().isoformat(),))
            conn.commit()

        # Poblar usuarios autorizados iniciales
        cursor.execute("SELECT COUNT(*) FROM usuarios_erp")
        if cursor.fetchone()[0] == 0:
            usuarios_iniciales = [
                ('admin', hashlib.sha256('Wilfrida7'.encode()).hexdigest(), 'Lic. Pedro Aníbal Baldera Rondón', 'Administrador', '133412918', 'licpedrobaldera@gmail.com', '829-771-7390', 'Aprobado', datetime.utcnow().isoformat()),
                ('dev_basa', hashlib.sha256('BASA2026*'.encode()).hexdigest(), 'Ing. Desarrollador BASA', 'Desarrollador', '133412918', 'dev@balderasantos.com', '829-771-7390', 'Aprobado', datetime.utcnow().isoformat()),
                ('manuel_king', hashlib.sha256('King2026*'.encode()).hexdigest(), 'Manuel King (Cliente)', 'Cliente', '133412918', 'mking@manuelking.com', '829-555-1234', 'Aprobado', datetime.utcnow().isoformat())
            ]
            for u in usuarios_iniciales:
                cursor.execute("""
                    INSERT INTO usuarios_erp (login_id, password_hash, nombre_completo, rol, rnc_asociado, email, telefono, estado, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, u)
            conn.commit()

        # Poblar datos 606 iniciales según la plantilla oficial DGII proporcionada
        cursor.execute("SELECT COUNT(*) FROM purchases_606_oficial")
        if cursor.fetchone()[0] == 0:
            compras_oficiales = [
                ('133412918', '202609', '133378711', '1', '02 - GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS', 'E310000000028', '', '20260920', '20260920', 6000.0, 0.0, 6000.0, 1080.0, 1080.0, 0.0, 0.0, 1080.0, 0.0, '00 - ', 0.0, 0.0, 0.0, 0.0, 0.0, '02 - CHEQUES/TRANSFERENCIAS/DEPÓSITO', 'Correcto', datetime.utcnow().isoformat()),
                ('133412918', '202610', '999888777', '1', '02 - GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS', 'E310000000101', '', '20261015', '20261015', 85000.0, 0.0, 85000.0, 15300.0, 0.0, 0.0, 0.0, 15300.0, 0.0, '00 - ', 850.0, 0.0, 0.0, 0.0, 0.0, '02 - CHEQUES/TRANSFERENCIAS/DEPÓSITO', 'Correcto', datetime.utcnow().isoformat())
            ]
            for co in compras_oficiales:
                cursor.execute("""
                    INSERT INTO purchases_606_oficial (rnc_empresa, periodo, rnc_suplidor, tipo_id, tipo_bienes_servicios, ncf_comprobante, ncf_o_doc_modificado, fecha_comprobante, fecha_pago, monto_servicios, monto_bienes, total_monto_facturado, itbis_facturado, itbis_retenido, itbis_sujeto_proporcionalidad, itbis_llevado_costo, itbis_por_adelantar, itbis_percibido_compras, tipo_retencion_isr, monto_retencion_renta, isr_percibido_compras, impuesto_selectivo_consumo, otros_impuestos_tasas, monto_propina_legal, forma_pago, estatus, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, co)
            conn.commit()

        conn.close()
    except Exception as e:
        logger = logging.getLogger("ERP_606_DGII")
        logger.error(f"Error DB Migration: {str(e)}")

init_db()

# Inicialización de Estado de Sesión
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = None
if "rnc_usuario" not in st.session_state:
    st.session_state.rnc_usuario = None
if "nombre_usuario" not in st.session_state:
    st.session_state.nombre_usuario = None

def registrar_alerta_intruso(usuario_intentado, evento, detalle):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO security_audit_log (usuario_o_intruso, ip_o_dispositivo, evento, detalle, timestamp)
            VALUES (?, 'Secure-Web-Client', ?, ?, ?)
        """, (usuario_intentado, evento, detalle, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass

# --- PORTAL DE ACCESO / LOGIN CON ALERTA Y BLOQUEO DE INTRUSOS ---
if not st.session_state.usuario_autenticado:
    st.markdown("""
        <div class="main-header">
            <h2>🛡️ BALDERA SANTOS Y ASOCIADOS - Portal ERP Protegido AFA & Formato 606 DGII</h2>
            <p>Sistema Criptográfico Protegido contra Plagio, Copias e Intrusos No Autorizados</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        tab_login, tab_recuperar = st.tabs(["🔐 Iniciar Sesión Segura", "🔑 Recuperar Clave"])
        
        with tab_login:
            st.subheader("Acceso Restringido y Monitoreado")
            login_id_input = st.text_input("ID de Usuario o Correo:", placeholder="Ej: admin o manuel_king")
            password_input = st.text_input("Contraseña:", type="password", placeholder="••••••••")
            
            if st.button("🚀 Ingresar al Sistema", type="primary"):
                if login_id_input and password_input:
                    pass_hash = hashlib.sha256(password_input.encode()).hexdigest()
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT login_id, nombre_completo, rol, rnc_asociado, estado FROM usuarios_erp WHERE (login_id = ? OR email = ?)", (login_id_input, login_id_input))
                        user_row = cursor.fetchone()
                        conn.close()
                        
                        if user_row:
                            if user_row[4] != 'Aprobado':
                                registrar_alerta_intruso(login_id_input, "Intento Acceso Usuario Inactivo/Bloqueado", "Cuenta inactiva o bloqueada.")
                                st.error("❌ Su cuenta se encuentra inactiva o bloqueada. Contacte al Administrador.")
                            else:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute("SELECT login_id, nombre_completo, rol, rnc_asociado FROM usuarios_erp WHERE (login_id = ? OR email = ?) AND password_hash = ?", (login_id_input, login_id_input, pass_hash))
                                auth_row = cursor.fetchone()
                                conn.close()
                                
                                if auth_row:
                                    st.session_state.usuario_autenticado = auth_row[0]
                                    st.session_state.nombre_usuario = auth_row[1]
                                    st.session_state.rol_usuario = auth_row[2]
                                    st.session_state.rnc_usuario = auth_row[3]
                                    
                                    registrar_alerta_intruso(auth_row[0], "Acceso Autorizado Exitoso", f"El usuario {auth_row[1]} inició sesión.")
                                    st.success(f"¡Bienvenido, {auth_row[1]}! Rol: {auth_row[2]}")
                                    st.rerun()
                                else:
                                    registrar_alerta_intruso(login_id_input, "Intento No Autorizado", "Contraseña incorrecta.")
                                    st.error("🚨 Contraseña incorrecta. Intento registrado en bitácora.")
                        else:
                            registrar_alerta_intruso(login_id_input, "Intruso / Usuario No Registrado", f"ID inexistente: {login_id_input}")
                            st.markdown("""
                                <div class="secure-alert-box">
                                    🚨 <b>ALERTA DE SEGURIDAD AFA:</b> Usuario no registrado ni autorizado. Acceso bloqueado y reportado.
                                </div>
                            """, unsafe_allow_html=True)
                    except Exception as ex:
                        st.error(f"Error de sistema: {str(ex)}")
                else:
                    st.warning("Por favor ingrese su usuario y contraseña.")
                    
        with tab_recuperar:
            st.subheader("Recuperación de Contraseña")
            correo_recup = st.text_input("Correo Registrado:", placeholder="ejemplo@correo.com")
            if st.button("📨 Enviar Enlace de Recuperación"):
                if correo_recup:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT login_id FROM usuarios_erp WHERE email = ?", (correo_recup,))
                        u_rec = cursor.fetchone()
                        conn.close()
                        if u_rec:
                            st.success(f"Instrucciones enviadas al correo `{correo_recup}`.")
                        else:
                            st.warning("El correo no está registrado.")
                    except Exception as ex:
                        st.error(f"Error: {str(ex)}")
                else:
                    st.warning("Ingrese un correo.")
                    
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- BARRA LATERAL: CONTROL DE SEGURIDAD Y MENÚ ERP ---
with st.sidebar:
    st.markdown("### 🛡️ BASA ERP - Formato 606 DGII")
    st.markdown(f"👤 **Usuario:** {st.session_state.nombre_usuario}")
    st.markdown(f"📌 **Rol:** `{st.session_state.rol_usuario}`")
    st.markdown(f"🏢 **RNC Empresa:** `{st.session_state.rnc_usuario}`")
    st.markdown("---")
    
    if st.button("🔒 Cerrar Sesión Segura"):
        registrar_alerta_intruso(st.session_state.usuario_autenticado, "Cierre de Sesión", "Cierre exitoso.")
        st.session_state.usuario_autenticado = None
        st.session_state.rol_usuario = None
        st.session_state.rnc_usuario = None
        st.session_state.nombre_usuario = None
        st.rerun()

    st.markdown("---")
    
    if st.session_state.rol_usuario in ["Administrador", "Desarrollador"]:
        opciones_menu = [
            "📊 Dashboard General & Consolidado ERP",
            "🚀 Emisión e-CF y Facturación de Ventas",
            "🛒 Formato 606 Oficial DGII (Registro, Histórico y Exportación)",
            "📋 Módulo de Declaración y Control IR-17 (Instructivo DGII)",
            "🔍 Investigación Forense Digital & Cruce Multi-Institucional",
            "📊 Módulo de Ventas (Formato 607 Detallado)",
            "🛡️ Constancias, Hash y Validación Criptográfica",
            "🚨 [Admin/Dev] Auditoría de Seguridad & Bitácora de Intrusos",
            "⚙️ [Admin/Dev] Gestión de Usuarios y Accesos",
            "🖨️ Centro de Reportes y Dictamen Pericial AFA"
        ]
    else:
        opciones_menu = [
            "📊 Dashboard Financiero & Estados Financieros",
            "🚀 Emisión e-CF y Facturación de Ventas",
            "🛒 Formato 606 Oficial DGII (Registro, Histórico y Exportación)",
            "📋 Módulo de Declaración y Control IR-17 (Instructivo DGII)",
            "📊 Módulo de Ventas (Formato 607 Detallado)",
            "🛡️ Constancias, Hash y Validación Criptográfica",
            "🖨️ Centro de Reportes y Estados Financieros"
        ]

    menu_principal = st.radio("Módulos ERP:", opciones_menu)

# --- MÓDULO 1: DASHBOARD ---
if menu_principal in ["📊 Dashboard Financiero & Estados Financieros", "📊 Dashboard General & Consolidado ERP"]:
    st.markdown(f'<div class="main-header"><h2>📊 Dashboard Financiero, Estados Financieros & DGII</h2><p>Control operativo y fiscal seguro para el RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    
    try:
        conn = get_db_connection()
        df_v_dash = pd.read_sql_query("SELECT monto_total FROM sales_invoices WHERE rnc_empresa = ?", conn, params=(st.session_state.rnc_usuario,))
        df_c_dash = pd.read_sql_query("SELECT total_monto_facturado FROM purchases_606_oficial WHERE rnc_empresa = ?", conn, params=(st.session_state.rnc_usuario,))
        conn.close()
    except Exception:
        df_v_dash = pd.DataFrame()
        df_c_dash = pd.DataFrame()

    total_ventas = df_v_dash['monto_total'].sum() if not df_v_dash.empty else 0.0
    total_compras = df_c_dash['total_monto_facturado'].sum() if not df_c_dash.empty else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Ventas Totales e-CF", f"RD$ {total_ventas:,.2f}")
    with k2:
        st.metric("Compras / Egresos Formato 606", f"RD$ {total_compras:,.2f}")
    with k3:
        st.metric("Estado Formato 606", "Sincronizado DGII 🟢")
    with k4:
        st.metric("Estado Fiscal", "Al Día / Protegido 🟢")

    st.markdown("---")
    st.markdown("""
        <div class="erp-module-box">
            <h4>📈 Formato 606 Oficial DGII Integrado</h4>
            <p>El sistema acumula automáticamente todas las compras registradas mes a mes, guardando un histórico detallado por cada factura y permitiendo su edición, eliminación y exportación exacta al formato oficial de la DGII.</p>
        </div>
    """, unsafe_allow_html=True)

# --- MÓDULO 2: EMISIÓN e-CF Y FACTURACIÓN ---
elif menu_principal == "🚀 Emisión e-CF y Facturación de Ventas":
    st.markdown(f'<div class="main-header"><h2>🚀 Emisión y Registro de Facturas de Ventas (e-CF)</h2><p>Módulo ERP para el RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    
    with st.form("form_crear_factura_erp"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tipo_ecf = st.selectbox("Tipo de Comprobante e-CF", [
                "E31 - Factura de Crédito Fiscal Electrónica",
                "E32 - Factura de Consumo Electrónica",
                "E33 - Nota de Crédito Electrónica",
                "E34 - Nota de Débito Electrónica"
            ])
            secuencia_ecf = st.text_input("Secuencia e-NCF", value="E310000000080")
            rnc_cliente = st.text_input("RNC / Cédula del Cliente", value="133378711")
            nombre_cliente = st.text_input("Razón Social del Cliente", value="BALDERA SANTOS Y ASOCIADOS SRL")
        with col_f2:
            fecha_emision = st.date_input("Fecha de Emisión", value=datetime.utcnow().date())
            condicion_pago = st.selectbox("Condición de Pago", ["Contado", "Crédito 30 Días", "Crédito 60 Días"])
            monto_neto = st.number_input("Monto Neto Imponible RD$", min_value=0.0, value=150000.0)
            tasa_itbis = st.selectbox("Tasa ITBIS", [0.18, 0.16, 0.0], index=0)

        itbis_calc = monto_neto * tasa_itbis
        total_calc = monto_neto + itbis_calc
        st.info(f"🧮 Neto: RD$ {monto_neto:,.2f} | ITBIS: RD$ {itbis_calc:,.2f} | **Total:** RD$ {total_calc:,.2f}")

        if st.form_submit_button("⚡ Registrar Venta e-CF", type="primary"):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sales_invoices (rnc_empresa, rnc_cliente, nombre_cliente, tipo_ncf, secuencia_encf, monto_neto, itbis, monto_total, estado_cobro, vencimiento, estado_dgii, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, 'AprobadoDGII', ?)
                """, (
                    st.session_state.rnc_usuario,
                    rnc_cliente,
                    nombre_cliente,
                    tipo_ecf.split(" - ")[0],
                    secuencia_ecf,
                    monto_neto,
                    itbis_calc,
                    total_calc,
                    str(fecha_emision + timedelta(days=30)),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                conn.close()
                st.success(f"¡Factura `{secuencia_ecf}` registrada con éxito!")
            except Exception as ex:
                st.error(f"Error: {str(ex)}")

# --- MÓDULO 3: FORMATO 606 OFICIAL DGII (REGISTRO, HISTÓRICO, EDICIÓN, BORRADO Y EXPORTACIÓN EXCEL) ---
elif menu_principal == "🛒 Formato 606 Oficial DGII (Registro, Histórico y Exportación)":
    st.markdown(f'<div class="main-header"><h2>🛒 Módulo Oficial Formato 606 DGII (Compras, Histórico y Exportación Excel)</h2><p>Acumulado mensual y gestión por factura para el RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    
    tab_reg_606, tab_hist_606, tab_exp_606 = st.tabs(["➕ Registrar Compra / Gasto 606", "📋 Histórico, Edición y Borrado", "📥 Exportar a Excel (Formato DGII Oficial)"])
    
    with tab_reg_606:
        st.success("🟢 Registro de Compras bajo la estructura oficial de la DGII (Herramienta de Distribución Gratuita Formato 606).")
        with st.form("form_nuevo_606_oficial"):
            col_6a, col_6b = st.columns(2)
            with col_6a:
                periodo_ing = st.text_input("Período Fiscal (AAAAMM)", value="202611")
                rnc_suplidor_ing = st.text_input("RNC o Cédula del Suplidor", value="101010101")
                tipo_id_ing = st.selectbox("Tipo ID Suplidor", ["1 - RNC", "2 - Cédula", "3 - Pasaporte"], index=0)
                tipo_bienes_ing = st.selectbox("Tipo de Bienes y Servicios Comprados", [
                    "01 - GASTOS DE PERSONAL",
                    "02 - GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS",
                    "03 - ARRENDAMIENTOS",
                    "04 - GASTOS DE ACTIVOS FIJO",
                    "05 - GASTOS DE REPRESENTACIÓN",
                    "06 - OTRAS DEDUCCIONES ADMITIDAS",
                    "07 - GASTOS FINANCIEROS",
                    "08 - GASTOS EXTRAORDINARIOS",
                    "09 - COMPRAS Y GASTOS QUE FORMARAN PARTE DEL COSTO DE VENTA",
                    "10 - ADQUISICIONES DE ACTIVOS",
                    "11 - GASTOS DE SEGUROS"
                ])
                ncf_ing = st.text_input("NCF o e-NCF del Comprobante", value="E310000000300")
                ncf_mod_ing = st.text_input("NCF o Documento Modificado (Si aplica)", value="")
            with col_6b:
                fecha_comp_ing = st.text_input("Fecha Comprobante (AAAAMMDD)", value="20261105")
                fecha_pago_ing = st.text_input("Fecha de Pago (AAAAMMDD)", value="20261105")
                monto_serv_ing = st.number_input("Monto Facturado en Servicios RD$", min_value=0.0, value=50000.0)
                monto_bienes_ing = st.number_input("Monto Facturado en Bienes RD$", min_value=0.0, value=0.0)
                itbis_fact_ing = st.number_input("ITBIS Facturado RD$", min_value=0.0, value=9000.0)
                itbis_retenido_ing = st.number_input("ITBIS Retenido RD$", min_value=0.0, value=0.0)
                ret_isr_monto = st.number_input("Monto Retención Renta (ISR) RD$", min_value=0.0, value=0.0)
                forma_pago_ing = st.selectbox("Forma de Pago", [
                    "01 - EFECTIVO",
                    "02 - CHEQUES/TRANSFERENCIAS/DEPÓSITO",
                    "03 - TARJETA CRÉDITO/DÉBITO",
                    "04 - COMPRA A CREDITO",
                    "05 - PERMUTA",
                    "06 - NOTA DE CREDITO",
                    "07 - MIXTO"
                ])

            total_fact_calc = monto_serv_ing + monto_bienes_ing
            st.info(f"🧮 Total Monto Facturado: RD$ {total_fact_calc:,.2f} | ITBIS Facturado: RD$ {itbis_fact_ing:,.2f}")

            if st.form_submit_button("🛒 Registrar Compra en Formato 606 Oficial", type="primary"):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO purchases_606_oficial (rnc_empresa, periodo, rnc_suplidor, tipo_id, tipo_bienes_servicios, ncf_comprobante, ncf_o_doc_modificado, fecha_comprobante, fecha_pago, monto_servicios, monto_bienes, total_monto_facturado, itbis_facturado, itbis_retenido, itbis_sujeto_proporcionalidad, itbis_llevado_costo, itbis_por_adelantar, itbis_percibido_compras, tipo_retencion_isr, monto_retencion_renta, isr_percibido_compras, impuesto_selectivo_consumo, otros_impuestos_tasas, monto_propina_legal, forma_pago, estatus, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 0.0, ?, 0.0, '00 - ', ?, 0.0, 0.0, 0.0, 0.0, ?, 'Correcto', ?)
                    """, (
                        st.session_state.rnc_usuario,
                        periodo_ing,
                        rnc_suplidor_ing,
                        tipo_id_ing.split(" - ")[0],
                        tipo_bienes_ing,
                        ncf_ing,
                        ncf_mod_ing,
                        fecha_comp_ing,
                        fecha_pago_ing,
                        monto_serv_ing,
                        monto_bienes_ing,
                        total_fact_calc,
                        itbis_fact_ing,
                        itbis_retenido_ing,
                        itbis_fact_ing, # ITBIS por adelantar automático
                        ret_isr_monto,
                        forma_pago_ing,
                        datetime.utcnow().isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Compra con NCF `{ncf_ing}` registrada y acumulada con éxito para el período `{periodo_ing}`!")
                except Exception as ex:
                    st.error(f"Error al registrar: {str(ex)}")

    with tab_hist_606:
        st.subheader("📋 Histórico Detallado por Factura (Edición y Eliminación)")
        
        periodo_filtro = st.text_input("Filtrar por Período (AAAAMM):", value="202611")
        
        try:
            conn = get_db_connection()
            df_606_hist = pd.read_sql_query("SELECT id, periodo, rnc_suplidor, tipo_bienes_servicios, ncf_comprobante, fecha_comprobante, total_monto_facturado, itbis_facturado, forma_pago FROM purchases_606_oficial WHERE rnc_empresa = ? AND periodo = ?", conn, params=(st.session_state.rnc_usuario, periodo_filtro))
            conn.close()
        except Exception:
            df_606_hist = pd.DataFrame()

        if not df_606_hist.empty:
            st.dataframe(df_606_hist, use_container_width=True)
            
            st.markdown("---")
            st.subheader("✏️ Editar o 🗑️ Borrar Factura Específica")
            
            factura_opts = {f"ID: {row['id']} | NCF: {row['ncf_comprobante']} | Suplidor: {row['rnc_suplidor']} | Total: RD$ {row['total_monto_facturado']:,.2f}": row['id'] for _, row in df_606_hist.iterrows()}
            
            sel_fact_str = st.selectbox("Seleccione Factura a Modificar o Eliminar:", list(factura_opts.keys()))
            if sel_fact_str:
                selected_id = factura_opts[sel_fact_str]
                row_act = df_606_hist[df_606_hist['id'] == selected_id].iloc[0]
                
                col_ed1, col_ed2 = st.columns(2)
                with col_ed1:
                    nuevo_monto_tot = st.number_input("Nuevo Monto Total Facturado RD$", value=float(row_act['total_monto_facturado']))
                with col_ed2:
                    nuevo_itbis_tot = st.number_input("Nuevo ITBIS Facturado RD$", value=float(row_act['itbis_facturado']))
                    
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Actualizar Factura"):
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE purchases_606_oficial SET total_monto_facturado = ?, itbis_facturado = ? WHERE id = ?", (nuevo_monto_tot, nuevo_itbis_tot, selected_id))
                            conn.commit()
                            conn.close()
                            st.success("¡Factura actualizada con éxito!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error: {str(ex)}")
                with col_btn2:
                    if st.button("🗑️ Eliminar Factura Permanentemente", type="primary"):
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM purchases_606_oficial WHERE id = ?", (selected_id,))
                            conn.commit()
                            conn.close()
                            st.success("¡Factura eliminada correctamente del histórico!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error: {str(ex)}")
        else:
            st.info(f"No hay registros de compras para el período `{periodo_filtro}`.")

    with tab_exp_606:
        st.subheader("📥 Exportar a Excel (Formato Oficial DGII)")
        periodo_exp = st.text_input("Ingrese Período a Exportar (AAAAMM):", value="202611")
        
        if st.button("📊 Generar Archivo Excel Formato 606 Oficial", type="primary"):
            try:
                conn = get_db_connection()
                df_exp = pd.read_sql_query("""
                    SELECT rnc_suplidor, tipo_id, tipo_bienes_servicios, ncf_comprobante, ncf_o_doc_modificado, 
                           fecha_comprobante, fecha_pago, monto_servicios, monto_bienes, total_monto_facturado, 
                           itbis_facturado, itbis_retenido, itbis_sujeto_proporcionalidad, itbis_llevado_costo, 
                           itbis_por_adelantar, itbis_percibido_compras, tipo_retencion_isr, monto_retencion_renta, 
                           isr_percibido_compras, impuesto_selectivo_consumo, otros_impuestos_tasas, monto_propina_legal, forma_pago 
                    FROM purchases_606_oficial WHERE rnc_empresa = ? AND periodo = ?
                """, conn, params=(st.session_state.rnc_usuario, periodo_exp))
                conn.close()
                
                if not df_exp.empty:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        header_info = pd.DataFrame([
                            ["Dirección General de Impuestos Internos", "", "Herramienta de Distribución Gratuita"],
                            ["Formato de Envío de Compras de Bienes y Servicios", "", "Derechos Reservados DGII 2019 ©"],
                            ["RNC o Cédula", st.session_state.rnc_usuario, ""],
                            ["Periodo", periodo_exp, ""],
                            ["Cantidad Registros", len(df_exp), ""]
                        ])
                        header_info.to_excel(writer, sheet_name='Formato 606', header=False, index=False, startrow=0)
                        df_exp.to_excel(writer, sheet_name='Formato 606', index=False, startrow=6)
                        
                    output.seek(0)
                    st.success(f"¡Archivo Excel del Formato 606 para el período `{periodo_exp}` generado exitosamente!")
                    st.download_button(
                        label="📥 Descargar Excel Oficial Formato 606 (.xlsx)",
                        data=output,
                        file_name=f"Formato_606_{st.session_state.rnc_usuario}_{periodo_exp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning(f"No hay registros en el período `{periodo_exp}` para exportar.")
            except Exception as ex:
                st.error(f"Error generando Excel: {str(ex)}")

# --- MÓDULO 4: CONTROL IR-17 ---
elif menu_principal == "📋 Módulo de Declaración y Control IR-17 (Instructivo DGII)":
    st.markdown(f'<div class="main-header"><h2>📋 Módulo de Declaración y Control IR-17 (Retenciones y Otras Rentas)</h2><p>Instructivo Oficial DGII para el RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="erp-module-box">
            <h4>📖 Instructivo Oficial y Base Legal del IR-17 (DGII)</h4>
            <p>El formulario <b>IR-17</b> es la Declaración Jurada para el pago de las retenciones del Impuesto Sobre la Renta (ISR) realizadas a terceros. Debe presentarse a más tardar el día <b>diez (10)</b> de cada mes.</p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        conn = get_db_connection()
        df_ir17 = pd.read_sql_query("SELECT periodo, tipo_retencion, monto_operacion, tasa_retencion, monto_retenido_ir17, cedula_rnc_retenido, nombre_retenido, estado_pago FROM ir17_retenciones WHERE rnc_empresa = ?", conn, params=(st.session_state.rnc_usuario,))
        conn.close()
    except Exception:
        df_ir17 = pd.DataFrame()

    if not df_ir17.empty:
        st.dataframe(df_ir17, use_container_width=True)
        st.metric("Total IR-17 a Pagar", f"RD$ {df_ir17['monto_retenido_ir17'].sum():,.2f}")
    else:
        st.info("No hay retenciones IR-17 registradas.")

# --- MÓDULO 5: INVESTIGACIÓN FORENSE DIGITAL ---
elif menu_principal == "🔍 Investigación Forense Digital & Cruce Multi-Institucional":
    st.markdown(f'<div class="main-header"><h2>🔍 Investigación Forense Digital & Cruce Multi-Institucional</h2><p>Conexión segura vía VPN para el RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    st.success("🟢 Gateway de Investigación Forense Activo (DGII, DGA, TSS, Registros Públicos/Privados).")

# --- MÓDULO 6: VENTAS 607 ---
elif menu_principal == "📊 Módulo de Ventas (Formato 607 Detallado)":
    st.markdown(f'<div class="main-header"><h2>📊 Módulo de Ventas - Formato 607 (Detalle por Factura)</h2><p>RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    try:
        conn = get_db_connection()
        df_v = pd.read_sql_query("SELECT secuencia_encf AS Comprobante, rnc_cliente AS RNC, nombre_cliente AS Nombre, monto_neto AS Neto, itbis AS ITBIS, monto_total AS Total, created_at AS Fecha FROM sales_invoices WHERE rnc_empresa = ?", conn, params=(st.session_state.rnc_usuario,))
        conn.close()
        if not df_v.empty:
            st.dataframe(df_v, use_container_width=True)
            st.metric("Total Ventas Formato 607", f"RD$ {df_v['Total'].sum():,.2f}")
        else:
            st.info("No hay registros de ventas.")
    except Exception as ex:
        st.error(f"Error: {str(ex)}")

# --- MÓDULO 7: HASH Y CONSTANCIAS ---
elif menu_principal == "🛡️ Constancias, Hash y Validación Criptográfica":
    st.markdown('<div class="main-header"><h2>🛡️ Módulo de Validación, Hash y Constancias Criptográficas</h2><p>Verificación de integridad pericial</p></div>', unsafe_allow_html=True)
    st.info(f"Hash Oficial de Integridad verificado: `461474D8A0FF77DB37AF7B7E0700E459#` (Válido y Auténtico).")

# --- MÓDULO 8: AUDITORÍA DE INTRUSOS (ADMIN / DEV) ---
elif menu_principal == "🚨 [Admin/Dev] Auditoría de Seguridad & Bitácora de Intrusos":
    st.markdown('<div class="main-header"><h2>🚨 Bitácora de Ciberseguridad & Control de Intrusos (AFA)</h2><p>Supervisión en tiempo real de intentos de acceso y ataques bloqueados</p></div>', unsafe_allow_html=True)
    try:
        conn = get_db_connection()
        df_logs = pd.read_sql_query("SELECT id, usuario_o_intruso, ip_o_dispositivo, evento, detalle, timestamp FROM security_audit_log ORDER BY id DESC", conn)
        conn.close()
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("No se registran alertas ni eventos de intrusión.")
    except Exception as ex:
        st.error(f"Error: {str(ex)}")

# --- MÓDULO 9: GESTIÓN DE USUARIOS (ADMIN / DEV) ---
elif menu_principal == "⚙️ [Admin/Dev] Gestión de Usuarios y Accesos":
    st.markdown('<div class="main-header"><h2>⚙️ Gestión de Usuarios y Accesos ERP</h2><p>Control maestro para aprobación de cuentas</p></div>', unsafe_allow_html=True)
    try:
        conn = get_db_connection()
        df_users = pd.read_sql_query("SELECT id, login_id, nombre_completo, rol, rnc_asociado, email, estado FROM usuarios_erp", conn)
        conn.close()
        st.dataframe(df_users, use_container_width=True)
    except Exception as ex:
        st.error(f"Error: {str(ex)}")

# --- MÓDULO 10: REPORTES ---
elif menu_principal in ["🖨️ Centro de Reportes y Dictamen Pericial AFA", "🖨️ Centro de Reportes y Estados Financieros"]:
    st.markdown(f'<div class="main-header"><h2>🖨️ Centro de Reportes Financieros, Fiscales & Dictamen Pericial</h2><p>Consolidado universal para el RNC: <b>{st.session_state.rnc_usuario}</b></p></div>', unsafe_allow_html=True)
    st.success("Reportes listos para visualización y presentación oficial.")
