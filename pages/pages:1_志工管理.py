import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
import time
import plotly.express as px

# --- 1. 🎨 薰衣草紫主題 (V4.1 輸入框顯色修復版) ---
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide")

# 定義顏色
THEME_COLOR = "#673AB7"
BG_COLOR = "#F3E5F5"
TEXT_COLOR = "#4527A0"

st.markdown(f"""
    <style>
    /* 1. 全域字體強制深色 */
    html, body, [class*="css"] {{
        color: #212121 !important;
        font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif;
    }}
    
    /* 2. 背景設定 */
    .stApp {{
        background-color: {BG_COLOR};
        background-image: linear-gradient(180deg, #F3E5F5 0%, #E1BEE7 100%);
    }}
    
    /* 3. 🔥【關鍵修復】輸入框與標籤強制顯色 */
    /* 輸入框上方的文字標籤 (Label) */
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label {{
        color: {TEXT_COLOR} !important;
        font-weight: bold !important;
        font-size: 1rem !important;
    }}
    
    /* 輸入框本體 (Input Box) */
    .stTextInput input {{
        color: #000000 !important;        /* 輸入的字變黑色 */
        background-color: #FFFFFF !important; /* 背景變白色 */
        border: 1px solid #B39DDB !important; /* 加個紫框比較明顯 */
    }}
    
    /* 下拉選單本體 */
    div[data-baseweb="select"] > div {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #B39DDB !important;
    }}
    
    /* 4. 標題優化 */
    h1, h2, h3 {{
        color: {TEXT_COLOR} !important;
        font-weight: 800 !important;
    }}

    /* 5. 按鈕樣式 (懸浮膠囊) */
    .stButton>button {{
        background: linear-gradient(90deg, #7E57C2 0%, #673AB7 100%);
        color: white !important; 
        border-radius: 50px;
        border: none;
        padding: 10px 24px;
        font-size: 16px !important;
        font-weight: bold !important;
        white-space: nowrap !important;
        box-shadow: 0 4px 10px rgba(103, 58, 183, 0.3);
        transition: all 0.3s ease;
        min-width: 120px;
        margin: 5px;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(103, 58, 183, 0.5);
    }}
    
    /* 6. 首頁大卡片 */
    .big-card-text {{
        font-size: 1.3rem;
        color: {TEXT_COLOR};
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }}
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

# --- 3. 🧮 邏輯運算 ---
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
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and row[join_col]: 
            if not (exit_col in row and row[exit_col]): is_active = True
    return not is_active

# --- 4. 🖥️ UI 導航 ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page != 'home':
    with st.container():
        c1, c2, c3, spacer = st.columns([1, 1, 1, 4])
        with c1:
            if st.button("🏠 回首頁"): st.session_state.page = 'home'; st.rerun()
        with c2:
            if st.button("⏰ 智能打卡"): st.session_state.page = 'checkin'; st.rerun()
        with c3:
            if st.button("📊 數據分析"): st.session_state.page = 'report'; st.rerun()
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# === 🏠 首頁 ===
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; margin-top: 20px;'>💜 福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666; margin-bottom: 50px;'>請點擊下方卡片進入功能</p>", unsafe_allow_html=True)
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="big-card-text">⏰ 智能打卡站</div>', unsafe_allow_html=True)
            if st.button("進入打卡系統", key="h1", use_container_width=True):
                st.session_state.page = 'checkin'; st.rerun()
        with c2:
            st.markdown(f'<div class="big-card-text">📋 志工名冊管理</div>', unsafe_allow_html=True)
            if st.button("管理名單", key="h2", use_container_width=True):
                st.session_state.page = 'members'; st.rerun()
        with c3:
            st.markdown(f'<div class="big-card-text">📊 數據分析</div>', unsafe_allow_html=True)
            if st.button("查看報表", key="h3", use_container_width=True):
                st.session_state.page = 'report'; st.rerun()

# === ⏰ 打卡頁 ===
elif st.session_state.page == 'checkin':
    st.markdown("## ⏰ 智能打卡站")
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    tab1, tab2 = st.tabs(["⚡️ 快速打卡區", "🛠️ 補登與維護"])
    
    with tab1:
        c_act, c_input = st.columns([1, 2])
        with c_act: act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
        
        def process_scan():
            pid = st.session_state.scan_box.strip().upper()
            if not pid: return
            now = datetime.now()
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
                        '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': act
                    }])
                    save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True), "logs")
                    st.session_state['scan_cooldowns'][pid] = now
                    st.success(f"✅ {name} {action} 成功！")
            else: st.error("❌ 查無此人")
            st.session_state.scan_box = ""

        st.text_input("請輸入身分證 (或掃描)", key="scan_box", on_change=process_scan)

    with tab2:
        st.info("補登遺漏紀錄")
        df_m = load_data_from_sheet("members")
        if not df_m.empty:
            c1, c2, c3 = st.columns(3)
            with c1: t_name = st.selectbox("志工", df_m['姓名'].tolist())
            with c2: t_date = st.date_input("日期")
            with c3: t_action = st.radio("動作", ["簽到", "簽退"], horizontal=True)
            if st.button("確認補登"):
                row = df_m[df_m['姓名'] == t_name].iloc[0]
                logs = load_data_from_sheet("logs")
                new = pd.DataFrame([{
                    '姓名': t_name, '身分證字號': row['身分證字號'], '電話': row['電話'], 
                    '志工分類': row['志工分類'], '動作': t_action, 
                    '時間': "12:00:00", '日期': t_date.strftime("%Y-%m-%d"), '活動內容': "補登"
                }])
                save_data_to_sheet(pd.concat([logs, new], ignore_index=True), "logs")
                st.success("已補登")

# === 📋 名冊頁 ===
elif st.session_state.page == 'members':
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")
    
    with st.expander("➕ 新增志工 (點擊展開)", expanded=True):
        st.write("請輸入以下資料：")
        c1, c2, c3 = st.columns(3)
        with c1: n = st.text_input("姓名")
        with c2: p = st.text_input("身分證字號")
        with c3: b = st.text_input("生日 (YYYY-MM-DD)")
        
        c4, c5 = st.columns([2, 1])
        with c4: addr = st.text_input("地址")
        with c5: ph = st.text_input("電話")
        
        cats = st.multiselect("志工分類", ALL_CATEGORIES)
        
        if st.button("新增資料"):
            if not p: st.error("身分證必填");
            elif not df.empty and p in df['身分證字號'].values: st.error("重複")
            else:
                new_data = {'姓名':n, '身分證字號':p, '生日':b, '電話':ph, '地址':addr, '志工分類':",".join(cats)}
                today_str = date.today().strftime("%Y-%m-%d")
                for cat in cats:
                    if "祥和" in cat: new_data['祥和_加入日期'] = today_str
                    if "週二" in cat: new_data['據點週二_加入日期'] = today_str
                    if "週三" in cat: new_data['據點週三_加入日期'] = today_str
                    if "環保" in cat: new_data['環保_加入日期'] = today_str
                new = pd.DataFrame([new_data])
                for c in DISPLAY_ORDER: 
                    if c not in new.columns: new[c] = ""
                save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                st.success("新增成功"); time.sleep(1); st.rerun()

    if not df.empty:
        st.write("---")
        df['年齡'] = df['生日'].apply(calculate_age)
        special_cols = ['姓名', '年齡', '電話', '地址', '志工分類']
        date_cols = [c for c in df.columns if '日期' in c]
        other_cols = [c for c in df.columns if c not in special_cols and c not in date_cols and c != '年齡']
        final_cols = special_cols + date_cols + other_cols
        final_cols = [c for c in final_cols if c in df.columns]
        st.data_editor(df[final_cols], use_container_width=True, num_rows="dynamic", key="member_editor")

# === 📊 報表頁 ===
elif st.session_state.page == 'report':
    st.markdown("## 📊 數據分析")
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    st.markdown("### 📝 近期出勤紀錄")
    if logs.empty: st.info("尚無出勤資料")
    else: st.dataframe(logs, use_container_width=True, height=300)
        
    st.divider()
    
    st.markdown("### 🎂 志工年齡結構")
    if members.empty: st.info("尚無志工資料")
    else:
        members['Calculated_Age'] = members['生日'].apply(calculate_age)
        valid_ages = members[members['Calculated_Age'] > 0]
        
        if valid_ages.empty:
            st.warning("⚠️ 無有效生日資料，無法計算年齡。")
        else:
            cat_stats = []
            for cat in ALL_CATEGORIES:
                subset = valid_ages[valid_ages['志工分類'].astype(str).str.contains(cat, na=False)]
                if not subset.empty:
                    cat_stats.append({'志工類別': cat, '平均年齡': round(subset['Calculated_Age'].mean(), 1), '人數': len(subset)})
            
            if cat_stats:
                df_stats = pd.DataFrame(cat_stats)
                cols = st.columns(len(cat_stats))
                for idx, row in df_stats.iterrows():
                    with cols[idx]:
                        st.metric(label=f"{row['志工類別']}", value=f"{row['平均年齡']} 歲", delta=f"{row['人數']} 人")

            st.write("")
            
            bins = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            labels = ['20歲↓', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90歲↑']
            valid_ages['Age_Group'] = pd.cut(valid_ages['Calculated_Age'], bins=bins, labels=labels, right=False)
            age_counts = valid_ages['Age_Group'].value_counts().sort_index().reset_index()
            age_counts.columns = ['年齡區間', '人數']
            
            fig = px.bar(
                age_counts, x='年齡區間', y='人數', text='人數', 
                color='人數', color_continuous_scale=['#D1C4E9', '#673AB7']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_color=THEME_COLOR, xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False, visible=False),
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False
            )
            fig.update_traces(textposition='outside', marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
