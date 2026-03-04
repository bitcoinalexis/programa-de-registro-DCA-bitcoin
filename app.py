import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime
import pytz
import plotly.express as px
import plotly.graph_objects as go
import os


# ---------------------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DCA Bitcoin Tracker",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded",
)

CDMX_TZ = pytz.timezone("America/Mexico_City")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dca_bitcoin.db")


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dca_records (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha                 TEXT    NOT NULL,
                mxn_gastado           REAL    NOT NULL,
                tipo_cambio_mxn_usd   REAL    NOT NULL,
                usd_equivalente       REAL    NOT NULL,
                btc_adquirido         REAL    NOT NULL,
                precio_compra_btc_usd REAL    NOT NULL,
                notas                 TEXT
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fee_records (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha             TEXT    NOT NULL,
                btc_fee           REAL    NOT NULL,
                precio_btc_usd    REAL    NOT NULL,
                usd_fee           REAL    NOT NULL,
                tipo_movimiento   TEXT    NOT NULL,
                notas             TEXT
            )
        """
        )
        conn.commit()


def insertar_registro(mxn, tc, usd, btc, precio, notas):
    fecha = datetime.now(CDMX_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO dca_records
               (fecha, mxn_gastado, tipo_cambio_mxn_usd, usd_equivalente,
                btc_adquirido, precio_compra_btc_usd, notas)
               VALUES (?,?,?,?,?,?,?)""",
            (fecha, mxn, tc, usd, btc, precio, notas),
        )
        conn.commit()


def obtener_registros() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM dca_records ORDER BY fecha DESC", conn
        )
    return df


