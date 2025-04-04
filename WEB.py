import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
from plotly.subplots import make_subplots
import plotly.express as px
import seaborn as sns
import matplotlib.colors as mcolors
import re
from streamlit_option_menu import option_menu
from ta.trend import SMAIndicator, EMAIndicator, MACD, PSARIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from fpdf import FPDF
from io import BytesIO
import tempfile
import plotly.io as pio
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

from pdf import generate_pdf
from readdata import process_financial_data
from drawchart import draw_chart

st.set_page_config(layout="wide")  # Giao diện toàn màn hình

# **Chèn CSS tùy chỉnh để áp dụng font "Poppins" cho toàn bộ trang**
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif;
    }
    h1 {
        font-size: 36px !important;
        font-weight: 700 !important;
        text-align: center;
        color: #111111;
    }

    h2 {
        font-size: 30px !important;
        font-weight: 600 !important;
        text-align: center;
        color: #333333;
    }

    h3 {
        font-size: 22px !important;
        font-weight: 600 !important;
        text-align: center;
        color: #333333;
    }

    .subheader-custom {
        font-size: 18px !important;
        font-weight: 600 !important;
        text-align: center;
        margin-bottom: 5px;
    }

    p, label, div {
        font-weight: 400;
        font-size: 14px;
        color: #444444;
    }

    .stSidebar {
        background-color: #F8F9FA;
    }

    .stButton>button {
        font-family: 'Poppins', sans-serif;
        font-size: 14px;
        font-weight: 600;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True)

# === Hàm load dữ liệu ===
def load_data_by_path(file_path):
    df = pd.read_csv(file_path)
    df['ngày'] = pd.to_datetime(df['ngày'], format='%Y-%m-%d').dt.date
    return df


# Sidebar với menu tùy chỉnh
with st.sidebar:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                background-color: Black !important; 
                padding: 20px;
                border-right: 1px solid #8A9BA8;
                border-radius: 2px;
                box-shadow: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-weight: bold; color:yellow ;'>Trang chủ</h2>",
                unsafe_allow_html=True)
    selected = option_menu(
        menu_title=None,
        options=["0. PHÂN TÍCH TỔNG HỢP", "1. Tổng quan thị trường","2. Tổng quan theo ngành", "3. Phân tích kỹ thuật", "4. Báo cáo tài chính"],
        icons=["stars", "bar-chart", "database", "clipboard-data", "book"],
        default_index=0,
        styles={"container": {"background-color": "black", "border-radius": "0px", "box-shadow": "none",
                              "padding": "0px"},
                "nav-link": {"font-size": "16px", "font-weight": "normal", "color": "white", "text-align": "left",
                             "padding": "10px"},
                "nav-link-selected": {"background-color": "#B0BEC5", "font-weight": "bold", "color": "Black",
                                      "border-radius": "5px"}})

@st.cache_data
def load_and_process_data():
    # Load the Excel file and process the data
    EXCEL_PATH = "./Data/Cleaned_Vietnam_Marketcap.xlsx"
    xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
    df1 = xls.parse("Sheet1").fillna({"Sector": "Unknown Sector"})
    df1["Sector"] = df1["Sector"].replace("-", "Uncategorized")

    df2 = xls.parse("Sheet2")
    df2.columns = [str(col).replace(" 00:00:00", "") for col in df2.columns]
    df2["Name"] = df2["Name"].str.replace(" - MARKET VALUE", "", regex=False)
    df2["Code"] = df2["Code"].str.replace("(MV)", "", regex=False)

    merged_df = df2.merge(df1[["Name", "Sector"]], on="Name", how="left")
    date_columns = merged_df.columns[2:-1]
    merged_df[date_columns] = merged_df[date_columns].apply(pd.to_numeric, errors='coerce')

    return df1, merged_df, date_columns

# Load data globally
DF1, MERGED_DF, DATE_COLUMNS = load_and_process_data()

# Helper function to plot stock price
def plot_stock_price(merged_df, stock_code):
    """Vẽ biểu đồ đường giá cổ phiếu theo mã cổ phiếu."""
    stock_data = merged_df[merged_df['Code'] == stock_code]
    if stock_data.empty:
        st.warning(f"Không tìm thấy cổ phiếu có mã {stock_code}")
        return None

    stock_data = stock_data.iloc[:, 2:-1]  # Exclude 'Name', 'Code', 'Sector' columns
    stock_data = stock_data.T  # Transpose so that dates are on the x-axis
    stock_data.index = pd.to_datetime(stock_data.index)  # Convert index to datetime

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(stock_data, label=f"{stock_code}")
    ax.set_title(f"Giá trị vốn hoá thị trường của {stock_code} theo thời gian")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Giá trị vốn hoá thị trường")
    ax.legend()
    ax.grid(True)
    return fig

# Plot sector treemap
def plot_sector_treemap(selected_date):
    sector_marketcap = MERGED_DF.groupby('Sector')[selected_date].sum().reset_index()
    fig = px.treemap(sector_marketcap, path=['Sector'], values=selected_date,
                        title=f'Vốn hóa thị trường theo ngành ({selected_date})',
                        color=selected_date, color_continuous_scale='blues', height=600)
    return fig

# Plot bubble chart
def plot_bubble_chart(selected_date):
    bubble_data = MERGED_DF.groupby(['Sector', 'Code'])[selected_date].sum().reset_index()
    bubble_data = bubble_data[bubble_data[selected_date] > 0]
    if bubble_data.empty:
        st.warning(f"Không có dữ liệu hợp lệ cho ngày {selected_date}!")
        return None

    fig = px.scatter(
        bubble_data, x='Sector', y=selected_date, size=selected_date,
        hover_name='Code', title=f'Bubble Chart ({selected_date})',
        size_max=50, color='Sector', width=1000, height=600
    )
    return fig

# Generate PDF report with stock price plot
def generate_pdf_by_stock_code(stock_code):
    progress_bar = st.progress(0)  # Initialize progress bar
    with st.spinner("📄 Đang tạo báo cáo PDF, vui lòng đợi..."):
        # Define SECTOR_MARKETCAP_T inside the function or globally
        SECTOR_MARKETCAP_T = MERGED_DF.groupby("Sector")[DATE_COLUMNS].sum().T
        SECTOR_MARKETCAP_T.index = pd.to_datetime(SECTOR_MARKETCAP_T.index)

        # Initialize PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("DejaVu", "", r"./DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", size=12)

        pdf.cell(200, 10, "Báo cáo thị trường chứng khoán Việt Nam", ln=True, align='C')
        pdf.ln(10)

        # Calculate top sectors
        top_sectors = SECTOR_MARKETCAP_T.sum().nlargest(5)
        for sector, value in top_sectors.items():
            pdf.cell(200, 10, f"{sector}: {value:,.0f} VNĐ", ln=True)

        pdf.ln(10)

    for i, plot_func in enumerate([plot_sector_treemap, plot_bubble_chart]):
        progress_bar.progress((i + 1) / 4)  # Update progress
        if plot_func in [plot_sector_treemap, plot_bubble_chart]:
            fig = plot_func(DATE_COLUMNS[-1])
        else:
            fig = plot_func()

        if fig is None:
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
            if hasattr(fig, "write_image"):
                fig.write_image(temp_img.name, format="png", width=800, height=600, engine="kaleido")
            else:
                fig.savefig(temp_img.name, format="png", dpi=100)

        pdf.image(temp_img.name, x=10, w=180)
        pdf.ln(5)

    # Generate the stock price plot for the given stock code
    fig_stock = plot_stock_price(MERGED_DF, stock_code)
    if fig_stock:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img_stock:
            fig_stock.savefig(temp_img_stock.name, format="png", dpi=100)

        pdf.ln(10)  # Adding some space before the image
        pdf.image(temp_img_stock.name, x=10, w=180)  # Adding the stock price plot image

    # Save the PDF to a file
    pdf_name = "Tong_quan_thi_truong_{stock_code}.pdf"
    pdf_path = "{pdf_name}.pdf"
    pdf.output(pdf_path, "F")

    with open(pdf_path, "rb") as file:
        st.success(f"✅ PDF đã được tạo: {pdf_path}")
        st.download_button("Tổng quan thị trường", data=file, file_name=pdf_path, mime="application/pdf")

def load_data_by_file(files):
    dfs = {}
    for path in files:
        df = pd.read_csv(path, encoding='utf-8')
        df.columns = df.columns.str.strip()  # Xóa khoảng trắng
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")  # Chuyển đổi định dạng Date
        dfs[path] = df

    # Gộp tất cả dữ liệu vào một dataframe chung
    data = pd.concat(dfs.values(), ignore_index=True)

    # Lọc bỏ ngày không có dữ liệu
    data = data.dropna(subset=["Date", "Net.F_Val", "Close"])  # Giữ lại các ngày có dữ liệu hợp lệ

    # Sắp xếp lại dữ liệu theo thời gian
    data = data.sort_values(by=["Date"]).reset_index(drop=True)

    return data


# 📌 Load dữ liệu từ file Excel
@st.cache_data
def load_data_tab3():
    PRICE_DATA_PATH = r'./Data/Processed_Vietnam_Price.xlsx'
    VOLUME_DATA_PATH = r'./Data/Processed_Vietnam_volume_2.xlsx'

    file_price = "./Data/Thong_ke_gia_phan_loai_NDT/Processed_Vietnam_Price_Long.csv.gz"
    file_volume = "./Data/Thong_ke_gia_phan_loai_NDT/Processed_Vietnam_Volume_Long.csv.gz"

    # Phân tích kỹ thuật với MA
    # Đường dẫn đến file CSV trên backend
    FILE_PATH1 = "./Data/Processed_Vietnam_Price.xlsx - Processed_Sheet2.csv"

    # Load dữ liệu từ file Excel
    df_price = pd.read_excel(PRICE_DATA_PATH)
    df_volume = pd.read_excel(VOLUME_DATA_PATH)

    # Chọn đúng cột ngày từ H -> BHN (cột ngày)
    date_columns = df_price.columns[7:]  # Cột H là cột thứ 7 (0-based index)

    return df_price, df_volume, date_columns


def select_date(date_columns):
    return st.selectbox("📅 Chọn ngày để hiển thị", date_columns)


def select_time_period():
    """Cho phép người dùng chọn khoảng thời gian"""
    return st.slider("⏳ Chọn số tuần phân tích", min_value=4, max_value=104, value=52, step=2)


