import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Sistem Yönetimi", layout="wide", initial_sidebar_state="collapsed")

# --- SINIF LİSTESİ (1-A'dan 4-D'ye) ---
SINIFLAR = []
for i in range(1, 5):
    for sube in ['A', 'B', 'C', 'D']:
        SINIFLAR.append(f"{i}-{sube}")

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
if 'admin_giris_yapildi' not in st.session_state:
    st.session_state.admin_giris_yapildi = False

if not st.session_state.admin_giris_yapildi:
    with st.container(border=True):
        st.subheader("🔑 Admin Girişi")
        a_u = st.text_input("Kullanıcı Adı")
        a_p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            conn = sqlite3.connect('okul_sistemi_final.db')
            res = conn.execute("SELECT * FROM sistem_adminleri WHERE k_adi=? AND sifre=?", (a_u, a_p)).fetchone()
            conn.close()
            if res:
                st.session_state.admin_giris_yapildi = True
                st.rerun()
            else: st.error("Hatalı admin bilgileri!")

else:
    col_h, col_c = st.columns([5,1])
    col_h.success("🔓 Yönetim Yetkisi Aktif")
    if col_c.button("🚪 Çıkış"):
        st.session_state.admin_giris_yapildi = False
        st.rerun()

    t1, t2, t3 = st.tabs(["👨‍🏫 Öğretmen Yönetimi", "👶 Öğrenci Yönetimi", "🛡️ Admin Ayarları"])
    conn = sqlite3.connect('okul_sistemi_final.db')

    # --- 1. ÖĞRETMEN YÖNETİMİ ---
    with t1:
        st.subheader("👨‍🏫 Yeni Öğretmen Kaydı")
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            h_ad_in = c1.text_input("Ad Soyad", key="h_ad_n")
            h_u_in = c2.text_input("Kullanıcı Adı", key="h_u_n")
            h_s_in = c3.text_input("Şifre", key="h_s_n")
            h_snf_in = c4.selectbox("Sorumlu Sınıf", SINIFLAR, key="h_snf_n")
            if st.button("Öğretmeni Ekle", use_container_width=True):
                conn.execute("INSERT INTO ogretmenler (ad_soyad, kullanici_adi, sifre, sinif) VALUES (?,?,?,?)", (h_ad_in, h_u_in, h_s_in, h_snf_in))
                conn.commit(); st.rerun()
        
        st.divider()
        st.subheader("✏️ Öğretmen Düzenle / Sil")
        df_h = pd.read_sql_query("SELECT * FROM ogretmenler", conn)
        
        if not df_h.empty:
            h_list = df_h.apply(lambda x: f"{x['id']} - {x['ad_soyad']}", axis=1).tolist()
            selected_h_str = st.selectbox("Düzenlenecek Öğretmeni Seçin", h_list, key="h_select_box")
            selected_h_id = int(selected_h_str.split(" - ")[0])
            h_data = df_h[df_h['id'] == selected_h_id].iloc[0]

            with st.container(border=True):
                ec1, ec2, ec3, ec4 = st.columns(4)
                up_ad = ec1.text_input("Ad Soyad", value=str(h_data['ad_soyad']), key=f"uh_ad_{selected_h_id}")
                up_u = ec2.text_input("Kullanıcı Adı", value=str(h_data['kullanici_adi']), key=f"uh_u_{selected_h_id}")
                up_s = ec3.text_input("Şifre", value=str(h_data['sifre']), key=f"uh_s_{selected_h_id}")
                try: c_idx = SINIFLAR.index(h_data['sinif'])
                except: c_idx = 0
                up_snf = ec4.selectbox("Sınıf", SINIFLAR, index=c_idx, key=f"uh_snf_{selected_h_id}")
                
                b1, b2 = st.columns(2)
                if b1.button("💾 GÜNCELLE", use_container_width=True, key=f"btn_uh_{selected_h_id}"):
                    conn.execute("UPDATE ogretmenler SET ad_soyad=?, kullanici_adi=?, sifre=?, sinif=? WHERE id=?", (up_ad, up_u, up_s, up_snf, selected_h_id))
                    conn.commit(); st.success("Güncellendi!"); st.rerun()
                if b2.button("🗑️ ÖĞRETMENİ SİL", use_container_width=True, key=f"btn_dh_{selected_h_id}"):
                    conn.execute("DELETE FROM ogretmenler WHERE id=?", (selected_h_id,))
                    conn.commit(); st.warning("Öğretmen Silindi!"); st.rerun()
        
        st.write("📋 **Kayıtlı Öğretmen Listesi**")
        st.dataframe(df_h, use_container_width=True)

    # --- 2. ÖĞRENCİ YÖNETİMİ ---
    with t2:
        st.subheader("👶 Yeni Öğrenci/Veli Kaydı")
        with st.container(border=True):
            o1, o2, o3, o4 = st.columns(4)
            o_tc = o1.text_input("Veli T.C.", key="o_tc_n")
            o_no = o2.text_input("Okul No", key="o_no_n")
            o_ad = o3.text_input("Öğrenci Ad", key="o_ad_n")
            o_snf = o4.selectbox("Sınıfı", SINIFLAR, key="o_snf_n")
            if st.button("Öğrenciyi Ekle", use_container_width=True):
                conn.execute("INSERT INTO ogrenciler (tc_no, okul_no, ad_soyad, sinif) VALUES (?,?,?,?)", (o_tc, o_no, o_ad, o_snf))
                conn.commit(); st.rerun()

        st.divider()
        st.subheader("✏️ Öğrenci Düzenle / Sil")
        df_o = pd.read_sql_query("SELECT * FROM ogrenciler", conn)
        
        if not df_o.empty:
            o_list = df_o.apply(lambda x: f"{x['tc_no']} - {x['ad_soyad']}", axis=1).tolist()
            selected_o_str = st.selectbox("Düzenlenecek Öğrenciyi Seçin", o_list, key="o_select_box")
            selected_o_tc = selected_o_str.split(" - ")[0]
            o_data = df_o[df_o['tc_no'] == selected_o_tc].iloc[0]

            with st.container(border=True):
                oc1, oc2, oc3, oc4 = st.columns(4)
                uo_tc = oc1.text_input("Veli T.C.", value=str(o_data['tc_no']), key=f"uo_tc_{selected_o_tc}")
                uo_no = oc2.text_input("Okul No", value=str(o_data['okul_no']), key=f"uo_no_{selected_o_tc}")
                uo_ad = oc3.text_input("Ad Soyad", value=str(o_data['ad_soyad']), key=f"uo_ad_{selected_o_tc}")
                try: o_idx = SINIFLAR.index(o_data['sinif'])
                except: o_idx = 0
                uo_snf = oc4.selectbox("Sınıf ", SINIFLAR, index=o_idx, key=f"uo_snf_{selected_o_tc}")

                ob1, ob2 = st.columns(2)
                if ob1.button("💾 GÜNCELLE ", use_container_width=True, key=f"btn_uo_{selected_o_tc}"):
                    conn.execute("UPDATE ogrenciler SET tc_no=?, okul_no=?, ad_soyad=?, sinif=? WHERE tc_no=?", (uo_tc, uo_no, uo_ad, uo_snf, selected_o_tc))
                    conn.commit(); st.success("Güncellendi!"); st.rerun()
                if ob2.button("🗑️ ÖĞRENCİYİ SİL", use_container_width=True, key=f"btn_do_{selected_o_tc}"):
                    conn.execute("DELETE FROM ogrenciler WHERE tc_no=?", (selected_o_tc,))
                    conn.commit(); st.warning("Öğrenci Silindi!"); st.rerun()
        
        st.write("📋 **Kayıtlı Öğrenci Listesi**")
        st.dataframe(df_o, use_container_width=True)

    # --- 3. ADMIN AYARLARI ---
    with t3:
        st.subheader("🛡️ Admin Yönetimi")
        with st.container(border=True):
            nu = st.text_input("Kullanıcı Adı", key="adm_u")
            np = st.text_input("Şifre", type="password", key="adm_p")
            if st.button("Admin Ekle"):
                conn.execute("INSERT INTO sistem_adminleri (k_adi, sifre) VALUES (?,?)", (nu, np))
                conn.commit(); st.success("Yeni admin eklendi!"); st.rerun()
        df_a = pd.read_sql_query("SELECT id, k_adi FROM sistem_adminleri", conn)
        st.table(df_a)

    conn.close()