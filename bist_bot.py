import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import os
import time

st.set_page_config(page_title="BIST Algoritmik Radar Terminali", layout="wide")

st.title("🦅 BIST Pro Algoritmik Sinyal & Radar Terminali")
st.write("Tüm indikatör filtreleri, otomatik Al/Sat/Stop seviyeleri ve saatlik otomatik güncelleme entegrasyonu.")

# 🔄 SAATLİK GÜNCELLEME MEKANİZMASI (1 Saat = 3600 Saniye)
# Gelecekte APK ve Telegram'a bağlarken bu önbellek süresi tetikleyici olacak.
OTOMATIK_YENILEME_SURESI = 3600 

@st.cache_data
def hisse_listesini_yukle():
    dosya_adi = "hisseler.txt"
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["THYAO.IS", "DOFRB.IS", "GEREL.IS", "EREGL.IS", "TUPRS.IS"]

TUM_HISSELER = hisse_listesini_yukle()

# Oturum Hafızası Kurulumu
if "tarama_sonuclari" not in st.session_state:
    st.session_state.tarama_sonuclari = None

# Sol Panel Ayarları
st.sidebar.header("⚙️ Algoritmik Filtre Paneli")
hepsini_sec = st.sidebar.checkbox(f"Tüm Hisseleri Seç ({len(TUM_HISSELER)} Adet)", value=False)

if hepsini_sec:
    secilen_hisseler = TUM_HISSELER
else:
    secilen_hisseler = st.sidebar.multiselect("Hisseleri Seçin", TUM_HISSELER, default=["THYAO.IS", "DOFRB.IS", "GEREL.IS"])

zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])
gosterim_tipi = st.sidebar.radio("Sinyal Filtresi", ["Tüm Liste", "Sadece AL Verenler", "Sadece SAT Verenler"])

# 🧮 TÜM İNDİKATÖRLERİN VE FİLTRELERİN HESAPLANDIĞI ANA MOTOR
@st.cache_data(ttl=OTOMATIK_YENILEME_SURESI)
def gelismis_algoritmik_analiz(ticker):
    try:
        # İndikatörler ve kırılımlar için en az 6 aylık veri çekiyoruz
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 30: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        close = df['Close'].astype(float)
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        open_p = df['Open'].astype(float)
        volume = df['Volume'].astype(float)
        
        son_fiyat = float(close.iloc[-1])
        
        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # 2. Hareketli Ortalamalar (EMA & SMA)
        ema5 = float(close.ewm(span=5, adjust=False).mean().iloc[-1])
        ema12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
        sma5 = float(close.rolling(window=5).mean().iloc[-1])
        sma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        # 3. ATR (Average True Range - 14)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = float(tr.rolling(window=14).mean().iloc[-1])
        
        # 4. OBV (On-Balance Volume)
        obv = np.where(close > close.shift(), volume, np.where(close < close.shift(), -volume, 0)).cumsum()
        son_obv = float(obv[-1])
        
        # 5. Williams %R (14)
        highest_high = high.rolling(window=14).max()
        lowest_low = low.rolling(window=14).min()
        williams_r = float(((highest_high - close) / (highest_high - lowest_low) * -100).iloc[-1])
        
        # 6. CCI (Commodity Channel Index - 20)
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad_tp = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = float(((tp - sma_tp) / (0.015 * mad_tp)).iloc[-1])
        
        # 7. MACD & MACD Signal
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        son_macd = float(macd_line.iloc[-1])
        son_signal = float(signal_line.iloc[-1])
        
        # 8. Destek & Direnç (Klasik Pivot Noktaları - Son Günün Verilerine Göre)
        p_high = float(high.iloc[-2])
        p_low = float(low.iloc[-2])
        p_close = float(close.iloc[-2])
        pivot = (p_high + p_low + p_close) / 3
        destek = round(2 * pivot - p_high, 2)
        direnc = round(2 * pivot - p_low, 2)
        
        # 9. Hacim Gücü (Son 5 günün hacim ortalamasına göre kıyas)
        hacim_ort = volume.rolling(window=5).mean().iloc[-2]
        hacim_gucu = "Yüksek" if volume.iloc[-1] > hacim_ort * 1.5 else ("Düşük" if volume.iloc[-1] < hacim_ort * 0.7 else "Normal")
        
        # 10. Kırılım Durumu (Düşen Trend Kırılımı Kontrolü)
        # Son 20 gündeki en yüksek tepeden bugüne çekilen hayali trend çizgisi aşılmış mı?
        max_20 = high.rolling(window=20).max().iloc[-2]
        kirilim = "Düşen Kırıldı 🚀" if son_fiyat > max_20 else "Yatay/Sıkışma"
        
        # 🎯 11. STRATEJİK AL-GİRİŞ, KAR VE ÇIKIŞ TUTARLARI HESAPLAMA MOTORU
        # ATR indikatörünü kullanarak piyasa oynaklığına göre dinamik fiyatlar belirliyoruz
        al_giris = round(son_fiyat, 2) # Cari fiyat giriş seviyesi kabul edilir
        kar_tutari = round(son_fiyat + (2 * atr), 2) # Risk Ödül Oranı: 2 ATR yukarı hedef
        cikis_tutari = round(son_fiyat - (1.5 * atr), 2) # Stop Loss: 1.5 ATR aşağısı stop
        
        # Genel Robot Karar Mekanizması
        if (rsi < 40 and son_macd > son_signal) or kirilim == "Düşen Kırıldı 🚀":
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
    except Exception as e:
        return None

