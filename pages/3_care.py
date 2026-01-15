import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time
import re  # 新增：用於正則表達式提取樓層

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="關懷戶管理系統", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="expanded" 
)

# 1. 初始化登入狀態
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 2. 頁面狀態初始化
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# 3. 初始化局部解鎖狀態
if 'unlock_members' not in st.session_state: st.session_state.unlock_members = False
if 'unlock_details' not in st.session_state: st.session_state.unlock_details = False

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A4E69"   # 深藍灰
GREEN   = "#8E9775"   # 苔蘚綠
BG_MAIN = "#F8F9FA"   # 淺灰底
TEXT    = "#333333"

# =========================================================
# 1) CSS 樣式 (請直接覆蓋整段)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}

.stApp {{ background-color: {BG_MAIN} !important; }}
section[data-testid="stSidebar"] {{ background-color: {BG_MAIN}; border-right: none; }}

/* 懸浮大卡片 */
.block-container {{
    background-color: #FFFFFF; border-radius: 25px;
    padding: 3rem 3rem !important; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem; max-width: 95% !important;
}}

header[data-testid="stHeader"] {{ display: block !important; background-color: transparent !important; }}
header[data-testid="stHeader"] .decoration {{ display: none; }}

/* 側邊欄按鈕 */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important; color: #666 !important;
    border: 1px solid transparent !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important; padding: 10px 0 !important;
    font-weight: 700 !important; width: 100%; margin-bottom: 8px !important;
    transition: all 0.2s;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    color: {GREEN} !important;
}}
.nav-active {{
    background: linear-gradient(135deg, {GREEN}, #6D6875);
    color: white !important; padding: 12px 0; text-align: center; border-radius: 25px;
    font-weight: 900; box-shadow: 0 4px 10px rgba(142, 151, 117, 0.4);
    margin-bottom: 12px; cursor: default;
}}

/* 輸入框優化 */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background-color: #FFFFFF !important; border-radius: 10px; padding: 5px;
}}
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #F8F9FA !important; color: #000000 !important;
    border: 2px solid #E0E0E0 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important;
}}
li[role="option"]:hover {{
    background-color: #E8F5E9 !important; color: {GREEN} !important;
}}

/* 按鈕樣式 */
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button {{
    background-color: {PRIMARY} !important; color: #FFFFFF !important;
    border: none !important; border-radius: 12px !important; font-weight: 900 !important;
    padding: 10px 25px !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: {GREEN} !important;
    transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}}

