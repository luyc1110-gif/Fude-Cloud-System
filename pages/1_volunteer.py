import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 核心初始化 (必須在最前面，解決 AttributeError)
# =========================================================
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#9A8C98"   # 莫蘭迪煙燻紫
ACCENT  = "#4A4E69"   # 深藍灰
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (莫蘭迪 + 高對比白字)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 數據看板：強制純白字 */
.vol-metric-box {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
    padding: 35px; border-radius: 25px; color: #FFFFFF !important; text-align: center; margin-bottom: 25px;
    box-shadow: 0 8px 25px rgba(154, 140, 152, 0.2);
}}
.vol-metric-box div, .vol-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 下拉選單與輸入框 (強制白底黑字) */
.stTextInput input, .stDateInput input, .stTimeInput input, div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; color: #000 !important;
    border: 2px solid #BCB4B4 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000 !important; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {ACCENT} !important;
    border: 2px solid {ACCENT} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {ACCENT} !important; color: white !important; }}

/* 卡片容器 */
.dash-card {{ background-color: white; padding: 18px; border-radius: 18px; border-left: 6px solid {PRIMARY}; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 12px; }}
.custom-card {{ background-color: white; border-radius: 20px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid white; margin-bottom: 20px; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯 (解決 KeyError: '日期' & nan 報錯)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
M_COLS = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]
L_COLS = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_data(sn):
    try:
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        target = M_COLS if sn == 'members' else L_COLS
        for c in target: 
            if c not in df.columns: df[c] = "" # 🔥 自動補齊遺失欄位
        return df
    except: return pd.DataFrame(columns=M_COLS if sn == 'members' else L_COLS)

def save_data(df, sn):
    try:
        # 🔥 徹底清洗 nan
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear(); sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        load_data.clear(); return True
    except Exception as e: st.error(f"寫入失敗：{e}"); return False

def calculate_age(b_str):
    try:
        bd = datetime.strptime(str(b_str).strip(), "%Y-%m-%d")
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return 0

def check_is_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'), ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any = False; active = False
    for j, e in roles:
        if str(row.get(j, "")).strip():
            has_any = True
            if not str(row.get(e, "")).strip(): active = True
    return has_any and not active

def calculate_hours_logic(logs_df, year):
    if logs_df.empty or '日期' not in logs_df.columns: return 0
    df = logs_df.copy()
    df['dt'] = pd.to_datetime(df['日期'] + ' ' + df['時間'], errors='coerce')
    df = df.dropna(subset=['dt'])
    y_logs = df[df['dt'].dt.year == year].sort_values(['姓名', 'dt'])
    total_sec = 0
    for (n, d), g in y_logs.groupby(['姓名', '日期']):
        acts, ts = g['動作'].tolist(), g['dt'].tolist()
        i = 0
        while i < len(acts):
            if acts[i] == '簽到':
                for j in range(i + 1, len(acts)):
                    if acts[j] == '簽退':
                        total_sec += (ts[j] - ts[i]).total_seconds()
                        i = j; break
            i += 1
    return total_sec

# =========================================================
# 3) UI 頁面路由
# =========================================================
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

# --- [分頁 1：首頁] ---
if st.session_state.page == 'home':
    if st.button("🚪 回系統大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    logs, mems = load_data("logs"), load_data("members")
    total_sec = calculate_hours_logic(logs, datetime.now().year)
    h, m = int(total_sec // 3600), int((total_sec % 3600) // 60)
    st.markdown(f'<div class="vol-metric-box"><div>📅 {datetime.now().year} 年度全體志工總時數</div><div style="font-size:4rem;">{h} 小時 {m} 分</div></div>', unsafe_allow_html=True)
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        c1, c2, c3, c4 = st.columns(4)
        cats = ["祥和", "據點週二", "據點週三", "環保"]
        for i, cat in enumerate(cats):
            sub = mems[mems['志工分類'].str.contains(cat, na=False)]
            avg = round(sub[sub['age']>0]['age'].mean(), 1) if not sub[sub['age']>0].empty else 0
            with [c1,c2,c3,c4][i]:
                st.markdown(f'<div class="dash-card"><div style="color:#666;font-weight:bold;">{cat}</div><div style="font-size:1.8rem;color:{ACCENT};font-weight:900;">{len(sub)} 人</div><div style="font-size:0.9rem;color:#888;">平均 {avg} 歲</div></div>', unsafe_allow_html=True)

# --- [分頁 2：智能打卡] ---
elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'checkin_msg' not in st.session_state: st.session_state.checkin_msg = (None, None)

    with st.container(border=True):
        st.markdown("#### 1. 設定執勤活動與日期 (補登請先修改日期時間)")
        c1, c2, c3 = st.columns([1.5, 1.5, 2])
        with c1: raw_act = st.selectbox("📌 選擇活動", ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"])
        with c2: t_date = st.date_input("執勤日期", value=date.today())
        with c3: t_time = st.time_input("執勤時間", value=datetime.now(TW_TZ).time())
        note = st.text_input("📝 活動名稱 (選填)") if "專案" in raw_act or "教育" in raw_act else ""

    with st.container(border=True):
        st.markdown("#### 2. 志工刷卡區 (支援條碼槍)")
        mt, mx = st.session_state.checkin_msg
        if mt == "error": st.error(mx)
        elif mt == "success": st.success(mx)

        def process_scan():
            pid = st.session_state.input_pid.strip().upper()
            if not pid: return
            df_m, df_l, d_s = load_data("members"), load_data("logs"), t_date.strftime("%Y-%m-%d")
            person = df_m[df_m['身分證字號'] == pid]
            if person.empty: st.session_state.checkin_msg = ("error", "❌ 查無此人")
            else:
                name = person.iloc[0]['姓名']
                t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == d_s)]
                act = "簽退" if (not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到") else "簽到"
                new = {'姓名':name, '身分證字號':pid, '動作':act, '時間':t_time.strftime("%H:%M:%S"), '日期':d_s, '活動內容':f"{raw_act}-{note}"}
                if save_data(pd.concat([df_l, pd.DataFrame([new])], ignore_index=True), "logs"):
                    st.session_state.checkin_msg = ("success", f"✅ {name} {act}成功 ({d_s})")
            st.session_state.input_pid = ""
        st.text_input("請掃描身分證條碼", key="input_pid", on_change=process_scan)

    logs_v = load_data("logs")
    d_s = t_date.strftime("%Y-%m-%d")
    day_logs = logs_v[logs_v['日期'] == d_s]
    if not day_logs.empty:
        st.markdown(f"### 📋 {d_s} 志工名單")
        edited = st.data_editor(day_logs.sort_values('時間', ascending=False), use_container_width=True, num_rows="dynamic", key="log_edit")
        if st.button("💾 儲存修改"):
            logs_v.update(edited); save_data(logs_v, "logs"); st.success("已更新！")

# --- [分頁 3：志工名冊] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊維護")
    df = load_data("members")
    with st.expander("➕ 新增志工"):
        with st.form("add_v"):
            c1, c2, c3 = st.columns(3); n, p, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.text_input("生日 (YYYY-MM-DD)")
            addr, ph = st.text_input("地址"), st.text_input("電話")
            if st.form_submit_button("確認新增"):
                if save_data(pd.concat([df, pd.DataFrame([{'姓名':n, '身分證字號':p.upper(), '生日':b, '電話':ph, '地址':addr}])], ignore_index=True), "members"): st.success("成功！"); st.rerun()
    if not df.empty:
        df['狀態'] = df.apply(lambda r: '服務中' if not check_is_retired(r) else '已退隊', axis=1)
        t1, t2 = st.tabs(["🔥 服務中", "🍂 已退隊"])
        with t1: st.data_editor(df[df['狀態']=='服務中'], use_container_width=True, num_rows="dynamic")
        with t2: st.data_editor(df[df['狀態']=='已退隊'], use_container_width=True, num_rows="dynamic")

# --- [分頁 4：數據分析] ---
elif st.session_state.page == 'report':
    render_nav()
    st.markdown("## 📊 數據分析")
    logs = load_data("logs")
    if not logs.empty:
        d_range = st.date_input("選擇統計區間", value=(date(date.today().year, 1, 1), date.today()))
        if isinstance(d_range, tuple) and len(d_range) == 2:
            logs['dt_obj'] = pd.to_datetime(logs['日期'], errors='coerce')
            f_logs = logs[(logs['dt_obj'].dt.date >= d_range[0]) & (logs['dt_obj'].dt.date <= d_range[1])].copy()
            st.markdown("### 🫧 活動分布 (靈動泡泡圖)")
            u_sessions = f_logs.drop_duplicates(subset=['日期', '活動內容']).copy()
            cts = u_sessions['活動內容'].value_counts().reset_index(); cts.columns = ['活動', '場次']
            random.seed(42); cts['x'], cts['y'] = [random.uniform(0,10) for _ in range(len(cts))], [random.uniform(0,10) for _ in range(len(cts))]
            cts['label'] = cts['活動'] + '<br>' + cts['場次'].astype(str) + '場'
            fig = px.scatter(cts, x="x", y="y", size="場次", color="活動", text="label", size_max=70, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='middle center', textfont=dict(size=14, color='black'))
            fig.update_layout(showlegend=False, height=450, xaxis=dict(showticklabels=False, title=""), yaxis=dict(showticklabels=False, title=""), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
