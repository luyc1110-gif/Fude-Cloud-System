import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random

# =========================================================
# 0) 系統設定與初始化 (解決 AttributeError)
# =========================================================
st.set_page_config(
    page_title="志工管理系統",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪煙燻紫配色
PRIMARY = "#9A8C98"   # 煙燻紫
ACCENT  = "#4A4E69"   # 深藍灰
BG_MAIN = "#F8F9FA"   
TEXT_DARK = "#333333"
TEXT_LIGHT = "#FFFFFF"

# =========================================================
# 1) CSS 樣式 (莫蘭迪 + 高對比)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: {TEXT_DARK} !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 下拉選單與輸入框 (白底黑字高對比) */
.stTextInput input, .stDateInput input, .stTimeInput input, div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #BCB4B4 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {PRIMARY} !important; color: white !important; }}

/* 🔥 年度時數大卡片：強制白字 */
.vol-metric-box {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
    padding: 35px; border-radius: 25px; color: {TEXT_LIGHT} !important; text-align: center; margin-bottom: 25px;
    box-shadow: 0 8px 25px rgba(154, 140, 152, 0.2);
}}
.vol-metric-box div, .vol-metric-box span {{ color: {TEXT_LIGHT} !important; font-weight: 900 !important; }}

/* 小統計卡片 */
.dash-card {{
    background-color: white; padding: 18px; border-radius: 18px; border-left: 6px solid {PRIMARY};
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 12px;
}}
.custom-card {{
    background-color: white; border-radius: 20px; padding: 25px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid white; margin-bottom: 20px;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯 (防呆修復 KeyError 與 NaN)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]
M_COLS = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]
L_COLS = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_data(sheet_name):
    try:
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        target = M_COLS if sheet_name == 'members' else L_COLS
        for c in target: 
            if c not in df.columns: df[c] = "" # 🔥 修復 KeyError
        return df
    except: return pd.DataFrame(columns=M_COLS if sheet_name == 'members' else L_COLS)

def save_data(df, sheet_name):
    try:
        # 🔥 修復 nan 錯誤：儲存前清空非法值
        df_to_save = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}")
        return False

def calculate_age(b_str):
    try:
        b_date = datetime.strptime(str(b_str).strip(), "%Y-%m-%d")
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

def check_is_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'), ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any = False; is_active = False
    for join, exit in roles:
        if str(row.get(join, "")).strip():
            has_any = True
            if not str(row.get(exit, "")).strip(): is_active = True
    return has_any and not is_active

