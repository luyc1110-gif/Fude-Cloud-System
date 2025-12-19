import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import os

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

# 配色變數
PRIMARY = "#4A148C"   # 尊爵紫 (文字/邊框)
ACCENT  = "#7B1FA2"   # 亮紫 (圖表/重點)
BG_MAIN = "#F0F2F5"   # 灰藍底 (現代感背景)
TEXT    = "#212121"   # 深黑字 (確保清晰)

# =========================================================
# 1) CSS 樣式 (V15.0 顯色終極版 + 導航回歸)
# =========================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

/* 1. 全域字體強制深色 (解決字體看不到的問題) */
html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}
.stApp {{ background-color: {BG_MAIN}; }}

/* 隱藏原生元素 */
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 2. 輸入框與下拉選單顯色 (強制白底黑字) */
.stTextInput input, .stDateInput input, .stTimeInput input {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #9FA8DA !important;
    border-radius: 10px;
    font-weight: 700;
}}
/* 下拉選單文字 */
div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 10px;
    border: 1px solid #9FA8DA !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}
div[role="listbox"] ul {{ background-color: #FFFFFF !important; }}
div[role="option"] {{ color: #000000 !important; }}

/* 標籤文字 */
label {{
    color: {PRIMARY} !important;
    font-weight: 900 !important;
    font-size: 1.05rem !important;
}}

/* 3. 按鈕美化 (大卡片風格回歸) */
div[data-testid="stButton"] > button {{
    width: 100%;
    background-color: white !important;
    color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important;
    border-radius: 15px !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    padding: 12px 0 !important;
    box-shadow: 0 4px 0px rgba(74, 20, 140, 0.2);
    transition: all 0.1s;
}}
div[data-testid="stButton"] > button:hover {{
    transform: translateY(-2px);
    background-color: #F3E5F5 !important;
}}
div[data-testid="stButton"] > button:active {{ transform: translateY(2px); box-shadow: none; }}

/* 表單送出按鈕 (實心紫 + 強制白字) */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT}) !important;
    color: #FFFFFF !important;      /* 強制亮白字 */
    font-weight: 900 !important;    /* 最粗體 */
    font-size: 1.2rem !important;   /* 字變大 */
    border: none !important;
    box-shadow: 0 4px 15px rgba(123, 31, 162, 0.3) !important; /* 增加立體感 */
}
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(123, 31, 162, 0.5) !important;
}

/* 4. 萬物皆卡片 (Forms, Dataframes, Expanders) */
div[data-testid="stForm"], div[data-testid="stDataFrame"], .streamlit-expanderContent, div[data-testid="stExpander"] details {{
    background-color: white;
    border-radius: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    padding: 25px;
    margin-bottom: 20px;
    border: 1px solid white;
}}

