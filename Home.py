import streamlit as st
import time

st.set_page_config(
    page_title="福德里 - 社區數位管理中樞 (雲端版)",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 美化 ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: #2c3e50;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.8);
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.2s;
    }
    .card:hover { transform: translateY(-5px); }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("☁️ 福德雲端系統")
    st.info("系統已部署於 Streamlit Cloud")
    st.caption(f"伺服器時間：{time.strftime('%H:%M:%S')}")

# --- 主畫面 ---
c1, c2 = st.columns([1, 10])
with c1: st.write("## ☁️")
with c2: st.markdown('<div class="main-title">福德里 - 雲端數位中樞</div>', unsafe_allow_html=True)

st.divider()

st.success("✅ 雲端系統運作中！資料已連接 Google 試算表，手機/電腦皆可同步使用。")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="card" style="border-top: 5px solid #3498db;">
        <h3>👤 1. 志工管理</h3>
        <p>智能刷卡 • 時數統計 • 榮譽榜</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card" style="border-top: 5px solid #f1c40f;">
        <h3>👴 2. 長輩據點</h3>
        <p>上課簽到 • 健康數據 • 關懷追蹤</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card" style="border-top: 5px solid #e74c3c;">
        <h3>🤝 3. 關心戶管理</h3>
        <p>訪視紀錄 • 物資庫存 • 個案歷程</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("系統開發：呂宜政里長辦公室 | Powered by Streamlit Cloud & Google Sheets")