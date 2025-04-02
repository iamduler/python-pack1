import plotly.express as px
import os
import datetime as dt
import streamlit as st
from fpdf import FPDF
from dotenv import load_dotenv
import requests
import tempfile
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from caculate import calculate_financial_ratios
from drawchart import draw_chart
import matplotlib.pyplot as plt

# Chuyển đổi đơn vị
def convert_units(df, factor, start_col):
    try:
        start_idx = df.columns.get_loc(start_col) + 1
        numeric_cols = df.columns[start_idx:]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce') / factor
    except Exception as e:
        print(f"⚠️ Lỗi khi chuyển đổi đơn vị: {e}")
    return df

# Chuẩn hóa tên cột
def standardize_columns(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace("\n", " ").str.upper()
    return df

# Gộp dữ liệu theo mã hoặc tên công ty
def merge_balance_sheets(dfs, search_term):
    data = []
    dfs = [standardize_columns(df) for df in dfs]
    search_term = search_term.upper().strip()

    for year, df in zip(range(2020, 2025), dfs):
        if 'MÃ' not in df.columns or 'TÊN CÔNG TY' not in df.columns:
            print(f"❌ Thiếu cột 'MÃ' hoặc 'TÊN CÔNG TY' trong file năm {year}")
            continue

        # Chuẩn hóa dữ liệu để tránh lỗi khoảng trắng hoặc phân biệt chữ hoa/thường
        df['MÃ'] = df['MÃ'].astype(str).str.strip().str.upper()
        df['TÊN CÔNG TY'] = df['TÊN CÔNG TY'].astype(str).str.strip().str.upper()

        # Phân biệt tìm kiếm theo mã hoặc tên công ty
        if len(search_term) <= 3:  # Giả định mã cổ phiếu thường ngắn (ví dụ 3-5 ký tự)
            stock_data = df[df['MÃ'] == search_term]  # Tìm chính xác theo mã
        else:
            stock_data = df[df['TÊN CÔNG TY'].str.contains(search_term, case=False, na=False)]  # Tìm theo tên

        if not stock_data.empty:
            print(f"✅ Tìm thấy dữ liệu cho {search_term} năm {year}")
            data.append(stock_data)

    if data:
        return pd.concat(data, ignore_index=True)
    else:
        print(f"❌ Không tìm thấy dữ liệu cho '{search_term}'")
        return pd.DataFrame()


# Xử lý dữ liệu tài chính
def process_financial_data(search_term):
    try:
        # Đọc dữ liệu từ các file Excel
        file_names = [f"{year}-Vietnam.xlsx" for year in range(2020, 2025)]
        dfs = [pd.read_excel(file, engine="openpyxl") for file in file_names]

        # Chuẩn hóa tên cột
        for df, year in zip(dfs, range(2020, 2025)):
            df.columns = df.columns.str.replace(f"Năm: {year}", "", regex=True).str.strip()
            df.columns = df.columns.str.replace(r"Đơn vị: (Tỷ|Triệu) VND", "", regex=True).str.strip()
            df.columns = df.columns.str.replace(r"\bHợp nhất\b", "", regex=True).str.strip()
            df.columns = df.columns.str.replace(r"\bQuý: Hàng năm\b", "", regex=True).str.strip()

        # Xóa các cột không cần thiết
        for df in dfs:
            df.drop(columns=[col for col in df.columns if "TM" in col], inplace=True, errors='ignore')

        # Xác định tên cột tham chiếu
        start_column = "Trạng thái kiểm toán"
        start_column_cleaned = start_column.replace("Hợp nhất", "").replace("Hàng năm", "").strip()

        # Chuyển đổi đơn vị (3 năm đầu)
        for i in range(3):
            dfs[i] = convert_units(dfs[i], 1e9, start_column_cleaned)

        # Gộp dữ liệu
        merged_df = merge_balance_sheets(dfs, search_term)
        if merged_df.empty:
            return pd.DataFrame()

        # Xóa cột không mong muốn
        merged_df = merged_df.loc[:, ~merged_df.columns.str.contains("CURRENT RATIO", case=False, na=False)]

        # Chuyển đổi DataFrame từ 5 hàng × N cột thành N hàng × 5 cột
        transposed_df = merged_df.T
        transposed_df.reset_index(inplace=True)

        # Xử lý cột dư thừa
        expected_years = [str(year) for year in range(2020, 2025)]
        valid_columns = ["Chỉ tiêu"] + expected_years

        if len(transposed_df.columns) != len(valid_columns):
            print(f"⚠️ Phát hiện số cột không khớp. Đang điều chỉnh...")
            transposed_df = transposed_df.iloc[:, :len(valid_columns)]

        # Gán lại tên cột
        transposed_df.columns = valid_columns
        transposed_df.fillna(0, inplace=True)

        print(f"✅ Dữ liệu sau khi điều chỉnh: {transposed_df.shape[1]} cột")
        return transposed_df

    except Exception as e:
        print(f"🛑 Lỗi trong quá trình xử lý dữ liệu: {e}")
        return pd.DataFrame()