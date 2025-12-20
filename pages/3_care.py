
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="關懷戶系統",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))

# 配色變數 (青綠色系：代表扶助與希望)
PRIMARY = "#00695C"   
ACCENT  = "#26A69A"   
BG_MAIN = "#F0F2F5"   
TEXT    = "#212121"   

# =========================================================
# 1) CSS 樣式 (維持統一風格)
# =========================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}
.stApp {{ background-color: {BG_MAIN}; }}

/* 隱藏原生側邊欄 */
[data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%;
    background-color: white !important;
    color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important;
    border-radius: 15px !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    padding: 12px 0 !important;
    box-shadow: 0 4px 0px rgba(0, 105, 92, 0.2);
    transition: all 0.1s;
}}
div[data-testid="stButton"] > button:hover {{
    transform: translateY(-2px);
    background-color: #E0F2F1 !important;
}}
div[data-testid="stButton"] > button:active {{ transform: translateY(2px); box-shadow: none; }}

/* 導航列 */
.nav-container {{
    background-color: white;
    padding: 15px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}

/* 施工中告示牌 */
.construction-box {{
    text-align: center;
    padding: 50px;
    background: white;
    border-radius: 20px;
    border: 2px dashed {ACCENT};
    margin-top: 30px;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Navigation
# =========================================================
def render_nav():
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 4])
    with c1:
        # 🔥 回到大廳
        if st.button("🏠 回系統大廳", use_container_width=True): st.switch_page("Home.py")
    with c2:
        st.markdown(f"<h3 style='margin:0; padding-top:10px; color:{PRIMARY};'>🏠 關懷戶關懷系統 (建置中)</h3>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 3) Main Page
# =========================================================
render_nav()

st.markdown(
    f"""
    <div class="construction-box">
        <div style="font-size: 80px;">🚧</div>
        <h2 style="color: {PRIMARY}; margin-top: 20px;">系統空間已預留</h2>
        <p style="font-size: 1.2rem; color: #666;">
            里長，這裡是未來的<b>「關懷戶管理中心」</b>。<br>
            我們可以規劃：關懷戶名冊、物資發放紀錄、訪視紀錄、個案備註...等功能。
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)