/* 5. 戰情室小卡 (Home Stats) */
.dash-card {{
    background-color: white;
    padding: 15px;
    border-radius: 15px;
    border-left: 6px solid {ACCENT};
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}}
.dash-label {{ font-size: 1rem; color: #666 !important; font-weight: bold; }}
.dash-value {{ font-size: 1.8rem; color: {PRIMARY} !important; font-weight: 900; margin: 5px 0; }}
.dash-sub {{ font-size: 0.9rem; color: #888 !important; }}

/* 6. 名冊檢視按鈕 (Pills) */
div[data-testid="stRadio"] label {{
    background-color: white;
    border: 1px solid #ddd;
    padding: 10px 20px;
    border-radius: 20px;
    margin-right: 10px;
    cursor: pointer;
    font-weight: bold;
    color: {TEXT} !important;
    transition: all 0.2s;
}}
div[data-testid="stRadio"] label:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY} !important;
}}

/* 7. 導航列容器 */
.nav-container {{
    background-color: white;
    padding: 15px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}

/* 圖片容器對齊 */
div[data-testid="stImage"] {{
    display: flex;
    justify-content: center;
    align-items: flex-end;
    height: 120px;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Google Sheets & Logic
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]
DISPLAY_ORDER = [
    "姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註",
    "祥和_加入日期", "祥和_退出日期",
    "據點週二_加入日期", "據點週二_退出日期",
    "據點週三_加入日期", "據點週三_退出日期",
    "環保_加入日期", "環保_退出日期",
]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df = df.astype(str)
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

def get_tw_time():
    return datetime.now(TW_TZ)

def calculate_age(birthday_str):
    if not birthday_str or len(birthday_str) < 4: return 0
    try:
        b_date = datetime.strptime(str(birthday_str).strip(), "%Y-%m-%d")
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any = False
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and str(row[join_col]).strip() != "":
            has_any = True
            if exit_col not in row or str(row[exit_col]).strip() == "":
                is_active = True
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

# =========================================================
# 3) Navigation (導航列 - 在內頁顯示)
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    # 使用白色卡片區塊包住導航按鈕，更有質感
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 回首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("⏰ 智能打卡", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
    with c3:
        if st.button("📋 志工名冊", use_container_width=True): st.session_state.page = 'members'; st.rerun()
    with c4:
        if st.button("📊 數據分析", use_container_width=True): st.session_state.page = 'report'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4) Page: Home (首頁)
# =========================================================
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; color: {PRIMARY}; margin-bottom: 30px; margin-top: 20px;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    # 卡片區 (排版：左1.5, 中2,2,2, 右0.5)
    col_spacer_l, c1, c2, c3, col_spacer_r = st.columns([1.5, 2, 2, 2, 0.5])
    
    with c1:
        if os.path.exists("icon_checkin.png"): st.image("icon_checkin.png", width=120)
        else: st.markdown("<div style='text-align:center; font-size:60px;'>⏰</div>", unsafe_allow_html=True)
        if st.button("智能打卡站", key="home_btn1"): st.session_state.page = 'checkin'; st.rerun()

    with c2:
        if os.path.exists("icon_members.png"): st.image("icon_members.png", width=120)
        else: st.markdown("<div style='text-align:center; font-size:60px;'>📋</div>", unsafe_allow_html=True)
        if st.button("志工名冊", key="home_btn2"): st.session_state.page = 'members'; st.rerun()

    with c3:
        if os.path.exists("icon_report.png"): st.image("icon_report.png", width=120)
        else: st.markdown("<div style='text-align:center; font-size:60px;'>📊</div>", unsafe_allow_html=True)
        if st.button("數據分析", key="home_btn3"): st.session_state.page = 'report'; st.rerun()
    
    st.markdown("---")
    
    # 1. 總時數大卡片
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    this_year = datetime.now().year
    
    total_sec = calculate_hours_year(logs, this_year)
    total_hours = int(total_sec // 3600)
    total_mins = int((total_sec % 3600) // 60)
    
    st.markdown(f"### 📊 {this_year} 年度即時概況")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(81, 45, 168, 0.25);">
        <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">📅 {this_year} 年度 - 全體志工總服務時數</div>
        <div style="font-size: 3.5rem; font-weight: 900; margin: 15px 0; color: white !important;">
            {total_hours} <span style="font-size: 1.5rem; color: white !important;">小時</span> 
            {total_mins} <span style="font-size: 1.5rem; color: white !important;">分</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 各分類統計卡片 (修復回歸！)
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
                st.markdown(f"""
                <div class="dash-card">
                    <div class="dash-label">{cat.replace('志工','')}</div>
                    <div class="dash-value">{count} <span style="font-size:1rem;color:#888;">人</span></div>
                    <div class="dash-sub">平均 {avg_age} 歲</div>
                </div>
                """, unsafe_allow_html=True)

# =========================================================
# 5) Page: Checkin (打卡)
# =========================================================
elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    st.caption(f"📅 台灣時間：{get_tw_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 'input_pid' not in st.session_state: st.session_state.input_pid = ""
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}

    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])
    
    with tab1:
        st.markdown('<div style="background:white; padding:20px; border-radius:20px; border:1px solid white; margin-bottom:20px;">', unsafe_allow_html=True)
        
        c_act, c_note = st.columns([1, 2])
        with c_act:
            raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
        
        # 專案活動邏輯
        note = ""
        with c_note:
            if raw_act in ["專案活動", "教育訓練"]:
                note = st.text_input("📝 請輸入活動名稱 (必填)", placeholder="例如：大掃除")
            else:
                st.write("") # 佔位

        def process_scan():
            pid = st.session_state.input_pid.strip().upper()
            if not pid: return

            # 檢查專案名稱
            final_act = raw_act
            if raw_act in ["專案活動", "教育訓練"]:
                if not note.strip():
                    st.error("⚠️ 請填寫「活動名稱」才能打卡！")
                    return
                final_act = f"{raw_act}：{note}"

            now = get_tw_time()
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.warning(f"⏳ 請勿重複刷卡 ({pid})")
                st.session_state.input_pid = ""
                return

            df_m = load_data_from_sheet("members")
            df_l = load_data_from_sheet("logs")
            
            if df_m.empty: st.error("❌ 無法讀取名單"); return
            
            person = df_m[df_m['身分證字號'] == pid]
            if not person.empty:
                row = person.iloc[0]
                name = row['姓名']
                if check_is_fully_retired(row):
                    st.error(f"❌ {name} 已退出")
                else:
                    today = now.strftime("%Y-%m-%d")
                    t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == today)]
                    action = "簽到"
                    if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到": action = "簽退"
                    
                    new_log = pd.DataFrame([{
                        '姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'],
                        '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': final_act
                    }])
                    save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True), "logs")
                    st.session_state['scan_cooldowns'][pid] = now
                    st.success(f"✅ {name} {action} 成功！")
            else:
                st.error("❌ 查無此人")
            
            st.session_state.input_pid = ""

        st.text_input("請輸入身分證 (Enter)", key="input_pid", on_change=process_scan)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        df_m = load_data_from_sheet("members")
        if not df.empty:
        st.write("")
        # 計算狀態與年齡
        df['狀態'] = df.apply(lambda r: '已退隊' if check_is_fully_retired(r) else '服務中', axis=1)
        df['年齡'] = df['生日'].apply(calculate_age)
        
        # 欄位設定
        cols = ['姓名', '年齡', '電話', '地址', '志工分類'] + [c for c in df.columns if '日期' in c] + ['備註']
        cols = [c for c in cols if c in df.columns]

        # 改用有設計感的 Tabs 分頁切換
        tab_active, tab_retired = st.tabs(["🔥 服務中", "🍂 已退隊"])
        
        with tab_active:
            active_df = df[df['狀態'] == '服務中']
            st.data_editor(active_df[cols], use_container_width=True, num_rows="dynamic", key="editor_active")
            
        with tab_retired:
            retired_df = df[df['狀態'] == '已退隊']
            st.data_editor(retired_df[cols], use_container_width=True, num_rows="dynamic", key="editor_retired")
            if st.button("💾 儲存修改"):
                save_data_to_sheet(edited, "logs")
                st.success("已更新")

