# UAV Mini — nền tảng học thuật chi phí thấp

Ngày: 03/11/2026. Chủ dự án chưa có phần cứng. Định hướng: kit học điều khiển và nền tảng thí nghiệm có thể sửa phần mềm/phần cứng, phát triển từ Flix. Crazyflie 2.1+ là mốc tham chiếu tính năng; không tuyên bố tương thích hoặc hiệu năng ngang bằng.

## 1. Sản phẩm đầu tiên

**Core Lab:** điều khiển tư thế, dữ liệu IMU, hiệu chuẩn, thay đổi PID, log và bài thực hành tiếng Việt. Cấu hình nghiên cứu: ESP32-S3, module IMU SPI được xác minh, bốn motor 8520 3,7 V, cánh phù hợp và pin 1S. Nguồn/driver phải qua thử bàn. Chưa chốt mã mua hoặc footprint.

**Research Add-on:** ToF + optical flow, ước lượng vận tốc/độ cao, giữ vị trí tương đối, API thí nghiệm. Cổng mở rộng có thể dự phòng sớm; tính năng chưa được triển khai trong firmware hiện tại.

**Multi-agent Lab:** định vị ngoài hoặc mốc tham chiếu, timestamp, đo trễ/mất gói, scheduler truyền thông, quản lý nhiều drone và khôi phục lỗi. Chỉ triển khai sau khi một drone đã ổn định.

## 2. So với Crazyflie

| Năng lực | Mốc Crazyflie | UAV Mini hiện tại | Mốc cần đạt |
|---|---|---|---|
| Tư thế/PID | Nền tảng bay và hệ firmware trưởng thành | Tích hợp Flix bench-only | Bay ổn định, log đủ để đánh giá |
| Log/đổi tham số/Python | Có hệ công cụ nghiên cứu | Kế thừa API/telemetry upstream; thêm analyzer CSV | Quy trình thí nghiệm có thể lặp lại |
| Giữ độ cao/vị trí | Dùng deck và hệ định vị phù hợp | Chưa làm driver/fusion/control bổ sung | ToF + flow + kiểm thử drift và điều kiện sàn |
| Bay bầy đàn | Hệ radio, định vị, SDK và công cụ | Chưa triển khai | Đo định lượng 2–3 máy trước khi tăng số |
| Cơ khí/khối lượng | 2.1+ công bố 29 g và 7 phút với pin gốc | Chưa biết khối lượng hoặc thời gian bay | Đo lực nâng, trọng lượng, nhiệt và thời lượng |
| Bảo trì/sản phẩm | Hệ module và tài liệu | Đang xây dựng | Module thay nhanh, kiểm tra xuất xưởng, tài liệu và phụ tùng |

Không dùng xung nhịp CPU để suy ra ngang Crazyflie. ESP32-S3 với Wi-Fi/ESP-NOW không mặc nhiên tương thích Crazyradio/cflib/CRTP/deck. Flow+ToF không tự cung cấp vị trí tuyệt đối và có thể trôi; mô hình cầm tay chưa phù hợp tuyên bố bay bầy đàn.

## 3. Ngân sách thiết kế

[Phân bổ mục tiêu](../hardware/budget_targets.json) là trần để sàng lọc linh kiện, không phải báo giá đã khảo sát:

- Core: 1.015.000 đ trước dự phòng; 1.218.000 đ với 20% dự phòng.
- Core + flow/ToF: 1.665.000 đ trước dự phòng; 1.998.000 đ với 20% dự phòng.
- Chưa gồm công, thiết bị đo, vận chuyển/thuế, các lần hỏng, hỗ trợ/bảo hành và hạ tầng định vị.

Chạy `python3 tools/budget.py` khi thay số. Chưa quyết định dung lượng pin chỉ theo giá: phải đo tổ hợp motor–cánh–pin và khối lượng trước. Chưa chốt giá bán hoặc lợi nhuận. Cần lấy ít nhất hai báo giá cho các linh kiện chính và tính chi phí lắp/kiểm thử/phụ tùng.

## 4. Các mốc kỹ thuật và nghiệm thu

Các số dưới đây là mục tiêu thiết kế để thảo luận và đo, không phải kết quả hiện có.

