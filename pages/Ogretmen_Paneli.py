import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, time
import hashlib

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Okul Randevu Sistemi", layout="wide", initial_sidebar_state="collapsed")

# --- 2. AYARLAR VE YARDIMCI FONKSİYONLAR ---
SINIF_LISTESI = [f"{s}-{b}" for s in range(1, 5) for b in ["A", "B", "C", "D"]]

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def turkce_tarih_formatla(tarih_str):
    gunler_tr = {'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
                 'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'}
    try:
        t_obj = datetime.strptime(tarih_str, '%Y-%m-%d')
        return t_obj.strftime(f'%d.%m.%Y {gunler_tr.get(t_obj.strftime("%A"))}')
    except: return tarih_str

# --- 3. VERİTABANI BAĞLANTISI ---
def init_db():
    conn = sqlite3.connect('kurumsal_ajanda.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ogretmenler 
                 (id INTEGER PRIMARY KEY, ad_soyad TEXT, kullanici TEXT, 
                  sifre TEXT, brans_sinif TEXT, rol TEXT DEFAULT "ogretmen")''')
    c.execute('CREATE TABLE IF NOT EXISTS ogrenciler (id INTEGER PRIMARY KEY, ad_soyad TEXT, sinif TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS program (
                    id INTEGER PRIMARY KEY, tarih TEXT, saat TEXT, 
                    ogrenci_ad TEXT, notlar TEXT, durum TEXT DEFAULT 'Bos', ogretmen_id INTEGER)''')
    if not c.execute("SELECT * FROM ogretmenler WHERE kullanici='admin'").fetchone():
        c.execute("INSERT INTO ogretmenler (ad_soyad, kullanici, sifre, rol) VALUES (?, ?, ?, ?)", 
                  ('Sistem Yöneticisi', 'admin', make_hashes('admin123'), 'admin'))
    conn.commit()
    return conn

conn = init_db()