def select_time_period_tab3():
    """Cho phép người dùng chọn khoảng thời gian"""
    return st.selectbox("⏳ Chọn khoảng thời gian", [
        "1 tuần", "1 tháng", "3 tháng", "6 tháng", "1 năm", "2 năm", "3 năm", "Toàn bộ"
    ])


def load_data2(price_file, volume_file):
    """Tải dữ liệu từ file CSV nén"""
    try:
        df_price = pd.read_csv(price_file, compression="gzip")
        df_volume = pd.read_csv(volume_file, compression="gzip")

        df_price['Date'] = pd.to_datetime(df_price['Date'], format='%Y%m%d')
        df_volume['Date'] = pd.to_datetime(df_volume['Date'], format='%Y%m%d')

        return df_price, df_volume
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return None, None


# PDF Export Functionality using Matplotlib
def export_pdf_combined(fig_plot, date):
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.8, "Foreign Investor Trading Report", fontsize=14, ha='center')
        plt.text(0.5, 0.6, f"Date Extracted: {date.strftime('%d/%m/%Y')}", fontsize=12, ha='center')
        plt.axis("off")
        pdf.savefig()
        plt.close()

        fig_bytes = pio.to_image(fig_plot, format="png")
        img = plt.imread(BytesIO(fig_bytes))
        plt.figure(figsize=(10, 6))
        plt.imshow(img)
        plt.axis("off")
        pdf.savefig()
        plt.close()
    buf.seek(0)
    return buf


def select_date1(df_price):
    available_dates = sorted(df_price['Date'].dropna().unique())
    return st.date_input("📅 Chọn ngày", value=available_dates[-1], min_value=available_dates[0],
                            max_value=available_dates[-1])


def create_summary_table(df_price, df_volume, selected_date):
    if selected_date not in df_price.columns or selected_date not in df_volume.columns:
        st.warning(f"⚠ Ngày {selected_date} không tồn tại trong dữ liệu!")
        return None

    # 📌 Chuyển cột ngày thành kiểu số (float) để tránh lỗi khi tính toán
    df_price[selected_date] = pd.to_numeric(df_price[selected_date], errors='coerce')
    df_volume[selected_date] = pd.to_numeric(df_volume[selected_date], errors='coerce')

    # Lấy ngày trước đó để tính % Change
    prev_day_index = df_price.columns.get_loc(selected_date) - 1
    if prev_day_index < 7:  # Đảm bảo không lấy cột không hợp lệ
        st.warning("⚠ Không đủ dữ liệu để tính toán % thay đổi.")
        return None

    prev_day = df_price.columns[prev_day_index]

    # 📌 Chuyển đổi ngày trước đó thành số
    df_price[prev_day] = pd.to_numeric(df_price[prev_day], errors='coerce')

    # Tạo bảng kết quả
    df_selected_price = df_price[['Code', 'Name', selected_date]].copy()
    df_selected_volume = df_volume[['Code', selected_date]].copy()

    # Tính % thay đổi
    df_selected_price["% Change"] = ((df_price[selected_date] - df_price[prev_day]) / df_price[prev_day]) * 100

    # Gộp dữ liệu
    df_summary = df_selected_price.merge(df_selected_volume, on="Code", suffixes=("_Giá", "_Khối lượng"))

    df_summary = df_summary.rename(columns={
        str(selected_date) + "_Giá": "Giá đóng cửa",
        str(selected_date) + "_Khối lượng": "Khối lượng giao dịch"
    })
    # Sắp xếp theo % Change giảm dần
    df_summary = df_summary.sort_values(by="% Change", ascending=False)

    return df_summary


# 📌 Hiển thị bảng trong Streamlit với màu sắc
def plot_price_trend(df_price, tickers, selected_date, start_date, date_columns):
    """
    Vẽ biểu đồ xu hướng giá đóng cửa theo thời gian.
    """
    # ✅ Chuyển đổi `date_columns` thành `datetime`
    date_columns_dt = pd.to_datetime(date_columns, format="%Y-%m-%d", errors="coerce").dropna().sort_values()

    # ✅ Kiểm tra nếu `selected_date` không có trong `date_columns_dt`, chọn ngày gần nhất
    if selected_date not in date_columns_dt.values:
        st.warning(f"⚠ Ngày {selected_date.date()} không có trong dữ liệu! Đang chọn ngày gần nhất...")
        selected_date = date_columns_dt.max()  # Chọn ngày gần nhất có trong dữ liệu

    # ✅ Lọc dữ liệu theo khoảng thời gian đã chọn
    selected_dates = date_columns_dt[(date_columns_dt >= start_date) & (date_columns_dt <= selected_date)]

    if selected_dates.empty:
        st.warning("⚠️ Không có dữ liệu trong khoảng thời gian đã chọn!")
        return

    # ✅ Kiểm tra nếu tất cả các ngày đã chọn có trong `df_price`
    selected_dates = selected_dates.intersection(df_price.columns)

    if selected_dates.empty:
        st.warning("⚠ Không có dữ liệu nào cho các ngày đã chọn!")
        return

    # ✅ Lọc dữ liệu
    df_filtered = df_price[["Code", "Name"] + list(selected_dates)].copy()

    # ✅ Chỉ giữ lại các mã cổ phiếu được chọn
    df_filtered = df_filtered[df_filtered["Code"].isin(tickers)]

    if df_filtered.empty:
        st.warning("⚠ Không có dữ liệu nào khớp với mã cổ phiếu đã chọn!")
        return

    # ✅ Chuyển đổi dữ liệu để vẽ biểu đồ
    df_melted = df_filtered.melt(id_vars=["Code", "Name"], var_name="Date", value_name="Price")

    # ✅ Chuyển đổi ngày thành datetime để vẽ biểu đồ
    df_melted["Date"] = pd.to_datetime(df_melted["Date"], errors="coerce")

    # ✅ Vẽ biểu đồ xu hướng giá đóng cửa
    fig = px.line(df_melted, x="Date", y="Price", color="Code",
                    title=f"📈 Xu hướng giá đóng cửa",
                    labels={"Price": "Giá đóng cửa", "Date": "", "Code": "Mã cổ phiếu"})

    st.plotly_chart(fig, use_container_width=True)


def calculate_indicators_snapshot(df_price, df_volume, selected_date):
    """
    Tính toán các chỉ báo (theo snapshot) cho cổ phiếu dựa trên dữ liệu giá và khối lượng.
    Hàm này dùng để hiển thị bảng chỉ báo.
    """
    if selected_date not in df_price.columns or selected_date not in df_volume.columns:
        st.warning(f"⚠ Ngày {selected_date} không tồn tại trong dữ liệu!")
        return None

    prev_day_index = df_price.columns.get_loc(selected_date) - 1
    if prev_day_index < 7:
        st.warning("⚠ Không đủ dữ liệu để tính toán chỉ báo.")
        return None
    prev_day = df_price.columns[prev_day_index]

    df = pd.DataFrame()
    df['Code'] = df_price['Code']
    df['open'] = pd.to_numeric(df_price[prev_day], errors='coerce')
    df['close'] = pd.to_numeric(df_price[selected_date], errors='coerce')
    df['high'] = df_price.loc[:, prev_day:selected_date].max(axis=1)
    df['low'] = df_price.loc[:, prev_day:selected_date].min(axis=1)
    df['volume'] = pd.to_numeric(df_volume[selected_date], errors='coerce')
    df = df.dropna()

    # Tính toán MA
    for period in [20, 50, 100, 200]:
        df[f'sma_{period}'] = SMAIndicator(close=df['close'], window=period).sma_indicator()
        df[f'ema_{period}'] = EMAIndicator(close=df['close'], window=period).ema_indicator()
    # MACD
    macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd_line'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    # PSAR
    psar = PSARIndicator(high=df['high'], low=df['low'], close=df['close'])
    df['psar'] = psar.psar()
    # RSI
    for period in [9, 14, 21]:
        df[f'rsi_{period}'] = RSIIndicator(close=df['close'], window=period).rsi()
    # CCI
    for period in [10, 20, 30]:
        df[f'cci_{period}'] = (df['close'] - df['close'].rolling(period).mean()) / (
                0.015 * df['close'].rolling(period).std())
    # Bollinger Bands
    bollinger = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_middle'] = bollinger.bollinger_mavg()
    df['bb_upper'] = bollinger.bollinger_hband()
    df['bb_lower'] = bollinger.bollinger_lband()
    # OBV
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    # MFI
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['raw_money_flow'] = df['typical_price'] * df['volume']
    df['money_flow_ratio'] = df['raw_money_flow'].rolling(14).sum() / df['raw_money_flow'].rolling(14).sum().shift(
        1)
    df['mfi'] = 100 - (100 / (1 + df['money_flow_ratio']))
    return df


def get_stock_timeseries(stock, df_price, df_volume, date_columns_dt, start_date, end_date):
    """
    Trích xuất chuỗi thời gian cho mã cổ phiếu đã chọn.
    Chỉ lấy các ngày trong khoảng [start_date, end_date].
    Giả sử các cột của df_price, df_volume có tên là chuỗi 'YYYY-MM-DD'.
    """
    # Lọc các ngày hợp lệ
    valid_dates = [d for d in date_columns_dt if start_date <= d <= end_date]

    stock_row = df_price[df_price['Code'] == stock]
    volume_row = df_volume[df_volume['Code'] == stock]
    if stock_row.empty or volume_row.empty:
        st.error("⚠ Không tìm thấy dữ liệu cho mã cổ phiếu này!")
        return None

    prices = []
    volumes = []
    for date_str in valid_dates:
        price_val = pd.to_numeric(stock_row[date_str].values[0], errors='coerce')
        volume_val = pd.to_numeric(volume_row[date_str].values[0], errors='coerce')
        prices.append(price_val)
        volumes.append(volume_val)
    df_ts = pd.DataFrame({
        'Date': valid_dates,
        'close': prices,
        'volume': volumes
    })

    # Xác định giá mở: lấy giá đóng của ngày trước đó (với ngày đầu tiên thì open = close)
    df_ts['open'] = df_ts['close'].shift(1)
    df_ts.loc[df_ts['open'].isna(), 'open'] = df_ts['close']
    # Giả định high = max(open, close), low = min(open, close)
    df_ts['high'] = df_ts[['open', 'close']].max(axis=1)
    df_ts['low'] = df_ts[['open', 'close']].min(axis=1)
    return df_ts


