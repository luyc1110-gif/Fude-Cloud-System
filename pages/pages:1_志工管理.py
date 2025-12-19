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
PRIMARY = "#4A148C"   # 尊爵紫
ACCENT  = "#7B1FA2"   # 亮紫
BG_MAIN = "#F0F2F5"   # 灰藍底
TEXT    = "#212121"
MUTED   = "#666666"

# =========================================================
# 1) CSS 樣式 (V14.0 顯色修復與按鈕化版)
# =========================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

/* 全域設定 */
html, body, [class*="css"] {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT};
}}
.stApp {{ background-color: {BG_MAIN}; }}

/* 隱藏原生元素 */
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 🔥 3. & 6. 關鍵修復：輸入框與下拉選單顯色 (強制黑字) */
.stTextInput input, .stDateInput input, .stTimeInput input {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #9FA8DA !important;
    border-radius: 8px;
    font-weight: 500;
}}
/* 下拉選單 (Selectbox) 內部文字修復 */
div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 8px;
    border: 1px solid #9FA8DA !important;
}}
div[data-baseweb="select"] span {{
    color: #000000 !important; /* 選單選中後的文字顏色 */
}}
div[role="listbox"] ul {{
    background-color: #FFFFFF !important;
}}
div[role="option"] {{
    color: #000000 !important; /* 下拉選項的文字顏色 */
}}

/* 標籤文字 */
label {{
    color: {PRIMARY} !important;
    font-weight: bold !important;
    font-size: 1rem !important;
}}

/* 導航按鈕 (首頁與上方) */
div[data-testid="stButton"] > button {{
    width: 100%;
    background-color: white !important;
    color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important;
    border-radius: 15px !important;
    font-weight: 900 !important;
    box-shadow: 0 4px 0px rgba(74, 20, 140, 0.2);
    transition: all 0.1s;
}}
div[data-testid="stButton"] > button:hover {{
    transform: translateY(-2px);
    background-color: #F3E5F5 !important;
}}
div[data-testid="stButton"] > button:active {{ transform: translateY(2px); box-shadow: none; }}

/* 表單送出按鈕 (實心紫) */
div[data-testid="stFormSubmitButton"] > button {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT}) !important;
    color: white !important;
    border: none !important;
}}

/* 卡片容器 (萬物皆卡片) */
div[data-testid="stForm"], div[data-testid="stDataFrame"], .streamlit-expanderContent, div[data-testid="stExpander"] details {{
    background-color: white;
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid white;
}}

