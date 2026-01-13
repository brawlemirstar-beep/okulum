import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Öğretmen Paneli", layout="wide", initial_sidebar_state="collapsed")

# --- TARİH FORMATLAMA FONKSİYONU ---
def turkce_tarih_formatla(tarih_str):
    gunler_tr = {
        'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
        'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
    }
    try:
        tarih_obj = datetime.strptime(tarih_str, '%Y-%m-%d')
        ing_gun = tarih_obj.strftime('%A')
        tr_gun = gunler_tr.get(ing_gun, ing_gun)
        return tarih_obj.strftime(f'%d.%m.%Y {tr_gun}')
    except:
        return tarih_str

# --- CSS TASARIM ---
st.markdown("""
   <meta name="color-scheme" content="dark only">
    <style>
        /* 1. TÜM SİSTEMİN ARKA PLANINI VE YAZI RENGİNİ SABİTLE */
        /* Bu kısım telefonun modunu (light/dark) görmezden gelir */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0E1117 !important;
        }

        /* TÜM yazıların (Başlık, metin, etiket) rengini beyaza kilitle */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, div {
            color: #FFFFFF !important;
        }

        /* 2. BUTONLARI TELEFONDA GÖRÜNÜR YAP */
        .stButton>button {
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 1px solid #4A4A4A !important;
            width: 100% !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }

        /* Butonun üzerine gelince veya tıklayınca beyaz kalmasını sağla */
        .stButton>button:hover, .stButton>button:active, .stButton>button:focus {
            color: #1f77b4 !important;
            border-color: #1f77b4 !important;
            background-color: #262730 !important;
        }

        /* 3. GİRİŞ KUTULARI (Görünmemesinin temel sebebi) */
        /* Kutunun içini hafif gri yap, yazıyı ise SİYAH veya ÇOK KOYU yap */
        input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important; /* iOS için zorunlu */
        }

        /* 4. MOBİL EKRAN AYARI */
        @media (max-width: 640px) {
            .block-container {
                padding: 1rem !important;
            }
            .stButton>button {
                padding: 10px 5px !important;
                font-size: 14px !important;
            }
        }

        /* Streamlit üst bar ve menüyü gizle */
        header, [data-testid="stToolbar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

if st.button("⬅️ Ana Menüye Dön"): st.switch_page("app.py")

# --- OTURUM KONTROLÜ ---
if 'ogretmen_giris_yapildi' not in st.session_state:
    st.session_state.ogretmen_giris_yapildi = False

if not st.session_state.ogretmen_giris_yapildi:
    with st.container(border=True):
        st.subheader("🔐 Öğretmen Girişi")
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            conn = sqlite3.connect('okul_sistemi_final.db')
            user = conn.execute("SELECT id, ad_soyad FROM ogretmenler WHERE kullanici_adi=? AND sifre=?", (u, p)).fetchone()
            conn.close()
            if user:
                st.session_state.ogretmen_giris_yapildi = True
                st.session_state.ogretmen_id = user[0]
                st.session_state.ogretmen_ad = user[1]
                st.rerun()
            else:
                st.error("Hatalı bilgiler!")
else:
    col_h, col_c = st.columns([5,1])
    col_h.success(f"👋 Hoş geldiniz, **{st.session_state.ogretmen_ad}**")
    if col_c.button("🚪 Çıkış Yap"):
        st.session_state.ogretmen_giris_yapildi = False
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["📅 Saat Oluştur", "⚡ Takvim Yönetimi", "📝 Alınan Randevular", "🗑️ Gün Sil"])
    conn = sqlite3.connect('okul_sistemi_final.db')

    # --- 1. SAAT OLUŞTURMA ---
    with t1:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            t_sec = c1.date_input("Tarih", min_value=datetime.today())
            b_s = c2.time_input("Başlangıç", value=datetime.strptime("09:00", "%H:%M").time())
            s_s = c3.time_input("Bitiş", value=datetime.strptime("17:00", "%H:%M").time())
            if st.button("30 Dakikalık Slotları Kaydet"):
                curr = datetime.combine(t_sec, b_s)
                while curr < datetime.combine(t_sec, s_s):
                    conn.execute("INSERT INTO randevular (ogretmen_id, tarih, saat, durum) VALUES (?,?,?, 'Bos')", 
                                 (st.session_state.ogretmen_id, t_sec.strftime('%Y-%m-%d'), curr.strftime('%H:%M')))
                    curr += timedelta(minutes=30)
                conn.commit()
                st.success("Takvim başarıyla oluşturuldu!")

    # --- 2. TAKVİM YÖNETİMİ (HOVER ÖZELLİĞİ EKLENDİ) ---
    with t2:
        st.subheader("🛠️ Slotları Manuel Yönet")
        # Öğrenci bilgilerini JOIN ile çekiyoruz ki hover'da gösterelim
        query = """
            SELECT r.id, r.tarih, r.saat, r.durum, r.veli_tc, o.ad_soyad, o.okul_no 
            FROM randevular r 
            LEFT JOIN ogrenciler o ON r.veli_tc = o.tc_no 
            WHERE r.ogretmen_id=? 
            ORDER BY r.tarih, r.saat
        """
        randevular = conn.execute(query, (st.session_state.ogretmen_id,)).fetchall()
        gunler = sorted(list(set([r[1] for r in randevular])))
        
        for gun in gunler:
            with st.container(border=True):
                st.markdown(f'<div class="date-header">🗓️ {turkce_tarih_formatla(gun)}</div>', unsafe_allow_html=True)
                gunun_slotlari = [r for r in randevular if r[1] == gun]
                cols = st.columns(6)
                for i, (sid, tarih, saat, durum, v_sahibi, o_ad, o_no) in enumerate(gunun_slotlari):
                    with cols[i % 6]:
                        if durum == "Bos":
                            if st.button(f"🟢 {saat}", key=f"h_m_{sid}", help="Boş Slot - Kapatmak için tıkla"):
                                conn.execute("UPDATE randevular SET durum='Dolu', veli_tc='KAPALI' WHERE id=?", (sid,))
                                conn.commit(); st.rerun()
                        elif v_sahibi == "KAPALI":
                            if st.button(f"🚫 {saat}", key=f"h_m_{sid}", help="Sizin tarafınızdan kapatıldı"):
                                conn.execute("UPDATE randevular SET durum='Bos', veli_tc=NULL WHERE id=?", (sid,))
                                conn.commit(); st.rerun()
                        else:
                            # BURASI HOVER ÖZELLİĞİ: help parametresi öğrenci ismini gösterir
                            hover_bilgi = f"👤 Öğrenci: {o_ad} (No: {o_no})"
                            st.button(f"👤 {saat}", key=f"h_m_{sid}", disabled=True, help=hover_bilgi)

    # --- 3. ALINAN RANDEVULAR ---
    with t3:
        st.subheader("📝 Alınan Randevu Listesi")
        if 'h_iptal_id' in st.session_state:
            st.error("🚨 Bu randevuyu iptal etmek üzeresiniz. Onaylıyor musunuz?")
            o1, o2 = st.columns(2)
            if o1.button("✅ Evet, İptal Et", key="onay_evet"):
                conn.execute("UPDATE randevular SET veli_tc=NULL, durum='Bos' WHERE id=?", (st.session_state.h_iptal_id,))
                conn.commit(); del st.session_state.h_iptal_id; st.rerun()
            if o2.button("🔙 Vazgeç", key="onay_hayir"):
                del st.session_state.h_iptal_id; st.rerun()

        liste = conn.execute("""
            SELECT r.id, r.tarih, r.saat, o.ad_soyad, o.okul_no 
            FROM randevular r 
            JOIN ogrenciler o ON r.veli_tc = o.tc_no 
            WHERE r.ogretmen_id=? AND r.veli_tc != 'KAPALI'
            ORDER BY r.tarih, r.saat
        """, (st.session_state.ogretmen_id,)).fetchall()

        if liste:
            for rid, rt, rs, ra, rno in liste:
                with st.container(border=True):
                    col_bilgi, col_islem = st.columns([4,1])
                    col_bilgi.write(f"📅 **{turkce_tarih_formatla(rt)}** | ⏰ **{rs}** | 👤 **{ra}** (No: {rno})")
                    if col_islem.button("İptal Et", key=f"l_ipt_{rid}"):
                        st.session_state.h_iptal_id = rid
                        st.rerun()
        else:
            st.info("Henüz alınmış bir randevu bulunmuyor.")

    # --- 4. GÜN SİLME ---
    with t4:
        st.subheader("🗑️ Tarih Bazlı Temizlik")
        t_list = conn.execute("SELECT DISTINCT tarih FROM randevular WHERE ogretmen_id=?", (st.session_state.ogretmen_id,)).fetchall()
        if t_list:
            secilen = st.selectbox("Silinecek Tarih", [t[0] for t in t_list])
            st.warning(f"Dikkat: {turkce_tarih_formatla(secilen)} tarihindeki TÜM saatler silinecektir.")
            if st.button("⚠️ Seçili Tarihi Tamamen Sil"):
                conn.execute("DELETE FROM randevular WHERE ogretmen_id=? AND tarih=?", (st.session_state.ogretmen_id, secilen))
                conn.commit(); st.rerun()
        else:
            st.write("Silinecek kayıt yok.")

    conn.close()