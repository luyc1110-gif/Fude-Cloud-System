import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
import time
import plotly.express as px

# --- 1. 🎨 薰衣草紫主題 (V3.0 美化修復版) ---
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide")

# 定義顏色變數 (加強對比度)
THEME_COLOR = "#673AB7"  # 深紫色 (按鈕背景)
BUTTON_TEXT_COLOR = "#FFFFFF" # 按鈕文字 (純白)
BG_COLOR = "#F3E5F5"     # 淺紫背景
TEXT_COLOR = "#311B92"   # 標題深藍紫
BODY_TEXT = "#000000"    # 內文全黑 (最清晰)

st.markdown(f"""
    <style>
    /* 全域字體與顏色 */
    html, body, [class*="css"] {{
        color: {BODY_TEXT};
        font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif;
    }}
    
    .stApp {{
        background-color: {BG_COLOR};
        background-image: linear-gradient(180deg, #F3E5F5 0%, #E1BEE7 100%);
    }}
    
    /* 卡片優化 */
    .stDataFrame, .stTab, div[data-testid="stVerticalBlock"] > div {{
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #E1BEE7;
    }}

    /* 標題優化 */
    h1, h2, h3 {{
        color: {TEXT_COLOR} !important;
        font-weight: 900 !important;
        letter-spacing: 1px;
    }}

    /* 🎯 按鈕終極美化 (解決斷行與配色問題) */
    .stButton>button {{
        background: linear-gradient(135deg, {THEME_COLOR} 0%, #512DA8 100%);
        color: {BUTTON_TEXT_COLOR} !important; 
        border-radius: 50px; /* 更圓潤 */
        border: none;
        padding: 12px 28px; /* 增加內距 */
        font-size: 16px !important;
        font-weight: bold !important;
        white-space: nowrap !important; /* 🔥 關鍵：禁止文字斷行 */
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        min-width: 140px; /* 保證最小寬度 */
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.25);
        background: linear-gradient(135deg, #7E57C2 0%, #673AB7 100%);
    }}
    
    /* 首頁大卡片文字 */
    .big-card-text {{
        font-size: 1.3rem;
        color: {TEXT_COLOR};
        text-align: center;
        font-weight: bold;
        margin-bottom: 15px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 🔗 Google Sheets 連線 ---
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']

# 🔥 這裡定義欄位順序 (您要的地址和日期都在這)
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
        df = df.astype(str) # 全部轉字串防呆
        
        # 補齊所有定義好的欄位，確保不缺漏
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

# 導航按鈕列 (使用 columns 讓按鈕排排站，不擁擠)
if st.session_state.page != 'home':
    c1, c2, c3, c4 = st.columns([1, 1, 1, 5]) # 調整比例讓按鈕靠左
    with c1:
        if st.button("🏠 回首頁"): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("⏰ 智能打卡"): st.session_state.page = 'checkin'; st.rerun()
    with c3:
        if st.button("📊 數據報表"): st.session_state.page = 'report'; st.rerun()
    st.write("") # 空一行

# === 🏠 首頁 ===
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; margin-bottom: 10px;'>💜 福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666; margin-bottom: 40px;'>請點擊下方卡片進入功能</p>", unsafe_allow_html=True)
    
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
            st.markdown(f'<div class="big-card-text">📊 數據與年齡分析</div>', unsafe_allow_html=True)
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
    
    with st.expander("➕ 新增志工", expanded=False):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("姓名")
        p = c2.text_input("身分證字號")
        b = c3.text_input("生日 (YYYY-MM-DD)")
        c4, c5 = st.columns([2, 1])
        addr = c4.text_input("地址")
        ph = c5.text_input("電話")
        cats = st.multiselect("分類", ALL_CATEGORIES)
        
        if st.button("新增資料"):
            if not p: st.error("身分證必填");
            elif not df.empty and p in df['身分證字號'].values: st.error("重複")
            else:
                new_data = {'姓名':n, '身分證字號':p, '生日':b, '電話':ph, '地址':addr, '志工分類':",".join(cats)}
                # 自動填入加入日期為今天 (預設)
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
        # 🔥 這裡強制欄位順序，並確保地址和日期出現
        df['年齡'] = df['生日'].apply(calculate_age)
        
        # 顯示欄位：姓名, 年齡, 電話, 地址, 分類, ...然後是各個日期
        special_cols = ['姓名', '年齡', '電話', '地址', '志工分類']
        date_cols = [c for c in df.columns if '日期' in c]
        other_cols = [c for c in df.columns if c not in special_cols and c not in date_cols and c != '年齡']
        
        final_cols = special_cols + date_cols + other_cols
        # 確保所有欄位都在 df 裡 (防呆)
        final_cols = [c for c in final_cols if c in df.columns]
        
        st.data_editor(df[final_cols], use_container_width=True, num_rows="dynamic", key="member_editor")

# === 📊 報表頁 ===
elif st.session_state.page == 'report':
    st.markdown("## 📊 數據與年齡分析")
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    tab_work, tab_age = st.tabs(["📈 出勤統計", "🎂 各類志工平均年齡"])
    
    with tab_work:
        if logs.empty: st.info("尚無出勤資料")
        else: st.dataframe(logs, use_container_width=True)
            
    with tab_age:
        if members.empty: st.info("尚無志工資料")
        else:
            members['Calculated_Age'] = members['生日'].apply(calculate_age)
            valid_ages = members[members['Calculated_Age'] > 0]
            
            if valid_ages.empty:
                st.warning("⚠️ 無有效生日資料，無法計算年齡。")
            else:
                st.markdown("### 📊 各類別平均年齡統計")
                
                # 🔥 計算各類別平均年齡 (拆解多重身分)
                cat_stats = []
                for cat in ALL_CATEGORIES:
                    # 篩選出包含該類別的志工
                    subset = valid_ages[valid_ages['志工分類'].astype(str).str.contains(cat, na=False)]
                    if not subset.empty:
                        avg = subset['Calculated_Age'].mean()
                        count = len(subset)
                        cat_stats.append({'志工類別': cat, '平均年齡': round(avg, 1), '人數': count})
                
                if cat_stats:
                    df_stats = pd.DataFrame(cat_stats)
                    
                    # 顯示漂亮的 Metric 卡片
                    cols = st.columns(len(cat_stats))
                    for idx, row in df_stats.iterrows():
                        with cols[idx % 3]: # 每行最多3個，超過換行
                             st.metric(label=f"{row['志工類別']} (共{row['人數']}人)", value=f"{row['平均年齡']} 歲")
                    
                    st.divider()
                    
                    # 畫長條圖比較
                    fig = px.bar(df_stats, x='志工類別', y='平均年齡', text='平均年齡', 
                                 title="各隊志工平均年齡比較", color='志工類別',
                                 color_discrete_sequence=px.colors.qualitative.Bold)
                    fig.update_layout(yaxis_title="歲數", plot_bgcolor="white")
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.info("目前沒有志工被歸類在已知類別中。")

                st.divider()
                st.markdown("### 全體年齡分佈")
                # 原本的總表保留
                bins = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                labels = ['20歲以下', '20-30歲', '30-40歲', '40-50歲', '50-60歲', '60-70歲', '70-80歲', '80-90歲', '90歲以上']
                valid_ages['Age_Group'] = pd.cut(valid_ages['Calculated_Age'], bins=bins, labels=labels, right=False)
                age_counts = valid_ages['Age_Group'].value_counts().sort_index().reset_index()
                age_counts.columns = ['年齡區間', '人數']
                
                fig2 = px.bar(age_counts, x='年齡區間', y='人數', text='人數', color_discrete_sequence=['#7E57C2'])
                fig2.update_layout(plot_bgcolor="white")
                st.plotly_chart(fig2, use_container_width=True)
