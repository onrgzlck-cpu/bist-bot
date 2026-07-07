import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import os
import requests
from datetime import datetime
import time

st.set_page_config(page_title="BIST OtonomTrading Terminali", layout="wide")

st.title("🦅 BIST Pro Ultra-Keskin Otonom Sinyal Fabrikası")
st.write("Sadece kurumsal hacimli kırılımları seçen, borsa saatlerinde saatte 1 çalışan akıllı robot.")

# 🔑 TELEGRAM BAĞLANTI BİLGİLERİ
TELEGRAM_TOKEN = "8861253852:AAHh_4raswH87kFEyVSib7EX5ssbLzF5ndA"
TELEGRAM_CHAT_ID = "8767394835"

# Otomatik Önbellek ve Yenileme Süresi (1 Saat = 3600 Saniye)
OTOMATIK_YENILEME_SURESI = 3600 

def telegram_mesaj_gonder(mesaj):
    if TELEGRAM_TOKEN == "BURAYA_TOKENI_YAZIN" or TELEGRAM_CHAT_ID == "BURAYA_CHAT_ID_YAZIN":
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except:
        return False

@st.cache_data
def hisse_listesini_yukle():
    dosya_adi = "hisseler.txt"
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["THYAO.IS", "DOFRB.IS", "GEREL.IS", "EREGL.IS", "TUPRS.IS"]

TUM_HISSELER = hisse_listesini_yukle()

if "tarama_sonuclari" not in st.session_state:
    st.session_state.tarama_sonuclari = None
if "son_otonom_tarama_saati" not in st.session_state:
    st.session_state.son_otonom_tarama_saati = 0

# Yan Panel
st.sidebar.header("⚙️ Kontrol Merkezi")
hepsini_sec = st.sidebar.checkbox(f"Tüm Hisseleri Seç ({len(TUM_HISSELER)} Adet)", value=True)
secilen_hisseler = TUM_HISSELER if hepsini_sec else st.sidebar.multiselect("Hisseleri Seçin", TUM_HISSELER, default=["THYAO.IS", "DOFRB.IS", "GEREL.IS"])
zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])

# 🧮 ULTRA KESKİN MATEMATİKSEL FİLTRE MOTORU
@st.cache_data(ttl=OTOMATIK_YENILEME_SURESI)
def ultra_keskin_analiz(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 30: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
        close = df['Close'].astype(float)
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        volume = df['Volume'].astype(float)
        son_fiyat = float(close.iloc[-1])
        
        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = float(100 - (100 / (1 + (gain / (loss + 1e-9)))).iloc[-1])
        
        # 2. MACD
        macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        # 3. Hacim Gücü Kontrolü (Son 5 günün ortalamasının 1.5 katı mı?)
        hacim_ort = volume.rolling(window=5).mean().iloc[-2]
        hacim_patlamasi = volume.iloc[-1] > (hacim_ort * 1.5)
        
        # 4. Düşen Trend Kırılımı (Son 20 günün en yüksek tepesi aşıldı mı?)
        max_20 = high.rolling(window=20).max().iloc[-2]
        trend_kirildi = son_fiyat > max_20
        
        # 5. Dinamik ATR Seviyeleri
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(window=14).mean().iloc[-1])
        
        al_giris = round(son_fiyat, 2)
        kar_tutari = round(son_fiyat + (2.5 * atr), 2) # Hedefi 2.5 ATR'ye çıkartarak kârlılığı artırdık
        cikis_tutari = round(son_fiyat - (1.5 * atr), 2)
        
        # 🔥 ULTRA KESKİN SİNYAL ŞARTI: Kırılım olacak + Hacimli olacak + MACD Al verecek + RSI şişmemiş olacak
        if trend_kirildi and hacim_patlamasi and (macd_line.iloc[-1] > signal_line.iloc[-1]) and rsi < 65:
            sinyal_skoru = "KESKİN AL 🚀"
        elif rsi > 75:
            sinyal_skoru = "SAT"
        else:
            sinyal_skoru = "NÖTR"

        return {
            "Hisse": ticker.replace(".IS", ""), "Son Fiyat": round(son_fiyat, 2), "Sinyal": sinyal_skoru,
            "Al Giriş Tutarı": al_giris, "Kâr Al Tutarı (TP)": kar_tutari, "Çıkış Tutarı (Stop)": cikis_tutari,
            "RSI (14)": round(rsi, 2), "Hacim": "Yüksek Patlama 🔥" if hacim_patlamasi else "Normal",
            "Kırılım": "Düşen Kırıldı" if trend_kirildi else "Sıkışma", "MACD": round(macd_line.iloc[-1], 2)
        }
    except:
        return None

# 📡 MANUEL TARAMA BUTONU (Yalnızca ekrandaki tabloyu günceller, Telegram'ı yormaz)
if st.button("📡 Ekran Matrisini Güncelle"):
    sonuclar = []
    for hisse in secilen_hisseler:
        analiz = ultra_keskin_analiz(hisse)
        if analiz: sonuclar.append(analiz)
    if sonuclar: st.session_state.tarama_sonuclari = pd.DataFrame(sonuclar)

# Tabloyu ekrana basma
if st.session_state.tarama_sonuclari is not None:
    st.subheader("📊 Filtrelenmiş Canlı Takip Listesi")
    st.dataframe(st.session_state.tarama_sonuclari)

# 🕒 ----------------- OTONOM SAATLİK ARKA PLAN MOTORU ----------------- 
su_an = time.time()
simdiki_zaman = datetime.now()
saat = simdiki_zaman.hour

# Şart 1: Sabah 10:00 ile Akşam 18:00 arasında mı?
# Şart 2: Son taramanın üzerinden 1 saat (3600 saniye) geçti mi? (Veya ilk kez mi çalışıyor?)
if (10 <= saat <= 18) and (su_an - st.session_state.son_otonom_tarama_saati > OTOMATIK_YENILEME_SURESI):
    st.session_state.son_otonom_tarama_saati = su_an
    
    otonom_al_listesi = []
    for hisse in TUM_HISSELER:
        res = ultra_keskin_analiz(hisse)
        if res and res["Sinyal"] == "KESKİN AL 🚀":
            otonom_al_listesi.append(res)
            
    if otonom_al_listesi:
        for h in otonom_al_listesi:
            mesaj = (
                f"🦅 *BIST OTONOM VIP AL SİNYALİ!*\n\n"
                f"📈 *Hisse:* #{h['Hisse']}\n"
                f"🔥 *Kriter:* Hacimli Düşen Trend Kırılımı!\n\n"
                f"💰 *Giriş Fiyatı:* {h['Al Giriş Tutarı']} TL\n"
                f"🎯 *Hedef (Kâr Al):* {h['Kâr Al Tutarı (TP)']} TL\n"
                f"🚨 *Zarar Kes (Stop):* {h['Çıkış Tutarı (Stop)']} TL\n\n"
                f"📊 _RSI: {h['RSI (14)']} | Zaman: {simdiki_zaman.strftime('%H:%M')}_"
            )
            telegram_mesaj_gonder(mesaj)

# Sayfayı canlı tutmak için küçük bir otomatik yenileme tetikleyicisi (Streamlit için görünmez yenileme)
st.sidebar.markdown(f"⏱️ Son Otonom Kontrol: {simdiki_zaman.strftime('%H:%M:%S')}")
