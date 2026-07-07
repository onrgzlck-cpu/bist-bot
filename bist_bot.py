import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import os
import requests

st.set_page_config(page_title="BIST Algoritmik Radar & Telegram", layout="wide")

st.title("🦅 BIST Pro Algoritmik Sinyal & Telegram Terminali")
st.write("Bulduğu AL sinyallerini anında Telegram üzerinden cebinize gönderen akıllı haberci sistemi.")

# 🔑 1. TELEGRAM BAĞLANTI BİLGİLERİ (Aldığınız bilgileri buraya yazın)
TELEGRAM_TOKEN = "8861253852:AAHh_4raswH87kFEyVSib7EX5ssbLzF5ndA"
TELEGRAM_CHAT_ID = "8767394835"

# Otomatik Önbellek Süresi (1 Saat)
OTOMATIK_YENILEME_SURESI = 3600 

# Telegram Mesaj Gönderme Fonksiyonu
def telegram_mesaj_gonder(mesaj):
    if TELEGRAM_TOKEN == "BURAYA_TOKENI_YAZIN" or TELEGRAM_CHAT_ID == "BURAYA_CHAT_ID_YAZIN":
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown"
    }
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

# Sol Panel
st.sidebar.header("⚙️ Kontrol Paneli")
hepsini_sec = st.sidebar.checkbox(f"Tüm Hisseleri Seç ({len(TUM_HISSELER)} Adet)", value=False)

if hepsini_sec:
    secilen_hisseler = TUM_HISSELER
else:
    secilen_hisseler = st.sidebar.multiselect("Hisseleri Seçin", TUM_HISSELER, default=["THYAO.IS", "DOFRB.IS", "GEREL.IS"])

zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])
gosterim_tipi = st.sidebar.radio("Sinyal Filtresi", ["Tüm Liste", "Sadece AL Verenler", "Sadece SAT Verenler"])

# 🧮 Gelişmiş Matematiksel Motor
@st.cache_data(ttl=OTOMATIK_YENILEME_SURESI)
def gelismis_algoritmik_analiz(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 30: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        close = df['Close'].astype(float)
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        volume = df['Volume'].astype(float)
        son_fiyat = float(close.iloc[-1])
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # Ortalamalar
        ema5 = float(close.ewm(span=5, adjust=False).mean().iloc[-1])
        ema12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
        sma5 = float(close.rolling(window=5).mean().iloc[-1])
        sma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        # ATR & Hedefler
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = float(tr.rolling(window=14).mean().iloc[-1])
        
        al_giris = round(son_fiyat, 2)
        kar_tutari = round(son_fiyat + (2 * atr), 2)
        cikis_tutari = round(son_fiyat - (1.5 * atr), 2)
        
        # OBV, Williams, CCI, MACD
        obv = np.where(close > close.shift(), volume, np.where(close < close.shift(), -volume, 0)).cumsum()
        son_obv = float(obv[-1])
        williams_r = float(((high.rolling(window=14).max() - close) / (high.rolling(window=14).max() - low.rolling(window=14).min()) * -100).iloc[-1])
        
        tp = (high + low + close) / 3
        cci = float(((tp - tp.rolling(window=20).mean()) / (0.015 * tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean()))).iloc[-1])
        
        macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        son_macd = float(macd_line.iloc[-1])
        son_signal = float(signal_line.iloc[-1])
        
        # Destek/Direnç & Kırılım
        pivot = (float(high.iloc[-2]) + float(low.iloc[-2]) + float(close.iloc[-2])) / 3
        destek = round(2 * pivot - float(high.iloc[-2]), 2)
        direnc = round(2 * pivot - float(low.iloc[-2]), 2)
        
        hacim_ort = volume.rolling(window=5).mean().iloc[-2]
        hacim_gucu = "Yüksek" if volume.iloc[-1] > hacim_ort * 1.5 else ("Düşük" if volume.iloc[-1] < hacim_ort * 0.7 else "Normal")
        
        max_20 = high.rolling(window=20).max().iloc[-2]
        kirilim = "Düşen Kırıldı 🚀" if son_fiyat > max_20 else "Yatay/Sıkışma"
        
        # Sinyal Kararı
        if (rsi < 42 and son_macd > son_signal) or kirilim == "Düşen Kırıldı 🚀":
            sinyal_skoru = "AL"
        elif rsi > 70 or son_macd < son_signal:
            sinyal_skoru = "SAT"
        else:
            sinyal_skoru = "TUT"

        return {
            "Hisse": ticker.replace(".IS", ""),
            "Son Fiyat": round(son_fiyat, 2),
            "Sinyal": sinyal_skoru,
            "Al Giriş Tutarı": al_giris,
            "Kâr Al Tutarı (TP)": kar_tutari,
            "Çıkış Tutarı (Stop)": cikis_tutari,
            "RSI (14)": round(rsi, 2),
            "EMA5": round(ema5, 2),
            "EMA12": round(ema12, 2),
            "EMA20": round(ema20, 2),
            "EMA26": round(ema26, 2),
            "SMA5": round(sma5, 2),
            "SMA20": round(sma20, 2),
            "ATR": round(atr, 2),
            "OBV": int(son_obv),
            "Williams %R": round(williams_r, 2),
            "CCI": round(cci, 2),
            "MACD": round(son_macd, 2),
            "MACD Signal": round(son_signal, 2),
            "Destek": destek,
            "Direnç": direnc,
            "Hacim Gücü": hacim_gucu,
            "Kırılım": kirilim
        }
    except:
        return None

