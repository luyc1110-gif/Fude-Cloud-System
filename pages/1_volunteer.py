import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import os
import streamlit.components.v1 as components

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="志工管理系統",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A148C"
ACCENT  = "#7B1FA2"
BG_MAIN = "#F0F2F5" # 背景色 (淺灰)
TEXT    = "#212121"

# =========================================================
# 1) CSS 樣式 (V20.0 懸浮大卡片 + 修復側邊欄 + 男女統計)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}

/* 🔥 1. 整體背景設為淺灰 */
.stApp {{
    background-color: {BG_MAIN} !important;
}}

/* 🔥 2. 側邊欄背景 (跟主背景融合) */
section[data-testid="stSidebar"] {{
    background-color: {BG_MAIN};
    border-right: none; /* 去掉那條死板的分隔線 */
}}

/* 🔥 3. 【關鍵】將主內容區變成一張「懸浮大卡片」 */
.block-container {{
    background-color: #FFFFFF; /* 卡片白底 */
    border-radius: 25px;       /* 圓角 */
    padding: 3rem 3rem !important; /* 內距 */
    box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* 陰影讓它浮起來 */
    margin-top: 2rem;          /* 離頂部一點距離 */
    margin-bottom: 2rem;       /* 離底部一點距離 */
    max-width: 95% !important; /* 寬度佔滿 95%，留邊 */
}}

/* 🔥 4. 修復側邊欄開關 (Header) */
/* 之前隱藏了 header 導致按鈕消失，現在恢復顯示，但讓背景透明 */
header[data-testid="stHeader"] {{
    display: block !important;
    background-color: transparent !important;
}}
/* 隱藏 header 裡面的彩虹線和裝飾，只留按鈕 */
header[data-testid="stHeader"] .decoration {{
    display: none;
}}

/* --- 側邊欄導航按鈕樣式 (膠囊) --- */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important;
    color: #666 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important;
    padding: 10px 0 !important;
    font-weight: 700 !important;
    transition: all 0.2s;
    width: 100%;
    margin-bottom: 8px !important;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    color: {PRIMARY} !important;
}}

.nav-active {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
    color: white !important;
    padding: 12px 0;
    text-align: center;
    border-radius: 25px;
    font-weight: 900;
    box-shadow: 0 4px 10px rgba(123, 31, 162, 0.4);
    margin-bottom: 12px;
    font-size: 1rem;
    cursor: default;
}}