def compute_timeseries_indicators(df):
    n = len(df)
    # Tính SMA & EMA: nếu không đủ dữ liệu cho period, gán NaN
    for period in [20, 50, 100, 200]:
        if n >= period:
            df[f'sma_{period}'] = SMAIndicator(close=df['close'], window=period).sma_indicator()
            df[f'ema_{period}'] = EMAIndicator(close=df['close'], window=period).ema_indicator()
        else:
            df[f'sma_{period}'] = np.nan
            df[f'ema_{period}'] = np.nan

    macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd_line'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()

    psar = PSARIndicator(high=df['high'], low=df['low'], close=df['close'])
    df['psar'] = psar.psar()

    for period in [9, 14, 21]:
        if n >= period:
            df[f'rsi_{period}'] = RSIIndicator(close=df['close'], window=period).rsi()
        else:
            df[f'rsi_{period}'] = np.nan

    for period in [10, 20, 30]:
        if n >= period:
            df[f'cci_{period}'] = (df['close'] - df['close'].rolling(period).mean()) / (
                    0.015 * df['close'].rolling(period).std())
        else:
            df[f'cci_{period}'] = np.nan

    bollinger = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_middle'] = bollinger.bollinger_mavg()
    df['bb_upper'] = bollinger.bollinger_hband()
    df['bb_lower'] = bollinger.bollinger_lband()

    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['raw_money_flow'] = df['typical_price'] * df['volume']
    df['money_flow_ratio'] = df['raw_money_flow'].rolling(14).sum() / df['raw_money_flow'].rolling(14).sum().shift(
        1)
    df['mfi'] = 100 - (100 / (1 + df['money_flow_ratio']))
    return df

    
