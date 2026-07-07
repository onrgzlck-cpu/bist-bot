import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import os
import requests

st.set_page_config(page_title="BIST Pro Terminali", layout="wide")

st.title("🦅 BIST Pro Algoritmik Radar & Matris Terminali")
st.write("Tüm indikatörleri canlı gösteren, seçmeli Telegram sinyal motorlu profesyonel sürüm.")

# 🔑 TELEGRAM BAĞLANTI BİLGİLERİ
TELEGRAM_TOKEN = "8861253852:AAHh_4raswH87kFEyVSib7EX5ssbLzF5ndA"
TELEGRAM_CHAT_ID = "8767394835"

# Önbellek Süresi (30 Dakika)
OTOMATIK_YENILEME_SURESI = 1800 

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

# 🧮 PROFESYONEL İNDİKATÖR MOTORU (TÜM LİSTEYİ HESAPLAR)
@st.cache_data(ttl=OTOMATIK_YENILEME_SURESI)
def komple_indikator_analizi(ticker):
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
        
        # 2. Ortalamalar (Hatanın düzeltildiği yer)
        ema5 = float(close.ewm(span=5, adjust=False).mean().iloc[-1])
        ema12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
        sma5 = float(close.rolling(window=5).mean().iloc[-1])
        sma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        # 3. ATR & Dinamik Fiyat Seviyeleri
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(window=14).mean().iloc[-1])
        
        al_giris = round(son_fiyat, 2)
        kar_tutari = round(son_fiyat + (2.2 * atr), 2)
        cikis_tutari = round(son_fiyat - (1.5 * atr), 2)
        
        # 4. OBV, Williams, CCI, MACD
        obv = np.where(close > close.shift(), volume, np.where(close < close.shift(), -volume, 0)).cumsum()
        williams_r = float(((high.rolling(window=14).max() - close) / (high.rolling(window=14).max() - low.rolling(window=14).min()) * -100).iloc[-1])
        
        tp = (high + low + close) / 3
        cci = float(((tp - tp.rolling(window=20).mean()) / (0.015 * tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean()))).iloc[-1])
        
        macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        # 5. Destek/Direnç & Kırılım
        pivot = (float(high.iloc[-2]) + float(low.iloc[-2]) + float(close.iloc[-2])) / 3
        destek = round(2 * pivot - float(high.iloc[-2]), 2)
        direnc = round(2 * pivot - float(low.iloc[-2]), 2)
        
        hacim_ort = volume.rolling(window=5).mean().iloc[-2]
        hacim_patlamasi = volume.iloc[-1] > (hacim_ort * 1.3)
        max_20 = high.rolling(window=20).max().iloc[-2]
        trend_kirildi = son_fiyat > max_20
        
        # 🎯 KESKİN SİNYAL KARARI
        if trend_kirildi and hacim_patlamasi and (macd_line.iloc[-1] > signal_line.iloc[-1]) and rsi < 62:
            sinyal_skoru = "KESKİN AL 🚀"
        elif rsi < 40 and (macd_line.iloc[-1] > signal_line.iloc[-1]):
            sinyal_skoru = "KADEMELİ AL"
        elif rsi > 75:
            sinyal_skoru = "SAT 🚨"
        else:
            sinyal_skoru = "TUT"

        return {
            "Hisse": ticker.replace(".IS", ""), "Son Fiyat": round(son_fiyat, 2), "Sinyal": sinyal_skoru,
            "Al Giriş Tutarı": al_giris, "Kâr Al Tutarı (TP)": kar_tutari, "Çıkış Tutarı (Stop)": cikis_tutari,
            "RSI (14)": round(rsi, 2), "EMA5": round(ema5, 2), "EMA12": round(ema12, 2), "EMA20": round(ema20, 2),
            "EMA26": round(ema26, 2), "SMA5": round(sma5, 2), "SMA20": round(sma20, 2), "ATR": round(atr, 2),
            "OBV": int(obv[-1]), "Williams %R": round(williams_r, 2), "CCI": round(cci, 2),
            "MACD": round(macd_line.iloc[-1], 2), "MACD Signal": round(signal_line.iloc[-1], 2),
            "Destek": destek, "Direnç": direnc, "Hacim Gücü": "Yüksek 🔥" if hacim_patlamasi else "Normal",
            "Kırılım": "Düşen Kırıldı" if trend_kirildi else "Yatay"
        }
    except:
        return None

