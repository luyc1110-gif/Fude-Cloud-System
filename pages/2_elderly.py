import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random

# =========================================================
# 0) 系統設定 (必須放在最前面)
# =========================================================
st.set_page_config(page_title="長輩關懷系統", page_icon="👴", layout="wide", initial_sidebar_state="collapsed")

# 🔥 核心修復：防止 AttributeError
if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#B5838D"   # 莫蘭迪暮色粉
ACCENT  = "#6D597A"   # 莫蘭迪煙燻紫
BG_MAIN = "#F8F9FA"

# =========================================================
# 1) CSS 樣式 (V33.0 文字對比極大化)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 🔥 數據大看板：強制文字變白，增加陰影 */
.metric-box {{
    padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.metric-box div, .metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}
.m-title {{ font-size: 1.2rem; opacity: 0.9; margin-bottom: 10px; }}
.m-value {{ font-size: 3.5rem; }}

/* 下拉選單白底黑字 */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input {{
    background-color: #FFFFFF !important; color: #000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000 !important; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {ACCENT} !important;
    border: 2px solid {ACCENT} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {ACCENT} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
M_COLS = ["姓名", "身分證字號", "性別", "出生年月日", "電話", "地址", "備註", "加入日期"]
L_COLS = ["姓名", "身分證字號", "日期", "時間", "課程分類", "課程名稱", "收縮壓", "舒張壓", "脈搏"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        target = M_COLS if sheet_name == 'elderly_members' else L_COLS
        for c in target: 
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=M_COLS if sheet_name == 'elderly_members' else L_COLS)

def save_data(df, sheet_name):
    try:
        df_to_save = df.fillna("").replace(['nan', 'NaN', 'nan.0'], "").astype(str)
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        load_data.clear()
        return True
    except Exception as e: st.error(f"寫入失敗：{e}"); return False

def get_tw_time(): return datetime.now(TW_TZ)

# =========================================================
# 3) UI 渲染
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 長輩首頁", use_container_width=True): st.session_state.page='home'; st.rerun()
    with c2:
        if st.button("📋 名冊管理", use_container_width=True): st.session_state.page='members'; st.rerun()
    with c3:
        if st.button("🩸 據點報到", use_container_width=True): st.session_state.page='checkin'; st.rerun()
    with c4:
        if st.button("📊 統計數據", use_container_width=True): st.session_state.page='stats'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.page == 'home':
    if st.button("🚪 回系統大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷據點系統</h1>", unsafe_allow_html=True)
    
    logs, members = load_data("elderly_logs"), load_data("elderly_members")
    this_year, today_str = get_tw_time().year, get_tw_time().strftime("%Y-%m-%d")
    
    # 計算人次
    y_count = len(logs[pd.to_datetime(logs['日期'], errors='coerce').dt.year == this_year]) if not logs.empty else 0
    t_count = len(logs[logs['日期'] == today_str]) if not logs.empty else 0

    st.markdown(f"### 📅 據點數據看板 ({today_str})")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="metric-box" style="background: linear-gradient(135deg, #B5838D 0%, #6D597A 100%);"><div class="m-title">📅 {this_year} 年度總服務人次</div><div class="m-value">{y_count}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-box" style="background: linear-gradient(135deg, #E5989B 0%, #B5838D 100%);"><div class="m-title">☀️ 今日服務人次</div><div class="m-value">{t_count}</div></div>""", unsafe_allow_html=True)

elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 統計數據分析")
    members, logs = load_data("elderly_members"), load_data("elderly_logs")
    
    if not logs.empty:
        logs['dt'] = pd.to_datetime(logs['日期'], errors='coerce')
        d_range = st.date_input("選擇區間", value=(date(date.today().year, 1, 1), date.today()))
        
        if isinstance(d_range, tuple) and len(d_range) == 2:
            f_logs = logs[(logs['dt'].dt.date >= d_range[0]) & (logs['dt'].dt.date <= d_range[1])].copy()
            
            # 🔥 靈動泡泡圖實現 (去重場次)
            unique_sessions = f_logs.drop_duplicates(subset=['日期', '課程名稱']).copy()
            unique_sessions['大分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[0] if '-' in x else x)
            main_cts = unique_sessions['大分類'].value_counts().reset_index()
            main_cts.columns = ['類別', '場次']

            st.markdown("### 🫧 課程場次佔比 (靈動泡泡圖)")
            # 隨機座標生成
            random.seed(42)
            main_cts['x'] = [random.uniform(0, 10) for _ in range(len(main_cts))]
            main_cts['y'] = [random.uniform(0, 10) for _ in range(len(main_cts))]
            main_cts['顯示'] = main_cts['類別'] + '<br>' + main_cts['場次'].astype(str) + '場'

            fig = px.scatter(main_cts, x="x", y="y", size="場次", color="類別", text="顯示", size_max=80, color_discrete_sequence=px.colors.sequential.RdPu)
            fig.update_traces(textposition='middle center', textfont=dict(size=14, color='white'))
            fig.update_layout(showlegend=False, xaxis=dict(showticklabels=False, title=""), yaxis=dict(showticklabels=False, title=""), height=400, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(main_cts[['類別', '場次']], use_container_width=True)

# 報到與名冊代碼同上，以此架構類推
