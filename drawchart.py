import matplotlib.pyplot as plt
import numpy as np
from caculate import calculate_financial_ratios

# Hàm lấy giá trị từ transposed_df, luôn trả về mảng numpy hợp lệ
def get_values(transposed_df, label):
    row = transposed_df[transposed_df["Chỉ tiêu"] == label]
    if row.empty:
        return np.zeros(len(transposed_df.columns[1:]), dtype=float)
    values = row.iloc[:, 1:].fillna(0).values.flatten()
    return np.array(values, dtype=float)

# Hàm vẽ biểu đồ
def draw_chart(stock_code):
    # Lấy và xử lý dữ liệu
    from readdata import process_financial_data
    transposed_df = process_financial_data(stock_code)
    if transposed_df.empty:
        print(f"Không tìm thấy dữ liệu cho mã cổ phiếu {stock_code}")
        return

    financial_ratios = calculate_financial_ratios(transposed_df)

    years = transposed_df.columns[1:]
    sales_revenue = np.round(get_values(transposed_df, "KQKD. DOANH THU THUẦN")).astype(int)
    total_assets = np.round(get_values(transposed_df, "CĐKT. TỔNG CỘNG TÀI SẢN")).astype(int)
    equity = np.round(get_values(transposed_df, "CĐKT. VỐN CHỦ SỞ HỮU")).astype(int)

    colors = {"sales_revenue": "#003f87", "total_assets": "#38b6ff", "equity": "#ffc000"}
    bar_width = 0.25
    x = np.arange(len(years))

    plt.figure(figsize=(12, 6))
    plt.bar(x - bar_width, sales_revenue, width=bar_width, color=colors["sales_revenue"], label="Sales Revenue", zorder=3)
    plt.bar(x, total_assets, width=bar_width, color=colors["total_assets"], label="Total Assets", zorder=3)
    plt.bar(x + bar_width, equity, width=bar_width, color=colors["equity"], label="Equity", zorder=3)

    plt.ylim(0, max(max(sales_revenue), max(total_assets), max(equity)) * 1.15)
    for i in range(len(years)):
        plt.text(x[i] - bar_width, sales_revenue[i] * 1.01, f"{sales_revenue[i]:,}", ha="center", fontsize=9, color="black", fontweight="bold")
        plt.text(x[i], total_assets[i] * 1.01, f"{total_assets[i]:,}", ha="center", fontsize=9, color="black", fontweight="bold")
        plt.text(x[i] + bar_width, equity[i] * 1.01, f"{equity[i]:,}", ha="center", fontsize=9, color="black", fontweight="bold")

    plt.title(f"Revenue, Total Assets, Equity of {stock_code}", fontsize=16, weight="bold")
    plt.xticks(x, years, fontweight="bold", fontsize=12)

    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)

    plt.tick_params(axis="y", labelsize=12, left=False)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)

    import os
    output_dir = "images/output"
    os.makedirs(output_dir, exist_ok=True)
    file_name = os.path.join(output_dir, f"revenue_totalassets_equity_{stock_code}.png")
    plt.savefig(file_name, format="png", dpi=300)
    print(f"Biểu đồ đã được lưu tại {file_name}")

    plt.show()
    
    # Vẽ biểu đồ cấu trúc tài sản
    ts_ngan_han = get_values(transposed_df, "CĐKT. TÀI SẢN NGẮN HẠN")
    ts_dai_han = get_values(transposed_df, "CĐKT. TÀI SẢN DÀI HẠN")
    total_assets = ts_ngan_han + ts_dai_han
    current_assets = np.round((ts_ngan_han / total_assets) * 100, 1)
    non_current_assets = np.round((ts_dai_han / total_assets) * 100, 1)

    plt.figure(figsize=(14, 6))
    plt.bar(x, current_assets, color="#003f87", edgecolor='white', width=0.5, label="Current Assets", zorder=3)
    plt.bar(x, non_current_assets, bottom=current_assets, color="#ffc000", edgecolor='white', width=0.5, label="Non-current Assets", zorder=3)

    for i in range(len(x)):
        plt.text(x[i], current_assets[i] / 2, f"{current_assets[i]}%", ha='center', va='center', color='white', fontsize=12, fontweight="bold", zorder=4)
        plt.text(x[i], current_assets[i] + non_current_assets[i] / 2, f"{non_current_assets[i]}%", ha='center', va='center', color='black', fontsize=12, fontweight="bold", zorder=4)

    plt.title("ASSET STRUCTURE", fontsize=16, weight="bold")
    plt.xticks(x, years, fontweight="bold")
    plt.ylim(0, 100)

    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)

    plt.gca().set_yticks([])
    plt.gca().tick_params(axis='y', which='both', left=False)

    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2)

    file_name = os.path.join(output_dir, f"asset_structure_{stock_code}.png")
    plt.tight_layout()
    plt.savefig(file_name, format="png", dpi=300)
    print(f"Biểu đồ cấu trúc tài sản đã được lưu tại {file_name}")

    plt.tight_layout()
    plt.show()
    #Vẽ biểu đồ Biểu đồ Equity, ROE & ROA
    # Lấy dữ liệu
    years = transposed_df.columns[1:]
    equity = np.round(get_values(transposed_df, "CĐKT. VỐN CHỦ SỞ HỮU")).astype(int)
    net_income = get_values(transposed_df, "KQKD. LỢI NHUẬN SAU THUẾ THU NHẬP DOANH NGHIỆP")
    total_assets = get_values(transposed_df, "CĐKT. TỔNG CỘNG TÀI SẢN")

    # Tính ROE và ROA
    roe = np.divide(net_income, equity, out=np.zeros_like(net_income), where=equity != 0) * 100
    roe = np.round(roe, 1)
    roa = np.divide(net_income, total_assets, out=np.zeros_like(net_income), where=total_assets != 0) * 100
    roa = np.round(roa, 1)

    # Xác định trục y tối đa
    y_max_roe_roa = max(max(roe, default=0), max(roa, default=0)) * 1.2
    y_max_equity = max(equity, default=0) * 1.2

    # Màu sắc
    colors = {"equity": "#003f87", "roe": "#f57c00", "roa": "#ffc000"}

    # Vẽ biểu đồ
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # Cột Equity
    ax1.bar(years, equity, color=colors["equity"], edgecolor='white', width=0.4, label="Equity", zorder=3)
    for i in range(len(years)):
        ax1.text(i, equity[i] + y_max_equity * 0.02, f'{equity[i]:,.0f}', ha='center', va='bottom', color=colors["equity"], fontsize=11, fontweight='bold')

    # Thiết lập trục y cho Equity
    ax1.set_ylim(0, y_max_equity)
    ax1.tick_params(axis='both', which='both', length=0)
    ax1.yaxis.grid(True, linestyle="--", alpha=0.3, zorder=1)
    for spine in ['top', 'left', 'right', 'bottom']:
        ax1.spines[spine].set_visible(False)

    # Trục y thứ 2 cho ROE và ROA
    ax2 = ax1.twinx()
    ax2.set_ylim(0, y_max_roe_roa)
    ax2.tick_params(axis='both', which='both', length=0)
    for spine in ['top', 'left', 'right']:
        ax2.spines[spine].set_visible(False)

    # Đường ROE và ROA
    ax2.plot(years, roe, color=colors["roe"], marker='o', label="ROE (%)", linewidth=2.2, zorder=4)
    ax2.plot(years, roa, color=colors["roa"], marker='o', label="ROA (%)", linewidth=2.2, zorder=4)

    # Thêm số liệu vào ROE & ROA
    for i in range(len(years)):
        ax2.text(i, roe[i] + 1, f'{roe[i]:.1f}%', ha='center', va='bottom', color=colors["roe"], fontsize=11, fontweight='bold')
        ax2.text(i, roa[i] - 2, f'{roa[i]:.1f}%', ha='center', va='top', color=colors["roa"], fontsize=11, fontweight='bold')

    # Thiết lập tiêu đề và trục x
    plt.title("EQUITY, ROE & ROA OF THE GROUP OVER YEARS", fontsize=16, weight="bold", fontname="Arial")
    ax1.set_xticks(np.arange(len(years)))
    ax1.set_xticklabels([f'{year}' for year in years], fontweight='bold', fontsize=12)

    # Chú thích
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=11)

    # Lưu biểu đồ
    import os
    output_dir = "images/output"
    os.makedirs(output_dir, exist_ok=True)
    file_name = os.path.join(output_dir, f"equity_roe_roa_{stock_code}.png")
    plt.tight_layout()
    plt.savefig(file_name, format="png", dpi=300)
    print(f"Biểu đồ Equity, ROE & ROA đã được lưu tại {file_name}")

    # Hiển thị biểu đồ
    plt.tight_layout()
    plt.show()
   #Vẽ biểu đồ Income After Tax Margin
    # Lấy dữ liệu lợi nhuận và doanh thu
    net_income = get_values(transposed_df, "KQKD. LỢI NHUẬN SAU THUẾ THU NHẬP DOANH NGHIỆP")
    revenue = get_values(transposed_df, "KQKD. DOANH THU THUẦN")

    # Tính Income After Tax Margin (%)
    income_after_tax_margin = np.divide(net_income, revenue, out=np.zeros_like(net_income), where=revenue != 0) * 100
    income_after_tax_margin = np.round(income_after_tax_margin, 1)

    # Lọc ra các năm 2020-2024
    selected_years = ["2020", "2021", "2022", "2023", "2024"]
    mask = np.isin(years, selected_years)

    years = years[mask]
    net_income = net_income[mask]
    revenue = revenue[mask]
    income_after_tax_margin = income_after_tax_margin[mask]

    # Màu sắc
    colors = {
        "revenue": "#003f87",
        "net_income": "#ffc000",
        "margin": "#f57c00"
    }

    # Tạo biểu đồ
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Vẽ cột doanh thu và lợi nhuận
    bar_width = 0.4
    x = np.arange(len(years))

    bars1 = ax1.bar(x - bar_width / 2, revenue, color=colors["revenue"], width=bar_width, label="Revenue", zorder=3)
    bars2 = ax1.bar(x + bar_width / 2, net_income, color=colors["net_income"], width=bar_width, label="Net Profit After Tax", zorder=3)

    # Thêm số liệu lên cột
    for i in range(len(years)):
        ax1.text(x[i] - bar_width / 2, revenue[i] + 5000, f'{revenue[i]:,.0f}', ha='center', color=colors["revenue"], fontweight='bold', fontsize=10)
        ax1.text(x[i] + bar_width / 2, net_income[i] + 2000, f'{net_income[i]:,.0f}', ha='center', color=colors["net_income"], fontweight='bold', fontsize=10)

    # Thiết lập trục y cho doanh thu và lợi nhuận
    ax1.set_ylim(0, max(revenue) * 1.2)

    # Tạo trục y thứ hai cho Income After Tax Margin (%)
    ax2 = ax1.twinx()
    ax2.set_ylim(0, max(income_after_tax_margin) * 1.2)

    # Vẽ đường Income After Tax Margin (%)
    line1 = ax2.plot(x, income_after_tax_margin, color=colors["margin"], marker='o', linewidth=2.2, label="Income After Tax Margin (%)", zorder=4)

    # Thêm số liệu trên đường
    for i in range(len(years)):
        ax2.text(x[i], income_after_tax_margin[i] + 1, f'{income_after_tax_margin[i]:.1f}%', ha='center', color=colors["margin"], fontweight='bold', fontsize=10)

    # Thiết lập tiêu đề và nhãn trục X
    plt.title("INCOME AFTER TAX MARGIN", fontsize=14, weight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, fontweight='bold', fontsize=12)

    # Giữ lại số trên trục tung
    ax1.tick_params(axis='y', labelsize=10)
    ax2.tick_params(axis='y', labelsize=10)

    # Xóa tất cả ticks mark
    ax1.tick_params(axis='both', length=0)
    ax2.tick_params(axis='both', length=0)

    # Xóa viền trái, phải, trên
    for spine in ["top", "left", "right"]:
        ax1.spines[spine].set_visible(False)
        ax2.spines[spine].set_visible(False)

    # Chú thích xuống đáy
    bars_labels = [bars1, bars2, line1[0]]
    labels = [b.get_label() for b in bars_labels]
    ax1.legend(bars_labels, labels, loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=10)

    # Đường lưới ngang nhẹ
    ax1.grid(axis='y', linestyle='--', alpha=0.5, zorder=1)

    # Lưu biểu đồ
    import os
    output_dir = "images/output"
    os.makedirs(output_dir, exist_ok=True)
    file_name = os.path.join(output_dir, f"income_after_tax_margin_{stock_code}.png")
    plt.tight_layout()
    plt.savefig(file_name, format="png", dpi=300)
    print(f"Biểu đồ Income After Tax Margin đã được lưu thành công tại {file_name}")

    # Hiển thị biểu đồ
    plt.tight_layout()
    plt.show()