# =========================================================
# 6) Page: Members (名冊)
# =========================================================
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")
    
    with st.expander("➕ 新增志工 (展開填寫)", expanded=True):
        with st.form("add_m"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            b = c3.text_input("生日 (YYYY-MM-DD)")
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            ph = c5.text_input("電話")
            
            st.markdown("---")
            st.markdown("**2. 志工分類與加入日期 (勾選後自動出現日期欄)**")
            
            # 卡片式條列設計
            col_l, col_r = st.columns([1, 2])
            with col_l:
                st.markdown("###### 勾選分類")
                is_x = st.checkbox("祥和志工")
                is_t = st.checkbox("據點週二志工")
                is_w = st.checkbox("據點週三志工")
                is_e = st.checkbox("環保志工")
            
            with col_r:
                st.markdown("###### 填寫加入日期")
                # 只有勾選才顯示，但為了排版穩定，這裡全部顯示，沒勾的存空值
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
                    new = pd.DataFrame([new_data])
                    for c in DISPLAY_ORDER: 
                        if c not in new.columns: new[c] = ""
                    save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                    st.success("新增成功"); time.sleep(1); st.rerun()

    if not df.empty:
        st.write("")
        mode = st.radio("名單檢視", ["🟢 在職志工", "📋 所有名單"], horizontal=True)
        
        df['狀態'] = df.apply(lambda r: '已退出' if check_is_fully_retired(r) else '在職', axis=1)
        df['年齡'] = df['生日'].apply(calculate_age)
        
        show_df = df[df['狀態'] == '在職'] if "在職" in mode else df
        
        cols = ['狀態', '姓名', '年齡', '電話', '地址', '志工分類'] + [c for c in df.columns if '日期' in c] + ['備註']
        cols = [c for c in cols if c in df.columns]
        st.data_editor(show_df[cols], use_container_width=True, num_rows="dynamic", key="m_edit")

# =========================================================
# 7) Page: Report (儀表板化 - 日期區間分析)
# =========================================================
elif st.session_state.page == 'report':
    render_nav()
    st.markdown("## 📊 數據分析")
    
    logs = load_data_from_sheet("logs")
    
    # 儀表板篩選器
    st.markdown('<div style="background:white; padding:20px; border-radius:15px; border:1px solid #ddd; margin-bottom:20px;">', unsafe_allow_html=True)
    c_date, c_mode = st.columns([1, 1])
    with c_date:
        # 日期區間
        d_range = st.date_input("📅 選擇日期區間", value=(date(date.today().year, 1, 1), date.today()))
    with c_mode:
        report_mode = st.radio("分析模式", ["依活動查詢", "依志工查詢"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if logs.empty:
        st.info("無打卡資料")
    else:
        # 資料預處理
        logs['dt'] = pd.to_datetime(logs['日期'] + ' ' + logs['時間'], errors='coerce')
        logs = logs.dropna(subset=['dt'])
        
        # 1. 篩選日期
        if isinstance(d_range, tuple) and len(d_range) == 2:
            start_d, end_d = d_range
            mask = (logs['dt'].dt.date >= start_d) & (logs['dt'].dt.date <= end_d)
            filtered_logs = logs[mask].copy()
        else:
            filtered_logs = logs.copy()
            
        if filtered_logs.empty:
            st.warning("此區間無資料")
        else:
            # 計算函數
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

            # === 依活動查詢 ===
            if report_mode == "依活動查詢":
                all_acts = filtered_logs['活動內容'].unique().tolist()
                target_act = st.selectbox("選擇活動", ["全部"] + all_acts)
                
                view_df = filtered_logs if target_act == "全部" else filtered_logs[filtered_logs['活動內容'] == target_act]
                
                # 計算總體
                tot_sess, tot_time_str, _ = calc_stats_display(view_df)
                
                # 顯示卡片
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f"""<div class="metric-card"><div class="metric-label">總人次</div><div class="metric-value">{tot_sess}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="metric-card"><div class="metric-label">總時數</div><div class="metric-value">{tot_time_str}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="metric-card"><div class="metric-label">參與志工數</div><div class="metric-value">{view_df['姓名'].nunique()}</div></div>""", unsafe_allow_html=True)
                
                st.markdown("### 📋 人員明細表")
                # 計算每個人的
                summary = []
                for name, g in view_df.groupby('姓名'):
                    c, s_str, s_num = calc_stats_display(g)
                    summary.append({'姓名': name, '次數': c, '時數': s_str, '排序用時數': s_num})
                
                st.dataframe(pd.DataFrame(summary).sort_values('排序用時數', ascending=False)[['姓名', '次數', '時數']], use_container_width=True)

            # === 依志工查詢 ===
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
