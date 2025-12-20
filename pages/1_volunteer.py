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
st.set_page_config(
    page_title="志工管理系統",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪煙燻紫配色 (對比強化版)
PRIMARY = "#9A8C98"   # 莫蘭迪主色
ACCENT  = "#4A4E69"   # 深色點綴色
BG_MAIN = "#F8F9FA"   # 極淺灰底
TEXT_DARK = "#333333" # 標題與標籤深色
TEXT_LIGHT = "#FFFFFF" # 背景深色時的反白字

# =========================================================
# 1) CSS 樣式 (V31.0 高對比莫蘭迪)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT_DARK} !important;
}}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 下拉選單與輸入框 (白底黑字) */
.stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input, div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; 
    color: #000000 !important;
    border: 1.5px solid #D1D1D1 !important; 
    border-radius: 12px !important;
    font-weight: 700 !important;
}}
div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ color: #000000 !important; }}

/* 標籤顏色 */
label {{
    color: {ACCENT} !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    margin-bottom: 8px !important;
}}

/* 導航按鈕：平常白底紫字，滑過深紫反白字 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; 
    color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important; 
    border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important;
    padding: 10px 0 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{
    background-color: {PRIMARY} !important; 
    color: {TEXT_LIGHT} !important; /* 🔥 這裡實現您的建議：背景深時字變白 */
    transform: translateY(-2px);
}}

/* 數據卡片與容器 */
.custom-card {{
    background-color: white; border-radius: 20px; padding: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.03);
    width: 100%; margin-bottom: 20px;
}}
.dash-card {{
    background-color: white; padding: 18px; border-radius: 18px; 
    border-left: 6px solid {PRIMARY};
    box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-bottom: 12px;
}}
.nav-container {{
    background-color: white; padding: 12px; border-radius: 20px;
    margin-bottom: 20px; box-shadow: 0 2px 15px rgba(0,0,0,0.04);
}}

/* Tab 分頁美化 */
div[data-baseweb="tab"] {{
    background-color: transparent; padding: 10px 20px; border-radius: 30px;
    font-weight: bold; color: {PRIMARY} !important;
}}
div[data-baseweb="tab"][aria-selected="true"] {{
    background-color: {PRIMARY} !important;
    color: {TEXT_LIGHT} !important; /* 🔥 反白字體 */
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Sheets
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]
M_COLS = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        if sheet_name == 'members':
            for c in M_COLS: 
                if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame()

def save_data(df, sheet_name):
    try:
        df_to_save = df.copy().replace(['nan', 'NaN', 'nan.0'], "").fillna("")
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}")
        return False

def get_tw_time(): return datetime.now(TW_TZ)

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'), ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any = False
    active = False
    for join, exit in roles:
        if join in row and str(row[join]).strip():
            has_any = True
            if exit not in row or not str(row[exit]).strip(): active = True
    return has_any and not active

def calculate_hours_year(logs_df, year):
    if logs_df.empty: return 0
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
# 3) Navigation
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 志工首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("⏰ 智能打卡", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
    with c3:
        if st.button("📋 志工名冊", use_container_width=True): st.session_state.page = 'members'; st.rerun()
    with c4:
        if st.button("📊 數據分析", use_container_width=True): st.session_state.page = 'report'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4) Pages
