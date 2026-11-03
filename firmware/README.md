# Firmware chạy bàn — UAV Mini

Đây là tích hợp **bench-only** với Flix, chưa phải firmware bay. Chưa có bo hoặc cảm biến để kiểm thử thực tế. File `upstream.lock.json` cố định commit và phiên bản thư viện. Mã upstream được tải vào `external/`, không sao chép vào lịch sử UAV Mini.

## Cài và build

Cần Git, Python 3.10+ và [Arduino CLI](https://docs.arduino.cc/arduino-cli/installation/). Trên Windows có thể thay `python3` bằng `py -3`.

Tại thư mục gốc UAV Mini:

```bash
python3 tools/prepare_firmware.py
python3 tools/build_firmware.py --install --output build/bench-compiled
```

Lệnh đầu tải đúng upstream và tạo `build/bench/flix`. Lệnh sau tạo một bản độc lập trong `build/bench-compiled` và compile; không nạp vào bo. Nếu thư mục đầu ra đã tồn tại, dùng tên khác để giữ kết quả cũ. Thư viện được cài vào môi trường Arduino CLI đang sử dụng.

FQBN đề xuất là ESP32-S3 generic, USB Serial/JTAG, CDC bật, PSRAM tắt. Đây là cấu hình thử; chưa xác nhận flash/USB/revision của SuperMini sẽ mua. Không phát hành binary chung cho mọi SuperMini.

## Những thay đổi so với Flix

- Bảng chân phù hợp đề xuất README: motor 4/5/6/7; SPI 12/13/11, CS 10.
- MPU6500/9250-family SPI là cấu hình nghiên cứu ban đầu; phải xác minh module và chiều trục.
- GPIO4–7 được giữ LOW ngay đầu setup và trong mọi lần gửi đầu ra; không gọi LEDC. Lệnh motor test bị từ chối. Đổi tham số qua console/NVS không bật được PWM trong bản này.
- Namespace NVS riêng `uavmini_bench` tránh lấy cấu hình Flix cũ. Các cấu hình của những lần bench trước vẫn có thể được lưu; kiểm tra `p` trước khi dùng.
- Giữ brownout detector theo cấu hình nền tảng; bỏ lệnh upstream vô hiệu hóa nó.
- Không điều khiển LED vì chưa biết chân LED của SuperMini; ADC pin và SBUS mặc định tắt.
- Telemetry `motors` và trạng thái `armed` của Flix có thể phản ánh yêu cầu phần mềm, **không phải duty PWM thật**. Tất cả đầu ra vật lý trong driver bench vẫn LOW.

Pull-down gate phần cứng vẫn cần thiết trong reset/boot trước setup. GPIO4–7 không được nối tới phần cứng khác. Chưa có cơ chế enable-flight trong bộ này: cần một nhánh phát triển, review, đo nguồn/motor, kiểm tra trục và failsafe trước khi triển khai đầu ra bay.

## Làm được ngay khi chưa mua phần cứng

```bash
python3 tools/budget.py
python3 tools/analyze_log.py examples/synthetic_log.csv
python3 -m unittest discover -s tests -v
```

`synthetic_log.csv` là dữ liệu giả lập để minh họa định dạng, không phải kết quả bay hoặc mô phỏng động lực học. `analyze_log.py` nhận CSV theo tên cột Flix, tính RMSE góc và khoảng cách mẫu, sắp lại log ring-buffer, từ chối NaN và timestamp trùng. Tần số log không phải tần số vòng điều khiển.

## Khi có phần cứng

1. Xác nhận nguồn/USB, module IMU, GPIO và axis mapping; tháo cánh và tách nguồn motor.
2. Build đúng bo, chọn cổng nạp sau khi kiểm tra. Bộ công cụ không tự flash.
3. Qua console Flix kiểm tra `p`, `imu`, `st`, `time`, `pw`; lắc từng trục và ghi dữ liệu. `pw` chưa đo pin khi voltagePin vẫn -1.
4. Chỉ dùng `preset` khi chấp nhận xóa cấu hình bench đã lưu; không tự reset hoặc hiệu chuẩn âm thầm.
5. Dùng tài liệu gốc để cấu hình kết nối Wi-Fi và pyflix. Công cụ UAV Mini hiện chưa bổ sung ToF, flow hoặc điều khiển vị trí.

Mô phỏng Gazebo của [Flix](https://github.com/okalachev/flix/tree/1f5b268271536e45a9377d1c5317d3eb6f3c3bba/gazebo) là bước tiếp theo; chưa chạy trong lần triển khai này. Không nhầm test driver chạy trên máy tính với SITL hoặc kiểm thử bay.
