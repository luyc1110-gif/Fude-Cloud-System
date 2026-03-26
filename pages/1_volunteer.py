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

/* 日期選單樣式 */
div[data-baseweb="calendar"] div, div[data-baseweb="calendar"] button, div[data-baseweb="calendar"] h1, div[data-baseweb="calendar"] h2, div[data-baseweb="calendar"] h3, div[data-baseweb="calendar"] h4, div[data-baseweb="calendar"] h5, div[data-baseweb="calendar"] h6 {{ color: #FFFFFF !important; }}
div[data-baseweb="calendar"] svg {{ fill: #FFFFFF !important; }}
div[data-baseweb="calendar"] button:hover, div[data-baseweb="calendar"] button[aria-selected="true"] {{ color: #FFFFFF !important; font-weight: bold !important; }}
div[data-baseweb="calendar"] {{ background-color: #262730 !important; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Helpers (高效能優化版 + 橋接主檔)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]

MEM_COLS = ["姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註", 
            "祥和_加入日期", "祥和_退出日期", "據點週二_加入日期", "據點週二_退出日期", 
            "據點週三_加入日期", "據點週三_退出日期", "環保_加入日期", "環保_退出日期"]

LOG_COLS = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']
COLS_MASTER = ['姓名', '身分證字號', '性別', '出生年月日', '電話', '地址', '緊急聯絡人', '緊急聯絡電話', '身分_志工', '身分_關懷戶', '身分_據點長輩', '志工分類', '關懷_身分別', '同住_18歲以下', '同住_成人', '同住_65歲以上', '拒絕物資', '人際關係']

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

# 🔥 優化 A：支援動態欄位的 load_data
@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name, target_cols=None):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_values()
        
        t_cols = target_cols if target_cols is not None else (MEM_COLS if sheet_name == 'members' else LOG_COLS)
        if not data: return pd.DataFrame(columns=t_cols)
        
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        for c in t_cols: 
            if c not in df.columns: df[c] = ""
        return df
    except: 
        t_cols = target_cols if target_cols is not None else (MEM_COLS if sheet_name == 'members' else LOG_COLS)
        return pd.DataFrame(columns=t_cols)

# 🔥 保護核取方塊的 save_data
def save_data_to_sheet(df, sheet_name):
    try:
        df_fix = df.fillna("").astype(str)
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist(), value_input_option="USER_ENTERED")
        st.cache_data.clear()
    except Exception as e: st.error(f"寫入失敗：{e}")

def append_data(sheet_name, row_dict, col_order):
    try:
        values = [str(row_dict.get(c, "")).strip() for c in col_order]
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.append_row(values, value_input_option="USER_ENTERED")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"新增失敗：{e}"); return False

def batch_append_data(sheet_name, rows_list, col_order):
    try:
        values_list = []
        for r in rows_list:
            values_list.append([str(r.get(c, "")).strip() for c in col_order])
        
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.append_rows(values_list, value_input_option="USER_ENTERED")
        st.cache_data.clear()
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
    if df_in.empty: return 0
    if 'dt' not in df_in.columns:
        df_in = df_in.copy()
        df_in['dt'] = pd.to_datetime(df_in['日期'] + ' ' + df_in['時間'], errors='coerce')
    df_in = df_in.dropna(subset=['dt']).sort_values(['姓名', 'dt'])
    
    all_intervals = []
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
# 🌟 主檔橋接核心 (專為志工系統打造的主從合併邏輯)
# =========================================================
def get_volunteer_members():
    """從主檔讀取基本資料，並跟舊 members 檔的退出日期合併"""
    master = load_data_from_sheet("master_residents", COLS_MASTER)
    vol_ext = load_data_from_sheet("members", MEM_COLS)
    
    if master.empty: return pd.DataFrame(columns=MEM_COLS)
    
    # 只抓取具備志工身分的人
    vol_master = master[master['身分_志工'] == 'TRUE'].copy()
    vol_master = vol_master.rename(columns={'出生年月日': '生日'})
    
    if not vol_ext.empty:
        # 提取專屬的加入退出日期
        ext_cols = ['身分證字號', '備註', '祥和_加入日期', '祥和_退出日期', '據點週二_加入日期', '據點週二_退出日期', '據點週三_加入日期', '據點週三_退出日期', '環保_加入日期', '環保_退出日期']
        ext_cols = [c for c in ext_cols if c in vol_ext.columns]
        vol_ext_mini = vol_ext[ext_cols].drop_duplicates(subset=['身分證字號'])
        merged = pd.merge(vol_master, vol_ext_mini, on='身分證字號', how='left')
    else:
        merged = vol_master
        
    for c in MEM_COLS:
        if c not in merged.columns: merged[c] = ""
        
    return merged[MEM_COLS]

def add_or_update_volunteer_to_master(new_data):
    master = load_data_from_sheet("master_residents", COLS_MASTER)
    uid = new_data.get('身分證字號', '').upper()
    
    if not uid or uid == 'NAN':
        uid = f"TEMP_{new_data.get('姓名', '').strip()}_{new_data.get('電話', '').strip()}"
        new_data['身分證字號'] = uid
        
    # 1. 寫入主檔
    master_data = {
        '姓名': new_data['姓名'], '身分證字號': uid, '性別': new_data.get('性別',''),
        '出生年月日': new_data.get('生日',''), '電話': new_data.get('電話',''),
        '地址': new_data.get('地址',''), '志工分類': new_data.get('志工分類','')
    }
    master_data['身分_志工'] = 'TRUE'

    if not master.empty and uid in master['身分證字號'].values:
        idx = master[master['身分證字號'] == uid].index[0]
        for k, v in master_data.items(): master.at[idx, k] = str(v)
        save_data_to_sheet(master, "master_residents")
    else:
        for c in COLS_MASTER:
            if c not in master_data: master_data[c] = "FALSE" if "身分_" in c else ""
        append_data("master_residents", master_data, COLS_MASTER)
        
    # 2. 寫入志工延伸檔 (保留加入與退出日期)
    vol_ext = load_data_from_sheet("members", MEM_COLS)
    if not vol_ext.empty and uid in vol_ext['身分證字號'].values:
        idx = vol_ext[vol_ext['身分證字號'] == uid].index[0]
        for k, v in new_data.items(): vol_ext.at[idx, k] = str(v)
        save_data_to_sheet(vol_ext, "members")
    else:
        append_data("members", new_data, MEM_COLS)
        
    return True

# =========================================================
# 🔄 同步功能：將志工時數同步到 App_Users
# =========================================================
def sync_to_app_users():
    try:
        members = get_volunteer_members()
        logs = load_data_from_sheet("logs")
        
        if members.empty:
            st.warning("名冊空白，無法同步")
            return

        client = get_google_sheet_client()
        try:
            sh = client.open_by_key(SHEET_ID)
            ws = sh.worksheet("App_Users")
        except:
            st.error("找不到 'App_Users' 分頁，請先在 Google Sheet 建立！")
            return

        current_app_data = ws.get_all_records()
        df_app = pd.DataFrame(current_app_data)
        
        points_map = {}
        if not df_app.empty and '手機' in df_app.columns:
            df_app['手機'] = df_app['手機'].astype(str).str.replace(".0", "", regex=False)
            for _, row in df_app.iterrows():
                phone_key = str(row['手機']).strip()
                points_map[phone_key] = {'環保': row.get('環保點數', 0), '樂活': row.get('樂活點數', 0)}

        final_rows = []
        progress_bar = st.progress(0)
        
        for idx, row in members.iterrows():
            name = row['姓名']
            pid = row['身分證字號']
            raw_phone = str(row['電話']).strip()
            
            phone = raw_phone.replace("-", "").replace(" ", "")
            if not phone: continue
            
            person_logs = logs[logs['身分證字號'] == pid] if '身分證字號' in logs.columns else logs[logs['姓名'] == name]
            total_sec = calculate_coverage_seconds(person_logs)
            total_hours = round(total_sec / 3600, 1)
            
            badge = "🌱 新手志工"
            if total_hours >= 100: badge = "🥇 金牌志工"
            elif total_hours >= 50: badge = "🥈 銀牌志工"
            elif total_hours >= 20: badge = "🥉 銅牌志工"
            
            pwd = pid[-4:] if len(pid) >= 4 else "0000"
            saved_points = points_map.get(phone, {'環保': 0, '樂活': 0})
            
            final_rows.append([phone, pwd, name, saved_points['環保'], saved_points['樂活'], total_hours, badge])
            progress_bar.progress((idx + 1) / len(members))

        ws.clear()
        ws.update([["手機", "密碼", "姓名", "環保點數", "樂活點數", "志工時數", "志工等級"]] + final_rows, value_input_option="USER_ENTERED")
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
    members = get_volunteer_members()
    this_year = datetime.now().year
    
    if not logs.empty:
        logs['dt'] = pd.to_datetime(logs['日期'] + ' ' + logs['時間'], errors='coerce')
        logs = logs.dropna(subset=['dt'])
        year_logs = logs[logs['dt'].dt.year == this_year]
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
            
            df_m = get_volunteer_members()
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)] if not df_m.empty else pd.DataFrame()
            
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

            if 'temp_vols' not in st.session_state:
                st.session_state.temp_vols = []

            def update_vols():
                st.session_state.temp_vols = st.session_state.checkin_ms

            available_names = []
            
            if not active_m.empty:
                if cat_filter != "全部":
                    filtered_m = active_m[active_m['志工分類'].astype(str).str.contains(cat_filter, na=False)]
                else:
                    filtered_m = active_m

                available_names = sorted(filtered_m['姓名'].tolist())
                
                if cat_filter == "環保志工" and group_filter != "全部":
                    group_names = env_groups.get(group_filter, [])
                    available_names = [n for n in available_names if n in group_names]

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
                        st.session_state.temp_vols = [] 
                        time.sleep(1)
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        with col_status:
            st.markdown("#### 🟢 目前在場志工")
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
        df_m = get_volunteer_members()
        if not df_m.empty:
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)]
            
            st.markdown("### 🛠️ 補登操作")
            if 'ms_vols_tab2' not in st.session_state: st.session_state.ms_vols_tab2 = []
                
            cat_filter_tab2 = st.selectbox("📌 篩選志工分類", ["全部", "環保志工", "祥和志工", "關懷據點週二志工", "關懷據點週三志工"], key="cat_filter_tab2")
            
            if cat_filter_tab2 != "全部":
                filtered_m_tab2 = active_m[active_m['志工分類'].astype(str).str.contains(cat_filter_tab2, na=False)]
            else:
                filtered_m_tab2 = active_m
                
            available_names_tab2 = sorted(filtered_m_tab2['姓名'].tolist())
            final_opts = sorted(list(set(available_names_tab2 + st.session_state.ms_vols_tab2)))
            
            c1, c2, c3, c4 = st.columns(4)
            d_date = c1.date_input("日期", value=date.today(), key="d_date_tab2")
            d_time = c2.time_input("時間", value=get_tw_time().time(), key="d_time_tab2")
            d_action = c3.selectbox("動作", ["簽到", "簽退"], key="d_action_tab2")
            d_act = c4.selectbox("活動", DEFAULT_ACTIVITIES, key="d_act_tab2")
            
            st.multiselect(
                "👤 選擇志工 (可單選或多選)", 
                options=final_opts,
                placeholder="請點此選擇要補登的志工...",
                key="ms_vols_tab2" 
            )
            
            st.write("") 
            if st.button("✅ 確認補登", type="primary"):
                selected_names = st.session_state.ms_vols_tab2
                
                if not selected_names:
                    st.error("❌ 請至少選擇一位志工！")
                else:
                    new_rows = []
                    for n in selected_names:
                        row = active_m[active_m['姓名'] == n].iloc[0]
                        new_rows.append({
                            '姓名': n, '身分證字號': row['身分證字號'], '電話': row['電話'], 
                            '志工分類': row['志工分類'], '動作': d_action, 
                            '時間': d_time.strftime("%H:%M:%S"), '日期': d_date.strftime("%Y-%m-%d"), 
                            '活動內容': d_act
                        })
                    
                    if batch_append_data("logs", new_rows, LOG_COLS):
                        st.success(f"✅ 已成功補登 {len(selected_names)} 筆資料！")
                        st.session_state.ms_vols_tab2 = []
                        time.sleep(1)
                        st.rerun()

elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊管理")
    df = get_volunteer_members()
    
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
                    
                    if add_or_update_volunteer_to_master(new_data):
                        st.success("新增成功並同步至主檔"); time.sleep(1); st.rerun()
    
    st.markdown("### 📝 完整志工名冊 (需密碼)")
    if not st.session_state.unlock_vol_members:
        c_pwd, c_btn = st.columns([2, 1])
        with c_pwd:
            pwd = st.text_input("請輸入管理員密碼", type="password", key="vol_pwd")
        with c_btn:
            st.markdown("<br>", unsafe_allow_html=True) 
            if st.button("🔓 解鎖名冊"):
                if pwd == st.secrets["admin_password"]:
                    st.session_state.unlock_vol_members = True
                    st.rerun()
                else:
                    st.error("密碼錯誤")
    else:
        if st.button("🔒 鎖定名冊"):
            st.session_state.unlock_vol_members = False
            st.rerun()
            
        if not df.empty:
            df['狀態'] = df.apply(lambda r: '已退隊' if check_is_fully_retired(r) else '服務中', axis=1)
            df['年齡'] = df['生日'].apply(calculate_age)
            df = df.sort_values(by='姓名')
            
            cols = ['姓名', '年齡', '電話', '地址', '志工分類'] + [c for c in df.columns if '日期' in c] + ['備註']
            cols = [c for c in cols if c in df.columns]
            tab_active, tab_retired = st.tabs(["🔥 服務中", "🍂 已退隊"])
            with tab_active:
                active_df = df[df['狀態'] == '服務中']
                ed_df = st.data_editor(active_df[cols], use_container_width=True, num_rows="dynamic", key="editor_active")
                if st.button("💾 儲存修改 (將寫回舊名冊表)"):
                    save_data_to_sheet(ed_df, "members")
                    st.success("✅ 修改已儲存！")
                    time.sleep(1); st.rerun()
            with tab_retired:
                retired_df = df[df['狀態'] == '已退隊']
                st.data_editor(retired_df[cols], use_container_width=True, num_rows="dynamic", key="editor_retired")

elif st.session_state.page == 'report':
    render_nav()
    st.markdown("## 📊 數據分析與報表")
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
                
                cov_seconds = calculate_coverage_seconds(view_df)
                cov_h = int(cov_seconds // 3600)
                cov_m = int((cov_seconds % 3600) // 60)
                team_time_str = f"{cov_h}小時 {cov_m}分" 

                tot_sess, _, _ = calc_stats_display(view_df) 
                
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f"""<div class="metric-box"><div class="metric-label">總人次</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="metric-box"><div class="metric-label">團隊服務時數</div><div class="metric-value">{team_time_str}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="metric-box"><div class="metric-label">參與志工數</div><div class="metric-value">{view_df['姓名'].nunique()}</div></div>""", unsafe_allow_html=True)
                
                csv = view_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載此報表 (CSV)", data=csv, file_name=f"志工報表_{date.today()}.csv", mime="text/csv")
                
                st.markdown("### 📋 人員明細表")
                summary = []
                for name, g in view_df.groupby('姓名'):
                    c, s_str, s_num = calc_stats_display(g)
                    summary.append({'姓名': name, '次數': c, '時數': s_str, '排序用時數': s_num})
                
                summ_df = pd.DataFrame(summary).sort_values('排序用時數', ascending=False)
                
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

            else: 
                all_names = sorted(filtered_logs['姓名'].unique().tolist())
                target_name = st.selectbox("選擇志工", all_names)
                view_df = filtered_logs[filtered_logs['姓名'] == target_name]
                tot_sess, tot_time_str, _ = calc_stats_display(view_df)
                
                m1, m2 = st.columns(2)
                with m1: st.markdown(f"""<div class="metric-box"><div class="metric-label">執勤次數</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="metric-box"><div class="metric-label">累積時數</div><div class="metric-value">{tot_time_str}</div></div>""", unsafe_allow_html=True)
                
                csv = view_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載個人紀錄 (CSV)", data=csv, file_name=f"個人報表_{target_name}_{date.today()}.csv", mime="text/csv")
                
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
