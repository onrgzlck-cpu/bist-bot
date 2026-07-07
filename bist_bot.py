import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="BIST Gelişmiş Analiz Terminali", layout="wide")

st.title("🦅 BIST Pro Analiz ve Radar Terminali")
st.write("Akşam analizleri için teknik, temel ve grafik destekli tarama sistemi.")

# 📑 TÜM BIST LİSTESİ (Endeksler ve hatalı kelimeler ayıklandı/optimize edildi)
TUM_HISSELER = [
    "A1CAP.IS","A1YEN.IS","AAGYO.IS","ACSEL.IS","ADEL.IS","ADESE.IS","ADGYO.IS","AEFES.IS","AFYON.IS","AGESA.IS",
    "AGHOL.IS","AGROT.IS","AGYO.IS","AHGAZ.IS","AHSGY.IS","AKBNK.IS","AKCNS.IS","AKENR.IS","AKFGY.IS","AKFIS.IS",
    "AKFYE.IS","AKGRT.IS","AKHAN.IS","AKMGY.IS","AKSA.IS","AKSEN.IS","AKSGY.IS","AKSUE.IS","AKYHO.IS","ALARK.IS",
    "ALBRK.IS","ALCAR.IS","ALCTL.IS","ALFAS.IS","ALGYO.IS","ALKA.IS","ALKIM.IS","ALKLC.IS","ALTNY.IS","ALVES.IS",
    "ANELE.IS","ANGEN.IS","ANHYT.IS","ANSGR.IS","ARASE.IS","ARCLK.IS","ARDYZ.IS","ARENA.IS","ARFYE.IS","ARMGD.IS",
    "ARSAN.IS","ARTMS.IS","ARZUM.IS","ASELS.IS","ASGYO.IS","ASTOR.IS","ASUZU.IS","ATAGY.IS","ATAKP.IS","ATATP.IS",
    "ATATR.IS","ATEKS.IS","ATLAS.IS","ATSYH.IS","AVGYO.IS","AVHOL.IS","AVOD.IS","AVPGY.IS","AVTUR.IS","AYCES.IS",
    "AYDEM.IS","AYEN.IS","AYES.IS","AYGAZ.IS","AZTEK.IS","BAGFS.IS","BAHKM.IS","BAKAB.IS","BALAT.IS","BALSU.IS",
    "BANVT.IS","BARMA.IS","BASCM.IS","BASGZ.IS","BAYRK.IS","BEGYO.IS","BERA.IS","BESLR.IS","BEYAZ.IS","BFREN.IS",
    "BIENY.IS","BIGCH.IS","BIGEN.IS","BIMAS.IS","BINBN.IS","BINHO.IS","BIOEN.IS","BIZIM.IS","BJKAS.IS","BLCYT.IS",
    "BLUME.IS","BMSCH.IS","BMSTL.IS","BNTAS.IS","BOBET.IS","BORLS.IS","BORSK.IS","BOSSA.IS","BRISA.IS","BRKO.IS",
    "BRKSN.IS","BRKVY.IS","BRLSM.IS","BRMEN.IS","BRSAN.IS","BRYAT.IS","BSOKE.IS","BTCIM.IS","BUCIM.IS","BURCE.IS",
    "BURVA.IS","BVSAN.IS","BYDNR.IS","CANTE.IS","CASA.IS","CATES.IS","CCOLA.IS","CELHA.IS","CEMAS.IS","CEMTS.IS",
    "CEOEM.IS","CIMSA.IS","CLEBI.IS","CMBTN.IS","CMENT.IS","CONSE.IS","COSMO.IS","CRDFA.IS","CRFSA.IS","CUSAN.IS",
    "CVKMD.IS","CWENE.IS","DAGI.IS","DAPGM.IS","DARDL.IS","DCTTR.IS","DENGE.IS","DERHL.IS","DERIM.IS","DESA.IS",
    "DESPC.IS","DEVA.IS","DGATE.IS","DGGYO.IS","DGNMO.IS","DIRIT.IS","DITAS.IS","DMRGD.IS","DMSAS.IS","DNISI.IS",
    "DOAS.IS","DOCO.IS","DOFER.IS","DOFRB.IS","DOGUB.IS","DOHOL.IS","DOKTA.IS","DUNYH.IS","DURDO.IS","DURKN.IS",
    "DYOBY.IS","DZGYO.IS","EBEBK.IS","ECILC.IS","ECZYT.IS","EDATA.IS","EDIP.IS","EFOR.IS","EGEEN.IS","EGEGY.IS",
    "EGEPO.IS","EGGUB.IS","EGPRO.IS","EGSER.IS","EKGYO.IS","EKIZ.IS","EKOS.IS","EKSUN.IS","ELITE.IS","EMKEL.IS",
    "EMNIS.IS","ENERY.IS","ENJSA.IS","ENKAI.IS","ENSRI.IS","ENTRA.IS","EPLAS.IS","ERBOS.IS","ERCB.IS","EREGL.IS",
    "ERSU.IS","ESCAR.IS","ESCOM.IS","ESEN.IS","ETILR.IS","ETYAT.IS","EUHOL.IS","EUKYO.IS","EUPWR.IS","EUREN.IS",
    "EUYO.IS","EYGYO.IS","FADE.IS","FENER.IS","FLAP.IS","FMIZP.IS","FONET.IS","FORMT.IS","FORTE.IS","FRIGO.IS",
    "FROTO.IS","FZLGY.IS","GARAN.IS","GARFA.IS","GATEG.IS","GEDIK.IS","GEDZA.IS","GENIL.IS","GENTS.IS","GEREL.IS",
    "GESAN.IS","GIPTA.IS","GLBMD.IS","GLCVY.IS","GLRMK.IS","GLRYH.IS","GLYHO.IS","GMTAS.IS","GOKNR.IS","GOLTS.IS",
    "GOODY.IS","GOZDE.IS","GRNYO.IS","GRSEL.IS","GSDDE.IS","GSDHO.IS","GSRAY.IS","GUBRF.IS","GWIND.IS","GZNMI.IS",
    "HALKB.IS","HALKS.IS","HATEK.IS","HATSN.IS","HDFGS.IS","HEDEF.IS","HEKTS.IS","HKTM.IS","HLGYO.IS","HOROZ.IS",
    "HRKET.IS","HTTBT.IS","HUBVC.IS","HUNER.IS","HURGZ.IS","ICBCT.IS","ICUGS.IS","IDGYO.IS","IEYHO.IS","IHAAS.IS",
    "IHEVA.IS","IHGZT.IS","IHLAS.IS","IHLGM.IS","IHYAY.IS","IMASM.IS","INDES.IS","INFO.IS","INGRM.IS","INTEM.IS",
    "INVEO.IS","INVES.IS","ISATR.IS","ISBIR.IS","ISBTR.IS","ISCTR.IS","ISDMR.IS","ISFIN.IS","ISGSY.IS","ISGYO.IS",
    "ISKPL.IS","ISKUR.IS","ISMEN.IS","ISSEN.IS","ISYAT.IS","IZENR.IS","IZFAS.IS","IZINV.IS","IZMDC.IS","JANTS.IS",
    "KAPLM.IS","KAREL.IS","KARSN.IS","KARTN.IS","KATMR.IS","KAYSE.IS","KBORU.IS","KCAER.IS","KCHOL.IS","KENT.IS",
    "KERVN.IS","KFEIN.IS","KGYO.IS","KIMMR.IS","KLGYO.IS","KLKIM.IS","KLMSN.IS","KLNMA.IS","KLRHO.IS","KLSER.IS",
    "KLSYN.IS","KMPUR.IS","KNFRT.IS","KOCMT.IS","KONKA.IS","KONTR.IS","KONYA.IS","KOPOL.IS","KORDS.IS","KOTON.IS",
    "KRDMA.IS","KRDMB.IS","KRDMD.IS","KRGYO.IS","KRONT.IS","KRPLS.IS","KRSTL.IS","KRTEK.IS","KRVGD.IS","KSTUR.IS",
    "KTLEV.IS","KTSKR.IS","KUTPO.IS","KUVVA.IS","KUYAS.IS","KZBGY.IS","KZGYO.IS","LIDER.IS","LIDFA.IS","LILAK.IS",
    "LINK.IS","LKMNH.IS","LMKDC.IS","LOGO.IS","LUKSK.IS","MAALT.IS","MACKO.IS","MAGEN.IS","MAKIM.IS","MAKTK.IS",
    "MANAS.IS","MARBL.IS","MARKA.IS","MARTI.IS","MAVI.IS","MEDTR.IS","MEGAP.IS","MEGMT.IS","MEKAG.IS","MEPET.IS",
    "MERCN.IS","MERIT.IS","MERKO.IS","METRO.IS","MGROS.IS","MHRGY.IS","MIATK.IS","MMCAS.IS","MNDRS.IS","MNDTR.IS",
    "MOBTL.IS","MOGAN.IS","MPARK.IS","MRGYO.IS","MRSHL.IS","MSGYO.IS","MTRKS.IS","MTRYO.IS","MZHLD.IS","NATEN.IS",
    "NETAS.IS","NIBAS.IS","NTGAZ.IS","NTHOL.IS","NUGYO.IS","NUHCM.IS","OBAMS.IS","OBASE.IS","ODAS.IS","ODINE.IS",
    "OFSYM.IS","ONCSM.IS","ONRYT.IS","ORCAY.IS","ORGE.IS","ORMA.IS","ORZAX.IS","OSMEN.IS","OSTIM.IS","OTKAR.IS",
    "OTTO.IS","OYAKC.IS","OYAYO.IS","OYLUM.IS","OYYAT.IS","OZATD.IS","OZGYO.IS","OZKGY.IS","OZRDN.IS","OZSUB.IS",
    "OZYSR.IS","PAGYO.IS","PAMEL.IS","PAPIL.IS","PARSN.IS","PASEU.IS","PATEK.IS","PCILT.IS","PEKGY.IS","PENGD.IS",
    "PENTA.IS","PETKM.IS","PETUN.IS","PGSUS.IS","PINSU.IS","PKART.IS","PKENT.IS","PLTUR.IS","PNLSN.IS","PNSUT.IS",
    "POLHO.IS","POLTK.IS","PRDGS.IS","PRKAB.IS","PRKME.IS","PRZMA.IS","PSDTC.IS","PSGYO.IS","QNBFK.IS","QNBTR.IS",
    "QUAGR.IS","RALYH.IS","RAYSG.IS","REEDR.IS","RGYAS.IS","RNPOL.IS","RODRG.IS","RTALB.IS","RUBNS.IS","RYGYO.IS",
    "RYSAS.IS","SAFKR.IS","SAHOL.IS","SAMAT.IS","SANEL.IS","SANFM.IS","SANKO.IS","SARKY.IS","SASA.IS","SAYAS.IS",
    "SDTTR.IS","SEGMN.IS","SEGYO.IS","SEKFK.IS","SEKUR.IS","SELEC.IS","SELVA.IS","SERNT.IS","SEYKM.IS","SILVR.IS",
    "SISE.IS","SKBNK.IS","SKTAS.IS","SMART.IS","SMRTG.IS","SMRVA.IS","SNGYO.IS","SNICA.IS","SNPAM.IS","SODSN.IS",
    "SOKE.IS","SOKM.IS","SONME.IS","SRVGY.IS","SUMAS.IS","SUNTK.IS","SURGY.IS","SUWEN.IS","TABGD.IS","TARKM.IS",
    "TATEN.IS","TATGD.IS","TAVHL.IS","TBORG.IS","TCELL.IS","TDGYO.IS","TEKTU.IS","TERA.IS","TEZOL.IS","TGSAS.IS",
    "THYAO.IS","TKFEN.IS","TKNSA.IS","TLMAN.IS","TMPOL.IS","TMSN.IS","TNZTP.IS","TOASO.IS","TRALT.IS","TRCAS.IS",
    "TRGYO.IS","TRHOL.IS","TRILC.IS","TSGYO.IS","TSKB.IS","TSPOR.IS","TTKOM.IS","TTRAK.IS","TUCLK.IS","TUKAS.IS",
    "TUPRS.IS","TUREX.IS","TURGG.IS","TURSG.IS","UFUK.IS","ULAS.IS","ULKER.IS","ULUFA.IS","ULUSE.IS","ULUUN.IS",
    "UNLU.IS","USAK.IS","VAKBN.IS","VAKFA.IS","VAKFN.IS","VAKKO.IS","VANGD.IS","VBTYZ.IS","VERTU.IS","VERUS.IS",
    "VESBE.IS","VESTL.IS","VKFYO.IS","VKGYO.IS","VKING.IS","VRGYO.IS","YAPRK.IS","YATAS.IS","YAYLA.IS","YBTAS.IS",
    "YEOTK.IS","YESIL.IS","YGGYO.IS","YIGIT.IS","YKBNK.IS","YKSLN.IS","YONGA.IS","YUNSA.IS","YYAPI.IS","YYLGD.IS",
    "ZEDUR.IS","ZERGY.IS","ZGYO.IS","ZOREN.IS","ZRGYO.IS"
]

