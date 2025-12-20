import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import os
import plotly.express as px
import random

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide", initial_sidebar_state="collapsed")
TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪煙燻紫 - 視覺強化
PRIMARY = "#9A8C98"   
ACCENT  = "#4A4E69"   
BG_MAIN = "#F8F9FA"   
TEXT_BLACK = "#1A1A1A" # 強制黑字
TEXT_WHITE = "#FFFFFF" # 強制白字

# =========================================================
# 1) CSS 樣式 (V32.0 視覺強化)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: {TEXT_BLACK} !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 下拉選單與輸入框 (強制白底黑字) */
.stTextInput input, .stDateInput input, .stTimeInput input, div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #BCB4B4 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {ACCENT} !important;
    border: 2px solid {ACCENT} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {ACCENT} !important; color: white !important; }}

/* 🔥 大看板：強制白字 */
.big-card {{
    background: linear-gradient(135deg, #9A8C98 0%, #4A4E69 100%);
    padding: 35px; border-radius: 25px; color: white !important; text-align: center; margin-bottom: 25px;
    box-shadow: 0 10px 20px rgba(74, 78, 105, 0.2);
}}
.big-card div, .big-card span {{ color: white !important; font-weight: 900 !important; }}

/* 小名牌卡片 */
.dash-card {{
    background-color: white; padding: 18px; border-radius: 18px; border-left: 6px solid {PRIMARY};
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 12px;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
M_COLS = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]
L_COLS = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        # 🔥 防呆：補齊遺失標題，避免 KeyError: '日期'
        target = M_COLS if sheet_name == 'members' else L_COLS
        for c in target: 
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=M_COLS if sheet_name == 'members' else L_COLS)

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

def calculate_hours_year(logs_df, year):
    if logs_df.empty or '日期' not in logs_df.columns: return 0
    df = logs_df.copy()
    df['dt'] = pd.to_datetime(df['日期'] + ' ' + df['時間'], errors='coerce')
    df = df.dropna(subset=['dt'])
    year_logs = df[df['dt'].dt.year == year].sort_values(['姓名', 'dt'])
    total_sec = 0
    for (name, d), g in year_logs.groupby(['姓名', '日期']):
        actions, times = g['動作'].tolist(), g['dt'].tolist()
        i = 0
        while i < len(actions):
            if actions[i] == '簽到':
                for j in range(i + 1, len(actions)):
                    if actions[j] == '簽退':
                        total_sec += (times[j] - times[i]).total_seconds()
                        i = j; break
            i += 1
    return total_sec

# =========================================================
# 3) UI
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 首頁", use_container_width=True): st.session_state.page='home'; st.rerun()
    with c2:
        if st.button("⏰ 打卡", use_container_width=True): st.session_state.page='checkin'; st.rerun()
    with c3:
        if st.button("📋 名冊", use_container_width=True): st.session_state.page='members'; st.rerun()
    with c4:
        if st.button("📊 數據", use_container_width=True): st.session_state.page='report'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.page == 'home':
    if st.button("🚪 回系統大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center; color: #444;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    logs, members = load_data("logs"), load_data("members")
    this_year = datetime.now().year
    total_sec = calculate_hours_year(logs, this_year)
    h, m = int(total_sec // 3600), int((total_sec % 3600) // 60)
    
    st.markdown(f"""
    <div class="big-card">
        <div style="font-size: 1.2rem; opacity: 0.9;">📅 {this_year} 年度總服務時數</div>
        <div style="font-size: 4rem; font-weight: 900; margin: 10px 0;">{h} <span style="font-size: 1.5rem;">小時</span> {m} <span style="font-size: 1.5rem;">分</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 志工人數統計卡片
    active_m = members[members['姓名'] != ""] # 簡單過濾
    c1, c2, c3, c4 = st.columns(4)
    cats = ["祥和", "關懷據點週二", "關懷據點週三", "環保"]
    for i, cat in enumerate(cats):
        count = len(active_m[active_m['志工分類'].str.contains(cat, na=False)])
        with [c1,c2,c3,c4][i]:
            st.markdown(f"""<div class="dash-card"><div style="color:#666;font-weight:bold;">{cat}</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{count} 人</div></div>""", unsafe_allow_html=True)

elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    
    with st.container(border=True):
        st.markdown("#### 1. 設定項目")
        c1, c2 = st.columns(2)
        with c1: raw_act = st.selectbox("📌 執勤項目", ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"])
        with c2: target_date = st.date_input("執勤日期", value=date.today())
        note = st.text_input("📝 活動名稱 (選填)") if "專案" in raw_act or "教育" in raw_act else ""

    with st.container(border=True):
        st.markdown("#### 2. 刷卡區")
        
        def process_scan():
            pid = st.session_state.input_pid.strip().upper()
            if not pid: return
            df_m, df_l = load_data("members"), load_data("logs")
            d_str = target_date.strftime("%Y-%m-%d")
            person = df_m[df_m['身分證字號'] == pid]
            if person.empty: st.error("❌ 查無此人")
            else:
                row = person.iloc[0]; name = row['姓名']
                # 判定簽到或簽退
                t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == d_str)]
                action = "簽退" if (not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到") else "簽到"
                new_log = {'姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'], '動作': action, '時間': datetime.now(TW_TZ).strftime("%H:%M:%S"), '日期': d_str, '活動內容': f"{raw_act}-{note}"}
                if save_data(pd.concat([df_l, pd.DataFrame([new_log])], ignore_index=True), "logs"):
                    st.success(f"✅ {name} {action}成功")
            st.session_state.input_pid = ""

        st.text_input("請掃描身分證條碼 (條碼槍對準處)", key="input_pid", on_change=process_scan)

    # 顯示當天名單
    logs_view = load_data("logs")
    d_str = target_date.strftime("%Y-%m-%d")
    if '日期' in logs_view.columns:
        day_logs = logs_view[logs_view['日期'] == d_str].sort_values('時間', ascending=False)
        if not day_logs.empty:
            st.markdown(f"### 📋 {d_str} 報到名單")
            edited = st.data_editor(day_logs, use_container_width=True, num_rows="dynamic", key="v_log_edit")
            if st.button("💾 儲存名單修改"):
                logs_view.update(edited) # 這裡簡單處理更新
                save_data(logs_view, "logs")

# 名冊與報表略，以此類推修正
