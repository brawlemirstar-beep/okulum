import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, time
import hashlib

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Yönetim Paneli (Admin)", layout="wide")

# --- LOGIN SİSTEMİ (TÜM UYGULAMAYI KORUR) ---
if 'admin_oturum' not in st.session_state:
    st.session_state.admin_oturum = False

if not st.session_state.admin_oturum:
    st.markdown("""
        <style>
        /* 1. TÜM SAYFAYI KARART */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
    }

    /* 2. TÜM YAZILARI BEYAZA ZORLA */
    h1, h2, h3, h4, h5, h6, p, span, label, li, div {
        color: #FFFFFF !important;
    }

    /* 3. INPUT VE SEÇİM KUTULARINI KİLİTLE */
    input, select, textarea, div[data-baseweb="select"], [role="listbox"] {
        background-color: #1E232D !important;
        color: white !important;
        border: 1px solid #28a745 !important;
        -webkit-text-fill-color: white !important; /* Safari için kritik */
    }

    /* 4. BUTONLARI RENKLENDİR */
    .stButton button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }
    
    /* 5. SEKMELER (TABS) ÇÖZÜMÜ */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
    }
    button[data-baseweb="tab"] p {
        color: #FFFFFF !important;
        font-size: 16px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 2px solid #28a745 !important;
    }

    /* 6. AÇILIR PENCERELER (POPOVER) */
    [data-testid="stPopoverContent"] {
        background-color: #1E232D !important;
        color: white !important;
        border: 1px solid #28a745 !important;
    }

    /* 7. YAN MENÜ (SIDEBAR) */
    [data-testid="stSidebar"] {
        background-color: #1E232D !important;
    }
            .login-box { background-color: #1E232D; padding: 30px; border-radius: 15px; border: 1px solid #28a745; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 Kurumsal Yönetim Girişi")
    with st.container():
        with st.form("admin_login"):
            sifre = st.text_input("Yönetici Şifresi", type="password")
            if st.form_submit_button("Sistemi Aç"):
                if sifre == "admin123": # ŞİFREN BURASIDIR
                    st.session_state.admin_oturum = True
                    st.rerun()
                else:
                    st.error("Hatalı Şifre!")
    st.stop() 

# --- 2. SINIF LİSTESİ ---
SINIF_LISTESI = [f"{s}-{b}" for s in range(1, 5) for b in ["A", "B", "C", "D"]]

# --- 3. GÜVENLİK VE VERİTABANI ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

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

# --- 4. CSS TASARIM (ORİJİNAL STİLİN) ---
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: white; }
        .day-header-wrapper { background-color: #1E232D; padding: 12px 20px; border-radius: 10px; border-left: 5px solid #28a745; margin: 25px 0 15px 0; }
        .day-title { font-weight: bold; font-size: 1.1rem; margin: 0; }
        .stButton button { width: 100%; border-radius: 8px; }
        div[data-testid="column"] button:contains("Sil") { background-color: #842029 !important; color: white !important; }
        @media print {
            header, footer, .stSidebar, [data-testid="stHeader"], [data-testid="stLayoutWrapper"], [data-baseweb="tab-list"], [data-testid="stMarkdownContainer"]   
            .stButton, stAppToolbar, .stButton button, .nav-buttons, .day-header-wrapper, stElementContainer, .no-print { display: none !important; }
            .stApp { background-color: white !important; color: black !important; }
            .print-only-table { display: block !important; width: 100% !important; color: black !important; }
            table { width: 100% !important; border-collapse: collapse !important; border: 2px solid black !important; }
            th, td { border: 1px solid black !important; padding: 2px 6px !important; text-align: left !important; color: black !important; font-size: 10pt !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --- 5. YAN MENÜ (SADECE GİRİŞ YAPILDIYSA GÖRÜNÜR) ---
with st.sidebar:
    if st.session_state.admin_oturum:
        st.header("🛠️ Yönetim Araçları")
        st.write("Giriş Yapıldı: Admin")
        st.divider()
        if st.button("🔴 Oturumu Kapat"):
            st.session_state.admin_oturum = False
            st.rerun()

# --- 6. ANA SEKMELER ---
tab_ajanda, tab_ogretmen, tab_ogrenci = st.tabs(["🗓️ Haftalık Ajanda", "👨‍🏫 Öğretmen Yönetimi", "🎓 Öğrenci Yönetimi"])

# --- TAB 1: ÖĞRENCİ YÖNETİMİ ---
with tab_ogrenci:
    st.header("🎓 Öğrenci Kayıt ve Detaylı Düzenleme")
    col_std_ekle, col_std_duzenle = st.columns([1, 1.5])
    with col_std_ekle:
        st.subheader("➕ Yeni Öğrenci Ekle")
        with st.form("yeni_ogrenci_form", clear_on_submit=True):
            std_as = st.text_input("Öğrenci Ad Soyad")
            std_sn = st.selectbox("Sınıfı", SINIF_LISTESI)
            if st.form_submit_button("Öğrenciyi Kaydet"):
                if std_as:
                    conn.execute("INSERT INTO ogrenciler (ad_soyad, sinif) VALUES (?, ?)", (std_as, std_sn))
                    conn.commit(); st.success(f"{std_as} eklendi!"); st.rerun()
    with col_std_duzenle:
            st.subheader("📝 Düzenle / Sil")
            ogrenciler_df = pd.read_sql_query("SELECT * FROM ogrenciler ORDER BY ad_soyad", conn)
            if not ogrenciler_df.empty:
                secilen_std_ad = st.selectbox("Öğrenci Seç", ogrenciler_df['ad_soyad'].tolist(), key="std_edit_sb")
                s_data = ogrenciler_df[ogrenciler_df['ad_soyad'] == secilen_std_ad].iloc[0]
                with st.container(border=True):
                    g_std_as = st.text_input("Ad Soyad", value=s_data['ad_soyad'], key=f"std_n_{s_data['id']}")
                    idx_sinif = SINIF_LISTESI.index(s_data['sinif']) if s_data['sinif'] in SINIF_LISTESI else 0
                    g_std_sn = st.selectbox("Sınıf", SINIF_LISTESI, index=idx_sinif, key=f"std_s_{s_data['id']}")
                    c1, c2 = st.columns(2)
                    if c1.button("💾 Güncelle", use_container_width=True, key=f"ub_{s_data['id']}"):
                        conn.execute("UPDATE ogrenciler SET ad_soyad=?, sinif=? WHERE id=?", (g_std_as, g_std_sn, int(s_data['id'])))
                        conn.commit(); st.success("Güncellendi"); st.rerun()
                    if c2.button("🗑️ Sil", use_container_width=True, key=f"db_{s_data['id']}"):
                        conn.execute("DELETE FROM ogrenciler WHERE id=?", (int(s_data['id']),))
                        conn.commit(); st.warning("Silindi"); st.rerun()

# --- TAB 2: ÖĞRETMEN YÖNETİMİ ---
with tab_ogretmen:
    st.header("👨‍🏫 Öğretmen Kayıt")
    col_o_ekle, col_o_duzenle = st.columns([1, 1.5])
    with col_o_ekle:
        with st.form("yeni_o_form", clear_on_submit=True):
            o_as = st.text_input("Ad Soyad")
            o_br = st.text_input("Branş")
            o_ka = st.text_input("Kullanıcı")
            o_sf = st.text_input("Şifre", type="password")
            if st.form_submit_button("Kaydet"):
                conn.execute("INSERT INTO ogretmenler (ad_soyad, kullanici, sifre, brans_sinif) VALUES (?,?,?,?)", (o_as, o_ka, make_hashes(o_sf), o_br))
                conn.commit(); st.success("Eklendi"); st.rerun()
    with col_o_duzenle:
        o_df = pd.read_sql_query("SELECT * FROM ogretmenler WHERE rol='ogretmen' ORDER BY ad_soyad", conn)
        if not o_df.empty:
            s_o_ad = st.selectbox("Öğretmen Seç", o_df['ad_soyad'].tolist(), key="o_sel")
            o_data = o_df[o_df['ad_soyad'] == s_o_ad].iloc[0]
            with st.container(border=True):
                go_as = st.text_input("Ad Soyad", value=o_data['ad_soyad'], key=f"t_n_{o_data['id']}")
                go_ka = st.text_input("Kullanıcı", value=o_data['kullanici'], key=f"t_u_{o_data['id']}")
                go_sf = st.text_input("Yeni Şifre", type="password", key=f"t_p_{o_data['id']}")
                b1, b2 = st.columns(2)
                if b1.button("💾 Kaydet", key=f"tub_{o_data['id']}"):
                    if go_sf: conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici=?, sifre=? WHERE id=?", (go_as, go_ka, make_hashes(go_sf), int(o_data['id'])))
                    else: conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici=? WHERE id=?", (go_as, go_ka, int(o_data['id'])))
                    conn.commit(); st.success("Güncellendi"); st.rerun()
                if b2.button("🗑️ Sil", key=f"tdb_{o_data['id']}"):
                    conn.execute("DELETE FROM ogretmenler WHERE id=?", (int(o_data['id']),))
                    conn.commit(); st.warning("Silindi"); st.rerun()

# --- TAB 3: HAFTALIK AJANDA ---
with tab_ajanda:
    if 'h_offset' not in st.session_state: st.session_state.h_offset = 0
    cn1, _, cn3 = st.columns([1,2,1])
    if cn1.button("⬅️ Önceki Hafta"): st.session_state.h_offset -= 1; st.rerun()
    if cn3.button("Sonraki Hafta ➡️"): st.session_state.h_offset += 1; st.rerun()

    days = [str((datetime.now().date() - timedelta(days=datetime.now().date().weekday()) + timedelta(weeks=st.session_state.h_offset) + timedelta(days=i))) for i in range(5)]
    randevulular = pd.read_sql_query("SELECT DISTINCT ogrenci_ad FROM program WHERE durum='Dolu'", conn)['ogrenci_ad'].tolist()
    ogrenci_df = pd.read_sql_query("SELECT ad_soyad || ' (' || sinif || ')' as g, ad_soyad FROM ogrenciler", conn)

    for day in days:
        if st.session_state.get(f"pv_{day}", False):
            rows = conn.execute(f"SELECT saat, ogrenci_ad, notlar, durum FROM program WHERE tarih='{day}' ORDER BY saat").fetchall()
            st.markdown(f'<div class="print-only-table" style="background:white; padding:10px; color:black;"><h4 style="text-align:center;">{day}</h4><table style="width:100%; border:1px solid black;"><thead><tr><th>SAAT</th><th>ÖĞRENCİ</th><th>NOT</th></tr></thead><tbody>' + "".join([f'<tr><td>{r[0]}</td><td>{r[1] if r[1] else ("(Kapalı)" if r[3]=="Kapali" else "")}</td><td>{r[2] if r[2] else ""}</td></tr>' for r in rows]) + '</tbody></table></div>', unsafe_allow_html=True)
            if st.button("❌ Kapat", key=f"cpv_{day}"): st.session_state[f"pv_{day}"] = False; st.rerun()

        st.markdown(f'<div class="day-header-wrapper"><p class="day-title">🗓️ {day}</p></div>', unsafe_allow_html=True)
        slots = conn.execute("SELECT id, saat, ogrenci_ad, notlar, durum FROM program WHERE tarih=? ORDER BY saat", (day,)).fetchall()
        
        # --- PROGRAM KURMA VE TEKLİ SAAT EKLEME ---
        col_kur1, col_kur2 = st.columns(2)
        with col_kur1.expander(f"➕ {day} Tek Saat Ekle"):
            tek_s = st.time_input("Saat", value=time(9,0), key=f"tek_s_{day}")
            if st.button("Ekle", key=f"tek_b_{day}"):
                s_str = tek_s.strftime("%H:%M")
                if not conn.execute("SELECT id FROM program WHERE tarih=? AND saat=?", (day, s_str)).fetchone():
                    conn.execute("INSERT INTO program (tarih, saat) VALUES (?, ?)", (day, s_str))
                    conn.commit(); st.rerun()
                else: st.error("Saat zaten var!")

        with col_kur2.expander(f"⚙️ {day} Program Kur"):
            c1, c2, c3 = st.columns(3)
            st_t = c1.time_input("Başlangıç", time(9, 0), key=f"s_{day}")
            en_t = c2.time_input("Bitiş", time(16, 0), key=f"e_{day}")
            gap = c3.number_input("Aralık", 10, 120, 45, key=f"g_{day}")
            if st.button("Kur", key=f"gen_{day}"):
                curr = datetime.combine(datetime.today(), st_t)
                while curr <= datetime.combine(datetime.today(), en_t):
                    s_str = curr.strftime("%H:%M")
                    if not conn.execute("SELECT id FROM program WHERE tarih=? AND saat=?", (day, s_str)).fetchone():
                        conn.execute("INSERT INTO program (tarih, saat) VALUES (?, ?)", (day, s_str))
                    curr += timedelta(minutes=gap)
                conn.commit(); st.rerun()

        # --- SAAT KUTULARI ---
        if slots:
            cols = st.columns(8)
            for i, row in enumerate(slots):
                sid, saat, ogr, ntl, durum = row
                with cols[i % 8]:
                    if durum == 'Bos':
                        with st.popover(f"⚪ {saat}", use_container_width=True):
                            f_ogr = [r['g'] for _, r in ogrenci_df.iterrows() if r['ad_soyad'] not in randevulular]
                            sec = st.selectbox("Öğrenci", ["Seç..."] + f_ogr, key=f"sel_{sid}")
                            nt = st.text_input("Not", key=f"n_{sid}")
                            if st.button("Kaydet", key=f"sv_{sid}"):
                                if sec != "Seç...":
                                    conn.execute("UPDATE program SET ogrenci_ad=?, durum='Dolu', notlar=? WHERE id=?", (sec.split(' (')[0], nt, sid))
                                    conn.commit(); st.rerun()
                            if st.button("Kapat", key=f"cl_{sid}"): conn.execute("UPDATE program SET durum='Kapali' WHERE id=?", (sid,)); conn.commit(); st.rerun()
                    elif durum == 'Kapali':
                        with st.popover(f"🟥 {saat}", use_container_width=True):
                            if st.button("Aç", key=f"op_{sid}"): conn.execute("UPDATE program SET durum='Bos' WHERE id=?", (sid,)); conn.commit(); st.rerun()
                    else:
                        with st.popover(f"🟢 {saat}", use_container_width=True):
                            st.success(f"👤 {ogr}"); st.info(f"📝 {ntl if ntl else 'Not yok.'}")
                            if st.button("Sil", key=f"del_{sid}"): conn.execute("UPDATE program SET ogrenci_ad=NULL, durum='Bos', notlar=NULL WHERE id=?", (sid,)); conn.commit(); st.rerun()
        
        ca = st.columns([0.15, 0.15, 0.7]) 
        if ca[0].button("🖨️ Yazdır", key=f"p_{day}"): st.session_state[f"pv_{day}"] = True; st.rerun()
        if ca[1].button("🗑️ Günü Sil", key=f"clr_{day}"): conn.execute("DELETE FROM program WHERE tarih=?", (day,)); conn.commit(); st.rerun()

conn.close()