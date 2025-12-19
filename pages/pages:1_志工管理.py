import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
import time
import plotly.express as px  # 引入繪圖庫

# --- 1. 🎨 薰衣草紫主題與 CSS 美化 ---
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide")

# 定義薰衣草紫主色調
THEME_COLOR = "#8E7CC3"  # 較深的薰衣草紫 (按鈕/標題)
BG_COLOR = "#F3E5F5"     # 極淺的紫 (背景)
CARD_COLOR = "#FFFFFF"   # 卡片白

st.markdown(f"""
    <style>
    /* 全站背景設定 */
    .stApp {{
        background-color: {BG_COLOR};
        background-image: linear-gradient(180deg, #F3E5F5 0%, #EDE7F6 100%);
    }}
    
    /* 隱藏預設的左側 Sidebar (Streamlit 內建) */
    [data-testid="stSidebar"] {{
        display: none;
    }}
    
    /* 卡片式容器風格 */
    .css-1r6slb0, .stDataFrame, .stTab, div[data-testid="stVerticalBlock"] > div {{
        background-color: {CARD_COLOR};
        border-radius: 20px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(142, 124, 195, 0.15); /* 紫色陰影 */
    }}

    /* 按鈕美化：薰衣草紫按鈕 */
    .stButton>button {{
        background-color: {THEME_COLOR};
        color: white;
        border-radius: 30px;
        border: none;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .stButton>button:hover {{
        background-color: #7B68EE; /* 深一點的紫 */
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }}

    /* 首頁大卡片按鈕特製 */
    .big-card-btn > button {{
        height: 150px;
        width: 100%;
        font-size: 1.5rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #B39DDB 0%, #7E57C2 100%);
    }}

    /* 標題與文字 */
    h1, h2, h3 {{
        color: #512DA8; /* 深紫文字 */
        font-weight: 800 !important;
    }}
    
    /* 成功與錯誤訊息 */
    .stSuccess {{ background-color: #D1C4E9; color: #311B92; }}
    .stError {{ background-color: #FFCDD2; color: #B71C1C; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 🔗 Google Sheets 連線設定 ---
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']
DISPLAY_ORDER = [
    '姓名', '身分證字號', '性別', '電話', '志工分類', '生日', '地址', '備註',
    '祥和_加入日期', '祥和_退出日期', '據點週二_加入日期', '據點週二_退出日期',
    '據點週三_加入日期', '據點週三_退出日期', '環保_加入日期', '環保_退出日期'
]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

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
        st.error(f"資料讀取錯誤 ({sheet_name})：{e}")
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# --- 3. 🧮 邏輯運算 (含年齡計算) ---
def calculate_age(birthday_str):
    # 嘗試解析多種生日格式
    if not birthday_str or len(birthday_str) < 4: return "未填寫"
    try:
        # 處理常見格式 YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD
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
        else:
            return "格式錯誤"
    except:
        return "格式錯誤"

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and row[join_col]: 
            if not (exit_col in row and row[exit_col]): is_active = True
    return not is_active

# --- 4. 🖥️ UI 導航控制 (核心改造) ---
# 初始化頁面狀態
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# 頂部導航列 (除了首頁外都顯示)
if st.session_state.page != 'home':
    c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
    with c1:
        if st.button("🏠 回首頁"): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("⏰ 智能打卡"): st.session_state.page = 'checkin'; st.rerun()
    with c3:
        if st.button("📊 數據報表"): st.session_state.page = 'report'; st.rerun()
    st.divider()

# === 🏠 首頁 (卡片式選單) ===
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>💜 福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>請點擊下方卡片進入功能</p>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="big-card-btn">', unsafe_allow_html=True)
        if st.button("⏰\n\n智能打卡站\n(手機/電腦)", key="home_btn_1"):
            st.session_state.page = 'checkin'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="big-card-btn">', unsafe_allow_html=True)
        if st.button("📋\n\n志工名冊管理\n(新增/修改)", key="home_btn_2"):
            st.session_state.page = 'members'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="big-card-btn">', unsafe_allow_html=True)
        if st.button("📊\n\n數據與年齡報表\n(統計分析)", key="home_btn_3"):
            st.session_state.page = 'report'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# === ⏰ 智能打卡頁面 ===
elif st.session_state.page == 'checkin':
    st.title("⏰ 智能打卡站")
    
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    tab1, tab2 = st.tabs(["⚡️ 快速打卡區", "🛠️ 補登與維護"])
    
    with tab1:
        c_act, c_input = st.columns([1, 2])
        with c_act:
            act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
        
        def process_scan():
            pid = st.session_state.scan_box.strip().upper()
            if not pid: return
            
            now = datetime.now()
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.warning(f"⏳ 兩分鐘內請勿重複刷卡 ({pid})")
                st.session_state.scan_box = ""; return

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
                        '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': act
                    }])
                    save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True), "logs")
                    st.session_state['scan_cooldowns'][pid] = now
                    st.success(f"✅ {name} {action} 成功！")
            else:
                st.error("❌ 查無此人")
            st.session_state.scan_box = ""

        st.text_input("請輸入身分證 (或掃描)", key="scan_box", on_change=process_scan)

    with tab2:
        st.info("手動補登遺漏紀錄")
        df_m = load_data_from_sheet("members")
        if not df_m.empty:
            c1, c2, c3 = st.columns(3)
            with c1: t_name = st.selectbox("志工", df_m['姓名'].tolist())
            with c2: t_date = st.date_input("日期")
            with c3: t_action = st.radio("動作", ["簽到", "簽退"], horizontal=True)
            
            if st.button("補登"):
                row = df_m[df_m['姓名'] == t_name].iloc[0]
                logs = load_data_from_sheet("logs")
                new = pd.DataFrame([{
                    '姓名': t_name, '身分證字號': row['身分證字號'], '電話': row['電話'], 
                    '志工分類': row['志工分類'], '動作': t_action, 
                    '時間': "12:00:00", '日期': t_date.strftime("%Y-%m-%d"), '活動內容': "補登"
                }])
                save_data_to_sheet(pd.concat([logs, new], ignore_index=True), "logs")
                st.success("已補登")

# === 📋 志工名單頁面 ===
elif st.session_state.page == 'members':
    st.title("📋 志工名冊管理")
    
    # 回首頁按鈕已經在最上方了，這裡專注內容
    df = load_data_from_sheet("members")
    
    with st.expander("➕ 新增志工 (展開)", expanded=False):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("姓名")
        p = c2.text_input("身分證字號")
        b = c3.text_input("生日 (YYYY-MM-DD)", placeholder="例：1960-01-01")
        cats = st.multiselect("分類", ALL_CATEGORIES)
        
        if st.button("新增"):
            if not p: st.error("身分證必填");
            elif not df.empty and p in df['身分證字號'].values: st.error("重複")
            else:
                new = pd.DataFrame([{'姓名':n, '身分證字號':p, '生日':b, '志工分類':",".join(cats)}])
                for c in DISPLAY_ORDER: 
                    if c not in new.columns: new[c] = ""
                save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                st.success("新增成功")
                time.sleep(1); st.rerun()

    if not df.empty:
        # 計算年齡預覽
        df['年齡'] = df['生日'].apply(calculate_age)
        # 調整顯示順序，把年齡放在前面一點
        cols = ['姓名', '年齡', '生日', '電話', '志工分類'] + [c for c in df.columns if c not in ['姓名', '年齡', '生日', '電話', '志工分類']]
        st.data_editor(df[cols], use_container_width=True, num_rows="dynamic", key="member_editor")
        if st.button("💾 儲存名單"):
            # 注意：這裡僅示範，完整版需處理欄位對應
            st.warning("請直接在 Google Sheets 修改較為安全，或使用新增功能。")

# === 📊 報表與年齡分析 ===
elif st.session_state.page == 'report':
    st.title("📊 數據與年齡分析")
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    tab_work, tab_age = st.tabs(["📈 出勤統計", "🎂 年齡結構分析"])
    
    with tab_work:
        if logs.empty:
            st.info("尚無出勤資料")
        else:
            st.dataframe(logs, use_container_width=True)
            
    with tab_age:
        if members.empty:
            st.info("尚無志工資料")
        else:
            # 計算年齡
            members['Calculated_Age'] = members['生日'].apply(calculate_age)
            
            # 過濾出有效年齡 (排除 '格式錯誤' 或 '未填寫')
            valid_ages = members[members['Calculated_Age'].apply(lambda x: isinstance(x, int))]
            
            if valid_ages.empty:
                st.warning("⚠️ 目前志工資料中沒有有效的「生日」資料，無法計算年齡。請至名單管理補填生日 (格式 YYYY-MM-DD)。")
            else:
                # 1. 顯示平均年齡
                avg_age = valid_ages['Calculated_Age'].mean()
                c1, c2, c3 = st.columns(3)
                c1.metric("平均年齡", f"{avg_age:.1f} 歲")
                c2.metric("最年長", f"{valid_ages['Calculated_Age'].max()} 歲")
                c3.metric("最年輕", f"{valid_ages['Calculated_Age'].min()} 歲")
                
                st.divider()
                
                # 2. 年齡分佈圖 (長條圖)
                # 建立年齡區間
                bins = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                labels = ['20歲以下', '20-30歲', '30-40歲', '40-50歲', '50-60歲', '60-70歲', '70-80歲', '80-90歲', '90歲以上']
                valid_ages['Age_Group'] = pd.cut(valid_ages['Calculated_Age'], bins=bins, labels=labels, right=False)
                
                age_counts = valid_ages['Age_Group'].value_counts().sort_index().reset_index()
                age_counts.columns = ['年齡區間', '人數']
                
                # 使用 Plotly 畫漂亮的紫色圖表
                fig = px.bar(age_counts, x='年齡區間', y='人數', title="志工年齡分佈圖", text='人數',
                             color_discrete_sequence=['#7E57C2']) # 使用薰衣草紫
                fig.update_layout(plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption("註：僅統計生日格式正確之志工資料")