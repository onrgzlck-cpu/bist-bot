-- coding: utf-8 --
import streamlit as st
import yfinance as yf
import pandas as pd

1. Sayfa Ayarları ve Başlık
st.set_page_config(page_title="BIST SMC Sinyal Paneli", layout="wide")
st.title("📊 BIST - Smart Money Concept (SMC) Sinyal Tarayıcı")
st.write("Fair Value Gap (FVG) yapısına göre otomatik giriş, hedef ve stop seviyeleri.")

İzleme Listesi (İstediğiniz hisseleri buraya ekleyebilirsiniz)
HISSELER = ["DOFRB.IS", "GEREL.IS", "THYAO.IS", "EREGL.IS", "AKBNK.IS", "ASELS.IS", "TUPRS.IS"]

Yan Menü Ayarları
zaman_dilimi = st.sidebar.selectbox("Zaman Dilimi (Interval)", ["1h", "1d", "15m"])
periyot_eslesme = {"15m": "5d", "1h": "1mo", "1d": "3mo"}
secilen_periyot = periyot_eslesme.get(zaman_dilimi, "1mo")

def smc_sinyal_bul(ticker, period, interval):
try:
# Tekil veri çekme ve sütunları temizleme
df = yf.download(ticker, period=period, interval=interval, progress=False)
if df.empty or len(df) < 5:
return None

# Sütun isimlerini tekilleştirme (yfinance bug koruması)
if isinstance(df.columns, pd.MultiIndex):
df.columns = df.columns.droplevel(1)

# Son tamamlanmış mumları alıyoruz
h1 = float(df['High'].iloc[-3]) # 1. Mumun Tepesi
l3 = float(df['Low'].iloc[-1]) # 3. Mumun Dibinin Başlangıcı
current_price = float(df['Close'].iloc[-1]) # Anlık Kapanış Fiyatı

# BOĞA YÖNLÜ FVG TESPİTİ (Fiyat yukarı fırlamış, arkada boşluk kalmış)
if h1 < l3:
giris_seviyesi = h1 # Fiyat buraya esnerse ALIM (Gap altı)
cikis_seviyesi = l3 # Hedef / Kâr Alma noktası (Gap üstü)
stop_loss = giris_seviyesi * 0.98 # Sabit %2 Stop Risk Yönetimi

# Potansiyel kâr oranı hesaplama
kar_orani = ((cikis_seviyesi - giris_seviyesi) / giris_seviyesi) * 100

# Sinyal Koşulu: Fiyat boşluğun yakınlarında veya içindeyse yakala
if current_price >= (giris_seviyesi * 0.99) and current_price <= (cikis_seviyesi * 1.01):
return {
"Hisse Sembolü": ticker.replace(".IS", ""),
"Güncel Fiyat (TL)": round(current_price, 2),
"Giriş Seviyesi (AL)": round(giris_seviyesi, 2),
"Hedef Fiyat (SAT)": round(cikis_seviyesi, 2),
"Stop Loss (%2)": round(stop_loss, 2),
"Potansiyel Kâr": f"%{round(kar_orani, 2)}"
}
except Exception as e:
# Hataları arka planda yut, paneli çökertme
pass
return None

4. Arayüz Butonu ve Tetikleme
if st.button("Piyasayı Tara ve Fırsatları Bul 🔍"):
sinyaller = []

with st.spinner("BIST Hisseleri SMC modeline göre taranıyor..."):
for hisse in HISSELER:
sonuc = smc_sinyal_bul(hisse, period=secilen_periyot, interval=zaman_dilimi)
if sonuc:
sinyaller.append(sonuc)

if sinyaller:
sinyal_df = pd.DataFrame(sinyaller)
st.success(f"🔥 Harika! Piyasada {len(sinyaller)} adet potansiyel SMC alım fırsatı tespit edildi.")

# Tabloyu ekrana bas ve renklendir
st.dataframe(sinyal_df.style.background_gradient(axis=0, cmap='Greens', subset=["Giriş Seviyesi (AL)", "Hedef Fiyat (SAT)"]))
else:
st.info("Şu anda izleme listenizdeki hisselerde kriterlere uyan aktif bir FVG (Boşluk) giriş sinyali bulunamadı.")