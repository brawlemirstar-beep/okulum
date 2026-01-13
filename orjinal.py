import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, time
import hashlib

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Yönetim Paneli (Admin)", layout="wide")

# --- 2. SINIF LİSTESİ OTOMATİSYONU (1-4 Sınıf, A-D Şube) ---
SINIF_LISTESI = [f"{s}-{b}" for s in range(1, 5) for b in ["A", "B", "C", "D"]]

# --- 3. GÜVENLİK VE VERİTABANI BAĞLANTISI ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = sqlite3.connect('kurumsal_ajanda.db', check_same_thread=False)
    c = conn.cursor()
    # Öğretmenler Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS ogretmenler 
                 (id INTEGER PRIMARY KEY, ad_soyad TEXT, kullanici TEXT, 
                  sifre TEXT, brans_sinif TEXT, rol TEXT DEFAULT "ogretmen")''')
    # Öğrenciler Tablosu
    c.execute('CREATE TABLE IF NOT EXISTS ogrenciler (id INTEGER PRIMARY KEY, ad_soyad TEXT, sinif TEXT)')
    # Randevu/Program Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS program (
                    id INTEGER PRIMARY KEY, tarih TEXT, saat TEXT, 
                    ogrenci_ad TEXT, notlar TEXT, durum TEXT DEFAULT 'Bos', ogretmen_id INTEGER)''')
    
    if not c.execute("SELECT * FROM ogretmenler WHERE kullanici='admin'").fetchone():
        c.execute("INSERT INTO ogretmenler (ad_soyad, kullanici, sifre, rol) VALUES (?, ?, ?, ?)", 
                  ('Sistem Yöneticisi', 'admin', make_hashes('admin123'), 'admin'))
    conn.commit()
    return conn

conn = init_db()

