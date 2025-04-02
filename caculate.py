import numpy as np
import pandas as pd

# Hàm lấy giá trị từ transposed_df
def get_values(transposed_df, label):
    row = transposed_df[transposed_df["Chỉ tiêu"] == label]
    return row.iloc[:, 1:].values.flatten() if not row.empty else np.zeros(len(transposed_df.columns[1:]))

# Các chỉ tiêu cần thiết
labels = {
    "total_current_assets": [
        "CĐKT. TIỀN VÀ TƯƠNG ĐƯƠNG TIỀN",
        "CĐKT. ĐẦU TƯ TÀI CHÍNH NGẮN HẠN",
        "CĐKT. CÁC KHOẢN PHẢI THU NGẮN HẠN",
        "CĐKT. HÀNG TỒN KHO, RÒNG",
        "CĐKT. TÀI SẢN NGẮN HẠN KHÁC"
    ],
    "ppe": [
        "CĐKT. GTCL TSCĐ HỮU HÌNH",
        "CĐKT. GTCL TÀI SẢN THUÊ TÀI CHÍNH",
        "CĐKT. GTCL TÀI SẢN CỐ ĐỊNH VÔ HÌNH",
        "CĐKT. XÂY DỰNG CƠ BẢN DỞ DANG (TRƯỚC 2015)"
    ],
    "total_assets": [
        "CĐKT. TÀI SẢN NGẮN HẠN",
        "CĐKT. TÀI SẢN DÀI HẠN"
    ],
    "total_current_liabilities": ["CĐKT. NỢ NGẮN HẠN"],
    "total_long_term_debt": ["CĐKT. NỢ DÀI HẠN"],
    "total_liabilities": ["CĐKT. NỢ PHẢI TRẢ"],
    "net_income": ["KQKD. LỢI NHUẬN SAU THUẾ THU NHẬP DOANH NGHIỆP"],
    "interest_expense": ["KQKD. CHI PHÍ LÃI VAY"],
    "taxes": ["KQKD. CHI PHÍ THUẾ TNDN HIỆN HÀNH"],
    "depreciation_amortization": ["KQKD. KHẤU HAO TÀI SẢN CỐ ĐỊNH"],
    "revenue": ["KQKD. DOANH THU THUẦN"],
    "gross_profit": ["KQKD. LỢI NHUẬN GỘP VỀ BÁN HÀNG VÀ CUNG CẤP DỊCH VỤ"],
    "financial_expense": ["KQKD. CHI PHÍ TÀI CHÍNH"],
    "selling_expense": ["KQKD. CHI PHÍ BÁN HÀNG"],
    "admin_expense": ["KQKD. CHI PHÍ QUẢN LÝ DOANH NGHIỆP"],
    "total_equity": ["CĐKT. VỐN CHỦ SỞ HỮU"],
    "total_debt": ["CĐKT. NỢ PHẢI TRẢ"],
    "operating_profit": ["KQKD. LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH"],
    "other_profit": ["KQKD. LỢI NHUẬN KHÁC"],
    "jv_profit": ["KQKD. LÃI/ LỖ TỪ CÔNG TY LIÊN DOANH (TRƯỚC 2015)"],
    "other_income": ["KQKD. LỢI NHUẬN KHÁC"]
}

