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
        
        # 2. Ortalamalar
        ema5 = float(close.ewm(span=5, adjust=False).mean().iloc[-1])
        ema12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
        sma5 = float(close.rolling(
