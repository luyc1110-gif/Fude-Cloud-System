import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import plotly.express as px
import os
import base64

# --- 1. 🎨 視覺美學設定 (V7.3 圖片整形修復版) ---
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide")

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A148C"
ACCENT = "#7B1FA2"
BG_MAIN = "#F3F4F6"

# 讀取圖片並轉為 Base64 (解決圖片無法用 HTML 控制大小的問題)
def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

st.markdown(f"""
    <style>
    html, body, [class*="css"], .stMarkdown, div, p {{
        color: #212121 !important;
        font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif;
    }}
    .stApp {{ background-color: {BG_MAIN}; }}
    
    /* 膠囊按鈕優化 */
    .stButton>button {{
        width: 100%;
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
        color: white !important; /* 強制白字 */
        border: none !important;
        border-radius: 50px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 10px 0;
        box-shadow: 0 4px 10px rgba(74, 20, 140, 0.3);
        margin-top: 10px; /* 與上方圖片保持距離 */
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(74, 20, 140, 0.4);
        color: white !important;
    }}
    
    /* 輸入框優化 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #9FA8DA !important;
        border-radius: 8px;
    }}
    .stTextInput label, .stSelectbox label, .stDateInput label {{
        color: {PRIMARY} !important;
        font-weight: bold;
    }}
    
    /* 統計小卡 */
    .dash-card {{
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid {ACCENT};
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}
    .dash-label {{ font-size: 1rem; color: #666; font-weight: bold; }}
    .dash-value {{ font-size: 1.8rem; color: {PRIMARY}; font-weight: 900; margin: 5px 0; }}
    .dash-sub {{ font-size: 0.9rem; color: #888; }}
    
    /* 隱藏選單 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 2. 🔗 Google Sheets 連線 ---
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']
DISPLAY_ORDER = [
    '姓名', '身分證字號', '性別', '電話', '志工分類', '生日', '地址', '備註',
    '祥和_加入日期', '祥和_退出日期', 
    '據點週二_加入日期', '據點週二_退出日期',
    '據點週三_加入日期', '據點週三_退出日期', 
    '環保_加入日期', '環保_退出日期'
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
    except Exception as e:
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        load_data_from_sheet.clear()
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# --- 3. 🧮 邏輯運算 ---
def get_tw_time():
    return datetime.now(TW_TZ)

def calculate_age(birthday_str):
    if not birthday_str or len(birthday_str) < 4: return 0
    try:
        b_date = None
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
            try:
                b_date = datetime.strptime(birthday_str, fmt)
                break
            except: continue
        if b_date:
            today = date.today()
            age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
            return age
        else: return 0
    except: return 0

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any_role = False
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and str(row[join_col]).strip() != "":
            has_any_role = True
            if not (exit_col in row and str(row[exit_col]).strip() != ""):
                is_active = True
    if not has_any_role: return False 
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
            else:
                i += 1
    return total_seconds

# --- 4. 🖥️ UI 導航 ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page != 'home':
    with st.container():
        c1, c2, c3, spacer = st.columns([1, 1, 1, 4])
        with c1:
            if st.button("🏠 首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
        with c2:
            if st.button("⏰ 打卡", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
        with c3:
            if st.button("📊 報表", use_container_width=True): st.session_state.page = 'report'; st.rerun()
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# === 🏠 首頁 (完美圖片版) ===
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; color: {PRIMARY}; margin-bottom: 30px;'>💜 福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    # 版面：置中 (中間三個各佔 2)
    col_spacer_l, c1, c2, c3, col_spacer_r = st.columns([1, 2, 2, 2, 1])
    
    # 🔥 1. 智能打卡卡片 (強制控制圖片大小)
    with c1:
        # 使用 Columns 技巧來置中圖片
        sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1]) # 中間佔 50%
        with sub_c2:
            if os.path.exists("icon_checkin.png"):
                st.image("icon_checkin.png", use_container_width=True) # 因為外層已經限制寬度，這裡填滿即可
            else:
                st.markdown("<div style='text-align:center; font-size:60px;'>⏰</div>", unsafe_allow_html=True)
        
        if st.button("進入打卡", key="home_btn1"):
            st.session_state.page = 'checkin'; st.rerun()

    # 🔥 2. 志工名冊卡片
    with c2:
        sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1])
        with sub_c2:
            if os.path.exists("icon_members.png"):
                st.image("icon_members.png", use_container_width=True)
            else:
                st.markdown("<div style='text-align:center; font-size:60px;'>📋</div>", unsafe_allow_html=True)
        
        if st.button("名冊管理", key="home_btn2"):
            st.session_state.page = 'members'; st.rerun()

    # 🔥 3. 數據分析卡片
    with c3:
        sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1])
        with sub_c2:
            if os.path.exists("icon_report.png"):
                st.image("icon_report.png", use_container_width=True)
            else:
                st.markdown("<div style='text-align:center; font-size:60px;'>📊</div>", unsafe_allow_html=True)
        
        if st.button("數據分析", key="home_btn3"):
            st.session_state.page = 'report'; st.rerun()
    
    st.markdown("---")
    st.markdown(f"### 📊 {datetime.now().year} 年度即時概況")
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    this_year = datetime.now().year
    total_sec = calculate_hours_year(logs, this_year)
    total_hours = int(total_sec // 3600)
    total_mins = int((total_sec % 3600) // 60)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(81, 45, 168, 0.3);">
        <div style="font-size: 1.2rem; opacity: 0.9;">📅 {this_year} 年度 - 全體志工總服務時數</div>
        <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0;">{total_hours} <span style="font-size: 1.5rem;">小時</span> {total_mins} <span style="font-size: 1.5rem;">分</span></div>
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
                st.markdown(f"""
                <div class="dash-card">
                    <div class="dash-label">{cat.replace('志工','')}</div>
                    <div class="dash-value">{count} <span style="font-size:1rem;color:#888;">人</span></div>
                    <div class="dash-sub">平均 {avg_age} 歲</div>
                </div>
                """, unsafe_allow_html=True)

# === ⏰ 打卡頁 ===
elif st.session_state.page == 'checkin':
    st.markdown("## ⏰ 智能打卡站")
    tw_now = get_tw_time()
    st.caption(f"📅 台灣時間：{tw_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])
    
    with tab1:
        c_act, c_spacer = st.columns([1, 2])
        with c_act: 
            raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
            final_act = raw_act
            if raw_act in ["專案活動", "教育訓練"]:
                note = st.text_input("📝 請輸入名稱", placeholder="例：大掃除")
                if note: final_act = f"{raw_act}：{note}"

        def process_scan():
            pid = st.session_state.scan_box.strip().upper()
            if not pid: return
            now = get_tw_time()
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.warning(f"⏳ 請勿重複刷卡 ({pid})"); st.session_state.scan_box = ""; return
            
            df_m = load_data_from_sheet("members")
            df_l = load_data_from_sheet("logs")
            if df_m.empty: st.error("❌ 無法讀取名單"); return
            
            person = df_m[df_m['身分證字號'] == pid]
            if not person.empty:
                row = person.iloc[0]
                name = row['姓名']
                if check_is_fully_retired(row): st.error(f"❌ {name} 已退出")
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
            else: st.error("❌ 查無此人")
            st.session_state.scan_box = ""

        st.text_input("請輸入身分證 (或掃描)", key="scan_box", on_change=process_scan)

    with tab2:
        entry_mode = st.radio("模式", ["單筆補登", "整批補登"], horizontal=True)
        df_m = load_data_from_sheet("members")
        if not df_m.empty:
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)]
            name_list = active_m['姓名'].tolist()
            with st.form("manual"):
                c1, c2, c3, c4 = st.columns(4)
                d_date = c1.date_input("日期")
                d_time = c2.time_input("時間", value=get_tw_time().time())
                d_action = c3.selectbox("動作", ["簽到", "簽退"])
                d_act = c4.selectbox("活動", DEFAULT_ACTIVITIES)
                
                if entry_mode == "單筆補登":
                    names = [st.selectbox("志工", name_list)]
                else:
                    names = st.multiselect("選擇多位", name_list)
                
                if st.form_submit_button("補登"):
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
                    st.success("已補登")

    with tab3:
        logs = load_data_from_sheet("logs")
        if not logs.empty:
            edited = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存"):
                save_data_to_sheet(edited, "logs")
                st.success("已更新")

# === 📋 名冊頁 ===
elif st.session_state.page == 'members':
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")
    
    with st.expander("➕ 新增志工", expanded=True):
        with st.form("add_m"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            b = c3.text_input("生日 (YYYY-MM-DD)")
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            ph = c5.text_input("電話")
            
            st.markdown("---")
            st.write("**志工分類與加入日期**")
            cats = []
            col_d1, col_d2 = st.columns(2)
            
            is_x = col_d1.checkbox("祥和")
            d_x = col_d2.text_input("祥和加入日", value=str(date.today()) if is_x else "")
            is_t = col_d1.checkbox("週二據點")
            d_t = col_d2.text_input("週二加入日", value=str(date.today()) if is_t else "")
            is_w = col_d1.checkbox("週三據點")
            d_w = col_d2.text_input("週三加入日", value=str(date.today()) if is_w else "")
            is_e = col_d1.checkbox("環保")
            d_e = col_d2.text_input("環保加入日", value=str(date.today()) if is_e else "")

            if st.form_submit_button("新增"):
                if not p: st.error("身分證必填")
                elif not df.empty and p in df['身分證字號'].values: st.error("重複")
                else:
                    if is_x: cats.append("祥和志工")
                    if is_t: cats.append("關懷據點週二志工")
                    if is_w: cats.append("關懷據點週三志工")
                    if is_e: cats.append("環保志工")
                    new_data = {
                        '姓名':n, '身分證字號':p, '生日':b, '電話':ph, '地址':addr, 
                        '志工分類':",".join(cats),
                        '祥和_加入日期': d_x if is_x else "",
                        '據點週二_加入日期': d_t if is_t else "",
                        '據點週三_加入日期': d_w if is_w else "",
                        '環保_加入日期': d_e if is_e else ""
                    }
                    new = pd.DataFrame([new_data])
                    for c in DISPLAY_ORDER: 
                        if c not in new.columns: new[c] = ""
                    save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                    st.success("新增成功"); time.sleep(1); st.rerun()

    if not df.empty:
        st.write("---")
        mode = st.radio("檢視模式", ["🟢 在職", "📋 全部"], horizontal=True)
        df['狀態'] = df.apply(lambda r: '已退出' if check_is_fully_retired(r) else '在職', axis=1)
        df['年齡'] = df['生日'].apply(calculate_age)
        
        show_df = df[df['狀態'] == '在職'] if mode == "🟢 在職" else df
        
        cols = ['狀態', '姓名', '年齡', '電話', '地址', '志工分類'] + [c for c in df.columns if '日期' in c] + ['備註']
        cols = [c for c in cols if c in df.columns]
        st.data_editor(show_df[cols], use_container_width=True, num_rows="dynamic", key="m_edit")

# === 📊 報表頁 ===
elif st.session_state.page == 'report':
    st.markdown("## 📊 數據分析")
    logs = load_data_from_sheet("logs")
    
    st.markdown("### 📝 近期出勤")
    if not logs.empty: st.dataframe(logs, use_container_width=True, height=400)
    else: st.info("無資料")