# Hàm tính các chỉ số
def calculate_financial_ratios(transposed_df):
    total_current_assets = sum(get_values(transposed_df, label) for label in labels["total_current_assets"])
    ppe = sum(get_values(transposed_df, label) for label in labels["ppe"])
    total_assets = sum(get_values(transposed_df, label) for label in labels["total_assets"])
    total_current_liabilities = get_values(transposed_df, labels["total_current_liabilities"][0])
    total_long_term_debt = get_values(transposed_df, labels["total_long_term_debt"][0])
    total_liabilities = get_values(transposed_df, labels["total_liabilities"][0])

    # Tính EBITDA
    net_income = get_values(transposed_df, labels["net_income"][0])
    interest_expense = get_values(transposed_df, labels["interest_expense"][0])
    taxes = get_values(transposed_df, labels["taxes"][0])
    depreciation_amortization = get_values(transposed_df, labels["depreciation_amortization"][0])
    ebitda = net_income + interest_expense + taxes + depreciation_amortization

    # Tính Net Income Before Taxes
    operating_profit = get_values(transposed_df, labels["operating_profit"][0])
    other_profit = get_values(transposed_df, labels["other_profit"][0])
    jv_profit = get_values(transposed_df, labels["jv_profit"][0])
    net_income_before_taxes = operating_profit + other_profit + jv_profit

    # Tính Net Income Before Extraordinary Items
    other_income = get_values(transposed_df, labels["other_income"][0])
    net_income_before_extraordinary_items = net_income + other_income

    # Tính Total Operating Expense
    revenue = get_values(transposed_df, labels["revenue"][0])
    gross_profit = get_values(transposed_df, labels["gross_profit"][0])
    financial_expense = get_values(transposed_df, labels["financial_expense"][0])
    selling_expense = get_values(transposed_df, labels["selling_expense"][0])
    admin_expense = get_values(transposed_df, labels["admin_expense"][0])
    total_operating_expense = revenue - gross_profit + financial_expense + selling_expense + admin_expense

    # Tính ROE, ROA, Income After Tax Margin, Revenue/Total Assets, Long Term Debt/Equity, Total Debt/Equity, ROS
    total_equity = get_values(transposed_df, labels["total_equity"][0])
    total_debt = get_values(transposed_df, labels["total_debt"][0])

    roe = np.divide(net_income, total_equity, out=np.zeros_like(net_income), where=total_equity != 0)
    roa = np.divide(net_income, total_assets, out=np.zeros_like(net_income), where=total_assets != 0)
    income_after_tax_margin = np.divide(net_income, revenue, out=np.zeros_like(net_income), where=revenue != 0)
    revenue_to_total_assets = np.divide(revenue, total_assets, out=np.zeros_like(revenue), where=total_assets != 0)
    long_term_debt_to_equity = np.divide(total_long_term_debt, total_equity, out=np.zeros_like(total_long_term_debt), where=total_equity != 0)
    total_debt_to_equity = np.divide(total_debt, total_equity, out=np.zeros_like(total_debt), where=total_equity != 0)
    ros = np.divide(net_income, revenue, out=np.zeros_like(net_income), where=revenue != 0)

    # Lấy danh sách các năm
    years = transposed_df.columns[1:]

    # Tạo DataFrame kết quả
    financial_ratios = pd.DataFrame({
        "Năm": years,
        "Total Current Assets": [f"{value:,.2f}" for value in total_current_assets],
        "Property/Plant/Equipment": [f"{value:,.2f}" for value in ppe],
        "Total Assets": [f"{value:,.2f}" for value in total_assets],
        "Total Current Liabilities": [f"{value:,.2f}" for value in total_current_liabilities],
        "Total Long-Term Debt": [f"{value:,.2f}" for value in total_long_term_debt],
        "Total Liabilities": [f"{value:,.2f}" for value in total_liabilities],
        "EBITDA": [f"{value:,.2f}" for value in ebitda],
        "Net Income Before Taxes": [f"{value:,.2f}" for value in net_income_before_taxes],
        "Net Income Before Extraordinary Items": [f"{value:,.2f}" for value in net_income_before_extraordinary_items],
        "Revenue": [f"{value:,.2f}" for value in revenue],
        "Total Operating Expense": [f"{value:,.2f}" for value in total_operating_expense],
        "Net Income After Taxes": [f"{value:,.2f}" for value in net_income],
        "ROE": [f"{value * 100:,.2f}" for value in roe],
        "ROA": [f"{value * 100:,.2f}" for value in roa],
        "ROS": [f"{value * 100:,.2f}" for value in ros],
        "Income After Tax Margin": [f"{value:,.2f}" for value in income_after_tax_margin],
        "Revenue/Total Assets": [f"{value * 100:,.2f}" for value in revenue_to_total_assets],
        "Long Term Debt/Equity": [f"{value * 100:,.2f}" for value in long_term_debt_to_equity],
        "Total Debt/Equity": [f"{value * 100:,.2f}" for value in total_debt_to_equity],
        "ROS": [f"{value * 100:,.2f}" for value in ros],
    })

    return financial_ratios
