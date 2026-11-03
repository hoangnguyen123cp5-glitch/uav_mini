# Nguồn gốc và phạm vi phát hành

Kiểm tra 03/11/2026, Flix commit `1f5b268271536e45a9377d1c5317d3eb6f3c3bba`.

- README Flix gọi dự án là open source và mời sửa thiết kế/code. Các file code có thông báo copyright của Oleg Kalachev.
- Không tìm thấy file LICENSE/COPYING trong cây file của snapshot đã đọc. Chưa đủ căn cứ để tự gán MIT/GPL hoặc khẳng định quyền phân phối binary, thiết kế sửa đổi và kit thương mại theo một giấy phép cụ thể.
- Tích hợp hiện tại ghi nhận nguồn và tải upstream vào thư mục local bị gitignore; repo UAV Mini chỉ thêm công cụ/profile riêng, không vendor toàn bộ Flix hoặc phát hành binary. Điều này không tự giải quyết quyền thương mại của sản phẩm cuối.
- Cần xác nhận giấy phép/điều khoản với tác giả trước phát hành kit có firmware phái sinh, đồng thời rà soát FlixPeriph, MAVLink, Arduino/ESP-IDF và mọi dependency thực tế. Chưa gửi liên hệ cho tác giả.
- Mã/thiết kế Bitcraze cần kiểm tra giấy phép riêng từng repository. Không dùng thương hiệu/logo Crazyflie để làm người mua hiểu là sản phẩm của Bitcraze hoặc tương thích khi chưa thử.
- Chưa đặt giấy phép chung cho toàn repo UAV Mini vì chưa xác minh quyền đối với mọi tài liệu/hình có từ trước. Quyết định giấy phép mã mới thuộc chủ dự án.

Nguồn: [Flix](https://github.com/okalachev/flix/tree/1f5b268271536e45a9377d1c5317d3eb6f3c3bba), [Bitcraze open-source philosophy](https://www.bitcraze.io/open-source-philosophy/).

Kế hoạch kinh doanh hiện là định hướng kỹ thuật. Giá thành vật tư mục tiêu chưa bao gồm phát triển, QC, lỗi, bảo hành hoặc hỗ trợ; không dùng làm giá bán. Hồ sơ triển khai/bán hàng thực tế còn cần xác định thị trường và các yêu cầu áp dụng.
