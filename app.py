import streamlit as st
import numpy as np
import time
import requests
from streamlit_lottie import st_lottie
import base64

# -------------------------
# MUST BE FIRST STREAMLIT CALL
# -------------------------
st.set_page_config(page_title="BB84 Photon Chat", layout="wide")

# -------------------------
# Background Setup
# -------------------------
def set_bg(file):
    with open(file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-attachment: fixed;
    }}

    @keyframes movePhoton {{
        0%   {{ left: 10%; top: 50%; }}
        50%  {{ left: 45%; top: 50%; }}
        100% {{ left: 80%; top: 50%; }}
    }}
    .photon {{
        position: absolute;
        width: 20px;
        height: 20px;
        background: radial-gradient(circle, #00f 20%, #0ff 80%);
        border-radius: 50%;
        animation: movePhoton 3s linear forwards;
        box-shadow: 0px 0px 15px #0ff;
    }}
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

# Call background setup (make sure bg.jpg exists in folder)
set_bg("bg.jpg")

# -------------------------
# Helper: Load Lottie animations
# -------------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Characters
ria_anim = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")  # girl
sia_anim = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_yr6zz3wv.json")  # boy
eve_anim = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_j1adxtyb.json")  # spy


# -------------------------
# BB84 Functions
# -------------------------
def generate_bits_bases(n, rng):
    bits = rng.integers(0, 2, size=n, dtype=np.uint8)
    bases = rng.choice(np.array(["Z", "X"]), size=n)
    return bits, bases

def transmit_measure(ria_bits, ria_bases, sia_bases, noise=0.0, eve=False, rng=None):
    rng = rng or np.random.default_rng()
    results = np.empty(len(ria_bits), dtype=np.uint8)
    for i in range(len(ria_bits)):
        send_bit, send_basis = ria_bits[i], ria_bases[i]
        if eve:  # Eve intercepts
            eve_basis = rng.choice(["Z", "X"])
            eve_meas = send_bit if eve_basis == send_basis else rng.integers(0, 2)
            send_bit, send_basis = eve_meas, eve_basis
        if sia_bases[i] == send_basis:
            meas = send_bit
        else:
            meas = rng.integers(0, 2)
        if rng.random() < noise:
            meas ^= 1
        results[i] = meas
    return results

def sift_keys(ria_bits, ria_bases, sia_bases, sia_results):
    keep = (ria_bases == sia_bases)
    return ria_bits[keep], sia_results[keep]

def estimate_qber(ria_key, sia_key, frac=0.5):
    rng = np.random.default_rng()
    m = len(ria_key)
    if m == 0:
        return 1.0
    sample_size = max(1, int(m * frac))
    idx = rng.choice(m, size=sample_size, replace=False)
    return np.mean(ria_key[idx] != sia_key[idx])


# -------------------------
# Photon Flow with Multiple Photons
# -------------------------
def photon_flow(eve_enabled=False, photon_count=5):
    for i in range(photon_count):
        st.markdown(
            f"<div class='photon' style='animation-delay:{i*0.5}s'></div>",
            unsafe_allow_html=True
        )
        time.sleep(0.5)

    time.sleep(3)
    if eve_enabled:
        st.error("🚨 Eve intercepted photons!")
        st.warning("⚠️ Your communication may be compromised.")
    else:
        st.success("✅ All photons safely received by Sia")


# -------------------------
# Streamlit UI
# -------------------------
st.markdown("<h1 style='text-align:center; color:#FFD700;'>🔐 BB84 Secure Chat with Photon Flow</h1>", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.header("⚙️ Key Generation")
n = st.sidebar.slider("Photons (N)", 50, 500, 100)
noise = st.sidebar.slider("Noise (%)", 0, 30, 2) / 100
eve = st.sidebar.checkbox("Enable Eve (middleman)", value=False)

if st.sidebar.button("🔑 Generate Shared Key"):
    rng = np.random.default_rng()
    ria_bits, ria_bases = generate_bits_bases(n, rng)
    sia_bases = rng.choice(["Z", "X"], n)
    sia_results = transmit_measure(ria_bits, ria_bases, sia_bases, noise=noise, eve=eve, rng=rng)
    ria_key, sia_key = sift_keys(ria_bits, ria_bases, sia_bases, sia_results)
    qber = estimate_qber(ria_key, sia_key)

    st.session_state["key"] = ria_key.tolist()
    st.session_state["qber"] = qber
    st.session_state["chat"] = []  # reset chat

# Characters Row
col1, col2, col3 = st.columns(3)

with col1:
    if ria_anim:
        st_lottie(ria_anim, height=200, key="ria")
    else:
        st.markdown("👩 Ria")

with col2:
    if eve and eve_anim:
        st_lottie(eve_anim, height=200, key="eve")
    elif eve:
        st.markdown("🕵️ Eve")

with col3:
    if sia_anim:
        st_lottie(sia_anim, height=200, key="sia")
    else:
        st.markdown("👨 Sia")

st.markdown("---")

# Security Status
if "key" not in st.session_state:
    st.warning("⚠️ Please generate a key first (sidebar).")
else:
    qber = st.session_state["qber"]
    if qber > 0.11:
        st.error(f"🚨 Eavesdropper Detected! (QBER={qber*100:.2f}%)")
        st.warning("⚠️ Your chat is not secure. Stop transmission!")
    else:
        st.success(f"✅ Secure channel established (QBER={qber*100:.2f}%)")

    # Photon Flow Button
    st.subheader("📡 Photon Transmission")
    if st.button("▶️ Start Photon Flow"):
        photon_flow(eve_enabled=eve, photon_count=7)

    # Chat
    st.subheader("💬 Secure Chat")
    col1, col2 = st.columns(2)
    with col1:
        ria_msg = st.text_input("👩 Ria's message:", key="ria_msg")
        if st.button("Send (Ria)"):
            if ria_msg.strip():
                st.session_state["chat"].append(("Ria", ria_msg))
    with col2:
        sia_msg = st.text_input("👨 Sia's message:", key="sia_msg")
        if st.button("Send (Sia)"):
            if sia_msg.strip():
                st.session_state["chat"].append(("Sia", sia_msg))

    # Show Chat History
    if "chat" in st.session_state and st.session_state["chat"]:
        st.markdown("### 📜 Chat History")
        for sender, msg in st.session_state["chat"]:
            if sender == "Ria":
                st.markdown(
                    f"<div style='text-align:left; background:rgba(135,206,250,0.8); "
                    f"padding:10px; border-radius:15px; margin:8px; width:60%; "
                    f"box-shadow:0px 0px 10px rgba(0,0,0,0.5);'><b>👩 Ria:</b> {msg}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align:right; background:rgba(255,165,0,0.8); "
                    f"padding:10px; border-radius:15px; margin:8px; width:60%; float:right; "
                    f"box-shadow:0px 0px 10px rgba(0,0,0,0.5);'><b>👨 Sia:</b> {msg}</div>",
                    unsafe_allow_html=True
                )
