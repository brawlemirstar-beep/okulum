import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Veli Girişi", layout="wide")

# Sabit Renk ve Mobil Uyumluluk CSS
st.markdown("""
    <style>
        .stApp { background-color: #0E1117 !important; }
        h1, h2, h3, span, label, p { color: white !important; }
        /* Input kutusunun içindeki yazıyı siyah yap (beyaz kutuda görünmesi için) */
        input { color: black !important; }
        /* Butonlar */
        .stButton button { background-color: #1E232D !important; color: white !important; font-weight: bold !important; }
        
        @media (max-width: 640px) {
            .stButton button { font-size: 14px !important; }
        }
    </style>
    <div style="background-color:#1E232D; padding:15px; border-radius:10px; text-align:center;">
        <h1 style="margin:0;">👩‍👦 VELİ GİRİŞİ</h1>
    </div>
""", unsafe_allow_html=True)

if st.button("⬅️ Ana Menü"):
    st.switch_page("app.py")

# --- GİRİŞ VE RANDEVU KODLARI BURAYA GELECEK ---
# (Önceki mesajdaki randevu alma mantığı aynı kalacak, sadece üstteki CSS ve linkler önemli)