# --- 4. CSS TASARIM ---
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: white; }
        .day-header-wrapper { background-color: #1E232D; padding: 12px 20px; border-radius: 10px; border-left: 5px solid #28a745; margin: 25px 0 15px 0; }
        .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
        div[data-testid="column"] button:contains("Sil"), div[data-testid="column"] button:contains("İptal") { 
            background-color: #842029 !important; color: white !important; 
        }
        input { background-color: #FFFFFF !important; color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 5. GİRİŞ KONTROLÜ ---
if 'giris_yapildi' not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    with st.container(border=True):
        st.header("🔐 Kurumsal Giriş Paneli")
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap"):
            user = conn.execute("SELECT id, ad_soyad, rol, brans_sinif FROM ogretmenler WHERE kullanici=? AND sifre=?", 
                                (u, make_hashes(p))).fetchone()
            if user:
                st.session_state.giris_yapildi = True
                st.session_state.u_id, st.session_state.u_ad, st.session_state.u_rol, st.session_state.u_sinif = user
                st.rerun()
            else: st.error("Hatalı giriş!")
else:
    c_m1, c_m2 = st.columns([5,1])
    c_m1.success(f"👋 Hoş geldiniz, **{st.session_state.u_ad}**")
    if c_m2.button("🚪 Çıkış"):
        st.session_state.giris_yapildi = False
        st.rerun()

    # --- ADMIN PANELİ ---
    if st.session_state.u_rol == "admin":
        tab_ajanda, tab_ogretmen, tab_ogrenci = st.tabs(["🗓️ Haftalık Ajanda", "👨‍🏫 Öğretmen Yönetimi", "🎓 Öğrenci Yönetimi"])

        with tab_ogretmen:
            st.header("👨‍🏫 Öğretmen Yönetimi")
            col_o1, col_o2 = st.columns([1, 1.5])
            with col_o1:
                st.subheader("➕ Yeni Ekle")
                with st.form("yeni_o_form", clear_on_submit=True):
                    o_as = st.text_input("Ad Soyad")
                    o_br = st.selectbox("Sınıfı", SINIF_LISTESI)
                    o_ka = st.text_input("Kullanıcı Adı")
                    o_sf = st.text_input("Şifre", type="password")
                    if st.form_submit_button("Kaydet"):
                        conn.execute("INSERT INTO ogretmenler (ad_soyad, kullanici, sifre, brans_sinif) VALUES (?,?,?,?)", 
                                     (o_as, o_ka, make_hashes(o_sf), o_br))
                        conn.commit(); st.rerun()
            with col_o2:
                st.subheader("📝 Düzenle / Sil")
                o_df = pd.read_sql_query("SELECT * FROM ogretmenler WHERE rol='ogretmen' ORDER BY ad_soyad", conn)
                if not o_df.empty:
                    s_o = st.selectbox("Öğretmen Seç", o_df['ad_soyad'].tolist())
                    o_data = o_df[o_df['ad_soyad'] == s_o].iloc[0]
                    with st.form(key=f"edit_o_f_{o_data['id']}"):
                        g_o_ad = st.text_input("Ad Soyad", value=o_data['ad_soyad'])
                        g_o_ka = st.text_input("Kullanıcı Adı", value=o_data['kullanici'])
                        g_o_sn = st.selectbox("Sınıf", SINIF_LISTESI, index=SINIF_LISTESI.index(o_data['brans_sinif']) if o_data['brans_sinif'] in SINIF_LISTESI else 0)
                        g_o_sf = st.text_input("Yeni Şifre (Boşsa değişmez)", type="password")
                        if st.form_submit_button("💾 Güncelle"):
                            if g_o_sf:
                                conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici=?, brans_sinif=?, sifre=? WHERE id=?", 
                                             (g_o_ad, g_o_ka, g_o_sn, make_hashes(g_o_sf), o_data['id']))
                            else:
                                conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici=?, brans_sinif=? WHERE id=?", 
                                             (g_o_ad, g_o_ka, g_o_sn, o_data['id']))
                            conn.commit(); st.success("Güncellendi"); st.rerun()
                    if st.button("🗑️ Öğretmeni Sil", key=f"del_o_{o_data['id']}"):
                        conn.execute("DELETE FROM ogretmenler WHERE id=?", (o_data['id'],))
                        conn.commit(); st.rerun()

        with tab_ogrenci:
            st.header("🎓 Öğrenci Yönetimi")
            col_s1, col_s2 = st.columns([1, 1.5])
            with col_s1:
                st.subheader("➕ Yeni Öğrenci")
                with st.form("yeni_s_form", clear_on_submit=True):
                    s_as = st.text_input("Ad Soyad")
                    s_sn = st.selectbox("Sınıfı", SINIF_LISTESI)
                    if st.form_submit_button("Kaydet"):
                        conn.execute("INSERT INTO ogrenciler (ad_soyad, sinif) VALUES (?, ?)", (s_as, s_sn))
                        conn.commit(); st.rerun()
            with col_s2:
                st.subheader("📝 Liste")
                og_df = pd.read_sql_query("SELECT * FROM ogrenciler ORDER BY ad_soyad", conn)
                for idx, row in og_df.iterrows():
                    c_n, c_s, c_i = st.columns([2, 1, 1])
                    c_n.write(f"**{row['ad_soyad']}**")
                    c_s.write(f"`{row['sinif']}`")
                    with c_i.popover("📝 Düzenle"):
                        y_n = st.text_input("İsim", value=row['ad_soyad'], key=f"yn_{row['id']}")
                        y_s = st.selectbox("Sınıf", SINIF_LISTESI, index=SINIF_LISTESI.index(row['sinif']) if row['sinif'] in SINIF_LISTESI else 0, key=f"ys_{row['id']}")
                        if st.button("💾 Kaydet", key=f"sv_{row['id']}"):
                            conn.execute("UPDATE ogrenciler SET ad_soyad=?, sinif=? WHERE id=?", (y_n, y_s, row['id']))
                            conn.commit(); st.rerun()
                        if st.button("🗑️ Sil", key=f"rm_{row['id']}"):
                            conn.execute("DELETE FROM ogrenciler WHERE id=?", (row['id'],))
                            conn.commit(); st.rerun()
                    st.divider()

        with tab_ajanda:
            st.header("🗓️ Genel Ajanda")
            if 'h_offset' not in st.session_state: st.session_state.h_offset = 0
            ca1, ca2, ca3 = st.columns([1,2,1])
            if ca1.button("⬅️ Geri"): st.session_state.h_offset -= 1; st.rerun()
            if ca3.button("İleri ➡️"): st.session_state.h_offset += 1; st.rerun()
            days = [str((datetime.now().date() - timedelta(days=datetime.now().date().weekday()) + timedelta(weeks=st.session_state.h_offset) + timedelta(days=i))) for i in range(5)]
            for d in days:
                st.markdown(f'<div class="day-header-wrapper">🗓️ {turkce_tarih_formatla(d)}</div>', unsafe_allow_html=True)
                slots = conn.execute("SELECT id, saat, ogrenci_ad, durum FROM program WHERE tarih=? ORDER BY saat", (d,)).fetchall()
                if not slots:
                    with st.expander("➕ Saat Oluştur"):
                        c1, c2, c3 = st.columns(3)
                        s_t = c1.time_input("Başlangıç", time(9, 0), key=f"st_{d}")
                        e_t = c2.time_input("Bitiş", time(16, 0), key=f"et_{d}")
                        gap = c3.number_input("Dakika", 10, 60, 30, key=f"gp_{d}")
                        if st.button("Oluştur", key=f"gn_{d}"):
                            curr = datetime.combine(datetime.today(), s_t)
                            while curr <= datetime.combine(datetime.today(), e_t):
                                conn.execute("INSERT INTO program (tarih, saat) VALUES (?, ?)", (d, curr.strftime("%H:%M")))
                                curr += timedelta(minutes=gap)
                            conn.commit(); st.rerun()
                else:
                    cols = st.columns(8)
                    for i, (sid, saat, ogr, durum) in enumerate(slots):
                        with cols[i % 8]:
                            if durum == 'Bos':
                                if st.button(f"⚪ {saat}", key=f"ab_{sid}", help="Kapatmak için tıkla"):
                                    conn.execute("UPDATE program SET durum='Kapali' WHERE id=?", (sid,))
                                    conn.commit(); st.rerun()
                            elif durum == 'Kapali':
                                if st.button(f"🚫 {saat}", key=f"ak_{sid}", help="Açmak için tıkla"):
                                    conn.execute("UPDATE program SET durum='Bos' WHERE id=?", (sid,))
                                    conn.commit(); st.rerun()
                            else: st.button(f"🟢 {saat}", key=f"ad_{sid}", help=f"{ogr}")
                    if st.button("🗑️ Günü Sil", key=f"clr_{d}"):
                        conn.execute("DELETE FROM program WHERE tarih=?", (d,)); conn.commit(); st.rerun()

    # --- ÖĞRETMEN PANELİ ---
    else:
        t1, t2 = st.tabs(["🗓️ Randevu Al", "📝 Sınıfım"])
        with t1:
            st.header(f"🏫 {st.session_state.u_sinif} Planı")
            dolu = pd.read_sql_query("SELECT DISTINCT ogrenci_ad FROM program WHERE durum='Dolu'", conn)['ogrenci_ad'].tolist()
            ogrencilerim = pd.read_sql_query("SELECT ad_soyad FROM ogrenciler WHERE sinif=?", conn, params=(st.session_state.u_sinif,))['ad_soyad'].tolist()
            prog = pd.read_sql_query("SELECT * FROM program ORDER BY tarih, saat", conn)
            for d in prog['tarih'].unique():
                st.markdown(f'<div class="day-header-wrapper">🗓️ {turkce_tarih_formatla(d)}</div>', unsafe_allow_html=True)
                d_slots = prog[prog['tarih'] == d]
                cols = st.columns(8)
                for i, row in enumerate(d_slots.itertuples()):
                    with cols[i % 8]:
                        # --- DURUM: BOŞ ---
                        if row.durum == 'Bos':
                            with st.popover(f"⚪ {row.saat}", use_container_width=True):
                                f_list = [o for o in ogrencilerim if o not in dolu]
                                sec = st.selectbox("Öğrenci Seç", ["Seç..."] + f_list, key=f"ps_{row.id}")
                                if st.button("Randevuyu Kaydet", key=f"pb_{row.id}"):
                                    if sec != "Seç...":
                                        conn.execute("UPDATE program SET ogrenci_ad=?, durum='Dolu', ogretmen_id=? WHERE id=?", (sec, st.session_state.u_id, row.id))
                                        conn.commit(); st.rerun()
                                # "Saati Kapat" butonu buradan kaldırıldı.

                        # --- DURUM: KAPALI (Öğretmen müdahale edemez) ---
                        elif row.durum == 'Kapali': 
                            st.button(f"🚫 {row.saat}", key=f"pk_{row.id}", disabled=True, help="Yönetici tarafından kapatıldı.")
                        
                        # --- DURUM: DOLU ---
                        else:
                            is_mine = row.ogrenci_ad in ogrencilerim
                            with st.popover(f"{'🟢' if is_mine else '👤'} {row.saat}", use_container_width=True):
                                st.write(f"👤 {row.ogrenci_ad}")
                                if is_mine:
                                    if st.button("Randevuyu İptal Et", key=f"pi_{row.id}"):
                                        conn.execute("UPDATE program SET ogrenci_ad=NULL, durum='Bos', ogretmen_id=NULL WHERE id=?", (row.id,))
                                        conn.commit(); st.rerun()
                                else: 
                                    st.warning("Bu randevu başka bir sınıfa aittir.")
        with t2:
            st.header("📋 Sınıf Randevu Listesi")
            if ogrencilerim:
                # Sadece öğretmenin kendi sınıfındaki öğrencilerin randevularını getir
                q = "SELECT tarih, saat, ogrenci_ad FROM program WHERE ogrenci_ad IN ({}) AND durum='Dolu' ORDER BY tarih, saat".format(','.join(['?']*len(ogrencilerim)))
                res = conn.execute(q, ogrencilerim).fetchall()
                if res:
                    for t, s, o in res: 
                        st.info(f"📅 {turkce_tarih_formatla(t)} | ⏰ {s} | 👤 {o}")
                else:
                    st.write("Sınıfınızdan henüz randevu alan öğrenci bulunmuyor.")

conn.close()