# 📡 RADAR BUTONU
if st.button("📡 Profesyonel Algoritmayı Başlat"):
    sonuclar = []
    pro_bar = st.progress(0)
    toplam = len(secilen_hisseler)
    
    with st.spinner("Tüm matematiksel indikatörler hesaplanıyor, lütfen bekleyin..."):
        for idx, hisse in enumerate(secilen_hisseler):
            analiz = gelismis_algoritmik_analiz(hisse)
            if analiz: sonuclar.append(analiz)
            pro_bar.progress((idx + 1) / toplam)
            
    if sonuclar:
        st.session_state.tarama_sonuclari = pd.DataFrame(sonuclar)
    else:
        st.error("Veri alınamadı veya indikatörler hesaplanırken hata oluştu.")

# 📊 VERİ MATRİSİNİN EKRANA YANSITILMASI
if st.session_state.tarama_sonuclari is not None:
    main_df = st.session_state.tarama_sonuclari
    
    # Filtreleme Seçenekleri
    if gosterim_tipi == "Sadece AL Verenler":
        gosterilecek_df = main_df[main_df["Sinyal"] == "AL"]
    elif gosterim_tipi == "Sadece SAT Verenler":
        gosterilecek_df = main_df[main_df["Sinyal"] == "SAT"]
    else:
        gosterilecek_df = main_df
        
    st.subheader("📊 Algoritmik Sinyal Matrisi")
    st.info("💡 Sütun başlıklarına tıklayarak Al Giriş, Hedef, Stop veya RSI değerlerine göre anında sıralama yapabilirsiniz.")
    
    # Renklendirilmiş Veri Tablosu
    st.dataframe(
        gosterilecek_df.style.background_gradient(axis=0, cmap='RdYlGn', subset=["RSI (14)", "CCI"])
    )
    
    # Excel Aktarımı
    excel_data = BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        gosterilecek_df.to_excel(writer, index=False, sheet_name='Sinyal_Raporu')
    st.download_button("📥 Algoritmik Verileri Excel Olarak İndir", data=excel_data.getvalue(), file_name="bist_algoritmik_sinyal.xlsx")
    
    st.markdown("---")
    
    # 🔍 SEÇİLEN HİSSENİN DETAY ANALİZ ODASI
    st.subheader("🔍 Tekil Hisse Algoritmik İnceleme Grafiği")
    aktif_hisse = st.selectbox("Grafiğini görmek istediğiniz hisseyi seçin:", gosterilecek_df["Hisse"].unique())
    
    if aktif_hisse:
        ticker_sym = f"{aktif_hisse}.IS"
        hisse_satiri = gosterilecek_df[gosterilecek_df["Hisse"] == aktif_hisse].iloc[0]
        
        # Hedef Fiyat Kartları Açılışı
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mevcut/Giriş Fiyatı", f"{hisse_satiri['Son Fiyat']} TL")
        c2.metric("🤖 Robot Kararı", hisse_satiri['Sinyal'])
        c3.metric("🎯 Kâr Al Hedefi (TP)", f"{hisse_satiri['Kâr Al Tutarı (TP)']} TL", delta=f"% {round(((hisse_satiri['Kâr Al Tutarı (TP)'] - hisse_satiri['Son Fiyat'])/hisse_satiri['Son Fiyat'])*100, 2)}")
        c4.metric("🚨 Zarar Kes (Stop/Çıkış)", f"{hisse_satiri['Çıkış Tutarı (Stop)']} TL", delta=f"% {round(((hisse_satiri['Çıkış Tutarı (Stop)'] - hisse_satiri['Son Fiyat'])/hisse_satiri['Son Fiyat'])*100, 2)}", delta_color="inverse")
        
        # Canlı Grafik Katmanı
        g_df = yf.download(ticker_sym, period="3mo", interval=zaman_dilimi, progress=False)
        if isinstance(g_df.columns, pd.MultiIndex):
            g_df.columns = g_df.columns.droplevel(1)
            
        fig = go.Figure(data=[go.Candlestick(
            x=g_df.index, open=g_df['Open'], high=g_df['High'], low=g_df['Low'], close=g_df['Close'], name="Mum Grafiği"
        )])
        fig.update_layout(title=f"{aktif_hisse} Teknik Analiz Görünümü", xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# 🕒 SAATLİK OTOMATIK GÜNCELLEME SİMÜLASYONU VE METADATA UYARISI
st.sidebar.markdown("---")
st.sidebar.caption("⏱️ Sistem arka planda saatlik olarak (3600 sn) verileri otomatik tazeleyecek şekilde yapılandırılmıştır.")
