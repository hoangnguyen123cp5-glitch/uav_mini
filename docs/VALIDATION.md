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
- Chưa hoàn thiện nguồn/định tuyến KiCad; chưa ERC hoặc xuất Gerber. DRC bố trí nháp đã chạy, kết quả bên dưới.
- Chưa triển khai flow/ToF/position control/swarm.
- Workflow GitHub đã được cấu hình; kết quả local ở trên không thay thế kết quả Actions trên máy chủ.

Nguồn mã/giấy phép và trạng thái phát hành: [COMMERCIALIZATION_NOTES.md](COMMERCIALIZATION_NOTES.md).

## KiCad DRAFT-0 — 03/11/2026

[Project và hướng dẫn](../hardware/kicad/UAV_Mini_RevA_Draft/README.md) đã được tạo bằng KiCad 7.0.11 và thư viện chính thức tương ứng. Đây là kết quả file CAD, chưa phải thử nghiệm phần cứng.

| Kiểm tra | Kết quả |
|---|---|
| Native schematic SVG/netlist export | PASS |
| Đọc lại `.kicad_pcb` bằng pcbnew | PASS, 33 footprint |
| Net schematic ↔ bảng thiết kế ↔ pad PCB | PASS theo giao diện đề xuất, không xác nhận pinout module thật |
| Gate/source/drain, cực diode, tách ba net nguồn | PASS theo topology đề xuất |
| DRC bố trí | 0 vi phạm khác; **67 mục chưa nối dây**, 0 lỗi footprint |
| ERC / kiểm tra điện trên phần cứng | Chưa chạy |
| Tracks / zones | 0 / 0 |
| Review preview | Đã xem SVG xuất từ KiCad và sửa chồng footprint/chữ |

**Không đạt điều kiện xuất sản xuất.** Board 60 × 60 mm, khoảng cách socket, package và connector đều chưa được xác nhận với phần cứng. Mạch chọn nguồn USB/boost chưa triển khai; không có Gerber.

Chạy lại bằng Python có `pcbnew`: `python3 tools/verify_kicad_draft.py --cli kicad-cli`. Xem [validation.json](../hardware/kicad/UAV_Mini_RevA_Draft/validation.json) và [báo cáo DRC](../hardware/kicad/UAV_Mini_RevA_Draft/drc-draft.txt).
