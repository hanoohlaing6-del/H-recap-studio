import asyncio
import os
import datetime
import re
import streamlit as st
import yt_dlp
from google import genai

# Streamlit Page Setup
st.set_page_config(page_title="Movie Recap Generator", page_icon="🎬", layout="wide")
st.title("🎬 TikTok Movie Recap Generator")

# ----------------- ADMIN & VIP CONFIG -----------------
ADMIN_KEYS = ["ADMIN123", "JEWAN_MASTER"]

VIP_KEYS_DATABASE = {
    "VIP-202608-0001": "2026-08-31",
    "VIP-202609-0001": "2026-09-30",
}

if "purchased_keys" not in st.session_state:
    st.session_state.purchased_keys = {}

if "today" not in st.session_state:
    st.session_state.today = datetime.date.today()
if "usage_count" not in st.session_state or st.session_state.today != datetime.date.today():
    st.session_state.today = datetime.date.today()
    st.session_state.usage_count = 0

def validate_vip_key(key):
    if key in VIP_KEYS_DATABASE:
        expiry_date_str = VIP_KEYS_DATABASE[key]
        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        
        if today <= expiry_date:
            return True, f"VIP သက်တမ်းရှိသေးသည် (သက်တမ်းကုန်ရက်: {expiry_date_str})"
        else:
            return False, f"❌ ဤ VIP Key သည် {expiry_date_str} တွင် သက်တမ်းကုန်သွားပါပြီ။"
    return False, "Invalid Key"

