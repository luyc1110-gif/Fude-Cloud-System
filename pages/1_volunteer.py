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
# 1) CSS 樣式 (V21.0 卡片化報表 + 密碼鎖樣式)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}

/* 🔥 1. 整體背景設為淺灰 */
.stApp {{ background-color: {BG_MAIN} !important; }}

/* 🔥 2. 側邊欄背景 */
section[data-testid="stSidebar"] {{ background-color: {BG_MAIN}; border-right: none; }}

/* 🔥 3. 主內容區懸浮大卡片 */
.block-container {{
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 3rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem;
    max-width: 95% !important;
}}

/* Header 設定 */
header[data-testid="stHeader"] {{ display: block !important; background-color: transparent !important; }}
header[data-testid="stHeader"] .decoration {{ display: none; }}

/* 側邊欄按鈕 */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important; color: #666 !important;
    border: 1px solid transparent !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important; padding: 10px 0 !important;
    font-weight: 700 !important; width: 100%; margin-bottom: 8px !important; transition: all 0.2s;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important; color: {PRIMARY} !important;
}}
.nav-active {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
    color: white !important; padding: 12px 0; text-align: center; border-radius: 25px;
    font-weight: 900; box-shadow: 0 4px 10px rgba(123, 31, 162, 0.4); margin-bottom: 12px; cursor: default;
}}