def update_chart(df, company, selected_indicators, selected_ma, selected_rsi, selected_cci,
                    selected_indicator_combination):
    """
    Xây dựng biểu đồ Plotly dựa trên dữ liệu chuỗi thời gian (df) và các lựa chọn của người dùng.
    Phiên bản này được chuyển thể từ code Dash (update_graph).
    """
    # Nếu không chọn chỉ báo hay tổ hợp nào, chỉ hiển thị biểu đồ nến
    # Tạo figure
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price',
                increasing_line_color='green',
                decreasing_line_color='red',
            )
        ]
    )
    if not selected_indicators and not selected_indicator_combination:
        # Chỉ hiển thị biểu đồ nến
        return fig
    # Nếu chọn tổ hợp chỉ báo, ưu tiên hiển thị tổ hợp
    if selected_indicator_combination:
        if selected_indicator_combination == 'PSAR + SMA':
            # Vẽ PSAR
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['psar'],
                mode='markers',
                name='PSAR',
                marker=dict(color='purple', size=6, symbol='circle'),
                opacity=0.8
            ))

            # Vẽ SMA 20 (ngắn hạn)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['sma_20'],
                mode='lines',
                name='SMA 20 (Short Term)',
                line=dict(color='blue', width=2),
                opacity=0.8
            ))

            # Vẽ SMA 100 (dài hạn)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['sma_100'],
                mode='lines',
                name='SMA 100 (Long Term)',
                line=dict(color='orange', width=2),
                opacity=0.8
            ))

            # Tín hiệu tiếp tục xu hướng giảm mạnh:
            # SMA 20 cắt xuống SMA 100 và PSAR nằm phía trên giá
            bearish_signal = (
                    (df['sma_20'] < df['sma_100']) &  # SMA 20 nằm dưới SMA 100
                    (df['sma_20'].shift(1) >= df['sma_100'].shift(1)) &  # SMA 20 vừa cắt xuống
                    (df['psar'] > df['close'])  # PSAR nằm trên giá
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][bearish_signal],
                y=df['close'][bearish_signal],
                mode='markers',
                name='Bearish Signal (Strong Downtrend)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ))

            # Tín hiệu tiếp tục xu hướng tăng mạnh:
            # SMA 20 cắt lên SMA 100 và PSAR nằm dưới giá
            bullish_signal = (
                    (df['sma_20'] > df['sma_100']) &  # SMA 20 nằm trên SMA 100
                    (df['sma_20'].shift(1) <= df['sma_100'].shift(1)) &  # SMA 20 vừa cắt lên
                    (df['psar'] < df['close'])  # PSAR nằm dưới giá
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][bullish_signal],
                y=df['close'][bullish_signal],
                mode='markers',
                name='Bullish Signal (Strong Uptrend)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ))
        elif selected_indicator_combination == 'PSAR + RSI':
            # Tạo subplots với 2 hàng: 1 hàng cho biểu đồ nến + PSAR, 1 hàng cho RSI
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,  # Dùng chung trục X
                row_heights=[0.7, 0.3],  # Tỷ lệ chiều cao của các hàng
                vertical_spacing=0.05,  # Khoảng cách giữa các hàng
                subplot_titles=["Candlestick with PSAR", "RSI"]
            )

            # Vẽ biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ),
                row=1, col=1
            )

            # Vẽ PSAR trên biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['psar'],
                    mode='markers',
                    name='PSAR',
                    marker=dict(color='purple', size=6, symbol='circle'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Vẽ RSI ở subplot thứ 2 (hàng 2)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['rsi_14'],
                    mode='lines',
                    name='RSI 14',
                    line=dict(color='blue', width=2),
                    opacity=0.8
                ),
                row=2, col=1
            )

            # Vẽ tín hiệu MUA trên biểu đồ nến
            buy_signal = (
                    (df['psar'] < df['close']) &
                    (df['rsi_14'] < 30) &
                    (df['rsi_14'].shift(1) <= df['rsi_14'])
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][buy_signal],
                    y=df['close'][buy_signal],
                    mode='markers',
                    name='Buy Signal (PSAR + RSI)',
                    marker=dict(color='blue', size=20, symbol='triangle-up'),
                    opacity=0.8
                ),
                row=1, col=1
            )
            # Vẽ tín hiệu BÁN trên biểu đồ nến
            sell_signal = (
                    (df['psar'] > df['close']) &
                    (df['rsi_14'] > 70) &
                    (df['rsi_14'].shift(1) >= df['rsi_14'])
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][sell_signal],
                    y=df['close'][sell_signal],
                    mode='markers',
                    name='Sell Signal (PSAR + RSI)',
                    marker=dict(color='orange', size=20, symbol='triangle-down'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Thêm dải màu cho vùng quá mua (RSI > 70) và quá bán (RSI < 30)
            fig.add_shape(
                # Vùng quá mua (RSI > 70) - Màu đỏ
                go.layout.Shape(
                    type="rect",
                    x0=df['Date'].iloc[0], x1=df['Date'].iloc[-1],
                    y0=70, y1=100,
                    line=dict(color="red", width=0),
                    fillcolor="rgba(255, 0, 0, 0.2)",  # Màu đỏ nhạt
                ),
                row=2, col=1
            )
            fig.add_shape(
                # Vùng quá bán (RSI < 30) - Màu xanh
                go.layout.Shape(
                    type="rect",
                    x0=df['Date'].iloc[0], x1=df['Date'].iloc[-1],
                    y0=0, y1=30,
                    line=dict(color="green", width=0),
                    fillcolor="rgba(0, 255, 0, 0.2)",  # Màu xanh nhạt
                ),
                row=2, col=1
            )
        elif selected_indicator_combination == 'PSAR + MACD':
            # Tạo subplots với 2 hàng: 1 hàng cho biểu đồ nến + PSAR, 1 hàng cho MACD
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,  # Dùng chung trục X
                row_heights=[0.7, 0.3],  # Tỷ lệ chiều cao của các hàng
                vertical_spacing=0.05,  # Khoảng cách giữa các hàng
                subplot_titles=["Candlestick with PSAR", "MACD"]
            )

            # Vẽ biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ),
                row=1, col=1
            )

            # Vẽ PSAR trên biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['psar'],
                    mode='markers',
                    name='PSAR',
                    marker=dict(color='purple', size=6, symbol='circle'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Vẽ MACD Line ở subplot thứ 2 (hàng 2)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['macd_line'],
                    mode='lines',
                    name='MACD Line',
                    line=dict(color='blue', width=2),
                    opacity=0.8
                ),
                row=2, col=1
            )

            # Vẽ Signal Line
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['macd_signal'],
                    mode='lines',
                    name='Signal Line',
                    line=dict(color='red', width=2, dash='dot'),
                    opacity=0.8
                ),
                row=2, col=1
            )

            # Vẽ Histogram
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['macd_histogram'],
                    name='MACD Histogram',
                    marker_color=df['macd_histogram'].apply(lambda x: 'green' if x > 0 else 'red'),
                    opacity=0.6
                ),
                row=2, col=1
            )

            # Tín hiệu MUA
            buy_signal = (
                    (df['psar'] < df['close']) &  # PSAR nằm dưới giá
                    (df['macd_line'] > df['macd_signal']) &  # MACD Line cắt Signal Line từ dưới lên
                    (df['macd_histogram'] > 0) &  # Histogram chuyển từ âm sang dương
                    (df['macd_histogram'].shift(1) <= 0)  # Xác nhận chuyển đổi từ âm sang dương
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][buy_signal],
                    y=df['close'][buy_signal],
                    mode='markers',
                    name='Buy Signal (PSAR + MACD)',
                    marker=dict(color='blue', size=20, symbol='triangle-up'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Tín hiệu BÁN
            sell_signal = (
                    (df['psar'] > df['close']) &  # PSAR nằm trên giá
                    (df['macd_line'] < df['macd_signal']) &  # MACD Line cắt Signal Line từ trên xuống
                    (df['macd_histogram'] < 0) &  # Histogram chuyển từ dương sang âm
                    (df['macd_histogram'].shift(1) >= 0)  # Xác nhận chuyển đổi từ dương sang âm
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][sell_signal],
                    y=df['close'][sell_signal],
                    mode='markers',
                    name='Sell Signal (PSAR + MACD)',
                    marker=dict(color='orange', size=20, symbol='triangle-down'),
                    opacity=0.8
                ),
                row=1, col=1
            )
        elif selected_indicator_combination == 'Bollinger Bands + RSI':
            # Tạo subplots với 2 hàng: 1 hàng cho biểu đồ nến + Bollinger Bands, 1 hàng cho RSI
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,  # Dùng chung trục X
                row_heights=[0.7, 0.3],  # Tỷ lệ chiều cao của các hàng
                vertical_spacing=0.05,  # Khoảng cách giữa các hàng
                subplot_titles=["Candlestick with Bollinger Bands", "RSI"]
            )

            # Vẽ biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ),
                row=1, col=1
            )

            # Vẽ Bollinger Bands trên biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['bb_upper'],
                    mode='lines',
                    name='Bollinger Upper Band',
                    line=dict(color='blue', width=1, dash='dash'),
                    opacity=0.8
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['bb_middle'],
                    mode='lines',
                    name='Bollinger Middle Band',
                    line=dict(color='grey', width=1),
                    opacity=0.8
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['bb_lower'],
                    mode='lines',
                    name='Bollinger Lower Band',
                    line=dict(color='blue', width=1, dash='dash'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Vẽ RSI trên subplot thứ 2 (hàng 2)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['rsi_14'],
                    mode='lines',
                    name='RSI (14)',
                    line=dict(color='purple', width=2),
                    opacity=0.8,
                    yaxis='y2'  # Hiển thị RSI trên trục y phụ
                ),
                row=2, col=1
            )

            # Tín hiệu MUA
            buy_signal = (
                    (df['close'] <= df['bb_lower']) &  # Giá chạm hoặc thấp hơn dải dưới của Bollinger Bands
                    (df['rsi_14'] < 30)  # RSI dưới 30 (quá bán)
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][buy_signal],
                    y=df['close'][buy_signal],
                    mode='markers',
                    name='Buy Signal (BB + RSI)',
                    marker=dict(color='blue', size=20, symbol='triangle-up'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Tín hiệu BÁN
            sell_signal = (
                    (df['close'] >= df['bb_upper']) &  # Giá chạm hoặc vượt dải trên của Bollinger Bands
                    (df['rsi_14'] > 70)  # RSI trên 70 (quá mua)
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][sell_signal],
                    y=df['close'][sell_signal],
                    mode='markers',
                    name='Sell Signal (BB + RSI)',
                    marker=dict(color='orange', size=20, symbol='triangle-down'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Thêm trục y thứ hai cho RSI
            fig.update_layout(
                yaxis2=dict(
                    showgrid=True
                )
            )
        elif selected_indicator_combination == 'Bollinger Bands + MACD':
            # Tạo subplots với 2 hàng: 1 hàng cho biểu đồ nến + Bollinger Bands, 1 hàng cho MACD
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,  # Dùng chung trục X
                row_heights=[0.7, 0.3],  # Tỷ lệ chiều cao của các hàng
                vertical_spacing=0.05,  # Khoảng cách giữa các hàng
                subplot_titles=["Candlestick with Bollinger Bands", "MACD"]
            )

            # Vẽ biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ),
                row=1, col=1
            )

            # Vẽ Bollinger Bands trên biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['bb_upper'],
                    mode='lines',
                    name='Bollinger Upper Band',
                    line=dict(color='blue', width=1, dash='dash'),
                    opacity=0.8
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['bb_middle'],
                    mode='lines',
                    name='Bollinger Middle Band',
                    line=dict(color='grey', width=1),
                    opacity=0.8
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['bb_lower'],
                    mode='lines',
                    name='Bollinger Lower Band',
                    line=dict(color='blue', width=1, dash='dash'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Vẽ MACD Line trên subplot thứ 2 (hàng 2)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['macd_line'],
                    mode='lines',
                    name='MACD Line',
                    line=dict(color='purple', width=2),
                    opacity=0.8
                ),
                row=2, col=1
            )

            # Vẽ Signal Line trên subplot thứ 2 (hàng 2)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['macd_signal'],
                    mode='lines',
                    name='Signal Line',
                    line=dict(color='red', width=2, dash='dot'),
                    opacity=0.8
                ),
                row=2, col=1
            )

            # Tín hiệu MUA
            buy_signal = (
                    (df['macd_line'] > df['macd_signal']) &  # MACD Line cắt lên Signal Line
                    (df['macd_line'].shift(1) <= df['macd_signal'].shift(1)) &  # Xác nhận cắt lên
                    (df['close'] <= df['bb_lower'])  # Giá nằm dưới dải dưới Bollinger Bands
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][buy_signal],
                    y=df['close'][buy_signal],
                    mode='markers',
                    name='Buy Signal (BB + MACD)',
                    marker=dict(color='blue', size=20, symbol='triangle-up'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Tín hiệu BÁN
            sell_signal = (
                    (df['macd_line'] < df['macd_signal']) &  # MACD Line cắt xuống Signal Line
                    (df['macd_line'].shift(1) >= df['macd_signal'].shift(1)) &  # Xác nhận cắt xuống
                    (df['close'] >= df['bb_upper'])  # Giá nằm trên dải trên Bollinger Bands
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'][sell_signal],
                    y=df['close'][sell_signal],
                    mode='markers',
                    name='Sell Signal (BB + MACD)',
                    marker=dict(color='orange', size=20, symbol='triangle-down'),
                    opacity=0.8
                ),
                row=1, col=1
            )

            # Thiết lập layout cho trục y thứ hai của MACD (hàng 2)
            fig.update_layout(
                yaxis2=dict(
                    showgrid=True
                )
            )
            # Vẽ biểu đồ nến (hàng 1)
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ),
                row=1, col=1
            )
            # Thiết lập layout cho trục y thứ hai của MACD (hàng 2)
            fig.update_layout(
                yaxis2=dict(
                    showgrid=True
                )
            )

            
        elif selected_indicator_combination == 'RSI + MACD':
            # Tạo subplots với 3 hàng: 1 hàng cho biểu đồ nến, 1 hàng cho RSI, 1 hàng cho MACD
            fig = make_subplots(
                rows=3,
                cols=1,
                shared_xaxes=True,  # Dùng chung trục X
                row_heights=[0.6, 0.2, 0.2],  # Tỷ lệ chiều cao của các hàng
                vertical_spacing=0.05,  # Khoảng cách giữa các hàng
                subplot_titles=('Candlestick Chart', 'RSI', 'MACD'),  # Tiêu đề cho mỗi subplot
                shared_yaxes=True  # Dùng chung trục Y
            )

            # Vẽ biểu đồ nến trong subplot chính (row 1)
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candlestick',
            ), row=1, col=1)

            # Vẽ RSI trong subplot 1 (row 2)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['rsi_14'],
                mode='lines',
                name='RSI (14)',
                line=dict(color='blue', width=2),
                opacity=0.8
            ), row=2, col=1)

            # Vùng quá mua (RSI > 70)
            fig.add_shape(
                type='rect',
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=70,
                y1=100,
                fillcolor='red',
                opacity=0.2,
                layer='below',
                line_width=0,
                yref='y2',
                row=2, col=1
            )

            # Vùng quá bán (RSI < 30)
            fig.add_shape(
                type='rect',
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=0,
                y1=30,
                fillcolor='green',
                opacity=0.2,
                layer='below',
                line_width=0,
                yref='y2',
                row=2, col=1
            )

            # Vẽ MACD trong subplot 2 (row 3)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['macd_line'],
                mode='lines',
                name='MACD Line',
                line=dict(color='green', width=2),
                opacity=0.8
            ), row=3, col=1)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['macd_signal'],
                mode='lines',
                name='Signal Line',
                line=dict(color='red', width=2, dash='dot'),
                opacity=0.8
            ), row=3, col=1)
            fig.add_trace(go.Bar(
                x=df['Date'],
                y=df['macd_histogram'],
                name='MACD Histogram',
                marker_color=df['macd_histogram'].apply(lambda x: 'green' if x > 0 else 'red'),
                opacity=0.6
            ), row=3, col=1)

            # Tín hiệu MUA
            buy_signal = (
                    (df['rsi_14'] < 30) &  # RSI trong vùng quá bán
                    (df['macd_line'] > df['macd_signal']) &  # Giao cắt tăng của MACD
                    (df['macd_line'].shift(1) <= df['macd_signal'].shift(1))  # MACD trước đó ở dưới Signal
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][buy_signal],
                y=df['close'][buy_signal],
                mode='markers',
                name='Buy Signal (RSI + MACD)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ), row=1, col=1)  # Vẽ trên biểu đồ nến chính

            # Tín hiệu BÁN
            sell_signal = (
                    (df['rsi_14'] > 70) &  # RSI trong vùng quá mua
                    (df['macd_line'] < df['macd_signal']) &  # Giao cắt giảm của MACD
                    (df['macd_line'].shift(1) >= df['macd_signal'].shift(1))  # MACD trước đó ở trên Signal
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][sell_signal],
                y=df['close'][sell_signal],
                mode='markers',
                name='Sell Signal (RSI + MACD)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ), row=1, col=1)  # Vẽ trên biểu đồ nến chính
    else:
        # Ví dụ: tích hợp Moving Averages nếu "MA" được chọn
        if 'MA' in selected_indicators:
            ma_pairs = {
                'sma_20': 'SMA 20',
                'sma_50': 'SMA 50',
                'sma_100': 'SMA 100',
                'sma_200': 'SMA 200',
                'ema_20': 'EMA 20',
                'ema_50': 'EMA 50',
                'ema_100': 'EMA 100',
                'ema_200': 'EMA 200'
            }
            if selected_ma:
                for short_ma, long_ma in ma_pairs:
                    # Kiểm tra nếu cả 2 MA được chọn
                    if short_ma in selected_ma and long_ma in selected_ma:
                        short_ma_series = df[short_ma]
                        long_ma_series = df[long_ma]

                        # Tín hiệu MUA: MA ngắn hạn cắt lên MA dài hạn
                        buy_signals = (short_ma_series > long_ma_series) & (
                                short_ma_series.shift(1) <= long_ma_series.shift(1))
                        fig.add_trace(go.Scatter(
                            x=df['Date'][buy_signals],
                            y=df['close'][buy_signals],
                            mode='markers',
                            name=f'Buy Signal ({short_ma} vs {long_ma})',
                            marker=dict(color='purple', size=20, symbol='triangle-up'),
                            opacity=0.8
                        ))

                        # Tín hiệu BÁN: MA ngắn hạn cắt xuống MA dài hạn
                        sell_signals = (short_ma_series < long_ma_series) & (
                                short_ma_series.shift(1) >= long_ma_series.shift(1))
                        fig.add_trace(go.Scatter(
                            x=df['Date'][sell_signals],
                            y=df['close'][sell_signals],
                            mode='markers',
                            name=f'Sell Signal ({short_ma} vs {long_ma})',
                            marker=dict(color='pink', size=20, symbol='triangle-down'),
                            opacity=0.8
                        ))

            # Vẽ các đường MA mà người dùng đã chọn
            ma_columns = {
                'sma_20': 'SMA 20',
                'sma_50': 'SMA 50',
                'sma_100': 'SMA 100',
                'sma_200': 'SMA 200',
                'ema_20': 'EMA 20',
                'ema_50': 'EMA 50',
                'ema_100': 'EMA 100',
                'ema_200': 'EMA 200'
            }

            # Vẽ từng đường MA được chọn và tính tín hiệu giao dịch nếu chỉ chọn 1 MA
            for ma_column, ma_label in ma_columns.items():
                if ma_column in selected_ma:
                    # Vẽ đường MA trên biểu đồ nến
                    fig.add_trace(go.Scatter(
                        x=df['Date'],
                        y=df[ma_column],
                        mode='lines',
                        name=ma_label,
                        line=dict(width=2, dash='solid'),
                        opacity=0.8
                    ))

                    # Nếu chỉ chọn 1 MA, thêm tín hiệu giao cắt với giá
                    buy_signals = (df['close'] > df[ma_column]) & (df['close'].shift(1) <= df[ma_column].shift(1))
                    sell_signals = (df['close'] < df[ma_column]) & (df['close'].shift(1) >= df[ma_column].shift(1))

                    # Vẽ tín hiệu MUA
                    fig.add_trace(go.Scatter(
                        x=df['Date'][buy_signals],
                        y=df['close'][buy_signals],
                        mode='markers',
                        name=f'Buy Signal ({ma_label})',
                        marker=dict(color='blue', size=20, symbol='triangle-up'),
                        opacity=0.8
                    ))

                    # Vẽ tín hiệu BÁN
                    fig.add_trace(go.Scatter(
                        x=df['Date'][sell_signals],
                        y=df['close'][sell_signals],
                        mode='markers',
                        name=f'Sell Signal ({ma_label})',
                        marker=dict(color='orange', size=20, symbol='triangle-down'),
                        opacity=0.8
                    ))
        elif 'MACD' in selected_indicators:
            # Tạo subplot cho MACD
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                vertical_spacing=0.02, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candlestick'
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['macd_line'],
                mode='lines',
                name='MACD Line',
                line=dict(color='blue', width=2),
                opacity=0.8
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['macd_signal'],
                mode='lines',
                name='Signal Line',
                line=dict(color='red', width=2, dash='dot'),
                opacity=0.8
            ), row=2, col=1)
            fig.add_trace(go.Bar(
                x=df['Date'],
                y=df['macd_histogram'],
                name='MACD Histogram',
                marker_color=df['macd_histogram'].apply(lambda x: 'green' if x >= 0 else 'red'),
                opacity=0.6
            ), row=2, col=1)
            # Tín hiệu giao dịch dựa trên MACD Line và Signal Line
            buy_signals = (df['macd_line'] > df['macd_signal']) & (
                    df['macd_line'].shift(1) <= df['macd_signal'].shift(1))
            sell_signals = (df['macd_line'] < df['macd_signal']) & (
                    df['macd_line'].shift(1) >= df['macd_signal'].shift(1))

            # Vẽ tín hiệu MUA
            fig.add_trace(go.Scatter(
                x=df['Date'][buy_signals],
                y=df['macd_line'][buy_signals],  # Chọn macd_line để hiện trên MACD chart
                mode='markers',
                name='Buy Signal (MACD)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ), row=2, col=1)

            # Vẽ tín hiệu BÁN
            fig.add_trace(go.Scatter(
                x=df['Date'][sell_signals],
                y=df['macd_line'][sell_signals],  # Chọn macd_line để hiện trên MACD chart
                mode='markers',
                name='Sell Signal (MACD)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ), row=2, col=1)

            # Zero Line Crossover
            zero_cross_up = (df['macd_line'] > 0) & (df['macd_line'].shift(1) <= 0)
            zero_cross_down = (df['macd_line'] < 0) & (df['macd_line'].shift(1) >= 0)

            # Tín hiệu Zero Line Crossover (Tăng giá)
            fig.add_trace(go.Scatter(
                x=df['Date'][zero_cross_up],
                y=df['macd_line'][zero_cross_up],
                mode='markers',
                name='Zero Line Up (MACD)',
                marker=dict(color='blue', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)

            # Tín hiệu Zero Line Crossover (Giảm giá)
            fig.add_trace(go.Scatter(
                x=df['Date'][zero_cross_down],
                y=df['macd_line'][zero_cross_down],
                mode='markers',
                name='Zero Line Down (MACD)',
                marker=dict(color='purple', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)
        elif 'PSAR' in selected_indicators:
            # Vẽ các điểm SAR trên biểu đồ nến
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['psar'],
                mode='markers',
                name='PSAR',
                marker=dict(color='purple', size=6, symbol='circle'),
                opacity=0.8
            ))

            # Tín hiệu giao dịch từ PSAR
            buy_signals = (df['psar'] < df['low']) & (df['psar'].shift(1) >= df['high'].shift(1))
            sell_signals = (df['psar'] > df['high']) & (df['psar'].shift(1) <= df['low'].shift(1))

            # Vẽ tín hiệu MUA
            fig.add_trace(go.Scatter(
                x=df['Date'][buy_signals],
                y=df['close'][buy_signals],
                mode='markers',
                name='Buy Signal (PSAR)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ))

            # Vẽ tín hiệu BÁN
            fig.add_trace(go.Scatter(
                x=df['Date'][sell_signals],
                y=df['close'][sell_signals],
                mode='markers',
                name='Sell Signal (PSAR)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ))
        # Tích hợp RSI nếu được chọn
        elif 'RSI' in selected_indicators and selected_rsi:
            # Tạo subplot với 2 hàng (1: Candlestick, 2: RSI)
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và RSI
            )

            # Vẽ biểu đồ nến
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candlestick'
            ), row=1, col=1)

            # Vẽ đường RSI trong hàng 2
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df[selected_rsi],
                mode='lines',
                name=f'{selected_rsi.upper()}',
                line=dict(color='blue', width=2),
                opacity=0.8
            ), row=2, col=1)  # Chỉ rõ vẽ ở hàng 2

            # Vùng Overbought (RSI > 70)
            fig.add_shape(
                type='rect',
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=70,
                y1=100,
                fillcolor='red',
                opacity=0.2,
                layer='below',
                line_width=0,
                row=2, col=1  # Chỉ rõ shape nằm ở hàng 2
            )

            # Vùng Oversold (RSI < 30)
            fig.add_shape(
                type='rect',
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=0,
                y1=30,
                fillcolor='green',
                opacity=0.2,
                layer='below',
                line_width=0,
                row=2, col=1  # Chỉ rõ shape nằm ở hàng 2
            )

            # Tín hiệu quá mua/quá bán
            overbought_signals = df[selected_rsi] > 70
            oversold_signals = df[selected_rsi] < 30

            # Tín hiệu MUA (quá bán)
            fig.add_trace(go.Scatter(
                x=df['Date'][oversold_signals],
                y=df[selected_rsi][oversold_signals],
                mode='markers',
                name='Buy Signal (RSI)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ), row=2, col=1)  # Vẽ tín hiệu MUA ở hàng 2

            # Tín hiệu BÁN (quá mua)
            fig.add_trace(go.Scatter(
                x=df['Date'][overbought_signals],
                y=df[selected_rsi][overbought_signals],
                mode='markers',
                name='Sell Signal (RSI)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ), row=2, col=1)  # Vẽ tín hiệu BÁN ở hàng 2

            # Cắt mức 50
            cross_up_50 = (df[selected_rsi] > 50) & (df[selected_rsi].shift(1) <= 50)
            cross_down_50 = (df[selected_rsi] < 50) & (df[selected_rsi].shift(1) >= 50)

            # Vẽ tín hiệu cắt mức 50
            fig.add_trace(go.Scatter(
                x=df['Date'][cross_up_50],
                y=df[selected_rsi][cross_up_50],
                mode='markers',
                name='RSI Cross Up 50',
                marker=dict(color='blue', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)  # Vẽ tín hiệu cắt lên ở hàng 2

            fig.add_trace(go.Scatter(
                x=df['Date'][cross_down_50],
                y=df[selected_rsi][cross_down_50],
                mode='markers',
                name='RSI Cross Down 50',
                marker=dict(color='purple', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)  # Vẽ tín hiệu cắt xuống ở hàng 2
        # Tích hợp CCI
        elif 'CCI' in selected_indicators and selected_cci:
            # Tạo subplot với 2 hàng (1: Candlestick, 2: CCI)
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và CCI
            )

            # Vẽ biểu đồ nến ở hàng đầu
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candlestick'
            ), row=1, col=1)

            # Vẽ đường CCI ở hàng thứ 2
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df[selected_cci],
                mode='lines',
                name=f'{selected_cci.upper()}',
                line=dict(color='purple', width=2),
                opacity=0.8
            ), row=2, col=1)

            # Vùng Overbought (> +100) ở hàng thứ 2
            fig.add_shape(
                type='rect',
                xref='x2',  # Tham chiếu đến x-axis của hàng thứ 2
                yref='y2',  # Tham chiếu đến y-axis của hàng thứ 2
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=100,
                y1=300,
                fillcolor='red',
                opacity=0.2,
                layer='below',
                line_width=0
            )

            # Vùng Oversold (< -100) ở hàng thứ 2
            fig.add_shape(
                type='rect',
                xref='x2',  # Tham chiếu đến x-axis của hàng thứ 2
                yref='y2',  # Tham chiếu đến y-axis của hàng thứ 2
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=-300,
                y1=-100,
                fillcolor='green',
                opacity=0.2,
                layer='below',
                line_width=0
            )

            # Tín hiệu giao dịch CCI
            buy_signals = df[selected_cci] < -100
            sell_signals = df[selected_cci] > 100

            # Vẽ tín hiệu MUA (quá bán) ở hàng thứ 2
            fig.add_trace(go.Scatter(
                x=df['Date'][buy_signals],
                y=df[selected_cci][buy_signals],
                mode='markers',
                name='Buy Signal (CCI)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ), row=2, col=1)

            # Vẽ tín hiệu BÁN (quá mua) ở hàng thứ 2
            fig.add_trace(go.Scatter(
                x=df['Date'][sell_signals],
                y=df[selected_cci][sell_signals],
                mode='markers',
                name='Sell Signal (CCI)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ), row=2, col=1)

            # Zero Line Crossover
            cross_up_zero = (df[selected_cci] > 0) & (df[selected_cci].shift(1) <= 0)
            cross_down_zero = (df[selected_cci] < 0) & (df[selected_cci].shift(1) >= 0)

            # Tín hiệu CCI cắt lên 0 ở hàng thứ 2
            fig.add_trace(go.Scatter(
                x=df['Date'][cross_up_zero],
                y=df[selected_cci][cross_up_zero],
                mode='markers',
                name='CCI Cross Up 0',
                marker=dict(color='blue', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)

            # Tín hiệu CCI cắt xuống 0 ở hàng thứ 2
            fig.add_trace(go.Scatter(
                x=df['Date'][cross_down_zero],
                y=df[selected_cci][cross_down_zero],
                mode='markers',
                name='CCI Cross Down 0',
                marker=dict(color='purple', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)

        # Tích hợp Bollinger Bands
        elif 'Bollinger Bands' in selected_indicators:
            # Vẽ Middle Band
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['bb_middle'],
                mode='lines',
                name='Middle Band',
                line=dict(color='blue', width=2),
                opacity=0.8
            ))

            # Vẽ Upper Band
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['bb_upper'],
                mode='lines',
                name='Upper Band',
                line=dict(color='red', width=2, dash='dot'),
                opacity=0.8
            ))

            # Vẽ Lower Band
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['bb_lower'],
                mode='lines',
                name='Lower Band',
                line=dict(color='green', width=2, dash='dot'),
                opacity=0.8
            ))

            # Tín hiệu giao dịch:
            # Quá mua: Giá chạm Upper Band
            overbought_signals = df['close'] >= df['bb_upper']
            fig.add_trace(go.Scatter(
                x=df['Date'][overbought_signals],
                y=df['close'][overbought_signals],
                mode='markers',
                name='Overbought (Sell Signal)',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ))

            # Quá bán: Giá chạm Lower Band
            oversold_signals = df['close'] <= df['bb_lower']
            fig.add_trace(go.Scatter(
                x=df['Date'][oversold_signals],
                y=df['close'][oversold_signals],
                mode='markers',
                name='Oversold (Buy Signal)',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ))

            # Breakout
            breakout_upper = df['high'] > df['bb_upper']
            breakout_lower = df['low'] < df['bb_lower']
            fig.add_trace(go.Scatter(
                x=df['Date'][breakout_upper],
                y=df['high'][breakout_upper],
                mode='markers',
                name='Breakout Above Upper Band',
                marker=dict(color='purple', size=10, symbol='circle'),
                opacity=0.8
            ))
            fig.add_trace(go.Scatter(
                x=df['Date'][breakout_lower],
                y=df['low'][breakout_lower],
                mode='markers',
                name='Breakout Below Lower Band',
                marker=dict(color='orange', size=10, symbol='circle'),
                opacity=0.8
            ))
        
        # Tích hợp OBV
        if 'OB' in selected_indicators:
            # Tạo subplot với 2 hàng (1: Candlestick, 2: OBV)
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và OBV
            )

            # Vẽ biểu đồ nến ở hàng đầu
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candlestick'
            ), row=1, col=1)

            # Vẽ đường OBV ở hàng thứ hai
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['obv'],
                mode='lines',
                name='OBV',
                line=dict(color='blue', width=2),
                opacity=0.8
            ), row=2, col=1)

            # Tín hiệu phân kỳ tăng (Bullish Divergence)
            bullish_divergence = (
                    (df['close'] < df['close'].shift(1)) & (df['obv'] > df['obv'].shift(1))
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][bullish_divergence],
                y=df['obv'][bullish_divergence],
                mode='markers',
                name='Bullish Divergence',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ), row=2, col=1)

            # Tín hiệu phân kỳ giảm (Bearish Divergence)
            bearish_divergence = (
                    (df['close'] > df['close'].shift(1)) & (df['obv'] < df['obv'].shift(1))
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][bearish_divergence],
                y=df['obv'][bearish_divergence],
                mode='markers',
                name='Bearish Divergence',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ), row=2, col=1)

            # Tín hiệu breakout (OBV tăng cùng giá)
            breakout_signal = (
                    (df['obv'] > df['obv'].shift(1)) & (df['close'] > df['close'].shift(1))
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][breakout_signal],
                y=df['obv'][breakout_signal],
                mode='markers',
                name='Breakout Signal',
                marker=dict(color='purple', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)

        # Tích hợp MFI
        if 'MFI' in selected_indicators:
            # Tạo subplot với 2 hàng (1: Candlestick, 2: MFI)
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và MFI
            )

            # Vẽ biểu đồ nến ở hàng đầu
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candlestick'
            ), row=1, col=1)

            # Vẽ đường MFI ở hàng thứ hai
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['mfi'],
                mode='lines',
                name='MFI',
                line=dict(color='purple', width=2),
                opacity=0.8
            ), row=2, col=1)

            # Vùng Overbought (MFI > 80) ở hàng thứ hai
            fig.add_shape(
                type='rect',
                xref='x2',  # Tham chiếu đến x-axis của hàng thứ 2
                yref='y2',  # Tham chiếu đến y-axis của hàng thứ 2
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=80,
                y1=100,
                fillcolor='red',
                opacity=0.2,
                layer='below',
                line_width=0
            )

            # Vùng Oversold (MFI < 20) ở hàng thứ hai
            fig.add_shape(
                type='rect',
                xref='x2',  # Tham chiếu đến x-axis của hàng thứ 2
                yref='y2',  # Tham chiếu đến y-axis của hàng thứ 2
                x0=df['Date'].min(),
                x1=df['Date'].max(),
                y0=0,
                y1=20,
                fillcolor='green',
                opacity=0.2,
                layer='below',
                line_width=0
            )

            # Tín hiệu phân kỳ tăng (Bullish Divergence)
            bullish_divergence = (
                    (df['close'] < df['close'].shift(1)) & (df['mfi'] > df['mfi'].shift(1))
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][bullish_divergence],
                y=df['mfi'][bullish_divergence],
                mode='markers',
                name='Bullish Divergence',
                marker=dict(color='blue', size=20, symbol='triangle-up'),
                opacity=0.8
            ), row=2, col=1)

            # Tín hiệu phân kỳ giảm (Bearish Divergence)
            bearish_divergence = (
                    (df['close'] > df['close'].shift(1)) & (df['mfi'] < df['mfi'].shift(1))
            )
            fig.add_trace(go.Scatter(
                x=df['Date'][bearish_divergence],
                y=df['mfi'][bearish_divergence],
                mode='markers',
                name='Bearish Divergence',
                marker=dict(color='orange', size=20, symbol='triangle-down'),
                opacity=0.8
            ), row=2, col=1)

            # Sự vượt qua ngưỡng 50
            cross_up_50 = (df['mfi'] > 50) & (df['mfi'].shift(1) <= 50)
            cross_down_50 = (df['mfi'] < 50) & (df['mfi'].shift(1) >= 50)

            fig.add_trace(go.Scatter(
                x=df['Date'][cross_up_50],
                y=df['mfi'][cross_up_50],
                mode='markers',
                name='MFI Cross Up 50',
                marker=dict(color='blue', size=10, symbol='circle'),
                opacity=0.8
            ), row=2, col=1)
    # Cập nhật layout
    title_text = f"Biểu đồ {company} - "
    if selected_indicator_combination:
        title_text += selected_indicator_combination
    elif selected_indicators:
        title_text += ", ".join(selected_indicators)
    else:
        title_text += "Price"
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        title=title_text,
        xaxis_title="Date",
        yaxis_title="Price / Indicators",
        template='plotly_dark',
        plot_bgcolor='rgb(0,0,0)',
        showlegend=True
    )
    return fig


