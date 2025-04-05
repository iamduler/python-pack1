from fpdf import FPDF
import datetime as datetime

def get_pdf_instance():
	# Tạo lớp PDF kế thừa từ FPDF
	class PDF(FPDF):

		def header(self):
			# Thêm phông chữ 
			pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)  # Regular
			pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)  # Bold
			pdf.add_font("DejaVu", "I", "DejaVuSans-Oblique.ttf", uni=True)  # Italic
			pdf.add_font("DejaVu", "BI", "DejaVuSans-BoldOblique.ttf", uni=True)  # Bold Italic
			
			self.set_fill_color(0, 0, 128)  # Màu xanh navy (#000080)
			self.rect(0, 0, self.w, 28, 'F')# Tô nền header toàn trang (cao 20px) 
			# Sử dụng phông chữ DejaVu Sans, cỡ 16
			self.set_text_color(255, 255, 255)  # Màu xám đậm (RGB: 64, 64, 64)
			self.set_font('DejaVu', 'B', 16)
			# self.cell(0, 10, company_name.upper(), 0, 1, 'R')  # Chuyển thành chữ hoa và căn phải

			# Dòng chứa Document Date, căn lề phải
			today = datetime.date.today()
			self.set_font('DejaVu', '', 10)  # Phông chữ DejaVu Sans, cỡ 8 cho Document Date
			self.cell(0, 5, f"Document Date: {today.strftime('%d-%b-%Y')}", 0, 1, 'R')

			self.ln(8)  # Thêm một khoảng trống nhỏ sau phần header
			
		def footer(self):
			# Vị trí 1.5 cm từ đáy trang
			self.set_y(-10)
			self.set_font('DejaVu', 'I', 8)  # Phông chữ nghiêng
			# Sử dụng `new_x` và `new_y` thay cho `ln` để không gặp cảnh báo DeprecationWarning
			self.cell(0, 5, f'Page {self.page_no()} of {{nb}}', 0, 1, 'C', new_x='RIGHT', new_y='NEXT')
		
		def chapter_title(self, title):
			self.set_text_color(0, 0, 128)  # Màu xanh dương cho chữ
			self.set_font('DejaVu', 'B', 13)  # Phông chữ đậm, cỡ 12 cho tiêu đề
			self.cell(0, 5, title, 0, 1, 'L')  # Title căn trái
			self.ln(5)

		def create_table_information(self, data): 
			
			# Vẽ đường nét đứt phía trên bảng
			self.set_draw_color(0, 0, 0)  # Màu xám đậm cho đường kẻ
			self.dashed_line(10, self.get_y(), 200, self.get_y(), 1, 1)  # (x1, y1, x2, y2, độ dài nét, khoảng cách)

			self.set_text_color(0, 0, 0)  # Màu chữ mặc định (đen)
			row_count = 0

			for item in data:
				# Tô màu nền xanh pastel cho hàng chẵn
				if row_count % 2 == 0:
					self.set_fill_color(230, 240, 250)  # Màu xanh pastel 
				else:
					self.set_fill_color(255, 255, 255)  # Màu trắng
		
				# Cột "Thông tin" có chữ xám đậm
				self.set_text_color(0, 0, 0)  # Màu xám 
				self.set_font('DejaVu', 'B', 8)  # Đậm hơn một chút

				self.cell(50, 6, item[0], 0, 0, 'L', fill=True)  

				# Cột "Giá trị" trở về màu đen bình thường
				self.set_text_color(0, 0, 0)  
				self.set_font('DejaVu', '', 8)  # Chữ thường

				self.cell(140, 6, item[1], 0, 1, 'L', fill=True)  

				row_count += 1
			# Vẽ đường nét đứt phía dưới bảng
			self.set_draw_color(0, 0, 0)
			end_y = self.get_y()  # Lưu vị trí kết thúc bảng
			self.dashed_line(10, end_y, 200, end_y, 1, 1)  # Đường nét đứt ngang
			
			self.ln(8)  # Thêm một khoảng trống sau bảng
		
		def create_table(self, title, data, years, header_color):
			self.set_font("DejaVu", "B", 8)

			# Chiều rộng trang A4 = 210mm, trừ đi lề 2 bên (10mm mỗi bên)
			page_width = 210 - 20  # 190mm là không gian sử dụng được
			col_width = page_width * 0.35  # 35% chiều rộng cho cột đầu tiên
			year_width = (page_width * 0.65) / len(years)  # 65% còn lại chia đều cho các năm

			self.set_x(10)  # Đặt vị trí x để bảng căn sát lề trái

			# Tiêu đề bảng trong ô đầu tiên với màu nền theo yêu cầu
			self.set_fill_color(*header_color)  # Đặt màu nền theo bảng cụ thể
			self.set_text_color(255, 255, 255)  # Màu chữ trắng cho dòng đầu tiên
			self.cell(col_width, 6, title, 0, 0, "L", fill=True)  # Không có viền
			for year in years:
				self.cell(year_width, 6, year, 0, 0, "R", fill=True)  # Căn phải
			self.ln()

			# In dữ liệu từng hàng
			self.set_x(10)  # Đảm bảo từng hàng bắt đầu từ lề trái
			self.set_font("DejaVu", "", 8)
			self.set_text_color(0, 0, 0)  # Đặt lại màu chữ đen cho các dòng tiếp theo
			row_count = 0
			line_height = 6

			for key, values in data.items():
				# Tô màu xen kẽ cho từng dòng (trừ dòng đầu tiên)
				self.set_fill_color(230, 240, 250) if row_count % 2 == 0 else self.set_fill_color(255, 255, 255)

				# In cột đầu tiên
				self.cell(col_width, line_height, key, 0, 0, "L", fill=True)

				# In dữ liệu theo từng năm (không viền, căn phải)
				for value in values:
					self.cell(year_width, line_height, value, 0, 0, "R", fill=True)
				self.ln()
				row_count += 1

			self.ln(10)  # Tạo khoảng trống 10mm giữa các bảng

	pdf = PDF()

	return pdf