| Mốc | Đầu ra | Tiêu chí nghiệm thu dự kiến |
|---|---|---|
| M0 — baseline phần mềm | Pin commit, profile S3, build, bench inhibit, công cụ log | Build đúng toolchain; test host qua; chưa cấp motor |
| M1 — mẫu bàn | Linh kiện thật, test nguồn/USB, IMU, một kênh motor | Không brownout trong tải bước; trục đúng; log dòng/nhiệt; đo lực nâng và dòng có cánh trên gá |
| M2 — drone đầu tiên | Khung, bốn motor, firmware có arm/disarm/failsafe được review | Đo vòng rate mục tiêu ≥500 Hz; log chu kỳ và overrun; tổng lực nâng mục tiêu ≥2 lần trọng lượng tại điện áp đã xác định |
| M3 — Core Lab | Bộ bài thực hành và PCB Rev A đã đo | Mục tiêu 3 phút bay, 10 lần thử có nhật ký; không reset; ghi PID/khối lượng/pin/điều kiện. Chưa phải chuẩn chứng nhận sản phẩm |
| M4 — Research | Driver flow/ToF, fusion, position loop | Mục tiêu RMS ngang ≤0,20 m trong 30 s, độ cao 0,5–1 m; đo độc lập bằng camera/mocap; công bố sàn/ánh sáng và drift |
| M5 — bán thử học thuật | 3 bộ tái lập + hướng dẫn + phụ tùng | Cùng quy trình QC, serial/revision/firmware, giấy phép rõ, thời gian hỗ trợ và lỗi được ghi nhận |
| M6 — nhiều drone | Giao thức và định vị ngoài | Thử 2–3 chiếc, log trễ/mất gói/failsafe; không suy từ một chiếc sang swarm |

## 5. Ticket thực hiện

| ID | Việc | Trạng thái / phụ thuộc |
|---|---|---|
| SW-01 | Khóa upstream và cấu hình bench | Đã triển khai; xem báo cáo validation |
| SW-02 | Build S3 và test chặn đầu ra | Xem báo cáo validation, không đồng nghĩa thử phần cứng |
| DATA-01 | Analyzer CSV và ví dụ synthetic | Đã triển khai; ví dụ không phải log bay |
| HW-01 | Chọn nơi mua và xác minh SuperMini/IMU | Chưa làm; trước khi đặt PCB |
| HW-02 | Đo motor/cánh/pin và khối lượng | Cần mua/đo mẫu |
| HW-03 | Nguồn/USB và driver một motor | Theo đặc tả Rev A, sau HW-01/02 |
| SW-03 | Đầu ra bay, state machine arm, timeout/IMU lỗi, low battery | Chưa triển khai; sau kiểm tra nguồn/driver |
| HW-04 | KiCad schematic/layout và Gerber | Chưa triển khai; sau dữ liệu footprint, điện và cơ khí |
| LAB-01 | Bài hiệu chuẩn, nhận dạng motor, PID, đo nhiễu | Đề cương ở dưới; cần dữ liệu thật |
| NAV-01 | Flow/ToF, fusion và position control | Chưa triển khai; sau M3 |
| PRODUCT-01 | Giấy phép, BOM mua hàng, QC và chi phí hỗ trợ | Chưa đủ để phát hành thương mại |

## 6. Đề cương bộ bài thực hành

1. Nguồn và đo pin: tải bước, ripple, sụt áp, brownout.
2. IMU: bias, hướng trục, nhiễu, ảnh hưởng rung và hiệu chuẩn.
3. Động lực học: đo lực đẩy theo duty/điện áp, nhận dạng mô hình.
4. Điều khiển: vòng tốc độ góc rồi vòng tư thế; so sánh PID bằng log.
5. Ước lượng: kết hợp gyro/acc; sau đó thêm ToF/flow.
6. Thí nghiệm tái lập: lưu commit, tham số, khối lượng, pin và điều kiện mỗi lần chạy.

Giá trị thương mại hướng tới là bộ kit đã kiểm tra, giáo trình, công cụ đo và hỗ trợ. Chưa có căn cứ quảng cáo “ngang Crazyflie” hoặc “bay bầy đàn” trước nghiệm thu tương ứng.

## Nguồn

- [Flix tại commit tham chiếu](https://github.com/okalachev/flix/tree/1f5b268271536e45a9377d1c5317d3eb6f3c3bba)
- [Crazyflie 2.1+](https://www.bitcraze.io/products/crazyflie-2-1-plus/)
- [Hệ nền tảng Bitcraze](https://www.bitcraze.io/documentation/system/platform/)
- [Ghi nhận giấy phép](COMMERCIALIZATION_NOTES.md)