# =========================================================
if st.session_state.page == 'home':
    c_back, c_empty = st.columns([1, 4])
    with c_back:
        if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown(f"<h1 style='text-align: center; color: #444; margin-bottom: 30px;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    col_l, c1, c2, c3, col_r = st.columns([1.5, 2, 2, 2, 0.5])
    with c1:
        if st.button("⏰ 智能打卡"): st.session_state.page = 'checkin'; st.rerun()
    with c2:
        if st.button("📋 志工名冊"): st.session_state.page = 'members'; st.rerun()
    with c3:
        if st.button("📊 數據分析"): st.session_state.page = 'report'; st.rerun()

    st.markdown("---")
    logs, members = load_data("logs"), load_data("members")
    this_year = datetime.now().year
    total_sec = calculate_hours_year(logs, this_year)
    h, m = int(total_sec // 3600), int((total_sec % 3600) // 60)
    
    # 🔥 年度服務時數大卡片 (高對比反白字體)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); padding: 35px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;">
        <div style="font-size: 1.2rem; opacity: 0.9; color: {TEXT_LIGHT} !important;">📅 {this_year} 年度總服務時數</div>
        <div style="font-size: 4rem; font-weight: 900; margin: 10px 0; color: {TEXT_LIGHT} !important;">
            {h} <span style="font-size: 1.5rem;">時</span> {m} <span style="font-size: 1.5rem;">分</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not members.empty:
        active_m = members[~members.apply(check_is_fully_retired, axis=1)].copy()
        cols = st.columns(4)
        for idx, cat in enumerate(ALL_CATEGORIES[:4]):
            count = len(active_m[active_m['志工分類'].str.contains(cat, na=False)])
            with cols[idx]:
                st.markdown(f"""<div class="dash-card"><div style="color:#888;font-weight:bold;">{cat.replace('志工','')}</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{count} 人</div></div>""", unsafe_allow_html=True)

elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'checkin_msg' not in st.session_state: st.session_state.checkin_msg = (None, None)

    st.markdown(f'<div class="custom-card" style="border-left: 6px solid {PRIMARY};">', unsafe_allow_html=True)
    st.markdown("#### 1. 設定活動與日期 (補登請先修改日期)")
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    with c1: raw_act = st.selectbox("📌 活動項目", DEFAULT_ACTIVITIES)
    with c2: target_date = st.date_input("執勤日期", value=get_tw_time().date())
    with c3: 
        note = st.text_input("📝 活動名稱", placeholder="專案或訓練名稱") if raw_act in ["專案活動", "教育訓練"] else ""
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    c_t, c_m = st.columns([2, 3])
    with c_t: st.markdown("#### 2. 刷卡區")
    with c_m:
        m_t, m_x = st.session_state.checkin_msg
        if m_t == "error": st.error(m_x)
        elif m_t == "success": st.success(m_x)

    def process_scan():
        pid = st.session_state.input_pid.strip().upper()
        if not pid: return
        df_m, df_l, d_str = load_data("members"), load_data("logs"), target_date.strftime("%Y-%m-%d")
        person = df_m[df_m['身分證字號'] == pid]
        if person.empty: st.session_state.checkin_msg = ("error", "❌ 查無此人")
        else:
            row = person.iloc[0]; name = row['姓名']
            t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == d_str)]
            action = "簽退" if (not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到") else "簽到"
            final_act = f"{raw_act}：{note}" if note else raw_act
            new_log = {'姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'], '動作': action, '時間': get_tw_time().strftime("%H:%M:%S"), '日期': d_str, '活動內容': final_act}
            if save_data(pd.concat([df_l, pd.DataFrame([new_log])], ignore_index=True), "logs"):
                st.session_state.checkin_msg = ("success", f"✅ {name} {action}成功 ({d_str})")
        st.session_state.input_pid = ""

    st.text_input("身分證掃描區", key="input_pid", on_change=process_scan)
    st.markdown('</div>', unsafe_allow_html=True)

    logs_view = load_data("logs")
    d_str = target_date.strftime("%Y-%m-%d")
    day_mask = (logs_view['日期'] == d_str)
    if not logs_view[day_mask].empty:
        st.markdown(f"### 📋 {d_str} 進出名單")
        edited = st.data_editor(logs_view[day_mask].sort_values('時間', ascending=False), use_container_width=True, num_rows="dynamic", key="log_edit")
        if st.button("💾 儲存修改"):
            logs_view[day_mask] = edited
            if save_data(logs_view, "logs"): st.success("已更新！")

elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊維護")
    df = load_data("members")
    with st.expander("➕ 新增志工資料"):
        with st.form("add_v"):
            c1, c2, c3 = st.columns(3)
            n, p, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.text_input("生日 (YYYY-MM-DD)")
            addr, ph = st.text_input("地址"), st.text_input("電話")
            if st.form_submit_button("確認新增"):
                new = pd.DataFrame([{'姓名':n, '身分證字號':p.upper(), '生日':b, '電話':ph, '地址':addr}])
                if save_data(pd.concat([df, new], ignore_index=True), "members"):
                    st.success("成功！"); time.sleep(1); st.rerun()
    
    if not df.empty:
        df['狀態'] = df.apply(lambda r: '已退隊' if check_is_fully_retired(r) else '服務中', axis=1)
        t1, t2 = st.tabs(["🔥 服務中", "🍂 已退隊"])
        with t1: st.data_editor(df[df['狀態']=='服務中'], use_container_width=True, num_rows="dynamic", key="v_active")
        with t2: st.data_editor(df[df['狀態']=='已退隊'], use_container_width=True, num_rows="dynamic", key="v_retired")

elif st.session_state.page == 'report':
    render_nav()
    st.markdown("## 📊 數據分析")
    logs = load_data("logs")
    if logs.empty: st.info("無紀錄")
    else:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        d_range = st.date_input("📅 統計區間", value=(date(date.today().year, 1, 1), date.today()))
        st.markdown('</div>', unsafe_allow_html=True)
        
        if isinstance(d_range, tuple) and len(d_range) == 2:
            logs['dt_obj'] = pd.to_datetime(logs['日期'], errors='coerce')
            f_logs = logs[(logs['dt_obj'].dt.date >= d_range[0]) & (logs['dt_obj'].dt.date <= d_range[1])].copy()
            
            st.markdown("### 🫧 活動分布 (場次占比)")
            unique_sessions = f_logs.drop_duplicates(subset=['日期', '活動內容']).copy()
            counts = unique_sessions['活動內容'].value_counts().reset_index()
            counts.columns = ['活動', '場次']
            
            random.seed(42)
            counts['x'], counts['y'] = [random.uniform(0,10) for _ in range(len(counts))], [random.uniform(0,10) for _ in range(len(counts))]
            counts['label'] = counts['活動'] + '<br>' + counts['場次'].astype(str) + '場'
            
            fig = px.scatter(counts, x="x", y="y", size="場次", color="活動", text="label", size_max=70, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='middle center', textfont=dict(size=13, color='black'))
            fig.update_layout(showlegend=False, height=400, xaxis=dict(showticklabels=False, title=""), yaxis=dict(showticklabels=False, title=""), margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

            summary = []
            for n, g in f_logs.groupby('姓名'):
                sec = calculate_hours_year(g, d_range[0].year)
                summary.append({'姓名': n, '時數': f"{int(sec//3600)}小時 {int((sec%3600)//60)}分", '排序': sec})
            st.dataframe(pd.DataFrame(summary).sort_values('排序', ascending=False)[['姓名', '時數']], use_container_width=True)
