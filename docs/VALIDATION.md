# Kiểm tra triển khai ban đầu — 03/11/2026

## Kết quả đã chạy

| Kiểm tra | Kết quả |
|---|---|
| 9 bài unittest trên host | PASS |
| Driver motor C++ thực tế, stub GPIO, g++ C++17 -Wall -Wextra -Werror | PASS: mọi lần ghi GPIO4–7 đều LOW, kể cả đổi motorPins/PWM và NaN/Inf demand |
| Analyzer log | PASS: RMSE biết trước, wrap yaw ±179°, ring buffer, gap, từ chối NaN/timestamp trùng/thiếu mẫu |
| Patch hook | PASS: từ chối hook mất hoặc xuất hiện nhiều lần |
| Chuẩn bị từ commit upstream cố định | PASS; upstream vẫn clean |
| Thư mục đầu ra đã tồn tại | Bị từ chối, không ghi đè |
| Lệnh tắt brownout của upstream | Đã loại khỏi bản generated |
| Compile ESP32-S3 với Arduino CLI 1.5.1 | PASS |
| git diff --check | PASS |

Lệnh thử host: `python3 -m unittest discover -s tests -v`.

## Cấu hình compile đã kiểm tra

- Flix: `1f5b268271536e45a9377d1c5317d3eb6f3c3bba`.
- Arduino CLI: 1.5.1; gói Linux được đối chiếu SHA-256 với metadata release chính thức.
- Core: `esp32:esp32@3.3.10`.
- Libraries: `FlixPeriph@1.12.1`, `MAVLink@2.0.33`.
- FQBN: `esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,PSRAM=disabled`.
- Profile: bench-only, MPU6500/9250-family SPI dự kiến, nguồn pin ADC tắt.

Compiler báo:

```text
Sketch uses 1037193 bytes (79%) of program storage space. Maximum is 1310720 bytes.
Global variables use 109796 bytes (33%) of dynamic memory, leaving 217884 bytes for local variables. Maximum is 327680 bytes.
```

Đây là dung lượng build và bộ nhớ tĩnh; không chứng minh stack/heap đủ ở mọi runtime, không phải hiệu năng vòng điều khiển. Binary tạo cục bộ, không phát hành trong repo.

## Chưa thực hiện

- Chưa nạp/chạy trên SuperMini thật; chưa xác minh revision/flash/USB.
- Chưa đọc IMU thật, kiểm tra trục, bus, thời gian lấy mẫu hoặc độ trễ RF.
- Chưa đo nguồn, dòng motor, lực nâng, nhiệt, khối lượng hay thời lượng bay.
- Chưa chạy SITL/Gazebo hoặc thử bay.
- Chưa thiết kế schematic/layout KiCad hoàn chỉnh; chưa ERC/DRC hoặc xuất Gerber.
- Chưa triển khai flow/ToF/position control/swarm.
- Workflow GitHub đã được cấu hình; kết quả local ở trên không thay thế kết quả Actions trên máy chủ.

Nguồn mã/giấy phép và trạng thái phát hành: [COMMERCIALIZATION_NOTES.md](COMMERCIALIZATION_NOTES.md).
