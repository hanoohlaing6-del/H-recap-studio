import streamlit as st
import google.generativeai as genai
import yt_dlp

# Page Configuration
st.set_page_config(
    page_title="AI Movie Recap Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Movie Recap Generator")

# Sidebar - Payment & Contact Info
st.sidebar.title("👑 VIP Key / ဆက်သွယ်ရန်")

col1, col2 = st.sidebar.columns(2)
with col1:
    st.image("kpay.png", caption="KBZPay", use_container_width=True)
with col2:
    st.image("promptpay.png", caption="PromptPay", use_container_width=True)

st.sidebar.info("📌 ငွေလွှဲပြီးပါက ပြေစာ (Receipt) ကို Telegram သို့ ပို့ပေးပါရန်။")
st.sidebar.link_button("✈️ Telegram သို့ ဆက်သွယ်ရန်", "https://t.me/Han_Oo_Hlaing")

# Main Interface
st.subheader("Video Link (TikTok / YouTube / Facebook / Rednote / Douyin) ထည့်ပါ:")
video_url = st.text_input("URL Input", placeholder="https://vt.tiktok.com/...")

api_key = st.text_input("Google AI Studio API Key ထည့်ပါ (VIP မဟုတ်ပါက):", type="password")

if st.button("Generate Recap"):
    if not video_url:
        st.error("ကျေးဇူးပြု၍ Video Link ထည့်သွင်းပေးပါ။")
    elif not api_key:
        st.error("ကျေးဇူးပြု၍ API Key ထည့်သွင်းပေးပါ။")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            
            st.info("Video အချက်အလက်များ ရယူနေပါသည်...")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.tiktok.com/'
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'Video')
                description = info.get('description', '')
                
            st.success(f"Video တွေ့ရှိပါသည်: {title}")
            st.info("AI Recap ရေးသားနေပါသည်...")
            
            prompt = f"Please write a comprehensive and engaging movie/video recap based on the following title and description in Myanmar language:\nTitle: {title}\nDescription: {description}"
            response = model.generate_content(prompt)
            
            st.subheader("📝 Movie Recap Result:")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"အမှားအယွင်း ရှိပါသည်။ Error: {str(e)}")