# 📡 RADAR BUTONU
if st.button("📡 Algoritmayı Başlat ve Sinyalleri Telegrame Gönder"):
    sonuclar = []
    al_verenler = []
    pro_bar = st.progress(0)
    toplam = len(secilen_hisseler)
    
    with st.spinner("Piyasa taranıyor ve sinyaller hazırlanıyor..."):
        for idx, hisse in enumerate(secilen_hisseler):
            analiz = gelismis_algoritmik_analiz(hisse)
            if analiz: 
                sonuclar.append(analiz)
                # Eğer hisse AL sinyali ürettiyse listeye ekle
                if analiz["Sinyal"] == "AL":
                    al_verenler.append(analiz)
            pro_bar.progress((idx + 1) / toplam)
            
    if sonuclar:
        st.session_state.tarama_sonuclari = pd.DataFrame(sonuclar)
        
        # 🔔 TELEGRAMA BİLDİRİM GÖNDERME KATMANI
        if al_verenler:
            st.success(f"🔥 Toplam {len(al_verenler)} adet hissede AL sinyali tespit edildi! Telegram'a gönderiliyor...")
            for h in al_verenler:
                mesaj_metni = (
                    f"🦅 *BIST RADAR AL SİNYALİ!*\n\n"
                    f"📈 *Hisse:* #{h['Hisse']}\n"
                    f"💰 *Al Giriş Tutarı:* {h['Al Giriş Tutarı']} TL\n"
                    f"🎯 *Kâr Al Hedefi (TP):* {h['Kâr Al Tutarı (TP)']} TL\n"
                    f"🚨 *Zarar Kes (Stop):* {h['Çıkış Tutarı (Stop)']} TL\n\n"
                    f"📊 *RSI (14):* {h['RSI (14)']} | *Kırılım:* {h['Kırılım']}\n"
                    f"⏱️ _Sinyal Zamanı: Canlı Veri_"
                )
                telegram_mesaj_gonder(mesaj_metni)
        else:
            st.info("Tarama bitti, ancak şu an kriterlere uyan aktif bir 'AL' sinyali bulunamadı.")
    else:
        st.error("Veri alınamadı.")

# Tablo Görünümü (Eski sistemimiz aynen korunuyor)
if st.session_state.tarama_sonuclari is not None:
    main_df = st.session_state.tarama_