# 🚀 SAYFA AÇILDIĞI AN OTOMATİK TARAMA BAŞLAR
if st.session_state.tarama_sonuclari is not None:
    all_data = st.session_state.tarama_sonuclari
else:
    ilk_veriler = []
    for h in TUM_HISSELER[:40]: # İlk açılışta ekran hızlı dolsun diye ilk 40 hisseyi çeker
        res = komple_indikator_analizi(h)
        if res: ilk_veriler.append(res)
    all_data = pd.DataFrame(ilk_veriler)
    st.session_state.tarama_sonuclari = all_data

# Yan Panel Butonları
st.sidebar.header("⚙️ Kontrol Paneli")
zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])
gosterim_tipi = st.sidebar.radio("Sinyal Filtresi", ["Tüm Liste", "Sadece KESKİN AL Olanlar"])

# 🔄 MANUEL TÜMÜNÜ YENİLE BUTONU
if st.sidebar.button("🔄 Tüm Listeyi Sıfırdan Tara"):
    yeniler = []
    pro_bar = st.progress(0)
    for idx, h in enumerate(TUM_HISSELER):
        res = komple_indikator_analizi(h)
        if res: yeniler.append(res)
        pro_bar.progress((idx + 1) / len(TUM_HISSELER))
    all_data = pd.DataFrame(yeniler)
    st.session_state.tarama_sonuclari = all_data
    st.rerun()

# 📡 TELEGRAMA SİNYAL GÖNDERME BUTONU
if st.button("📡 Keskin AL Verenleri İncele ve Telegram'a Gönder"):
    keskinler = all_data[all_data["Sinyal"] == "KESKİN AL 🚀"]
    if not keskinler.empty:
        st.success(f"🔥 {len(keskinler)} adet hisse Telegram'a gönderildi!")
        for _, row in keskinler.iterrows():
            mesaj = (
                f"🦅 *BIST PRO VIP AL SİNYALİ!*\n\n"
                f"📈 *Hisse:* #{row['Hisse']}\n"
                f"💰 *Giriş Fiyatı:* {row['Al Giriş Tutarı']} TL\n"
                f"🎯 *Kâr Al Hedefi:* {row['Kâr Al Tutarı (TP)']} TL\n"
                f"🚨 *Zarar Kes (Stop):* {row['Çıkış Tutarı (Stop)']} TL\n\n"
                f"📊 _RSI: {row['RSI (14)']} | Hacim: {row['Hacim Gücü']}_"
            )
            telegram_mesaj_gonder(mesaj)
    else:
        st.info("Şu an tam kırılım aşamasında KESKİN AL veren hisse yok. Tablodan diğer 'KADEMELİ AL'ları inceleyebilirsiniz.")

# 📊 EKRANA BASMA KATMANI
if all_data is not None and not all_data.empty:
    if gosterim_tipi == "Sadece KESKİN AL Olanlar":
        gosterilecek_df = all_data[all_data["Sinyal"] == "KESKİN AL 🚀"]
    else:
        gosterilecek_df = all_data
        
    st.subheader("📊 Canlı Pro Radar Matrisi")
    st.dataframe(gosterilecek_df.style.background_gradient(axis=0, cmap='RdYlGn', subset=["RSI (14)", "CCI"]))

    st.markdown("---")
    
    # Grafikler
    st.subheader("🔍 Tekil Hisse Grafik Odası")
    aktif_hisse = st.selectbox("Hisse Seçin:", gosterilecek_df["Hisse"].unique())
    if aktif_hisse:
        h_row = gosterilecek_df[gosterilecek_df["Hisse"] == aktif_hisse].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fiyat", f"{h_row['Son Fiyat']} TL")
        c2.metric("Sinyal", h_row['Sinyal'])
        c3.metric("Kâr Al (TP)", f"{h_row['Kâr Al Tutarı (TP)']} TL")
        c4.metric("Zarar Kes (Stop)", f"{h_row['Çıkış Tutarı (Stop)']} TL")
        
        g_df = yf.download(f"{aktif_hisse}.IS", period="3mo", interval=zaman_dilimi, progress=False)
        if isinstance(g_df.columns, pd.MultiIndex): g_df.columns = g_df.columns.droplevel(1)
        fig = go.Figure(data=[go.Candlestick(x=g_df.index, open=g_df['Open'], high=g_df['High'], low=g_df['Low'], close=g_df['Close'])])
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
