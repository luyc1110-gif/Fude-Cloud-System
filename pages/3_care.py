import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 核心初始化
# =========================================================
st.set_page_config(page_title="關懷戶管理系統", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#8E9775"   # 苔蘚綠
ACCENT  = "#6D6875"   # 灰紫色
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (強力顯色修復版)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 🔥 強制下拉選單背景為白、字體為黑 */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
/* 選單展開後的樣式 */
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}

/* 表格白底黑字 */
div[data-testid="stDataFrame"] {{ background-color: #FFFFFF !important; border-radius: 10px; padding: 10px; }}
.stDataFrame div, .stDataFrame span {{ color: #000000 !important; }}

/* 數據看板 */
.care-metric-box {{
    padding: 30px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {PRIMARY} !important; color: white !important; }}
.dash-card {{ background-color: white; padding: 15px; border-radius: 15px; border-left: 6px solid {PRIMARY}; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯 (加強快取同步)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=30) # 🔥 縮短 TTL 以防資料讀取延遲
def load_data(sn, target_cols):
    try:
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=target_cols)

def save_data(df, sn):
    try:
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear(); sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        st.cache_data.clear(); return True # 🔥 強制清空快取
    except Exception as e:
        st.error(f"寫入失敗：{e}"); return False

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today(); return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) 頁面渲染
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    pages = [("🏠 首頁", 'home'), ("📋 名冊", 'members'), ("🏥 健康", 'health'), ("📦 物資", 'inventory'), ("🤝 訪視", 'visit'), ("📊 統計", 'stats')]
    for i, (label, p_key) in enumerate(pages):
        with [c1, c2, c3, c4, c5, c6][i]:
            if st.button(label, use_container_width=True, key=f"nav_{p_key}"): 
                st.session_state.page = p_key; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- [首頁：年度對比看板] ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    render_nav()
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    
    cur_y = datetime.now().year
    last_y = cur_y - 1
    
    if not logs.empty:
        logs['dt'] = pd.to_datetime(logs['發放日期'], errors='coerce')
        cur_total = logs[logs['dt'].dt.year == cur_y]['發放數量'].replace("", "0").astype(float).sum()
        last_total = logs[logs['dt'].dt.year == last_y]['發放數量'].replace("", "0").astype(float).sum()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>📅 {cur_y} 當年度發放總量</div><div style="font-size:3.5rem;">{int(cur_total)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>⏳ {last_y} 上年度發放總量</div><div style="font-size:3.5rem;">{int(last_total)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)

    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        dis_c = len(mems[mems['身分別'].str.contains("身障", na=False)])
        st.markdown(f'<div class="dash-card"><b>基本統計</b><br>關懷戶總數：{len(mems)} 人<br>身障人數：{dis_c} 人<br>平均年齡：{round(mems["age"].mean(),1)} 歲</div>', unsafe_allow_html=True)

# --- [名冊管理：性別與聯絡人回歸] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    with st.expander("➕ 新增關懷戶資料"):
        with st.form("add_care"):
            c1, c2, c3, c4 = st.columns(4)
            n, p, g, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.selectbox("性別", ["男", "女"]), c4.date_input("生日", value=date(1950, 1, 1))
            addr, ph = st.text_input("地址"), st.text_input("電話")
            ce1, ce2 = st.columns(2)
            en = ce1.text_input("緊急聯絡人")
            ep = ce2.text_input("緊急聯絡人電話")
            if st.form_submit_button("確認新增"):
                new = {"姓名":n, "身分證字號":p.upper(), "性別":g, "生日":str(b), "地址":addr, "電話":ph, "緊急聯絡人":en, "緊急聯絡人電話":ep}
                if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"): st.success("成功"); st.rerun()
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        edited = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
        if st.button("💾 儲存名冊修改"): 
            if save_data(edited, "care_members"): st.success("已更新")

# --- [健康指標：完整欄位回歸] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康指標管理")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 登記健康指標數據"):
        with st.form("add_h"):
            sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            dent = c1.selectbox("是否有假牙", ["無", "有"])
            wash = c2.selectbox("今年洗牙", ["否", "是"])
            grip = c3.text_input("握力 (kg)")
            h = c4.text_input("身高 (cm)")
            w = c5.text_input("體重 (kg)")
            hear = c6.selectbox("聽力測試", ["正常", "需注意"])
            if st.form_submit_button("儲存健康紀錄"):
                pid = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                new = {"姓名":sel_n, "身分證字號":pid, "是否有假牙":dent, "今年洗牙":wash, "握力":grip, "身高":h, "體重":w, "聽力測試":hear}
                if save_data(pd.concat([h_df, pd.DataFrame([new])], ignore_index=True), "care_health"): st.success("已存檔"); st.rerun()
    
    if not h_df.empty:
        edited_h = st.data_editor(h_df, use_container_width=True, num_rows="dynamic", key="h_edit")
        if st.button("💾 儲存修改"): save_data(edited_h, "care_health")

# --- [訪視發放：資料救援機制] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    mems, inv, logs = load_data("care_members", COLS_MEM), load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    
    with st.container(border=True):
        st.markdown("#### 🎁 新增發放紀錄")
        c1, c2, c3 = st.columns(3)
        v = st.selectbox("執行志工", load_data("members", ["姓名"])['姓名'].tolist() if not load_data("members", ["姓名"]).empty else ["無資料"])
        d = st.date_input("日期", value=date.today())
        p = st.selectbox("領取戶", mems['姓名'].tolist() if not mems.empty else ["無名冊"])
        sel_i = st.selectbox("選擇物資", ["(僅訪視)"] + inv['物資內容'].unique().tolist())
        sel_q = st.number_input("數量", min_value=0, value=1)
        note = st.text_area("訪視紀錄")
        if st.button("確認提交紀錄"):
            new = {"志工":v, "發放日期":str(d), "關懷戶姓名":p, "物資內容":sel_i, "發放數量":sel_q, "訪視紀錄":note}
            if save_data(pd.concat([logs, pd.DataFrame([new])], ignore_index=True), "care_logs"):
                st.success("✅ 存檔成功！資料已同步至雲端庫存。"); time.sleep(1); st.rerun()

    if not logs.empty:
        st.markdown("### 📋 歷史清單")
        ed_logs = st.data_editor(logs.sort_values('發放日期', ascending=False), use_container_width=True, num_rows="dynamic", key="log_ed")
        if st.button("💾 儲存修改紀錄"): save_data(ed_logs, "care_logs")

# --- [數據統計] ---
elif st.session_state.page == 'stats':
    render_nav()
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    if not inv.empty:
        fig = px.bar(inv.groupby('物資類型')['總數量'].apply(lambda x: x.astype(float).sum()).reset_index(), x='物資類型', y='總數量', title="各類物資捐贈統計")
        st.plotly_chart(fig, use_container_width=True)
