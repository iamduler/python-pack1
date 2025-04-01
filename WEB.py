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
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from fpdf import FPDF
from io import BytesIO
import tempfile
import plotly.io as pio
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

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
def load_data(file_path):
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
        options=["Thông tin giao dịch", "Tổng quan theo ngành", "Tổng quan thị trường", "Xu hướng thị trường"],
        icons=["bar-chart", "database", "clipboard-data", "book"],
        default_index=0,
        styles={"container": {"background-color": "black", "border-radius": "0px", "box-shadow": "none",
                              "padding": "0px"},
                "nav-link": {"font-size": "16px", "font-weight": "normal", "color": "white", "text-align": "left",
                             "padding": "10px"},
                "nav-link-selected": {"background-color": "#B0BEC5", "font-weight": "bold", "color": "Black",
                                      "border-radius": "5px"}})

if selected == "Thông tin giao dịch":
    # ----------------------SECTION 1 ------------------#
    st.markdown("<h1>Phân loại theo Nhà Đầu Tư - Ngành chuyên sâu </h1>", unsafe_allow_html=True)

    df = load_data("E:\GOI1\MSSV_CHAN_GOI1_GROUP1\MSSV_CHAN_GOI1_GROUP1\Data\output.csv")

    type_options = ['khớp_ròng', 'thỏa_thuận_ròng']
    investor_options = ['cá_nhân', 'tổ_chức_trong_nước', 'tự_doanh', 'nước_ngoài']
    with st.expander('🔎 **Bộ lọc**', expanded=True):
        with st.container():
            st.markdown("""
            <style>
                div[data-testid="stExpander"] {
                    background-color: #DDEBF7 !important;
                    border-radius: 10px;
                }
            </style>
            """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            type_selected = st.selectbox("Loại giao dịch", type_options,
                                         format_func=lambda x: x.replace("_", " ").title())
        with col2:
            investor_selected = st.selectbox("Nhà đầu tư", investor_options,
                                             format_func=lambda x: x.replace("_", " ").title())
        with col3:
            start_date = st.date_input("Từ ngày", df['ngày'].min())
        with col4:
            end_date = st.date_input("Đến ngày", df['ngày'].max())
        st.markdown("</div>", unsafe_allow_html=True)

    if start_date > end_date:
        st.error("⚠️ Ngày bắt đầu không thể lớn hơn ngày kết thúc!")
        st.stop()

    column_keyword = f"{investor_selected}_{type_selected}"
    matching_columns = [col for col in df.columns if column_keyword in col]

    if not matching_columns:
        st.warning("⚠️ Không có dữ liệu phù hợp với lựa chọn của bạn.")
        st.stop()

    df_filtered = df[(df['ngày'] >= start_date) & (df['ngày'] <= end_date)]
    if df_filtered.empty:
        st.warning("⚠️ Không có dữ liệu trong khoảng thời gian đã chọn!")
        st.stop()

    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(
            f"<p class='subheader-custom' style='color:#FF9800;margin-bottom: 20px;'>Tổng giá trị giao dịch</p>",
            unsafe_allow_html=True)


        # === Hàm vẽ biểu đồ tổng giao dịch ===
        def plot_total_transaction(df_filtered, matching_columns):
            total_buy = df_filtered[df_filtered[matching_columns].sum(axis=1) > 0][matching_columns].sum().sum() / 1e9
            total_sell = df_filtered[df_filtered[matching_columns].sum(axis=1) < 0][matching_columns].sum().sum() / 1e9

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[''], y=[total_buy], marker_color='#4CAF50', name="Mua ròng",
                text=f"{total_buy:,.1f}bn", textposition="inside", insidetextanchor="middle",
                textangle=0, hovertext=f"Mua ròng: {total_buy:.1f}T", hoverinfo="text"
            ))
            fig.add_trace(go.Bar(
                x=[''], y=[total_sell], marker_color='#FF9800', name="Bán ròng",
                text=f"{total_sell:,.1f}bn", textposition="inside", insidetextanchor="middle",
                textangle=0, hovertext=f"Bán ròng: {total_sell:.1f}T", hoverinfo="text"
            ))
            fig.update_layout(barmode='relative', showlegend=True, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)


        plot_total_transaction(df_filtered, matching_columns)
    with col2:
        st.markdown(
            f"<p class='subheader-custom' style='color:#FF9800;margin-bottom: -20px;'>Giao dịch theo Ngành và Nhà đầu tư</p>",
            unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align: center; font-size: 12px; color: black; margin-bottom: -5px;'>Dữ liệu theo Ngành L2</p>",
            unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align: center; font-size: 12px; color: black; margin-top: -5px;'>Bộ lọc: {investor_selected.replace('_', ' ').title()} - {type_selected.replace('_', ' ').title()}</p>",
            unsafe_allow_html=True)


        def plot_sector_transaction(df_filtered, matching_columns):
            df_filtered['Giá trị ròng'] = df_filtered[matching_columns].sum(axis=1) / 1e9
            df_sorted = df_filtered.groupby('ngành')['Giá trị ròng'].sum().reset_index()
            df_sorted['ngành'] = df_sorted['ngành'].str.replace(' L2', '', regex=True)
            df_sorted = df_sorted.sort_values(by='Giá trị ròng', ascending=True)
            df_sorted['Mua ròng'] = df_sorted['Giá trị ròng'].apply(lambda x: x if x > 0 else 0)
            df_sorted['Bán ròng'] = df_sorted['Giá trị ròng'].apply(lambda x: x if x < 0 else 0)

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                y=df_sorted['ngành'], x=df_sorted['Mua ròng'], orientation='h', marker_color='#4CAF50', name="Mua ròng",
                text=[f"{val:,.1f}bn" if val > 0 else "" for val in df_sorted['Mua ròng']], textposition="outside",
                hoverinfo="text"
            ))
            fig2.add_trace(go.Bar(
                y=df_sorted['ngành'], x=df_sorted['Bán ròng'], orientation='h', marker_color='#FF9800', name="Bán ròng",
                text=[f"{val:,.1f}bn" if val < 0 else "" for val in df_sorted['Bán ròng']], textposition="outside",
                hoverinfo="text"
            ))

            fig2.update_layout(barmode='relative', showlegend=True,
                               xaxis=dict(tickformat=',', tickprefix=' ', ticksuffix=' bn'),
                               margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)


        plot_sector_transaction(df_filtered, matching_columns)
    with st.container():
        st.markdown(
            f"<p class='subheader-custom' style='color:#4B8BBE;'>Giá trị mua/bán ròng theo thời gian</p>",
            unsafe_allow_html=True)

        st.markdown(
            f"<p style='text-align: center; font-size: 12px; color: black; margin-top: -5px;'>Bộ lọc: {investor_selected.replace('_', ' ').title()} - {type_selected.replace('_', ' ').title()}</p>",
            unsafe_allow_html=True)


        def plot_transaction_by_time(df_filtered, matching_columns):
            df_time = df_filtered[['ngày'] + matching_columns].groupby('ngày').sum().reset_index().copy()
            df_time['ngày'] = pd.to_datetime(df_time['ngày'])
            df_time.loc[:, 'Tổng giá trị giao dịch'] = df_time[matching_columns].sum(axis=1) / 1e9
            df_time.loc[:, 'Tích lũy ròng'] = df_time['Tổng giá trị giao dịch'].cumsum()

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_time['ngày'], y=df_time['Tổng giá trị giao dịch'],
                                 name="Giá trị mua/bán ròng", marker_color='#4B8BBE', opacity=1,
                                 text=[f"{val:,.1f}bn" for val in df_time['Tổng giá trị giao dịch']],
                                 textposition='outside', textfont=dict(size=30, color='black'),
                                 yaxis='y1', hovertemplate='Giá trị mua ròng: %{y:,.1f}bn<extra></extra>'))
            fig.add_trace(go.Scatter(x=df_time['ngày'], y=df_time['Tích lũy ròng'],
                                     mode='lines+markers', name="Tích lũy ròng", marker=dict(color='#D62728', size=8),
                                     yaxis='y2', hovertemplate='Tích lũy ròng: %{y:,.1f}bn<extra></extra>'))

            fig.update_layout(
                xaxis_title="Ngày",
                yaxis=dict(side='left', showgrid=False, showticklabels=False, zeroline=True, domain=[0.2, 1.0]),
                yaxis2=dict(side='right', overlaying='y', showgrid=False, showticklabels=False, zeroline=True,
                            domain=[0.2, 1.0]),
                showlegend=True,
                xaxis=dict(showgrid=False),
                hovermode="x unified", barmode='overlay', height=500, width=2000,
                bargap=0.05, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)


        plot_transaction_by_time(df_filtered, matching_columns)
    # ========== SECTION 2: PHÂN BỔ GIAO DỊCH THEO NGÀNH VÀ NHÀ ĐẦU TƯ ==========
    st.markdown("<h1>📊 Phân Bổ Mua/Bán Ròng Theo Ngành Và Nhà Đầu Tư</h1>", unsafe_allow_html=True)

    # **Bộ lọc ngày**
    with st.expander('🔎 **Bộ lọc**', expanded=True):
        st.markdown("""
                <style>
                    div[data-testid="stExpander"] {
                        background-color: #DDEBF7 !important;
                        border-radius: 10px;
                    }
                </style>
                """, unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            type_options = ['khớp_ròng', 'thỏa_thuận_ròng', 'Tổng hợp']  # 🔥 Thêm "Tổng hợp" vào danh sách
            type_selected = st.selectbox(
                "Loại giao dịch",
                type_options,
                format_func=lambda x: x.replace("_", " ").title(),
                key="type_2"
            )

            total_selected = (type_selected == "Tổng hợp")  # ✅ Biến `total_selected` vẫn tồn tại

        with col2:
            if not total_selected:  # 🔥 Ẩn cột này nếu chọn "Tổng hợp"
                transaction_selected = st.selectbox("Loại giao dịch ròng", ['Mua ròng', 'Bán ròng', 'Tổng GT ròng'],
                                                    key="transaction_2")
            else:
                transaction_selected = None  # ✅ Đảm bảo giá trị không ảnh hưởng khi bị ẩn

        with col3:
            start_date = st.date_input("Từ ngày", df['ngày'].min(), key="start_date_2")
        with col4:
            end_date = st.date_input("Đến ngày", df['ngày'].max(), key="end_date_2")
        if start_date > end_date:
            st.error("⚠️ Ngày bắt đầu không thể lớn hơn ngày kết thúc!")
            st.stop()

        # Lọc dữ liệu
    filtered_df = df[(df['ngày'] >= start_date) & (df['ngày'] <= end_date)]
    if filtered_df.empty:
        st.warning("⚠️ Không có dữ liệu trong khoảng thời gian đã chọn!")
        st.stop()
    if transaction_selected == "Tổng GT ròng":
        khop_columns = [col for col in filtered_df.columns if "khớp_ròng" in col]
        thoa_thuan_columns = [col for col in filtered_df.columns if "thỏa_thuận_ròng" in col]
    # Xác định cột matching
    if total_selected:
        matching_columns = {
            "Cá nhân": "cá_nhân_tổng_gt_ròng",
            "Tổ chức trong nước": "tổ_chức_trong_nước_tổng_gt_ròng",
            "Tự doanh": "tự_doanh_tổng_gt_ròng",
            "Nước ngoài": "nước_ngoài_tổng_gt_ròng"
        }
    else:
        matching_columns = {
            "Cá nhân": f"cá_nhân_{type_selected}",
            "Tổ chức trong nước": f"tổ_chức_trong_nước_{type_selected}",
            "Tự doanh": f"tự_doanh_{type_selected}",
            "Nước ngoài": f"nước_ngoài_{type_selected}"
        }

    valid_columns = [col for col in matching_columns.values() if col in filtered_df.columns]
    if not valid_columns:
        st.warning("⚠️ Không có dữ liệu phù hợp với lựa chọn của bạn.")
        st.stop()
    agg_data = filtered_df.groupby('ngành')[valid_columns].sum()
    agg_data = agg_data / 1e9

    # Vẽ biểu đồ

    if transaction_selected == "Tổng GT ròng":
        # 🎯 ====== BIỂU ĐỒ TỔNG GT RÒNG (CÓ GIÁ TRỊ ÂM/DƯƠNG) ======
        fig_khop = go.Figure()
        fig_thoa_thuan = go.Figure()

        # 🔥 Màu sắc cố định cho từng nhóm nhà đầu tư
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        investor_list = ["cá_nhân", "tổ_chức_trong_nước", "tự_doanh", "nước_ngoài"]

        # 🔥 Lọc dữ liệu cho từng nhóm (khớp ròng & thỏa thuận ròng)
        agg_data_khop = filtered_df.groupby('ngành')[khop_columns].sum() if khop_columns else None
        agg_data_thoa_thuan = filtered_df.groupby('ngành')[thoa_thuan_columns].sum() if thoa_thuan_columns else None

        # 🔥 Chuyển đơn vị về tỷ VND
        if agg_data_khop is not None:
            agg_data_khop /= 1e9
        if agg_data_thoa_thuan is not None:
            agg_data_thoa_thuan /= 1e9

        # 🔥 Kiểm tra nếu cả 2 đều trống
        if (agg_data_khop is None or agg_data_khop.empty) and (
                agg_data_thoa_thuan is None or agg_data_thoa_thuan.empty):
            st.warning("⚠️ Không có dữ liệu Tổng GT ròng để hiển thị!")
            st.stop()

        # 🔥 Sắp xếp dữ liệu theo tổng giá trị tuyệt đối để đưa thanh dài nhất lên trên
        if agg_data_khop is not None and not agg_data_khop.empty:
            agg_data_khop["Tổng GT tuyệt đối"] = agg_data_khop.abs().sum(axis=1)
            agg_data_khop_sorted = agg_data_khop.sort_values(by="Tổng GT tuyệt đối", ascending=True)
            agg_data_khop_sorted = agg_data_khop_sorted.drop(columns=["Tổng GT tuyệt đối"])
        if agg_data_thoa_thuan is not None and not agg_data_thoa_thuan.empty:
            agg_data_thoa_thuan["Tổng GT tuyệt đối"] = agg_data_thoa_thuan.abs().sum(axis=1)
            agg_data_thoa_thuan_sorted = agg_data_thoa_thuan.sort_values(by="Tổng GT tuyệt đối", ascending=True)
            agg_data_thoa_thuan_sorted = agg_data_thoa_thuan_sorted.drop(columns=["Tổng GT tuyệt đối"])

        # 🔥 Vẽ biểu đồ Khớp Ròng
        if agg_data_khop is not None and not agg_data_khop.empty:
            for index, investor in enumerate(investor_list):
                color = colors[index % len(colors)]
                df_col_khop = f"{investor}_khớp_ròng"

                if df_col_khop in agg_data_khop.columns:
                    fig_khop.add_trace(go.Bar(
                        y=agg_data_khop.index,
                        x=agg_data_khop[df_col_khop],
                        name=f"{investor.replace('_', ' ').title()}",
                        marker_color=color,
                        orientation='h',
                        text=[f"{x:,.1f}bn" if abs(x) > 500 else "" for x in agg_data_khop[df_col_khop]],
                        textposition="inside",
                        insidetextanchor="middle",
                        hovertemplate=f"{investor.replace('_', ' ').title()} - Khớp Ròng<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                    ))

            # 🔥 Cập nhật layout cho Khớp Ròng
            fig_khop.update_layout(
                title="📊 KHỚP LỆNH",
                xaxis_title="Giá trị giao dịch (Tỷ VND)",
                height=600,
                width=700,
                margin=dict(t=50, b=50),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                barmode='relative',
                xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
                yaxis=dict(categoryorder="array", categoryarray=agg_data_khop_sorted.index.tolist())
            )

        # 🔥 Vẽ biểu đồ Thỏa Thuận Ròng
        if agg_data_thoa_thuan is not None and not agg_data_thoa_thuan.empty:
            for index, investor in enumerate(investor_list):
                color = colors[index % len(colors)]
                df_col_thoa_thuan = f"{investor}_thỏa_thuận_ròng"

                if df_col_thoa_thuan in agg_data_thoa_thuan.columns:
                    fig_thoa_thuan.add_trace(go.Bar(
                        y=agg_data_thoa_thuan.index,
                        x=agg_data_thoa_thuan[df_col_thoa_thuan],
                        name=f"{investor.replace('_', ' ').title()}",
                        marker_color=color,
                        orientation='h',
                        text=[f"{x:,.1f}bn" if abs(x) > 500 else "" for x in agg_data_thoa_thuan[df_col_thoa_thuan]],
                        textposition="inside",
                        insidetextanchor="middle",
                        hovertemplate=f"{investor.replace('_', ' ').title()} - Thỏa Thuận Ròng<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                    ))

            # 🔥 Cập nhật layout cho Thỏa Thuận Ròng
            fig_thoa_thuan.update_layout(
                title="📊 THỎA THUẬN",
                xaxis_title="Giá trị giao dịch (Tỷ VND)",
                height=600,
                width=700,
                margin=dict(t=50, b=50),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                barmode='relative',
                xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
                yaxis=dict(categoryorder="array", categoryarray=agg_data_thoa_thuan_sorted.index.tolist())
            )

        # 🔥 Hiển thị hai biểu đồ tách biệt
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_khop, use_container_width=True)
        with col2:
            st.plotly_chart(fig_thoa_thuan, use_container_width=True)

    else:
        fig = go.Figure()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        if total_selected:
            # ====== BIỂU ĐỒ TỔNG HỢP ======
            agg_data["Tổng giá trị tuyệt đối"] = agg_data.abs().sum(axis=1)
            agg_data_sorted = agg_data.sort_values(by="Tổng giá trị tuyệt đối", ascending=True)
            agg_data_sorted = agg_data_sorted.drop(columns=["Tổng giá trị tuyệt đối"])

            for i, investor in enumerate(matching_columns.keys()):
                df_col = matching_columns[investor]
                if df_col not in agg_data_sorted.columns:
                    continue

                fig.add_trace(go.Bar(
                    y=agg_data_sorted.index,
                    x=agg_data_sorted[df_col],
                    name=investor,
                    marker_color=colors[i % len(colors)],
                    orientation='h',
                    text=[f"{x:,.1f}bn" if abs(x) > 300 else "" for x in agg_data_sorted[df_col]],
                    textposition="inside", insidetextanchor="middle",
                    hovertemplate=f"{investor}<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                ))

            fig.update_layout(
                title="📊 BIỂU ĐỒ THỊ TRƯỜNG (KHỚP LỆNH + THỎA THUẬN)",
                font=dict(family="Poppins, sans-serif", size=18, color="black"),
                xaxis_title="Giá trị mua/bán ròng (Tỷ VND)",
                height=700,
                margin=dict(t=50, b=50),
                legend=dict(title="Nhà đầu tư"),
                barmode='relative',
                xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
                yaxis=dict(categoryorder="array", categoryarray=agg_data_sorted.index.tolist()))

        else:
            agg_data["Tổng giá trị"] = agg_data.sum(axis=1)
            agg_data = agg_data.sort_values(by="Tổng giá trị", ascending=False)
            agg_data = agg_data.drop(columns=["Tổng giá trị"])
            # ====== BIỂU ĐỒ MUA RÒNG / BÁN RÒNG ======
            for i, investor in enumerate(matching_columns.keys()):
                df_col = matching_columns[investor]
                if df_col not in agg_data.columns:
                    continue

                data_filtered = agg_data[df_col]
                if transaction_selected == "Mua ròng":
                    data_buy = data_filtered[data_filtered > 0]
                    data_sell = None
                elif transaction_selected == "Bán ròng":
                    data_sell = data_filtered[data_filtered < 0]
                    data_buy = None
                elif transaction_selected == "Tổng GT ròng":
                    data_buy = data_filtered[data_filtered > 0]
                    data_sell = data_filtered[data_filtered < 0]

                if data_buy is not None and not data_buy.empty:
                    fig.add_trace(go.Bar(
                        y=data_buy.index,
                        x=data_buy.values,
                        name=f"{investor}",
                        marker_color=colors[i % len(colors)],
                        orientation='h',
                        text=[f"{val:,.1f}bn" if abs(val) > 100 else "" for val in data_buy],
                        textposition="inside", insidetextanchor="middle",
                        hovertemplate=f"{investor} - Mua ròng<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                    ))

                if data_sell is not None and not data_sell.empty:
                    fig.add_trace(go.Bar(
                        y=data_sell.index,
                        x=data_sell.values,
                        name=f"{investor}",
                        marker_color=colors[i % len(colors)],
                        orientation='h',
                        text=[f"{val:,.1f}bn" if abs(val) > 100 else "" for val in data_sell],
                        textposition="inside", insidetextanchor="middle",
                        hovertemplate=f"{investor} - Bán ròng<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                    ))

            fig.update_layout(
                title=f"📊 BIỂU ĐỒ THỊ TRƯỜNG ({transaction_selected.upper()})",
                font=dict(family="Poppins, sans-serif", size=18, color="black"),
                xaxis_title="Giá trị giao dịch (Tỷ VND)",
                yaxis_title="Ngành",
                height=700,
                margin=dict(t=50, b=50),
                legend=dict(title="Nhà đầu tư"),
                barmode='relative',
                xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
                yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)


    def plot_investor_charts(agg_data, matching_columns, total_selected, transaction_selected):
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=list(matching_columns.keys()),
            vertical_spacing=0.1,
            horizontal_spacing=0.2
        )

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        if total_selected:
            # 🎯 ====== BIỂU ĐỒ TỔNG HỢP ======
            agg_data["Tổng giá trị tuyệt đối"] = agg_data.abs().sum(axis=1)
            agg_data_sorted = agg_data.sort_values(by="Tổng giá trị tuyệt đối", ascending=True)
            agg_data_sorted = agg_data_sorted.drop(columns=["Tổng giá trị tuyệt đối"])

            for i, (investor, column) in enumerate(matching_columns.items()):
                row, col = (i // 2) + 1, (i % 2) + 1

                if column in agg_data_sorted.columns:
                    fig.add_trace(go.Bar(
                        y=agg_data_sorted.index,
                        x=agg_data_sorted[column],
                        name=investor,
                        marker_color=colors[i % len(colors)],
                        orientation='h',
                        hovertemplate=f"{investor}<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                    ), row=row, col=col)
                    fig.update_yaxes(categoryorder="array", categoryarray=agg_data_sorted.index.tolist(), row=row,
                                     col=col)

            title_text = "📊 PHÂN BỔ GIAO DỊCH THEO NHÀ ĐẦU TƯ (KHỚP LỆNH + THỎA THUẬN)"
            fig.update_layout(
                title=title_text,
                font=dict(family="Poppins, sans-serif", size=18, color="black"),
                height=700,
                width=500,
                margin=dict(l=0, r=0, t=60, b=60),
                showlegend=False,
                barmode='relative')

        else:
            # 🎯 ====== BIỂU ĐỒ MUA RÒNG / BÁN RÒNG ======
            agg_data["Tổng giá trị"] = agg_data.sum(axis=1)
            agg_data = agg_data.sort_values(by="Tổng giá trị", ascending=False)
            agg_data = agg_data.drop(columns=["Tổng giá trị"])

            for i, (investor, column) in enumerate(matching_columns.items()):
                row, col = (i // 2) + 1, (i % 2) + 1

                if column in agg_data.columns:
                    data_filtered = agg_data[column]
                    data_buy, data_sell = None, None
                    if transaction_selected == "Mua ròng":
                        data_buy = data_filtered[data_filtered > 0]
                        data_sell = None
                    elif transaction_selected == "Bán ròng":
                        data_sell = data_filtered[data_filtered < 0]
                        data_buy = None
                    elif transaction_selected == "Tổng GT ròng":
                        data_buy = data_filtered[data_filtered > 0]
                        data_sell = data_filtered[data_filtered < 0]

                    if data_buy is not None and not data_buy.empty:
                        fig.add_trace(go.Bar(
                            y=data_buy.index,
                            x=data_buy.values,
                            name=f"{investor}",
                            marker_color=colors[i % len(colors)],
                            orientation='h',
                            hovertemplate=f"{investor} - Mua ròng<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                        ), row=row, col=col)

                    if data_sell is not None and not data_sell.empty:
                        fig.add_trace(go.Bar(
                            y=data_sell.index,
                            x=data_sell.values,
                            name=f"{investor}",
                            marker_color=colors[i % len(colors)],
                            orientation='h',
                            hovertemplate=f"{investor} - Bán ròng<br>Ngành: %{{y}}<br>Giá trị: %{{x:.2f}} tỷ VND"
                        ), row=row, col=col)
                    fig.update_yaxes(categoryorder="total ascending", row=row, col=col)
            title_text = f"📊 PHÂN BỔ GIAO DỊCH THEO NHÀ ĐẦU TƯ ({transaction_selected.upper()})"
            fig.update_layout(
                title=title_text,
                font=dict(family="Poppins, sans-serif", size=18, color="black"),
                height=700,
                width=500,
                margin=dict(l=0, r=0, t=50, b=50),
                showlegend=False,
                barmode='relative'
            )

        st.plotly_chart(fig, use_container_width=True)


    plot_investor_charts(agg_data, matching_columns, total_selected, transaction_selected)
    # -------- SECTION 3: Thống kê dòng tiền ----------#
    # Tiêu đề
    st.markdown("<h1>📊 Thống Kê Dòng Tiền</h1>", unsafe_allow_html=True)

    # Bộ lọc ngày
    with st.expander('🔎 **Bộ lọc**', expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Từ ngày", df['ngày'].min(), key="start_date_3")
        with col2:
            end_date = st.date_input("Đến ngày", df['ngày'].max(), key="end_date_3")

    # Kiểm tra dữ liệu hợp lệ
    if start_date > end_date:
        st.error("⚠️ Ngày bắt đầu không thể lớn hơn ngày kết thúc!")
        st.stop()

    df_filtered = df[(df['ngày'] >= start_date) & (df['ngày'] <= end_date)]
    if df_filtered.empty:
        st.warning("⚠️ Không có dữ liệu trong khoảng thời gian đã chọn!")
        st.stop()

    # Mapping nhóm nhà đầu tư
    col_mapping = {
        "Cá nhân": "cá_nhân",
        "Tổ chức": "tổ_chức_trong_nước",
        "Tự doanh": "tự_doanh",
        "Nước ngoài": "nước_ngoài"
    }
    investor_types = list(col_mapping.keys())

    # Tính giá trị khớp và thỏa thuận (đổi sang đơn vị Tỷ VND)
    khop_values = [df_filtered[f"{col_mapping[inv]}_khớp_ròng"].sum() / 1e9 for inv in investor_types]
    thoa_thuan_values = [df_filtered[f"{col_mapping[inv]}_thỏa_thuận_ròng"].sum() / 1e9 for inv in investor_types]

    # Tạo figure
    fig = go.Figure()

    # Biểu đồ “Khớp lệnh” Ribbon + hiển thị số
    fig.add_trace(go.Scatter(
        x=investor_types,
        y=khop_values,
        mode='lines+markers+text',  # hiển thị đường, marker, và text
        line=dict(shape='spline', smoothing=1.2, color='rgba(30, 144, 255, 0.9)', width=2),
        fill='tonexty',
        fillcolor='rgba(30, 144, 255)',
        name='Khớp lệnh',
        text=[f"{v:.1f}" for v in khop_values],  # chuỗi text hiển thị
        textposition='top center',  # vị trí text
        textfont=dict(color='black', size=14),  # màu & cỡ chữ
        marker=dict(size=6)  # kích thước marker
    ))

    # Biểu đồ “Thỏa thuận” Ribbon + hiển thị số
    fig.add_trace(go.Scatter(
        x=investor_types,
        y=thoa_thuan_values,
        mode='lines+markers+text',
        line=dict(shape='spline', smoothing=1.2, color='rgba(0, 0, 139, 0.9)', width=2),
        fill='tonexty',
        fillcolor='rgba(0, 0, 139)',
        name='Thỏa thuận',
        text=[f"{v:.1f}" for v in thoa_thuan_values],
        textposition='top center',
        textfont=dict(color='white', size=14),
        marker=dict(size=6),
    ))
    # Nếu bạn không muốn các đường thẳng đứng “nối từ 0 đến giá trị”, hãy bỏ hẳn for-loop này.
    # (Hoặc giữ lại nhưng sẽ vẫn là đường thẳng, không thể bo tròn do cùng hoành độ.)
    # for i, investor in enumerate(investor_types):
    #     fig.add_trace(go.Scatter(
    #         x=[investor, investor],
    #         y=[0, khop_values[i]],
    #         mode="lines",
    #         line=dict(width=10, color='rgba(30, 144, 255, 0.9)'),
    #         name=f"Khớp lệnh ({investor})"
    #     ))
    #     fig.add_trace(go.Scatter(
    #         x=[investor, investor],
    #         y=[0, thoa_thuan_values[i]],
    #         mode="lines",
    #         line=dict(width=10, color='rgba(0, 0, 139, 0.9)'),
    #         name=f"Thỏa thuận ({investor})"
    #     ))

    # Tùy chỉnh layout
    fig.update_layout(
        title="📊 Thống Kê Dòng Tiền",
        xaxis_title="Nhóm nhà đầu tư",
        yaxis_title="Giá trị giao dịch (Tỷ VND)",
        showlegend=True,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, zeroline=True),
        plot_bgcolor='white',
        font=dict(size=14),
    )

    # Hiển thị biểu đồ trên Streamlit
    st.plotly_chart(fig, use_container_width=True)
    # ============BIỂU ĐỒ THANH BAR============#
    # **Tính tổng theo ngày**
    df_grouped = df_filtered.groupby("ngày").sum()

    # Tạo figure cho Khớp lệnh & Thỏa thuận
    fig_khop = go.Figure()
    fig_thoa_thuan = go.Figure()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    investor_list = ["cá_nhân", "tổ_chức_trong_nước", "tự_doanh", "nước_ngoài"]

    # Xác định giá trị lớn nhất để tự động scale trục Y
    all_values = []

    for investor in investor_list:
        df_col_khop = f"{investor}_khớp_ròng"
        df_col_thoa_thuan = f"{investor}_thỏa_thuận_ròng"

        if df_col_khop in df_grouped.columns:
            all_values.extend(df_grouped[df_col_khop].tolist())

        if df_col_thoa_thuan in df_grouped.columns:
            all_values.extend(df_grouped[df_col_thoa_thuan].tolist())

    # **Tự động điều chỉnh trục Y**
    y_max = max(abs(v / 1e9) for v in all_values if v != 0)
    y_range = [-y_max * 1.1, y_max * 1.1]

    for index, investor in enumerate(investor_list):
        color = colors[index % len(colors)]
        df_col_khop = f"{investor}_khớp_ròng"
        df_col_thoa_thuan = f"{investor}_thỏa_thuận_ròng"

        if df_col_khop in df_grouped.columns:
            fig_khop.add_trace(go.Bar(
                x=df_grouped.index,
                y=df_grouped[df_col_khop] / 1e9,  # Chia cho 1e9 để hiển thị Tỷ VND
                name=investor.replace('_', ' ').title(),
                marker_color=color,
                text=[f"{int(x)} bn" if abs(x) > 3000 else "" for x in df_grouped[df_col_khop] / 1e9],  # Làm tròn số
                textposition="inside",  # Số liệu nằm trong cột
                insidetextanchor="middle"  # **Giữ text ở chính giữa**
            ))

        if df_col_thoa_thuan in df_grouped.columns:
            fig_thoa_thuan.add_trace(go.Bar(
                x=df_grouped.index,
                y=df_grouped[df_col_thoa_thuan] / 1e9,  # Chia cho 1e9 để hiển thị Tỷ VND
                name=investor.replace('_', ' ').title(),
                marker_color=color,
                text=[f"{int(x)} bn" if abs(x) > 3000 else "" for x in df_grouped[df_col_thoa_thuan] / 1e9],
                # Làm tròn số
                textposition="inside",  # Số liệu nằm trong cột
                insidetextanchor="middle"  # **Giữ text ở chính giữa**
            ))

    fig_khop.update_layout(
        title="📊 KHỚP LỆNH",
        barmode='relative',
        bargap=0.1,  # Cột sát nhau nhưng không dính
        xaxis=dict(type="category", tickangle=-45),  # Xoay ngày thành xéo
        yaxis=dict(visible=False),  # Ẩn trục Y
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5),  # Chú thích nằm ngang
    )

    fig_thoa_thuan.update_layout(
        title="📊 THỎA THUẬN",
        barmode='relative',
        bargap=0.1,
        xaxis=dict(type="category", tickangle=-45),  # Xoay ngày thành xéo
        yaxis=dict(visible=False),  # Ẩn trục Y
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5),  # Chú thích nằm ngang
    )

    # Hiển thị hai biểu đồ cạnh nhau
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_khop, use_container_width=True)
    with col2:
        st.plotly_chart(fig_thoa_thuan, use_container_width=True)

elif selected == "Tổng quan thị trường":
    st.markdown("<h1>📊 Tổng quan về vốn hóa TTCK Việt Nam</h1>", unsafe_allow_html=True)
    EXCEL_PATH = "E:/GOI1_B3/cat1/Cleaned_Vietnam_Marketcap.xlsx"


    @st.cache_data
    def load_and_process_data():
        # Load the Excel file and process the data
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


    # Plot sector count
    def plot_sector_count():
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        sector_counts = DF1["Sector"].value_counts()
        top_sectors = sector_counts.head(15)
        top_sectors.plot(kind="bar", ax=ax, color='skyblue', edgecolor='black')
        ax.set_xlabel("Ngành")
        ax.set_ylabel("Số lượng công ty")
        ax.set_title("Thống kê về số lượng công ty trong mỗi ngành")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        return fig


    # Plot market cap
    def plot_market_cap():
        SECTOR_MARKETCAP_T = MERGED_DF.groupby("Sector")[DATE_COLUMNS].sum().T
        SECTOR_MARKETCAP_T.index = pd.to_datetime(SECTOR_MARKETCAP_T.index)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        top_sectors = SECTOR_MARKETCAP_T.sum().nlargest(5).index
        for sector in top_sectors:
            ax.plot(SECTOR_MARKETCAP_T.index, SECTOR_MARKETCAP_T[sector], label=sector)
        ax.set_xlabel("Thời gian")
        ax.set_ylabel("Tổng vốn hóa thị trường (VNĐ)")
        ax.set_title("Thống kê về vốn hóa thị trường qua các năm")
        ax.legend(loc="upper left")
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
    def generate_pdf(stock_code):
        progress_bar = st.progress(0)  # Initialize progress bar
        with st.spinner("📄 Đang tạo báo cáo PDF, vui lòng đợi..."):
            # Define SECTOR_MARKETCAP_T inside the function or globally
            SECTOR_MARKETCAP_T = MERGED_DF.groupby("Sector")[DATE_COLUMNS].sum().T
            SECTOR_MARKETCAP_T.index = pd.to_datetime(SECTOR_MARKETCAP_T.index)

            # Initialize PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("DejaVu", "", r"E:/GOI1/MSSV_CHAN_GOI1_GROUP1/ttf/DejaVuSans.ttf", uni=True)
            pdf.set_font("DejaVu", size=12)

            pdf.cell(200, 10, "Báo cáo thị trường chứng khoán Việt Nam", ln=True, align='C')
            pdf.ln(10)

            # Calculate top sectors
            top_sectors = SECTOR_MARKETCAP_T.sum().nlargest(5)
            for sector, value in top_sectors.items():
                pdf.cell(200, 10, f"{sector}: {value:,.0f} VNĐ", ln=True)

            pdf.ln(10)

        for i, plot_func in enumerate([plot_sector_count, plot_market_cap, plot_sector_treemap, plot_bubble_chart]):
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
        pdf_path = "market_report.pdf"
        pdf.output(pdf_path, "F")

        with open(pdf_path, "rb") as file:
            st.success(f"✅ PDF đã được tạo: {pdf_path}")
            st.download_button("📥 Tải xuống PDF", data=file, file_name="market_report.pdf", mime="application/pdf")


    st.pyplot(plot_sector_count())
    st.pyplot(plot_market_cap())

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
        generate_pdf(stock_code)  # Pass stock_code to generate_pdf
elif selected == "Tổng quan theo ngành":
    st.markdown("<h1>📊 Phân loại theo nhà đầu tư - khối ngoại FT</h1>", unsafe_allow_html=True)
    subpage = st.radio("Chọn danh mục", ["Net FT Overview", "Net FT - Ticker", "TOP_FT"], horizontal=True)
    file_paths = {
        "E:/GOI1_B3/Cleaned data/CleanedFT/FT1921_cleaned.csv",
        "E:/GOI1_B3/Cleaned data/CleanedFT/FT2123_cleaned.csv",
        "E:/GOI1_B3/Cleaned data/CleanedFT/FT2325_cleaned.csv"
    }
    if subpage == "Net FT Overview":
        def load_data():
            dfs = [pd.read_csv(path) for path in file_paths]
            df = pd.concat(dfs, ignore_index=True)
            df.columns = df.columns.str.strip()
            df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
            df = df.dropna(subset=["Date", "Net.F_Val", "Close", "%Chg"])
            df = df.sort_values(by="Date").reset_index(drop=True)
            return df

        # Calculate % price change
        def calculate_price_change(df, start_date, end_date):
            first_day = df[df['Date'] == start_date].groupby('Ticker')['Close'].mean()
            last_day = df[df['Date'] == end_date].groupby('Ticker')['Close'].mean()
            price_change = ((last_day - first_day) / first_day).fillna(0)
            return price_change.reset_index().rename(columns={'Close': 'Price_Chg'})


        # Draw treemap
        def draw_treemap(df, title):
            df['color'] = df['Price_Chg'].apply(lambda x: 'green' if x >= 0 else 'red')
            fig = px.treemap(df,
                             path=['Ticker'],
                             values='abs_val',
                             color='color',
                             color_discrete_map={'green': '#00cc96', 'red': '#EF553B'})
            fig.update_traces(texttemplate='%{label}<br>%{customdata[0]:.2%}',
                              customdata=df[['Price_Chg']],
                              marker=dict(line=dict(color='black', width=1)))
            fig.update_layout(title=title, margin=dict(t=40, l=0, r=0, b=0), coloraxis_showscale=False)
            return fig


        def export_pdf(start_date, end_date, fig_time_series, fig1, fig2, filename="treemap_full.pdf"):
            fig_time_series.write_image("time_series.png", width=1000, height=500)
            fig1.write_image("mua_rong.png", width=1000, height=500)
            fig2.write_image("ban_rong.png", width=1000, height=500)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Data from: {start_date} to: {end_date}", ln=True, align='C')

            pdf.image("time_series.png", x=10, y=30, w=190)
            pdf.add_page()
            pdf.image("mua_rong.png", x=10, y=20, w=190)
            pdf.add_page()
            pdf.image("ban_rong.png", x=10, y=20, w=190)

            pdf.output(filename)
            with open(filename, "rb") as file:
                st.download_button(
                    label="📥 Download PDF",
                    data=file,
                    file_name=filename,
                    mime="application/pdf"
                )


        st.title("Net Foreign Trading Overview ")

        df = load_data()
        start_date, end_date = st.date_input("Select date range:", [df.Date.min(), df.Date.max()])

        filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]

        st.subheader("📈 Total Foreign Trading Value")
        fig_time_series = go.Figure()
        fig_time_series.add_trace(
            go.Scatter(x=filtered_df["Date"], y=filtered_df["F.Buy_Val"], mode='lines', name="Foreign Buy",
                       line=dict(color='blue', width=5)))
        fig_time_series.add_trace(
            go.Scatter(x=filtered_df["Date"], y=filtered_df["F.Sell_Val"], mode='lines', name="Foreign Sell",
                       line=dict(color='red', width=5)))
        fig_time_series.add_trace(
            go.Scatter(x=filtered_df["Date"], y=filtered_df["Net.F_Val"], mode='lines', name="Net Foreign Trading",
                       line=dict(color='green', width=5)))
        fig_time_series.update_layout(xaxis_title="Date", yaxis_title="Billion VND", template="plotly_dark", width=1200,
                                      height=600)
        st.plotly_chart(fig_time_series)

        total_net_df = filtered_df.groupby('Ticker')['Net.F_Val'].sum().reset_index()
        price_change = calculate_price_change(filtered_df, pd.to_datetime(start_date), pd.to_datetime(end_date))
        merged_df = total_net_df.merge(price_change, on='Ticker')

        mua_rong = merged_df[merged_df['Net.F_Val'] > 0].copy()
        ban_rong = merged_df[merged_df['Net.F_Val'] < 0].copy()

        mua_rong['abs_val'] = mua_rong['Net.F_Val']
        ban_rong['abs_val'] = ban_rong['Net.F_Val'].abs()

        total_mua = mua_rong['abs_val'].sum()
        total_ban = ban_rong['abs_val'].sum()

        col1, col2 = st.columns([total_mua, total_ban])

        with col1:
            st.subheader(f"Net Buy ({total_mua:,.0f} Billion)")
            fig1 = draw_treemap(mua_rong, "Net Buy")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader(f"Net Sell ({total_ban:,.0f} Billion)")
            fig2 = draw_treemap(ban_rong, "Net Sell")
            st.plotly_chart(fig2, use_container_width=True)
        if st.button("Export PDF"):
            export_pdf(start_date, end_date, fig_time_series, fig1, fig2)
    if subpage == "Net FT - Ticker":
        def load_data(files):
            dfs = {}
            for path in files:
                df = pd.read_csv(path, encoding='utf-8')
                df.columns = df.columns.str.strip()  # Xóa khoảng trắng
                df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")  # Chuyển đổi định dạng Date
                dfs[path] = df
            return dfs


        # Tải dữ liệu
        dataframes = load_data(file_paths)

        # Gộp tất cả dữ liệu vào một dataframe chung
        data = pd.concat(dataframes.values(), ignore_index=True)

        # Lọc bỏ ngày không có dữ liệu
        data = data.dropna(subset=["Date", "Net.F_Val", "Close"])  # Giữ lại các ngày có dữ liệu hợp lệ

        # Sắp xếp lại dữ liệu theo thời gian
        data = data.sort_values(by=["Date"]).reset_index(drop=True)

        # Giao diện Streamlit
        st.title("📊 NET FT - Ticker")

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

                st.plotly_chart(fig)
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
                if st.button("📄 Export PDF"):
                    pdf_output = export_pdf_combined(fig, datetime.now())
                    st.download_button(
                        label="Download PDF",
                        data=pdf_output,
                        file_name=f"NET_FT_{ticker_selected}.pdf",
                        mime="application/pdf"
                    )
    if subpage == "TOP_FT":
        st.title("📊 TOP Net Foreign Buying and Selling")
        def load_and_merge_data(files):
            dataframes = []
            for path in files:
                df = pd.read_csv(path, encoding='utf-8')
                df.columns = df.columns.str.strip()
                df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
                df = df.dropna(subset=["Date", "Net.F_Val", "%Chg", "Close"])
                dataframes.append(df)
            return pd.concat(dataframes, ignore_index=True)


        # Hàm xuất PDF với 4 biểu đồ trong cùng một ảnh
        def export_pdf_combined(figs, top_mua_rong, top_ban_rong, date):
            buf = BytesIO()
            with PdfPages(buf) as pdf:
                plt.figure(figsize=(8, 6))
                plt.text(0.5, 0.8, f"Báo cáo giao dịch nhà đầu tư nước ngoài", fontsize=14, ha='center')
                plt.text(0.5, 0.6, f"Ngày trích xuất: {date.strftime('%d/%m/%Y')}", fontsize=12, ha='center')
                plt.axis("off")
                pdf.savefig()
                plt.close()
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                titles = ["Top GTGD NN mua ròng", "Top KLGD NN mua ròng", "Top GTGD NN bán ròng",
                          "Top KLGD NN bán ròng"]
                for ax, fig_plot, title in zip(axes.flatten(), figs, titles):
                    fig_bytes = pio.to_image(fig_plot, format="png")
                    img = plt.imread(BytesIO(fig_bytes))
                    ax.imshow(img)
                    ax.set_title(title, fontsize=14, fontweight="bold")
                    ax.axis("off")
                plt.tight_layout()
                pdf.savefig()
                plt.close()
                # Xuất bảng Top Mua/Bán Ròng
                for title, df in [("📈 Top Mua Ròng", top_mua_rong), ("📉 Top Bán Ròng", top_ban_rong)]:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.axis("off")
                    ax.table(cellText=df[['Ticker', 'Close', '%Chg', 'Net.F_Val']].values,
                             colLabels=['Mã', 'Giá (Nghìn đồng)', 'Thay đổi (%)', 'Giá trị (Tỷ VND)'],
                             cellLoc='center', loc='center')
                    ax.set_title(title, fontsize=14)
                    pdf.savefig()
                    plt.close()
            buf.seek(0)
            return buf

        df = load_and_merge_data(file_paths)


        def plot_bar_chart(df, net_col, buy_col, sell_col, title):
            df_sorted = df.sort_values(by=net_col, ascending=('sell' in title.lower())).head(10)

            fig = go.Figure()

            fig.add_trace(go.Bar(
                y=df_sorted["Ticker"],
                x=df_sorted[sell_col],
                name="Sell",
                orientation="h",
                marker=dict(color="red"),
                text=df_sorted[sell_col].apply(lambda x: f"{x:.1f}bn"),
                textposition="inside"
            ))

            fig.add_trace(go.Bar(
                y=df_sorted["Ticker"],
                x=df_sorted[buy_col],
                name="Buy",
                orientation="h",
                marker=dict(color="green"),
                text=df_sorted[buy_col].apply(lambda x: f"{x:.1f}bn"),
                textposition="inside"
            ))

            color_net = ["yellow" if val >= 0 else "blue" for val in df_sorted[net_col]]
            fig.add_trace(go.Bar(
                y=df_sorted["Ticker"],
                x=df_sorted[net_col],
                name="Net",
                orientation="h",
                marker=dict(color=color_net),
                text=df_sorted[net_col].apply(lambda x: f"{x:.1f}bn"),
                textposition="inside"
            ))

            fig.update_layout(
                title=title,
                barmode="relative",
                xaxis_title="VL",
                yaxis_title="Ticker",
                template="plotly_dark",
                height=400,
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
            )

            return fig

        # Date selection
        selected_date = st.date_input("📅 Select Date", pd.to_datetime("2025-02-01"))
        filtered_df = df[df['Date'].dt.date == selected_date]
        if filtered_df.empty:
            st.warning(f"⚠️ No trading data available for {selected_date}. Please choose another date.")
        else:
            st.success(f"✅ Successfully loaded data for {selected_date.strftime('%d/%m/%Y')}")
            st.dataframe(filtered_df)

            # Display top net buying and selling
            top_buy = filtered_df.nlargest(10, 'Net.F_Val')
            top_sell = filtered_df.nsmallest(10, 'Net.F_Val')

            col1, col2 = st.columns(2)

            with col1:
                st.write("### 📈 Top Net Buy")
                st.dataframe(top_buy[['Ticker', 'Close', '%Chg', 'Net.F_Val']])

            with col2:
                st.write("### 📉 Top Net Sell")
                st.dataframe(top_sell[['Ticker', 'Close', '%Chg', 'Net.F_Val']])

            # Bar charts
            fig1 = plot_bar_chart(top_buy, 'Net.F_Val', 'F.Buy_Val', 'F.Sell_Val', 'Top Net Buy')
            fig2 = plot_bar_chart(top_sell, 'Net.F_Val', 'F.Buy_Val', 'F.Sell_Val', 'Top Net Sell')
            fig3 = plot_bar_chart(filtered_df[filtered_df["Net.F_Vol"] >= 0], "Net.F_Vol", "F.Buy_Vol", "F.Sell_Vol",
                                  "Top Net Buy Volume")
            fig4 = plot_bar_chart(filtered_df[filtered_df["Net.F_Vol"] < 0], "Net.F_Vol", "F.Buy_Vol", "F.Sell_Vol",
                                  "Top Net Sell Volume")

            st.plotly_chart(fig1)
            st.plotly_chart(fig2)
            st.plotly_chart(fig3)
            st.plotly_chart(fig4)
            # Export PDF
            if st.button("📥 Export PDF"):
                pdf_file = export_pdf_combined([fig1, fig3, fig2, fig4], top_buy, top_sell, selected_date)
                st.download_button("Download PDF", pdf_file, f"report_{selected_date}.pdf", "application/pdf")

# CAT 4
elif selected == "Xu hướng thị trường":
    st.markdown("<h1>📊 Xu hướng thị trường - Phân tích kỹ thuật</h1>", unsafe_allow_html=True)
    # ✅ Tạo menu subpage
    subpage = st.radio("Chọn danh mục",
                       ["Tổng quan", "Chi tiết cổ phiếu", "So sánh cổ phiếu", "Phân tích thị trường với MA",
                        "Đỉnh của CP"], horizontal=True)
    PRICE_DATA_PATH = 'E:/GOI1/MSSV_CHAN_GOI1_GROUP1/MSSV_CHAN_GOI1_GROUP1/Data/Processed_Vietnam_Price.xlsx'
    VOLUME_DATA_PATH = 'E:/GOI1/MSSV_CHAN_GOI1_GROUP1/MSSV_CHAN_GOI1_GROUP1/Data/Processed_Vietnam_volume_2.xlsx'


    # 📌 Load dữ liệu từ file Excel
    @st.cache_data
    def load_data():
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


    def select_time_period1():
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


    file_price = "E:/GOI1_B3/Lợi/Processed_Vietnam_Price_Long.csv.gz"
    file_volume = "E:/GOI1_B3/Lợi/Processed_Vietnam_Volume_Long.csv.gz"


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
    def display_colored_table(df_summary):
        if df_summary is None:
            return

        def highlight_cells(val):
            """
            Tô màu dựa trên giá trị % Change:
            - Màu đỏ: Giảm mạnh
            - Màu vàng: Biến động nhẹ
            - Màu xanh: Tăng mạnh
            """
            color = 'red' if val < 0 else 'lightgreen' if 0 <= val <= 20 else 'green' if val > 20 else 'white'
            return f'background-color: {color}'

        styled_df = df_summary.style.applymap(highlight_cells, subset=['% Change'])

        st.write("📊 **Bảng thống kê giá đóng cửa & khối lượng giao dịch**")
        st.dataframe(styled_df)


    def plot_sector_distribution(df_price):
        """
        Vẽ biểu đồ số lượng công ty trong từng ngành.
        """
        # Đổi tên ngành '-' thành 'Others'
        df_price['Sector'] = df_price['Sector'].replace('-', 'Others')

        # Nhóm dữ liệu theo ngành và đếm số lượng công ty
        grouped_by_sector = df_price.groupby('Sector').agg({'Name': 'count'}).reset_index()
        grouped_by_sector.columns = ['Ngành', 'Số lượng công ty']

        # Sắp xếp theo thứ tự từ cao đến thấp
        grouped_by_sector = grouped_by_sector.sort_values(by='Số lượng công ty', ascending=False)

        # Tạo bảng màu tự động từ Seaborn
        colors = sns.color_palette("tab20", len(grouped_by_sector))

        # Vẽ biểu đồ cột dọc với màu sắc khác nhau
        fig, ax = plt.subplots(figsize=(15, 8))
        bars = ax.bar(grouped_by_sector['Ngành'], grouped_by_sector['Số lượng công ty'], color=colors)

        ax.set_xticklabels(grouped_by_sector['Ngành'], rotation=45, ha='right', fontsize=10)
        ax.set_title('Số lượng công ty trong từng ngành', fontsize=16)
        ax.set_xlabel('Ngành', fontsize=12)
        ax.set_ylabel('Số lượng công ty', fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        # Thêm giá trị chú thích phía trên từng cột
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5, f'{int(height)}', ha='center', fontsize=10,
                    color='blue')

        plt.tight_layout()

        # Hiển thị biểu đồ trong Streamlit
        st.pyplot(fig)


    def plot_treemap_ma200(df_price, selected_date):
        # 📌 Kiểm tra nếu ngày được chọn không hợp lệ
        if selected_date not in df_price.columns:
            st.warning(f"⚠ Ngày {selected_date} không tồn tại trong dữ liệu!")
            return

        # 📌 Chuyển đổi các cột ngày thành kiểu float để tính toán chính xác
        df_price[selected_date] = pd.to_numeric(df_price[selected_date], errors='coerce')

        # 📌 Xác định ngày trước đó (dùng để lấy giá mở cửa hôm nay)
        prev_day_index = df_price.columns.get_loc(selected_date) - 1
        if prev_day_index < 7:
            st.warning("⚠ Không đủ dữ liệu để tính toán MA200.")
            return

        prev_day = df_price.columns[prev_day_index]
        df_price[prev_day] = pd.to_numeric(df_price[prev_day], errors='coerce')

        # 📌 Tính giá mở cửa hôm nay = Giá đóng cửa ngày trước đó
        df_price["Open"] = df_price[prev_day]

        # 📌 Tính MA200 (Trung bình động 200 ngày)
        df_price["MA200"] = df_price.iloc[:, -200:].mean(axis=1)

        # 📌 Xác định cổ phiếu có MA200 đang tăng
        df_price["MA200 Change"] = ((df_price[selected_date] - df_price["MA200"]) / df_price["MA200"]) * 100
        df_ma200_up = df_price[df_price["MA200 Change"] > 0].copy()

        # 📌 Kiểm tra nếu không có cổ phiếu nào thỏa mãn
        if df_ma200_up.empty:
            st.warning("⚠ Không có cổ phiếu nào có MA200 đang tăng.")
            return

        # 📌 Xử lý cột ngành (Sector)
        df_ma200_up["Sector"] = df_ma200_up["Sector"].fillna("Unknown Sectors")
        df_ma200_up["Sector"] = df_ma200_up["Sector"].replace("-", "Others")

        # 📌 Chuẩn bị dữ liệu cho TreeMap
        df_ma200_up["Custom Data"] = df_ma200_up["Code"] + "<br> MA200 Change: " + df_ma200_up["MA200 Change"].round(
            2).astype(str) + "%"

        # 📌 Vẽ biểu đồ TreeMap với Plotly
        fig = px.treemap(
            df_ma200_up,
            path=['Sector', 'Code'],
            values=selected_date,  # Kích thước ô dựa trên giá trị đóng cửa
            color='MA200 Change',  # Màu sắc thể hiện mức độ thay đổi so với MA200
            hover_data=['Code', selected_date, "MA200 Change"],
            title=f"TreeMap - Cổ phiếu có MA200 đang tăng ({selected_date})",
            custom_data=['Custom Data'],
            color_continuous_scale='RdBu',
            color_continuous_midpoint=0
        )

        # 📌 Hiển thị mã cổ phiếu + % thay đổi trực tiếp trên TreeMap
        fig.update_traces(texttemplate='%{customdata[0]}')

        fig.update_layout(
            width=3200,
            height=700,
        )

        # 📌 Hiển thị biểu đồ trong Streamlit
        st.plotly_chart(fig)

        # 📌 Load dữ liệu


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


    def plot_price_change(df_price, tickers, selected_date, previous_date):
        """
        Vẽ biểu đồ Bar Chart % thay đổi giá trong ngày.
        """

        # 🔹 Kiểm tra nếu `previous_date` không có trong dữ liệu
        if previous_date not in df_price.columns:
            st.warning(
                f"⚠ Ngày {previous_date.date()} không có trong dữ liệu! Không thể tính % thay đổi giá trong ngày.")
            return

        df_filtered = df_price[df_price["Code"].isin(tickers)][["Code", selected_date, previous_date]].copy()

        # ✅ Tính toán % Change so với ngày trước đó
        df_filtered["% Change"] = ((df_filtered[selected_date] - df_filtered[previous_date]) / df_filtered[
            previous_date]) * 100

        # ✅ Vẽ Bar Chart
        fig = go.Figure(data=[
            go.Bar(x=df_filtered["Code"], y=df_filtered["% Change"],
                   text=df_filtered["% Change"].round(2), textposition='outside',
                   marker_color=["green" if x > 0 else "red" for x in df_filtered["% Change"]])
        ])

        fig.update_layout(title="📊 % Thay đổi giá trong ngày",
                          xaxis_title="Mã cổ phiếu", yaxis_title="% Change")

        st.plotly_chart(fig, use_container_width=True)


    def plot_price_change_period(df_price, tickers, selected_date, start_date):
        """
        Vẽ biểu đồ Bar Chart % thay đổi giá từ đầu kỳ (so với `start_date`).
        """

        # 🔹 Kiểm tra nếu `start_date` không có trong dữ liệu
        if start_date not in df_price.columns:
            st.warning(f"⚠ Ngày {start_date.date()} không có trong dữ liệu! Không thể tính % thay đổi giá từ đầu kỳ.")
            return

        df_filtered = df_price[df_price["Code"].isin(tickers)][["Code", selected_date, start_date]].copy()

        # ✅ Tính toán % Change so với ngày đầu kỳ
        df_filtered["% Change"] = ((df_filtered[selected_date] - df_filtered[start_date]) / df_filtered[
            start_date]) * 100

        # ✅ Vẽ Bar Chart
        fig = go.Figure(data=[
            go.Bar(x=df_filtered["Code"], y=df_filtered["% Change"],
                   text=df_filtered["% Change"].round(2), textposition='outside',
                   marker_color=["blue" if x > 0 else "orange" for x in df_filtered["% Change"]])
        ])

        fig.update_layout(
            title="📊 % Thay đổi giá từ đầu kỳ",
            xaxis_title="Mã cổ phiếu",
            yaxis_title="% Change",
            width=1200,  # Chiều rộng (px)
            height=600  # Chiều cao (px), nếu muốn
        )

        st.plotly_chart(fig, use_container_width=True)


    def calculate_highs(df_price, df_volume, selected_date):
        selected_date = pd.to_datetime(selected_date)
        df_price_sorted = df_price[df_price['Date'] < selected_date].sort_values(by='Date', ascending=False)
        df_price_valid = df_price_sorted.groupby('Code').head(260)
        df_price_max = df_price_valid.groupby('Code')['Value'].max().reset_index()
        df_price_max.columns = ['Code', 'H52W']

        df_latest = df_price[df_price['Date'] == selected_date][['Code', 'Value', 'Sector']]
        df_combined = df_latest.merge(df_price_max, on='Code', how='left').dropna(subset=['H52W'])
        df_combined['% Đỉnh 52W'] = ((df_combined['Value'] - df_combined['H52W']) / df_combined['H52W']) * 100

        df_new_highs = df_combined[df_combined['Value'] > df_combined['H52W']]
        df_new_highs['H52W'] = df_new_highs['Value']

        # 🔥 Chỉ lấy các cổ phiếu có % Đỉnh 52W < 10%
        df_near_highs = df_combined[(df_combined['% Đỉnh 52W'] > -10) & (df_combined['% Đỉnh 52W'] < 0)]

        df_volume_5_avg = df_volume[df_volume['Date'] < selected_date].groupby('Code').tail(5)
        df_volume_5_avg['GTGDQ5P'] = df_volume_5_avg['Value'] * df_volume_5_avg.groupby('Code')['Value'].transform(
            'mean')
        df_volume_5_avg = df_volume_5_avg.groupby('Code')['GTGDQ5P'].mean().reset_index()

        df_new_highs = df_new_highs.merge(df_volume_5_avg, on='Code', how='left')
        df_near_highs = df_near_highs.merge(df_volume_5_avg, on='Code', how='left')

        df_new_highs = df_new_highs[df_new_highs['GTGDQ5P'] >= 10000]
        df_new_highs = df_new_highs[df_new_highs['Sector'] != "-"]
        df_near_highs = df_near_highs[df_near_highs['Sector'] != "-"]

        for col in ['Value', 'H52W', '% Đỉnh 52W', 'GTGDQ5P']:
            df_new_highs[col] = df_new_highs[col].round(2)
            df_near_highs[col] = df_near_highs[col].round(2)

        df_new_highs = df_new_highs.sort_values(by='GTGDQ5P', ascending=False)
        df_near_highs = df_near_highs.sort_values(by='GTGDQ5P', ascending=False)

        return df_new_highs, df_near_highs


    def highlight_gradient(val):
        """Tô màu dải màu gradient cho % Đỉnh 52W với chữ màu trắng"""
        if pd.isna(val):
            return 'background-color: white; color: black; text-align: center;'

        # 🔥 Giới hạn phạm vi chỉ từ -10% đến 0%
        val = max(min(val, 0), -10)

        # Sử dụng thang màu sáng hơn để tránh quá đậm ở cuối
        color = px.colors.sample_colorscale("Viridis", (val + 10) / 12)  # Làm sáng màu

        # Nếu là danh sách lồng nhau, lấy phần tử đầu tiên
        if isinstance(color, list):
            color = color[0]

        # 🔥 Nếu `color` là chuỗi "rgb(x, y, z)", cần tách thành tuple (x, y, z)
        if isinstance(color, str) and color.startswith("rgb"):
            rgb_values = re.findall(r"[\d.]+", color)  # Lấy số từ chuỗi
            rgb_color = tuple(float(v) / 255 for v in rgb_values[:3])  # Chuyển về dạng (R, G, B)
        else:
            rgb_color = color[:3]  # Nếu đã là tuple, chỉ lấy 3 giá trị đầu

        # Chuyển RGB sang HEX
        hex_color = mcolors.to_hex(rgb_color)

        return f'background-color: {hex_color}; color: white; text-align: center;'


    def display_styled_table(df, title, show_percent_col=True, sort_by_percent=False):
        """Hiển thị bảng dữ liệu có màu gradient, căn giữa chữ và sắp xếp nếu cần"""
        if df.empty:
            st.warning(f"⚠ Không có dữ liệu cho {title}")
            return

        columns_to_show = ['Code', 'Value', 'H52W', '% Đỉnh 52W', 'GTGDQ5P', 'Sector'] if show_percent_col else ['Code',
                                                                                                                 'Value',
                                                                                                                 'H52W',
                                                                                                                 'GTGDQ5P',
                                                                                                                 'Sector']
        df = df[columns_to_show].copy()

        # 🔥 Nếu là bảng tiệm cận đỉnh, sort theo % Đỉnh 52W tăng dần
        if sort_by_percent:
            df = df.sort_values(by='% Đỉnh 52W', ascending=True)

        # 🔥 Giới hạn chỉ hiển thị 40 dòng
        df = df.head(40)

        styled_df = df.style.format(
            {'Value': "{:.2f}", 'H52W': "{:.2f}", '% Đỉnh 52W': "{:.2f}%", 'GTGDQ5P': "{:,.0f}"}) \
            .applymap(highlight_gradient, subset=['% Đỉnh 52W'] if '% Đỉnh 52W' in df.columns else []) \
            .set_properties(**{
            'text-align': 'center',  # Căn giữa tất cả nội dung
            'vertical-align': 'middle',  # Căn giữa theo chiều dọc
            'white-space': 'nowrap'  # Tránh bị xuống dòng
        }) \
            .bar(subset=['GTGDQ5P'], color='#3498db')

        st.write(f"📊 **{title}**")
        st.dataframe(styled_df)


    def display_sector_chart(df_near_highs):
        """Biểu đồ thanh thể hiện số lượng cổ phiếu tiệm cận đỉnh theo ngành (chỉ lấy top 10 ngành cao nhất)"""
        sector_counts = df_near_highs['Sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']
        sector_counts = sector_counts.head(10)

        fig = px.bar(
            sector_counts, x='Sector', y='Count', color='Sector',
            title="📊 SLCP Vượt & Tiệm Cận 10% Đỉnh 52T Theo Ngành (Top 10)",
            text_auto=True, color_discrete_sequence=px.colors.sequential.Plasma_r
        )

        fig.update_layout(
            xaxis_title="Ngành",
            yaxis_title="Số lượng CP",
            showlegend=False,
            xaxis=dict(tickangle=-45),
            plot_bgcolor='white'
        )
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
        # Stochastic Oscillator
        stochastic = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
        df['stochastic_%k'] = stochastic.stoch()
        df['stochastic_%d'] = stochastic.stoch_signal()
        # CCI
        for period in [10, 20, 30]:
            df[f'cci_{period}'] = (df['close'] - df['close'].rolling(period).mean()) / (
                    0.015 * df['close'].rolling(period).std())
        # Bollinger Bands
        bollinger = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_middle'] = bollinger.bollinger_mavg()
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_lower'] = bollinger.bollinger_lband()
        # ATR
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
        df['atr'] = atr.average_true_range()
        # Chaikin Volatility
        df['chaikin_volatility'] = (df['high'] - df['low']).ewm(span=10, adjust=False).mean().diff() / df['low'] * 100
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

        stochastic = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
        df['stochastic_%k'] = stochastic.stoch()
        df['stochastic_%d'] = stochastic.stoch_signal()

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

        # Điều chỉnh window cho ATR dựa trên số hàng có sẵn
        window_atr = 14 if n >= 14 else n
        if window_atr < 1:
            window_atr = 1  # Đảm bảo window không nhỏ hơn 1
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=window_atr)
        df['atr'] = atr.average_true_range()

        df['chaikin_volatility'] = (df['high'] - df['low']).ewm(span=10, adjust=False).mean().diff() / df['low'] * 100
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
            elif selected_indicator_combination == 'Bollinger Bands + Stochastic Oscillator':
                # Tạo subplots với 2 hàng: 1 hàng cho biểu đồ nến + Bollinger Bands, 1 hàng cho Stochastic Oscillator
                fig = make_subplots(
                    rows=2,
                    cols=1,
                    shared_xaxes=True,  # Dùng chung trục X
                    row_heights=[0.7, 0.3],  # Tỷ lệ chiều cao của các hàng
                    vertical_spacing=0.05,  # Khoảng cách giữa các hàng
                    subplot_titles=["Candlestick with Bollinger Bands", "Stochastic Oscillator"]
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

                # Vẽ Stochastic Oscillator trên subplot thứ 2 (hàng 2)
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['stochastic_%k'],
                        mode='lines',
                        name='Stochastic %K',
                        line=dict(color='green', width=2),
                        opacity=0.8,
                        yaxis='y2'
                    ),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['stochastic_%d'],
                        mode='lines',
                        name='Stochastic %D',
                        line=dict(color='orange', width=2, dash='dot'),
                        opacity=0.8,
                        yaxis='y2'
                    ),
                    row=2, col=1
                )

                # Thêm vùng quá mua và quá bán cho Stochastic
                fig.add_shape(
                    type='rect',
                    x0=df['Date'].min(),
                    x1=df['Date'].max(),
                    y0=80,
                    y1=100,
                    fillcolor='red',
                    opacity=0.2,
                    layer='below',
                    line_width=0,
                    yref='y2'
                )
                fig.add_shape(
                    type='rect',
                    x0=df['Date'].min(),
                    x1=df['Date'].max(),
                    y0=0,
                    y1=20,
                    fillcolor='green',
                    opacity=0.2,
                    layer='below',
                    line_width=0,
                    yref='y2'
                )

                # Tín hiệu MUA
                buy_signal = (
                        (df['close'] <= df['bb_lower']) &  # Giá chạm hoặc dưới dải dưới Bollinger Bands
                        (df['stochastic_%k'] < 20) &  # %K trong vùng quá bán
                        (df['stochastic_%k'] > df['stochastic_%d'])  # %K cắt lên %D
                )
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'][buy_signal],
                        y=df['close'][buy_signal],
                        mode='markers',
                        name='Buy Signal (BB + Stochastic)',
                        marker=dict(color='blue', size=20, symbol='triangle-up'),
                        opacity=0.8
                    ),
                    row=1, col=1
                )

                # Tín hiệu BÁN
                sell_signal = (
                        (df['close'] >= df['bb_upper']) &  # Giá chạm hoặc trên dải trên Bollinger Bands
                        (df['stochastic_%k'] > 80) &  # %K trong vùng quá mua
                        (df['stochastic_%k'] < df['stochastic_%d'])  # %K cắt xuống %D
                )
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'][sell_signal],
                        y=df['close'][sell_signal],
                        mode='markers',
                        name='Sell Signal (BB + Stochastic)',
                        marker=dict(color='orange', size=20, symbol='triangle-down'),
                        opacity=0.8
                    ),
                    row=1, col=1
                )

                # Thiết lập layout cho trục y thứ hai của Stochastic (hàng 2)
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
            # Tích hợp Stochastic Oscillator
            elif 'Stochastic Oscillator' in selected_indicators:
                # Tạo subplot với 2 hàng (1: Candlestick, 2: Stochastic Oscillator)
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                    row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và Stochastic Oscillator
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

                # Vẽ %K Line trong hàng 2
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['stochastic_%k'],
                    mode='lines',
                    name='%K Line',
                    line=dict(color='blue', width=2),
                    opacity=0.8
                ), row=2, col=1)

                # Vẽ %D Line trong hàng 2
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['stochastic_%d'],
                    mode='lines',
                    name='%D Line',
                    line=dict(color='orange', width=2, dash='dot'),
                    opacity=0.8
                ), row=2, col=1)

                # Vùng Overbought (Trên 80) trong hàng 2
                fig.add_shape(
                    type='rect',
                    xref='x2',  # Tham chiếu đến hàng thứ 2 (x-axis của hàng 2)
                    yref='y2',  # Tham chiếu đến hàng thứ 2 (y-axis của hàng 2)
                    x0=df['Date'].min(),
                    x1=df['Date'].max(),
                    y0=80,
                    y1=100,
                    fillcolor='red',
                    opacity=0.2,
                    layer='below',
                    line_width=0
                )

                # Vùng Oversold (Dưới 20) trong hàng 2
                fig.add_shape(
                    type='rect',
                    xref='x2',  # Tham chiếu đến hàng thứ 2
                    yref='y2',  # Tham chiếu đến hàng thứ 2
                    x0=df['Date'].min(),
                    x1=df['Date'].max(),
                    y0=0,
                    y1=20,
                    fillcolor='green',
                    opacity=0.2,
                    layer='below',
                    line_width=0
                )

                # Tín hiệu giao dịch: Crossovers
                buy_signals = (df['stochastic_%k'] > df['stochastic_%d']) & (
                        df['stochastic_%k'].shift(1) <= df['stochastic_%d'].shift(1))
                sell_signals = (df['stochastic_%k'] < df['stochastic_%d']) & (
                        df['stochastic_%k'].shift(1) >= df['stochastic_%d'].shift(1))

                # Vẽ tín hiệu MUA trong hàng 2
                fig.add_trace(go.Scatter(
                    x=df['Date'][buy_signals],
                    y=df['stochastic_%k'][buy_signals],
                    mode='markers',
                    name='Buy Signal (Stochastic)',
                    marker=dict(color='blue', size=20, symbol='triangle-up'),
                    opacity=0.8
                ), row=2, col=1)

                # Vẽ tín hiệu BÁN trong hàng 2
                fig.add_trace(go.Scatter(
                    x=df['Date'][sell_signals],
                    y=df['stochastic_%k'][sell_signals],
                    mode='markers',
                    name='Sell Signal (Stochastic)',
                    marker=dict(color='orange', size=20, symbol='triangle-down'),
                    opacity=0.8
                ), row=2, col=1)

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
            # Tích hợp ATR
            if 'ATR' in selected_indicators:
                # Tạo subplot với 2 hàng (1: Candlestick, 2: ATR)
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                    row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và ATR
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

                # Vẽ đường ATR ở hàng thứ 2
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['atr'],
                    mode='lines',
                    name='ATR',
                    line=dict(color='purple', width=2),
                    opacity=0.8
                ), row=2, col=1)

            # Tích hợp Chaikin Volatility
            if 'Chaikin Volatility' in selected_indicators:
                # Tạo subplot với 2 hàng (1: Candlestick, 2: Chaikin Volatility)
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.02,  # Khoảng cách giữa các hàng
                    row_heights=[0.7, 0.3]  # Tỷ lệ chiều cao giữa candlestick và CV
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

                # Vẽ đường Chaikin Volatility ở hàng thứ 2
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['chaikin_volatility'],
                    mode='lines',
                    name='Chaikin Volatility',
                    line=dict(color='orange', width=2),
                    opacity=0.8
                ), row=2, col=1)

                # Tín hiệu biến động tăng (High CV)
                high_cv = df['chaikin_volatility'] > df['chaikin_volatility'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(
                    x=df['Date'][high_cv],
                    y=df['chaikin_volatility'][high_cv],
                    mode='markers',
                    name='High CV (Potential Breakout)',
                    marker=dict(color='orange', size=20, symbol='triangle-up'),
                    opacity=0.8
                ), row=2, col=1)

                # Tín hiệu biến động giảm (Low CV)
                low_cv = df['chaikin_volatility'] < df['chaikin_volatility'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(
                    x=df['Date'][low_cv],
                    y=df['chaikin_volatility'][low_cv],
                    mode='markers',
                    name='Low CV (Potential Accumulation)',
                    marker=dict(color='blue', size=20, symbol='triangle-down'),
                    opacity=0.8
                ), row=2, col=1)

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


    # Phân tích kỹ thuật với MA
    # Đường dẫn đến file CSV trên backend
    FILE_PATH1 = "E:/GOI1/MSSV_CHAN_GOI1_GROUP1/MSSV_CHAN_GOI1_GROUP1/Data/Processed_Vietnam_Price.xlsx - Processed_Sheet2.csv"


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


    # 📌 Gọi hàm vẽ biểu đồ
    df_price, df_volume, date_columns = load_data()
    if subpage == "Tổng quan":
        st.markdown("<h2>📊 Tổng quan cho các mã</h2>", unsafe_allow_html=True)
        # 📌 Chọn ngày từ danh sách
        selected_date = select_date(date_columns)
        # 📌 Tạo bảng thống kê
        df_summary = create_summary_table(df_price, df_volume, selected_date)
        # Hiển thị bảng có màu sắc
        display_colored_table(df_summary)
        plot_treemap_ma200(df_price, selected_date)

    elif subpage == "So sánh cổ phiếu":
        if df_price is None or df_volume is None:
            st.stop()
        # ✅ Chuyển đổi `date_columns` thành `datetime`
        date_columns_dt = pd.to_datetime(date_columns, format="%Y-%m-%d", errors="coerce").dropna().sort_values()

        # ✅ Lấy `selected_date` từ `select_date()`
        selected_date = select_date(date_columns_dt)
        # ✅ Chọn mã cổ phiếu
        tickers = st.multiselect("Chọn các mã cổ phiếu để so sánh", df_price["Code"].unique(), default=["VIC", "HPG"])

        # ✅ Kiểm tra nếu không có mã nào được chọn
        if not tickers:
            st.warning("⚠ Vui lòng chọn ít nhất một mã cổ phiếu!")
            st.stop()

        # ✅ Chọn khoảng thời gian
        time_range = st.selectbox("Chọn khoảng thời gian",
                                  ["1 tuần", "1 tháng", "3 tháng", "6 tháng", "1 năm", "2 năm", "3 năm", "Toàn bộ"])
        # 🔹 Nếu ngày được chọn là ngày đầu tiên, cảnh báo và dừng lại
        if selected_date == date_columns_dt.min():
            st.warning("⚠ Ngày đầu tiên của bộ dữ liệu không thể chọn mốc thời gian trước đó.")
            st.stop()

        # ✅ Xác định ngày đầu kỳ theo khoảng thời gian
        time_ranges = {
            "1 tuần": selected_date - pd.DateOffset(weeks=1),
            "1 tháng": selected_date - pd.DateOffset(months=1),
            "3 tháng": selected_date - pd.DateOffset(months=3),
            "6 tháng": selected_date - pd.DateOffset(months=6),
            "1 năm": selected_date - pd.DateOffset(years=1),
            "2 năm": selected_date - pd.DateOffset(years=2),
            "3 năm": selected_date - pd.DateOffset(years=3),
            "Toàn bộ": date_columns_dt.min(),
        }
        start_date = time_ranges.get(time_range, date_columns_dt.min())

        # 🔹 Kiểm tra nếu `start_date` nhỏ hơn ngày nhỏ nhất trong dữ liệu
        if start_date < date_columns_dt.min():
            st.warning(f"⚠ Không có đủ dữ liệu để tính {time_range}! Đang chọn ngày sớm nhất có thể.")
            start_date = date_columns_dt.min()

        # ✅ Vẽ biểu đồ xu hướng giá theo mốc thời gian đã chọn
        plot_price_trend(df_price, tickers, selected_date, start_date, date_columns_dt)

        # ✅ Xác định ngày trước đó
        previous_date = date_columns_dt[date_columns_dt < selected_date].max()

        # 🔹 Kiểm tra nếu `previous_date` hợp lệ
        if pd.isna(previous_date):
            st.warning("⚠ Không có dữ liệu ngày trước đó để tính toán thay đổi giá.")
        elif previous_date in df_price.columns:
            plot_price_change(df_price, tickers, selected_date, previous_date)

        # ✅ Hiển thị % thay đổi giá từ đầu kỳ
        if start_date in df_price.columns:
            plot_price_change_period(df_price, tickers, selected_date, start_date)
    elif subpage == "Đỉnh của CP":
        df_price, df_volume = load_data2(file_price, file_volume)
        selected_date = select_date1(df_price)
        # Cổ phiếu đạt đỉnh, tiệm cận đỉnh
        df_new_highs, df_near_highs = calculate_highs(df_price, df_volume, selected_date)
        display_styled_table(df_new_highs, "📊 Danh sách CP tạo đỉnh mới 52T", show_percent_col=False)
        display_styled_table(df_near_highs, "📊 Danh sách CP tiệm cận đỉnh 52T (<10%)", show_percent_col=True)
        display_sector_chart(df_near_highs)
    elif subpage == "Chi tiết cổ phiếu":
        st.title("📈 Phân tích Chi Tiết Mã Cổ Phiếu")
        if df_price is None or df_volume is None:
            st.stop()

        # Chuyển đổi date_columns sang datetime
        date_columns_dt = pd.to_datetime(date_columns, format="%Y-%m-%d", errors="coerce").dropna().sort_values()
        # Lấy ngày kết thúc
        selected_date = select_date(date_columns_dt)
        # Hiển thị bảng snapshot chỉ báo
        df_snapshot = calculate_indicators_snapshot(df_price, df_volume, selected_date)
        if df_snapshot is not None:
            st.write("🔍 **Bảng chỉ báo kỹ thuật (snapshot)**")
            st.dataframe(df_snapshot)
            # Dropdown chọn mã cổ phiếu
            stock_list = df_snapshot['Code'].unique().tolist()

            selected_stock = st.selectbox("Chọn mã cổ phiếu", stock_list)
            if not selected_stock:
                st.warning("⚠ Vui lòng chọn ít nhất một mã cổ phiếu!")
                st.stop()
            # Dropdown chọn chỉ báo kỹ thuật
            indicators = [
                "SMA", "EMA", "MACD", "PSAR", "RSI", "Stochastic Oscillator",
                "CCI", "Bollinger Bands", "Chaikin Volatility", "OB", "MFI", "ATR"
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
                "Bollinger Bands + RSI", "Bollinger Bands + MACD", "Bollinger Bands + Stochastic Oscillator",
                "RSI + MACD"
            ]
            selected_combination = st.selectbox("Chọn tổ hợp chỉ báo", [None] + indicator_combinations)
            # Chọn khoảng thời gian (tính theo chuỗi thời gian từ dữ liệu Excel)
            time_range = select_time_period1()
            # Xác định ngày bắt đầu dựa trên khoảng thời gian được chọn
            time_ranges = {
                "1 tuần": selected_date - pd.DateOffset(weeks=1),
                "1 tháng": selected_date - pd.DateOffset(months=1),
                "3 tháng": selected_date - pd.DateOffset(months=3),
                "6 tháng": selected_date - pd.DateOffset(months=6),
                "1 năm": selected_date - pd.DateOffset(years=1),
                "2 năm": selected_date - pd.DateOffset(years=2),
                "3 năm": selected_date - pd.DateOffset(years=3),
                "Toàn bộ": date_columns_dt.min(),
            }
            start_date = time_ranges.get(time_range, date_columns_dt.min())
            if start_date < date_columns_dt.min():
                st.warning(f"⚠ Không có đủ dữ liệu để tính {time_range}! Đang chọn ngày sớm nhất có thể.")
                start_date = date_columns_dt.min()

            # Lấy chuỗi thời gian cho mã được chọn (sử dụng dữ liệu từ file Excel)
            df_ts = get_stock_timeseries(selected_stock, df_price, df_volume, date_columns_dt, start_date,
                                         selected_date)
            if df_ts is None or df_ts.empty:
                st.error("⚠ Không đủ dữ liệu thời gian cho mã được chọn.")
                st.stop()
            # Tính toán các chỉ báo trên chuỗi thời gian
            df_ts = compute_timeseries_indicators(df_ts)
            # Xây dựng biểu đồ dựa trên các lựa chọn
            fig = update_chart(df_ts, selected_stock, selected_indicators, selected_ma, selected_rsi, selected_cci,
                               selected_combination)
            st.plotly_chart(fig, use_container_width=True)
    elif subpage == "Phân tích thị trường với MA":
        st.title("Phân Tích Xu Hướng Thị Trường với chỉ số Moving Average (MA)")

        df_long = load_data_TA()
        ma_periods = [10, 20, 50, 100, 200]
        df_long = calculate_moving_averages(df_long, ma_periods)
        df_above_ma_final = count_stocks_above_ma(df_long, ma_periods)
        df_ma_increase_final = count_increasing_ma(df_long, ma_periods)

        # Chọn khoảng thời gian
        min_date = df_long["Date"].min()
        max_date = df_long["Date"].max()
        start_date, end_date = st.date_input("Chọn khoảng thời gian", [min_date, max_date], min_value=min_date,
                                             max_value=max_date)

        df_above_ma_final = df_above_ma_final.loc[start_date:end_date]
        df_ma_increase_final = df_ma_increase_final.loc[start_date:end_date]

        # Tạo layout 2x2 với Plotly Subplots
        fig = make_subplots(rows=2, cols=2, subplot_titles=[
            "SLCP có giá nằm trên các MA tương ứng (D)",
            "SLCP có MA tương ứng đang tăng (D)",
            "SLCP trend template ngày (D) và tuần (W)",
            "SLCP trend template và biến thiên (D)"
        ], specs=[[{}, {}], [{"secondary_y": False}, {"secondary_y": True}]])

        # Biểu đồ 1: Số lượng cổ phiếu có giá trên MA
        for ma in ma_periods:
            fig.add_trace(go.Scatter(x=df_above_ma_final.index, y=df_above_ma_final[f"Above_MA{ma}"], mode='lines',
                                     name=f"Above MA{ma}"), row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Số lượng CP", row=1, col=1)
        fig.update_layout(showlegend=True)

        # Biểu đồ 2: Số lượng cổ phiếu có MA tăng
        for ma in ma_periods:
            fig.add_trace(
                go.Scatter(x=df_ma_increase_final.index, y=df_ma_increase_final[f"Increase_MA{ma}"], mode='lines',
                           name=f"Increase MA{ma}"), row=1, col=2)
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_yaxes(title_text="Số lượng CP", row=1, col=2)

        # Biểu đồ 3: Xu hướng ngày và tuần
        df_trend = df_above_ma_final.mean(axis=1).rolling(window=10).mean()
        df_trend_weekly = df_above_ma_final.mean(axis=1).rolling(window=50).mean()
        fig.add_trace(
            go.Scatter(x=df_trend.index, y=df_trend, mode='lines', name="TrendTP_D", line=dict(color='orange')), row=2,
            col=1)
        fig.add_trace(go.Scatter(x=df_trend_weekly.index, y=df_trend_weekly, mode='lines', name="TrendTP_W",
                                 line=dict(color='blue')), row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Trend", row=2, col=1)

        # Biểu đồ 4: Xu hướng và biến thiên với 2 trục tung
        trend_diff = df_trend.diff().fillna(0)
        fig.add_trace(go.Bar(x=trend_diff.index, y=trend_diff, name="Biến thiên",
                             marker_color=['red' if x < 0 else 'green' for x in trend_diff]), row=2, col=2,
                      secondary_y=False)
        fig.add_trace(
            go.Scatter(x=df_trend.index, y=df_trend, mode='lines', name="TrendTP_D", line=dict(color='orange')), row=2,
            col=2, secondary_y=True)
        fig.update_xaxes(title_text="Date", row=2, col=2)
        fig.update_yaxes(title_text="Biến thiên", row=2, col=2, secondary_y=False)
        fig.update_yaxes(title_text="Trend", row=2, col=2, secondary_y=True)

        st.plotly_chart(fig)