def eliminar_registro(record_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM dca_records WHERE id = ?", (record_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# CRUD — Fees de envío
# ---------------------------------------------------------------------------
def insertar_fee(btc_fee: float, precio_btc_usd: float, tipo_movimiento: str, notas: str):
    fecha = datetime.now(CDMX_TZ).strftime("%Y-%m-%d %H:%M:%S")
    usd_fee = btc_fee * precio_btc_usd
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO fee_records
               (fecha, btc_fee, precio_btc_usd, usd_fee, tipo_movimiento, notas)
               VALUES (?,?,?,?,?,?)""",
            (fecha, btc_fee, precio_btc_usd, usd_fee, tipo_movimiento, notas),
        )
        conn.commit()


def obtener_fees() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM fee_records ORDER BY fecha DESC", conn
        )
    return df


def eliminar_fee(fee_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM fee_records WHERE id = ?", (fee_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# API tipo de cambio
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def obtener_tipo_cambio() -> float | None:
    """Obtiene MXN por 1 USD desde APIs públicas gratuitas (sin llave)."""
    endpoints = [
        "https://open.er-api.com/v6/latest/USD",
        "https://api.exchangerate-api.com/v4/latest/USD",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                rates = r.json().get("rates", {})
                if "MXN" in rates:
                    return float(rates["MXN"])
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Estilos personalizados
# ---------------------------------------------------------------------------
def inyectar_css():
    st.markdown(
        """
        <style>
        /* Fondo del sidebar */
        section[data-testid="stSidebar"] { background-color: #1a1a2e; }
        section[data-testid="stSidebar"] * { color: #e0e0e0 !important; }

        /* Tarjetas de métricas */
        div[data-testid="metric-container"] {
            background: #1e1e2e;
            border: 1px solid #f7931a33;
            border-radius: 10px;
            padding: 12px 16px;
        }
        div[data-testid="metric-container"] label { color: #aaaaaa !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #f7931a !important;
            font-size: 1.3rem !important;
        }

        /* Botón primario */
        div.stButton > button[kind="primary"] {
            background-color: #f7931a;
            color: #000;
            font-weight: 700;
            border: none;
        }
        div.stButton > button[kind="primary"]:hover { background-color: #e07d0a; }

        /* Header principal */
        h1 { color: #f7931a !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------
init_db()
inyectar_css()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/4/46/Bitcoin.svg",
        width=80,
    )
    st.title("DCA Bitcoin")
    st.caption("Registro de acumulación de Bitcoin")
    st.markdown("---")
    st.markdown(
        """
        **¿Qué es DCA?**  
        *Dollar Cost Averaging* — estrategia de compra periódica para 
        reducir el impacto de la volatilidad del precio.
        """
    )
    st.markdown("---")
    st.caption("🕐 Zona horaria: CDMX (America/Mexico_City)")
    ahora_cdmx = datetime.now(CDMX_TZ)
    st.caption(f"Hora actual: **{ahora_cdmx.strftime('%d/%m/%Y %H:%M:%S')}**")

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("₿ Panel de Registro DCA Bitcoin")
st.markdown("Registra tus compras de Bitcoin y lleva el control de tu estrategia DCA.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Pestañas
# ---------------------------------------------------------------------------
tab_registro, tab_fees, tab_historial, tab_resumen = st.tabs(
    ["📝 Registrar Compra", "💸 Fees de Envío", "📋 Historial", "📊 Resumen & Gráficas"]
)

# ===========================================================================
# PESTAÑA 1 — REGISTRO
# ===========================================================================
with tab_registro:
    st.subheader("Nueva compra de Bitcoin")

    # --- Tipo de cambio ---
    tc_api = obtener_tipo_cambio()

    if tc_api:
        st.success(
            f"💱 Tipo de cambio obtenido automáticamente: **1 USD = {tc_api:.4f} MXN**  "
            f"*(actualización cada 5 min)*"
        )
    else:
        st.warning(
            "⚠️ No se pudo obtener el tipo de cambio automáticamente. "
            "Ingresa el valor manualmente."
        )

    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown("#### 💵 Datos en pesos MXN")

        mxn_gastado = st.number_input(
            "MXN gastados",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            help="Cantidad total en pesos mexicanos que gastaste en esta compra",
        )

        tipo_cambio = st.number_input(
            "Tipo de cambio (MXN por 1 USD)",
            min_value=0.01,
            value=float(tc_api) if tc_api else 17.50,
            step=0.01,
            format="%.4f",
            help="Puedes ajustar este valor si el de tu exchange difiere",
        )

        usd_equivalente = mxn_gastado / tipo_cambio if tipo_cambio > 0 else 0.0

        st.info(
            f"💲 Equivalente en USD: **${usd_equivalente:,.4f} USD**"
            if mxn_gastado > 0
            else "Ingresa el monto en MXN para ver el equivalente en USD."
        )

    with col_der:
        st.markdown("#### ₿ Datos Bitcoin")

        btc_adquirido = st.number_input(
            "BTC adquiridos",
            min_value=0.0,
            value=0.0,
            step=0.00001,
            format="%.8f",
            help="Cantidad exacta de BTC que recibiste (revisa tu exchange)",
        )

        modo_precio = st.radio(
            "Ingresar precio BTC en:",
            options=["MXN", "USD"],
            horizontal=True,
            key="modo_precio_btc",
            help="Elige la moneda en que aparece el precio en tu exchange",
        )

        if modo_precio == "MXN":
            precio_btc_mxn_input = st.number_input(
                "Precio de compra BTC (MXN)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                format="%.2f",
                help="Precio en MXN tal como lo muestra tu exchange (ej: 1,293,620.00)",
            )
            precio_btc_usd = (
                precio_btc_mxn_input / tipo_cambio
                if tipo_cambio > 0 and precio_btc_mxn_input > 0
                else 0.0
            )
            if precio_btc_mxn_input > 0:
                st.info(f"💲 Equivalente en USD: **${precio_btc_usd:,.2f} USD**")
        else:
            precio_btc_usd = st.number_input(
                "Precio de compra BTC (USD)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
                help="Precio en USD al que compraste el BTC en esta operación",
            )
            precio_btc_mxn_calc = precio_btc_usd * tipo_cambio if precio_btc_usd > 0 else 0.0
            if precio_btc_usd > 0:
                st.info(f"₿ Equivalente en MXN: **${precio_btc_mxn_calc:,.2f} MXN**")

    notas = st.text_area(
        "Notas (opcional)",
        placeholder="Ej: Compra automática Bitso, semana 12...",
        height=80,
    )

    # --- Vista previa ---
    if mxn_gastado > 0 or btc_adquirido > 0:
        st.markdown("---")
        st.markdown("**Vista previa del registro:**")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("MXN gastados", f"${mxn_gastado:,.2f}")
        p2.metric("USD equivalente", f"${usd_equivalente:,.4f}")
        p3.metric("BTC adquiridos", f"{btc_adquirido:.8f}")
        p4.metric("Precio BTC (USD)", f"${precio_btc_usd:,.2f}")

    st.markdown("---")

    if st.button("💾 Guardar registro", type="primary", use_container_width=True):
        errores = []
        if mxn_gastado <= 0:
            errores.append("La cantidad de MXN debe ser mayor a 0.")
        if btc_adquirido <= 0:
            errores.append("La cantidad de BTC debe ser mayor a 0.")
        if precio_btc_usd <= 0:
            errores.append("El precio de compra del BTC debe ser mayor a 0.")

        if errores:
            for e in errores:
                st.error(f"❌ {e}")
        else:
            insertar_registro(
                mxn_gastado,
                tipo_cambio,
                usd_equivalente,
                btc_adquirido,
                precio_btc_usd,
                notas,
            )
            st.success("✅ ¡Registro guardado exitosamente!")
            st.balloons()

# ===========================================================================
# PESTAÑA 2 — FEES DE ENVÍO
# ===========================================================================
with tab_fees:
    st.subheader("Registrar fee de envío de Bitcoin")
    st.caption(
        "Registra aquí los fees (comisiones) que pagaste al enviar BTC "
        "a tu wallet fría, a otro exchange, etc."
    )

    tc_fee = obtener_tipo_cambio()

    col_f1, col_f2 = st.columns(2, gap="large")

    with col_f1:
        st.markdown("#### ₿ Fee pagado")

        btc_fee = st.number_input(
            "BTC pagados como fee",
            min_value=0.0,
            value=0.0,
            step=0.000001,
            format="%.8f",
            key="btc_fee_input",
            help="Cantidad de BTC que se cobró como comisión de red (on-chain fee)",
        )

        precio_btc_fee = st.number_input(
            "Precio BTC al momento del envío (USD)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            key="precio_btc_fee_input",
            help="Precio de mercado del BTC cuando realizaste el envío",
        )

        usd_fee_calc = btc_fee * precio_btc_fee
        mxn_fee_calc = usd_fee_calc * (tc_fee if tc_fee else 0)

        if btc_fee > 0 and precio_btc_fee > 0:
            st.info(
                f"💲 Fee equivalente: **${usd_fee_calc:.6f} USD**"
                + (f"  ≈  **${mxn_fee_calc:.4f} MXN**" if tc_fee else "")
            )

    with col_f2:
        st.markdown("#### 📋 Detalle del movimiento")

        tipo_movimiento = st.selectbox(
            "Tipo de movimiento",
            options=[
                "Envío a wallet fría",
                "Retiro de exchange",
                "Consolidación de UTXOs",
                "Envío entre wallets propias",
                "Pago a tercero",
                "Otro",
            ],
            key="tipo_mov_input",
        )

        notas_fee = st.text_area(
            "Notas (opcional)",
            placeholder="Ej: Envío de Bitso a Ledger, tx: abc123...",
            height=80,
            key="notas_fee_input",
        )

    if btc_fee > 0 and precio_btc_fee > 0:
        st.markdown("---")
        st.markdown("**Vista previa:**")
        pf1, pf2, pf3 = st.columns(3)
        pf1.metric("BTC fee", f"{btc_fee:.8f} BTC")
        pf2.metric("USD equivalente", f"${usd_fee_calc:.6f}")
        pf3.metric("Tipo de movimiento", tipo_movimiento)

    st.markdown("---")

    if st.button("💾 Guardar fee", type="primary", use_container_width=True, key="btn_save_fee"):
        errores_fee = []
        if btc_fee <= 0:
            errores_fee.append("La cantidad de BTC del fee debe ser mayor a 0.")
        if precio_btc_fee <= 0:
            errores_fee.append("El precio de BTC al momento del envío debe ser mayor a 0.")

        if errores_fee:
            for e in errores_fee:
                st.error(f"❌ {e}")
        else:
            insertar_fee(btc_fee, precio_btc_fee, tipo_movimiento, notas_fee)
            st.success("✅ ¡Fee registrado correctamente!")
            st.balloons()

    # --- Historial de fees en la misma pestaña ---
    st.markdown("---")
    st.subheader("Historial de fees registrados")

    df_fees = obtener_fees()

    if df_fees.empty:
        st.info("📭 Aún no hay fees registrados.")
    else:
        df_fees_vis = df_fees.rename(
            columns={
                "id": "ID",
                "fecha": "Fecha (CDMX)",
                "btc_fee": "BTC Fee",
                "precio_btc_usd": "Precio BTC (USD)",
                "usd_fee": "USD Fee",
                "tipo_movimiento": "Tipo",
                "notas": "Notas",
            }
        )
        st.dataframe(
            df_fees_vis.style.format(
                {
                    "BTC Fee": "{:.8f}",
                    "Precio BTC (USD)": "${:,.2f}",
                    "USD Fee": "${:.6f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        total_btc_fees = df_fees["btc_fee"].sum()
        total_usd_fees = df_fees["usd_fee"].sum()
        sf1, sf2, sf3 = st.columns(3)
        sf1.metric("Total BTC pagados en fees", f"{total_btc_fees:.8f}")
        sf2.metric("Total USD en fees", f"${total_usd_fees:.6f}")
        sf3.metric("Número de operaciones", str(len(df_fees)))

        csv_fees = df_fees.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar fees en CSV",
            csv_fees,
            "dca_bitcoin_fees.csv",
            "text/csv",
            use_container_width=True,
        )

        st.markdown("---")
        with st.expander("🗑️ Eliminar un fee"):
            ids_fees = df_fees["id"].tolist()
            id_fee_del = st.selectbox(
                "Selecciona el ID del fee a eliminar",
                options=ids_fees,
                format_func=lambda x: f"ID {x} — {df_fees.loc[df_fees['id']==x, 'fecha'].values[0]} | {df_fees.loc[df_fees['id']==x, 'tipo_movimiento'].values[0]}",
                key="sel_fee_del",
            )
            if st.button("Eliminar fee seleccionado", type="secondary", key="btn_del_fee"):
                eliminar_fee(id_fee_del)
                st.success(f"Fee ID {id_fee_del} eliminado.")
                st.rerun()


# ===========================================================================
# PESTAÑA 3 — HISTORIAL
# ===========================================================================
with tab_historial:
    st.subheader("Historial de compras")

    df = obtener_registros()

    if df.empty:
        st.info("📭 No hay registros aún. ¡Registra tu primera compra DCA!")
    else:
        # Formateo para visualización
        df_vis = df.rename(
            columns={
                "id": "ID",
                "fecha": "Fecha (CDMX)",
                "mxn_gastado": "MXN Gastados",
                "tipo_cambio_mxn_usd": "T.C. MXN/USD",
                "usd_equivalente": "USD Equiv.",
                "btc_adquirido": "BTC Adquiridos",
                "precio_compra_btc_usd": "Precio BTC (USD)",
                "notas": "Notas",
            }
        )

        st.dataframe(
            df_vis.style.format(
                {
                    "MXN Gastados": "${:,.2f}",
                    "T.C. MXN/USD": "{:.4f}",
                    "USD Equiv.": "${:,.4f}",
                    "BTC Adquiridos": "{:.8f}",
                    "Precio BTC (USD)": "${:,.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        # Descarga CSV
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Descargar historial en CSV",
            data=csv_data,
            file_name="dca_bitcoin_historial.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Eliminar registro
        st.markdown("---")
        with st.expander("🗑️ Eliminar un registro"):
            ids_disponibles = df["id"].tolist()
            id_eliminar = st.selectbox(
                "Selecciona el ID del registro a eliminar",
                options=ids_disponibles,
                format_func=lambda x: f"ID {x} — {df.loc[df['id']==x, 'fecha'].values[0]}",
            )
            if st.button("Eliminar registro seleccionado", type="secondary"):
                eliminar_registro(id_eliminar)
                st.success(f"Registro ID {id_eliminar} eliminado.")
                st.rerun()

# ===========================================================================
# PESTAÑA 3 — RESUMEN & GRÁFICAS
# ===========================================================================
with tab_resumen:
    st.subheader("Resumen de inversión")

    df = obtener_registros()

    if df.empty:
        st.info("📭 No hay datos para mostrar aún.")
    else:
        # Métricas globales
        total_mxn = df["mxn_gastado"].sum()
        total_usd = df["usd_equivalente"].sum()
        total_btc = df["btc_adquirido"].sum()
        num_compras = len(df)

        # Precio promedio ponderado
        if total_btc > 0:
            precio_prom = (df["precio_compra_btc_usd"] * df["btc_adquirido"]).sum() / total_btc
        else:
            precio_prom = 0.0

        # Precio BTC actual (para calcular P&L)
        @st.cache_data(ttl=120)
        def precio_btc_actual() -> float | None:
            try:
                r = requests.get(
                    "https://api.coingecko.com/api/v3/simple/price"
                    "?ids=bitcoin&vs_currencies=usd",
                    timeout=6,
                )
                if r.status_code == 200:
                    return float(r.json()["bitcoin"]["usd"])
            except Exception:
                pass
            return None

        precio_actual = precio_btc_actual()

        # --- Métricas row 1 ---
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total MXN invertidos", f"${total_mxn:,.2f}")
        c2.metric("Total USD invertidos", f"${total_usd:,.2f}")
        c3.metric("BTC acumulados", f"{total_btc:.8f}")
        c4.metric("Precio promedio (USD)", f"${precio_prom:,.2f}")
        c5.metric("Número de compras", str(num_compras))

        # --- Métricas row 2 (con precio actual si disponible) ---
        if precio_actual:
            valor_actual_usd = total_btc * precio_actual
            valor_actual_mxn = valor_actual_usd * (tc_api if tc_api else 1)
            ganancia_usd = valor_actual_usd - total_usd
            pct_cambio = (ganancia_usd / total_usd * 100) if total_usd > 0 else 0

            st.markdown("---")
            st.caption(f"Precio BTC actual: **${precio_actual:,.2f} USD** (CoinGecko, cache 2 min)")
            ca, cb, cc = st.columns(3)
            ca.metric("Valor actual de tu BTC (USD)", f"${valor_actual_usd:,.2f}", f"{ganancia_usd:+,.2f} USD")
            if tc_api:
                cb.metric("Valor actual de tu BTC (MXN)", f"${valor_actual_mxn:,.2f}")
            cc.metric("Rendimiento sobre inversión", f"{pct_cambio:+.2f}%")

        # --- Métricas de fees ---
        df_fees_res = obtener_fees()
        if not df_fees_res.empty:
            total_btc_fees = df_fees_res["btc_fee"].sum()
            total_usd_fees = df_fees_res["usd_fee"].sum()
            btc_neto = total_btc - total_btc_fees

            st.markdown("---")
            st.markdown("##### 💸 Impacto de fees de envío")
            cf1, cf2, cf3, cf4 = st.columns(4)
            cf1.metric("BTC pagados en fees", f"{total_btc_fees:.8f}")
            cf2.metric("USD en fees", f"${total_usd_fees:.6f}")
            cf3.metric("BTC neto (sin fees)", f"{btc_neto:.8f}")
            cf4.metric("Operaciones de envío", str(len(df_fees_res)))

        st.markdown("---")

        # --- Gráficas ---
        df_ord = df.sort_values("fecha").copy()
        df_ord["btc_acumulado"] = df_ord["btc_adquirido"].cumsum()
        df_ord["mxn_acumulado"] = df_ord["mxn_gastado"].cumsum()
        df_ord["usd_acumulado"] = df_ord["usd_equivalente"].cumsum()

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            fig_btc = px.area(
                df_ord,
                x="fecha",
                y="btc_acumulado",
                title="BTC Acumulado",
                labels={"fecha": "Fecha", "btc_acumulado": "BTC"},
                color_discrete_sequence=["#f7931a"],
            )
            fig_btc.update_layout(
                plot_bgcolor="#1e1e2e",
                paper_bgcolor="#1e1e2e",
                font_color="#e0e0e0",
            )
            st.plotly_chart(fig_btc, use_container_width=True)

        with col_g2:
            fig_mxn = px.bar(
                df_ord,
                x="fecha",
                y="mxn_gastado",
                title="Inversión por compra (MXN)",
                labels={"fecha": "Fecha", "mxn_gastado": "MXN"},
                color_discrete_sequence=["#f7931a"],
            )
            fig_mxn.update_layout(
                plot_bgcolor="#1e1e2e",
                paper_bgcolor="#1e1e2e",
                font_color="#e0e0e0",
            )
            st.plotly_chart(fig_mxn, use_container_width=True)

        # Precio de compra vs promedio
        fig_precio = go.Figure()
        fig_precio.add_trace(
            go.Scatter(
                x=df_ord["fecha"],
                y=df_ord["precio_compra_btc_usd"],
                mode="lines+markers",
                name="Precio de compra",
                line=dict(color="#f7931a"),
                marker=dict(size=8),
            )
        )
        fig_precio.add_hline(
            y=precio_prom,
            line_dash="dash",
            line_color="#aaaaaa",
            annotation_text=f"Precio promedio: ${precio_prom:,.2f}",
            annotation_font_color="#aaaaaa",
        )
        if precio_actual:
            fig_precio.add_hline(
                y=precio_actual,
                line_dash="dot",
                line_color="#00d4aa",
                annotation_text=f"Precio actual: ${precio_actual:,.2f}",
                annotation_font_color="#00d4aa",
            )
        fig_precio.update_layout(
            title="Precio BTC en cada compra (USD)",
            xaxis_title="Fecha",
            yaxis_title="Precio (USD)",
            plot_bgcolor="#1e1e2e",
            paper_bgcolor="#1e1e2e",
            font_color="#e0e0e0",
        )
        st.plotly_chart(fig_precio, use_container_width=True)

        # Acumulado en USD
        fig_usd = px.area(
            df_ord,
            x="fecha",
            y="usd_acumulado",
            title="Capital acumulado invertido (USD)",
            labels={"fecha": "Fecha", "usd_acumulado": "USD invertidos"},
            color_discrete_sequence=["#00d4aa"],
        )
        fig_usd.update_layout(
            plot_bgcolor="#1e1e2e",
            paper_bgcolor="#1e1e2e",
            font_color="#e0e0e0",
        )
        st.plotly_chart(fig_usd, use_container_width=True)