def calculate_hours_logic(logs_df, year):
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
# 3) 導航列與 UI
# =========================================================
def render_nav():
    st.markdown('<div class="nav-container" style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 志工首頁", use_container_width=True): st.session_state.page='home'; st.rerun()
    with c2:
        if st.button("⏰ 智能打卡", use_container_width=True): st.session_state.page='checkin'; st.rerun()
    with c3:
        if st.button("📋 志工名冊", use_container_width=True): st.session_state.page='members'; st.rerun()
    with c4:
        if st.button("📊 數據分析", use_container_width=True): st.session_state.page='report'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 頁面：首頁 ---
if st.session_state.page == 'home':
    c_back, _ = st.columns([1, 4])
    with c_back:
        if st.button("🚪 回系統大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    logs, members = load_data("logs"), load_data("members")
    this_year = datetime.now().year
    total_sec = calculate_hours_logic(logs, this_year)
    h, m = int(total_sec // 3600), int((total_sec % 3600) // 60)
    
    st.markdown(f"""
    <div class="vol-metric-box">
        <div style="font-size: 1.2rem; opacity: 0.9;">📅 {this_year} 年度全體志工總服務時數</div>
        <div style="font-size: 4rem; font-weight: 900; margin: 10px 0;">
            {h} <span style="font-size: 1.5rem;">小時</span> {m} <span style="font-size: 1.5rem;">分</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not members.empty:
        members['age'] = members['生日'].apply(calculate_age)
        c1, c2, c3, c4 = st.columns(4)
        cats = ["祥和", "據點週二", "據點週三", "環保"]
        for i, cat in enumerate(cats):
            subset = members[members['志工分類'].str.contains(cat, na=False)]
            count = len(subset)
            avg_age = round(subset[subset['age']>0]['age'].mean(), 1) if not subset[subset['age']>0].empty else 0
            with [c1,c2,c3,c4][i]:
                st.markdown(f"""
                <div class="dash-card">
                    <div style="color:#666;font-weight:bold;">{cat}志工</div>
                    <div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{count} 人</div>
                    <div style="font-size:0.9rem;color:#888;">平均 {avg_age} 歲</div>
                </div>
                """, unsafe_allow_html=True)

# --- 頁面：打卡 ---
elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'checkin_msg' not in st.session_state: st.session_state.checkin_msg = (None, None)

    st.markdown('<div class="custom-card" style="border-left: 6px solid #9A8C98;">', unsafe_allow_html=True)
    st.markdown("#### 1. 設定執勤活動與日期")
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    with c1: raw_act = st.selectbox("📌 活動項目", DEFAULT_ACTIVITIES)
    with c2: target_date = st.date_input("執勤日期", value=date.today())
    with c3: note = st.text_input("📝 活動名稱 (選填)") if "專案" in raw_act or "教育" in raw_act else ""
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    ct, cm = st.columns([2, 3])
    with ct: st.markdown("#### 2. 志工刷卡 (支援條碼槍)")
    with cm:
        mt, mx = st.session_state.checkin_msg
        if mt == "error": st.error(mx)
        elif mt == "success": st.success(mx)

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
            new_log = {'姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'], '動作': action, '時間': datetime.now(TW_TZ).strftime("%H:%M:%S"), '日期': d_str, '活動內容': final_act}
            if save_data(pd.concat([df_l, pd.DataFrame([new_log])], ignore_index=True), "logs"):
                st.session_state.checkin_msg = ("success", f"✅ {name} {action}成功 ({d_str})")
        st.session_state.input_pid = ""

    st.text_input("身分證字號掃描區", key="input_pid", on_change=process_scan)
    st.markdown('</div>', unsafe_allow_html=True)

    logs_view = load_data("logs")
    d_str = target_date.strftime("%Y-%m-%d")
    if not logs_view[logs_view['日期'] == d_str].empty:
        st.markdown(f"### 📋 {d_str} 志工進出名單")
        day_df = logs_view[logs_view['日期'] == d_str].sort_values('時間', ascending=False)
        edited = st.data_editor(day_df, use_container_width=True, num_rows="dynamic", key="v_log_edit")
        if st.button("💾 儲存修改"):
            logs_view[logs_view['日期'] == d_str] = edited
            if save_data(logs_view, "logs"): st.success("紀錄已更新！")

# --- 頁面：名冊 ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊維護")
    df = load_data("members")
    with st.expander("➕ 新增志工資料"):
        with st.form("add_v"):
            c1, c2, c3 = st.columns(3); n, p, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.text_input("生日 (YYYY-MM-DD)")
            addr, ph = st.text_input("地址"), st.text_input("電話")
            if st.form_submit_button("確認新增"):
                new = pd.DataFrame([{'姓名':n, '身分證字號':p.upper(), '生日':b, '電話':ph, '地址':addr}])
                if save_data(pd.concat([df, new], ignore_index=True), "members"): st.success("成功！"); st.rerun()
    if not df.empty:
        df['狀態'] = df.apply(lambda r: '服務中' if check_is_retired(r) else '已退隊', axis=1)
        t1, t2 = st.tabs(["🔥 服務中", "🍂 已退隊"])
        with t1: st.data_editor(df[df['狀態']=='服務中'], use_container_width=True, num_rows="dynamic", key="v_active_edit")
        with t2: st.data_editor(df[df['狀態']=='已退隊'], use_container_width=True, num_rows="dynamic", key="v_retired_edit")

# --- 頁面：數據 ---
elif st.session_state.page == 'report':
    render_nav()
    st.markdown("## 📊 數據分析")
    logs = load_data("logs")
    if not logs.empty:
        d_range = st.date_input("📅 統計區間", value=(date(date.today().year, 1, 1), date.today()))
        if isinstance(d_range, tuple) and len(d_range) == 2:
            logs['dt_obj'] = pd.to_datetime(logs['日期'], errors='coerce')
            f_logs = logs[(logs['dt_obj'].dt.date >= d_range[0]) & (logs['dt_obj'].dt.date <= d_range[1])].copy()
            st.markdown("### 🫧 活動分布占比 (靈動泡泡圖)")
            unique_sessions = f_logs.drop_duplicates(subset=['日期', '活動內容']).copy()
            counts = unique_sessions['活動內容'].value_counts().reset_index()
            counts.columns = ['活動', '場次']
            random.seed(42); counts['x'], counts['y'] = [random.uniform(0,10) for _ in range(len(counts))], [random.uniform(0,10) for _ in range(len(counts))]
            counts['label'] = counts['活動'] + '<br>' + counts['場次'].astype(str) + '場'
            fig = px.scatter(counts, x="x", y="y", size="場次", color="活動", text="label", size_max=70, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='middle center', textfont=dict(size=14, color='black'))
            fig.update_layout(showlegend=False, height=400, xaxis=dict(showticklabels=False, title=""), yaxis=dict(showticklabels=False, title=""), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