# 2. SOL MENÜ (FİLTRELER VE SEÇİMLER)
st.sidebar.header("⚙️ Kontrol Paneli")

hepsini_sec = st.sidebar.checkbox("Tüm Hisseleri Seç (%d Adet)" % len(TUM_HISSELER), value=True)
if hepsini_sec:
    secilen_hisseler = TUM_HISSELER
else:
    secilen_hisseler = st.sidebar.multiselect("Hisseleri Seçin", TUM_HISSELER, default=["DOFRB.IS", "GEREL.IS", "THYAO.IS"])

zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])
gosterim_tipi = st.sidebar.radio("Tablo Filtresi", ["Tüm Liste (Sinyalsizler Dahil)", "Sadece Sinyal Verenler"])

# 🔄 MOBİLDE KAPANMALARA KARŞI AGRESİF ÖNBELLEK (HAFIZA) MEKANİZMASI
@st.cache_data(ttl=1800) # Verileri 30 dakika hafızada tutar, bağlantı kopsa da kaldığı yerden devam eder
def detayli_analiz_yap(ticker):
    try:
        # Akşam analizi için kararlı günlük veriler
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
        
        # SMC (Fair Value Gap) Kontrolü
        h1 = float(en_yuksekler.iloc[-3])
        l3 = float(en_dusukler.iloc[-1])
        
        # --- TEMEL ANALİZ ---
        ticker_obj = yf.Ticker(ticker)
        hisse_bilgisi = ticker_obj.info
        fk = hisse_bilgisi.get('trailingPE', "N/A")
        pd_dd = hisse_bilgisi.get('priceToBook', "N/A")
        sektor = hisse_bilgisi.get('sector', "Bilinmiyor")
        
        return {
            "Hisse": ticker.replace(".IS", ""),
            "Son Kapanış (TL)": round(son_fiyat, 2),
            "SMC Durumu": "SMC Alım (FVG)" if h1 < l3 else "Normal",
            "SMC Giriş (Retest)": round(h1, 2) if h1 < l3 else "-",
            "SMC Hedef": round(l3, 2) if h1 < l3 else "-",
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
        return news[:3] if news else []
    except:
        return []

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='BIST_Analiz')
    processed_data = output.getvalue()
    return processed_data

