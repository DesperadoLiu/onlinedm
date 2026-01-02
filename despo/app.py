import streamlit as st
from google import genai  # 修改為新版導入方式
import os
import sys
import io
import sqlite3
import pandas as pd
import asyncio
import edge_tts
import warnings
import requests  # 用於獲取天氣資訊
from docx import Document
from datetime import datetime

# --- 0. 系統設定與警告抑制 ---
warnings.filterwarnings("ignore", category=FutureWarning)

# --- 1. 資料庫與資料夾設定 ---
DEFAULT_API_KEY = "" 
DOC_FOLDER = "./documents"
AUDIO_FOLDER = "./audio_records"
DB_FILE = "chat_history_v2.db"
# --- 設定 Logo 路徑 ---
LOGO_IMAGE = "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/01/2019-鬍鬚張-logo-07.png" 

for folder in [DOC_FOLDER, AUDIO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 自動產生 VBS 啟動檔功能 ---
def create_vbs_launcher():
    if os.name == 'nt':
        try:
            current_script = os.path.abspath(sys.argv[0])
            launcher_path = os.path.join(os.path.dirname(current_script), "啟動系統(隱藏CMD).vbs")
            if not os.path.exists(launcher_path):
                with open(launcher_path, "w", encoding="utf-8-sig") as f:
                    f.write(f'Set WshShell = CreateObject("WScript.Shell")\n')
                    f.write(f'WshShell.Run "streamlit run ""{current_script}""", 0\n')
                    f.write(f'Set WshShell = Nothing')
        except Exception:
            pass

create_vbs_launcher()

# --- 天氣抓取功能 ---
def get_weather_info():
    try:
        resp = requests.get("https://wttr.in/?format=%c+%t", timeout=3)
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        return "☀️" 
    return ""

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, mode TEXT, query TEXT, response TEXT, audio_path TEXT)''')
    c.execute("PRAGMA table_info(history)")
    columns = [column[1] for column in c.fetchall()]
    if 'audio_path' not in columns:
        c.execute("ALTER TABLE history ADD COLUMN audio_path TEXT")
    conn.commit()
    conn.close()

def save_to_db(mode, query, response, audio_path=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO history (timestamp, mode, query, response, audio_path) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mode, query, response, audio_path))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

# --- 2. 核心功能函式 ---
async def generate_neural_voice(text, output_path, voice_id, rate="+10%", pitch="+0Hz"):
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    await communicate.save(output_path)

def load_single_file(folder_path, filename):
    path = os.path.join(folder_path, filename)
    try:
        if filename.endswith(".docx"):
            return "\n".join([p.text for p in Document(path).paragraphs])
        elif filename.endswith((".xlsx", ".xls")):
            return pd.read_excel(path).to_string()
    except Exception as e:
        return f"讀取失敗 ({filename}): {e}"
    return ""

# --- 3. 專家角色與多國語言聲線矩陣定義 ---
ROLE_DEFINITIONS = {
    "🔍 通用策略諮詢": "你是一位資深行銷顧問，請基於文件提供專業策略建議，結構清晰，層次分明。",
    "✍️ 社群創意文案": "你是一位充滿創意的社群經理，語氣活潑，擅長使用 Emoji、Hook 標題，針對 Z 世代撰寫文案。",
    "📈 數據趨勢洞察": "你是一位數據分析專家，請深度解讀報表中的數據，指出異常與成長機會，並給出預算優化建議。",
    "📻 廣播廣告生成": "你是一位專業廣播腳本家，擅長撰寫具節奏感、聽覺畫面感的廣告詞，口語自然流暢。",
    "🛡️ 品牌規範審核": "你是一位品牌守護者，請嚴格比對提供的文件與使用者的內容，確保視覺與語氣符合品牌規範。"
}

VOICE_MATRIX = {
    "繁體中文": {"女聲": "zh-TW-HsiaoChenNeural", "男聲": "zh-TW-YunJheNeural"},
    "English": {"女聲": "en-US-EmmaNeural", "男聲": "en-US-BrianNeural"},
    "日本語": {"女聲": "ja-JP-NanamiNeural", "男聲": "ja-JP-KeitaNeural"},
    "한국어": {"女聲": "ko-KR-SunHiNeural", "男聲": "ko-KR-InGookNeural"},
    "Tiếng Việt": {"女聲": "vi-VN-HoaiMyNeural", "男聲": "vi-VN-NamMinhNeural"},
    "Português": {"女聲": "pt-BR-FranciscaNeural", "男聲": "pt-BR-AntonioNeural"},
    "简体中文": {"女聲": "zh-CN-XiaoxiaoNeural", "男聲": "zh-CN-YunxiNeural"}
}

# --- 4. 初始化介面 (強制深色模式設定) ---
st.set_page_config(layout="wide", page_title="星空極光 Pro | 行企AI輔助系統", page_icon="🎙️")

if "editable_script" not in st.session_state: st.session_state.editable_script = ""
if "audio_bytes" not in st.session_state: st.session_state.audio_bytes = None

# 抓取天氣圖示
weather_icon = get_weather_info()

# CSS 注入
st.markdown(f"""
    <style>
        .stApp {{ 
            background: radial-gradient(circle at center, #1B2735 0%, #090A0F 100%); 
            color: #E2E8F0; 
        }}
        [data-testid="stStatusWidget"] {{ display: none; }}
        .stDeployButton > button:after {{
            content: "發佈系統";
            font-size: 14px;
            color: white;
            visibility: visible;
        }}
        .stDeployButton > button > div {{
            visibility: hidden;
            width: 0px;
        }}
        #MainMenu > button:after {{
            content: "設定";
            font-size: 14px;
            color: #4CC9F0;
            margin-left: 5px;
        }}
        #big-welcome {{ 
            background: linear-gradient(90deg, #A2D2FF, #4361EE, #B5179E); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            font-size: 45px !important; 
            font-weight: 900; 
            text-align: center; 
            margin-bottom: 10px; 
        }}
        .current-time {{ 
            text-align: right; 
            color: #4CC9F0; 
            font-family: monospace; 
            font-weight: bold; 
            font-size: 32px !important;
            margin-bottom: 15px;
        }}
        .result-box {{ 
            background-color: rgba(255, 255, 255, 0.05); 
            padding: 25px; 
            border-radius: 15px; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            line-height: 1.6; 
        }}
    </style>
""", unsafe_allow_html=True)

# --- 5. 側邊欄控制 ---
with st.sidebar:
    col1, col2, col3 = st.columns([0.1, 2.5, 0.1])
    with col2:
        st.image(LOGO_IMAGE, width=180) 
        
    st.markdown("---")
    st.markdown("## 🛸 功能項目設置")
    api_key_input = st.text_input("輸入授權代碼", type="password")
    
    task_mode = st.selectbox("🎯 專家角色", list(ROLE_DEFINITIONS.keys()))

    st.divider()
    st.markdown("### 🌍 語言與翻譯設定")
    target_lang = st.selectbox(
        "選擇輸出語言", 
        ["繁體中文", "English", "日本語", "한국어", "Tiếng Việt", "Português", "简体中文"]
    )
    
    st.divider()
    st.markdown("### 🎙️ 語音設定")
    gender_choice = st.radio("配音員性別", ["女聲", "男聲"], horizontal=True)
    
    v_rate = st.slider("語速調整 (%)", -50, 50, 10, step=5)
    v_pitch = st.slider("音調調整 (Hz)", -20, 20, 0, step=1)
    
    selected_voice_id = VOICE_MATRIX[target_lang][gender_choice]
    st.info(f"當前配音：{target_lang} - {gender_choice}")
        
    rate_str = f"{'+' if v_rate >= 0 else ''}{v_rate}%"
    pitch_str = f"{'+' if v_pitch >= 0 else ''}{v_pitch}Hz"

# --- 6. 主頁面內容 ---
st.markdown(f'<p class="current-time">{weather_icon} 系統時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
st.markdown('<p id="big-welcome">歡迎使用行銷AI輔助，提升工作效能</p>', unsafe_allow_html=True)

tab_gen, tab_doc, tab_hist = st.tabs(["🚀 內容生成", "📂 知識庫管理", "📜 歷程對照"])

with tab_gen:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("💡 需求描述")
        all_files = sorted([f for f in os.listdir(DOC_FOLDER) if not f.startswith('.')])
        selected_files = st.multiselect("📢 選擇參考文件 (可多選，不選則參考全庫)", options=all_files)
        query_text = st.text_area("請輸入您的具體指令或調整建議...", height=200)

        col_btn1, col_btn2 = st.columns(2)
        btn_generate = col_btn1.button("🔥 啟動專家演算", use_container_width=True)
        
        btn_ab_test = False
        if task_mode == "✍️ 社群創意文案":
            btn_ab_test = col_btn2.button("🧪 一鍵生成 A/B 測試文案", use_container_width=True)

        if btn_generate or btn_ab_test:
            if not api_key_input:
                st.error("忘記輸入授權代碼")
            else:
                with st.status("專家思考中...", expanded=True) as status:
                    files_to_read = selected_files if selected_files else all_files
                    context = ""
                    excel_data = None
                    
                    for f in files_to_read:
                        context += f"\n--- 檔案內容: {f} ---\n{load_single_file(DOC_FOLDER, f)}\n"
                        if task_mode == "📈 數據趨勢洞察" and f.endswith((".xlsx", ".xls")):
                            try:
                                excel_data = pd.read_excel(os.path.join(DOC_FOLDER, f))
                            except: pass

                    system_prompt = ROLE_DEFINITIONS[task_mode]
                    system_prompt += f"\n\n[重要指令]：請全程使用「{target_lang}」進行回覆與內容撰寫。"
                    
                    if btn_ab_test:
                        system_prompt += "\n請同時提供三種不同風格的文案版本，並標註各自的優點。"
                    
                    final_prompt = f"系統設定：{system_prompt}\n\n知識庫內容：\n{context}\n\n用戶需求：{query_text}"
                    
                    # 使用新版 google-genai 進行內容生成
                    client = genai.Client(api_key=api_key_input)
                    response = client.models.generate_content(
                        model="gemini-2.5-flash", # 已修正模型名稱為穩定版本
                        contents=final_prompt
                    )
                    st.session_state.editable_script = response.text
                    
                    if excel_data is not None:
                        st.session_state.insight_df = excel_data
                    
                    status.update(label=f"✅ 內容已生成 ({target_lang})", state="complete")

    with col_right:
        st.subheader("🎯 生成成果")
        
        if task_mode == "📈 數據趨勢洞察" and "insight_df" in st.session_state:
            with st.expander("📊 數據趨勢自動可視化", expanded=True):
                df = st.session_state.insight_df
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    st.line_chart(df[numeric_cols])

        if st.session_state.editable_script:
            if task_mode == "📻 廣播廣告生成":
                edited_script = st.text_area("📄 腳本預覽與微調", value=st.session_state.editable_script, height=300)
                if st.button("🎙️ 合成高品質語音"):
                    with st.spinner(f"正在使用 {target_lang} {gender_choice}配音員合成中..."):
                        ts = datetime.now().strftime('%m%d_%H%M%S')
                        fpath = os.path.join(AUDIO_FOLDER, f"voice_{ts}.mp3")
                        asyncio.run(generate_neural_voice(edited_script, fpath, selected_voice_id, rate_str, pitch_str))
                        with open(fpath, "rb") as f:
                            st.session_state.audio_bytes = f.read()
                        save_to_db(task_mode, query_text[:20], edited_script, fpath)
                
                if st.session_state.audio_bytes:
                    st.audio(st.session_state.audio_bytes)
                    st.download_button("💾 下載音檔", st.session_state.audio_bytes, file_name=f"AD_{target_lang}_{gender_choice}.mp3")
            else:
                st.markdown(f'<div class="result-box">{st.session_state.editable_script}</div>', unsafe_allow_html=True)
                if btn_generate or btn_ab_test:
                    save_to_db(task_mode, query_text[:20], st.session_state.editable_script)

with tab_doc:
    uploaded = st.file_uploader("批次上傳文件", accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            with open(os.path.join(DOC_FOLDER, f.name), "wb") as sf: sf.write(f.getbuffer())
        st.rerun()
    for f in os.listdir(DOC_FOLDER):
        if not f.startswith('.'):
            c1, c2 = st.columns([5, 1])
            c1.write(f"📄 {f}")
            if c2.button("🗑️", key=f"del_{f}"):
                os.remove(os.path.join(DOC_FOLDER, f))
                st.rerun()

with tab_hist:
    h_df = load_history()
    for _, row in h_df.iterrows():
        with st.expander(f"🕒 {row['timestamp']} | {row['mode']}"):
            st.write(f"提問: {row['query']}")
            st.write(f"回應: {row['response']}")
            if row['audio_path'] and os.path.exists(str(row['audio_path'])):
                with open(str(row['audio_path']), "rb") as af: st.audio(af.read())

st.caption(f"© {datetime.now().year} 鬍鬚張股份有限公司 | 行銷企劃部AI輔助系統 | Powered by Gemini | Designed by Desperado")