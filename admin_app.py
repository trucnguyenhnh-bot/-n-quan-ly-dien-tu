import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU (Chạy lần đầu sẽ tự tạo file db)
# ==========================================
def init_db():
    conn = sqlite3.connect('electronics_store.db')
    c = conn.cursor()
    # Tạo bảng Sản phẩm (Mô phỏng DB đồ điện tử)
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            imei TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Hàm hỗ trợ chạy lệnh SQL
def run_query(query, params=()):
    conn = sqlite3.connect('electronics_store.db')
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    data = c.fetchall()
    conn.close()
    return data

# Khởi tạo DB khi chạy app
init_db()

# ==========================================
# 2. GIAO DIỆN QUẢN TRỊ (ADMIN DASHBOARD)
# ==========================================
st.set_page_config(page_title="Admin Panel - Cửa Hàng Điện Tử", layout="wide")
st.title("⚙️ Hệ Thống Quản Trị Cửa Hàng (Admin)")

# Menu bên trái
menu = st.sidebar.selectbox("Chọn chức năng:", ["🔍 Tra cứu Sản phẩm", "➕ Thêm Sản phẩm mới", "✏️ Chỉnh sửa / Xóa"])

# ------------------------------------------
# CHỨC NĂNG 1: TRA CỨU
# ------------------------------------------
if menu == "🔍 Tra cứu Sản phẩm":
    st.header("Tra cứu thông tin theo IMEI hoặc Tên")
    search_term = st.text_input("Nhập mã IMEI hoặc Tên sản phẩm:")
    
    if st.button("Tìm kiếm"):
        query = "SELECT * FROM products WHERE imei LIKE ? OR name LIKE ?"
        results = run_query(query, (f'%{search_term}%', f'%{search_term}%'))
        
        if results:
            df = pd.DataFrame(results, columns=["ID", "Tên Sản Phẩm", "Số IMEI/Serial", "Giá Bán", "Trạng Thái"])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Không tìm thấy sản phẩm nào!")
            
    st.markdown("---")
    st.subheader("Tất cả sản phẩm trong kho")
    all_data = run_query("SELECT * FROM products")
    if all_data:
        df_all = pd.DataFrame(all_data, columns=["ID", "Tên Sản Phẩm", "Số IMEI/Serial", "Giá Bán", "Trạng Thái"])
        st.dataframe(df_all, use_container_width=True)

# ------------------------------------------
# CHỨC NĂNG 2: THÊM MỚI (CREATE)
# ------------------------------------------
elif menu == "➕ Thêm Sản phẩm mới":
    st.header("Nhập kho sản phẩm mới")
    
    with st.form("add_form"):
        name = st.text_input("Tên sản phẩm (VD: iPhone 15 Pro Max)")
        imei = st.text_input("Mã IMEI / Serial (Duy nhất)")
        price = st.number_input("Giá bán (VNĐ)", min_value=0, step=100000)
        status = st.selectbox("Trạng thái", ["Còn hàng", "Đã bán", "Đang bảo hành"])
        
        submit = st.form_submit_button("Thêm vào Cơ sở dữ liệu")
        
        if submit:
            if name and imei:
                try:
                    run_query("INSERT INTO products (name, imei, price, status) VALUES (?, ?, ?, ?)", 
                              (name, imei, price, status))
                    st.success(f"Đã thêm thành công: {name} (IMEI: {imei})")
                except sqlite3.IntegrityError:
                    st.error("Lỗi: Mã IMEI này đã tồn tại trong hệ thống!")
            else:
                st.error("Vui lòng nhập đầy đủ Tên và IMEI.")