# Hàm đọc và xử lý dữ liệu
def load_data_TA():
    df = pd.read_csv(FILE_PATH1, dtype=str, low_memory=False, encoding="utf-8")
    df_long = df.melt(id_vars=["Name", "Code"], var_name="Date", value_name="Close_Price")
    invalid_dates = ["RIC", "Start Date", "Exchange", "Sector", "Activity"]
    df_long = df_long[~df_long["Date"].isin(invalid_dates)]
    df_long["Date"] = df_long["Date"].astype(str).str.split().str[0]
    df_long["Date"] = pd.to_datetime(df_long["Date"], format="%Y-%m-%d", errors="coerce")
    df_long["Close_Price"] = pd.to_numeric(df_long["Close_Price"], errors="coerce")
    df_long = df_long.dropna(subset=["Date", "Close_Price"])
    df_long = df_long.sort_values(by=["Code", "Date"])
    return df_long


# Hàm tính MA
def calculate_moving_averages(df_long, ma_periods):
    for ma in ma_periods:
        df_long[f"MA{ma}"] = df_long.groupby("Code")["Close_Price"].transform(
            lambda x: x.rolling(window=ma, min_periods=1).mean())
    return df_long


# Hàm tính số lượng cổ phiếu trên MA
def count_stocks_above_ma(df_long, ma_periods):
    above_ma_counts = df_long.copy()
    for ma in ma_periods:
        above_ma_counts[f"Above_MA{ma}"] = above_ma_counts["Close_Price"] > above_ma_counts[f"MA{ma}"]
    return above_ma_counts.groupby("Date")[[f"Above_MA{ma}" for ma in ma_periods]].sum()


