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
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A148C"
ACCENT  = "#7B1FA2"
BG_MAIN = "#F0F2F5"
TEXT    = "#212121"

# =========================================================
# 1) CSS 樣式 (V17.0 顯色+導航優化)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 輸入框與選單顯色修復 */
.stTextInput input, .stDateInput input, .stTimeInput input {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 2px solid #9FA8DA !important;
    border-radius: 10px;
    font-weight: 700;
}}
div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    border: 2px solid #9FA8DA !important;
    border-radius: 10px !important;
    color: #000000 !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; font-weight: 700 !important; }}
ul[data-baseweb="menu"], div[role="listbox"] {{ background-color: #FFFFFF !important; }}
li[role="option"], div[role="option"] {{
    color: #000000 !important; background-color: #FFFFFF !important; font-weight: 700 !important;
}}
li[role="option"]:hover, div[role="option"]:hover {{ background-color: #E1BEE7 !important; }}

label {{ color: {PRIMARY} !important; font-weight: 900 !important; font-size: 1.1rem !important; }}

/* 按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important;
    padding: 12px 0 !important; box-shadow: 0 4px 0px rgba(74, 20, 140, 0.2);
    transition: all 0.1s;
}}
div[data-testid="stButton"] > button:hover {{ transform: translateY(-2px); background-color: #F3E5F5 !important; }}
div[data-testid="stButton"] > button:active {{ transform: translateY(2px); box-shadow: none; }}

div[data-testid="stFormSubmitButton"] > button {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT}) !important;
    color: #FFFFFF !important; font-weight: 900 !important; border: none !important;
}}

/* 卡片 */
div[data-testid="stForm"], div[data-testid="stDataFrame"], .streamlit-expanderContent, div[data-testid="stExpander"] details {{
    background-color: white; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    padding: 25px; margin-bottom: 20px; border: 1px solid white;
}}
.dash-card {{
    background-color: white; padding: 15px; border-radius: 15px; border-left: 6px solid {ACCENT};
    box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px;
}}
.dash-label {{ font-size: 1rem; color: #666 !important; font-weight: bold; }}
.dash-value {{ font-size: 1.8rem; color: {PRIMARY} !important; font-weight: 900; margin: 5px 0; }}
.dash-sub {{ font-size: 0.9rem; color: #888 !important; }}

.nav-container {{
    background-color: white; padding: 15px; border-radius: 20px;
    margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}
div[data-testid="stImage"] {{ display: flex; justify-content: center; align-items: flex-end; height: 120px; }}

div[data-baseweb="tab-list"] {{ gap: 10px; }}
div[data-baseweb="tab"] {{
    background-color: white; border-radius: 30px; padding: 10px 20px; border: 1px solid #E0E0E0;
    font-weight: bold; color: {TEXT} !important;
}}
div[data-baseweb="tab"][aria-selected="true"] {{
    background-color: {PRIMARY} !important; color: white !important; border: 1px solid {PRIMARY};
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic
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
    """計算目前場內有哪些人（最後動作為簽到者）"""
    if logs_df.empty: return pd.DataFrame()
    today_str = get_tw_time().strftime("%Y-%m-%d")
    # 篩選今日紀錄
    today_logs = logs_df[logs_df['日期'] == today_str].copy()
    if today_logs.empty: return pd.DataFrame()
    
    # 確保按時間排序
    today_logs['dt'] = pd.to_datetime(today_logs['日期'] + ' ' + today_logs['時間'])
    today_logs = today_logs.sort_values('dt')
    
    # 抓取每個人最後一筆狀態
    latest_status = today_logs.groupby('身分證字號').last().reset_index()
    
    # 篩選出最後動作是 "簽到" 的人
    present = latest_status[latest_status['動作'] == '簽到']
    return present[['姓名', '時間', '活動內容']]

# =========================================================
# 3) Navigation
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    # 內頁導航，只回到志工首頁
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
    # 🔥 首頁上方增加「回系統大廳」
    c_back, c_empty = st.columns([1, 4])
    with c_back:
        if st.button("🚪 回系統大廳"): st.switch_page("Home.py")

    st.markdown(f"<h1 style='text-align: center; color: {PRIMARY}; margin-bottom: 30px;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    col_spacer_l, c1, c2, c3, col_spacer_r = st.columns([1.5, 1.5, 1.5, 1.5, 0.5])
    with c1:
        # --- 1. 圖示部分 (保持不動) ---
        if os.path.exists("icon_checkin.png"): 
            st.image("icon_checkin.png", width=120)
        else: 
            st.markdown("<div style='text-align:center; font-size:60px;'>⏰</div>", unsafe_allow_html=True)
        
        # --- 2. 按鈕部分 (加隔間把按鈕往右推) ---
        # 這裡是在 c1 裡面再切出 [1, 3] 兩塊巧克力
        sub_spacer, sub_button = st.columns([0.2, 3.8]) 
        
        with sub_button:
            # key 一定要唯一，不能重複喔
            if st.button("智能打卡站", key="home_btn1_fixed"): 
                st.session_state.page = 'checkin'
                st.rerun()
    with c2:
        # --- 1. 圖示部分 (保持不動) ---
        if os.path.exists("icon_members.png"): 
            st.image("icon_members.png", width=120)
        else: 
            st.markdown("<div style='text-align:center; font-size:60px;'>📋</div>", unsafe_allow_html=True)
        
        # --- 2. 按鈕部分 (加隔間把按鈕往右推) ---
        # 這裡是在 c2 裡面再切出 [1, 3] 兩塊巧克力
        sub_spacer, sub_button = st.columns([0.2, 3.8]) 
        
        with sub_button:
            # key 一定要唯一，不能重複喔
            if st.button("志工名冊", key="home_btn2_fixed"): 
                st.session_state.page = 'members'
                st.rerun()
    with c3:
        # --- 1. 圖示部分 (保持不動) ---
        if os.path.exists("icon_report.png"): 
            st.image("icon_report.png", width=120)
        else: 
            st.markdown("<div style='text-align:center; font-size:60px;'>📊</div>", unsafe_allow_html=True)
        
        # --- 2. 按鈕部分 (加隔間把按鈕往右推) ---
        # 這裡是在 c2 裡面再切出 [1, 3] 兩塊巧克力
        sub_spacer, sub_button = st.columns([0.2, 3.8]) 
        
        with sub_button:
            # key 一定要唯一，不能重複喔
            if st.button("數據分析", key="home_btn3_fixed"): 
                st.session_state.page = 'report'
                st.rerun()
    
    st.markdown("---")
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    this_year = datetime.now().year
    total_sec = calculate_hours_year(logs, this_year)
    total_hours = int(total_sec // 3600)
    total_mins = int((total_sec % 3600) // 60)
    
    st.markdown(f"### 📊 {this_year} 年度即時概況")
    st.markdown(f"""
    <div style="background: #ceafe3; padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(81, 45, 168, 0.25);">
        <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">📅 {this_year} 年度 - 全體志工總服務時數</div>
        <div style="font-size: 3.5rem; font-weight: 900; margin: 15px 0; color: white !important;">
            {total_hours} <span style="font-size: 1.5rem; color: white !important;">小時</span> 
            {total_mins} <span style="font-size: 1.5rem; color: white !important;">分</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not members.empty:
        active_m = members[~members.apply(check_is_fully_retired, axis=1)].copy()
        active_m['age'] = active_m['生日'].apply(calculate_age)
        valid_age = active_m[active_m['age'] > 0]
        cols = st.columns(4)
        for idx, cat in enumerate(ALL_CATEGORIES):
            if cat == "臨時志工": continue
            subset = active_m[active_m['志工分類'].astype(str).str.contains(cat, na=False)]
            count = len(subset)
            age_subset = valid_age[valid_age['志工分類'].astype(str).str.contains(cat, na=False)]
            avg_age = round(age_subset['age'].mean(), 1) if not age_subset.empty else 0
            with cols[idx % 4]:
                st.markdown(f"""<div class="dash-card"><div class="dash-label">{cat.replace('志工','')}</div><div class="dash-value">{count} <span style="font-size:1rem;color:#888;">人</span></div><div class="dash-sub">平均 {avg_age} 歲</div></div>""", unsafe_allow_html=True)

elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    st.caption(f"📅 台灣時間：{get_tw_time().strftime('%Y-%m-%d %H:%M:%S')}")
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}

    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])
    with tab1:
        # --- 版面配置：左邊掃描區，右邊即時狀態 ---
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

            # 定義處理邏輯
            def process_scan():
                pid = st.session_state.input_pid.strip().upper()
                if not pid: return
                final_act = raw_act
                if raw_act in ["專案活動", "教育訓練"]:
                    if not note.strip(): st.error("⚠️ 請填寫「活動名稱」才能打卡！"); return
                    final_act = f"{raw_act}：{note}"
                
                now = get_tw_time()
                last = st.session_state['scan_cooldowns'].get(pid)
                # 防止連點 (2秒冷卻)
                if last and (now - last).total_seconds() < 2: 
                    st.warning(f"⏳ 刷卡過快，請稍候"); st.session_state.input_pid = ""; return
                
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
                        
                        # 自動判斷 簽到 或是 簽退
                        action = "簽到"
                        if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到": 
                            action = "簽退"
                        
                        new_log = pd.DataFrame([{'姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'], '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': final_act}])
                        save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True), "logs")
                        st.session_state['scan_cooldowns'][pid] = now
                        
                        if action == "簽到":
                            st.toast(f"✅ {name} 簽到成功！", icon="👋")
                        else:
                            st.toast(f"✅ {name} 簽退成功！", icon="🏠")
                else: 
                    st.error("❌ 查無此人")
                
                # 清空輸入框
                st.session_state.input_pid = ""

            # 輸入框 (綁定 Enter 觸發 callback)
            st.text_input("請輸入身分證 (Enter)", key="input_pid", on_change=process_scan, placeholder="掃描或輸入後按 Enter")
            
            # --- JavaScript 自動 Focus 核心 ---
            # 這段 JS 會尋找 label 為 "請輸入身分證 (Enter)" 的 input 元素並強制聚焦
            components.html(f"""
                <script>
                    var input = window.parent.document.querySelector('input[aria-label="請輸入身分證 (Enter)"]');
                    if (input) {{
                        input.focus();
                    }}
                </script>
            """, height=0, width=0)
            
            st.markdown('</div>', unsafe_allow_html=True)

        with col_status:
            st.markdown("#### 🟢 目前在場志工")
            logs = load_data_from_sheet("logs")
            present_df = get_present_volunteers(logs)
            
            if not present_df.empty:
                count = len(present_df)
                st.markdown(f"<div style='font-size:2rem; font-weight:bold; color:#4A148C; margin-bottom:10px;'>共 {count} 人</div>", unsafe_allow_html=True)
                
                # 美化顯示列表
                for idx, row in present_df.iterrows():
                    st.markdown(f"""
                    <div style="background:white; padding:10px; border-radius:10px; border-left: 5px solid #66BB6A; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom:8px;">
                        <div style="font-weight:bold; font-size:1.1rem;">{row['姓名']}</div>
                        <div style="font-size:0.85rem; color:#666;">🕒 {row['時間']} | 🚩 {row['活動內容']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("目前無人簽到中")

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
                st.markdown("### 📋 執勤紀錄明細")
                st.dataframe(view_df[['日期', '時間', '動作', '活動內容']].sort_values(['日期', '時間'], ascending=False), use_container_width=True)
