import os
import datetime as dt
from fpdf import FPDF
from dotenv import load_dotenv
import requests
from datetime import datetime
import tempfile
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
from readdata import *
from caculate import calculate_financial_ratios
from drawchart import draw_chart
from pdf_instance import get_pdf_instance

# Hàm tạo PDF
def generate_pdf(stock_code, pdf = None):
    # Lấy dữ liệu tài chính
    transposed_df = process_financial_data(stock_code)
    if transposed_df.empty:
        print(f"Không tìm thấy dữ liệu cho mã cổ phiếu {stock_code}")
        return
    
    return_pdf = False if pdf is None else True

    # Tính các chỉ số tài chính
    financial_ratios = calculate_financial_ratios(transposed_df)

    # Thông tin công ty
    today = dt.date.today()
    company_name = transposed_df.iloc[1]['2024']
    stock_symbol = transposed_df.iloc[0]['2024']
    exchange_code = transposed_df.iloc[2]['2024']
    industry = " - ".join(map(str, transposed_df.iloc[3:7]['2024'].values))

    # Dữ liệu thông tin chung
    general_info = [
        ("Tên công ty", company_name),
        ("Mã chứng khoán", stock_symbol),
        ("Sàn giao dịch", exchange_code),
        ("Ngành (ICB)", industry)
    ]

    # Dữ liệu bảng tài chính
    balance_sheet_data = {
        "Total Current Assets": financial_ratios["Total Current Assets"],
        "Property/Plant/Equipment": financial_ratios["Property/Plant/Equipment"],
        "Total Assets": financial_ratios["Total Assets"],
        "Total Current Liabilities": financial_ratios["Total Current Liabilities"],
        "Total Long-Term Debt": financial_ratios["Total Long-Term Debt"],
        "Total Liabilities": financial_ratios["Total Liabilities"]
    }

    fundamental_data = {
        "EBITDA": financial_ratios["EBITDA"]
    }

    income_statement_data = {
        "Revenue": financial_ratios["Revenue"],
        "Total Operating Expense": financial_ratios["Total Operating Expense"],
        "Net Income Before Taxes": financial_ratios["Net Income Before Taxes"],
        "Net Income After Taxes": financial_ratios["Net Income After Taxes"],
        "Net Income Before Extraordinary Items": financial_ratios["Net Income Before Extraordinary Items"]
    }

    profitability_analysis_data = {
        "ROE, %": financial_ratios["ROE"],
        "ROA, %": financial_ratios["ROA"],
        "Income After Tax Margin, %": financial_ratios["Income After Tax Margin"],
        "Revenue/Total Assets, %": financial_ratios["Revenue/Total Assets"],
        "Long Term Debt/Equity, %": financial_ratios["Long Term Debt/Equity"],
        "Total Debt/Equity, %": financial_ratios["Total Debt/Equity"],
        "ROS, %": financial_ratios["ROS"]
    }

    # Danh sách năm
    years = list(transposed_df.columns[1:])

    if pdf is None:
        pdf = get_pdf_instance()

    pdf.add_page()
    pdf.create_table("BALANCE SHEET", balance_sheet_data, years,header_color=(128, 0, 0) )
    pdf.create_table("FUNDAMENTAL", fundamental_data, years, header_color=(0, 128, 0))
    pdf.create_table("INCOME STATEMENT", income_statement_data, years, header_color=(76, 0, 153))
    pdf.create_table("PROFITABILITY ANALYSIS", profitability_analysis_data, years, header_color=(0, 102, 204))
    import os
    import google.generativeai as genai
    import requests
    from dotenv import load_dotenv

    # Tải API key từ file môi trường
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    # Kiểm tra xem API key có tồn tại không
    if not api_key:
        raise ValueError("API Key chưa được đặt. Vui lòng kiểm tra file .env")

    # Cấu hình model Google Gemini
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction="Chatbot này sẽ hoạt động như một broker chứng khoán chuyên nghiệp..."
    )

    # Kiểm tra nếu các biến dữ liệu chưa được khai báo
    balance_sheet = balance_sheet_data
    income_statement = income_statement_data
    profitability_analysis = profitability_analysis_data

    # Thêm thông tin chung và bảng BALANCE SHEET trên cùng một trang
    pdf.chapter_title("THÔNG TIN CHUNG")
    pdf.set_font("DejaVu", size=12)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    # Tạo nội dung prompt
    prompt = f""" 
    Bạn là một chuyên gia phân tích tài chính chuyên về phân tích cơ bản cổ phiếu. Hãy đánh giá rủi ro và triển vọng đầu tư của mã cổ phiếu dựa trên các chỉ số tài chính và thông tin sau.
    Giữ văn phong chuyên nghiệp và báo cáo dưới 300 từ.

    Cho các dữ liệu báo cáo tài chính sau:  
    Bảng cân đối kế toán (Balance Sheet):
    {balance_sheet}  
    Báo cáo thu nhập (Income Statement):
    {income_statement}  
    Phân tích khả năng sinh lời (Profitability Analysis):
    {profitability_analysis} 
    Hãy lấy các chỉ số tài chính từ các dữ liệu trên và đánh giá rủi ro và triển vọng đầu tư của mã cổ phiếu. kkhi đưa ra so sánh hoặc đánh giá nên trích dẫn số liệu cụ thể.
    Nhận xét với văn phong và từ ngữ nên được tham khảo sau đây, khi đưa ra so sánh hoặc đánh giá nên trích dẫn số liệu cụ thể lấy từ dữ liệu đã chocho:
    Yêu cầu phân tích:

    - PHÂN TÍCH TÀI CHÍNH:
    Một đoạn văn dưới 200 từ, phân tích các chỉ số tài chính quan trọng sau:
    Doanh thu và Lợi nhuận ròng: Xu hướng tăng trưởng qua các năm.
    Biên lợi nhuận gộp (Gross Margin), biên lợi nhuận ròng (Net Profit Margin): So sánh với trung bình ngành.
    Tỷ lệ giá trên thu nhập (P/E): Tỷ lệ này đo lường mối quan hệ giữa giá cổ phiếu và thu nhập của công ty. P/E càng cao thì cổ phiếu càng được định giá cao.
    Tỷ lệ giá trên giá trị sổ sách (P/B): Tỷ lệ này đo lường mối quan hệ giữa giá cổ phiếu và giá trị sổ sách của công ty. P/B càng thấp thì cổ phiếu càng được định giá thấp.
    Tỷ lệ lợi nhuận trên vốn chủ sở hữu (ROE): Tỷ lệ này đo lường khả năng sinh lời của công ty trên vốn chủ sở hữu. ROE càng cao thì công ty càng có khả năng tạo ra lợi nhuận.
    Tỷ lệ lợi nhuận trên tài sản (ROA): Tỷ lệ này đo lường khả năng sinh lời của công ty trên tổng tài sản. ROA càng cao thì công ty càng có khả năng tạo ra lợi nhuận từ tài sản của mình.
    Tỷ lệ nợ trên vốn chủ sở hữu (D/E): Tỷ lệ này đo lường mức độ đòn bẩy tài chính của công ty. D/E càng cao thì công ty càng phụ thuộc vào nợ vay.
    EBITDA: EBITDA là chỉ số đo lường lợi nhuận trước thuế, lãi vay, khấu hao và chi phí khấu hao.
    Hãy đưa ra nhận xét ngắn gọn về tình hình tài chính.

    - PHÂN TÍCH RỦI RO:
    Đoạn văn dưới 200 từ đánh giá được rủi ro tài chính (nợ vay, thanh khoản, dòng tiền).

    - ĐÁNH GIÁ TRIỂN VỌNG ĐẦU TƯ:
    Đoạn văn ngắn đánh giá ttiềm năng tăng trưởng lợi nhuận và biên lợi nhuận.

    Định dạng đầu ra mong muốn: Đoạn văn nhận xét súc tích, logic (khoảng bé hơnhơn 300 từ)
    Có kết luận rõ ràng về tiềm năng đầu tư của HPG.
    """

    headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


    try:
        response = model.generate_content(prompt)
        result = response.text
        formatted_comment = result.replace("*", "")
        print("API Response:", formatted_comment)  # Kiểm tra phản hồi từ API
    except Exception as e:
        print(f"Lỗi khi gọi API: {str(e)}")
        
    # Khởi tạo đối tượng PDF
    # pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Thêm thông tin chung và bảng BALANCE SHEET trên cùng một trang
    pdf.chapter_title("THÔNG TIN CHUNG")
    pdf.set_font("DejaVu", size=12)
    pdf.set_text_color(0, 0, 0)  # Màu chữ đen
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    info = [
        f"🏢 Tên công ty: {company_name}",
        f"📈 Mã cổ phiếu: {stock_symbol}",
        f"🏛️ Sàn giao dịch: {exchange_code}"
    ]

    # Dùng pdf.cell() cho các dòng ngắn
    for line in info:
        pdf.cell(0, 10, line, ln=True)

    # Dùng pdf.multi_cell() cho dòng dài
    pdf.multi_cell(0, 10, f"🏭 Ngành nghề: {industry}")
    pdf.ln(5)  # Giảm khoảng cách giữa phần thông tin và bảng
    
    # Thêm bảng BALANCE SHEET ngay trên cùng trang
    pdf.create_table("BALANCE SHEET", balance_sheet_data, years,header_color=(128, 0, 0) )
    pdf.create_table("FUNDAMENTAL", fundamental_data, years, header_color=(0, 128, 0))
    pdf.create_table("INCOME STATEMENT", income_statement_data, years, header_color=(76, 0, 153))
    pdf.create_table("PROFITABILITY ANALYSIS", profitability_analysis_data, years, header_color=(0, 102, 204))

    # Thêm 4 biểu đồ vào PDF
    pdf.add_page()
    pdf.chapter_title("BIỂU ĐỒ.")
    pdf.image(f"images/output/revenue_totalassets_equity_{stock_code}.png", x=45, y=35, w=120, h=100)
    pdf.image(f"images/output/asset_structure_{stock_code}.png", x=45, y=145, w=120, h=100)

    pdf.add_page()
    pdf.chapter_title("BIỂU ĐỒ")
    pdf.image(f"images/output/equity_roe_roa_{stock_code}.png", x=45, y=35, w=120, h=100)
    pdf.image(f"images/output/income_after_tax_margin_{stock_code}.png", x=45, y=145, w=120, h=100)

   # Trang cuối: Nhận xét từ AI
    pdf.add_page()
    pdf.chapter_title("NHẬN XÉT TÀI CHÍNH TỪ AI")

    # Thiết lập font mặc định là DejaVu Sans, cỡ chữ 13
    pdf.set_font("DejaVu", size=12)
    pdf.set_text_color(0, 0, 0)  # Màu chữ đen
    # Chèn nhận xét đã được định dạng (xóa dấu *) vào PDF
    pdf.multi_cell(0, 10, formatted_comment)
    
    if return_pdf is False:
        # Xuất file PDF
        pdf_filename = f"{stock_symbol}_FINANCIAL_REPORT.pdf"
        pdf.output(pdf_filename)
        print(f"PDF file created successfully: {pdf_filename}")
        os.startfile(pdf_filename)
    else:
        return pdf