# --- 4. CSS TASARIM (ORİJİNAL STİL) ---
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: white; }
        .day-header-wrapper { background-color: #1E232D; padding: 12px 20px; border-radius: 10px; border-left: 5px solid #28a745; margin: 25px 0 15px 0; }
        .day-title { font-weight: bold; font-size: 1.1rem; margin: 0; }
        .stButton button { width: 100%; border-radius: 8px; }
        div[data-testid="column"] button:contains("Sil") { background-color: #842029 !important; color: white !important; }
        @media print {
            header, footer, .stSidebar, [data-testid="stHeader"], [data-testid="stLayoutWrapper"], 
            .stButton, .nav-buttons, .day-header-wrapper, stElementContainer, .no-print { display: none !important; }
            .stApp { background-color: white !important; color: black !important; }
            .print-only-table { display: block !important; width: 100% !important; color: black !important; }
            table { width: 100% !important; border-collapse: collapse !important; border: 2px solid black !important; }
            th, td { border: 1px solid black !important; padding: 2px 6px !important; text-align: left !important; color: black !important; font-size: 10pt !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --- 5. ANA SEKMELER ---
tab_ajanda, tab_ogretmen, tab_ogrenci = st.tabs(["🗓️ Haftalık Ajanda", "👨‍🏫 Öğretmen Yönetimi", "🎓 Öğrenci Yönetimi"])

# --- TAB 1: ÖĞRENCİ YÖNETİMİ ---
with tab_ogrenci:
    st.header("🎓 Öğrenci Kayıt ve Detaylı Düzenleme")
    col_std_ekle, col_std_duzenle = st.columns([1, 1.5])

    with col_std_ekle:
        st.subheader("➕ Yeni Öğrenci Ekle")
        with st.form("yeni_ogrenci_form", clear_on_submit=True):
            std_as = st.text_input("Öğrenci Ad Soyad")
            std_sn = st.selectbox("Sınıfı", SINIF_LISTESI) # Otomatik sınıf listesi
            if st.form_submit_button("Öğrenciyi Kaydet"):
                if std_as:
                    conn.execute("INSERT INTO ogrenciler (ad_soyad, sinif) VALUES (?, ?)", (std_as, std_sn))
                    conn.commit(); st.success(f"{std_as} eklendi!"); st.rerun()
        
        st.divider()
        st.subheader("📂 Excel'den Toplu Yükle")
        yuklenen = st.file_uploader("Excel Dosyası Seç", type=["xlsx", "xls"], key="excel_up")
        if yuklenen and st.button("Veritabanına Aktar"):
            df_ex = pd.read_excel(yuklenen)
            for _, r in df_ex.iterrows():
                conn.execute("INSERT INTO ogrenciler (ad_soyad, sinif) VALUES (?, ?)", (str(r['ad_soyad']), str(r['sinif'])))
            conn.commit(); st.success("Toplu aktarım başarılı!"); st.rerun()


    with col_std_duzenle:
            st.subheader("📝 Öğrenci Bilgilerini Güncelle / Sil")
            ogrenciler_df = pd.read_sql_query("SELECT * FROM ogrenciler ORDER BY ad_soyad", conn)
            
            if not ogrenciler_df.empty:
                # 1. ÖĞRENCİ SEÇİMİ
                secilen_std_ad = st.selectbox("Düzenlenecek Öğrenciyi Seçin", ogrenciler_df['ad_soyad'].tolist(), key="std_edit_sb")
                s_data = ogrenciler_df[ogrenciler_df['ad_soyad'] == secilen_std_ad].iloc[0]
                
                # 2. GÜNCELLEME ALANI (Container kullanımı güncelleme sorununu çözer)
                with st.container(border=True):
                    g_std_as = st.text_input("Ad Soyad", value=s_data['ad_soyad'], key=f"std_name_inp_{s_data['id']}")
                    
                    idx_sinif = SINIF_LISTESI.index(s_data['sinif']) if s_data['sinif'] in SINIF_LISTESI else 0
                    g_std_sn = st.selectbox("Sınıf Güncelle", SINIF_LISTESI, index=idx_sinif, key=f"std_class_inp_{s_data['id']}")
                    
                    st.write("---")
                    c_std_btn1, c_std_btn2 = st.columns(2)
                    
                    # GÜNCELLEME BUTONU
                    if c_std_btn1.button("💾 Bilgileri Güncelle", use_container_width=True):
                        conn.execute("UPDATE ogrenciler SET ad_soyad=?, sinif=? WHERE id=?", (g_std_as, g_std_sn, int(s_data['id'])))
                        conn.commit()
                        st.success("Öğrenci bilgileri güncellendi!")
                        st.rerun()
                    
                    # SİLME BUTONU (Hata buradaydı, artık hizalı)
                    if c_std_btn2.button("🗑️ Öğrenciyi Sil", use_container_width=True):
                        conn.execute("DELETE FROM ogrenciler WHERE id=?", (int(s_data['id']),))
                        conn.commit()
                        st.warning("Öğrenci sistemden silindi.")
                        st.rerun()
            else:
                st.info("Kayıtlı öğrenci bulunamadı.")

     

                
                
                

# --- TAB 2: ÖĞRETMEN YÖNETİMİ ---
with tab_ogretmen:
    st.header("👨‍🏫 Öğretmen Kayıt ve Detaylı Düzenleme")
    col_o_ekle, col_o_duzenle = st.columns([1, 1.5])
    with col_o_ekle:
        st.subheader("➕ Yeni Öğretmen Ekle")
        with st.form("yeni_o_form", clear_on_submit=True):
            o_as = st.text_input("Ad Soyad")
            o_br = st.text_input("Branş / Sorumlu Sınıf")
            o_ka = st.text_input("Kullanıcı Adı")
            o_sf = st.text_input("Şifre", type="password")
            if st.form_submit_button("Kaydet"):
                if o_as and o_ka and o_sf:
                    conn.execute("INSERT INTO ogretmenler (ad_soyad, kullanici, sifre, brans_sinif) VALUES (?, ?, ?, ?)", 
                                 (o_as, o_ka, make_hashes(o_sf), o_br))
                    conn.commit(); st.success(f"{o_as} eklendi!"); st.rerun()

    with col_o_duzenle:
            st.subheader("📝 Bilgileri Güncelle / Sil")
            o_df = pd.read_sql_query("SELECT * FROM ogretmenler WHERE rol='ogretmen' ORDER BY ad_soyad", conn)
            
            if not o_df.empty:
                # Seçim kutusu
                s_o_ad = st.selectbox("Öğretmen Seçin", o_df['ad_soyad'].tolist(), key="o_sel_box")
                o_data = o_df[o_df['ad_soyad'] == s_o_ad].iloc[0]
                
                with st.container(border=True):
                    # Inputlarda 'key' kullanımı verilerin çakışmasını ve silme hatasını önler
                    go_as = st.text_input("Ad Soyad", value=o_data['ad_soyad'], key=f"edit_as_{o_data['id']}")
                    
                    # Sınıf indeksi kontrolü
                    try:
                        idx_sinif = SINIF_LISTESI.index(o_data['brans_sinif'])
                    except:
                        idx_sinif = 0
                        
                    go_br = st.selectbox("Sınıf / Branş", SINIF_LISTESI, index=idx_sinif, key=f"edit_br_{o_data['id']}")
                    go_ka = st.text_input("Kullanıcı Adı", value=o_data['kullanici'], key=f"edit_ka_{o_data['id']}")
                    go_sf = st.text_input("Yeni Şifre (Boşsa değişmez)", type="password", key=f"edit_sf_{o_data['id']}")
                    
                    st.write(" ") # Mesafe için
                    btn_col1, btn_col2 = st.columns(2)
                    
                    # 1. GÜNCELLEME BUTONU
                    if btn_col1.button("💾 Değişiklikleri Kaydet", use_container_width=True):
                        if go_sf:
                            conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici=?, sifre=?, brans_sinif=? WHERE id=?", 
                                         (go_as, go_ka, make_hashes(go_sf), go_br, int(o_data['id'])))
                        else:
                            conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici=?, brans_sinif=? WHERE id=?", 
                                         (go_as, go_ka, go_br, int(o_data['id'])))
                        conn.commit()
                        st.success("Bilgiler Güncellendi")
                        st.rerun()

                    # 2. SİLME BUTONU (Sorunu çözen kısım)
                    if btn_col2.button("🗑️ Öğretmeni Sil", use_container_width=True):
                        # Veritabanından silme işlemi
                        conn.execute("DELETE FROM ogretmenler WHERE id=?", (int(o_data['id']),))
                        conn.commit()
                        st.warning(f"{s_o_ad} başarıyla silindi.")
                        st.rerun()
            else:
                st.info("Kayıtlı öğretmen bulunmuyor.")

                

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
        
        if not slots:
            with st.expander(f"➕ {day} Program Kur"):
                c1, c2, c3 = st.columns(3)
                st_t = c1.time_input("Başlangıç", time(9, 0), key=f"s_{day}")
                en_t = c2.time_input("Bitiş", time(16, 0), key=f"e_{day}")
                gap = c3.number_input("Aralık", 10, 120, 45, key=f"g_{day}")
                if st.button("Kur", key=f"gen_{day}"):
                    curr = datetime.combine(datetime.today(), st_t)
                    while curr <= datetime.combine(datetime.today(), en_t):
                        conn.execute("INSERT INTO program (tarih, saat) VALUES (?, ?)", (day, curr.strftime("%H:%M")))
                        curr += timedelta(minutes=gap)
                    conn.commit(); st.rerun()
        else:
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
        if ca[1].button("🗑️ Günlük Programı Sil", key=f"clr_{day}"): conn.execute("DELETE FROM program WHERE tarih=?", (day,)); conn.commit(); st.rerun()

conn.close()