/* 看板卡片 */
.care-metric-box {{
    padding: 20px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1); min-height: 140px;
    display: flex; flex-direction: column; justify-content: center;
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 訪視卡片 */
.visit-card {{
    background-color: #FFFFFF; border-left: 5px solid {GREEN};
    border-radius: 10px; padding: 15px 20px; margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;
}}
.visit-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.visit-date {{ font-weight: 900; font-size: 1.1rem; color: #333; }}
.visit-volunteer {{ font-size: 0.9rem; color: #666; background: #f0f0f0; padding: 4px 12px; border-radius: 15px; }}
.visit-tag {{
    display: inline-block; background-color: {GREEN}; color: white !important;
    padding: 4px 10px; border-radius: 5px; font-size: 0.9rem; font-weight: bold; margin-bottom: 8px;
}}
.visit-tag.only {{ background-color: #9E9E9E; }} 
.visit-note {{ font-size: 1rem; color: #444; line-height: 1.5; background: #FAFAFA; padding: 10px; border-radius: 8px; }}

/* 庫存管理卡片 */
.stock-card {{
    background-color: white; border: 1px solid #eee; border-radius: 15px;
    padding: 20px; margin-bottom: 20px; position: relative;
    transition: all 0.3s ease; height: 100%;
}}
.stock-card:hover {{
    transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: {GREEN};
}}
.stock-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
.stock-icon {{ font-size: 2.5rem; background: #F5F5F5; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }}
.stock-info {{ text-align: right; width: 100%; padding-left: 10px; }}
.stock-name {{ font-size: 1.3rem; font-weight: 900; color: #333; margin-bottom: 3px; line-height: 1.2; }}
.stock-donor {{ font-size: 0.9rem; color: {PRIMARY}; background: #EFEBE9; padding: 2px 8px; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
.stock-type {{ font-size: 0.8rem; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 8px; display: inline-block; }}
.stock-bar-bg {{ width: 100%; height: 10px; background: #eee; border-radius: 5px; overflow: hidden; margin-top: 10px; }}
.stock-bar-fill {{ height: 100%; border-radius: 5px; transition: width 0.5s ease; }}
.stock-stats {{ display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.9rem; color: #666; font-weight: bold; }}
.stock-warning {{ color: #D32F2F; font-weight: bold; display: flex; align-items: center; gap: 5px; margin-top: 10px; font-size: 0.9rem; }}

/* 卡片上浮效果 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    border: 2px solid #E0E0E0 !important; background-color: #FFFFFF;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    transform: translateY(-8px); box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    border-color: {GREEN} !important; z-index: 10;
}}
.inv-card-header {{ font-weight: 900; font-size: 1.1rem; color: #333; margin-bottom: 5px; }}
.inv-card-stock {{ font-size: 0.9rem; color: #666; background-color: #eee; padding: 2px 8px; border-radius: 10px; display: inline-block; margin-bottom: 10px; }}
.inv-card-stock.low {{ color: #D32F2F !important; background-color: #FFEBEE !important; border: 1px solid #D32F2F; }}

/* --- 🔥 新增：健康儀表板卡片樣式 --- */
.health-dashboard-card {{
    padding: 15px;
    border-radius: 15px;
    color: white !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: transform 0.2s;
}}
.health-dashboard-card:hover {{ transform: translateY(-3px); }}

/* 危險 (紅) */
.h-card-danger {{
    background: linear-gradient(135deg, #FF5252 0%, #C62828 100%);
    border: 1px solid #B71C1C;
}}
/* 警告 (橘) */
.h-card-warning {{
    background: linear-gradient(135deg, #FFB74D 0%, #EF6C00 100%);
    border: 1px solid #E65100;
}}
/* 安全 (綠) */
.h-card-safe {{
    background: linear-gradient(135deg, #81C784 0%, #2E7D32 100%);
    border: 1px solid #1B5E20;
}}

.h-card-icon {{ font-size: 2.5rem; margin-right: 15px; opacity: 0.9; }}
.h-card-content {{ flex-grow: 1; }}
.h-card-title {{ font-size: 0.9rem; opacity: 0.9; font-weight: bold; }}
.h-card-value {{ font-size: 1.4rem; font-weight: 900; }}
.h-card-score {{ background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; }}

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
# 2) 資料邏輯 (更新欄位定義)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者", "拒絕物資"] 

# 更新資料定義：包含 Word 檔所有題項
# =========================================================
COLS_HEALTH = [
    # 識別
    "姓名", "身分證字號", "評估日期",
    
    # 一、前測問卷及身體狀況 (Source 1 & 21)
    "收縮壓", "舒張壓", "心跳", "身高", "體重", "BMI", "右手握力", "左手握力",
    "教育程度", "婚姻狀況", "居住狀況", "居住樓層", "信仰", "經濟狀況", "是否有工作",
    "主要照顧者", "過去疾病史", 
    "使用行走輔具", "使用聽力輔具", "使用視力輔具", "半年內跌倒紀錄", 
    "服用助眠藥", "服用心血管藥物", "喝乳品習慣", "使用漏尿墊", "男性小便斷續", # 身體狀況問卷細項

    # 二、ICOPE (Source 3 & 4)
    "ICOPE_記憶減退", "ICOPE_跌倒風險", "ICOPE_體重減輕", "ICOPE_食慾不佳", 
    "ICOPE_視力困難", "ICOPE_曾驗光", "ICOPE_曾洗牙", 
    "ICOPE_聽力_聽不清", "ICOPE_聽力_太這聲", "ICOPE_聽力_需重說", "ICOPE_聽力_不想社交", # 聽力四細項
    "ICOPE_心情低落", "ICOPE_減少社交",
    
    # 三、BSRS-5 心情溫度計 (Source 6 & 7)
    "BSRS_1_睡眠", "BSRS_2_緊張", "BSRS_3_動怒", "BSRS_4_憂鬱", "BSRS_5_自卑", "BSRS_6_自殺",
    "BSRS_總分", "BSRS_狀態",

    # 四、MNA (Source 2 雖未列細項，但依照標準 MNA 補齊，並做防重複邏輯)
    "MNA_A_食量", "MNA_B_體重", "MNA_C_活動", "MNA_D_創傷", "MNA_E_精神", "MNA_F_BMI",
    "MNA_篩檢分數", "MNA_狀態",

    # 五、WHO-5 (Source 9 & 10)
    "WHO5_1_開朗", "WHO5_2_平靜", "WHO5_3_活力", "WHO5_4_休息", "WHO5_5_興趣",
    "WHO5_總分",

    # 六、膀胱症狀 (Source 12-16)
    "膀胱_1_頻尿", "膀胱_2_尿急", "膀胱_3_用力漏尿", "膀胱_4_少量漏尿", "膀胱_5_解尿困難", "膀胱_6_下腹痛",
    "IIQ7_1_家事", "IIQ7_2_健身", "IIQ7_3_娛樂", "IIQ7_4_開車搭車", "IIQ7_5_社交", "IIQ7_6_情緒", "IIQ7_7_挫折",

    # 七、WHOQOL-BREF (Source 18 & 19)
    "QOL_1_生活品質", "QOL_2_健康滿意", "QOL_3_疼痛妨礙", "QOL_4_醫療依賴", "QOL_5_享受生活", "QOL_6_生命意義", "QOL_7_集中精神",
    "QOL_8_安全感", "QOL_9_環境健康", "QOL_10_精力", "QOL_11_外表", "QOL_12_金錢", "QOL_13_資訊", "QOL_14_休閒",
    "QOL_15_行動能力", "QOL_16_睡眠", "QOL_17_日常活動", "QOL_18_工作能力", "QOL_19_自我滿意", "QOL_20_人際關係", "QOL_21_性生活",
    "QOL_22_朋友支持", "QOL_23_住所", "QOL_24_醫療方便", "QOL_25_交通", "QOL_26_負面感受", "QOL_27_被尊重", "QOL_28_食物"
]

COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]
# ==========================================
# 🧠 智慧判讀字典：定義「類別」包含哪些「關鍵字」
# ==========================================
SMART_RULES = {
    "海鮮": ["魚", "蝦", "蟹", "貝", "蛤", "魷", "透抽", "鯖", "鮪", "海苔", "XO醬"],
    "甲殼": ["蝦", "蟹", "龍蝦"],
    "牛肉": ["牛"],
    "豬肉": ["豬", "培根", "火腿", "香腸"],
    "堅果": ["花生", "杏仁", "核桃", "腰果", "芝麻"],
}

def check_conflict(refuse_str, item_name):
    """
    智慧比對函數：
    1. refuse_str: 關懷戶拒絕的項目 (如 "海鮮, 辣")
    2. item_name: 物資名稱 (如 "紅燒鯖魚罐頭")
    回傳: (是否衝突, 衝突的原因關鍵字)
    """
    if not refuse_str: return False, None
    
    # 1. 整理拒絕清單
    refuse_list = [k.strip() for k in refuse_str.split(',') if k.strip()]
    
    for r_key in refuse_list:
        # A. 直接比對 (例如拒絕 "鯖魚"，物資是 "鯖魚罐頭" -> 中)
        if r_key in item_name:
            return True, r_key
            
        # B. 查字典比對 (例如拒絕 "海鮮"，系統去查海鮮包含什麼)
        if r_key in SMART_RULES:
            related_words = SMART_RULES[r_key]
            for word in related_words:
                if word in item_name:
                    return True, f"{r_key}(含{word})"
    
    return False, None

# =========================================================
# 2) 資料邏輯 (優化版)
# =========================================================
# ... (保留原本的 SHEET_ID 與 COLS 定義) ...

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

# 優化 A：快取時間延長至 60 秒，減少切換頁面時的卡頓
@st.cache_data(ttl=60)
def load_data(sn, target_cols):
    try:
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        # 這裡建議用 get_all_values 比較快，再轉 DataFrame
        data = sheet.get_all_values()
        if not data: return pd.DataFrame(columns=target_cols)
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        # 補齊缺少的欄位
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=target_cols)

# 維持原本的 save_data 用於「修改舊資料/編輯整張表」
def save_data(df, sn):
    try:
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear(); sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}"); return False

# 優化 B：新增「追加模式」函式 (新增資料專用)
def append_data(sn, row_dict, col_order):
    """
    sn: 工作表名稱 (如 'care_logs')
    row_dict: 要新增的資料字典
    col_order: 欄位順序列表 (如 COLS_LOG)
    """
    try:
        # 依照固定欄位順序產生 list
        row_values = [str(row_dict.get(c, "")).strip() for c in col_order]
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.append_row(row_values) # 關鍵：只加一行
        st.cache_data.clear() # 清除快取，讓下次讀取能讀到新的
        return True
    except Exception as e:
        st.error(f"新增失敗：{e}"); return False

# 🔥 新增函數：從地址推斷樓層
def extract_floor(address_str):
    """
    嘗試從地址字串中提取樓層。
    例如: "桃園市中正路10號3樓" -> "3樓"
    "中正路5號" -> "1樓" (若無樓層字樣通常為1樓或透天)
    """
    if not address_str: return "無法推斷"
    # 尋找 "X樓" 或 "XF" 的模式
    match = re.search(r'(\d+|[一二三四五六七八九十]+)[樓Ff]', address_str)
    if match:
        return match.group(0) # 返回如 "3樓"
    return "1樓" # 預設

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today(); return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) Navigation
# =========================================================
def render_nav():
    with st.sidebar:
        st.markdown(f"<h2 style='color:{GREEN}; margin-bottom:5px; padding-left:10px;'>🏠 關懷戶中心</h2>", unsafe_allow_html=True)
        st.write("") 
        if st.session_state.page == 'home':
            st.markdown('<div class="nav-active">📊 關懷概況看板</div>', unsafe_allow_html=True)
        else:
            if st.button("📊 關懷概況看板", key="nav_home", use_container_width=True): st.session_state.page = 'home'; st.rerun()
        if st.session_state.page == 'members':
            st.markdown('<div class="nav-active">📋 名冊管理</div>', unsafe_allow_html=True)
        else:
            if st.button("📋 名冊管理", key="nav_members", use_container_width=True): st.session_state.page = 'members'; st.rerun()
        if st.session_state.page == 'health':
            st.markdown('<div class="nav-active">🏥 健康追蹤</div>', unsafe_allow_html=True)
        else:
            if st.button("🏥 健康追蹤", key="nav_health", use_container_width=True): st.session_state.page = 'health'; st.rerun()
        if st.session_state.page == 'inventory':
            st.markdown('<div class="nav-active">📦 物資庫存</div>', unsafe_allow_html=True)
        else:
            if st.button("📦 物資庫存", key="nav_inv", use_container_width=True): st.session_state.page = 'inventory'; st.rerun()
        if st.session_state.page == 'visit':
            st.markdown('<div class="nav-active">🤝 訪視發放</div>', unsafe_allow_html=True)
        else:
            if st.button("🤝 訪視發放", key="nav_visit", use_container_width=True): st.session_state.page = 'visit'; st.rerun()
        if st.session_state.page == 'stats':
            st.markdown('<div class="nav-active">📈 數據統計</div>', unsafe_allow_html=True)
        else:
            if st.button("📈 數據統計", key="nav_stats", use_container_width=True): st.session_state.page = 'stats'; st.rerun()
        st.markdown("---")
        if st.button("🚪 回系統大廳", key="nav_back", use_container_width=True): st.switch_page("Home.py")
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem;'>Designed for Fude Community</div>", unsafe_allow_html=True)

# =========================================================
# 4) Pages
# =========================================================

# --- [分頁 0：首頁] ---
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {GREEN};'>📊 關懷戶概況看板</h2>", unsafe_allow_html=True)
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        mems_display = mems[~mems['身分別'].str.contains("一般戶", na=False)]
        
        cur_y = datetime.now(TW_TZ).year
        prev_y = cur_y - 1
        
        dist_df = logs.copy()
        if not logs.empty:
            dist_df['dt'] = pd.to_datetime(dist_df['發放日期'], errors='coerce')
            cur_val = dist_df[dist_df['dt'].dt.year == cur_y]['發放數量'].replace("","0").astype(float).sum()
            prev_val = dist_df[dist_df['dt'].dt.year == prev_y]['發放數量'].replace("","0").astype(float).sum()
        else: cur_val = prev_val = 0
        
        # ---原本的統計邏輯 (保留並微調)---
        dis_c = len(mems[mems['身分別'].str.contains("身障", na=False)])
        low_c = len(mems[mems['身分別'].str.contains("低收|中低收", na=False)])
        
        # 【新增程式碼】計算獨居老人數據
        # 邏輯：篩選身分別包含「獨居」的資料
        sol_df = mems[mems['身分別'].str.contains("獨居", na=False)]
        sol_c = len(sol_df)
        # 計算平均年齡 (如果沒有人則為 0)
        sol_age = round(sol_df['age'].mean(), 1) if not sol_df.empty else 0
        
        # 【修改版面】將原本 st.columns(3) 改為 4 欄，以便放入新卡片
        c1, c2, c3, c4 = st.columns(4)
        
        # 卡片1：總人數 (維持原樣)
        with c1: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數</div><div style="font-size:2.8rem;">{len(mems_display)} <span style="font-size:1.2rem;">人</span></div><div>平均 {round(mems_display["age"].mean(),1)} 歲</div></div>', unsafe_allow_html=True)
        
        # 卡片2：【新增】獨居長者 (使用暖色系漸層區隔)
        with c2: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#CB997E 0%,#6D6875 100%);"><div>👴 獨居長者</div><div style="font-size:2.8rem;">{sol_c} <span style="font-size:1.2rem;">人</span></div><div>平均 {sol_age} 歲</div></div>', unsafe_allow_html=True)
        
        # 卡片3：身障 (原本的 c2 移到這裡)
        with c3: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數</div><div style="font-size:2.8rem;">{dis_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        
        # 卡片4：低收 (原本的 c3 移到這裡)
        with c4: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#6D6875 0%,#4A4E69 100%);"><div>📉 低收/中低收</div><div style="font-size:2.8rem;">{low_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        
        # ---第二排維持顯示發放量 (變數名稱順延修改為 c5, c6)---
        c5, c6 = st.columns(2)
        with c5: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#BC6C25 0%,#8E9775 100%);"><div>🎁 {cur_y} 當年度發放量</div><div style="font-size:3.5rem;">{int(cur_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#6D6875 100%);"><div>⏳ {prev_y} 上年度發放量</div><div style="font-size:3.5rem;">{int(prev_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)

# --- [分頁 1：名冊] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增關懷戶 (展開填寫)", expanded=False):
        with st.form("add_care", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            g = c3.selectbox("性別", ["男", "女"])
            b = c4.date_input("生日", value=date(1950, 1, 1), min_value=date(1911, 1, 1), max_value=date(2025, 12, 31))
            addr = st.text_input("地址")
            ph = st.text_input("電話")
            ce1, ce2 = st.columns(2)
            en = ce1.text_input("緊急聯絡人")
            ep = ce2.text_input("緊急聯絡電話")
            cn1, cn2, cn3 = st.columns(3)
            child = cn1.number_input("18歲以下子女", min_value=0, value=0, step=1)
            adult = cn2.number_input("成人數量", min_value=0, value=0, step=1)
            senior = cn3.number_input("65歲以上長者", min_value=0, value=0, step=1)
            id_t = st.multiselect("身分別", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女", "一般戶"])
            
            if st.form_submit_button("確認新增"):
                is_duplicate = False
                if not df.empty:
                    mask = (df['姓名'] == n) & (df['身分證字號'] == p.upper())
                    if not df[mask].empty: is_duplicate = True

                if is_duplicate: st.error(f"❌ 資料重複！名冊中已有「{n} ({p})」的資料。")
                elif not n or not p: st.error("❌ 姓名與身分證字號必填")
                else:
                    new = {
                        "姓名": n, "身分證字號": p.upper(), "性別": g, "生日": str(b), 
                        "地址": addr, "電話": ph, "緊急聯絡人": en, "緊急聯絡人電話": ep, 
                        "身分別": ",".join(id_t),
                        "18歲以下子女": str(child), "成人數量": str(adult), "65歲以上長者": str(senior)
                    }
                    if append_data("care_members", new, COLS_MEM):
                        st.success("✅ 已新增！"); time.sleep(1); st.rerun()
    
    st.markdown("### 📝 完整名冊 (需權限)")
    if st.session_state.unlock_members:
        if not df.empty:
            df['歲數'] = df['生日'].apply(calculate_age)
            ed = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
            if st.button("💾 儲存修改"): 
                if save_data(ed, "care_members"): st.success("已更新")
    else:
        st.info("🔒 為保護個資，查看完整表格需輸入管理員密碼。")
        c_pwd, c_btn = st.columns([2, 1])
        with c_pwd: pwd_m = st.text_input("請輸入密碼", type="password", key="unlock_m_pwd")
        with c_btn: 
            if st.button("🔓 解鎖名冊"):
                if pwd_m == st.secrets["admin_password"]:
                    st.session_state.unlock_members = True; st.rerun()
                else: st.error("❌ 密碼錯誤")

# =========================================================
# 🔥 Page: Health (依照 Word 檔嚴格分區)
# =========================================================
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 綜合健康評估 (2026前測版)")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增/更新 評估紀錄", expanded=True):
        sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
        
        # 0. 預載資料 (避免重複問)
        p_info = {}
        if sel_n != "無名冊" and not m_df.empty:
            p_row = m_df[m_df['姓名'] == sel_n].iloc[0]
            p_info['gender'] = p_row['性別']
            p_info['age'] = calculate_age(p_row['生日'])
            p_info['floor'] = extract_floor(p_row['地址'])
            st.info(f"✅ 系統已自動帶入：{p_info['gender']}性 / {p_info['age']}歲 / 推測住 {p_info['floor']}")

        with st.form("h_form_full"):
            eval_date = st.date_input("填表日期", value=date.today())

            # 依照 Word 檔案分類建立 7 個分頁
            t1, t2, t3, t4, t5, t6, t7 = st.tabs([
                "一、基本與身體", "二、ICOPE", "三、BSRS-5", "四、MNA", "五、WHO-5", "六、膀胱", "七、WHOQOL"
            ])

            # --- 一、前測問卷及身體狀況問卷 ---
            with t1:
                st.markdown("### 1. 基本資料與身體狀況")
                c1, c2, c3 = st.columns(3)
                edu = c1.selectbox("教育程度", ["不識字", "識字未就學", "國小", "國中", "高中", "大專以上"])
                marry = c2.selectbox("婚姻狀況", ["未婚", "已婚", "鰥寡", "分居", "離異", "其他"])
                # 若名冊無樓層資料才詢問
                floor_val = p_info.get('floor', '無法推斷')
                if floor_val == '無法推斷':
                    floor_final = c3.text_input("居住樓層", placeholder="例如：3樓")
                else:
                    floor_final = floor_val # 隱藏欄位，直接帶入
                    c3.success(f"居住樓層：{floor_val} (已帶入)")

                c4, c5 = st.columns(2)
                live_st = c4.selectbox("居住狀況", ["獨居", "榮家", "僅與配偶居", "與家人居(含配偶)", "與家人居(不含配偶)", "與親友居", "機構", "其他"])
                relig = c5.selectbox("信仰", ["無", "佛教", "道教", "基督教", "回教", "天主教", "其他"])
                
                c6, c7, c8 = st.columns(3)
                work = c6.radio("目前工作?", ["退休", "家管", "有工作"], horizontal=True)
                econ = c7.radio("經濟狀況?", ["富裕", "小康", "貧窮", "其他"], horizontal=True)
                caregiver = c8.multiselect("主要照顧者", ["自己", "配偶", "子女", "看護", "其他"])
                
                dis_hist = st.multiselect("過去疾病史", ["無", "糖尿病", "高血壓", "高血脂", "心臟病", "腎臟病", "肝炎", "關節炎", "骨鬆", "氣喘", "癌症", "其他"])

                st.markdown("---")
                st.markdown("#### 身體狀況量測")
                bp1, bp2, hr = st.columns(3)
                sys_p = bp1.number_input("收縮壓", step=1)
                dia_p = bp2.number_input("舒張壓", step=1)
                hr_p = hr.number_input("心跳", step=1)
                
                h1, w1, bmi_col = st.columns(3)
                h_v = h1.number_input("身高(cm)", min_value=0.0, step=0.1)
                w_v = w1.number_input("體重(kg)", min_value=0.0, step=0.1)
                bmi_cal = round(w_v/((h_v/100)**2),1) if h_v > 0 and w_v > 0 else 0
                bmi_col.info(f"BMI: {bmi_cal}")

                g1, g2 = st.columns(2)
                grip_r = g1.number_input("右手握力", step=0.1)
                grip_l = g2.number_input("左手握力", step=0.1)

                m1, m2, m3, m4 = st.columns(4)
                aid_walk = m1.checkbox("使用行走輔具")
                aid_hear = m2.checkbox("使用聽力輔具")
                aid_eye = m3.checkbox("使用視力輔具(眼鏡)")
                fall_rec = m4.radio("半年內曾跌倒?", ["無", "有"], horizontal=True)

                d1, d2, d3 = st.columns(3)
                med_sleep = d1.radio("服用助眠藥?", ["無", "有"], horizontal=True)
                med_cv = d2.radio("服用心血管藥?", ["無", "有"], horizontal=True)
                milk_habit = d3.radio("喝乳品習慣?", ["無", "有"], horizontal=True)

                # 性別特有題
                spec_q = st.container()
                pad_use = "無"
                male_urine = "無"
                if p_info.get('gender') == '女':
                    spec_q.markdown("**👩 女性專用題**")
                    pad_use = spec_q.radio("使用漏尿墊?", ["無", "有"], horizontal=True)
                elif p_info.get('gender') == '男':
                    spec_q.markdown("**👨 男性專用題**")
                    male_urine = spec_q.radio("小便斷續不連貫?", ["無", "有"], horizontal=True)

            # --- 二、ICOPE ---
            with t2:
                st.markdown("### 2. 高齡功能 ICOPE")
                icope_mem = st.radio("記憶明顯減退?", ["否", "是"], horizontal=True)
                # 跌倒題 ICOPE 問的是"過去一年"，不同於前面的"半年"，故依 Word 檔保留
                icope_fall = st.radio("過去一年曾跌倒/擔心跌倒/需扶東西?", ["否", "是"], horizontal=True)
                icope_w = st.radio("過去三個月體重減輕>3kg?", ["否", "是"], horizontal=True)
                icope_eat = st.radio("過去三個月食慾不好?", ["否", "是"], horizontal=True)
                
                st.markdown("---")
                i1, i2, i3 = st.columns(3)
                icope_eye = i1.radio("看遠近/閱讀困難?", ["否", "是"], horizontal=True)
                icope_opt = i2.radio("過去一年曾眼睛檢查?", ["否", "是"], horizontal=True) # Word 題目是"曾接受"，選項0否1是
                icope_teeth = i3.radio("過去六個月曾洗牙?", ["否", "是"], horizontal=True) # Word 題目是"曾洗牙"

                st.markdown("---")
                st.write("**聽力狀況 (任一符合請勾選)**")
                h_c1, h_c2 = st.columns(2)
                ih_1 = h_c1.checkbox("電話聽不清")
                ih_2 = h_c2.checkbox("被說音量太大")
                ih_3 = h_c1.checkbox("需對方重說")
                ih_4 = h_c2.checkbox("因聽力不想聚會")
                
                st.markdown("---")
                icope_mood = st.radio("過去兩週常心情不好/沒希望?", ["否", "是"], horizontal=True)
                icope_soc = st.radio("過去兩週減少活動/朋友來往?", ["否", "是"], horizontal=True)

            # --- 三、BSRS-5 ---
            with t3:
                st.markdown("### 3. BSRS-5 心情溫度計")
                st.caption("0:完全沒有 ~ 4:非常厲害")
                bsrs_sc = []
                bsrs_sc.append(st.slider("1. 睡眠困難", 0, 4, 0))
                bsrs_sc.append(st.slider("2. 感覺緊張不安", 0, 4, 0))
                bsrs_sc.append(st.slider("3. 覺得容易動怒", 0, 4, 0))
                bsrs_sc.append(st.slider("4. 感覺憂鬱低落", 0, 4, 0))
                bsrs_sc.append(st.slider("5. 覺得比不上別人", 0, 4, 0))
                bsrs_6 = st.slider("6. 有自殺想法 (獨立計分)", 0, 4, 0)
                
                bsrs_total = sum(bsrs_sc)
                if bsrs_total >= 15: bsrs_stat = "重度情緒困擾"
                elif bsrs_total >= 10: bsrs_stat = "中度情緒困擾"
                elif bsrs_total >= 6: bsrs_stat = "輕度情緒困擾"
                else: bsrs_stat = "正常"
                st.caption(f"當前得分：{bsrs_total} ({bsrs_stat})")

            # --- 四、MNA (防重複邏輯) ---
            with t4:
                st.markdown("### 4. MNA 營養評估")
                
                # Q1: 食慾 (參考 ICOPE)
                mna_a_idx = 2
                if icope_eat == "是":
                    st.warning("⚠️ ICOPE 已填寫「食慾不好」，請確認程度：")
                    mna_a = st.radio("A. 食量減少程度?", ["0:嚴重減少", "1:中度減少", "2:無改變"], horizontal=True)
                else:
                    st.success("✅ ICOPE 填寫「食慾正常」，自動代入「無改變」")
                    mna_a = "2:無改變"

                # Q2: 體重 (參考 ICOPE)
                if icope_w == "是":
                    st.warning("⚠️ ICOPE 已填寫「體重減輕>3kg」，請確認：")
                    mna_b = st.radio("B. 體重減輕情況?", ["0:>3公斤", "1:不知道", "2:1~3公斤", "3:無"], horizontal=True)
                else:
                    st.success("✅ ICOPE 填寫「無減輕>3kg」，自動代入「無/無改變」")
                    mna_b = "3:無"

                # 其他 MNA 題
                mna_c = st.radio("C. 活動能力?", ["0:臥床/輪椅", "1:可下床但無法外出", "2:可外出"], horizontal=True)
                mna_d = st.radio("D. 過去3個月有心理創傷/急性病?", ["0:有", "2:無"], horizontal=True)
                mna_e = st.radio("E. 精神心理問題(失智/憂鬱)?", ["0:嚴重", "1:輕度", "2:無"], horizontal=True)
                
                # MNA BMI
                mna_bmi_score = 0
                if bmi_cal < 19: mna_bmi_score = 0
                elif 19 <= bmi_cal < 21: mna_bmi_score = 1
                elif 21 <= bmi_cal < 23: mna_bmi_score = 2
                else: mna_bmi_score = 3
                st.write(f"F. BMI ({bmi_cal}) 得分：{mna_bmi_score}")

                # 計算分
                try:
                    mna_score = int(mna_a[0]) + int(mna_b[0]) + int(mna_c[0]) + int(mna_d[0]) + int(mna_e[0]) + mna_bmi_score
                    mna_st = "正常" if mna_score >= 12 else ("有風險" if mna_score >= 8 else "營養不良")
                    st.caption(f"MNA 總分: {mna_score} ({mna_st})")
                except: mna_score = 0; mna_st = "計算中"

            # --- 五、WHO-5 ---
            with t5:
                st.markdown("### 5. 幸福指標 WHO-5 (過去兩週)")
                who_q = ["1. 感到情緒開朗精神不錯", "2. 感到心情平靜放鬆", "3. 感到有活力精力充沛", "4. 醒來感到神清氣爽", "5. 充滿感興趣的事物"]
                who_s = []
                for q in who_q:
                    who_s.append(st.slider(q, 0, 5, 3, help="0:從未 ~ 5:全部時間"))
                who_total = sum(who_s) * 4
                st.caption(f"幸福指數 (0-100): {who_total}")

            # --- 六、膀胱與 IIQ-7 ---
            with t6:
                st.markdown("### 6. 膀胱症狀與生活品質")
                st.markdown("**第一部分：症狀困擾 (0:不會 ~ 3:嚴重困擾)**")
                blad_qs = ["常上廁所?", "尿急來不及?", "用力時漏尿?", "少量漏尿?", "解尿困難?", "下腹/私密處痛?"]
                blad_ans = []
                for bq in blad_qs:
                    blad_ans.append(st.radio(bq, ["不會", "輕微", "中等", "嚴重"], horizontal=True, key=bq))
                
                st.markdown("---")
                st.markdown("**第二部分：IIQ-7 生活影響 (沒有/輕微/中等/嚴重)**")
                iiq_qs = ["做家事", "健身活動", "休閒娛樂", "開車/搭車", "社交活動", "情緒健康", "挫折感"]
                iiq_ans = []
                for iq in iiq_qs:
                    iiq_ans.append(st.radio(f"影響{iq}?", ["沒有", "輕微", "中等", "嚴重"], horizontal=True, key=f"iiq_{iq}"))

            # --- 七、WHOQOL-BREF ---
            with t7:
                st.markdown("### 7. WHOQOL-BREF 生活品質")
                st.info("請依照過去兩週的感受作答")
                
                qol_data = {}
                
                # Q1, Q2 獨立選項
                qol_data['Q1'] = st.selectbox("1. 整體生活品質評價?", ["1:極不好", "2:不好", "3:中等", "4:好", "5:極好"])
                qol_data['Q2'] = st.selectbox("2. 對自己健康滿意嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"])
                
                st.markdown("---")
                # Q3-Q28 列表呈現
                qol_items = [
                    (3, "身體疼痛妨礙做事?", ["5:完全沒有", "4:有一點", "3:中等", "2:很妨礙", "1:極妨礙"]),
                    (4, "需要醫療幫助?", ["5:完全沒有", "4:有一點", "3:中等", "2:很需要", "1:極需要"]),
                    (5, "享受生活?", ["1:完全沒有", "2:有一點", "3:中等", "4:很享受", "5:極享受"]),
                    (6, "生命有意義?", ["1:完全沒有", "2:有一點", "3:中等", "4:很有", "5:極有"]),
                    (7, "集中精神能力?", ["1:完全不好", "2:有一點", "3:中等", "4:很好", "5:極好"]),
                    (8, "感到安全嗎?", ["1:完全不", "2:有一點", "3:中等", "4:很安全", "5:極安全"]),
                    (9, "環境健康嗎?", ["1:完全不", "2:有一點", "3:中等", "4:很健康", "5:極健康"]),
                    (10, "精力足夠嗎?", ["1:完全不", "2:少許", "3:中等", "4:很足夠", "5:完全足夠"]),
                    (11, "接受自己外表?", ["1:完全不", "2:少許", "3:中等", "4:很能夠", "5:完全能夠"]),
                    (12, "金錢足夠嗎?", ["1:完全不", "2:少許", "3:中等", "4:很足夠", "5:完全足夠"]),
                    (13, "資訊方便嗎?", ["1:完全不", "2:少許", "3:中等", "4:很方便", "5:完全方便"]),
                    (14, "休閒機會?", ["1:完全沒有", "2:少許", "3:中等", "4:很有", "5:完全有"]),
                    (15, "行動能力?", ["1:完全不好", "2:有一點", "3:中等", "4:很好", "5:極好"]),
                    (16, "睡眠滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (17, "日常活動能力?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (18, "工作能力?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (19, "對自己滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (20, "人際關係滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (21, "性生活滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (22, "朋友支持滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (23, "住所滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (24, "醫療方便滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (25, "交通滿意?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                    (26, "負面感受頻率?", ["5:從來沒有", "4:不常有", "3:一半一半", "2:很常有", "1:一直都有"]),
                    (27, "被尊重?", ["1:完全沒有", "2:有一點", "3:中等", "4:很有", "5:極有"]),
                    (28, "想吃的能吃到?", ["1:從來沒有", "2:不常有", "3:一半一半", "4:很常有", "5:一直都有"]),
                ]
                
                for q_idx, q_txt, q_opts in qol_items:
                    qol_data[f"Q{q_idx}"] = st.radio(f"{q_idx}. {q_txt}", q_opts, horizontal=True)

            # --- 送出儲存 ---
            if st.form_submit_button("💾 儲存完整問卷資料"):
                if sel_n == "無名冊":
                    st.error("請選擇關懷戶")
                else:
                    # 整理所有資料
                    row_data = {
                        "姓名": sel_n, "身分證字號": p_row['身分證字號'], "評估日期": str(eval_date),
                        
                        # 1. 身體
                        "收縮壓": sys_p, "舒張壓": dia_p, "心跳": hr_p, "身高": h_v, "體重": w_v, "BMI": bmi_cal,
                        "右手握力": grip_r, "左手握力": grip_l,
                        "教育程度": edu, "婚姻狀況": marry, "居住狀況": live_st, "居住樓層": floor_final, "信仰": relig,
                        "經濟狀況": econ, "是否有工作": work, "主要照顧者": ",".join(caregiver), "過去疾病史": ",".join(dis_hist),
                        "使用行走輔具": aid_walk, "使用聽力輔具": aid_hear, "使用視力輔具": aid_eye, "半年內跌倒紀錄": fall_rec,
                        "服用助眠藥": med_sleep, "服用心血管藥物": med_cv, "喝乳品習慣": milk_habit, 
                        "使用漏尿墊": pad_use, "男性小便斷續": male_urine,

                        # 2. ICOPE
                        "ICOPE_記憶減退": icope_mem, "ICOPE_跌倒風險": icope_fall, "ICOPE_體重減輕": icope_w, "ICOPE_食慾不佳": icope_eat,
                        "ICOPE_視力困難": icope_eye, "ICOPE_曾驗光": icope_opt, "ICOPE_曾洗牙": icope_teeth,
                        "ICOPE_聽力_聽不清": ih_1, "ICOPE_聽力_太這聲": ih_2, "ICOPE_聽力_需重說": ih_3, "ICOPE_聽力_不想社交": ih_4,
                        "ICOPE_心情低落": icope_mood, "ICOPE_減少社交": icope_soc,

                        # 3. BSRS
                        "BSRS_1_睡眠": bsrs_sc[0], "BSRS_2_緊張": bsrs_sc[1], "BSRS_3_動怒": bsrs_sc[2],
                        "BSRS_4_憂鬱": bsrs_sc[3], "BSRS_5_自卑": bsrs_sc[4], "BSRS_6_自殺": bsrs_6,
                        "BSRS_總分": bsrs_total, "BSRS_狀態": bsrs_stat,

                        # 4. MNA
                        "MNA_A_食量": mna_a, "MNA_B_體重": mna_b, "MNA_C_活動": mna_c, "MNA_D_創傷": mna_d,
                        "MNA_E_精神": mna_e, "MNA_F_BMI": mna_bmi_score, "MNA_篩檢分數": mna_score, "MNA_狀態": mna_st,

                        # 5. WHO5
                        "WHO5_1_開朗": who_s[0], "WHO5_2_平靜": who_s[1], "WHO5_3_活力": who_s[2], 
                        "WHO5_4_休息": who_s[3], "WHO5_5_興趣": who_s[4], "WHO5_總分": who_total,

                        # 6. 膀胱
                        "膀胱_1_頻尿": blad_ans[0], "膀胱_2_尿急": blad_ans[1], "膀胱_3_用力漏尿": blad_ans[2],
                        "膀胱_4_少量漏尿": blad_ans[3], "膀胱_5_解尿困難": blad_ans[4], "膀胱_6_下腹痛": blad_ans[5],
                        "IIQ7_1_家事": iiq_ans[0], "IIQ7_2_健身": iiq_ans[1], "IIQ7_3_娛樂": iiq_ans[2], "IIQ7_4_開車搭車": iiq_ans[3],
                        "IIQ7_5_社交": iiq_ans[4], "IIQ7_6_情緒": iiq_ans[5], "IIQ7_7_挫折": iiq_ans[6],
                    }
                    
                    # 7. WHOQOL 批次寫入
                    for k, v in qol_data.items():
                        row_data[f"QOL_{k.replace('Q','')}"] = v # 轉成如 QOL_1, QOL_2...
                        
                    # 儲存
                    if save_data(pd.concat([h_df, pd.DataFrame([row_data])], ignore_index=True), "care_health"):
                        st.success("✅ 完整問卷已存檔！")
                        time.sleep(1)
                        st.rerun()

    # 歷史紀錄
    if not h_df.empty:
        st.markdown("### 📂 歷史問卷紀錄")
        st.dataframe(h_df.sort_values("評估日期", ascending=False), use_container_width=True)

# --- [分頁 3：物資] ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    
    with st.expander("➕ 新增捐贈物資 / 款項", expanded=False):
        existing_donors = sorted(list(set(inv['捐贈者'].dropna().unique()))) if not inv.empty else []
        
        st.markdown(f"<div style='background:#f9f9f9; padding:10px; border-radius:10px; margin-bottom:10px;'><b>⚙️ 步驟 1：設定來源與類型</b></div>", unsafe_allow_html=True)
        c_mode1, c_mode2 = st.columns(2)
        with c_mode1:
            donor_mode = st.radio("👤 捐贈者來源", ["從歷史名單選擇", "輸入新單位"], horizontal=True)
        with c_mode2:
            sel_type = st.selectbox("📦 物資類型", ["食物","日用品","輔具","急難救助金","服務"])
            type_history = []
            if not inv.empty:
                type_history = sorted(inv[inv['物資類型'] == sel_type]['物資內容'].unique().tolist())
            if type_history:
                item_mode = st.radio(f"📝 {sel_type}名稱來源", ["從歷史紀錄選擇", "輸入新名稱"], horizontal=True)
            else:
                st.caption(f"💡 目前「{sel_type}」類尚無紀錄，請直接輸入新名稱。")
                item_mode = "輸入新名稱"

        with st.form("add_inv_form"):
            st.markdown(f"<div style='background:#f9f9f9; padding:10px; border-radius:10px; margin-bottom:10px;'><b>✍️ 步驟 2：填寫細節</b></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1.5, 1.5, 1])
            with c1:
                if donor_mode == "從歷史名單選擇":
                    final_donor = st.selectbox("捐贈單位/人", existing_donors) if existing_donors else ""
                else:
                    final_donor = st.text_input("輸入新單位/人", placeholder="例如：善心人士張先生")
            with c2:
                if item_mode == "從歷史紀錄選擇" and type_history:
                    final_item_name = st.selectbox(f"選擇{sel_type}品項", type_history)
                else:
                    final_item_name = st.text_input(f"輸入{sel_type}名稱", placeholder="例如：白米")
            with c3:
                qt = st.number_input("數量/金額", min_value=1)
            
            if st.form_submit_button("✅ 錄入庫存"):
                if not final_donor: st.error("❌ 請填寫捐贈者！")
                elif not final_item_name: st.error("❌ 請填寫物資名稱！")
                else:
                    new = {
                        "捐贈者": final_donor, "物資類型": sel_type, 
                        "物資內容": final_item_name, "總數量": qt, "捐贈日期": str(date.today())
                    }
                    if append_data("care_inventory", new, COLS_INV): 
                        st.success(f"已成功錄入：{final_donor} 捐贈 {final_item_name} x {qt}")
                        time.sleep(1); st.rerun()

    if not inv.empty:
        st.markdown("### 📊 庫存概況 (智慧卡片)")
        inv_summary = []
        for (item_name, donor_name), group in inv.groupby(['物資內容', '捐贈者']):
            total_in = group['總數量'].replace("","0").astype(float).sum()
            composite_name = f"{item_name} ({donor_name})"
            total_out = logs[logs['物資內容'] == composite_name]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            remain = total_in - total_out
            if remain > 0:
                m_type = group.iloc[0]['物資類型']
                icon_map = {"食物": "🍱", "日用品": "🧻", "輔具": "🦯", "急難救助金": "💰", "服務": "🧹"}
                icon = icon_map.get(m_type, "📦")
                pct = int((remain / total_in * 100)) if total_in > 0 else 0
                if pct < 0: pct = 0
                bar_color = "#8E9775"
                if remain <= 5: bar_color = "#D32F2F"
                elif pct < 30: bar_color = "#FBC02D"
                inv_summary.append({
                    "name": item_name, "donor": donor_name, "type": m_type, "icon": icon,
                    "in": int(total_in), "out": int(total_out), "remain": int(remain),
                    "pct": pct, "bar_color": bar_color
                })
        
        if not inv_summary:
            st.info("💡 目前無庫存 (或已全數發放完畢)")
        else:
            for i in range(0, len(inv_summary), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(inv_summary):
                        item = inv_summary[i + j]
                        with cols[j]:
                            warning_html = f'<div class="stock-warning">⚠️ 庫存告急！僅剩 {item["remain"]}</div>' if item["remain"] <= 5 else ""
                            st.markdown(f"""
<div class="stock-card">
<div class="stock-top">
<div class="stock-icon">{item['icon']}</div>
<div class="stock-info">
<div class="stock-name">{item['name']}</div>
<div class="stock-donor">{item['donor']}</div>
</div>
</div>
<div class="stock-stats">
<span>總入庫: {item['in']}</span>
<span>已發放: {item['out']}</span>
</div>
<div class="stock-bar-bg">
<div class="stock-bar-fill" style="width: {item['pct']}%; background-color: {item['bar_color']};"></div>
</div>
<div style="text-align:right; margin-top:5px; font-size:0.85rem; color:#888;">
剩餘庫存: <span style="font-size:1.2rem; color:{item['bar_color']}; font-weight:900;">{item['remain']}</span>
</div>
{warning_html}
</div>
""", unsafe_allow_html=True)

        with st.expander("🛠️ 進階管理：編輯原始庫存資料 (點擊展開)"):
            ed_i = st.data_editor(inv, use_container_width=True, num_rows="dynamic", key="inv_ed")
            if st.button("💾 儲存修改內容"): save_data(ed_i, "care_inventory")

# --- [插入位置：分頁 4：訪視] ---
# --- [分頁 4：訪視] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    
    # 1. 載入資料
    mems = load_data("care_members", COLS_MEM)
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    # 2. 計算即時庫存
    stock_map = {}
    if not inv.empty:
        for (item_name, donor_name), group in inv.groupby(['物資內容', '捐贈者']):
            total_in = group['總數量'].replace("","0").astype(float).sum()
            composite_name = f"{item_name} ({donor_name})"
            total_out = logs[logs['物資內容'] == composite_name]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            remain = int(total_in - total_out)
            if remain > 0: stock_map[composite_name] = remain

    # =========================================================
    # ✨ 功能 A：智慧發放建議 (已找回並升級)
    # =========================================================
    with st.expander("🤖 智慧發放建議 (點擊展開)", expanded=False):
        st.caption("💡 系統將根據「弱勢積分」推薦，並自動過濾「已領過」或「拒收」的個案。")
        
        if not stock_map:
            st.warning("目前無庫存物資可供分析。")
        else:
            suggest_item = st.selectbox("選擇要評估發放的物資：", list(stock_map.keys()))
            
            suggestion_list = []
            for index, row in mems.iterrows():
                p_name = row['姓名']
                p_tags = str(row['身分別'])
                p_refuse = str(row.get('拒絕物資', '')) # 取得該人的拒絕清單
                
                # 1. 檢查是否拒收 (呼叫我們寫好的字典判讀)
                is_conflict, _ = check_conflict(p_refuse, suggest_item)
                if is_conflict: continue # 如果拒收，直接跳過這個人

                # 2. 檢查是否領過
                has_received = False
                if not logs.empty:
                    check_log = logs[(logs['關懷戶姓名'] == p_name) & (logs['物資內容'] == suggest_item)]
                    if not check_log.empty:
                        total_rec = pd.to_numeric(check_log['發放數量'], errors='coerce').sum()
                        if total_rec > 0: has_received = True
                
                if not has_received:
                    # 3. 計算弱勢積分
                    score = 0
                    if "獨居" in p_tags: score += 3
                    if "低收" in p_tags: score += 3
                    if "中低收" in p_tags: score += 2
                    if "身障" in p_tags: score += 2
                    if "老人" in p_tags or "65歲以上" in str(row): score += 1
                    try:
                        if int(row.get('18歲以下子女', 0)) > 2: score += 2
                    except: pass
                    
                    suggestion_list.append({"姓名": p_name, "身分別": p_tags, "弱勢積分": score})
            
            # 顯示結果
            if suggestion_list:
                df_suggest = pd.DataFrame(suggestion_list).sort_values("弱勢積分", ascending=False).head(5)
                for _, row in df_suggest.iterrows():
                    st.markdown(f"""
                    <div style="background:white; padding:8px; border-left:5px solid #FF7043; margin-bottom:5px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                        <span style="font-weight:bold;">{row['姓名']}</span> 
                        <span style="color:#666; font-size:0.85rem;">(積分: {row['弱勢積分']} | {row['身分別']})</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("沒有符合的推薦對象 (大家都領過了，或是不適合該物資)。")

    st.markdown("---")

    # =========================================================
    # ✨ 功能 B：訪視與物資發放 (修復卡片顯示)
    # =========================================================
    st.markdown("#### 1. 選擇訪視對象")
    
    # 篩選選單
    all_tags = set()
    if not mems.empty:
        for s in mems['身分別'].astype(str):
            for t in s.split(','):
                if t.strip(): all_tags.add(t.strip())
    
    c_filter, c_person = st.columns([1, 2])
    with c_filter:
        sel_tag = st.selectbox("🌪️ 依身分別篩選", ["(全部顯示)"] + sorted(list(all_tags)))
    with c_person:
        filtered_mems = mems if sel_tag == "(全部顯示)" else mems[mems['身分別'].str.contains(sel_tag, na=False)]
        target_p = st.selectbox("👤 選擇關懷戶", filtered_mems['姓名'].tolist() if not filtered_mems.empty else [])

    # 編輯拒絕清單
    current_refuse = ""
    if target_p and not mems.empty:
        p_row_idx = mems[mems['姓名'] == target_p].index[0]
        current_refuse = str(mems.loc[p_row_idx].get('拒絕物資', ''))
        
        # 顯示簡易編輯器
        with st.expander(f"📝 編輯「{target_p}」的拒絕清單 (目前: {current_refuse})", expanded=False):
            c_edit, c_btn = st.columns([3, 1])
            new_refuse_input = c_edit.text_input("拒絕項目 (逗號隔開)", value=current_refuse)
            if c_btn.button("💾 更新"):
                mems.at[p_row_idx, '拒絕物資'] = new_refuse_input
                save_data(mems, "care_members")
                st.toast("✅ 備註已更新！"); time.sleep(1); st.rerun()

    st.markdown("#### 2. 填寫訪視內容與物資")
    
    # --- [新增程式碼] 鉤稽志工系統名單 ---
    # 1. 讀取志工名冊 (共用同一個 Spreadsheet，分頁名稱為 'members')
    vol_df = load_data("members", ["姓名", "志工分類"])
    
    # 2. 預設名單
    vol_list = ["呂宜政", "預設志工"]
    
    # 3. 篩選邏輯：志工分類包含 "關懷據點" (涵蓋週二、週三志工)
    if not vol_df.empty:
        # 確保志工分類轉為字串並進行篩選
        mask = vol_df['志工分類'].astype(str).str.contains("關懷據點", na=False)
        target_vols = vol_df[mask]['姓名'].unique().tolist()
        if target_vols:
            vol_list = sorted(target_vols) # 排序方便查找
    # ------------------------------------

    c1, c2 = st.columns(2)
    visit_who = c1.selectbox("執行志工", vol_list) 
    visit_date = c2.date_input("日期", value=date.today())
    
    st.write("📦 **庫存物資清單 (紅色 = 系統判定不宜)**")
    
    quantities = {}
    warning_msgs = []

    if not stock_map:
        st.info("💡 目前無庫存。")
    else:
        valid_items = sorted(stock_map.items())
        
        for i in range(0, len(valid_items), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(valid_items):
                    c_name, c_stock = valid_items[i+j]
                    
                    # 判讀是否衝突
                    is_bad, bad_reason = check_conflict(current_refuse, c_name)
                    
                    with cols[j]:
                        # 準備樣式
                        if is_bad:
                            bg = "#FFEBEE"
                            border = "#D32F2F"
                            warn_txt = f"<div style='color:#D32F2F; font-weight:bold; font-size:0.85rem; margin-bottom:5px;'>🚫 不宜：{bad_reason}</div>"
                        else:
                            bg = "#FFFFFF"
                            border = "#ddd"
                            warn_txt = ""

                        # --- 🔥 修正重點：使用變數來構建 HTML，解決縮排顯示錯誤的問題 ---
                        warn_txt = warn_txt or ""
                        card_html = (
                            f'<div style="background-color:{bg}; border:2px solid {border}; border-radius:10px; padding:15px;">'
                            f'{warn_txt}'
                            f'<div style="font-weight:900; font-size:1.1rem; margin-bottom:5px; color:#333;">{c_name}</div>'
                            f'<div style="color:#666; font-size:0.9rem; margin-bottom:10px;">庫存: {c_stock}</div>'
                            f'</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # 輸入框
                        qty = st.number_input(f"數量", min_value=0, max_value=c_stock, step=1, key=f"q_{c_name}")
                        quantities[c_name] = qty
                        
                        if qty > 0 and is_bad:
                            st.markdown(f"<span style='color:red; font-weight:bold;'>⚠️ 警告：包含{bad_reason}</span>", unsafe_allow_html=True)
                            warning_msgs.append(f"⚠️ {c_name}：包含個案拒絕的「{bad_reason}」")

    # 提交區塊
    note = st.text_area("訪視紀錄 / 備註", height=100)
    
    if warning_msgs:
        st.error("🚨 請注意：您選擇了個案不宜的物資！")
        for w in warning_msgs: st.write(w)
    
    if st.button("✅ 確認提交紀錄", type="primary", use_container_width=True):
        if not target_p:
            st.error("❌ 請選擇關懷戶")
        else:
            items_to_give = [(k, v) for k, v in quantities.items() if v > 0]
            new_logs = []
            if items_to_give:
                for item_name, amount in items_to_give:
                    new_logs.append({
                        "志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p,
                        "物資內容": item_name, "發放數量": amount, "訪視紀錄": note
                    })
            else:
                new_logs.append({
                    "志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p,
                    "物資內容": "(僅訪視)", "發放數量": 0, "訪視紀錄": note
                })
            
            try:
                client = get_client()
                sheet = client.open_by_key(SHEET_ID).worksheet("care_logs")
                
                rows_values = []
                for row in logs_to_add:
                    # 轉成 list
                    rows_values.append([str(row.get(c, "")).strip() for c in COLS_LOG])
                
                # 一次寫入多行 (最快)
                sheet.append_rows(rows_values)
                st.cache_data.clear()
                st.success("✅ 紀錄已儲存！"); time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"儲存失敗: {e}")

    # 歷史紀錄顯示 (保留原功能)
    if not logs.empty:
        st.markdown("#### 📝 最近訪視紀錄")
        st.dataframe(logs.sort_values('發放日期', ascending=False).head(10), use_container_width=True)

# --- [分頁 5：統計 (加入健康警示)] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計與個案查詢")
    logs, mems = load_data("care_logs", COLS_LOG), load_data("care_members", COLS_MEM)
    h_df = load_data("care_health", COLS_HEALTH)

    tab1, tab2, tab3 = st.tabs(["👤 個案詳細檔案", "🔍 健康特徵篩選", "📈 整體物資統計"])
    
    # --- Tab 1: 個案檔案 (含動態警示卡片) ---
    with tab1:
        if mems.empty: st.info("目前尚無關懷戶名冊資料")
        else:
            all_names = mems['姓名'].unique().tolist()
            target_name = st.selectbox("🔍 請選擇或輸入關懷戶姓名", all_names)
            if target_name:
                p_data = mems[mems['姓名'] == target_name].iloc[0]
                # ... (原有基本資料卡片代碼) ...
                age = calculate_age(p_data['生日'])
                try:
                    c = int(p_data['18歲以下子女']) if p_data['18歲以下子女'] else 0
                    a = int(p_data['成人數量']) if p_data['成人數量'] else 0
                    s = int(p_data['65歲以上長者']) if p_data['65歲以上長者'] else 0
                    total_fam = c + a + s
                except: total_fam = 0
                
                st.markdown(f"""
                <div style="background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid {GREEN}; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 1.8rem; font-weight: 900; color: #333;">{p_data['姓名']} <span style="font-size: 1rem; color: #666; background: #eee; padding: 2px 8px; border-radius: 10px;">{p_data['性別']} / {age} 歲</span></div>
                <div style="font-weight: bold; color: {PRIMARY}; border: 2px solid {PRIMARY}; padding: 5px 15px; border-radius: 20px;">{p_data['身分別']}</div>
                </div>
                <div><b>📞 電話：</b> {p_data['電話']} | <b>📍 地址：</b> {p_data['地址']}</div>
                </div>
                """, unsafe_allow_html=True)

                # 🔥 動態健康警示區
                if not h_df.empty:
                    p_health = h_df[h_df['姓名'] == target_name]
                    if not p_health.empty:
                        last_h = p_health.sort_values("評估日期").iloc[-1]
                        st.markdown("### 🩺 健康與風險評估摘要")
                        st.caption(f"最近評估日期：{last_h['評估日期']}")
                        
                        # 收集所有異常項目
                        alerts = []
                        
                        # 1. 自殺風險
                        if last_h.get('有自殺意念') == '是':
                            alerts.append({'icon': '🚨', 'title': '自殺風險', 'val': '有自殺意念', 'type': 'danger'})
                        
                        # 2. 營養/情緒
                        if '營養不良' in str(last_h.get('營養狀態', '')):
                            alerts.append({'icon': '📉', 'title': '營養狀態', 'val': last_h['營養狀態'], 'type': 'danger'})
                        if '重度' in str(last_h.get('情緒狀態', '')):
                            alerts.append({'icon': '⛈️', 'title': '情緒狀態', 'val': last_h['情緒狀態'], 'type': 'danger'})
                            
                        # 3. ICOPE 功能異常 (洗牙、視力、聽力)
                        if last_h.get('今年洗牙') == '否':
                            alerts.append({'icon': '🦷', 'title': '口腔保健', 'val': '半年未洗牙', 'type': 'warning'})
                        if last_h.get('半年內跌倒紀錄') == '是':
                            alerts.append({'icon': '🤕', 'title': '跌倒風險', 'val': '半年內曾跌倒', 'type': 'warning'})
                        if last_h.get('視力困難') == '是':
                            alerts.append({'icon': '👓', 'title': '視力異常', 'val': '自覺視力困難', 'type': 'warning'})
                        if last_h.get('聽力困難') == '是':
                            alerts.append({'icon': '👂', 'title': '聽力異常', 'val': '自覺聽力困難', 'type': 'warning'})
                        if last_h.get('記憶力減退') == '是':
                            alerts.append({'icon': '🧠', 'title': '認知異常', 'val': '記憶明顯減退', 'type': 'warning'})
                            
                        # 4. 膀胱
                        if last_h.get('頻尿漏尿困擾') in ['中等', '嚴重']:
                            alerts.append({'icon': '🚽', 'title': '泌尿困擾', 'val': '頻尿/漏尿', 'type': 'warning'})

                        # 🔥 渲染卡片：使用 st.columns 自動排版
                        if alerts:
                            cols_per_row = 3
                            for i in range(0, len(alerts), cols_per_row):
                                row_alerts = alerts[i:i+cols_per_row]
                                cols = st.columns(cols_per_row)
                                for idx, alert in enumerate(row_alerts):
                                    # 設定顏色樣式
                                    css_cls = "h-card-danger" if alert['type'] == 'danger' else "h-card-warning"
                                    with cols[idx]:
                                        st.markdown(f"""
                                        <div class="health-dashboard-card {css_cls}">
                                            <div class="h-card-icon">{alert['icon']}</div>
                                            <div class="h-card-content">
                                                <div class="h-card-title">{alert['title']}</div>
                                                <div class="h-card-value" style="font-size:1.1rem;">{alert['val']}</div>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="health-dashboard-card h-card-safe">
                                <div class="h-card-icon">✅</div>
                                <div class="h-card-content">
                                    <div class="h-card-title">健康狀況</div>
                                    <div class="h-card-value">目前無明顯異常指標</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

    # --- Tab 2: 健康特徵篩選 (新功能) ---
    with tab2:
        st.markdown("### 🔍 依健康問卷結果篩選")
        st.caption("例如：找出「沒洗牙」或「心情不好」的長者")
        
        if h_df.empty:
            st.warning("尚無健康評估資料")
        else:
            # 1. 選擇要篩選的題目 (Column)
            # 排除掉姓名等個資，只留問卷項
            filter_options = [c for c in COLS_HEALTH if c not in ['姓名', '身分證字號', '評估日期', '身高', '體重']]
            target_col = st.selectbox("選擇篩選項目", filter_options, index=filter_options.index('今年洗牙') if '今年洗牙' in filter_options else 0)
            
            # 2. 選擇該題目中的答案 (Value)
            available_vals = h_df[target_col].unique().tolist()
            target_val = st.selectbox(f"選擇「{target_col}」的數值", available_vals)
            
            # 3. 執行篩選
            result_df = h_df[h_df[target_col] == target_val]
            st.markdown(f"#### 篩選結果：共 {len(result_df)} 人")
            
            if not result_df.empty:
                # 顯示簡易名單
                st.dataframe(result_df[['姓名', '評估日期', target_col, '電話', '地址']].merge(mems[['姓名', '電話', '地址']], on='姓名', how='left'), use_container_width=True)
            else:
                st.info("沒有符合條件的個案。")

                # 機敏資料
                if not st.session_state.unlock_details:
                    st.info("🔒 詳細個資已隱藏。")
                    c_pwd, c_btn = st.columns([2, 1])
                    with c_pwd: pwd_stat = st.text_input("請輸入密碼解鎖個資", type="password", key="unlock_stat_pwd")
                    with c_btn:
                        if st.button("🔓 解鎖查看"):
                            if pwd_stat == st.secrets["admin_password"]:
                                st.session_state.unlock_details = True; st.rerun()
                            else: st.error("❌ 密碼錯誤")
                else:
                    if st.button("🔒 隱藏機敏資料"): st.session_state.unlock_details = False; st.rerun()
                    st.markdown(f"""
<div style="background-color: #FFF8E1; padding: 20px; border-radius: 15px; border: 1px dashed #FFB74D; margin-bottom: 20px;">
<div style="font-weight:bold; color:#F57C00; margin-bottom:10px;">⚠️ 機敏個資區域 (已解鎖)</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
<div><b>🆔 身分證：</b> {p_data['身分證字號']}</div>
<div><b>🎂 生日：</b> {p_data['生日']}</div>
</div>
<hr style="border-top: 1px dashed #ccc;">
<div style="margin-top: 10px; color: #555;">
<b>🏠 家庭結構明細：</b> 18歲以下 <b>{p_data['18歲以下子女']}</b> 人，成人 <b>{p_data['成人數量']}</b> 人，65歲以上 <b>{p_data['65歲以上長者']}</b> 人
</div>
<div style="margin-top: 10px; color: #D32F2F;">
<b>🚨 緊急聯絡人：</b> {p_data['緊急聯絡人']} ({p_data['緊急聯絡人電話']})
</div>
</div>
""", unsafe_allow_html=True)
                
                st.markdown("### 🤝 歷史訪視紀錄")
                p_logs = logs[logs['關懷戶姓名'] == target_name]
                if p_logs.empty: st.info("尚無訪視紀錄。")
                else:
                    p_logs = p_logs.sort_values("發放日期", ascending=False)
                    for idx, row in p_logs.iterrows():
                        tag_class = "only" if row['物資內容'] == "(僅訪視)" else ""
                        item_display = row['物資內容'] if row['物資內容'] == "(僅訪視)" else f"{row['物資內容']} x {row['發放數量']}"
                        st.markdown(f"""
<div class="visit-card">
<div class="visit-header">
<span class="visit-date">📅 {row['發放日期']}</span>
<span class="visit-volunteer">👮 志工：{row['志工']}</span>
</div>
<div style="margin-bottom:8px;">
<span class="visit-tag {tag_class}">{item_display}</span>
</div>
<div class="visit-note">{row['訪視紀錄']}</div>
</div>
""", unsafe_allow_html=True)

    with tab2:
        inv = load_data("care_inventory", COLS_INV)
        if not inv.empty:
            inv['qty'] = pd.to_numeric(inv['總數量'], errors='coerce').fillna(0)
            st.markdown("### 🎁 捐贈來源與物資分析")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🏆 愛心捐贈芳名錄")
                donor_stat = inv.groupby('捐贈者')['qty'].sum().reset_index().sort_values('qty', ascending=False)
                fig_donor = px.pie(donor_stat, values='qty', names='捐贈者', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_donor, use_container_width=True)
            with c2:
                st.markdown("#### 📦 物資種類結構")
                fig_sun = px.sunburst(inv, path=['物資類型', '物資內容'], values='qty', color='物資類型', color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig_sun, use_container_width=True)
            st.markdown("#### 📝 歷年捐贈明細總表")
            st.dataframe(inv, use_container_width=True)
        else: st.info("目前尚無捐贈紀錄")
