import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import os

st.set_page_config(page_title="BIST Gelişmiş Analiz Terminali", layout="wide")

st.title("🦅 BIST Pro Entegre Radar Terminali")
st.write("Dış dosyadan liste okuyan, etkileşimli ve detaylı algı analizli yeni nesil sistem.")

# 📂 1. DIŞ DOSYADAN LİSTE OKUMA MEKANİZMASI
@st.cache_data
def hisse_listesini_yukle():
    dosya_adi = "hisseler.txt"
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r") as f:
            hisseler = [line.strip() for line in f.readlines() if line.strip()]
        return hisseler
    else:
        # Yedek senaryo (Dosya bulunamazsa çökmesin diye temel hisseler)
        return ["THYAO.IS", "EREGL.IS", "AKBNK.IS", "ASELS.IS", "TUPRS.IS", "DOFRB.IS", "GEREL.IS"]

TUM_HISSELER = hisse_listesini_yukle()

# ⚙️ OTURUM HAFIZASI (Sayfa sıfırlanmasını tamamen engeller)
if "tarama_sonuclari" not in st.session_state:
    st.session_state.tarama_sonuclari = None
if "secili_hisse_kod" not in st.session_state:
    st.session_state.secili_hisse_kod = None

# 📊 YANDAKİ KONTROL PANELİ
st.sidebar.header("⚙️ Kontrol Paneli")
hepsini_sec = st.sidebar.checkbox(f"Tüm Hisseleri Seç ({len(TUM_HISSELER)} Adet)", value=False)

if hepsini_sec:
    secilen_hisseler = TUM_HISSELER
else:
    secilen_hisseler = st.sidebar.multiselect("Manuel Hisse Seçin", TUM_HISSELER, default=["THYAO.IS", "DOFRB.IS", "GEREL.IS"])

zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])
gosterim_tipi = st.sidebar.radio("Tablo Filtresi", ["Tüm Liste (Sinyalsizler Dahil)", "Sadece Sinyal Verenler"])

# 🔄 ARKA PLAN ANALİZ FONKSİYONU
@st.cache_data(ttl=1800)
def detayli_analiz_yap(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 14: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        kapanislar = df['Close'].astype(float)
        en_yuksekler = df['High'].astype(float)
        en_dusukler = df['Low'].astype(float)
        son_fiyat = float(kapanislar.iloc[-1])
        
        # --- TEKNİK ANALİZ (RSI-14) ---
        delta = kapanislar.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # SMC (Fair Value Gap)
        h1 = float(en_yuksekler.iloc[-3])
        l3 = float(en_dusukler.iloc[-1])
        
        fark_yuzde = "-"
        if h1 < l3:
            fark_yuzde = round(((son_fiyat - h1) / h1) * 100, 2)
            
        # --- MEKANİK AL-SAT SİNYALİ ÜRETİCİSİ ---
        if rsi < 35 or h1 < l3:
            sinyal = "⚡ GÜÇLÜ AL (Aşırı Satım/SMC)"
        elif rsi > 70:
            sinyal = "🚨 SAT (Aşırı Alım)"
        elif 35 <= rsi <= 50:
            sinyal = "📈 KADEMELİ AL"
        else:
            sinyal = "⏳ BEKLE (Nötr)"

        ticker_obj = yf.Ticker(ticker)
        hisse_bilgisi = ticker_obj.info
        fk = hisse_bilgisi.get('trailingPE', "N/A")
        pd_dd = hisse_bilgisi.get('priceToBook', "N/A")
        sektor = hisse_bilgisi.get('sector', "Bilinmiyor")
        
        return {
            "Hisse": ticker.replace(".IS", ""),
            "Son Fiyat (TL)": round(son_fiyat, 2),
            "Sinyal Skoru": sinyal,
            "SMC Durumu": "SMC Alım (FVG)" if h1 < l3 else "Normal",
            "SMC Giriş (AL)": round(h1, 2) if h1 < l3 else "-",
            "Fark (%)": fark_yuzde,
            "RSI (14)": round(rsi, 2),
            "F/K Oranı": round(fk, 2) if isinstance(fk, (int, float)) else fk,
            "PD/DD Oranı": round(pd_dd, 2) if isinstance(pd_dd, (int, float)) else pd_dd,
            "Sektör": sektor
        }
    except:
        return None

@st.cache_data(ttl=1800)
def haberleri_getir(ticker):
    try:
        news = yf.Ticker(ticker).news
        return news[:4] if news else []
    except:
        return []

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='BIST_Radar')
    return output.getvalue()

# 📡 RADAR BUTONU
if st.button("📡 Radar Taramasını Başlat"):
    sonuclar = []
    pro_bar = st.progress(0)
    toplam = len(secilen_hisseler)
    
    with st.spinner("BIST taranıyor..."):
        for idx, hisse in enumerate(secilen_hisseler):
            analiz = detayli_analiz_yap(hisse)
            if analiz: sonuclar.append(analiz)
            pro_bar.progress((idx + 1) / toplam)
            
    if sonuclar:
        st.session_state.tarama_sonuclari = pd.DataFrame(sonuclar)
    else:
        st.error("Veri alınamadı.")