/* 儀表板數據卡 (Dashboard Metric) */
.metric-card {{
    background: white;
    padding: 20px;
    border-radius: 15px;
    border-left: 6px solid {ACCENT};
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    text-align: center;
}}
.metric-label {{ font-size: 1rem; color: #666; font-weight: bold; }}
.metric-value {{ font-size: 2.2rem; font-weight: 900; color: {PRIMARY}; margin: 5px 0; }}
.metric-sub {{ font-size: 0.9rem; color: #888; }}

/* 1. 名冊檢視模式按鈕 (改為 Pills 風格) */
div[data-testid="stRadio"] label {{
    background-color: white;
    border: 1px solid #ddd;
    padding: 10px 20px;
    border-radius: 20px;
    margin-right: 10px;
    cursor: pointer;
    font-weight: bold;
    color: {TEXT};
    transition: all 0.2s;
}}
div[data-testid="stRadio"] label:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY};
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

# 計算時數與人次 (精確到分)
def calculate_stats(logs_df):
    if logs_df.empty: return 0, 0
    
    logs_df['dt'] = pd.to_datetime(logs_df['日期'] + ' ' + logs_df['時間'], errors='coerce')
    logs_df = logs_df.dropna(subset=['dt']).sort_values(['姓名', 'dt'])
    
    total_seconds = 0
    total_sessions = 0
    
    for (name, date_val), group in logs_df.groupby(['姓名', '日期']):
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
            
    return total_sessions, total_seconds

# 轉換秒數為 "X小時 Y分"
def format_seconds(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}小時 {m}分", h + round(m/60, 1)

# =========================================================
# 3) Navigation
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    with st.container():
        c1, c2, c3, spacer = st.columns([1, 1, 1, 4])
        with c1:
            if st.button("🏠 首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
        with c2:
            if st.button("⏰ 打卡", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
        with c3:
            if st.button("📊 報表", use_container_width=True): st.session_state.page = 'report'; st.rerun()
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# =========================================================
# 4) Page: Home (首頁)
# =========================================================
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; color: {PRIMARY}; margin-bottom: 30px; margin-top: 20px;'>福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
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
    
    # 年度概況 (維持不動)
    logs = load_data_from_sheet("logs")
    this_year = datetime.now().year
    
    # 簡單計算今年總時數
    total_sec = 0
    if not logs.empty:
        logs['dt'] = pd.to_datetime(logs['日期'] + ' ' + logs['時間'], errors='coerce')
        y_logs = logs[logs['dt'].dt.year == this_year].copy()
        _, total_sec = calculate_stats(y_logs)
    
    h_str, _ = format_seconds(total_sec)
    h_only = h_str.split('小時')[0]
    m_only = h_str.split('小時')[1].replace('分','').strip()

    st.markdown(f"### 📊 {this_year} 年度即時概況")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(81, 45, 168, 0.25);">
        <div style="font-size: 1.2rem; opacity: 0.9;">📅 {this_year} 年度 - 全體志工總服務時數</div>
        <div style="font-size: 3.5rem; font-weight: 900; margin: 15px 0;">{h_only} <span style="font-size: 1.5rem;">小時</span> {m_only} <span style="font-size: 1.5rem;">分</span></div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 5) Page: Checkin (打卡站 - 邏輯修正版)
# =========================================================
elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    st.caption(f"📅 台灣時間：{get_tw_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化 Session State (用於清空輸入框)
    if 'scan_box_key' not in st.session_state: st.session_state.scan_box_key = ""
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}

    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])
    
    with tab1:
        # 1. 選擇活動 (移出 form 以便即時反應)
        st.markdown('<div style="background:white; padding:20px; border-radius:20px; border:1px solid white; margin-bottom:20px;">', unsafe_allow_html=True)
        
        c_act, c_note = st.columns([1, 2])
        with c_act:
            raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
        
        # 4. 動態顯示說明欄位
        note = ""
        with c_note:
            if raw_act in ["專案活動", "教育訓練"]:
                note = st.text_input("📝 請輸入活動名稱 (必填)", placeholder="例如：社區大掃除")
            else:
                st.write("") # 佔位

        # 核心打卡邏輯
        def process_scan():
            # 取得輸入的身分證
            pid = st.session_state.input_pid.strip().upper()
            if not pid: return # 空值不處理

            # 4. 檢查專案活動是否填寫說明
            final_act = raw_act
            if raw_act in ["專案活動", "教育訓練"]:
                if not note.strip():
                    st.error("⚠️ 請填寫「活動名稱」才能打卡！")
                    return
                final_act = f"{raw_act}：{note}"

            now = get_tw_time()
            
            # 防重複刷卡 (2分鐘)
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.warning(f"⏳ 請勿重複刷卡 ({pid})")
                st.session_state.input_pid = "" # 清空
                return

            df_m = load_data_from_sheet("members")
            df_l = load_data_from_sheet("logs")
            
            if df_m.empty: st.error("❌ 無法讀取名單"); return
            
            person = df_m[df_m['身分證字號'] == pid]
            if not person.empty:
                row = person.iloc[0]
                name = row['姓名']
                if check_is_fully_retired(row):
                    st.error(f"❌ {name} 已顯示為「已退出」，無法打卡。")
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
                    st.success(f"✅ {name} {action} 成功！ ({now.strftime('%H:%M')})")
            else:
                st.error("❌ 查無此人，請確認身分證字號。")
            
            # 5. 打卡完清空身分證欄位
            st.session_state.input_pid = ""

        # 身分證輸入框 (綁定 on_change)
        st.text_input("請輸入身分證 (Enter 送出)", key="input_pid", on_change=process_scan)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # 6. 補登作業 (CSS 已修復字體顏色)
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
                else:
                    names = st.multiselect("選擇多位志工", name_list)
                
                if st.form_submit_button("確認補登"):
                    logs = load_data_from_sheet("logs")
                    new_rows = []
                    for n in names:
                        row = df_m[df_m['姓名'] == n].iloc[0]
                        new_rows.append({
                            '姓名': n, '身分證字號': row['身分證字號'], '電話': row['電話'], 
                            '志工分類': row['志工分類'], '動作': d_action, 
                            '時間': d_time.strftime("%H:%M:%S"), '日期': d_date.strftime("%Y-%m-%d"), 
                            '活動內容': d_act
                        })
                    save_data_to_sheet(pd.concat([logs, pd.DataFrame(new_rows)], ignore_index=True), "logs")
                    st.success(f"已補登 {len(names)} 筆資料")

    with tab3:
        logs = load_data_from_sheet("logs")
        if not logs.empty:
            edited = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存修改"):
                save_data_to_sheet(edited, "logs")
                st.success("已更新")

# =========================================================
# 6) Page: Members (名冊 - 修正加入日期欄位)
# =========================================================
elif st.session_state.page == 'members':
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
            st.write("**2. 志工分類與加入日期 (請勾選)**")
            
            # 2. 這裡改成條列式，確保日期欄位看得到
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.write("###### 選擇類別")
                is_x = st.checkbox("祥和志工")
                is_t = st.checkbox("據點週二志工")
                is_w = st.checkbox("據點週三志工")
                is_e = st.checkbox("環保志工")
            
            with col_right:
                st.write("###### 填寫加入日期 (YYYY-MM-DD)")
                # 只有勾選時才需要填，但為了版面整齊，我們都顯示，沒勾選的存空值
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
        # 1. 檢視模式按鈕化 (用 Radio 但樣式像按鈕)
        mode = st.radio("名單檢視", ["🟢 在職志工", "📋 所有名單 (含退出)"], horizontal=True)
        
        df['狀態'] = df.apply(lambda r: '已退出' if check_is_fully_retired(r) else '在職', axis=1)
        df['年齡'] = df['生日'].apply(calculate_age)
        
        show_df = df[df['狀態'] == '在職'] if "在職" in mode else df
        
        cols = ['狀態', '姓名', '年齡', '電話', '地址', '志工分類'] + [c for c in df.columns if '日期' in c] + ['備註']
        cols = [c for c in cols if c in df.columns]
        st.data_editor(show_df[cols], use_container_width=True, num_rows="dynamic", key="m_edit")

# =========================================================
# 7) Page: Report (報表儀表板化 - 無圖表)
# =========================================================
elif st.session_state.page == 'report':
    st.markdown("## 📊 數據分析 (儀表板)")
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    # 篩選區塊 (Dashboard Filter)
    st.markdown('<div style="background:white; padding:20px; border-radius:15px; border:1px solid #ddd; margin-bottom:20px;">', unsafe_allow_html=True)
    c_date, c_type = st.columns([1, 1])
    with c_date:
        d_range = st.date_input("📅 選擇日期區間", value=(date(date.today().year, 1, 1), date.today()))
    
    with c_type:
        report_mode = st.radio("分析視角", ["依活動查詢", "依志工查詢"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 資料處理
    if logs.empty:
        st.info("無打卡資料")
    else:
        logs['dt'] = pd.to_datetime(logs['日期'] + ' ' + logs['時間'], errors='coerce')
        logs = logs.dropna(subset=['dt'])
        
        # 日期篩選
        if isinstance(d_range, tuple) and len(d_range) == 2:
            start_d, end_d = d_range
            mask = (logs['dt'].dt.date >= start_d) & (logs['dt'].dt.date <= end_d)
            filtered_logs = logs[mask].copy()
        else:
            filtered_logs = logs.copy() # 預設全選或只選一天
            
        if filtered_logs.empty:
            st.warning("此區間無資料")
        else:
            # === 依活動查詢 ===
            if report_mode == "依活動查詢":
                all_acts = filtered_logs['活動內容'].unique().tolist()
                target_act = st.selectbox("選擇活動", ["全部"] + all_acts)
                
                if target_act != "全部":
                    view_df = filtered_logs[filtered_logs['活動內容'] == target_act]
                else:
                    view_df = filtered_logs
                
                # 計算統計
                total_sess, total_sec = calculate_stats(view_df)
                h_str, _ = format_seconds(total_sec)
                
                # 顯示儀表板數字
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">期間總人次</div><div class="metric-value">{total_sess}</div></div>""", unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">期間總時數</div><div class="metric-value">{h_str}</div></div>""", unsafe_allow_html=True)
                with m3:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">參與人數</div><div class="metric-value">{view_df['姓名'].nunique()}</div></div>""", unsafe_allow_html=True)
                
                st.markdown("### 📋 詳細執勤名單")
                # 依人名加總
                summary = []
                for name, g in view_df.groupby('姓名'):
                    c, s = calculate_stats(g)
                    h_fmt, _ = format_seconds(s)
                    summary.append({'姓名': name, '執勤次數': c, '總時數': h_fmt, '時數(小數)': round(s/3600, 2)})
                
                st.dataframe(pd.DataFrame(summary).sort_values('時數(小數)', ascending=False), use_container_width=True)

            # === 依志工查詢 ===
            else:
                all_names = filtered_logs['姓名'].unique().tolist()
                target_name = st.selectbox("選擇志工", all_names)
                
                view_df = filtered_logs[filtered_logs['姓名'] == target_name]
                
                # 計算統計
                total_sess, total_sec = calculate_stats(view_df)
                h_str, _ = format_seconds(total_sec)
                
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">{target_name} - 執勤次數</div><div class="metric-value">{total_sess}</div></div>""", unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">{target_name} - 累積時數</div><div class="metric-value">{h_str}</div></div>""", unsafe_allow_html=True)
                
                st.markdown("### 📋 執勤紀錄明細")
                display_cols = ['日期', '時間', '動作', '活動內容']
                st.dataframe(view_df[display_cols].sort_values(['日期', '時間'], ascending=False), use_container_width=True)