# Subtitle Generator
def generate_pretty_srt(script_text, output_srt="myanmar_sub.srt"):
    raw_sentences = re.split(r'(?<=[။၊?\n])', script_text)
    short_lines = []
    
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        words = sentence.split()
        if len(words) > 8:
            for i in range(0, len(words), 7):
                short_lines.append(" ".join(words[i:i+7]))
        else:
            short_lines.append(sentence)

    with open(output_srt, "w", encoding="utf-8") as f:
        current_time = 0.0
        for idx, line in enumerate(short_lines, 1):
            duration = max(1.5, len(line.split()) * 0.35)
            start_sec = current_time
            end_sec = current_time + duration
            
            def format_time(seconds):
                millisec = int((seconds % 1) * 1000)
                sec = int(seconds) % 60
                mins = (int(seconds) // 60) % 60
                hrs = int(seconds) // 3600
                return f"{hrs:02d}:{mins:02d}:{sec:02d},{millisec:03d}"
            
            f.write(f"{idx}\n{format_time(start_sec)} --> {format_time(end_sec)}\n{line}\n\n")
            current_time = end_sec + 0.1

    return output_srt

# ----------------- SIDEBAR UI -----------------
st.sidebar.header("🔑 License & API Key")
gemini_api_key = st.sidebar.text_input("Gemini API Key (AIzaSy...)", type="password")
user_license_key = st.sidebar.text_input("VIP / Admin License Key", type="password").strip()

is_admin = user_license_key in ADMIN_KEYS
is_vip = False

if user_license_key:
    if is_admin:
        is_vip = True
        st.sidebar.success("👑 Admin Mode: Unlimited Access")
    else:
        is_valid_vip, vip_msg = validate_vip_key(user_license_key)
        if is_valid_vip:
            is_vip = True
            st.sidebar.success(f"⭐ VIP Member: {vip_msg}")
        elif "သက်တမ်းကုန်" in vip_msg:
            st.sidebar.error(vip_msg)
        else:
            st.sidebar.warning("❌ မှားယွင်းသော VIP Key ဖြစ်ပါသည်။")

if not is_vip:
    remaining = max(0, 2 - st.session_state.usage_count)
    st.sidebar.info(f"FREE Mode: ဒီနေ့အတွက် ကျန်ရှိသော အကြိမ်အရေအတွက် - {remaining} / 2")

# ----------------- MAIN TABS -----------------
tab1, tab2, tab3 = st.tabs(["🎬 Movie Recap Tool", "💳 VIP Key ဝယ်ယူရန် (MM / TH)", "🔍 ဝယ်ယူမှုအခြေအနေ စစ်ရန်"])

with tab1:
    tiktok_url = st.text_input("TikTok Video Link ကို ထည့်ပါ:")

    if st.button("Generate Recap"):
        if not gemini_api_key:
            st.error("ကျေးဇူးပြု၍ ဘေးဘက် (Sidebar) တွင် Gemini API Key ထည့်ပါ။")
        elif not tiktok_url:
            st.error("TikTok Video Link ထည့်ပါ။")
        elif not is_vip and st.session_state.usage_count >= 2:
            st.error("❌ ဒီနေ့အတွက် အခမဲ့ ၂ ကြိမ် ပြည့်သွားပါပြီ။ ထပ်မံအသုံးပြုလိုပါက 'VIP Key ဝယ်ယူရန်' Tab တွင် ဝယ်ယူပါ။")
        else:
            try:
                client = genai.Client(api_key=gemini_api_key)
                
                with st.spinner("⏳ Audio ဒေါင်းလုဒ်ဆွဲနေပါသည်..."):
                    ydl_opts = {'format': 'm4a/bestaudio/best', 'outtmpl': 'input_audio.m4a', 'quiet': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([tiktok_url])
                    audio_path = "input_audio.m4a"
                
                with st.spinner("⏳ AI ဖြင့် Script ရေးသားနေပါသည်..."):
                    audio_file = client.files.upload(file=audio_path)
                    prompt = "ဒီ Audio ကို နားထောင်ပြီး ရုပ်ရှင်ဇာတ်လမ်းတို (Movie Recap) Voiceover Script မြန်မာလို ရေးပေးပါ။"
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=[audio_file, prompt])
                    script = response.text
                    st.subheader("📝 ထွက်ရှိလာသော Script")
                    st.write(script)
                
                with st.spinner("⏳ မြန်မာ အသံဖိုင် ပြုလုပ်နေပါသည်..."):
                    import edge_tts
                    communicate = edge_tts.Communicate(script, "my-MM-NilarNeural")
                    asyncio.run(communicate.save("recap_voiceover.mp3"))
                    st.subheader("🔊 ထွက်ရှိလာသော အသံဖိုင်")
                    st.audio("recap_voiceover.mp3")

                with st.spinner("⏳ မြန်မာ စာတန်းထိုး (.srt) အလှ ထုတ်လုပ်နေပါသည်..."):
                    srt_file = generate_pretty_srt(script)
                    st.subheader("💬 ထွက်ရှိလာသော မြန်မာ စာတန်းထိုး (Subtitles)")
                    with open(srt_file, "r", encoding="utf-8") as f:
                        st.download_button(
                            label="📥 တစ်ကြောင်းချင်းစီ မြန်မာစာတန်းထိုး (.SRT) ဒေါင်းလုဒ်ဆွဲရန်",
                            data=f,
                            file_name="pretty_myanmar_subtitles.srt",
                            mime="text/plain"
                        )
                    
                if not is_vip:
                    st.session_state.usage_count += 1
                    
                st.success("🎉 အားလုံး ပြီးမြောက်ပါပြီ။ CapCut ထဲသို့ .srt ဖိုင် Import ထည့်၍ စာတန်းထိုး အသုံးပြုနိုင်ပါပြီ။")
                
            except Exception as e:
                st.error(f"အမှားအယွင်း ရှိပါသည်: {e}")

with tab2:
    st.header("💳 VIP Key ဝယ်ယူရန် (Myanmar & Thailand)")
    currency = st.radio("ငွေပေးချေမည့် နိုင်ငံ / ငွေကြေး ရွေးပါ:", ["🇲🇲 မြန်မာကျပ်ငွေ (45,000 MMK)", "🇹🇭 ထိုင်းဘတ်ငွေ (350 THB)"], horizontal=True)
    st.divider()
    
    if "🇲🇲" in currency:
        st.subheader("🇲🇲 မြန်မာဘဏ်များဖြင့် ငွေလွှဲရန် (၁ လစာ = 45,000 MMK)")
        col1, col2 = st.columns(2)
        with col1:
            st.info("📱 **KBZPay Account**\n\nName: U Jewan\nNo: 09XXXXXXXXX")
        with col2:
            st.success("📱 **WaveMoney Account**\n\nName: U Jewan\nNo: 09XXXXXXXXX")
    else:
        st.subheader("🇹🇭 ထိုင်းဘဏ်များဖြင့် ငွေလွှဲရန် (၁ လစာ = 350 THB)")
        col1, col2 = st.columns(2)
        with col1:
            st.info("🏦 **Kasikornbank (K-Bank)**\n\nName: Mr. Jewan\nAcc No: XXX-X-XXXXX-X")
        with col2:
            st.success("📱 **PromptPay (พร้อมเพย์)**\n\nName: Mr. Jewan\nPhone / ID: 08X-XXX-XXXX")

    st.divider()
    phone_no = st.text_input("သင့် ဖုန်းနံပါတ် (VIP Key ပြန်စစ်ရန်):", placeholder="09xxxxxxxxx သို့မဟုတ် 08xxxxxxxx")
    txn_id = st.text_input("Transaction ID / လွှဲမှတ်နံပါတ် (နောက်ဆုံး ၆ လုံး):", placeholder="123456")
    receipt = st.file_uploader("ငွေလွှဲပြေစာ Screenshot တင်ပါ:", type=["png", "jpg", "jpeg"])
    
    if st.button("Submit Payment Proof"):
        if not phone_no or not txn_id or not receipt:
            st.warning("⚠️ အချက်အလက်များကို အပြည့်အစုံ ဖြည့်စွက်ပေးပါ။")
        else:
            assigned_key = f"VIP-{datetime.date.today().strftime('%Y%m')}-{txn_id[-4:]}"
            VIP_KEYS_DATABASE[assigned_key] = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            st.session_state.purchased_keys[phone_no] = {"key": assigned_key, "status": "Approved", "txn": txn_id}
            st.success(f"🎉 ငွေလွှဲမှု အတည်ပြုပြီးပါပြီ! သင့် VIP Key အသစ်မှာ: **{assigned_key}** ဖြစ်ပါသည်။")

with tab3:
    st.header("🔍 ဝယ်ယူထားသော Key စစ်ဆေးရန်")
    search_phone = st.text_input("ဝယ်ယူစဉ်က ထည့်ခဲ့သော ဖုန်းနံပါတ် ရိုက်ထည့်ပါ:")
    if st.button("Check Key"):
        if search_phone in st.session_state.purchased_keys:
            data = st.session_state.purchased_keys[search_phone]
            st.success(f"✅ သင့် VIP Key: **{data['key']}** (Status: {data['status']})")
        else:
            st.error("❌ ဤဖုန်းနံပါတ်ဖြင့် ဝယ်ယူထားသော Key မရှိသေးပါ။")
