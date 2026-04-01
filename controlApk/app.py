import streamlit as st
import yfinance as yf
import time
import base64
import os

st.markdown(
    """
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#000000">
    """,
    unsafe_allow_html=True
)



def reproducir_sonido(tipo):
    archivo = {
        "compra": "target_s.wav",
        "target": "target_s.wav",
        "stop": "stop_s.wav"
    }.get(tipo, "alert.wav")

    try:
        base_dir = os.path.dirname(__file__)
        ruta = os.path.join(base_dir, "static", archivo)

        with open(ruta, "rb") as f:
            audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/wav", autoplay=True)

    except Exception as e:
        st.error(f"Error sonido: {e}")
        
        
st.set_page_config(page_title="Monitor Trading", layout="centered")

st.title("📈 Monitor de Activos")

# --- Inicializar estado ---
if "activos" not in st.session_state:
    st.session_state.activos = []

if "monitoreo" not in st.session_state:
    st.session_state.monitoreo = False


# --- Inputs ---
activos_input = []

for i in range(3):
    st.subheader(f"Activo {i+1}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        simbolo = st.text_input(f"Símbolo {i+1}", key=f"simbolo_{i}", value="YPFD.BA")
    with col2:
        compra = st.number_input(f"Compra {i+1}", key=f"compra_{i}", value=60000.0)
    with col3:
        target = st.number_input(f"Target {i+1}", key=f"target_{i}", value=70000.0)
    with col4:
        stop = st.number_input(f"Stop {i+1}", key=f"stop_{i}", value=55000.0)

    activos_input.append({
        "simbolo": simbolo,
        "compra": compra,
        "target": target,
        "stop": stop
    })


# --- Botón ---
if st.button("🚀 Iniciar Monitoreo"):
    st.session_state.activos = []
    for a in activos_input:
        st.session_state.activos.append({
            **a,
            "activo": True,
            "ultimo_precio": None
        })

    st.session_state.monitoreo = True


# --- Función segura de descarga ---
@st.cache_data(ttl=30)
def obtener_datos(simbolo):
    try:
        data = yf.download(
            tickers=simbolo,
            period="1d",
            interval="1m",
            progress=False,
            threads=False
        )
        return data
    except:
        return None


# --- Monitoreo ---
if st.session_state.monitoreo:

    st.subheader("📊 Estado en vivo")

    for activo in st.session_state.activos:

        if not activo["activo"]:
            continue

        simbolo = activo["simbolo"]

        data = obtener_datos(simbolo)

        # --- Manejo robusto ---
        if data is not None and not data.empty:
            close = data["Close"]

# Si es DataFrame (varios valores)
            if hasattr(close, "columns"):
                precio = float(close.iloc[-1].dropna().values[0])
            else:
                precio = float(close.iloc[-1])
                activo["ultimo_precio"] = precio
        else:
            precio = activo["ultimo_precio"]

        if precio is None:
            st.warning(f"{simbolo}: sin datos ⏳")
            continue

        pnl = ((precio / activo["compra"]) - 1) * 100

        # --- Color dinámico ---
        color = "green" if pnl >= 0 else "red"

        # --- Estado ---
       # --- Estado ---
        estado = ""

        # margen para detectar compra (0.1%)
        margen = activo["compra"] * 0.001

        # 1. BREAKEVEN (precio compra)
        if abs(precio - activo["compra"]) <= margen:
            estado = "⚠️ COMPRA"
            reproducir_sonido("compra")

        # 2. TARGET
        elif precio >= activo["target"]:
            estado = "🎯 TARGET"
            reproducir_sonido("target")

        # 3. STOP
        elif precio <= activo["stop"]:
            estado = "🛑 STOP"
            reproducir_sonido("stop")
        # --- UI tipo broker ---
        st.markdown(
            f"""
            **{simbolo}**  
            💰 Precio: {precio:.2f}  
            📊 P&L: <span style='color:{color}'>{pnl:+.2f}%</span>  
            {estado}
            """,
            unsafe_allow_html=True
        )

        time.sleep(1)  # evita bloqueo de Yahoo

    # --- Auto refresh limpio ---
    time.sleep(30)
    st.rerun()