# 4. RADAR TARAMA BAŞLANGICI
if st.button("📡 Radar Taramasını Başlat"):
    sonuclar = []
    
    # İlerleme çubuğu (Büyük liste için kullanıcıyı bilgilendirmek şart)
    pro_bar = st.progress(0)
    toplam_hisse = len(secilen_hisseler)
    
    with st.spinner("Tüm BIST taranıyor... Telefon ekranınızı kapatmayın."):
        for idx, hisse in enumerate(secilen_hisseler):
            analiz = detayli_analiz_yap(hisse)
            if analiz:
                sonuclar.append(analiz)
            # İlerlemeyi güncelle
            pro_bar.progress((idx + 1) / toplam_hisse)
                
    if sonuclar:
        main_df = pd.DataFrame(sonuclar)
        
        if gosterim_tipi == "Sadece Sinyal Verenler":
            gosterilecek_df = main_df[main_df["SMC Durumu"] == "SMC Alım (FVG)"]
        else:
            gosterilecek_df = main_df
            
        st.subheader("📊 Tarama Sonuç Matrisi (Excel Tarzı)")
        
        # Filtreleme ve Sıralama Arayüzü (Streamlit dahili)
        st.dataframe(gosterilecek_df.style.background_gradient(axis=0, cmap='YlGn', subset=["RSI (14)"]))
        
        # EXCEL'E AKTARMA BUTONU
        excel_data = to_excel(gosterilecek_df)
        st.download_button(
            label="📥 Tüm Sonuçları Excel (.xlsx) Olarak İndir",
            data=excel_data,
            file_name="bist_aksam_raporu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        # 5. DETAY & GRAFİK & HABER SEÇİM ALANI
        st.subheader("🔍 Tekil Hisse Detay Analizi & Güncel Grafik")
        secilen_detay_hisse = st.selectbox("Detayını ve Canlı Grafiğini İncelemek İstediğiniz Hisseyi Seçin", gosterilecek_df["Hisse"].unique())
        
        if secilen_detay_hisse:
            ticker_sym = f"{secilen_detay_hisse}.IS"
            
            # İnteraktif Grafik Çizimi
            g_df = yf.download(ticker_sym, period="3mo", interval=zaman_dilimi, progress=False)
            if isinstance(g_df.columns, pd.MultiIndex):
                g_df.columns = g_df.columns.droplevel(1)
                
            fig = go.Figure(data=[go.Candlestick(
                x=g_df.index, open=g_df['Open'], high=g_df['High'], low=g_df['Low'], close=g_df['Close'], name="Mum Grafiği"
            )])
            fig.update_layout(title=f"{secilen_detay_hisse} Teknik Mum Grafiği", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # Haber Başlıkları
            st.subheader(f"📰 {secilen_detay_hisse} Küresel Haber Akışı & Algı")
            haberler = haberleri_getir(ticker_sym)
            if haberler:
                for h in haberler:
                    st.write(f"🔗 **[{h['title']}]({h['link']})**")
                    st.caption(f"Yayıncı: {h.get('publisher', 'Bilinmiyor')}")
            else:
                st.info("Bu hisseye ait güncel haber akışı bulunamadı.")
            
    else:
        st.error("Seçilen hisselerden analiz verisi üretilemedi.")