/* --- 內部卡片 (例如統計數字) 微調 --- */
/* 因為底已經是白色的，內部的卡片改用淺灰底或邊框區隔 */
.dash-card {{
    background-color: #F8F9FA; /* 稍微深一點的灰白，跟大白底區隔 */
    padding: 20px; 
    border-radius: 15px; 
    border-left: 6px solid {ACCENT};
    margin-bottom: 15px;
}}
.dash-label {{ font-size: 1.1rem; color: #444 !important; font-weight: bold; margin-bottom: 5px; }}
.dash-value {{ font-size: 2.2rem; color: {PRIMARY} !important; font-weight: 900; margin: 10px 0; }}
.dash-sub {{ font-size: 0.95rem; color: #666 !important; line-height: 1.6; }}

/* 輸入框優化 */
.stTextInput input, .stDateInput input, .stTimeInput input, div[data-baseweb="select"] > div {{
    background-color: #F8F9FA !important; /* 微灰底 */
    border: 1px solid #E0E0E0 !important;
    border-radius: 12px !important;
    color: #333 !important;
}}

/* Toast 美化 */
div[data-baseweb="toast"] {{
    background-color: #FFFFFF !important;
    border: 3px solid {PRIMARY} !important;
    border-radius: 15px !important;
    padding: 15px !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.3) !important;
}}
div[data-baseweb="toast"] * {{
    color: #000000 !important;
    font-weight: 900 !important;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Helpers
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]
DISPLAY_ORDER = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data).astype(str)
        if sheet_name == 'members':
            for c in DISPLAY_ORDER: 
                if c not in df.columns: df[c] = ""
        elif sheet_name == 'logs':
            required = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']
            for c in required: 
                if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        load_data_from_sheet.clear()
    except Exception as e: st.error(f"寫入失敗：{e}")

def get_tw_time(): return datetime.now(TW_TZ)

def calculate_age(birthday_str):
    try:
        b_date = datetime.strptime(str(birthday_str).strip(), "%Y-%m-%d")
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'), ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any = False
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and str(row[join_col]).strip() != "":
            has_any = True
            if exit_col not in row or str(row[exit_col]).strip() == "": is_active = True
    if not has_any: return False 
    return not is_active

def calculate_hours_year(logs_df, year):
    if logs_df.empty: return 0
    logs_df['dt'] = pd.to_datetime(logs_df['日期'] + ' ' + logs_df['時間'], errors='coerce')
    logs_df = logs_df.dropna(subset=['dt'])
    year_logs = logs_df[logs_df['dt'].dt.year == year].copy()
    if year_logs.empty: return 0
    total_seconds = 0
    year_logs = year_logs.sort_values(['姓名', 'dt'])
    for (name, date_val), group in year_logs.groupby(['姓名', '日期']):
        actions = group['動作'].tolist()
        times = group['dt'].tolist()
        i = 0
        while i < len(actions):
            if actions[i] == '簽到':
                for j in range(i + 1, len(actions)):
                    if actions[j] == '簽退':
                        total_seconds += (times[j] - times[i]).total_seconds()
                        i = j
                        break
                i += 1
            else: i += 1
    return total_seconds

def get_present_volunteers(logs_df):
    if logs_df.empty: return pd.DataFrame()
    today = get_tw_time()
    today_str_dash = today.strftime("%Y-%m-%d") 
    today_str_slash = today.strftime("%Y/%m/%d")
    today_logs = logs_df[(logs_df['日期'] == today_str_dash) | (logs_df['日期'] == today_str_slash)].copy()
    if today_logs.empty: return pd.DataFrame()
    today_logs['dt'] = pd.to_datetime(today_logs['日期'] + ' ' + today_logs['時間'], errors='coerce')
    today_logs = today_logs.dropna(subset=['dt'])
    today_logs = today_logs.sort_values('dt')
    latest_status = today_logs.groupby('身分證字號').last().reset_index()
    present = latest_status[latest_status['動作'] == '簽到']
    return present[['姓名', '時間', '活動內容']]

# =========================================================
# 3) Navigation
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    with st.sidebar:
        st.markdown(f"<h2 style='color:{PRIMARY}; margin-bottom:5px; padding-left:10px;'>🏠 福德里志工中心</h2>", unsafe_allow_html=True)
        st.write("") 

        if st.session_state.page == 'home':
            st.markdown('<div class="nav-active">📊 年度概況看板</div>', unsafe_allow_html=True)
        else:
            if st.button("📊 年度概況看板", key="nav_home", use_container_width=True):
                st.session_state.page = 'home'; st.rerun()

        if st.session_state.page == 'checkin':
            st.markdown('<div class="nav-active">⏰ 智能打卡站</div>', unsafe_allow_html=True)
        else:
            if st.button("⏰ 智能打卡站", key="nav_checkin", use_container_width=True):
                st.session_state.page = 'checkin'; st.rerun()

        if st.session_state.page == 'members':
            st.markdown('<div class="nav-active">📋 志工名冊管理</div>', unsafe_allow_html=True)
        else:
            if st.button("📋 志工名冊管理", key="nav_members", use_container_width=True):
                st.session_state.page = 'members'; st.rerun()

        if st.session_state.page == 'report':
            st.markdown('<div class="nav-active">📉 數據報表中心</div>', unsafe_allow_html=True)
        else:
            if st.button("📉 數據報表中心", key="nav_report", use_container_width=True):
                st.session_state.page = 'report'; st.rerun()

        st.markdown("---")
        if st.button("🚪 回系統大廳", key="nav_back", use_container_width=True):
            st.switch_page("Home.py")
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem;'>Designed for Fude Community</div>", unsafe_allow_html=True)

# =========================================================
# 4) Pages
# =========================================================
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {PRIMARY};'>📊 {datetime.now().year} 年度志工概況</h2>", unsafe_allow_html=True)
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    this_year = datetime.now().year
    total_sec = calculate_hours_year(logs, this_year)
    total_hours = int(total_sec // 3600)
    total_mins = int((total_sec % 3600) // 60)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #CE93D8, #AB47BC); padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 25px rgba(171, 71, 188, 0.3);">
        <div style="font-size: 1.3rem; opacity: 0.9; color: white !important;">📅 {this_year} 年度 - 全體志工總服務時數</div>
        <div style="font-size: 4rem; font-weight: 900; margin: 15px 0; color: white !important;">
            {total_hours} <span style="font-size: 1.5rem; color: white !important;">小時</span> 
            {total_mins} <span style="font-size: 1.5rem; color: white !important;">分</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not members.empty:
        # 篩選服務中的志工
        active_m = members[~members.apply(check_is_fully_retired, axis=1)].copy()
        active_m['age'] = active_m['生日'].apply(calculate_age)
        
        # 統計各分類
        cols = st.columns(4)
        for idx, cat in enumerate(ALL_CATEGORIES):
            if cat == "臨時志工": continue
            subset = active_m[active_m['志工分類'].astype(str).str.contains(cat, na=False)]
            count = len(subset)
            
            # 平均年齡
            age_subset = subset[subset['age'] > 0]
            avg_age = round(age_subset['age'].mean(), 1) if not age_subset.empty else 0
            
            # 🔥 新增：男女統計
            male_count = len(subset[subset['性別'] == '男'])
            female_count = len(subset[subset['性別'] == '女'])
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div class="dash-card">
                    <div class="dash-label">{cat.replace('志工','')}</div>
                    <div class="dash-value">{count} <span style="font-size:1rem;color:#888;">人</span></div>
                    <div class="dash-sub">
                        平均 {avg_age} 歲<br>
                        <span style="color:#1E88E5; font-weight:bold;">♂ 男 {male_count}</span>  / 
                        <span style="color:#E91E63; font-weight:bold;">♀ 女 {female_count}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    st.caption(f"📅 台灣時間：{get_tw_time().strftime('%Y-%m-%d %H:%M:%S')}")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    # 🔥 新增這一行：初始化計數器 (用來強制重整游標焦點)
    if 'scan_key' not in st.session_state: st.session_state.scan_key = 0

    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])
    with tab1:
        col_scan, col_status = st.columns([1.5, 1])

        with col_scan:
            st.markdown('<div style="background:white; padding:20px; border-radius:20px; border:1px solid #ddd; margin-bottom:20px;">', unsafe_allow_html=True)
            st.markdown("#### ⚡️ 掃描簽到/退")
            
            c_act, c_note = st.columns([1, 2])
            with c_act: raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
            note = ""
            with c_note:
                if raw_act in ["專案活動", "教育訓練"]: note = st.text_input("📝 請輸入活動名稱 (必填)", placeholder="例如：社區大掃除")
                else: st.write("") 

            def process_scan():
                pid = st.session_state.input_pid.strip().upper()
                if not pid: return
                final_act = raw_act
                if raw_act in ["專案活動", "教育訓練"]:
                    if not note.strip(): st.error("⚠️ 請填寫「活動名稱」才能打卡！"); return
                    final_act = f"{raw_act}：{note}"
                
                now = get_tw_time()
                last = st.session_state['scan_cooldowns'].get(pid)
                if last and (now - last).total_seconds() < 1: 
                    st.warning(f"⏳ 刷卡過快"); st.session_state.input_pid = ""; return
                
                # 強制重讀資料
                load_data_from_sheet.clear()
                df_m = load_data_from_sheet("members")
                df_l = load_data_from_sheet("logs")
                
                if df_m.empty: st.error("❌ 無法讀取名單"); return
                person = df_m[df_m['身分證字號'] == pid]
                
                if not person.empty:
                    row = person.iloc[0]
                    name = row['姓名']
                    if check_is_fully_retired(row): 
                        st.error(f"❌ {name} 已退出，無法打卡。")
                    else:
                        today = now.strftime("%Y-%m-%d")
                        t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == today)]
                        action = "簽到"
                        if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到": action = "簽退"
                        
                        new_log = pd.DataFrame([{'姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'], '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': final_act}])
                        save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True), "logs")
                        st.session_state['scan_cooldowns'][pid] = now
                        
                        if action == "簽到": st.toast(f"👋 歡迎 {name} 簽到成功！", icon="✅")
                        else: st.toast(f"🏠 辛苦了 {name} 簽退成功！", icon="✅")
                else: st.error("❌ 查無此人")
                
                # 清空輸入框並讓計數器 +1 (這會強制更新下方的 Script)
                st.session_state.input_pid = ""
                st.session_state.scan_key += 1
                st.text_input("請輸入身分證 (Enter)", key="input_pid", on_change=process_scan, placeholder="掃描或輸入後按 Enter")
            
            # 🔥 修正版：改用 scan_key 計數器，完全不需要 datetime 或 time，保證不報錯
            components.html(f"""
                <script>
                    const input = window.parent.document.querySelector('input[aria-label="請輸入身分證 (Enter)"]');
                    if (input) input.focus();
                </script>
            """, height=0, width=0)
            
            st.markdown('</div>', unsafe_allow_html=True)

        with col_status:
            st.markdown("#### 🟢 目前在場志工")
            load_data_from_sheet.clear()
            logs = load_data_from_sheet("logs")
            present_df = get_present_volunteers(logs)
            if not present_df.empty:
                count = len(present_df)
                st.markdown(f"<div style='font-size:2rem; font-weight:bold; color:#4A148C; margin-bottom:10px;'>共 {count} 人</div>", unsafe_allow_html=True)
                for idx, row in present_df.iterrows():
                    st.markdown(f"""
                    <div style="background:white; padding:15px; border-radius:15px; border-left: 8px solid #4A148C; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-weight:900; font-size:1.4rem; color:#333;">#{idx+1} {row['姓名']}</div>
                            <div style="font-size:1rem; color:#4A148C; background:#F3E5F5; padding:4px 12px; border-radius:20px; font-weight:bold;">{row['時間']}</div>
                        </div>
                        <div style="font-size:1rem; color:#555; margin-top:8px; font-weight:500;">🚩 {row['活動內容']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("目前無人簽到中")

    with tab2:
        df_m = load_data_from_sheet("members")
        if not df_m.empty:
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)]
            name_list = active_m['姓名'].tolist()
            with st.form("manual_entry"):
                st.markdown("### 🛠️ 補登操作")
                entry_mode = st.radio("模式", ["單筆補登", "整批補登"], horizontal=True)
                c1, c2, c3, c4 = st.columns(4)
                d_date = c1.date_input("日期", value=date.today())
                d_time = c2.time_input("時間", value=get_tw_time().time())
                d_action = c3.selectbox("動作", ["簽到", "簽退"])
                d_act = c4.selectbox("活動", DEFAULT_ACTIVITIES)
                names = []
                if entry_mode == "單筆補登":
                    n = st.selectbox("選擇志工", name_list)
                    names = [n]
                else: names = st.multiselect("選擇多位志工", name_list)
                if st.form_submit_button("確認補登"):
                    logs = load_data_from_sheet("logs")
                    new_rows = []
                    for n in names:
                        row = df_m[df_m['姓名'] == n].iloc[0]
                        new_rows.append({'姓名': n, '身分證字號': row['身分證字號'], '電話': row['電話'], '志工分類': row['志工分類'], '動作': d_action, '時間': d_time.strftime("%H:%M:%S"), '日期': d_date.strftime("%Y-%m-%d"), '活動內容': d_act})
                    save_data_to_sheet(pd.concat([logs, pd.DataFrame(new_rows)], ignore_index=True), "logs")
                    st.success(f"已補登 {len(names)} 筆資料")
    with tab3:
        logs = load_data_from_sheet("logs")
        if not logs.empty:
            edited = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存修改"): save_data_to_sheet(edited, "logs"); st.success("已更新")

elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")
    with st.expander("➕ 新增志工 (展開填寫)", expanded=True):
        with st.form("add_m"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證字號")
            b = c3.text_input("生日 (YYYY-MM-DD)")
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            ph = c5.text_input("電話")
            st.markdown("---")
            col_l, col_r = st.columns([1, 2])
            with col_l:
                st.markdown("###### 勾選分類")
                is_x = st.checkbox("祥和志工")
                is_t = st.checkbox("據點週二志工")
                is_w = st.checkbox("據點週三志工")
                is_e = st.checkbox("環保志工")
            with col_r:
                st.markdown("###### 填寫加入日期")
                d_x = st.date_input("祥和加入日", value=date.today())
                d_t = st.date_input("週二加入日", value=date.today())
                d_w = st.date_input("週三加入日", value=date.today())
                d_e = st.date_input("環保加入日", value=date.today())
            if st.form_submit_button("確認新增"):
                if not p: st.error("身分證必填")
                elif not df.empty and p in df['身分證字號'].values: st.error("重複")
                else:
                    cats = []
                    if is_x: cats.append("祥和志工")
                    if is_t: cats.append("關懷據點週二志工")
                    if is_w: cats.append("關懷據點週三志工")
                    if is_e: cats.append("環保志工")
                    new_data = {'姓名':n, '身分證字號':p, '生日':b, '電話':ph, '地址':addr, '志工分類':",".join(cats), '祥和_加入日期': str(d_x) if is_x else "", '據點週二_加入日期': str(d_t) if is_t else "", '據點週三_加入日期': str(d_w) if is_w else "", '環保_加入日期': str(d_e) if is_e else ""}
                    new = pd.DataFrame([new_data])
                    for c in DISPLAY_ORDER: 
                        if c not in new.columns: new[c] = ""
                    save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                    st.success("新增成功"); time.sleep(1); st.rerun()
    if not df.empty:
        st.write("")
        df['狀態'] = df.apply(lambda r: '已退隊' if check_is_fully_retired(r) else '服務中', axis=1)
        df['年齡'] = df['生日'].apply(calculate_age)
        cols = ['姓名', '年齡', '電話', '地址', '志工分類'] + [c for c in df.columns if '日期' in c] + ['備註']
        cols = [c for c in cols if c in df.columns]
        tab_active, tab_retired = st.tabs(["🔥 服務中", "🍂 已退隊"])
        with tab_active:
            active_df = df[df['狀態'] == '服務中']
            st.data_editor(active_df[cols], use_container_width=True, num_rows="dynamic", key="editor_active")
        with tab_retired:
            retired_df = df[df['狀態'] == '已退隊']
            st.data_editor(retired_df[cols], use_container_width=True, num_rows="dynamic", key="editor_retired")

elif st.session_state.page == 'report':
    render_nav()
    st.markdown("## 📊 數據分析")
    logs = load_data_from_sheet("logs")
    st.markdown('<div style="background:white; padding:20px; border-radius:15px; border:1px solid #ddd; margin-bottom:20px;">', unsafe_allow_html=True)
    c_date, c_mode = st.columns([1, 1])
    with c_date: d_range = st.date_input("📅 選擇日期區間", value=(date(date.today().year, 1, 1), date.today()))
    with c_mode: report_mode = st.radio("分析模式", ["依活動查詢", "依志工查詢"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if logs.empty: st.info("無打卡資料")
    else:
        logs['dt'] = pd.to_datetime(logs['日期'] + ' ' + logs['時間'], errors='coerce')
        logs = logs.dropna(subset=['dt'])
        if isinstance(d_range, tuple) and len(d_range) == 2:
            start_d, end_d = d_range
            mask = (logs['dt'].dt.date >= start_d) & (logs['dt'].dt.date <= end_d)
            filtered_logs = logs[mask].copy()
        else: filtered_logs = logs.copy()
        if filtered_logs.empty: st.warning("此區間無資料")
        else:
            def calc_stats_display(df_in):
                total_seconds = 0
                total_sessions = 0
                for (name, date_val), group in df_in.groupby(['姓名', '日期']):
                    actions = group['動作'].tolist()
                    times = group['dt'].tolist()
                    i = 0
                    while i < len(actions):
                        if actions[i] == '簽到':
                            for j in range(i + 1, len(actions)):
                                if actions[j] == '簽退':
                                    total_seconds += (times[j] - times[i]).total_seconds()
                                    total_sessions += 1
                                    i = j
                                    break
                            i += 1
                        else: i += 1
                h = int(total_seconds // 3600)
                m = int((total_seconds % 3600) // 60)
                return total_sessions, f"{h}小時 {m}分", round(total_seconds/3600, 2)
            if report_mode == "依活動查詢":
                all_acts = filtered_logs['活動內容'].unique().tolist()
                target_act = st.selectbox("選擇活動", ["全部"] + all_acts)
                view_df = filtered_logs if target_act == "全部" else filtered_logs[filtered_logs['活動內容'] == target_act]
                tot_sess, tot_time_str, _ = calc_stats_display(view_df)
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f"""<div class="metric-card"><div class="metric-label">總人次</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="metric-card"><div class="metric-label">總時數</div><div class="metric-value">{tot_time_str}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="metric-card"><div class="metric-label">參與志工數</div><div class="metric-value">{view_df['姓名'].nunique()}</div></div>""", unsafe_allow_html=True)
                
                # 🔥 新增功能：匯出按鈕
                csv = view_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載此報表 (CSV)", data=csv, file_name=f"志工報表_{date.today()}.csv", mime="text/csv")
                
                st.markdown("### 📋 人員明細表")
                summary = []
                for name, g in view_df.groupby('姓名'):
                    c, s_str, s_num = calc_stats_display(g)
                    summary.append({'姓名': name, '次數': c, '時數': s_str, '排序用時數': s_num})
                st.dataframe(pd.DataFrame(summary).sort_values('排序用時數', ascending=False)[['姓名', '次數', '時數']], use_container_width=True)
            else:
                all_names = filtered_logs['姓名'].unique().tolist()
                target_name = st.selectbox("選擇志工", all_names)
                view_df = filtered_logs[filtered_logs['姓名'] == target_name]
                tot_sess, tot_time_str, _ = calc_stats_display(view_df)
                m1, m2 = st.columns(2)
                with m1: st.markdown(f"""<div class="metric-card"><div class="metric-label">執勤次數</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="metric-card"><div class="metric-label">累積時數</div><div class="metric-value">{tot_time_str}</div></div>""", unsafe_allow_html=True)
                
                # 🔥 新增功能：匯出按鈕
                csv = view_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載個人紀錄 (CSV)", data=csv, file_name=f"個人報表_{target_name}_{date.today()}.csv", mime="text/csv")
                
                st.markdown("### 📋 執勤紀錄明細")
                st.dataframe(view_df[['日期', '時間', '動作', '活動內容']].sort_values(['日期', '時間'], ascending=False), use_container_width=True)
