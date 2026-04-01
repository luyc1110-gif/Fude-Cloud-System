import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from supabase import create_client, Client
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
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background-color: #FFFFFF !important; border-radius: 10px; padding: 5px;
}}
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input, .stTextArea textarea {{
    background-color: #F8F9FA !important; color: #000000 !important;
    border: 2px solid #E0E0E0 !important; border-radius: 12px !important; font-weight: 700 !important;
}}

/* 確保下拉選單打字時文字可見 */
div[data-baseweb="select"] input {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
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

/* 1. 危險 (紅) - 高風險 */
.h-card-danger {{
    background: linear-gradient(135deg, #FF5252 0%, #C62828 100%);
    border: 1px solid #B71C1C;
}}

/* 2. 警告 (橘) - 中風險 */
.h-card-warning {{
    background: linear-gradient(135deg, #FFB74D 0%, #E65100 100%);
    border: 1px solid #EF6C00;
}}

/* 3. [新增] 提醒 (金黃) - 輕微/預防性 */
.h-card-notice {{
    background: linear-gradient(135deg, #FDD835 0%, #F9A825 100%);
    border: 1px solid #F57F17;
    color: #333 !important; /* 黃色背景配深色字比較清楚，若想維持白色字可移除這行 */
}}
.h-card-notice .h-card-value, .h-card-notice .h-card-title, .h-card-notice .h-card-icon {{
    color: #333 !important; /* 強制深色字 */
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

/* 🎨 [可調整] 標籤式單選按鈕 (Radio Tags) */
div[role="radiogroup"] {{
    gap: 10px;
    display: flex;
    flex-wrap: wrap;
}}
div[role="radiogroup"] label {{
    background-color: #FFFFFF;    /* 🎨 未選中時的背景顏色 */
    border: 1px solid #aaa;       /* 🎨 邊框顏色 */
    border-radius: 50px !important; /* 🔥 變成橢圓形的關鍵 (原本是矩形) */
    padding: 5px 20px !important;   /* 🔥 調整標籤的大小 (內距) */
    transition: all 0.2s;
    margin-right: 8px;
}}
div[role="radiogroup"] label:hover {{
    border-color: {GREEN};
    background-color: #F1F8E9;
}}
div[role="radiogroup"] label[data-checked="true"] {{
    background-color: {GREEN} !important; /* 🎨 選中時的背景顏色 (綠色) */
    color: white !important;              /* 🎨 選中時的文字顏色 */
    border-color: {GREEN} !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}}

/* 題目文字樣式 */
.q-text {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #333;
    margin-bottom: 8px;
    display: block;
}}
.q-help {{
    font-size: 0.85rem;
    color: #666;
    margin-bottom: 5px;
}}

/* 🎨 可調整：優化 Streamlit 的 Radio Button 變成按鈕標籤狀 */
/* 注意：這會影響全域的橫向 radio，若只想影響特定區域需更精細的 CSS selector，但在此範例中統一風格較佳 */
div[data-testid="stRadio"] > div {{
    gap: 10px;
}}
div[role="radiogroup"] label {{
    background-color: #F1F3F4;
    padding: 8px 16px;
    border-radius: 20px;
    border: 1px solid transparent;
    transition: all 0.2s;
}}
div[role="radiogroup"] label[data-checked="true"] {{
    background-color: {GREEN} !important; /* 🎨 可調整：選中時的背景色 */
    color: white !important;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}}
div[role="radiogroup"] label:hover {{
    border-color: {GREEN};
    background-color: #E8F5E9;
}}

/* 🎨 [可調整] 分頁籤 (Tabs) 樣式 */
button[data-baseweb="tab"] {{
    border-radius: 20px !important; /* 🔥 讓分頁籤變圓 */
    border: 1px solid #eee !important;
    background-color: white !important;
    margin-right: 5px !important;
    padding: 4px 15px !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    background-color: {PRIMARY} !important; /* 🎨 選中分頁的顏色 */
    color: white !important;
    border: none !important;
}}

/* 滑桿區塊優化 */
div[data-testid="stSlider"] {{
    padding-top: 10px;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯 (更新欄位定義)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者", "拒絕物資", "人際關係"] 

# 更新資料定義：包含 Word 檔所有題項
# =========================================================
COLS_HEALTH = [
    # 識別
    "姓名", "身分證字號", "評估日期",
    
    # 一、前測問卷及身體狀況
    "收縮壓", "舒張壓", "心跳", "身高", "體重", "BMI", "右手握力", "左手握力",
    "Q1_性別", "Q2_出生年月日", "Q3_年齡", # 這些通常自動帶入
    "Q4_教育程度", "Q5_婚姻狀況", "Q6_居住狀況", "Q7_居住樓層", "Q8_信仰", "Q9_工作狀態", "Q10_經濟狀況",
    "Q11_主要照顧者", "Q12_過去疾病史", 
    "使用行走輔具", "使用聽力輔具", "使用視力輔具", "半年內跌倒紀錄", 
    "服用助眠藥", "服用心血管藥物", "喝乳品習慣", "使用漏尿墊", "男性小便斷續",

    # 二、ICOPE
    "ICOPE_1_記憶減退", "ICOPE_2_跌倒風險", "ICOPE_3_體重減輕", "ICOPE_4_食慾不佳", 
    "ICOPE_5_視力困難", "ICOPE_6_曾驗光", "ICOPE_7_曾洗牙", 
    "ICOPE_8_聽力困擾", # 整合題
    "ICOPE_9_心情低落", "ICOPE_10_減少社交",
    
    # 三、BSRS-5
    "BSRS_1_睡眠", "BSRS_2_緊張", "BSRS_3_動怒", "BSRS_4_憂鬱", "BSRS_5_自卑", "BSRS_6_自殺",
    "BSRS_總分", "BSRS_狀態",

    # 四、MNA
    "MNA_A_食量", "MNA_B_體重", "MNA_C_活動", "MNA_D_創傷", "MNA_E_精神", "MNA_F_BMI",
    "MNA_篩檢分數", "MNA_狀態",

    # 五、WHO-5
    "WHO5_1_開朗", "WHO5_2_平靜", "WHO5_3_活力", "WHO5_4_休息", "WHO5_5_興趣",
    "WHO5_總分",

    # 六、膀胱 & IIQ-7
    "膀胱_1_頻尿", "膀胱_2_尿急", "膀胱_3_用力漏尿", "膀胱_4_少量漏尿", "膀胱_5_解尿困難", "膀胱_6_下腹痛",
    "IIQ7_1_家事", "IIQ7_2_健身", "IIQ7_3_娛樂", "IIQ7_4_開車搭車", "IIQ7_5_社交", "IIQ7_6_情緒", "IIQ7_7_挫折",

    # 七、WHOQOL-BREF
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
# 2) 資料庫核心 (Supabase)
# =========================================================
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=1)
def load_data(sheet_name, target_cols=None):
    try:
        supabase = get_supabase_client()
        response = supabase.table(sheet_name).select("*").execute()
        df = pd.DataFrame(response.data)
        if df.empty: return pd.DataFrame(columns=target_cols if target_cols else [])
        if target_cols:
            for c in target_cols:
                if c not in df.columns: df[c] = ""
        return df
    except Exception as e:
        st.error(f"資料庫讀取失敗：{e}")
        return pd.DataFrame(columns=target_cols if target_cols else [])

# 🔥 [新增] 卡片式標籤題目 (完全符合草圖需求)
def ui_card_radio(label, options, key=None, help_text=None, index=None):
    """
    產生一個帶邊框的卡片，內含題目與橢圓形標籤選項
    """
    # 🎨 border=True 會產生如草圖般的圓角矩形外框
    with st.container(border=True): 
        # 顯示題目
        st.markdown(f'<span class="q-text">{label}</span>', unsafe_allow_html=True)
        if help_text:
            st.markdown(f'<span class="q-help">{help_text}</span>', unsafe_allow_html=True)
        
        # 顯示選項 (horizontal=True 讓選項橫向排列)
        return st.radio(label, options, key=key, index=index, horizontal=True, label_visibility="collapsed")

# 🔥 [新增] 卡片式滑桿題目 (含程度註記)
def ui_card_slider(label, min_v, max_v, key=None, help_text=None, annotations=None):
    with st.container(border=True):
        st.markdown(f'<span class="q-text">{label}</span>', unsafe_allow_html=True)
        if help_text:
            st.markdown(f'<span class="q-help">{help_text}</span>', unsafe_allow_html=True)
        
        val = st.slider(label, min_v, max_v, key=key, label_visibility="collapsed")
    
    # 顯示滑桿下方的程度文字
    if annotations:
        current_anno = annotations.get(val, f"{val} 分")
        st.caption(f"📍 目前選擇程度：**{current_anno}**")
    
    return val

def append_data(sheet_name, row_dict, col_order=None):
    try:
        supabase = get_supabase_client()
        clean_data = {k: str(v).strip() for k, v in row_dict.items() if str(v).strip() and str(v).strip() != 'nan'}
        supabase.table(sheet_name).insert(clean_data).execute()
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"新增失敗：{e}")
        return False

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
# 🌟 主檔 (Master Data) 橋接邏輯 (單一真實來源版)
# =========================================================
COLS_MASTER = ['姓名', '身分證字號', '性別', '出生年月日', '電話', '地址', '緊急聯絡人', '緊急聯絡電話', '身分_志工', '身分_關懷戶', '身分_據點長輩', '志工分類', '關懷_身分別', '同住_18歲以下', '同住_成人', '同住_65歲以上', '拒絕物資', '人際關係']

def get_care_members():
    df = load_data("master_residents")
    if df.empty: return pd.DataFrame(columns=COLS_MEM)
    if '身分_關懷戶' not in df.columns: df['身分_關懷戶'] = ""
    
    care_df = df[df['身分_關懷戶'].astype(str).str.upper() == 'TRUE'].copy()
    care_df = care_df.rename(columns={
        '出生年月日': '生日', '關懷_身分別': '身分別', '同住_18歲以下': '18歲以下子女', 
        '同住_成人': '成人數量', '同住_65歲以上': '65歲以上長者'
    })
    for c in COLS_MEM:
        if c not in care_df.columns: care_df[c] = ""
    return care_df[COLS_MEM].reset_index(drop=True)

def update_master_fields(uid, update_dict):
    try:
        supabase = get_supabase_client()
        master = load_data("master_residents")
        existing = master[master['身分證字號'] == uid]
        if not existing.empty and 'id' in existing.columns:
            record_id = int(existing.iloc[0]['id'])
            map_dict = {'生日': '出生年月日', '身分別': '關懷_身分別', '18歲以下子女': '同住_18歲以下', '成人數量': '同住_成人', '65歲以上長者': '同住_65歲以上'}
            final_update = {map_dict.get(k, k): str(v) for k, v in update_dict.items()}
            supabase.table("master_residents").update(final_update).eq("id", record_id).execute()
            load_data.clear()
            return True
        return False
    except: return False

def add_or_update_care_member_to_master(new_data):
    uid = new_data.get('身分證字號', '').upper()
    if not uid or uid == 'NAN':
        uid = f"TEMP_{new_data.get('姓名', '').strip()}_{new_data.get('電話', '').strip()}"
        new_data['身分證字號'] = uid
        
    map_dict = {'生日': '出生年月日', '身分別': '關懷_身分別', '18歲以下子女': '同住_18歲以下', '成人數量': '同住_成人', '65歲以上長者': '同住_65歲以上'}
    master_data = {map_dict.get(k, k): str(v) for k, v in new_data.items()}
    master_data['身分_關懷戶'] = 'TRUE'

    try:
        supabase = get_supabase_client()
        existing = supabase.table("master_residents").select("id").eq("身分證字號", uid).execute()
        if existing.data:
            record_id = existing.data[0]['id']
            supabase.table("master_residents").update(master_data).eq("id", record_id).execute()
        else:
            for c in COLS_MASTER:
                if c not in master_data: master_data[c] = "FALSE" if "身分_" in c else ""
            supabase.table("master_residents").insert(master_data).execute()
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}")
        return False

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
    mems, logs = get_care_members(), load_data("care_logs", COLS_LOG)
    
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

        # =========================================================
        # 🔥 [新增] 社區高風險預警看板 (自動抓取最新一筆健康紀錄)
        # =========================================================
        st.markdown("---")
        st.markdown(f"<h3 style='color: {PRIMARY};'>🚨 智慧高風險預警雷達</h3>", unsafe_allow_html=True)
        
        h_df = load_data("care_health", COLS_HEALTH)
        
        if not h_df.empty:
            # 1. 抓取每個人「最新的一筆」紀錄
            h_df['dt'] = pd.to_datetime(h_df['評估日期'], errors='coerce')
            latest_health = h_df.dropna(subset=['dt']).sort_values('dt').groupby('身分證字號').last().reset_index()
            
            # 2. 建立警示名單容器
            alert_lists = {
                "心情_重度": [], "心情_中度": [], "心情_輕度": [],
                "營養_異常": [], "認知_異常": [], "跌倒_高風險": []
            }
            
            # 3. 依據您的 COLS_HEALTH 進行精準判定
            for _, row in latest_health.iterrows():
                name = str(row.get('姓名', '未知'))
                
                # --- A. BSRS-5 心情溫度計 ---
                bsrs_stat = str(row.get('BSRS_狀態', ''))
                bsrs_score = str(row.get('BSRS_總分', ''))
                if "重度" in bsrs_stat: alert_lists["心情_重度"].append(f"{name} ({bsrs_score}分)")
                elif "中度" in bsrs_stat: alert_lists["心情_中度"].append(f"{name} ({bsrs_score}分)")
                elif "輕度" in bsrs_stat: alert_lists["心情_輕度"].append(f"{name} ({bsrs_score}分)")
                    
                # --- B. 營養與進食 (MNA & ICOPE) ---
                mna_stat = str(row.get('MNA_狀態', ''))
                icope_weight = str(row.get('ICOPE_3_體重減輕', ''))
                icope_eat = str(row.get('ICOPE_4_食慾不佳', ''))
                if "不良" in mna_stat or "風險" in mna_stat or icope_weight == "是" or icope_eat == "是":
                    alert_lists["營養_異常"].append(name)
                    
                # --- C. 認知與社交 (ICOPE) ---
                icope_mem = str(row.get('ICOPE_1_記憶減退', ''))
                if icope_mem == "是":
                    alert_lists["認知_異常"].append(name)
                    
                # --- D. 跌倒風險 (ICOPE) ---
                icope_fall = str(row.get('ICOPE_2_跌倒風險', ''))
                if icope_fall == "是":
                    alert_lists["跌倒_高風險"].append(name)

            # 4. 渲染警示看板
            ca1, ca2, ca3 = st.columns(3)
            
            # -- 💔 警示卡 1：心情溫度計 --
            with ca1:
                st.markdown("""<div style="background:#FFF3E0; border-left:5px solid #E65100; padding:15px; border-radius:10px; margin-bottom:15px; height:100%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <h4 style="color:#E65100; margin-top:0; font-weight:900;">💔 心情溫度預警</h4>""", unsafe_allow_html=True)
                
                if alert_lists["心情_重度"]:
                    st.markdown(f"<div style='color:#D32F2F; font-weight:bold; margin-bottom:5px;'>🔴 重度風險 ({len(alert_lists['心情_重度'])}人)</div>", unsafe_allow_html=True)
                    st.markdown(f"**{', '.join(alert_lists['心情_重度'])}**")
                if alert_lists["心情_中度"]:
                    st.markdown(f"<div style='color:#EF6C00; font-weight:bold; margin-top:10px; margin-bottom:5px;'>🟠 中度風險 ({len(alert_lists['心情_中度'])}人)</div>", unsafe_allow_html=True)
                    st.markdown(f"{', '.join(alert_lists['心情_中度'])}")
                if alert_lists["心情_輕度"]:
                    st.markdown(f"<div style='color:#F9A825; font-weight:bold; margin-top:10px; margin-bottom:5px;'>🟡 輕度關注 ({len(alert_lists['心情_輕度'])}人)</div>", unsafe_allow_html=True)
                    st.caption(f"{', '.join(alert_lists['心情_輕度'])}")
                    
                if not any([alert_lists["心情_重度"], alert_lists["心情_中度"], alert_lists["心情_輕度"]]):
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>✅ 目前無長輩有心情風險</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -- 🍲 警示卡 2：營養風險 --
            with ca2:
                st.markdown("""<div style="background:#E8F5E9; border-left:5px solid #2E7D32; padding:15px; border-radius:10px; margin-bottom:15px; height:100%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <h4 style="color:#2E7D32; margin-top:0; font-weight:900;">🍲 營養不良預警</h4>""", unsafe_allow_html=True)
                
                if alert_lists["營養_異常"]:
                    # set() 用來去重，避免同時觸發 MNA 與 ICOPE 導致名字出現兩次
                    st.markdown(f"<div style='color:#D32F2F; font-weight:bold; margin-bottom:5px;'>🚨 需注意名單 ({len(set(alert_lists['營養_異常']))}人)</div>", unsafe_allow_html=True)
                    st.markdown(f"**{', '.join(set(alert_lists['營養_異常']))}**")
                else:
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>✅ 目前無長輩有營養風險</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -- 🧠 警示卡 3：認知與防跌 --
            with ca3:
                st.markdown("""<div style="background:#FCE4EC; border-left:5px solid #C2185B; padding:15px; border-radius:10px; margin-bottom:15px; height:100%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <h4 style="color:#C2185B; margin-top:0; font-weight:900;">🧠 認知與防跌預警</h4>""", unsafe_allow_html=True)
                
                if alert_lists["認知_異常"]:
                    st.markdown(f"<div style='color:#E65100; font-weight:bold; margin-bottom:5px;'>🤯 記憶明顯減退 ({len(alert_lists['認知_異常'])}人)</div>", unsafe_allow_html=True)
                    st.markdown(f"{', '.join(alert_lists['認知_異常'])}")
                    
                if alert_lists["跌倒_高風險"]:
                    st.markdown(f"<div style='color:#D32F2F; font-weight:bold; margin-top:10px; margin-bottom:5px;'>⚠️ 跌倒高風險 ({len(alert_lists['跌倒_高風險'])}人)</div>", unsafe_allow_html=True)
                    st.markdown(f"**{', '.join(alert_lists['跌倒_高風險'])}**")
                    
                if not alert_lists["認知_異常"] and not alert_lists["跌倒_高風險"]:
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>✅ 目前無認知或跌倒風險</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("尚無健康評估紀錄，累積資料後系統將自動產出高風險預警。")
# --- [分頁 1：名冊] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = get_care_members()
    
    # === 🔥 修改開始：新增「最新 3 筆」卡片顯示區 ===
    st.markdown("### 🆕 最新建檔關懷戶")
    if not df.empty:
        # 1. 取出最後 3 筆 (假設最新資料在最下面)，並反轉順序讓最新的排第一個
        recent_mems = df.tail(3).iloc[::-1]
        
        cols = st.columns(3)
        for idx, (i, row) in enumerate(recent_mems.iterrows()):
            with cols[idx]:
                # 使用簡單的卡片樣式
                st.markdown(f"""
                <div style="
                    background: white; 
                    border-radius: 12px; 
                    padding: 15px; 
                    border-left: 5px solid #8E9775; 
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: 900; color: #333;">{row['姓名']}</div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">
                        {row.get('性別','')} / {calculate_age(row.get('生日',''))} 歲
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("尚無名冊資料")
    st.markdown("---")
    
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
                    if add_or_update_care_member_to_master(new):
                        st.success("✅ 已新增！"); time.sleep(1); st.rerun()

# =========================================================
# 🔥 Page: Health (分頁優化、即時計算、無預設值)
# =========================================================
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 綜合健康評估")
    h_df, m_df = load_data("care_health", COLS_HEALTH), get_care_members()
    
    with st.expander("➕ 新增/更新 評估紀錄 (請依序填寫)", expanded=True):
        sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"], index=None, placeholder="請選擇...")
        
        # 0. 預載資料
        p_info = {}
        if sel_n and not m_df.empty:
            p_row = m_df[m_df['姓名'] == sel_n].iloc[0]
            p_info['gender'] = p_row['性別']
            p_info['dob'] = p_row['生日']
            p_info['age'] = calculate_age(p_row['生日'])
            p_info['floor'] = extract_floor(p_row['地址'])
            
            st.info(f"✅ 系統已自動帶入個案基本資料：{p_info['gender']}性 / {p_info['age']}歲 / {p_info['dob']} / 推測住 {p_info['floor']}")

        eval_date = st.date_input("填表日期", value=date.today())

        # 使用 Tabs，並加上 Emoji 增加辨識度
        t1, t2, t3, t4, t5, t6, t7 = st.tabs([
            "🟢一、基本&身體", "🔵二、ICOPE", "🟡三、BSRS-5", "🟠四、MNA", "🔴五、WHO-5", "🟣六、膀胱", "⚪七、WHOQOL"
        ])

        # 初始化跨分頁變數 (避免未填寫時報錯)
        icope_eat_val = None
        icope_weight_val = None
        bmi_val = 0.0

        # --- 一、前測問卷及身體狀況 ---
        with t1:
            st.markdown("### 📝 第一部分：基本資料與身體狀況")
                
            # Q1~Q3 已自動帶入
            st.caption("1.性別, 2.生日, 3.年齡 已自動帶入")

            c1, c2, c3 = st.columns(3)
            edu = ui_card_radio("4. 您的教育程度是？", ["不識字", "識字未就學", "國小", "國中", "高中", "大專以上"], key="q4_edu", index=None)
            marry = ui_card_radio("5. 您的婚姻狀況是？", ["未婚", "已婚", "鰥寡", "分居", "離異", "其他"], key="q5_marry", index=None)
                
            if p_info.get('floor', '無法推斷') == '無法推斷':
                floor_final = ui_card_radio("7. 您目前住幾樓？", ["一樓", "二樓以上無電梯", "二樓以上有電梯"], key="q7_floor", index=None)
            else:
                floor_final = p_info['floor']
                c3.success(f"7. 住幾樓：{floor_final} (已帶入)")
                    
            c4, c5 = st.columns(2)
            live_st = ui_card_radio("6. 您目前居住狀況是？", ["獨居", "榮家", "僅與配偶居", "與家人居(含配偶)", "與家人居(不含配偶)", "與親友居", "機構", "其他"], key="q6_live", index=None)
            relig = ui_card_radio("8. 您的信仰是？", ["無", "佛教", "道教", "基督教", "回教", "天主教", "其他"], key="q8_relig", index=None)
                
            c6, c7, c8 = st.columns(3)
            work = ui_card_radio("9. 您目前是否有工作？", ["退休", "家管", "目前有工作", "待業中"], key="q9_work", index=None)
            econ = ui_card_radio("10. 您的經濟狀況是？", ["富裕", "小康", "貧窮", "其他"], key="q10_econ", index=None)
            caregiver = c8.multiselect("11. 誰是主要照顧您的人？(可複選)", ["自己", "配偶", "子女", "看護", "其他"])
                
                # === 🔥 修改開始：動態疾病選項邏輯 ===
                # 1. 定義系統預設的基本選項
            base_diseases = ["無", "糖尿病", "高血壓", "高血脂", "心臟病", "腎臟病", "肝炎", "關節炎", "骨質疏鬆", "氣喘", "癌症", "其他"]
            history_diseases = set()
            if not h_df.empty and 'Q12_過去疾病史' in h_df.columns:
                for record in h_df['Q12_過去疾病史'].dropna().astype(str):
                    items = [x.strip() for x in record.split(',') if x.strip()]
                    history_diseases.update(items)

            all_options = sorted(list(set(base_diseases) | history_diseases))
            if "其他" in all_options: all_options.remove("其他")
            all_options.append("其他")

            dis_hist = st.multiselect("12. 您過去是否有以下疾病？(可複選)", all_options)

# 初始化變數 (這行很重要，避免沒選其他時報錯)
            other_disease_text = "" 
            if "其他" in dis_hist:
    # 因為移除了 st.form，這裡會即時顯示
                other_disease_text = st.text_input("↳ 請輸入疾病名稱 (輸入後儲存，下次將自動變為選項)", placeholder="例如：痛風...")
                # === 🔥 修改結束 ===

            st.markdown("---")
            st.markdown("#### 🩺 身體狀況量測")
                
                # 排版優化：使用 Container 區分不同類型量測
            with st.container():
                st.markdown("**A. 生命徵象**")
                bp1, bp2, hr = st.columns(3)
                sys_p = bp1.number_input("血壓(收縮壓)", min_value=0, step=1, value=None)
                dia_p = bp2.number_input("血壓(舒張壓)", min_value=0, step=1, value=None)
                hr_p = hr.number_input("心跳數", min_value=0, step=1, value=None)

            with st.container():
                st.markdown("**B. 體位測量 (即時計算BMI)**")
                h1, w1, b_res = st.columns(3)
                h_v = h1.number_input("身高(cm)", min_value=0.0, step=0.1, value=None)
                w_v = w1.number_input("體重(kg)", min_value=0.0, step=0.1, value=None)
                    
                if h_v and w_v and h_v > 0:
                    bmi_val = round(w_v/((h_v/100)**2), 1)
                    b_res.metric("BMI", bmi_val)
                else:
                    b_res.info("輸入身高體重後顯示")

            with st.container():
                st.markdown("**C. 握力與輔具**")
                g1, g2 = st.columns(2)
                grip_r = g1.number_input("右手握力(kg)", step=0.1, value=None)
                grip_l = g2.number_input("左手握力(kg)", step=0.1, value=None)
                    
                st.caption("請勾選目前使用的輔具：")
                aa1, aa2, aa3, aa4 = st.columns(4)
                aid_walk = aa1.checkbox("7. 使用行走輔具")
                aid_hear = aa2.checkbox("8. 使用聽力輔具")
                aid_eye = aa3.checkbox("9. 使用視力輔具(眼鏡)")
                fall_rec = aa4.radio("10. 最近半年有無跌倒？", ["有", "沒有"], index=None)

            with st.container():
                st.markdown("**D. 其他習慣**")
                d1, d2, d3 = st.columns(3)
                med_sleep = ui_card_radio("11. 服用助眠藥?", ["有", "沒有"], index=None)
                med_cv = ui_card_radio("12. 服用心血管藥?", ["有", "沒有"], index=None)
                milk_habit = ui_card_radio("13. 喝乳品習慣?", ["有", "沒有"], index=None)

                    # 性別邏輯題
                if p_info.get('gender') == '女':
                    pad_use = ui_card_radio("14. (女性) 使用漏尿墊/護墊?", ["有", "沒有"], index=None)
                    male_urine = "不適用"
                elif p_info.get('gender') == '男':
                    male_urine = ui_card_radio("15. (男性) 小便斷續不連貫?", ["有", "沒有"], index=None)
                    pad_use = "不適用"
                else:
                    pad_use = "未填"
                    male_urine = "未填"

            # --- 二、ICOPE ---
        with t2:
            st.markdown("### 🧠 第二部分：高齡功能 ICOPE")
            
            c_i1, c_i2 = st.columns(2)
            icope_mem = ui_card_radio("1. 最近一年是否有記憶明顯減退?", ["否", "是"], key="ic_1", index=None)
            icope_fall = ui_card_radio("2. 過去一年曾跌倒/擔心跌倒/需扶東西才能從椅子站起?", ["否", "是"], key="ic_2", index=None)
            
            st.markdown("---")
            c_i3, c_i4 = st.columns(2)
            icope_weight_val = ui_card_radio("3. 過去三個月體重減輕>3kg?", ["否", "是"], key="ic_3", index=None)
            icope_eat_val = ui_card_radio("4. 過去三個月「曾經」食慾不好?", ["否", "是"], key="ic_4", index=None)
                
            st.markdown("---")
            c_i5, c_i6, c_i7 = st.columns(3)
            icope_eye = ui_card_radio("5. 看遠近/閱讀有困難?", ["否", "是"], key="ic_5", index=None)
            icope_opt = ui_card_radio("6. 過去一年「曾」接受眼睛檢查?", ["否", "是"], key="ic_6", index=None)
            icope_teeth = ui_card_radio("7. 過去六個月「曾」到牙科洗牙?", ["否", "是"], key="ic_7", index=None)

            st.markdown("---")
            st.write("8. 聽力狀況 (若無勾選則視為正常)")
            
            # 1. 定義選項清單 (加入 "其他")
            h_options = [
                "電話交談時聽不清或因為沒聽到鈴聲而漏接", 
                "看電視或聽收音機時被說音量開太大聲", 
                "與對方交談需對方提高音量或重說", 
                "因聽力問題而不想聚會",
                "其他"
            ]
            
            # 2. 顯示多選單
            hear_opts = st.multiselect("請選擇符合的情況：", h_options)
            
            # 3. 如果選中「其他」，顯示輸入框 (雖然目前後端只存 "是/否"，但這裡讓使用者輸入可作為紀錄參考)
            if "其他" in hear_opts:
                st.text_input("↳ 請說明其他聽力狀況", placeholder="例如：單耳重聽、需長時間配戴助聽器...")
            
            # 4. 異常判定邏輯
            # 只要 hear_opts 列表長度大於 0 (代表有選，無論是選一般選項還是選其他)，結果就是 "是"
            icope_hear_res = "是" if len(hear_opts) > 0 else "否"
                
            st.markdown("---")
            c_i8, c_i9 = st.columns(2)
            icope_mood = ui_card_radio("9. 過去兩週常心情不好/覺得沒希望?", ["否", "是"], key="ic_9", index=None)
            icope_soc = ui_card_radio("10. 過去兩週減少活動/朋友來往?", ["否", "是"], key="ic_10", index=None)

            # --- 三、BSRS-5 (使用滑桿卡片) ---
        with t3:
            st.markdown("### 🌡️ BSRS-5 心情溫度計")
            st.info("請滑動滑桿選擇程度 (0~4分)")
                
                # 🔥 定義程度文字 (可自行修改)
            scale_anno = {0: "完全沒有", 1: "輕微", 2: "中等程度", 3: "厲害", 4: "非常厲害"}

            b1 = ui_card_slider("1. 睡眠困難（難以入睡、易醒或早醒）", 0, 4, key="bs_1", annotations=scale_anno)
            b2 = ui_card_slider("2. 感覺緊張不安", 0, 4, key="bs_2", annotations=scale_anno)
            b3 = ui_card_slider("3. 覺得容易動怒", 0, 4, key="bs_3", annotations=scale_anno)
            b4 = ui_card_slider("4. 感覺憂鬱、心情低落", 0, 4, key="bs_4", annotations=scale_anno)
            b5 = ui_card_slider("5. 覺得比不上別人", 0, 4, key="bs_5", annotations=scale_anno)
                
            st.markdown("---")
            b6 = ui_card_slider("6. 有自殺的想法 (獨立計分)", 0, 4, key="bs_6", annotations=scale_anno)

                # 即時計算分數
            if None not in [b1, b2, b3, b4, b5]:
                bsrs_total = b1+b2+b3+b4+b5
                if bsrs_total >= 15: bsrs_stat = "重度情緒困擾"
                elif bsrs_total >= 10: bsrs_stat = "中度情緒困擾"
                elif bsrs_total >= 6: bsrs_stat = "輕度情緒困擾"
                else: bsrs_stat = "正常"
                st.success(f"📊 當前總分：{bsrs_total} 分 ({bsrs_stat})")
            else:
                bsrs_total = 0
                bsrs_stat = "填寫中"
                st.caption("請完成所有題目以顯示總分...")

            # --- 四、MNA ---
        # --- 四、MNA ---
        with t4:
            st.markdown("### 🍱 第四部分：MNA 營養評估")
            
            # === 🔥 修改開始：自動帶入但允許修改 ===
            
            # A題：食量
            st.write("**A. 過去三個月食量減少程度?**")
            mna_a_opts = ["0:食量嚴重減少", "1:食量中度減少", "2:食量沒有改變"]
            # 預設索引：如果 ICOPE 食慾(Q4)為否(正常)，預選第 3 個選項(索引2)；否則不預選
            mna_a_idx = 2 if icope_eat_val == "否" else None
            
            mna_a = st.radio(
                "A題 (請詳實評估)", 
                mna_a_opts, 
                index=mna_a_idx, 
                horizontal=True  # 排版美觀可選
            )
            # 提示文字
            if icope_eat_val == "否":
                st.caption("💡 系統依 ICOPE 自動建議「食量無改變」，如有誤請手動修正。")

            st.markdown("---")

            # B題：體重
            st.write("**B. 過去三個月體重下降情況?**")
            mna_b_opts = ["0:下降大於3公斤", "1:不知道", "2:下降1-3公斤", "3:沒有下降"]
            # 預設索引：如果 ICOPE 體重(Q3)為否(正常)，預選第 4 個選項(索引3)；否則不預選
            mna_b_idx = 3 if icope_weight_val == "否" else None
            
            mna_b = st.radio(
                "B題 (請詳實評估)", 
                mna_b_opts, 
                index=mna_b_idx, 
                horizontal=True
            )
            if icope_weight_val == "否":
                st.caption("💡 系統依 ICOPE 自動建議「體重無下降」，如有誤請手動修正。")
            
            # === 🔥 修改結束 ===

            st.markdown("---")

            mna_c = st.radio("C. 活動能力?", ["0:需長期臥床或坐輪椅", "1:可下床但不能外出", "2:可以外出"], index=None)
            mna_d = st.radio("D. 過去3個月內有無受到心理創傷或急性疾病?", ["0:有", "2:沒有"], index=None)
            mna_e = st.radio("E. 精神心理問題?", ["0:嚴重失智或憂鬱", "1:輕度失智", "2:沒有問題"], index=None)
                
                # BMI 分數自動計算
            mna_bmi_score = 0
            if bmi_val > 0:
                if bmi_val < 19: mna_bmi_score = 0
                elif 19 <= bmi_val < 21: mna_bmi_score = 1
                elif 21 <= bmi_val < 23: mna_bmi_score = 2
                else: mna_bmi_score = 3
                st.info(f"F. BMI ({bmi_val}) 自動得分：{mna_bmi_score} 分")
            else:
                st.warning("⚠️ 請先在第一部分輸入身高體重")

                # MNA 總分
            if (mna_a and mna_b and mna_c and mna_d and mna_e and bmi_val > 0):
                try:
                    ms = int(mna_a.split(':')[0]) + int(mna_b.split(':')[0]) + int(mna_c.split(':')[0]) + \
                         int(mna_d.split(':')[0]) + int(mna_e.split(':')[0]) + mna_bmi_score
                    m_stat = "正常營養狀況" if ms >= 12 else ("有營養不良風險" if ms >= 8 else "營養不良")
                    st.success(f"📊 MNA 總分: {ms} ({m_stat})")
                except: ms = 0; m_stat = "計算錯誤"
            else:
                ms = 0; m_stat = "填寫中"
                st.caption("完成所有題目後顯示結果...")

            # --- 五、WHO-5 ---
        with t5:
            st.markdown("### 😊 第五部分：WHO-5 幸福指標")
            st.caption("請選出過去兩週最接近您的感受 (0:從來沒有 ~ 5:全部的時間)")
                
            who_opts = [0, 1, 2, 3, 4, 5]
            w1 = st.radio("1. 我感到情緒開朗且精神不錯", who_opts, index=None, horizontal=True)
            w2 = st.radio("2. 我感到心情平靜和放鬆", who_opts, index=None, horizontal=True)
            w3 = st.radio("3. 我感到有活力且精力充沛", who_opts, index=None, horizontal=True)
            w4 = st.radio("4. 我醒來感到神清氣爽並有充分休息", who_opts, index=None, horizontal=True)
            w5 = st.radio("5. 我的日常生活中充滿讓我感興趣的事物", who_opts, index=None, horizontal=True)

            if None not in [w1, w2, w3, w4, w5]:
                who_total = (w1+w2+w3+w4+w5) * 4
                st.success(f"📊 幸福指數: {who_total} 分")
            else:
                who_total = 0

            # --- 六、膀胱 ---
        with t6:
            st.markdown("### 🚽 第六部分：膀胱症狀與生活品質")
            
            st.markdown("**I. 膀胱症狀及嚴重度 (0:不會 ~ 3:嚴重困擾)**")
            b_opts = ["不會", "會(輕微)", "會(中等)", "會(嚴重)"]
            bq1 = st.radio("1. 是否需要常常上廁所小便？", b_opts, index=None, horizontal=True)
            bq2 = st.radio("2. 尿急時，是否會來不及到廁所就尿出來？", b_opts, index=None, horizontal=True)
            bq3 = st.radio("3. 活動或用力時(如咳嗽/跑跳)，是否會漏尿？", b_opts, index=None, horizontal=True)
            bq4 = st.radio("4. 是否有漏尿量為少量(幾滴)的尿失禁？", b_opts, index=None, horizontal=True)
            bq5 = st.radio("5. 是否會解尿困難？", b_opts, index=None, horizontal=True)
            bq6 = st.radio("6. 是否感覺到下腹部、外陰部或陰道疼痛？", b_opts, index=None, horizontal=True)

            st.markdown("---")
            st.markdown("**II. IIQ-7 生活品質影響 (沒有 ~ 嚴重影響)**")
            i_opts = ["沒有影響", "輕微影響", "中等影響", "嚴重影響"]
            iq1 = st.radio("1. 影響做家事？", i_opts, index=None, horizontal=True)
            iq2 = st.radio("2. 影響健身活動？", i_opts, index=None, horizontal=True)
            iq3 = st.radio("3. 影響外出休閒娛樂？", i_opts, index=None, horizontal=True)
            iq4 = st.radio("4. 影響開車或搭車外出？", i_opts, index=None, horizontal=True)
            iq5 = st.radio("5. 影響社交活動？", i_opts, index=None, horizontal=True)
            iq6 = st.radio("6. 影響情緒健康？", i_opts, index=None, horizontal=True)
            iq7 = st.radio("7. 帶來挫折感？", i_opts, index=None, horizontal=True)

            # --- 七、WHOQOL ---
        with t7:
            st.markdown("### 🌏 第七部分：WHOQOL-BREF")
            st.info("我們想知道您對生活品質的感受 (過去兩週)")

            qol_ans = {}
            qol_ans['Q1'] = st.selectbox("1. 整體來說，您如何評價您的生活品質？", ["1:極不好", "2:不好", "3:中等程度好", "4:好", "5:極好"], index=None)
            qol_ans['Q2'] = st.selectbox("2. 整體來說，您滿意自己的健康嗎？", ["1:極不滿意", "2:不滿意", "3:中等程度滿意", "4:滿意", "5:極滿意"], index=None)
                
            st.markdown("---")
                # 使用列表生成題目，讓程式碼簡潔
            q_list = [
                (3, "您覺得身體疼痛會妨礙您處理需要做的事情嗎?", ["5:完全沒有", "4:有一點", "3:中等", "2:很妨礙", "1:極妨礙"]),
                (4, "您需要靠醫療的幫助應付日常生活嗎?", ["5:完全沒有", "4:有一點", "3:中等", "2:很需要", "1:極需要"]),
                (5, "您享受生活嗎?", ["1:完全沒有", "2:有一點", "3:中等", "4:很享受", "5:極享受"]),
                (6, "您覺得自己的生命有意義嗎?", ["1:完全沒有", "2:有一點", "3:中等", "4:很有", "5:極有"]),
                (7, "您集中精神(含思考、學習、記憶)的能力有多好?", ["1:完全不好", "2:有一點", "3:中等", "4:很好", "5:極好"]),
                (8, "在日常生活中，您感到安全嗎?", ["1:完全不", "2:有一點", "3:中等", "4:很安全", "5:極安全"]),
                (9, "您所處的環境健康嗎?", ["1:完全不", "2:有一點", "3:中等", "4:很健康", "5:極健康"]),
                (10, "您每天的生活有足夠的精力嗎?", ["1:完全不足", "2:少許", "3:中等", "4:很足夠", "5:完全足夠"]),
                (11, "您能接受自己的外表嗎?", ["1:完全不", "2:少許", "3:中等", "4:很能夠", "5:完全能夠"]),
                (12, "您有足夠的金錢應付所需嗎?", ["1:完全不足", "2:少許", "3:中等", "4:很足夠", "5:完全足夠"]),
                (13, "您能方便得到每日生活所需的資訊嗎?", ["1:完全不", "2:少許", "3:中等", "4:很方便", "5:完全方便"]),
                (14, "您有機會從事休閒活動嗎?", ["1:完全沒有", "2:少許", "3:中等", "4:很有", "5:完全有"]),
                (15, "您四處行動的能力好嗎?", ["1:完全不好", "2:有一點", "3:中等", "4:很好", "5:極好"]),
                (16, "您滿意自己的睡眠狀況嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (17, "您對自己從事日常活動的能力滿意嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (18, "您滿意自己的工作能力嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (19, "您對自己滿意嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (20, "您滿意自己的人際關係嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (21, "您滿意自己的性生活嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (22, "您滿意朋友給您的支持嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (23, "您滿意自己住所的狀況嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (24, "您對醫療保健服務的方便程度滿意嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (25, "您滿意所使用的交通運輸方式嗎?", ["1:極不滿意", "2:不滿意", "3:中等", "4:滿意", "5:極滿意"]),
                (26, "您常有負面的感受嗎(擔心/焦慮)?", ["5:從來沒有", "4:不常有", "3:一半一半", "2:很常有", "1:一直都有"]),
                (27, "您覺得自己有面子或被尊重嗎?", ["1:完全沒有", "2:有一點", "3:中等", "4:很有", "5:極有"]),
                (28, "您想吃的食物通常都能吃到嗎?", ["1:從來沒有", "2:不常有", "3:一半一半", "4:很常有", "5:一直都有"]),
            ]
                
            for idx, txt, opts in q_list:
                qol_ans[f'Q{idx}'] = st.radio(f"{idx}. {txt}", opts, index=None, horizontal=True)

            # --- 提交 ---
            st.markdown("---")
            if st.button("💾 儲存完整問卷資料", type="primary"):
                # 簡單的防呆檢查
                if not sel_n:
                    st.error("❌ 尚未選擇關懷戶！")
                else:
                    # 組合資料 (處理 None 值為空字串以避免寫入錯誤)
                    def safe_str(val): return str(val) if val is not None else ""
                    
                    # === 🔥 修正重點：先處理疾病字串邏輯，再放入字典 ===
                    # 1. 複製使用者選的清單
                    final_dis_list = list(dis_hist)

                    # 2. 如果清單中有 "其他"，將其移除，並加入手動輸入的文字
                    if "其他" in final_dis_list:
                        final_dis_list.remove("其他") # 移除 "其他" 這個選項
                        if other_disease_text.strip(): # 如果有輸入文字
                            final_dis_list.append(other_disease_text.strip()) 

                    # 3. 轉成逗號隔開的字串
                    final_dis_str = ",".join(final_dis_list)
                    # === 🔥 修正結束 ===

                    row_data = {
                        "姓名": sel_n, "身分證字號": p_row['身分證字號'], "評估日期": str(eval_date),
                        "收縮壓": safe_str(sys_p), "舒張壓": safe_str(dia_p), "心跳": safe_str(hr_p),
                        "身高": safe_str(h_v), "體重": safe_str(w_v), "BMI": str(bmi_val),
                        "右手握力": safe_str(grip_r), "左手握力": safe_str(grip_l),
                        "Q1_性別": p_info.get('gender',''), "Q2_出生年月日": str(p_info.get('dob','')), "Q3_年齡": str(p_info.get('age','')),
                        "Q4_教育程度": safe_str(edu), "Q5_婚姻狀況": safe_str(marry), "Q6_居住狀況": safe_str(live_st),
                        "Q7_居住樓層": safe_str(floor_final), "Q8_信仰": safe_str(relig), "Q9_工作狀態": safe_str(work),
                        "Q10_經濟狀況": safe_str(econ), "Q11_主要照顧者": ",".join(caregiver), 
                        
                        # ⬇️ 這裡直接使用上面算好的字串
                        "Q12_過去疾病史": final_dis_str, 

                        "使用行走輔具": aid_walk, "使用聽力輔具": aid_hear, "使用視力輔具": aid_eye, "半年內跌倒紀錄": safe_str(fall_rec),
                        "服用助眠藥": safe_str(med_sleep), "服用心血管藥物": safe_str(med_cv), "喝乳品習慣": safe_str(milk_habit),
                        "使用漏尿墊": safe_str(pad_use), "男性小便斷續": safe_str(male_urine),
                        
                        # ICOPE
                        "ICOPE_1_記憶減退": safe_str(icope_mem), "ICOPE_2_跌倒風險": safe_str(icope_fall), 
                        "ICOPE_3_體重減輕": safe_str(icope_weight_val), "ICOPE_4_食慾不佳": safe_str(icope_eat_val),
                        "ICOPE_5_視力困難": safe_str(icope_eye), "ICOPE_6_曾驗光": safe_str(icope_opt), 
                        "ICOPE_7_曾洗牙": safe_str(icope_teeth), "ICOPE_8_聽力困擾": icope_hear_res,
                        "ICOPE_9_心情低落": safe_str(icope_mood), "ICOPE_10_減少社交": safe_str(icope_soc),

                        # BSRS
                        "BSRS_1_睡眠": safe_str(b1), "BSRS_2_緊張": safe_str(b2), "BSRS_3_動怒": safe_str(b3),
                        "BSRS_4_憂鬱": safe_str(b4), "BSRS_5_自卑": safe_str(b5), "BSRS_6_自殺": safe_str(b6),
                        "BSRS_總分": bsrs_total, "BSRS_狀態": bsrs_stat,

                        # MNA
                        "MNA_A_食量": safe_str(mna_a), "MNA_B_體重": safe_str(mna_b), "MNA_C_活動": safe_str(mna_c),
                        "MNA_D_創傷": safe_str(mna_d), "MNA_E_精神": safe_str(mna_e), "MNA_F_BMI": mna_bmi_score,
                        "MNA_篩檢分數": ms, "MNA_狀態": m_stat,

                        # WHO5
                        "WHO5_1_開朗": safe_str(w1), "WHO5_2_平靜": safe_str(w2), "WHO5_3_活力": safe_str(w3),
                        "WHO5_4_休息": safe_str(w4), "WHO5_5_興趣": safe_str(w5), "WHO5_總分": who_total,

                        # 膀胱
                        "膀胱_1_頻尿": safe_str(bq1), "膀胱_2_尿急": safe_str(bq2), "膀胱_3_用力漏尿": safe_str(bq3),
                        "膀胱_4_少量漏尿": safe_str(bq4), "膀胱_5_解尿困難": safe_str(bq5), "膀胱_6_下腹痛": safe_str(bq6),
                        "IIQ7_1_家事": safe_str(iq1), "IIQ7_2_健身": safe_str(iq2), "IIQ7_3_娛樂": safe_str(iq3),
                        "IIQ7_4_開車搭車": safe_str(iq4), "IIQ7_5_社交": safe_str(iq5), "IIQ7_6_情緒": safe_str(iq6), "IIQ7_7_挫折": safe_str(iq7),
                    }
                    
                    # 寫入 QOL 28題
                    for k, v in qol_ans.items():
                        row_data[f"QOL_{k.replace('Q','')}"] = safe_str(v)
                    
                    if append_data("care_health", row_data, COLS_HEALTH): 
                        st.success("✅ 問卷儲存成功！"); st.rerun()

    # === 🔥 修改開始：直接抓取資料表「最下方」的 3 筆 ===
    if not h_df.empty:
        st.markdown("### 📂 最新評估紀錄 (僅顯示最新 3 筆)")
        
        # 邏輯修正：
        # 1. .tail(3) -> 抓出最後面(最新加入)的 3 筆
        # 2. .iloc[::-1] -> 上下顛倒，讓最下面那一筆(最新)排在第一個顯示
        recent_h = h_df.tail(3).iloc[::-1]
        
        h_cols = st.columns(3)
        for idx, (i, row) in enumerate(recent_h.iterrows()):
            # 確保不會因為資料少於3筆而報錯
            if idx < 3:
                with h_cols[idx]:
                    st.markdown(f"""
                    <div style="
                        background: white; 
                        border-radius: 12px; 
                        padding: 15px; 
                        border-top: 5px solid #4A4E69; 
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        display: flex; flex-direction: column; align-items: center;">
                        <div style="font-size: 0.85rem; color: #888; margin-bottom: 5px;">📅 {row['評估日期']}</div>
                        <div style="font-size: 1.3rem; font-weight: 900; color: #333;">{row['姓名']}</div>
                        <div style="
                            margin-top: 10px; 
                            background: #F8F9FA; 
                            padding: 4px 12px; 
                            border-radius: 15px; 
                            font-size: 0.8rem; 
                            color: #555;">
                            BSRS: {row.get('BSRS_總分','-')} 分
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    # === 🔥 修改結束 ===
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
            if st.button("💾 儲存修改內容"):
                with st.spinner("正在寫入資料庫..."):
                    supabase = get_supabase_client()
                    for _, row in ed_i.iterrows():
                        if 'id' in row and pd.notna(row['id']):
                            update_data = {k: str(v) for k, v in row.items() if k != 'id' and pd.notna(v)}
                            supabase.table("care_inventory").update(update_data).eq("id", int(row['id'])).execute()
                    load_data.clear()
                    st.success("✅ 庫存修改已儲存")
                    time.sleep(1); st.rerun()

# --- [插入位置：分頁 4：訪視] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    
    # 1. 載入必要的資料表
    mems = get_care_members()
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    # [新增] 跨系統載入據點的報到紀錄，以及「目前活躍的據點長輩名單」
    elderly_logs = load_data("elderly_logs", ["姓名", "身分證字號", "日期"]) 
    active_elders = load_data("master_residents", ["姓名"]) # 👈 關鍵：抓取還沒被結案的長輩

    # =========================================================
    # 🚨 系統自動鉤稽：連續兩次未報到之預警工單
    # =========================================================
    st.markdown("### 🚨 建議訪視名單")
    
    if not elderly_logs.empty and not active_elders.empty:
        # 1. 確保日期格式正確
        elderly_logs['日期'] = pd.to_datetime(elderly_logs['日期'], errors='coerce')
        
        # 2. 抓出據點所有的「實際開課日期」，並由新到舊排序
        valid_dates = elderly_logs['日期'].dropna().dt.date.unique()
        valid_dates = sorted(valid_dates, reverse=True)
        
        if len(valid_dates) >= 2:
            date_last = pd.to_datetime(valid_dates[0]) # 最近一次上課
            date_prev = pd.to_datetime(valid_dates[1]) # 倒數第二次上課
            
            # 3. 找出每位長輩的最後報到日
            last_checkin = elderly_logs.groupby('姓名')['日期'].max().reset_index()
            
            # 4. 篩選出「最後報到日 < 倒數第二次上課日」的長輩
            missing_elders = last_checkin[last_checkin['日期'] < date_prev].copy()
            
            # 🔴 5. [關鍵修復] 剔除已經結案/過世/退出的長輩
            active_names = active_elders['姓名'].tolist()
            missing_elders = missing_elders[missing_elders['姓名'].isin(active_names)]
            
            if not missing_elders.empty:
                # 6. [防呆機制] 檢查志工是否已經去家訪過了
                pending_tickets = []
                
                if not logs.empty:
                    logs['發放日期'] = pd.to_datetime(logs['發放日期'], errors='coerce')
                    last_visit = logs.groupby('關懷戶姓名')['發放日期'].max().reset_index()
                else:
                    last_visit = pd.DataFrame(columns=['關懷戶姓名', '發放日期'])

                for _, row in missing_elders.iterrows():
                    e_name = row['姓名']
                    last_seen_date = row['日期']
                    
                    # 尋找該長輩最近的家訪紀錄
                    visit_record = last_visit[last_visit['關懷戶姓名'] == e_name]
                    
                    needs_visit = True
                    if not visit_record.empty:
                        v_date = visit_record.iloc[0]['發放日期']
                        # 如果家訪日期 >= 倒數第二次開課日，代表志工已經介入處理了，解除警報
                        if v_date >= date_prev:
                            needs_visit = False
                    
                    if needs_visit:
                        pending_tickets.append({
                            "姓名": e_name, 
                            "最後報到": last_seen_date.strftime('%Y-%m-%d')
                        })

                # 7. 渲染 UI 工單卡片 (含快速結案功能)
                if pending_tickets:
                    st.warning(f"⚠️ 偵測到 {len(pending_tickets)} 位活躍長輩連續兩次未至據點，請優先安排關懷訪視或快速結案！")
                    
                    cols = st.columns(3)
                    for idx, ticket in enumerate(pending_tickets):
                        e_name = ticket['姓名']
                        with cols[idx % 3]:
                            with st.container(border=True):
                                st.markdown(f"""
                                <div style="font-weight: 900; font-size: 1.2rem; color: #E65100;">{e_name}</div>
                                <div style="color: #555; font-size: 0.9rem; margin-top: 5px; margin-bottom: 10px;">
                                    📅 最後現身：{ticket['最後報到']}<br>
                                    <span style="color: #D32F2F; font-weight: bold;">缺席：{date_prev.strftime('%m/%d')}、{date_last.strftime('%m/%d')}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # ⚡ 快速結案選單
                                quick_reason = st.selectbox(
                                    "確認長輩安全狀況", 
                                    ["路上有看到", "Line/電話有回覆", "有請假 / 家屬告知", "其他 (需手動填寫訪視)"], 
                                    key=f"qr_{e_name}",
                                    label_visibility="collapsed"
                                )
                                
                                # 執行快速結案
                                if st.button("✅ 標記為安全 (結案)", key=f"btn_{e_name}", use_container_width=True):
                                    if "其他" in quick_reason:
                                        st.error("請在下方表單填寫完整的訪視紀錄")
                                    else:
                                        quick_log = {
                                            "志工": "系統快速結案", 
                                            "發放日期": str(date.today()), 
                                            "關懷戶姓名": e_name,
                                            "物資內容": "(僅訪視)", 
                                            "發放數量": 0, 
                                            "訪視紀錄": f"【快速結案】{quick_reason}"
                                        }
                                        if append_data("care_logs", quick_log, COLS_LOG):
                                            st.toast(f"✅ 已將 {e_name} 標記為安全！")
                                            time.sleep(0.5)
                                            st.rerun()
                else:
                    st.success("🟢 缺席長輩皆已確認安全或完成家訪追蹤。")
            else:
                st.success("🟢 目前所有活躍長輩皆有穩定出席。")
        else:
            st.info("據點開課次數不足兩次，尚無法進行缺席判定。")
    else:
        st.info("尚無足夠的據點報到與名冊資料可供分析。")
        
    st.markdown("---")
    
    # 2. 計算即時庫存與類型
    stock_map = {}
    item_type_map = {} # 🟢 新增：用來記錄該庫存的物資類型
    if not inv.empty:
        for (item_name, donor_name), group in inv.groupby(['物資內容', '捐贈者']):
            total_in = group['總數量'].replace("","0").astype(float).sum()
            composite_name = f"{item_name} ({donor_name})"
            total_out = logs[logs['物資內容'] == composite_name]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            remain = int(total_in - total_out)
            if remain > 0: 
                stock_map[composite_name] = remain
                item_type_map[composite_name] = group.iloc[0]['物資類型'] # 🟢 紀錄類型

    # =========================================================
    # ✨ 功能 A：智慧發放建議 (含營養不良加權機制)
    # =========================================================
    with st.expander("🤖 優先發放建議", expanded=False):
        st.caption("💡 系統將根據「弱勢積分」推薦，並過濾「已領過」或「拒收」個案。若發放食物，有營養風險者將獲大幅加分。")
        
        if not stock_map:
            st.warning("目前無庫存物資可供分析。")
        else:
            # 🟢 新增：預先找出有營養風險的名單，避免在迴圈內重複計算拖慢速度
            malnutrition_names = set()
            h_df = load_data("care_health", COLS_HEALTH)
            if not h_df.empty:
                h_df['dt'] = pd.to_datetime(h_df['評估日期'], errors='coerce')
                latest_health = h_df.dropna(subset=['dt']).sort_values('dt').groupby('身分證字號').last().reset_index()
                for _, r in latest_health.iterrows():
                    mna_stat = str(r.get('MNA_狀態', ''))
                    icope_w = str(r.get('ICOPE_3_體重減輕', ''))
                    icope_e = str(r.get('ICOPE_4_食慾不佳', ''))
                    # 只要符合任何一項營養風險指標，就加入名單
                    if "不良" in mna_stat or "風險" in mna_stat or icope_w == "是" or icope_e == "是":
                        malnutrition_names.add(str(r.get('姓名', '')))
            
            suggest_item = st.selectbox("選擇要評估發放的物資：", list(stock_map.keys()))
            is_food = (item_type_map.get(suggest_item) == "食物") # 判斷當前物資是否為食物
            
            suggestion_list = []
            for index, row in mems.iterrows():
                p_name = row['姓名']
                p_tags = str(row['身分別'])
                p_refuse = str(row.get('拒絕物資', '')) 
                
                # 1. 檢查是否拒收 (呼叫字典判讀)
                is_conflict, _ = check_conflict(p_refuse, suggest_item)
                if is_conflict: continue 

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
                    
                    # 🟢 新增：營養風險加權機制
                    if is_food and p_name in malnutrition_names:
                        score += 5  # 高權重加分 (直接加5分，保證名列前茅)
                        p_tags += " | 🚨需營養補充" # 在畫面上多給一個警示標籤
                    
                    suggestion_list.append({"姓名": p_name, "身分別": p_tags, "弱勢積分": score})
            
            # 顯示結果
            if suggestion_list:
                df_suggest = pd.DataFrame(suggestion_list).sort_values("弱勢積分", ascending=False).head(5)
                for _, row in df_suggest.iterrows():
                    # 🟢 特殊樣式：若觸發營養補充條件，給予醒目的淡紅色背景與紅邊框
                    alert_style = "border-left:5px solid #D32F2F; background:#FFEBEE;" if "需營養補充" in row['身分別'] else "border-left:5px solid #FF7043; background:white;"
                    
                    st.markdown(f"""
                    <div style="{alert_style} padding:8px; margin-bottom:5px; box-shadow:0 1px 3px rgba(0,0,0,0.1); border-radius: 5px;">
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
    st.markdown("#### 1. 訪視對象")
    
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
        target_p = st.selectbox("👤 選擇關懷戶", filtered_mems['姓名'].tolist() if not filtered_mems.empty else [], index=None, placeholder="請點擊此處輸入或選擇姓名...")

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
                update_master_fields(mems.loc[p_row_idx, '身分證字號'], {'拒絕物資': new_refuse_input})
                st.toast("✅ 備註已更新！"); time.sleep(1); st.rerun()

    st.markdown("#### 2. 訪視內容與物資")
    
    # --- [新增程式碼] 鉤稽志工系統名單 ---
    # 1. 讀取志工名冊 (共用同一個 Spreadsheet，分頁名稱為 'members')
    vol_df = load_data("master_residents", ["姓名", "志工分類", "身分_志工"])
    vol_df = vol_df[vol_df['身分_志工'].astype(str).str.upper() == 'TRUE']
    
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
    
    if st.button("✅ 確認提交紀錄", type="primary"):
        if not target_p:
            st.error("❌ 請選擇關懷戶")
        else:
            # 1. 收集要寫入的資料
            items_to_give = [(k, v) for k, v in quantities.items() if v > 0]
            new_logs = [] # 變數名稱在這裡定義為 new_logs

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
            
            # 2. 寫入資料庫
            try:
                success_count = 0
                for row_data in new_logs:
                    # 直接呼叫您原本定義好的 append_data 函式
                    # 此函式使用的是 sheet.append_row，保證是「追加」
                    if append_data("care_logs", row_data, COLS_LOG):
                        success_count += 1
                
                if success_count == len(new_logs):
                    st.success(f"✅ 成功新增 {success_count} 筆紀錄！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(f"⚠️ 部分資料寫入異常，僅成功 {success_count} 筆。")
                    
            except Exception as e:
                st.error(f"儲存失敗: {e}")

    # === 🔥 修改開始：訪視紀錄改為卡片 ===
    if not logs.empty:
        st.markdown("#### 📝 最新訪視動態 (Top 3)")
        
        # 1. 排序並取前 3
        recent_logs = logs.sort_values('發放日期', ascending=False).head(3)
        
        v_cols = st.columns(3)
        for idx, (i, row) in enumerate(recent_logs.iterrows()):
            if idx < 3:
                with v_cols[idx]:
                    # 判斷是物資還是純訪視，給不同顏色標籤
                    is_only_visit = (row['物資內容'] == "(僅訪視)")
                    tag_bg = "#9E9E9E" if is_only_visit else "#8E9775"
                    item_text = "純訪視" if is_only_visit else f"{row['物資內容']}"
                    
                    st.markdown(f"""
                    <div style="
                        background: white; 
                        border-radius: 12px; 
                        padding: 15px; 
                        border-right: 5px solid {tag_bg}; 
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span style="font-weight:900; font-size:1.1rem; color:#333;">{row['關懷戶姓名']}</span>
                            <span style="font-size:0.8rem; color:#888;">{row['發放日期']}</span>
                        </div>
                        <div style="background:{tag_bg}; color:white; font-size:0.8rem; padding:2px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">
                            {item_text}
                        </div>
                        <div style="font-size:0.9rem; color:#555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {row['訪視紀錄'] if row['訪視紀錄'] else "(無備註)"}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# =========================================================
# 🔥 Page: Stats (數據統計與詳細檔案卡片 - 升級版)
# =========================================================
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計與個案查詢")
    logs, mems = load_data("care_logs", COLS_LOG), get_care_members()
    h_df = load_data("care_health", COLS_HEALTH)

    # 修改：從 2 個分頁變成 3 個分頁
    tab1, tab2, tab3 = st.tabs(["👤 個案詳細檔案 (含警示)", "🔍 題項交叉篩選", "📈 整體物資統計"])

    # --- Tab 1: 詳細檔案 (含雙向關係與警示) ---
    with tab1:
        if mems.empty: st.info("無資料")
        else:
            # 建立選單用的名單 (顯示: 姓名 + ID末四碼以防重複)
            all_options = mems.apply(lambda x: f"{x['姓名']} ({str(x['身分證字號'])[-4:]})", axis=1).tolist()
            
            # 選擇主要查看對象
            sel_label = st.selectbox("請選擇關懷戶", all_options, index=None, placeholder="請點擊此處輸入或選擇姓名...")
            
            target_name = None # 初始化變數，避免未選擇時產生 NameError
            
            if not sel_label:
                # 尚未選擇任何個案時的提示與建議畫面
                st.info("💡 請在上方點擊輸入姓名，以載入個案詳細資料。")
                st.markdown("""
                <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-top: 10px;">
                    <h4 style="color: #4A4E69; margin-bottom: 15px;">🔍 透過此頁面，您可以查看該個案的：</h4>
                    <ul style="line-height: 1.8; color: #555;">
                        <li><b>👤 基本資料與聯絡方式</b>（含弱勢身分標籤）</li>
                        <li><b>🔗 人際網絡圖</b>（自動鉤稽雙向關係與警示）</li>
                        <li><b>🩺 智慧健康警示卡片</b>（依據最新評估自動標示高低風險）</li>
                        <li><b>📈 健康數據趨勢圖</b>（追蹤 BMI、血壓、情緒溫度計等歷次變化）</li>
                        <li><b>📝 近期訪視紀錄</b>（快速檢視前五次物資領取與訪視摘要）</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 1. 解析出選到的這個人是誰
                target_name = sel_label.split(' (')[0]
                
                # 取得該個案資料列
                p_row = mems[mems.apply(lambda x: f"{x['姓名']} ({str(x['身分證字號'])[-4:]})", axis=1) == sel_label].iloc[0]
                p_idx = p_row.name # 取得原始資料表的 index 方便寫入
                
                # 取得關鍵變數
                my_id = str(p_row['身分證字號']).strip()
                my_name = p_row['姓名']
                age = calculate_age(p_row['生日'])
                
                # 2. 建立 ID 查找字典
                id_to_name = mems.set_index('身分證字號')['姓名'].to_dict()

                # =========================================================
                # 🔥 區塊一：左側卡片 & 右側關係氣泡
                # =========================================================
                
                def get_tag_html(tag_text):
                    color_map = {
                        "獨居": ("#FFF3E0", "#E65100"), "身障": ("#E3F2FD", "#1565C0"),
                        "低收": ("#FFEBEE", "#C62828"), "中低收": ("#FFEBEE", "#C62828"),
                        "老人": ("#E8F5E9", "#2E7D32"), "一般": ("#F5F5F5", "#616161"),
                    }
                    bg, txt = ("#F3F4F6", "#374151")
                    for key, (c_bg, c_txt) in color_map.items():
                        if key in tag_text:
                            bg, txt = c_bg, c_txt
                            break
                    return f"""<span style="background-color:{bg};color:{txt};padding:4px 12px;border-radius:15px;font-size:0.85rem;font-weight:bold;margin-right:6px;display:inline-block;margin-bottom:4px;">{tag_text}</span>"""

                raw_tags = str(p_row['身分別']).replace('，', ',').split(',')
                tags_html = "".join([get_tag_html(t.strip()) for t in raw_tags if t.strip()])

                # 切分版面
                c_card, c_rel = st.columns([3, 1])

                with c_card:
                    # 卡片 HTML (注意這裡的三引號 f""" ... """ 必須正確閉合)
                    card_html = f"""
                    <div style="background-color: white; padding: 25px; border-radius: 15px; border-left: 8px solid {GREEN}; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; margin-bottom: 12px;">
                            <div style="font-size: 1.8rem; font-weight: 900; color: #333; margin-right: 15px;">{my_name}</div>
                            <div style="background: #F3F4F6; color: #4B5563; padding: 4px 12px; border-radius: 8px; font-weight: bold; font-size: 0.9rem;">{p_row['性別']} / {age}歲</div>
                        </div>
                        <div style="margin-bottom: 20px;">{tags_html}</div>
                        <div style="display:grid; grid-template-columns: 1fr 2fr; gap:15px; border-top: 1px solid #eee; padding-top: 15px;">
                            <div style="display: flex; align-items: center; color: #444; font-weight: bold;"><span style="font-size: 1.2rem; margin-right: 8px;">📞</span> {p_row['電話']}</div>
                            <div style="display: flex; align-items: center; color: #444;"><span style="font-size: 1.2rem; margin-right: 8px; color: #D32F2F;">📍</span> {p_row['地址']}</div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                with c_rel:
                    st.markdown("#### 🔗 人際網絡")
                    
                    # === 核心邏輯：雙向關係計算 ===
                    all_rels = []
                    
                    # 1. [主動關係]
                    raw_str = str(p_row.get('人際關係', ''))
                    if raw_str:
                        for item in raw_str.split(','):
                            if ':' in item:
                                r_key, r_type = item.split(':', 1)
                                r_key = r_key.strip()
                                final_name = id_to_name.get(r_key, r_key) 
                                all_rels.append((final_name, r_type, "我標記"))

                    # 2. [被動關係]
                    related_rows = mems[
                        (mems['人際關係'].astype(str).str.contains(my_id, regex=False)) & 
                        (mems['身分證字號'] != my_id)
                    ]
                    
                    for _, other_row in related_rows.iterrows():
                        other_items = str(other_row['人際關係']).split(',')
                        for item in other_items:
                            if ':' in item:
                                t_id, t_type = item.split(':', 1)
                                if t_id.strip() == my_id:
                                    all_rels.append((other_row['姓名'], t_type, "對方標記"))

                    # === 渲染氣泡 ===
                    if not all_rels:
                        st.caption("尚無紀錄")
                    else:
                        seen = set()
                        unique_rels = []
                        for r in all_rels:
                            key = f"{r[0]}-{r[1]}"
                            if key not in seen:
                                unique_rels.append(r)
                                seen.add(key)

                        bad_kws = ['不合']
                        bad_list = [r for r in unique_rels if any(k in r[1] for k in bad_kws)]
                        good_list = [r for r in unique_rels if r not in bad_list]

                        # 優化後的氣泡生成器 (解決縮排導致的 </div> 顯示錯誤)
                        def render_bubbles(rel_list):
                            # 外層容器 (Flex佈局)
                            html = "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;'>"
                            
                            for name, r_type, source in rel_list:
                                is_bad = any(k in r_type for k in bad_kws)
                                
                                # 樣式變數
                                bg = "#FFEBEE" if is_bad else "#E8F5E9"
                                border = "#EF9A9A" if is_bad else "#A5D6A7"
                                text_c = "#C62828" if is_bad else "#2E7D32"
                                icon = "⚡" if is_bad else "🤝"
                                
                                # 來源圖示
                                src_html = ""
                                if source == "對方標記":
                                    src_html = f"<span style='font-size:0.7rem; opacity:0.6; margin-left:3px;' title='由{name}的檔案自動連結'>🔗</span>"

                                # 🔥 修正重點：
                                # 1. 將 CSS 獨立出來，並加上 white-space: nowrap (防止文字被擠壓換行)
                                # 2. 將 HTML 改為單行字串 (防止 Markdown 誤判縮排為程式碼)
                                style_str = (
                                    f"background:{bg}; color:{text_c}; border:1px solid {border}; "
                                    f"padding:4px 10px; border-radius:20px; font-size:0.9rem; "
                                    f"font-weight:bold; display:flex; align-items:center; "
                                    f"white-space: nowrap;"  # <--- 關鍵：強制不換行
                                )
                                
                                # 組合 HTML (單行模式)
                                html += (
                                    f'<div style="{style_str}">'
                                    f'<span style="margin-right:4px;">{icon}</span> {name} '
                                    f'<span style="font-size:0.75rem; opacity:0.8; margin-left:4px;">({r_type})</span>'
                                    f'{src_html}'
                                    f'</div>'
                                )

                            html += "</div>"
                            return html

                        if bad_list:
                            st.markdown("<small style='color:#999'>⚠️ 需注意關係</small>", unsafe_allow_html=True)
                            st.markdown(render_bubbles(bad_list), unsafe_allow_html=True)
                        if good_list:
                            st.markdown("<small style='color:#999'>❤️ 連結網絡</small>", unsafe_allow_html=True)
                            st.markdown(render_bubbles(good_list), unsafe_allow_html=True)

                # =========================================================
                # 🔥 區塊二：新增介面 (隱藏原始資料串)
                # =========================================================
                st.markdown("---")
                with st.expander(f"⚙️ 新增 {my_name} 的人際關係", expanded=False):
                    
                    tab_link, tab_manual = st.tabs(["🔗 連結名冊成員 (推薦)", "✍️ 手動輸入非成員"])
                    
                    # --- 模式 A: 連結名冊 ---
                    with tab_link:
                        other_df = mems[mems['身分證字號'] != my_id].copy()
                        other_df['label'] = other_df.apply(
                            lambda x: f"{x['姓名']} ({calculate_age(x['生日'])}歲 / {str(x['地址'])[:6]}..)", axis=1
                        )
                        label_map = other_df.set_index('label')['身分證字號'].to_dict()
                        
                        c1, c2, c3 = st.columns([2, 1, 1])
                        sel_target = c1.selectbox("選擇對象", options=other_df['label'].tolist(), index=None, placeholder="請點擊此處輸入或選擇姓名...", key="link_p")
                        sel_type = c2.selectbox("關係", ["朋友", "親戚", "鄰居", "反感", "不合", "債務", "其他"], key="link_t")
                        
                        # 排版空行
                        c3.write("") 
                        c3.write("")
                        if c3.button("➕ 新增", key="btn_link"):
                            if not sel_target:
                                st.error("❌ 請先選擇對象")
                            else:
                                target_id = label_map[sel_target]
                                new_entry = f"{target_id}:{sel_type}"
                            
                                old_str = str(p_row.get('人際關係', ''))
                            # 簡單防呆：ID已存在就不給加
                                if target_id in old_str:
                                    st.error("❌ 已有此人紀錄")
                                else:
                                    new_val = f"{old_str},{new_entry}" if old_str else new_entry
                                    new_val = ",".join([x for x in new_val.split(',') if x.strip()])
                                    mems.at[p_idx, '人際關係'] = new_val
                                    update_master_fields(my_id, {'人際關係': new_val})
                                    st.success(f"已連結：{sel_target.split(' (')[0]}")
                                    time.sleep(0.5); st.rerun()

                    # --- 模式 B: 手動輸入 ---
                    with tab_manual:
                        st.caption("適用於：該對象不在系統名冊內 (如外地親友)")
                        cm1, cm2, cm3 = st.columns([2, 1, 1])
                        man_name = cm1.text_input("對方姓名", placeholder="例如: 遠房表哥")
                        man_type = cm2.text_input("關係", placeholder="例如: 很少往來")
                        
                        cm3.write("")
                        cm3.write("")
                        if cm3.button("➕ 新增", key="btn_manual"):
                            if man_name and man_type:
                                new_entry = f"{man_name}:{man_type}"
                                old_str = str(p_row.get('人際關係', ''))
                                new_val = f"{old_str},{new_entry}" if old_str else new_entry
                                new_val = ",".join([x for x in new_val.split(',') if x.strip()])
                                mems.at[p_idx, '人際關係'] = new_val
                                update_master_fields(my_id, {'人際關係': new_val})
                                st.rerun()
                
                # ... (原有的健康警示邏輯區塊，可接續在後) ...

                
                # 2. 自動警示卡片邏輯 (Smart Alerts)
                if not h_df.empty:
                    p_health = h_df[h_df['姓名'] == target_name]
                    if not p_health.empty:
                        last_h = p_health.sort_values("評估日期").iloc[-1]
                        st.markdown(f"#### 🩺 健康評估警示 (評估日：{last_h['評估日期']})")
                        
                        alerts = []
                        
                        # ==========================================
                        # 1. 通用規則 (簡單欄位檢查)
                        # ==========================================
                        # 移除原本的 BMI 規則，改由下方獨立邏輯處理
                        rules = [
                            # === 🔴 高風險 (Danger) ===
                            ("BSRS_6_自殺", lambda x: "分" in str(x) and str(x) != "0分", "自殺意念", "🚨", "danger"),
                            ("BSRS_狀態", ["重度情緒困擾"], "重度情緒困擾", "⛈️", "danger"),
                            ("MNA_狀態", "營養不良", "營養不良", "📉", "danger"),
                            
                            # === 🟠 中風險 (Warning) ===
                            ("BSRS_狀態", ["中度情緒困擾"], "中度情緒困擾", "🌧️", "warning"),
                            ("MNA_狀態", "有營養不良風險", "營養風險", "📉", "warning"),
                            ("ICOPE_2_跌倒風險", "是", "跌倒風險", "🤕", "warning"),
                            ("ICOPE_1_記憶減退", "是", "記憶減退", "🧠", "warning"),
                            ("ICOPE_9_心情低落", "是", "心情低落", "☁️", "warning"),
                            ("膀胱_1_頻尿", ["會(嚴重)"], "嚴重頻尿", "🚽", "warning"),

                            # === 🟡 提醒/輕微 (Notice) ===
                            ("ICOPE_7_曾洗牙", "否", "半年未洗牙", "🦷", "notice"),
                            ("ICOPE_5_視力困難", "是", "視力異常", "👓", "notice"),
                            ("ICOPE_8_聽力困擾", "是", "聽力異常", "👂", "notice"),
                            ("膀胱_1_頻尿", ["會(中等)"], "中度頻尿", "🚽", "notice"),
                        ]
                        
                        # 執行通用規則迴圈
                        for col, trigger, title, icon, level in rules:
                            val = str(last_h.get(col, ''))
                            is_hit = False
                            if callable(trigger):
                                try: is_hit = trigger(val)
                                except: is_hit = False
                            elif isinstance(trigger, list):
                                is_hit = val in trigger
                            elif val == trigger:
                                is_hit = True
                            
                            if is_hit:
                                alerts.append({'icon': icon, 'title': title, 'val': val, 'type': level})

                        # ==========================================
                        # 2. 複雜邏輯：BMI (針對 60 歲以上長者)
                        # ==========================================
                        try:
                            # 優先使用名冊計算的 age (即時)，若無則用問卷填寫的 Q3_年齡
                            check_age = age if age > 0 else float(last_h.get('Q3_年齡', 0))
                            bmi_val = float(last_h.get('BMI', 0))
                            
                            if check_age >= 60 and bmi_val > 0:
                                if bmi_val < 19:
                                    alerts.append({'icon': '⚖️', 'title': '體重過輕', 'val': f"BMI {bmi_val}", 'type': 'danger'})
                                elif 19 <= bmi_val < 21:
                                    alerts.append({'icon': '⚖️', 'title': '體重偏輕', 'val': f"BMI {bmi_val}", 'type': 'warning'})
                                elif 21 <= bmi_val < 23:
                                    alerts.append({'icon': '⚖️', 'title': '注意體重', 'val': f"BMI {bmi_val}", 'type': 'notice'})
                                # 23 以上不警示
                        except:
                            pass # 避免資料轉換錯誤導致當機

                        # ==========================================
                        # 3. 複雜邏輯：握力 (區分性別)
                        # ==========================================
                        try:
                            # 判斷性別
                            p_gender = last_h.get('Q1_性別', '')
                            # 取左右手最大值 (慣用手概念)
                            g_r = float(last_h.get('右手握力', 0) if last_h.get('右手握力') else 0)
                            g_l = float(last_h.get('左手握力', 0) if last_h.get('左手握力') else 0)
                            max_grip = max(g_r, g_l)
                            
                            is_low_grip = False
                            if max_grip > 0: # 確保有數值才判斷
                                if p_gender == '男' and max_grip < 26:
                                    is_low_grip = True
                                elif p_gender == '女' and max_grip < 18:
                                    is_low_grip = True
                            
                            if is_low_grip:
                                 alerts.append({'icon': '💪', 'title': '握力不足', 'val': f"{max_grip}kg", 'type': 'notice'})
                        except:
                            pass

                        # ==========================================
                        # 4. 渲染卡片 (依嚴重度排序)
                        # ==========================================
                        if alerts:
                            sort_map = {"danger": 1, "warning": 2, "notice": 3}
                            alerts.sort(key=lambda k: sort_map.get(k['type'], 99))

                            cols_per_row = 3
                            for i in range(0, len(alerts), cols_per_row):
                                row_alerts = alerts[i:i+cols_per_row]
                                cols = st.columns(cols_per_row)
                                for idx, alert in enumerate(row_alerts):
                                    with cols[idx]:
                                        css_cls = f"h-card-{alert['type']}"
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
                            # 顯示安全卡片
                            st.markdown("""
                            <div class="health-dashboard-card h-card-safe">
                                <div class="h-card-icon">✅</div>
                                <div class="h-card-content">
                                    <div class="h-card-title">健康狀況</div>
                                    <div class="h-card-value">目前無明顯異常指標</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                # 🔥 [新增] 健康追蹤趨勢圖
        if target_name and not h_df.empty:
            p_history = h_df[h_df['姓名'] == target_name].copy()
            
            # 至少有兩筆資料才畫圖
            if len(p_history) >= 2:
                st.markdown("---")
                st.markdown("#### 📈 健康數據趨勢變化")
                
                # 整理日期格式
                p_history['評估日期'] = pd.to_datetime(p_history['評估日期'])
                p_history = p_history.sort_values('評估日期')

                # 選擇要畫圖的指標
                trend_opts = ["BMI", "體重", "收縮壓", "BSRS_總分", "WHO5_總分", "MNA_篩檢分數"]
                trend_col = st.selectbox("選擇趨勢指標", trend_opts)

                # 強制轉數值以免報錯
                p_history[trend_col] = pd.to_numeric(p_history[trend_col], errors='coerce')

                # 繪製折線圖
                fig = px.line(p_history, x='評估日期', y=trend_col, markers=True, title=f"{target_name} 的 {trend_col} 歷史變化")
                fig.update_traces(line_color=GREEN, marker_size=10) # 🎨 可在此調整線條顏色
                st.plotly_chart(fig, use_container_width=True)
            elif len(p_history) == 1:
                st.caption("💡 累積兩次以上評估後，此處將自動顯示趨勢圖。")

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
                
                st.markdown("---") # 加一條分隔線會比較清楚
        st.markdown("### 🤝 近五筆訪視紀錄")
        
        # 篩選該個案的紀錄 (這裡開始都要向左縮排，確保與 if target_name and not h_df.empty: 同層級)
        p_logs = logs[logs['關懷戶姓名'] == target_name]
        
        if p_logs.empty: 
            st.info("💡 該個案尚無任何訪視或物資領取紀錄。")
        else:
            # 依日期排序並取前 5 筆
            p_logs = p_logs.sort_values("發放日期", ascending=False).head(5)
            
            for idx, row in p_logs.iterrows():
                # --- 卡片樣式設定 ---
                is_pure_visit = (row['物資內容'] == "(僅訪視)")
                border_color = "#9E9E9E" if is_pure_visit else "#8E9775"
                bg_icon = "💬" if is_pure_visit else "🎁"
                
                if is_pure_visit:
                    main_content = "純訪視關懷 (無物資)"
                    badge_style = "background:#eee; color:#666;"
                else:
                    qty = row['發放數量']
                    main_content = f"領取：{row['物資內容']}"
                    badge_style = "background:#E8F5E9; color:#2E7D32; font-weight:bold;"

                note_text = row['訪視紀錄'] if row['訪視紀錄'] and row['訪視紀錄'].strip() != "" else "(本次無詳細文字紀錄)"

                # --- 渲染 HTML 卡片 ---
                st.markdown(f"""
                <div style="
                    background-color: white;
                    border-radius: 12px;
                    border-left: 6px solid {border_color};
                    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                    padding: 15px;
                    margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 900; color: #333;">📅 {row['發放日期']}</span>
                        <span style="font-size: 0.85rem; background-color: #f5f5f5; color: #555; padding: 4px 10px; border-radius: 20px;">👮 執行志工：{row['志工']}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <span style="font-size: 1rem; padding: 6px 12px; border-radius: 8px; display: inline-block; {badge_style}">
                            {bg_icon} {main_content} 
                            {f'<span style="background:white; padding:0 6px; border-radius:4px; margin-left:5px; font-size:0.9rem; border:1px solid #cfcfcf;">x {qty}</span>' if not is_pure_visit else ''}
                        </span>
                    </div>
                    <div style="background-color: #FAFAFA; padding: 10px; border-radius: 8px; font-size: 0.95rem; color: #444; line-height: 1.5;">
                        <div style="font-size: 0.8rem; color: #999; margin-bottom: 4px; font-weight: bold;">📝 訪視內容 / 備註：</div>
                        {note_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- Tab 2: 跨問卷交叉篩選 (完全改寫) ---
    with tab2:
        st.markdown("### 🔍 跨題項/跨名冊 交叉篩選")
        st.caption("💡 可自由新增不同問卷，並針對數值設定大於、小於或區間條件。")

        if h_df.empty:
            st.warning("尚無健康資料")
        else:
            # 1. 資料合併
            full_data = h_df.copy()
            if not mems.empty:
                mems_mini = mems[['姓名', '電話', '地址', '身分別', '生日']]
                full_data = full_data.merge(mems_mini, on='姓名', how='left')
                full_data['數值年齡'] = full_data['生日'].apply(calculate_age) 

            # 2. 定義題項分類
            category_map = {
                "📝 基本資料與身體狀況": ["數值年齡", "身分別", "Q1_性別", "收縮壓", "舒張壓", "心跳", "身高", "體重", "BMI", "右手握力", "左手握力", "Q4_教育程度", "Q5_婚姻狀況", "Q6_居住狀況", "Q7_居住樓層", "Q8_信仰", "Q9_工作狀態", "Q10_經濟狀況", "Q11_主要照顧者", "Q12_過去疾病史", "使用行走輔具", "使用聽力輔具", "使用視力輔具", "半年內跌倒紀錄", "服用助眠藥", "服用心血管藥物", "喝乳品習慣", "使用漏尿墊", "男性小便斷續"],
                "🧠 ICOPE (高齡功能)": [c for c in COLS_HEALTH if c.startswith("ICOPE")],
                "🌡️ BSRS-5 (心情溫度計)": [c for c in COLS_HEALTH if c.startswith("BSRS")],
                "🍱 MNA (營養評估)": [c for c in COLS_HEALTH if c.startswith("MNA")],
                "😊 WHO-5 (幸福指標)": [c for c in COLS_HEALTH if c.startswith("WHO5")],
                "🚽 膀胱與 IIQ-7": [c for c in COLS_HEALTH if c.startswith("膀胱") or c.startswith("IIQ7")],
                "🌏 WHOQOL (生活品質)": [c for c in COLS_HEALTH if c.startswith("QOL")]
            }
            
            # 定義哪些欄位是數值 (用於判斷要顯示大於/小於還是多選單)
            num_cols = ['數值年齡', 'BMI', '收縮壓', '舒張壓', '心跳', '身高', '體重', '右手握力', '左手握力', 'BSRS_總分', 'WHO5_總分', 'MNA_篩檢分數', 'MNA_F_BMI']

            # 3. 初始化篩選群組數量
            if 'filter_group_count' not in st.session_state:
                st.session_state.filter_group_count = 1

            # 頂部控制按鈕
            c_btn1, c_btn2, _ = st.columns([1, 1, 4])
            if c_btn1.button("➕ 新增問卷分類"):
                st.session_state.filter_group_count += 1; st.rerun()
            if c_btn2.button("🗑️ 重置所有條件"):
                st.session_state.filter_group_count = 1; st.rerun()

            st.markdown("---")
            
            # 收集使用者選中的所有題目
            selected_all_items = []
            
            # 4. 產生 N 個篩選群組 (依據使用者按新增的次數)
            for i in range(st.session_state.filter_group_count):
                with st.container(border=True):
                    c_cat, c_item = st.columns([1, 2])
                    cat = c_cat.selectbox(f"📋 選擇問卷類別 (第 {i+1} 組)", list(category_map.keys()), key=f"cat_sel_{i}")
                    items = c_item.multiselect(f"選擇「{cat}」中的題項", category_map[cat], key=f"item_sel_{i}", placeholder="請點此選擇題目...")
                    if items:
                        selected_all_items.extend(items)

            # 5. 動態生成篩選條件設定區塊
            filters = {}
            if selected_all_items:
                st.markdown("##### ⚙️ 設定條件細節：")
                
                # --- 新增：數值意義提示字典 ---
                hint_dict = {
                    "BSRS": "💡 【分數意義】0: 完全沒有, 1: 輕微, 2: 中等, 3: 厲害, 4: 非常厲害。(分數「越高」代表越困擾)",
                    "WHO5": "💡 【分數意義】0: 從來沒有 ~ 5: 全部的時間。(總分最高100分，分數「越高」代表越幸福)",
                    "MNA": "💡 【分數意義】分數「越低」代表營養狀況越差 (總分 <12 為風險, <8 為不良)。",
                    "握力": "💡 【參考標準】男性小於 26kg、女性小於 18kg 視為握力不足。",
                    "BMI": "💡 【參考標準】< 18.5 過輕, 18.5~24 正常, 24~27 過重, ≥ 27 肥胖。",
                    "膀胱": "💡 【嚴重程度】依照選項字面意義選擇 (例如：「會(嚴重)」)。",
                    "IIQ7": "💡 【影響程度】依照選項字面意義選擇 (沒有影響 ~ 嚴重影響)。",
                    "QOL": "💡 【分數意義】1~5 分，依照選項字面意義選擇 (通常 5 為極好/極滿意)。"
                }

                # 使用者每選一題，就產生一個對應的設定框
                for col in selected_all_items:
                    with st.container(border=True):
                        # --- 顯示對應的提示文字 ---
                        for key, hint_text in hint_dict.items():
                            if key in col:
                                st.markdown(f"<div style='background-color:#E1F5FE; color:#0277BD; padding:6px 10px; border-radius:8px; font-size:0.85rem; font-weight:bold; margin-bottom:10px;'>{hint_text}</div>", unsafe_allow_html=True)
                                break
                                
                        if col in num_cols:
                            # 【數值型態】的條件介面
                            c_op, c_v1, c_v2 = st.columns([1, 1, 1])
                            op = c_op.selectbox(f"設定【{col}】條件", ["大於等於", "小於等於", "介於", "等於"], key=f"op_{col}")
                            
                            # 自動判斷是否需要小數點
                            is_float = col in ['BMI', '身高', '體重', '右手握力', '左手握力']
                            def_v = 0.0 if is_float else 0
                            def_max = 100.0 if is_float else 100
                            step_v = 0.1 if is_float else 1

                            if op == "介於":
                                v1 = c_v1.number_input("最小值", key=f"min_{col}", value=def_v, step=step_v)
                                v2 = c_v2.number_input("最大值", key=f"max_{col}", value=def_max, step=step_v)
                                filters[col] = ("between", v1, v2)
                            else:
                                v = c_v1.number_input("輸入數值", key=f"val_{col}", value=def_v, step=step_v)
                                filters[col] = (op, v)
                                
                        else:
                            # 【文字/選項型態】的條件介面
                            unique_opts = sorted([str(x) for x in full_data[col].unique() if str(x) != 'nan' and str(x) != ''])
                            selected_opts = st.multiselect(f"設定【{col}】包含", unique_opts, key=f"f_{col}")
                            if selected_opts:
                                filters[col] = ("in", selected_opts)

            # 6. 執行篩選邏輯
            result_df = full_data.copy()
            for col, condition in filters.items():
                cond_type = condition[0]
                
                if cond_type == "in":
                    # 處理文字/多選
                    selected_opts = condition[1]
                    if col == '身分別':
                        mask = result_df[col].astype(str).apply(lambda x: any(tag in x for tag in selected_opts))
                        result_df = result_df[mask]
                    else:
                        result_df = result_df[result_df[col].astype(str).isin(selected_opts)]
                else:
                    # 處理數值
                    result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
                    if cond_type == "between":
                        result_df = result_df[(result_df[col] >= condition[1]) & (result_df[col] <= condition[2])]
                    elif cond_type == "大於等於":
                        result_df = result_df[result_df[col] >= condition[1]]
                    elif cond_type == "小於等於":
                        result_df = result_df[result_df[col] <= condition[1]]
                    elif cond_type == "等於":
                        result_df = result_df[result_df[col] == condition[1]]
            
            # 7. 顯示結果 (改為卡片式)
            if selected_all_items:
                st.markdown(f"#### 🎯 篩選結果：共 {len(result_df)} 人符合條件")
                
                if not result_df.empty:
                    # 去除重複選取的欄位
                    unique_selected_items = list(dict.fromkeys(selected_all_items))
                    
                    # 以 3 欄式排列卡片
                    cols = st.columns(3)
                    for idx, (_, row) in enumerate(result_df.iterrows()):
                        with cols[idx % 3]:
                            # 組合卡片內的題項明細
                            details_html = ""
                            for c in unique_selected_items:
                                val = row.get(c, '無資料')
                                details_html += f"<div style='font-size:0.85rem; color:#555; margin-bottom:4px;'><b>{c}:</b> {val}</div>"
                            
                            st.markdown(f"""
                            <div style="background: white; border-radius: 12px; padding: 15px; border-top: 5px solid #8E9775; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 15px; height: 100%;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                                    <div style="font-size: 1.2rem; font-weight: 900; color: #333;">{row['姓名']}</div>
                                    <div style="font-size: 0.8rem; background: #F3F4F6; padding: 2px 8px; border-radius: 10px; color: #666;">{row.get('評估日期', '無日期')}</div>
                                </div>
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">📞 {row.get('電話', '無紀錄')}</div>
                                <div style="background: #F8F9FA; padding: 10px; border-radius: 8px; border: 1px solid #eee;">
                                    {details_html}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ 沒有符合條件的個案。")
            else:
                st.info("💡 請在上方選擇題目後，即可顯示設定條件與篩選結果。")

    # --- Tab 3: 物資統計 ---
    with tab3:
        inv = load_data("care_inventory", COLS_INV)
        if not inv.empty:
            inv['qty'] = pd.to_numeric(inv['總數量'], errors='coerce').fillna(0)
            
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 1.2rem; font-weight: 700; color: #4A4E69; margin-bottom: 10px;'>🏆 愛心捐贈芳名錄</div>", unsafe_allow_html=True)
                    donor_stat = inv.groupby('捐贈者')['qty'].sum().reset_index().sort_values('qty', ascending=False)
                    fig_donor = px.pie(donor_stat, values='qty', names='捐贈者', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    
                    # 加上這行：強制標籤在內部，太小的區塊會自動隱藏數字
                    fig_donor.update_traces(textposition='inside')
                    
                    # 強制設定為白底與深色字
                    fig_donor.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(color='#333333'), margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_donor, use_container_width=True, theme=None)
                    
            with c2:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 1.2rem; font-weight: 700; color: #4A4E69; margin-bottom: 10px;'>📦 物資種類結構</div>", unsafe_allow_html=True)
                    fig_sun = px.sunburst(inv, path=['物資類型', '物資內容'], values='qty', color='物資類型', color_discrete_sequence=px.colors.qualitative.Set3)
                    # 加入 font=dict(color='#333333') 強制字體為深灰/黑色
                    fig_sun.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(color='#333333'), margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_sun, use_container_width=True, theme=None)
        else:
            st.info("目前尚無庫存資料")