/* --- 📊 數據報表：指標卡片 (Metric Card) --- */
.metric-box {{
    background-color: #F8F9FA;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    border-bottom: 5px solid {PRIMARY};
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    transition: transform 0.2s;
}}
.metric-box:hover {{ transform: translateY(-5px); }}
.metric-label {{ font-size: 1.1rem; color: #666 !important; font-weight: bold; margin-bottom: 5px; }}
.metric-value {{ font-size: 2.5rem; color: {PRIMARY} !important; font-weight: 900; }}

/* --- 📋 數據報表：志工明細卡片 (Volunteer Card) --- */
.vol-card {{
    background-color: #FFFFFF;
    border: 1px solid #EEE;
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 6px solid {ACCENT};
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    display: flex; justify-content: space-between; align-items: center;
}}
.vol-card-name {{ font-size: 1.3rem; font-weight: 900; color: #333; }}
.vol-card-stats {{ text-align: right; }}
.vol-card-tag {{ background: #F3E5F5; color: {PRIMARY}; padding: 3px 10px; border-radius: 10px; font-size: 0.85rem; font-weight: bold; margin-left: 10px; }}
.vol-log-card {{
    background-color: #FAFAFA; border-radius: 12px; padding: 12px; margin-bottom: 10px;
    border-left: 4px solid #aaa; display: flex; justify-content: space-between; align-items: center;
}}
.vol-log-date {{ font-weight: bold; color: #333; }}
.vol-log-action {{ font-weight: bold; padding: 2px 8px; border-radius: 5px; font-size: 0.9rem; }}
.action-in {{ background-color: #E8F5E9; color: #2E7D32; }}
.action-out {{ background-color: #FFEBEE; color: #C62828; }}

/* 輸入框優化 */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input {{
    background-color: #FFFFFF !important; border: 2px solid #E0E0E0 !important; border-radius: 12px !important; color: #000 !important;
}}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{ background-color: #FFFFFF !important; color: #000 !important; }}
li[role="option"]:hover {{ background-color: #F3E5F5 !important; }}

/* 🔥 確保時間選擇器裡面的文字絕對是黑色的 */
div[data-testid="stTimeInput"] * {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}}

/* 按鈕樣式 */
div[data-testid="stFormSubmitButton"] > button, div[data-testid="stDownloadButton"] > button {{
    background-color: {PRIMARY} !important; color: #FFFFFF !important; border: none !important; border-radius: 12px !important; padding: 10px 20px !important; font-weight: 900 !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover, div[data-testid="stDownloadButton"] > button:hover {{
    background-color: {ACCENT} !important; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}}
div[data-testid="stFormSubmitButton"] > button *, div[data-testid="stDownloadButton"] > button * {{ color: #FFFFFF !important; }}

/* Toast */
div[data-baseweb="toast"] {{ background-color: #FFFFFF !important; border: 3px solid {PRIMARY} !important; border-radius: 15px !important; padding: 15px !important; }}

/* 1. 將所有日期選單內的文字強制改為「白色」，確保在深色背景下清晰可見 */
div[data-baseweb="calendar"] div, 
div[data-baseweb="calendar"] button, 
div[data-baseweb="calendar"] h1, 
div[data-baseweb="calendar"] h2, 
div[data-baseweb="calendar"] h3, 
div[data-baseweb="calendar"] h4, 
div[data-baseweb="calendar"] h5, 
div[data-baseweb="calendar"] h6 {{
    color: #FFFFFF !important;
}}

/* 2. 將月份左右切換的箭頭改為「白色」 */
div[data-baseweb="calendar"] svg {{
    fill: #FFFFFF !important;
}}

/* 3. 修正「滑鼠移過去」和「被選中」日期的文字顏色 */
div[data-baseweb="calendar"] button:hover,
div[data-baseweb="calendar"] button[aria-selected="true"] {{
    color: #FFFFFF !important; 
    font-weight: bold !important;
}}

/* 4. 確保選單背景維持深色 (避免半白半黑的狀況) */
div[data-baseweb="calendar"] {{
    background-color: #262730 !important;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Helpers (高效能優化版)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]

# 🔥 定義固定欄位順序，確保 Append 時不會錯位
MEM_COLS = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", 
            "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", 
            "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]

LOG_COLS = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

# 🔥 優化 A：讀取加速 (get_all_values)
@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_values()
        
        target_cols = MEM_COLS if sheet_name == 'members' else LOG_COLS
        if not data: return pd.DataFrame(columns=target_cols)
        
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        
        # 補齊可能缺少的欄位
        for c in target_cols: 
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame()

# 維持原版 save (僅用於修改資料/DataEditor)
def save_data_to_sheet(df, sheet_name):
    try:
        # 轉成字串避免 JSON 錯誤
        df_fix = df.fillna("").astype(str)
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        load_data_from_sheet.clear()
    except Exception as e: st.error(f"寫入失敗：{e}")

# 🔥 優化 B：單筆秒速寫入 (用於打卡、新增志工)
def append_data(sheet_name, row_dict, col_order):
    try:
        values = [str(row_dict.get(c, "")).strip() for c in col_order]
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.append_row(values)
        load_data_from_sheet.clear() # 清除快取，讓介面更新
        return True
    except Exception as e:
        st.error(f"新增失敗：{e}"); return False

# 🔥 優化 C：批次極速寫入 (用於補登)
def batch_append_data(sheet_name, rows_list, col_order):
    try:
        values_list = []
        for r in rows_list:
            values_list.append([str(r.get(c, "")).strip() for c in col_order])
        
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.append_rows(values_list)
        load_data_from_sheet.clear()
        return True
    except Exception as e:
        st.error(f"批次失敗：{e}"); return False

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

def calculate_coverage_seconds(df_in):
    """
    通用版：計算傳入 DataFrame 的「不重疊」服務總秒數
    適用於：首頁年度統計、報表活動統計
    """
    if df_in.empty: return 0
    
    # 確保有 dt 欄位
    if 'dt' not in df_in.columns:
        df_in = df_in.copy()
        df_in['dt'] = pd.to_datetime(df_in['日期'] + ' ' + df_in['時間'], errors='coerce')
    
    df_in = df_in.dropna(subset=['dt']).sort_values(['姓名', 'dt'])
    
    all_intervals = []
    # 擷取區間
    for (name, date_val), group in df_in.groupby(['姓名', '日期']):
        actions = group['動作'].tolist()
        times = group['dt'].tolist()
        i = 0
        while i < len(actions):
            if actions[i] == '簽到':
                for j in range(i + 1, len(actions)):
                    if actions[j] == '簽退':
                        if times[j] > times[i]:
                            all_intervals.append((times[i], times[j]))
                        i = j
                        break
                else: i += 1
            else: i += 1
            
    if not all_intervals: return 0

    # 合併重疊
    all_intervals.sort(key=lambda x: x[0])
    merged = []
    if all_intervals:
        curr_start, curr_end = all_intervals[0]
        for next_start, next_end in all_intervals[1:]:
            if next_start < curr_end:
                curr_end = max(curr_end, next_end)
            else:
                merged.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged.append((curr_start, curr_end))
        
    return sum((end - start).total_seconds() for start, end in merged)

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
# 🔄 同步功能：將志工時數同步到 App_Users (無照片/手機登入版)
# =========================================================
def sync_to_app_users():
    try:
        # 1. 讀取原始資料
        members = load_data_from_sheet("members")
        logs = load_data_from_sheet("logs")
        
        if members.empty:
            st.warning("名冊空白，無法同步")
            return

        # 2. 準備要寫入的資料
        # 我們先讀取 App_Users 目前的資料，為了保留「點數」不被覆蓋
        client = get_google_sheet_client()
        try:
            sh = client.open_by_key(SHEET_ID)
            ws = sh.worksheet("App_Users")
        except:
            st.error("找不到 'App_Users' 分頁，請先在 Google Sheet 建立！")
            return

        current_app_data = ws.get_all_records()
        df_app = pd.DataFrame(current_app_data)
        
        # 轉成字典方便查詢：Key=手機, Value={環保點數:x, 樂活點數:y}
        points_map = {}
        if not df_app.empty and '手機' in df_app.columns:
            # 強制轉字串，避免格式問題
            df_app['手機'] = df_app['手機'].astype(str).str.replace(".0", "", regex=False)
            for _, row in df_app.iterrows():
                phone_key = str(row['手機']).strip()
                points_map[phone_key] = {
                    '環保': row.get('環保點數', 0),
                    '樂活': row.get('樂活點數', 0)
                }

        # 3. 重新計算所有人的時數與等級
        final_rows = []
        progress_bar = st.progress(0)
        
        for idx, row in members.iterrows():
            name = row['姓名']
            pid = row['身分證字號']
            raw_phone = str(row['電話']).strip()
            
            # 清理電話號碼 (移除 - 和空白)
            phone = raw_phone.replace("-", "").replace(" ", "")
            if not phone: continue # 沒電話就跳過
            
            # 計算時數
            person_logs = logs[logs['身分證字號'] == pid] if '身分證字號' in logs.columns else logs[logs['姓名'] == name]
            total_sec = calculate_coverage_seconds(person_logs)
            total_hours = round(total_sec / 3600, 1)
            
            # 判斷等級
            badge = "🌱 新手志工"
            if total_hours >= 100: badge = "🥇 金牌志工"
            elif total_hours >= 50: badge = "🥈 銀牌志工"
            elif total_hours >= 20: badge = "🥉 銅牌志工"
            
            # 密碼 (身分證後4碼)
            pwd = pid[-4:] if len(pid) >= 4 else "0000"
            
            # 取回舊點數 (如果有的話)
            saved_points = points_map.get(phone, {'環保': 0, '樂活': 0})
            
            final_rows.append([
                phone, pwd, name, 
                saved_points['環保'], saved_points['樂活'], 
                total_hours, badge
            ])
            progress_bar.progress((idx + 1) / len(members))

        # 4. 寫回 Google Sheet (全量覆蓋，但保留了點數)
        ws.clear()
        ws.append_row(["手機", "密碼", "姓名", "環保點數", "樂活點數", "志工時數", "志工等級"])
        ws.append_rows(final_rows)
        
        st.success(f"✅ 同步完成！已更新 {len(final_rows)} 筆資料到 App。")
        
    except Exception as e:
        st.error(f"同步失敗：{e}")

# =========================================================
# 3) Navigation
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'unlock_vol_members' not in st.session_state: st.session_state.unlock_vol_members = False

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
    
    # --- 🔥 修正開始：先篩選年度，再呼叫通用函式 ---
    if not logs.empty:
        # 1. 建立時間欄位 (以利篩選年份)
        logs['dt'] = pd.to_datetime(logs['日期'] + ' ' + logs['時間'], errors='coerce')
        logs = logs.dropna(subset=['dt'])
        
        # 2. 篩選出今年的資料
        year_logs = logs[logs['dt'].dt.year == this_year]
        
        # 3. 呼叫通用函式計算 (計算團隊重疊後時數)
        total_sec = calculate_coverage_seconds(year_logs)
    else:
        total_sec = 0

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
        active_m = members[~members.apply(check_is_fully_retired, axis=1)].copy()
        active_m['age'] = active_m['生日'].apply(calculate_age)
        
        cols = st.columns(4)
        for idx, cat in enumerate(ALL_CATEGORIES):
            if cat == "臨時志工": continue
            subset = active_m[active_m['志工分類'].astype(str).str.contains(cat, na=False)]
            count = len(subset)
            age_subset = subset[subset['age'] > 0]
            avg_age = round(age_subset['age'].mean(), 1) if not age_subset.empty else 0
            male_count = len(subset[subset['性別'] == '男'])
            female_count = len(subset[subset['性別'] == '女'])
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div class="metric-box" style="border-left: 5px solid {ACCENT}; border-bottom: none; text-align:left;">
                    <div style="font-size:1.1rem; font-weight:bold; color:#666;">{cat.replace('志工','')}</div>
                    <div style="font-size:2.2rem; font-weight:900; color:{PRIMARY}; margin:5px 0;">{count} <span style="font-size:1rem;color:#999;">人</span></div>
                    <div style="font-size:0.9rem; color:#888;">
                        均齡 {avg_age} 歲<br>
                        <span style="color:#1976D2;">♂ {male_count}</span> / <span style="color:#D81B60;">♀ {female_count}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    st.caption(f"📅 台灣時間：{get_tw_time().strftime('%Y-%m-%d %H:%M:%S')}")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    tab1, tab2 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業"])
    with tab1:
        col_scan, col_status = st.columns([1.5, 1])

        with col_scan:
            st.markdown('<div style="background:#F8F9FA; padding:20px; border-radius:20px; border:1px solid #eee; margin-bottom:20px;">', unsafe_allow_html=True)
            st.markdown("#### ⚡️ 批次/個人 簽到退")
            
            c_act, c_note = st.columns([1, 2])
            with c_act: raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
            note = ""
            with c_note:
                if raw_act in ["專案活動", "教育訓練"]: note = st.text_input("📝 請輸入活動名稱 (必填)", placeholder="例如：社區大掃除")
                else: st.write("") 

            st.markdown("---")
            
            # 讀取名單
            load_data_from_sheet.clear()
            df_m = load_data_from_sheet("members")
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)] if not df_m.empty else pd.DataFrame()
            
            # 定義環保志工分組
            env_groups = {
                "第一組": ["涂玉梅", "羅愛梅", "楊素鳳", "張天德", "邱煥原", "張瑞群", "郭惠美", "林素玲", "范銀英", "石美花", "呂春煌", "解美菊", "陳張牡丹", "黃美燕", "黃麗卿", "林瑞琴"],
                "第二組": ["簡玉娥", "李月鳳", "邱淑珠", "蔡寶雲", "邱黃秀", "李玉梅"],
                "第三組": ["黃李昭", "張李惷", "邱鄭冬吟", "吳王秀琴", "沈秀枝", "賴美麗"],
                "第四組": ["呂宜政", "黃秋霞", "彭金玉", "呂玉華", "莊榮川", "劉采稱", "林月娉", "張秭榆", "陳天助", "王甄與", "陳俊維", "郭坤山", "陳清哲", "彭瑞鑑", "陳素惠", "趙再添", "黃敬恩", "吳玟玲"]
            }

            c_f1, c_f2 = st.columns(2)
            cat_filter = c_f1.selectbox("分類篩選", ["全部", "環保志工", "祥和志工", "關懷據點"])
            
            group_filter = "全部"
            if cat_filter == "環保志工":
                group_filter = c_f2.selectbox("分組篩選 (環保)", ["全部", "第一組", "第二組", "第三組", "第四組"])

            # --- 新增：利用 session_state 記住跨組別的選擇 ---
            if 'temp_vols' not in st.session_state:
                st.session_state.temp_vols = []

            def update_vols():
                # 當下拉選單有勾選變動時，馬上把名單存進暫存區
                st.session_state.temp_vols = st.session_state.checkin_ms

            available_names = []
            
            if not active_m.empty:
                # 依分類篩選
                if cat_filter != "全部":
                    filtered_m = active_m[active_m['志工分類'].astype(str).str.contains(cat_filter, na=False)]
                else:
                    filtered_m = active_m

                available_names = sorted(filtered_m['姓名'].tolist())
                
                # 如果有選環保志工的特定組別，則「縮小可選範圍」至該組名單
                if cat_filter == "環保志工" and group_filter != "全部":
                    group_names = env_groups.get(group_filter, [])
                    # 重新篩選：只保留存在於該組別的人
                    available_names = [n for n in available_names if n in group_names]

            # 🔥 關鍵修復：將「目前已經勾選的人」也加入到當前的候選名單中
            # 這樣切換到別組時，上一組選過的人才不會被系統自動洗掉
            final_options = sorted(list(set(available_names + st.session_state.temp_vols)))

            selected_names = st.multiselect(
                "👤 選擇打卡志工 (可打字搜尋、複選)", 
                options=final_options, 
                default=st.session_state.temp_vols,
                placeholder="請點擊輸入或選擇姓名...",
                key="checkin_ms",
                on_change=update_vols
            )

            if st.button("✅ 確認打卡 (自動判斷簽到/退)", type="primary"):
                if not selected_names:
                    st.error("❌ 請至少選擇一位志工")
                else:
                    final_act = raw_act
                    if raw_act in ["專案活動", "教育訓練"]:
                        if not note.strip(): 
                            st.error("⚠️ 請填寫「活動名稱」才能打卡！")
                            st.stop()
                        final_act = f"{raw_act}：{note}"
                    
                    now = get_tw_time()
                    today = now.strftime("%Y-%m-%d")
                    time_str = now.strftime("%H:%M:%S")
                    
                    df_l = load_data_from_sheet("logs")
                    new_rows = []
                    
                    for name in selected_names:
                        row = active_m[active_m['姓名'] == name].iloc[0]
                        pid = row['身分證字號']
                        
                        # 判斷簽到或簽退
                        t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == today)]
                        action = "簽到"
                        if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到": 
                            action = "簽退"
                        
                        new_rows.append({
                            '姓名': name, '身分證字號': pid, '電話': row['電話'], 
                            '志工分類': row['志工分類'], '動作': action, 
                            '時間': time_str, '日期': today, 
                            '活動內容': final_act
                        })
                        
                    if batch_append_data("logs", new_rows, LOG_COLS):
                        st.success(f"✅ 已成功處理 {len(selected_names)} 人的打卡紀錄！")
                        
                        # 🔥 打卡成功後，清空暫存區，讓下一批人可以乾淨地重新選
                        st.session_state.temp_vols = [] 
                        
                        time.sleep(1)
                        st.rerun()

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
                    <div style="background:#F8F9FA; padding:15px; border-radius:15px; border-left: 8px solid #4A148C; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-weight:900; font-size:1.4rem; color:#333;">#{idx+1} {row['姓名']}</div>
                            <div style="font-size:1rem; color:#4A148C; background:#EEE; padding:4px 12px; border-radius:20px; font-weight:bold;">{row['時間']}</div>
                        </div>
                        <div style="font-size:1rem; color:#555; margin-top:8px; font-weight:500;">🚩 {row['活動內容']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("目前無人簽到中")

    with tab2:
        df_m = load_data_from_sheet("members")
        if not df_m.empty:
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)]
            
            st.markdown("### 🛠️ 補登操作")
            
            # --- 1. 安全的狀態管理 (避免畫面崩潰) ---
            if 'manual_ms' not in st.session_state:
                st.session_state.manual_ms = []

            # 2. 分類篩選
            cat_filter_tab2 = st.selectbox("📌 篩選志工分類", ["全部", "環保志工", "祥和志工", "關懷據點週二志工", "關懷據點週三志工"], key="cat_filter_tab2")
            
            if cat_filter_tab2 != "全部":
                filtered_m_tab2 = active_m[active_m['志工分類'].astype(str).str.contains(cat_filter_tab2, na=False)]
            else:
                filtered_m_tab2 = active_m
                
            available_names_tab2 = sorted(filtered_m_tab2['姓名'].tolist())
            
            # 3. 🔥 關鍵防呆：把「已經在暫存區的人名」強制加進選項中，避免系統切換組別時找不到人而當機
            final_options_tab2 = sorted(list(set(available_names_tab2 + st.session_state.manual_ms)))
            
            # 4. 表單細節 (加入獨立 key 避免互相干擾)
            c1, c2, c3, c4 = st.columns(4)
            d_date = c1.date_input("日期", value=date.today(), key="d_date_tab2")
            d_time = c2.time_input("時間", value=get_tw_time().time(), key="d_time_tab2")
            d_action = c3.selectbox("動作", ["簽到", "簽退"], key="d_action_tab2")
            d_act = c4.selectbox("活動", DEFAULT_ACTIVITIES, key="d_act_tab2")
            
            # 5. 志工選單 (拿掉 default 與 on_change，純靠 key 記憶)
            names = st.multiselect(
                "👤 選擇志工 (可單選或多選)", 
                options=final_options_tab2,
                placeholder="請點此選擇要補登的志工...",
                key="manual_ms"
            )
            
            st.write("") # 空行排版
            if st.button("✅ 確認補登", type="primary"):
                if not names:
                    st.error("❌ 請至少選擇一位志工！")
                else:
                    new_rows = []
                    for n in names:
                        row = active_m[active_m['姓名'] == n].iloc[0]
                        new_rows.append({
                            '姓名': n, '身分證字號': row['身分證字號'], '電話': row['電話'], 
                            '志工分類': row['志工分類'], '動作': d_action, 
                            '時間': d_time.strftime("%H:%M:%S"), '日期': d_date.strftime("%Y-%m-%d"), 
                            '活動內容': d_act
                        })
                    
                    if batch_append_data("logs", new_rows, LOG_COLS):
                        st.success(f"✅ 已成功補登 {len(names)} 筆資料！")
                        # 送出後安全清空選擇
                        st.session_state.manual_ms = [] 
                        time.sleep(1)
                        st.rerun()

elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")
    
    # 公開區域：新增志工
    with st.expander("➕ 新增志工 (展開填寫)", expanded=False):
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
                    new_data = {
                        '姓名':n, '身分證字號':p, '生日':b, '電話':ph, '地址':addr, 
                        '志工分類':",".join(cats), 
                        '祥和_加入日期': str(d_x) if is_x else "", 
                        '據點週二_加入日期': str(d_t) if is_t else "", 
                        '據點週三_加入日期': str(d_w) if is_w else "", 
                        '環保_加入日期': str(d_e) if is_e else ""
                    }
                    
                    # --- 🔥 修改重點：改用 append_data ---
                    if append_data("members", new_data, MEM_COLS):
                        st.success("新增成功"); time.sleep(1); st.rerun()
    
    # 🔒 密碼保護區域：完整名冊
    st.markdown("### 📝 完整志工名冊 (需密碼)")
    if not st.session_state.unlock_vol_members:
        c_pwd, c_btn = st.columns([2, 1])
        with c_pwd:
            pwd = st.text_input("請輸入管理員密碼", type="password", key="vol_pwd")
        with c_btn:
            st.markdown("<br>", unsafe_allow_html=True) # spacer
            if st.button("🔓 解鎖名冊"):
                if pwd == st.secrets["admin_password"]:
                    st.session_state.unlock_vol_members = True
                    st.rerun()
                else:
                    st.error("密碼錯誤")
    else:
        # 解鎖後顯示
        if st.button("🔒 鎖定名冊"):
            st.session_state.unlock_vol_members = False
            st.rerun()
            
        if not df.empty:
            df['狀態'] = df.apply(lambda r: '已退隊' if check_is_fully_retired(r) else '服務中', axis=1)
            df['年齡'] = df['生日'].apply(calculate_age)
            # 🔥 自動依照姓名排序
            df = df.sort_values(by='姓名')
            
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
    st.markdown("## 📊 數據分析與報表")
    logs = load_data_from_sheet("logs")
    
    # 搜尋與篩選區塊
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
                
                # 1. 計算團隊實際服務時數 (扣除重疊)
                cov_seconds = calculate_coverage_seconds(view_df)
                cov_h = int(cov_seconds // 3600)
                cov_m = int((cov_seconds % 3600) // 60)
                team_time_str = f"{cov_h}小時 {cov_m}分" # 🔥 這裡是定義 team_time_str

                # 2. 計算總人次
                tot_sess, _, _ = calc_stats_display(view_df) # 🔥 這裡的舊變數被 _ 取代了
                
                # 🔥 1. 卡片式統計指標
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f"""<div class="metric-box"><div class="metric-label">總人次</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                
                # 🔥 修正點：這裡要用 team_time_str，且建議標籤改成「團隊服務時數」
                with m2: st.markdown(f"""<div class="metric-box"><div class="metric-label">團隊服務時數</div><div class="metric-value">{team_time_str}</div></div>""", unsafe_allow_html=True)
                
                with m3: st.markdown(f"""<div class="metric-box"><div class="metric-label">參與志工數</div><div class="metric-value">{view_df['姓名'].nunique()}</div></div>""", unsafe_allow_html=True)
                
                csv = view_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載此報表 (CSV)", data=csv, file_name=f"志工報表_{date.today()}.csv", mime="text/csv")
                
                # 🔥 2. 卡片式志工明細 (Grid Layout)
                st.markdown("### 📋 人員明細表")
                summary = []
                for name, g in view_df.groupby('姓名'):
                    c, s_str, s_num = calc_stats_display(g)
                    summary.append({'姓名': name, '次數': c, '時數': s_str, '排序用時數': s_num})
                
                summ_df = pd.DataFrame(summary).sort_values('排序用時數', ascending=False)
                
                # 每3個一列顯示卡片
                for i in range(0, len(summ_df), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(summ_df):
                            row = summ_df.iloc[i+j]
                            with cols[j]:
                                st.markdown(f"""
                                <div class="vol-card">
                                    <div>
                                        <div class="vol-card-name">{row['姓名']}</div>
                                        <div style="color:#888; font-size:0.9rem;">共出勤 {row['次數']} 次</div>
                                    </div>
                                    <div class="vol-card-stats">
                                        <div class="vol-card-tag">{row['時數']}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

            else: # 依志工查詢
                all_names = sorted(filtered_logs['姓名'].unique().tolist())
                target_name = st.selectbox("選擇志工", all_names)
                view_df = filtered_logs[filtered_logs['姓名'] == target_name]
                tot_sess, tot_time_str, _ = calc_stats_display(view_df)
                
                # 🔥 統計指標卡片
                m1, m2 = st.columns(2)
                with m1: st.markdown(f"""<div class="metric-box"><div class="metric-label">執勤次數</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="metric-box"><div class="metric-label">累積時數</div><div class="metric-value">{tot_time_str}</div></div>""", unsafe_allow_html=True)
                
                csv = view_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載個人紀錄 (CSV)", data=csv, file_name=f"個人報表_{target_name}_{date.today()}.csv", mime="text/csv")
                
                # 🔥 卡片式打卡紀錄
                st.markdown("### 📋 執勤紀錄明細")
                view_df = view_df.sort_values(['日期', '時間'], ascending=False)
                
                for idx, row in view_df.iterrows():
                    action_class = "action-in" if row['動作'] == "簽到" else "action-out"
                    st.markdown(f"""
                    <div class="vol-log-card">
                        <div class="vol-log-date">{row['日期']} {row['時間']}</div>
                        <div style="flex-grow:1; margin-left:15px; color:#555;">{row['活動內容']}</div>
                        <div class="vol-log-action {action_class}">{row['動作']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        if st.button("🔄 同步資料到 App"):
            sync_to_app_users()