# Hàm tính số lượng MA đang tăng
def count_increasing_ma(df_long, ma_periods):
    df_ma_increase = df_long.copy()
    for ma in ma_periods:
        df_ma_increase[f"Increase_MA{ma}"] = df_ma_increase[f"MA{ma}"].diff() > 0
    return df_ma_increase.groupby("Date")[[f"Increase_MA{ma}" for ma in ma_periods]].sum()

    buf = BytesIO()
    with PdfPages(buf) as pdf:
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.8, "Foreign Investor Trading Report", fontsize=14, ha='center')
        plt.text(0.5, 0.6, f"Date Extracted: {date.strftime('%d/%m/%Y')}", fontsize=12, ha='center')
        plt.axis("off")
        pdf.savefig()
        plt.close()

        fig_bytes = pio.to_image(fig_plot, format="png")
        img = plt.imread(BytesIO(fig_bytes))
        plt.figure(figsize=(10, 6))
        plt.imshow(img)
        plt.axis("off")
        pdf.savefig()
        plt.close()
    buf.seek(0)
    return buf

def createFigureTab2(filtered_data, ticker_selected):
    # Lọc bỏ ngày không có dữ liệu và sắp xếp lại dữ liệu để không có khoảng trống trên biểu đồ
    filtered_data = filtered_data.dropna(subset=["Net.F_Val", "Close"]).sort_values(by="Date").reset_index(
        drop=True)

    # Tạo dữ liệu riêng cho mua ròng và bán ròng
    buy_data = filtered_data[filtered_data["Net.F_Val"] >= 0]
    sell_data = filtered_data[filtered_data["Net.F_Val"] < 0]

    # Vẽ biểu đồ cột giá trị ròng và đường giá đóng cửa
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=buy_data["Date"],
        y=buy_data["Net.F_Val"],
        name="Mua ròng",
        marker_color="#007bff",
        opacity=0.9,
        yaxis='y1'
    ))
    fig.add_trace(go.Bar(
        x=sell_data["Date"],
        y=sell_data["Net.F_Val"],
        name="Bán ròng",
        marker_color="#dc3545",
        opacity=0.9,
        yaxis='y1'
    ))

    # Thêm đường giá đóng cửa trên trục y thứ hai
    fig.add_trace(go.Scatter(
        x=filtered_data["Date"],
        y=filtered_data["Close"],
        mode='lines+markers',
        name="Giá đóng cửa",
        line=dict(color='#ffcc00', width=2),
        marker=dict(size=4),
        yaxis='y2'
    ))

    # Cập nhật layout với nền tối để nổi bật biểu đồ
    fig.update_layout(
        title=f"Dòng tiền và Giá đóng cửa - {ticker_selected}",
        xaxis_title="Thời gian",
        xaxis=dict(
            tickmode='array',
            tickvals=filtered_data["Date"].iloc[::max(len(filtered_data) // 10, 1)],
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title="Dòng tiền (Tỷ VND)",
            side='left',
            showgrid=False
        ),
        yaxis2=dict(
            title="Giá đóng cửa",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.15
        ),
        template="plotly_dark",
        width=1200,
        height=600
    )

    return fig

# Phục vụ cho tab 2. Tổng quan theo ngành
file_paths = {
    "./Data/CleanedFT/FT1921_cleaned.csv",
    "./Data/CleanedFT/FT2123_cleaned.csv",
    "./Data/CleanedFT/FT2325_cleaned.csv"
}

# Tải dữ liệu
dataframesTab2 = load_data_by_file(file_paths)

# 📌 Gọi hàm vẽ biểu đồ
df_price_tab3, df_volume_tab3, date_columns_tab3 = load_data_tab3()
# ============================================ MAIN ========================================================
if selected == "1. Tổng quan thị trường":
    st.markdown("<h1>📊 Tổng quan thị trường</h1>", unsafe_allow_html=True)
    st.markdown("<h6>Tổng quan về vốn hóa TTCK Việt Nam</h6>", unsafe_allow_html=True)

    selected_date = st.selectbox("Chọn ngày để hiển thị Treemap", DATE_COLUMNS[::-1])
    st.plotly_chart(plot_sector_treemap(selected_date))
    st.plotly_chart(plot_bubble_chart(selected_date))

    # Get the stock code input from the user
    stock_codes = MERGED_DF["Code"].dropna().unique()
    stock_code = st.selectbox("Chọn mã cổ phiếu để xem giá trị thị trường", options=stock_codes)
    if stock_code:
        fig_stock = plot_stock_price(MERGED_DF, stock_code)
        if fig_stock:
            st.pyplot(fig_stock)
        # Pass the stock code to generate_pdf function when button is clicked
    if st.button("Xuất báo cáo PDF"):
        generate_pdf_by_stock_code(stock_code)  # Pass stock_code to generate_pdf

elif selected == "2. Tổng quan theo ngành":
    st.markdown("<h1>📊 Tổng quan theo ngành</h1>", unsafe_allow_html=True)
    st.markdown("<h6>Dòng tiền và giá đóng cửa</h6>", unsafe_allow_html=True)

    data = dataframesTab2.copy()

    # Kiểm tra nếu dữ liệu rỗng
    if data.empty:
        st.warning("Không có dữ liệu để hiển thị.")
    else:
        # Chọn mã cổ phiếu
        tickers = sorted(data["Ticker"].dropna().unique())
        ticker_selected = st.selectbox("Chọn mã cổ phiếu", tickers)

        # Chọn khoảng thời gian
        min_date = data["Date"].min()
        max_date = data["Date"].max()
        if pd.isna(min_date) or pd.isna(max_date):
            st.warning("Dữ liệu không có ngày hợp lệ. Vui lòng kiểm tra lại.")
            min_date, max_date = pd.to_datetime("2025-01-01"), pd.to_datetime("2025-02-28")
        start_date = st.date_input("Chọn ngày bắt đầu", min_date)
        end_date = st.date_input("Chọn ngày kết thúc", max_date)

        # Lọc dữ liệu theo mã cổ phiếu và thời gian
        filtered_data = data[(data["Ticker"] == ticker_selected) & (data["Date"] >= pd.to_datetime(start_date)) & (
                data["Date"] <= pd.to_datetime(end_date))].copy()

        # Kiểm tra nếu không có dữ liệu sau khi lọc
        if filtered_data.empty:
            st.warning("Không có dữ liệu trong khoảng thời gian đã chọn.")
        else:
            fig = createFigureTab2(filtered_data, ticker_selected)
            st.plotly_chart(fig)
            
            if st.button("📄 Export PDF"):
                pdf_output = export_pdf_combined(fig, datetime.now())
                st.download_button(
                    label="Tổng quan theo ngành",
                    data=pdf_output,
                    file_name=f"Tong_quan_theo_nganh_{ticker_selected}.pdf",
                    mime="application/pdf"
                )

elif selected == "3. Phân tích kỹ thuật":
    st.markdown("<h1>📊Phân tích kỹ thuật</h1>", unsafe_allow_html=True)
 
    # if subpage == "Chi tiết cổ phiếu":
    st.title("📈 Phân tích Chi Tiết Mã Cổ Phiếu")
    if df_price_tab3 is None or df_volume_tab3 is None:
        st.stop()

    # Chuyển đổi date_columns_tab3 sang datetime
    date_columns_dt_tab3 = pd.to_datetime(date_columns_tab3, format="%Y-%m-%d", errors="coerce").dropna().sort_values()
    # Lấy ngày kết thúc
    selected_date = select_date(date_columns_dt_tab3)
    # Hiển thị bảng snapshot chỉ báo
    df_snapshot_tab3 = calculate_indicators_snapshot(df_price_tab3, df_volume_tab3, selected_date)
    if df_snapshot_tab3 is not None:
        st.write("🔍 **Bảng chỉ báo kỹ thuật (snapshot)**")
        st.dataframe(df_snapshot_tab3)
        # Dropdown chọn mã cổ phiếu
        stock_list = df_snapshot_tab3['Code'].unique().tolist()

        selected_stock_tab3 = st.selectbox("Chọn mã cổ phiếu", stock_list)
        if not selected_stock_tab3:
            st.warning("⚠ Vui lòng chọn ít nhất một mã cổ phiếu!")
            st.stop()
        # Dropdown chọn chỉ báo kỹ thuật
        indicators = [
            "SMA", "EMA", "MACD", "PSAR", "RSI",
            "CCI", "Bollinger Bands", "OB", "MFI"
        ]
        selected_indicators = st.multiselect("Chọn chỉ báo kỹ thuật", indicators)
        # Nếu chọn MA thì cho phép chọn các đường MA cụ thể
        selected_ma = []
        if "SMA" in selected_indicators or "EMA" in selected_indicators or "MA" in selected_indicators:
            ma_options = ["sma_20", "sma_50", "sma_100", "sma_200", "ema_20", "ema_50", "ema_100", "ema_200"]
            selected_ma = st.multiselect("Chọn đường trung bình động", ma_options)
        selected_rsi = None
        if "RSI" in selected_indicators:
            rsi_options = ["rsi_9", "rsi_14", "rsi_21"]
            selected_rsi = st.selectbox("Chọn RSI", rsi_options)
        selected_cci = None
        if "CCI" in selected_indicators:
            cci_options = ["cci_10", "cci_20", "cci_30"]
            selected_cci = st.selectbox("Chọn CCI", cci_options)
        # Dropdown chọn tổ hợp chỉ báo
        indicator_combinations = [
            "PSAR + SMA", "PSAR + EMA", "PSAR + RSI", "PSAR + MACD",
            "Bollinger Bands + RSI", "Bollinger Bands + MACD",
            "RSI + MACD"
        ]
        selected_combination = st.selectbox("Chọn tổ hợp chỉ báo", [None] + indicator_combinations)
        # Chọn khoảng thời gian (tính theo chuỗi thời gian từ dữ liệu Excel)
        time_range_tab3 = select_time_period_tab3()
        # Xác định ngày bắt đầu dựa trên khoảng thời gian được chọn
        time_ranges_tab3 = {
            "1 tuần": selected_date - pd.DateOffset(weeks=1),
            "1 tháng": selected_date - pd.DateOffset(months=1),
            "3 tháng": selected_date - pd.DateOffset(months=3),
            "6 tháng": selected_date - pd.DateOffset(months=6),
            "1 năm": selected_date - pd.DateOffset(years=1),
            "2 năm": selected_date - pd.DateOffset(years=2),
            "3 năm": selected_date - pd.DateOffset(years=3),
            "Toàn bộ": date_columns_dt_tab3.min(),
        }
        start_date = time_ranges_tab3.get(time_range_tab3, date_columns_dt_tab3.min())
        if start_date < date_columns_dt_tab3.min():
            st.warning(f"⚠ Không có đủ dữ liệu để tính {time_range_tab3}! Đang chọn ngày sớm nhất có thể.")
            start_date = date_columns_dt_tab3.min()

        # Lấy chuỗi thời gian cho mã được chọn (sử dụng dữ liệu từ file Excel)
        df_ts = get_stock_timeseries(selected_stock_tab3, df_price_tab3, df_volume_tab3, date_columns_dt_tab3, start_date,
                                        selected_date)
        
        if df_ts is None or df_ts.empty:
            st.error("⚠ Không đủ dữ liệu thời gian cho mã được chọn.")
            st.stop()
        # Tính toán các chỉ báo trên chuỗi thời gian
        df_ts = compute_timeseries_indicators(df_ts)

        # Xây dựng biểu đồ dựa trên các lựa chọn
        fig = update_chart(df_ts, selected_stock_tab3, selected_indicators, selected_ma, selected_rsi, selected_cci,
                            selected_combination)
        st.plotly_chart(fig, use_container_width=True)

    if "pdf_exported" not in st.session_state:
        st.session_state["pdf_exported"] = False

    if st.button("📄 Export PDF") and not st.session_state["pdf_exported"]:
        st.session_state["pdf_exported"] = True
        pdf_output = export_pdf_combined(fig, datetime.now())
        st.download_button(
            label="Download PDF",
            data=pdf_output,
            file_name=f"Phân tích kỹ thuật {selected_stock_tab3}.pdf",
            mime="application/pdf"
        )

elif selected == "4. Báo cáo tài chính":
    st.title("📝 Báo cáo tài chính")

    stock_codes = MERGED_DF["Code"].dropna().unique()
    stock_code = st.selectbox("Chọn mã cổ phiếu", options=stock_codes)

    # Nút xuất báo cáo PDF
    if st.button("📄 Xuất báo cáo PDF"):
        with st.spinner("⏳ Đang tạo biểu đồ..."):
            draw_chart(stock_code)
        with st.spinner("⏳ Đang tạo báo cáo PDF..."):
            generate_pdf(stock_code)
        st.success(f"✅ Báo cáo PDF cho {stock_code} đã được tạo thành công!")
        
elif selected == "0. PHÂN TÍCH TỔNG HỢP":
    st.title("🔍 Phân tích Tổng Hợp - Cung cấp góc nhìn 360 độ thể thao")
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get the stock code input from the user
        stock_codes = MERGED_DF["Code"].dropna().unique()
        stock_code = st.selectbox("Chọn mã cổ phiếu", options=stock_codes)
        
        # Technical Analysis Filters
        st.subheader("1. Bộ lọc - Tổng quan thị trường")
        st.markdown("<h6>Đầu vào bao gồm: Mã cổ phiếu</h6>", unsafe_allow_html=True)

        # Financial Report Filters
        st.subheader("2. Bộ lọc - Tổng quan theo ngành")
        st.markdown("<h6>Đầu vào bao gồm: Mã cổ phiếu + ngày bắt đầu & kết thúc.</h6>", unsafe_allow_html=True)

        dataTab2 = dataframesTab2.copy()

        min_date = dataTab2["Date"].min()
        max_date = dataTab2["Date"].max()

        start_date = st.date_input("Chọn ngày bắt đầu", min_date)
        end_date = st.date_input("Chọn ngày kết thúc", max_date)
        
        filtered_data = dataTab2[(dataTab2["Ticker"] == stock_code) & (dataTab2["Date"] >= pd.to_datetime(start_date)) & (
            dataTab2["Date"] <= pd.to_datetime(end_date))].copy()

        figTab2 = createFigureTab2(filtered_data, stock_code)
        
        if st.button("Xuất Báo Cáo Tổng Hợp"):
            pdf_output = export_pdf_combined(figTab2, datetime.now())
            st.download_button(
                label="Tổng quan theo ngành",
                data=pdf_output,
                file_name=f"Tong_quan_theo_nganh_{stock_code}.pdf",
                mime="application/pdf"
            )

        # Industry Overview Filters
        st.subheader("3. Bộ lọc - Phân tích kỹ thuật")
        st.markdown("<h6>Đầu vào bao gồm: Mã cổ phiếu + chỉ báo kĩ thuật + khoảng thời gian.</h6>", unsafe_allow_html=True)
        
        if not stock_code:
            st.warning("⚠ Vui lòng chọn mã cổ phiếu!")
            st.stop()
        # Dropdown chọn chỉ báo kỹ thuật
        indicators = [
            "SMA", "EMA", "MACD", "PSAR", "RSI",
            "CCI", "Bollinger Bands", "OB", "MFI"
        ]
        selected_indicators = st.multiselect("Chọn chỉ báo kỹ thuật", indicators)
        # Nếu chọn MA thì cho phép chọn các đường MA cụ thể
        selected_ma = []
        if "SMA" in selected_indicators or "EMA" in selected_indicators or "MA" in selected_indicators:
            ma_options = ["sma_20", "sma_50", "sma_100", "sma_200", "ema_20", "ema_50", "ema_100", "ema_200"]
            selected_ma = st.multiselect("Chọn đường trung bình động", ma_options)
        selected_rsi = None
        if "RSI" in selected_indicators:
            rsi_options = ["rsi_9", "rsi_14", "rsi_21"]
            selected_rsi = st.selectbox("Chọn RSI", rsi_options)
        selected_cci = None
        if "CCI" in selected_indicators:
            cci_options = ["cci_10", "cci_20", "cci_30"]
            selected_cci = st.selectbox("Chọn CCI", cci_options)
        # Dropdown chọn tổ hợp chỉ báo
        indicator_combinations = [
            "PSAR + SMA", "PSAR + EMA", "PSAR + RSI", "PSAR + MACD",
            "Bollinger Bands + RSI", "Bollinger Bands + MACD",
            "RSI + MACD"
        ]
        selected_combination = st.selectbox("Chọn tổ hợp chỉ báo", [None] + indicator_combinations)
        # Chọn khoảng thời gian (tính theo chuỗi thời gian từ dữ liệu Excel)
        time_range_tab3 = select_time_period_tab3()
        # Xác định ngày bắt đầu dựa trên khoảng thời gian được chọn

        # Chuyển đổi date_columns_tab3 sang datetime
        date_columns_dt_tab3 = pd.to_datetime(date_columns_tab3, format="%Y-%m-%d", errors="coerce").dropna().sort_values()
        # Lấy ngày kết thúc
        selected_date = select_date(date_columns_dt_tab3)

        time_ranges_tab3 = {
            "1 tuần": selected_date - pd.DateOffset(weeks=1),
            "1 tháng": selected_date - pd.DateOffset(months=1),
            "3 tháng": selected_date - pd.DateOffset(months=3),
            "6 tháng": selected_date - pd.DateOffset(months=6),
            "1 năm": selected_date - pd.DateOffset(years=1),
            "2 năm": selected_date - pd.DateOffset(years=2),
            "3 năm": selected_date - pd.DateOffset(years=3),
            "Toàn bộ": date_columns_dt_tab3.min(),
        }
        start_date = time_ranges_tab3.get(time_range_tab3, date_columns_dt_tab3.min())
        if start_date < date_columns_dt_tab3.min():
            st.warning(f"⚠ Không có đủ dữ liệu để tính {time_range_tab3}! Đang chọn ngày sớm nhất có thể.")
            start_date = date_columns_dt_tab3.min()

        # Lấy chuỗi thời gian cho mã được chọn (sử dụng dữ liệu từ file Excel)
        df_ts = get_stock_timeseries(stock_code, df_price_tab3, df_volume_tab3, date_columns_dt_tab3, start_date,
                                        selected_date)
        
        if df_ts is None or df_ts.empty:
            st.error("⚠ Không đủ dữ liệu thời gian cho mã được chọn.")
            st.stop()
        # Tính toán các chỉ báo trên chuỗi thời gian
        df_ts = compute_timeseries_indicators(df_ts)

        # Xây dựng biểu đồ dựa trên các lựa chọn
        fig = update_chart(df_ts, stock_code, selected_indicators, selected_ma, selected_rsi, selected_cci, selected_combination)
        
        if st.button("📄 Export PDF"):
            pdf_output = export_pdf_combined(fig, datetime.now())
            st.download_button(
                label="Download PDF",
                data=pdf_output,
                file_name=f"Phân tích kỹ thuật {stock_code}.pdf",
                mime="application/pdf"
            )


        # Market Overview Filters
        st.subheader("4. Báo cáo tài chính")
        st.markdown("<h6>Đầu vào bao gồm: Mã cổ phiếu</h6>", unsafe_allow_html=True)
    
    with col2:
        st.subheader("📄 Xuất Báo Cáo Tổng Hợp")
        if st.button("Tạo Báo Cáo PDF"):
            with st.spinner("⏳ Đang tạo báo cáo tổng hợp..."):
                # Create a comprehensive PDF report
                def generate_comprehensive_pdf():
                    pdf = FPDF()
                    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                    pdf.set_font("DejaVu", size=12)
                    
                    # Title Page
                    pdf.add_page()
                    pdf.set_font("DejaVu", size=24)
                    pdf.cell(200, 40, "Báo Cáo Phân Tích Tổng Hợp", ln=True, align='C')
                    pdf.set_font("DejaVu", size=12)
                    pdf.cell(200, 10, f"Ngày tạo: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
                    
                    # Technical Analysis Section
                    pdf.add_page()
                    pdf.set_font("DejaVu", size=16)
                    pdf.cell(200, 20, "1. Phân tích Kỹ thuật", ln=True)
                    if selected_indicators:
                        fig_technical = update_chart(df_ts, stock_code, selected_indicators, 
                                                   selected_ma, selected_rsi, selected_cci, None)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                            fig_technical.write_image(temp_img.name)
                            pdf.image(temp_img.name, x=10, w=190)
                    
                    # Financial Report Section
                    pdf.add_page()
                    pdf.cell(200, 20, "2. Báo cáo Tài chính", ln=True)
                    if stock_code:
                        transposed_df = process_financial_data(stock_code)
                        # Add financial data visualization
                        
                    # Industry Overview Section
                    pdf.add_page()
                    pdf.cell(200, 20, "3. Tổng quan Ngành", ln=True)
                    if selected_date:
                        fig_industry = plot_sector_treemap(selected_date)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                            fig_industry.write_image(temp_img.name)
                            pdf.image(temp_img.name, x=10, w=190)
                    
                    # Market Overview Section
                    pdf.add_page()
                    pdf.cell(200, 20, "4. Tổng quan Thị trường", ln=True)
                    # Add market overview visualization
                    
                    return pdf
                
                # Generate and save the PDF
                pdf = generate_comprehensive_pdf()
                pdf_path = "comprehensive_report.pdf"
                pdf.output(pdf_path)
                
                # Provide download button
                with open(pdf_path, "rb") as file:
                    st.download_button(
                        "📥 Tải xuống Báo cáo Tổng hợp",
                        data=file,
                        file_name="comprehensive_report.pdf",
                        mime="application/pdf"
                    )
                st.success("✅ Báo cáo tổng hợp đã được tạo thành công!")
# ============================== TỔNG HỢP - END ===============================