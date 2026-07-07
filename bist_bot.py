import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import requests

st.set_page_config(page_title="BIST Pro VIP Terminali", layout="wide")

st.title("🦅 BIST Pro VIP Algoritmik Terminal & Grafik Odası")
st.write("Gelişmiş indikatörlü grafikler, otomatik ayar yönetimi ve Sosyal Medya/Haber algı analizi.")

# 🔑 TELEGRAM AYARLARINI DOSYADAN OKUMA MOTORU
def telegram_bilgilerini_yukle():
    token, chat_id = None, None
    if os.path.exists("telegram_ayarlar.txt"):
        with open("telegram_ayarlar.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("TOKEN:"):
                    token = line.replace("TOKEN:", "").strip()
                elif line.startswith("CHAT_ID:"):
                    chat_id = line.replace("CHAT_ID:", "").strip()
    return token, chat_id

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = telegram_bilgilerini_yukle()
OTOMATIK_YENILEME_SURESI = 1800 

if "tarama_sonuclari" not in st.session_state:
    st.session_state.tarama_sonuclari = None

def telegram_mesaj_gonder(mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
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

# 🧮 PROFESYONEL İNDİKATÖR MOTORU
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
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = float(100 - (100 / (1 + (gain / (loss + 1e-9)))).iloc[-1])
        
        # Ortalamalar
        ema5 = float(close.ewm(span=5, adjust=False).mean().iloc[-1])
        ema12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
        sma5 = float(close.rolling(window=5).mean().iloc[-1])
        sma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        # ATR & Dinamik Seviyeler
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(window=14).mean().iloc[-1])
        
        al_giris = round(son_fiyat, 2)
        kar_tutari = round(son_fiyat + (2.2 * atr), 2)
        cikis_tutari = round(son_fiyat - (1.5 * atr), 2)
        
        # Diğer Göstergeler
        obv = np.where(close > close.shift(), volume, np.where(close < close.shift(), -volume, 0)).cumsum()
        williams_r = float(((high.rolling(window=14).max() - close) / (high.rolling(window=14).max() - low.rolling(window=14).min()) * -100).iloc[-1])
        
        tp = (high + low + close) / 3
        cci = float(((tp - tp.rolling(window=20).mean()) / (0.015 * tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean()))).iloc[-1])
        
        macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        # Destek/Direnç & Kırılım
        pivot = (float(high.iloc[-2]) + float(low.iloc[-2]) + float(close.iloc[-2])) / 3
        destek = round(2 * pivot - float(high.iloc[-2]), 2)
        direnc = round(2 * pivot - float(low.iloc[-2]), 2)
        
        hacim_ort = volume.rolling(window=5).mean().iloc[-2]
        hacim_patlamasi = volume.iloc[-1] > (hacim_ort * 1.3)
        max_20 = high.rolling(window=20).max().iloc[-2]
        trend_kirildi = son_fiyat > max_20
        
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
            "Kırılım": "Düşen Kırıldı" if trend_kirildi