# ------------------------------------------
# CHỨC NĂNG 3: CHỈNH SỬA / XÓA (UPDATE / DELETE)
# ------------------------------------------
elif menu == "✏️ Chỉnh sửa / Xóa":
    st.header("Cập nhật thông tin sản phẩm")
    
    # Lấy danh sách sản phẩm để chọn
    all_products = run_query("SELECT id, name, imei FROM products")
    if not all_products:
        st.info("Kho dữ liệu đang trống.")
    else:
        # Tạo dict để hiển thị tên đẹp trong ô dropdown
        product_dict = {f"{p[1]} - IMEI: {p[2]} (ID: {p[0]})": p[0] for p in all_products}
        selected_product = st.selectbox("Chọn sản phẩm cần sửa:", list(product_dict.keys()))
        
        product_id = product_dict[selected_product]
        
        # Lấy dữ liệu cũ của sản phẩm được chọn
        current_data = run_query("SELECT name, imei, price, status FROM products WHERE id = ?", (product_id,))[0]
        
        with st.form("edit_form"):
            st.write("Sửa thông tin:")
            new_name = st.text_input("Tên sản phẩm", value=current_data[0])
            new_imei = st.text_input("IMEI", value=current_data[1])
            new_price = st.number_input("Giá bán", value=float(current_data[2]), step=100000.0)
            
            # Cài đặt giá trị mặc định cho selectbox
            status_options = ["Còn hàng", "Đã bán", "Đang bảo hành"]
            current_status_index = status_options.index(current_data[3]) if current_data[3] in status_options else 0
            new_status = st.selectbox("Trạng thái", status_options, index=current_status_index)
            
            col1, col2 = st.columns(2)
            with col1:
                update_btn = st.form_submit_button("Lưu thay đổi", type="primary")
            with col2:
                delete_btn = st.form_submit_button("Xóa sản phẩm này")
                
            if update_btn:
                try:
                    run_query("UPDATE products SET name=?, imei=?, price=?, status=? WHERE id=?", 
                              (new_name, new_imei, new_price, new_status, product_id))
                    st.success("Đã cập nhật thành công! Vui lòng tải lại trang.")
                except sqlite3.IntegrityError:
                    st.error("Lỗi: Mã IMEI bị trùng với sản phẩm khác!")
                    
            if delete_btn:
                run_query("DELETE FROM products WHERE id=?", (product_id,))
                st.success("Đã xóa sản phẩm thành công! Vui lòng tải lại trang.")
                # ------------------------------------------
# CHỨC NĂNG 4: CHUYỂN ĐỔI DỮ LIỆU (ETL)
# ------------------------------------------
elif menu == "🔄 Chuyển đổi dữ liệu (ETL)":
    st.header("Chuyển đổi dữ liệu từ hệ thống cũ")
    st.info("Tính năng này cho phép Import hàng loạt dữ liệu từ file CSV/Excel cũ vào cơ sở dữ liệu mới, tự động kiểm tra trùng lặp IMEI.")
    
    # Cho phép tải file lên
    uploaded_file = st.file_uploader("Tải lên file dữ liệu cũ (định dạng .csv)", type=["csv"])
    
    # Code tạo file CSV mẫu để bạn tải về test thử
    st.markdown("*(Hoặc tải [File CSV mẫu tại đây](#) nếu bạn chưa có)*")
    sample_df = pd.DataFrame({
        "Ten_SP": ["Samsung Galaxy S24", "MacBook Pro M3", "iPad Air 5"],
        "Ma_IMEI": ["SAM123456", "MAC987654", "IPA112233"],
        "Gia": [22000000, 35000000, 15000000],
        "Trang_thai": ["Còn hàng", "Còn hàng", "Đã bán"]
    })
    st.download_button(
        label="📥 Tải file CSV mẫu để test",
        data=sample_df.to_csv(index=False).encode('utf-8'),
        file_name='du_lieu_cu_mau.csv',
        mime='text/csv',
    )

    if uploaded_file is not None:
        try:
            # EXTRACT: Đọc dữ liệu từ file
            df = pd.read_csv(uploaded_file)
            st.write("📋 Xem trước dữ liệu từ hệ thống cũ:")
            st.dataframe(df.head())
            
            if st.button("🚀 Bắt đầu chuyển đổi (Migrate Data)"):
                success_count = 0
                error_count = 0
                error_list = []
                
                # Biến quá trình (Progress bar) cho sinh động
                progress_bar = st.progress(0)
                total_rows = len(df)
                
                # TRANSFORM & LOAD: Lặp qua từng dòng để đưa vào DB
                for index, row in df.iterrows():
                    try:
                        # Giả sử file có các cột: Ten_SP, Ma_IMEI, Gia, Trang_thai
                        name = str(row['Ten_SP'])
                        imei = str(row['Ma_IMEI'])
                        price = float(row['Gia'])
                        status = str(row['Trang_thai'])
                        
                        run_query("INSERT INTO products (name, imei, price, status) VALUES (?, ?, ?, ?)", 
                                  (name, imei, price, status))
                        success_count += 1
                    except sqlite3.IntegrityError:
                        error_count += 1
                        error_list.append(f"Dòng {index + 1}: IMEI '{imei}' đã tồn tại.")
                    except Exception as e:
                        error_count += 1
                        error_list.append(f"Dòng {index + 1}: Lỗi định dạng dữ liệu.")
                    
                    # Cập nhật thanh tiến trình
                    progress_bar.progress((index + 1) / total_rows)
                
                # Hiển thị kết quả báo cáo
                st.success(f"✅ Đã chuyển đổi thành công: {success_count} sản phẩm.")
                if error_count > 0:
                    st.error(f"❌ Có {error_count} sản phẩm bị lỗi (bỏ qua).")
                    with st.expander("Xem chi tiết lỗi"):
                        for err in error_list:
                            st.write(err)
                            
        except Exception as e:
            st.error(f"Đã xảy ra lỗi khi đọc file: {e}. Vui lòng đảm bảo file đúng định dạng CSV.")