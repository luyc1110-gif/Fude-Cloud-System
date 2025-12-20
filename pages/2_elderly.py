import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(page_title="長輩關懷系統", page_icon="👴", layout="wide", initial_sidebar_state="collapsed")
TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪暮色粉 - 視覺強化
PRIMARY = "#B5838D"   
ACCENT  = "#6D597A"   
BG_MAIN = "#F8F9FA"   
TEXT_BLACK = "#1A1A1A"
TEXT_WHITE = "#FFFFFF"

# =========================================================
# 1) CSS 樣式 (V32.0)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: {TEXT_BLACK} !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 下拉選單強化 */
.stTextInput input, .stDateInput input, .stNumberInput input, div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #BCB4B4 !important; border-radius: 12px !important; font-weight: 700 !important;
}}

/* 🔥 數據大看板：強制白字且背景加深 */
.metric-year {{
    background: linear-gradient(135deg, #B5838D 0%, #6D597A 100%);
    padding: 30px; border-radius: 20px; color: white !important; text-align: center; margin-bottom: 15px;
}}
.metric-today {{
    background: linear-gradient(135deg, #E5989B 0%, #B5838D 100%);
    padding: 30px; border-radius: 20px; color: white !important; text-align: center; margin-bottom: 15px;
}}
.metric-year div, .metric-today div {{ color: white !important; font-weight: 900 !important; }}
.metric-value {{ font-size: 3.5rem !important; }}

.dash-card {{
    background-color: white; padding: 18px; border-radius: 18px; border-left: 6px solid {PRIMARY};
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 12px;
}}
</style>
""", unsafe_allow_html=True)

# ... (中間 Logic 部分與您現有的一致，但 save_data 內加入以下修復) ...

def save_data(df, sheet_name):
    try:
        # 🔥 修正 nan 錯誤：儲存前清除所有無效值
        df_to_save = df.copy()
        df_to_save = df_to_save.replace(['nan', 'NaN', 'None', '<NA>', 'nan.0'], "").fillna("")
        client = get_client() # 此處對應您的 client 函數
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        return True
    except Exception as e: st.error(f"寫入失敗：{e}"); return False

# ... (UI 渲染部分) ...

if st.session_state.page == 'home':
    # 這裡顯示大看板
    c_year, c_today = st.columns(2)
    with c_year:
        st.markdown(f"""<div class="metric-year"><div>📅 年度總服務人次</div><div class="metric-value">{year_count}</div></div>""", unsafe_allow_html=True)
    with c_today:
        st.markdown(f"""<div class="metric-today"><div>☀️ 今日服務人次</div><div class="metric-value">{today_count}</div></div>""", unsafe_allow_html=True)