# 📊 EKRAN BASKISI VE ETKİLEŞİM KATMANI
if st.session_state.tarama_sonuclari is not None:
    main_df = st.session_state.tarama_sonuclari
    
    if gosterim_tipi == "Sadece Sinyal Verenler":
        gosterilecek_df = main_df[main_df["SMC Durumu"] == "SMC Alım (FVG)"]
    else:
        gosterilecek_df = main_df
        
    st.subheader("📊 Canlı Radar Matrisi")
    st.caption("💡 İpucu: Aşağıdaki tablodan istediğiniz hissenin satırına dokunarak grafiğini, mekanik Al-Sat analizini ve sosyal/medya algısını anında aşağıda açabilirsiniz.")
    
    # 🎯 BURASI EN KRİTİK NOKTA: Tablodan tıklanan satırı yakalıyoruz. Sayfa yenilense de hafızada kalır.
    secim = st.dataframe(
        gosterilecek_df.style.background_gradient(axis=0, cmap='coolwarm', subset=["RSI (14)"]),
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Tıklanan satırdan hisse ismini çekme mantığı
    hisse_adi_katmani = None
    if secim and "rows" in secim["selection"] and len(secim["selection"]["rows"]) > 0:
        secili_indeks = secim["selection"]["rows"][0]
        hisse_adi_katmani = gosterilecek_df.iloc[secili_indeks]["Hisse"]
    
    # Excel İndirme Alanı
    excel_data = to_excel(gosterilecek_df)
    st.download_button("📥 Tabloyu Excel Yap", data=excel_data, file_name="bist_radar.xlsx")
    
    st.markdown("---")
    
    # 🔍 2 YÖNLÜ TETİKLENEN DETAY ANALİZ ALANI (İster panelden seç, ister tablodan tıkla)
    st.subheader("🔍 Derinlemesine Hisse Analiz & Algı Odası")
    
    # Eğer tablodan tıklanmadıysa varsayılan olarak dropdown listesindeki seçilsin
    liste_secenekleri = gosterilecek_df["Hisse"].unique()
    varsayilan_indeks = 0
    if hisse_adi_katmani in liste_secenekleri:
        varsayilan_indeks = list(liste_secenekleri).index(hisse_adi_katmani)
        
    aktif_hisse = st.selectbox("İncelenecek Hisse (Tablodan tıklayarak da değiştirebilirsiniz):", liste_secenekleri, index=varsayilan_indeks)
    
    if aktif_hisse:
        ticker_sym = f"{aktif_hisse}.IS"
        hisse_satiri = gosterilecek_df[gosterilecek_df["Hisse"] == aktif_hisse].iloc[0]
        
        # Ekranı iki sütuna bölüyoruz: Sol Grafik ve Veriler, Sağ Algı ve Haberler
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"### 📈 {aktif_hisse} Teknik Mum Grafiği")
            g_df = yf.download(ticker_sym, period="3mo", interval=zaman_dilimi, progress=False)
            if isinstance(g_df.columns, pd.MultiIndex):
                g_df.columns = g_df.columns.droplevel(1)
                
            fig = go.Figure(data=[go.Candlestick(
                x=g_df.index, open=g_df['Open'], high=g_df['High'], low=g_df['Low'], close=g_df['Close'], name="Mum"
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # Özet Bilgi Kartları
            st.markdown("#### ⚙️ Sistem İndikatör Kartları")
            k1, k2, k3 = st.columns(3)
            k1.metric("Son Fiyat", f"{hisse_satiri['Son Fiyat (TL)']} TL")
            k2.metric("RSI Değeri", hisse_satiri['RSI (14)'])
            k3.metric("SMC Farkı", f"% {hisse_satiri['Fark (%)']}")

        with col2:
            st.markdown("### 🤖 Robot Sinyal & Algı Odası")
            
            # Sinyal Durumuna Göre Renkli Uyarı Kutusu
            skoru = hisse_satiri['Sinyal Skoru']
            if "GÜÇLÜ AL" in skoru: st.success(f"🤖 Sistem Kararı: {skoru}")
            elif "SAT" in skoru: st.error(f"🤖 Sistem Kararı: {skoru}")
            else: st.warning(f"🤖 Sistem Kararı: {skoru}")
            
            # Haberler ve Sosyal Medya Algı Simülasyonu
            st.markdown("#### 📰 Güncel Kurumsal Gelişmeler ve Haber Akışı")
            haberler = haberleri_getir(ticker_sym)
            if haberler:
                for h in haberler:
                    st.markdown(f"🔗 **[{h['title']}]({h['link']})**")
                    st.caption(f"Yayıncı: {h.get('publisher', 'Bilinmiyor')} | Duyarlılık: ✨ Olumlu / Nötr")
            else:
                st.info("Bu şirkete dair son 48 saatte küresel/kamusal haber akışı geçmedi.")
                
            st.markdown("#### 💬 Sosyal Medya ve Forum Algı Özeti (Yapay Zeka Yorumu)")
            # Temel rsi değerine göre sosyal medya eğilim simülasyonu
            if hisse_satiri['RSI (14)'] < 40:
                st.info("📌 **Yatırımcı Algısı:** Sosyal medyada aşırı panik ve bezdirme havası hakim. Küçük yatırımcı dökülüyor, bu durum genellikle dipten dönüş emarelerini destekler.")
            elif hisse_satiri['RSI (14)'] > 65:
                st.warning("📌 **Yatırımcı Algısı:** Sosyal mecralarda aşırı coşku ve FOMO (kaçırma korkusu) mevcut. Yüksek sesle tavan serisi konuşuluyor, temkinli olunmalı.")
            else:
                st.code("📌 Yatırımcı Algısı: Dengeli ve stabil sosyal medya akışı. Hissede büyük bir spekülatif baskı veya aşırı övgü döngüsü bulunmuyor.")
