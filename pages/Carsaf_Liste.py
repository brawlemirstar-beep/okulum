import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Haftalık Çizelge", layout="wide")

# --- CSS (Hem Ekran Hem Yazıcı İçin Görünürlük Garantisi) ---
st.markdown("""
    <style>
        /* EKRAN AYARLARI (Koyu Tema Sabitleme) */
        .stApp { 
            background-color: #0E1117 !important; 
            color: #FFFFFF !important; 
        }
        
        /* Navigasyon Alanı */
        .nav-btns { margin-bottom: 15px; padding: 10px; border-radius: 10px; background-color: #1c2128; }

        /* Yazdırılan Kibar Tarih Yazısı */
        .header-info {
            font-size: 0.9rem;
            font-style: italic;
            color: #4ade80; /* Parlak Yeşil */
            padding: 5px 0;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .calendar-row { display: flex; width: 100%; margin-bottom: -1px; }

        /* Hücreler */
        .cell {
            flex: 1;
            border: 1px solid #444;
            height: 40px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 2px;
            font-size: 0.75rem;
            background-color: #1c2128; /* Hücre içi koyu zemin */
        }

        /* Saat Hücresi */
        .time-cell {
            flex: 0.35;
            background-color: #2d333b !important;
            color: #4ade80 !important;
            font-weight: bold;
        }

        /* Gün Başlıkları */
        .day-title {
            flex: 1;
            background-color: #238636 !important;
            color: white !important;
            font-weight: bold;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #444;
            font-size: 0.7rem;
            line-height: 1.2;
        }

        .day-title-container { display: flex; width: 100%; }
        .time-title-spacer { flex: 0.35; }

        /* İsim Metni (Ekranda Kesin Beyaz) */
        .name-text { 
            font-weight: bold; 
            color: #FFFFFF !important; 
            width: 100%; 
            word-wrap: break-word; 
        }
        
        .note-text { font-size: 0.6rem; color: #adbac7; margin-top: 1px; }

        /* YAZDIRMA AYARLARI (Siyah-Beyaz Zıtlık) */
        @media print {
            @page { size: portrait; margin: 0.3cm; }
            [data-testid="stSidebar"], [data-testid="stHeader"], .stButton, .nav-btns {
                display: none !important;
            }
            .stApp { background-color: white !important; color: black !important; }
            .main .block-container { padding: 0 !important; margin: 0 !important; }
            
            .calendar-row { border-bottom: 1px solid #000 !important; }
            .cell { 
                border: 1px solid #000 !important; 
                background-color: white !important; 
                color: black !important; 
            }
            .time-cell { 
                background-color: #f0f0f0 !important; 
                color: black !important; 
            }
            .day-title { 
                background-color: #eee !important; 
                color: black !important; 
                border: 1px solid #000 !important; 
            }
            .name-text { color: black !important; } /* Yazdırırken isimler Siyah olur */
            .header-info { color: black !important; border-bottom: 1px solid #000 !important; }
        }
    </style>
""", unsafe_allow_html=True)

conn = sqlite3.connect('kurumsal_ajanda.db', check_same_thread=False)

if 'h_offset' not in st.session_state: st.session_state.h_offset = 0

# --- NAVİGASYON ---
st.markdown('<div class="nav-btns">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1,1,4])
with c1: 
    if st.button("⬅️ Önceki Hafta"): st.session_state.h_offset -= 1; st.rerun()
with c2: 
    if st.button("Sonraki Hafta ➡️"): st.session_state.h_offset += 1; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Tarih Hesaplamaları
base_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday()) + timedelta(weeks=st.session_state.h_offset)
days_dates = [base_date + timedelta(days=i) for i in range(5)]
days_str = [d.strftime('%Y-%m-%d') for d in days_dates]

# --- KİBAR TARİH BİLGİSİ ---
tarih_araligi_metni = f"📅 Program Aralığı: {days_dates[0].strftime('%d/%m/%Y')} - {days_dates[-1].strftime('%d/%m/%Y')}"
st.markdown(f'<div class="header-info">{tarih_araligi_metni}</div>', unsafe_allow_html=True)

# Saatleri çek
saat_listesi = [s[0] for s in conn.execute(
    "SELECT DISTINCT saat FROM program WHERE tarih BETWEEN ? AND ? ORDER BY saat", 
    (days_str[0], days_str[-1])).fetchall()]

if not saat_listesi:
    st.info("💡 Seçili hafta için planlanmış bir randevu bulunmuyor.")
else:
    # BAŞLIK SATIRI
    gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    header_html = f'<div class="day-title-container"><div class="time-title-spacer"></div>'
    for i, d in enumerate(days_dates):
        tarih_etiket = f"{d.strftime('%d/%m/%Y')}<br>{gun_isimleri[i]}"
        header_html += f'<div class="day-title">{tarih_etiket}</div>'
    header_html += '</div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # VERİ SATIRLARI
    for s in saat_listesi:
        row_html = f'<div class="calendar-row">'
        row_html += f'<div class="cell time-cell">{s}</div>'
        
        for d_str in days_str:
            r = conn.execute("SELECT ogrenci_ad, notlar, durum FROM program WHERE tarih=? AND saat=?", (d_str, s)).fetchone()
            
            if r and r[2] == 'Dolu':
                row_html += f'''
                    <div class="cell">
                        <div class="name-text">{r[0]}</div>
                        <div class="note-text">{r[1][:12] if r[1] else ''}</div>
                    </div>'''
            else:
                row_html += '<div class="cell" style="background-color: transparent;"></div>'
        
        row_html += '</div>'
        st.markdown(row_html, unsafe_allow_html=True)

conn.close()