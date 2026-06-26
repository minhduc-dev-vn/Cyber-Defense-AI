# Demo Script - Cyber Defense AI

## Mục tiêu demo

Trình bày ứng dụng mô phỏng AI trên đồ thị mạng: tìm đường, tối ưu phòng thủ, phân vùng CSP, belief-state và đối kháng Hacker/Defender. Demo tập trung vào việc mỗi thuật toán sinh log, animation, path/plan và metrics thật từ logic thuật toán.

## Chuẩn bị

```bash
cd Cyber-Defense-AI
pip install -r requirements.txt
python main.py
```

Có thể tạo lại screenshot demo bằng:

```bash
python tools/render_demo_assets.py
```

Ảnh sẽ nằm trong thư mục `screenshots/`.

## Luồng thuyết trình đề xuất

1. Mở ứng dụng và giới thiệu bố cục:
   - Thanh tab 6 nhóm thuật toán ở trên.
   - Sidebar chọn thuật toán, bản đồ, điều khiển chạy.
   - Bản đồ mạng ở giữa.
   - Thông tin node, chú thích, log, giám sát, kết quả và đường đi.

2. Nhóm tìm kiếm mù:
   - Chọn `Tìm kiếm mù`.
   - Chạy `BFS`, nhấn `Chạy`, quan sát frontier/explored và đường đi cuối.
   - Reset, chạy `DFS`, so sánh cách duyệt sâu.
   - Chạy `UCS` để nhấn mạnh chi phí đường đi.

3. Nhóm tìm kiếm có phí:
   - Chọn `Tìm kiếm có phí`.
   - Chạy `Greedy`, `A*`, `IDA*`.
   - Giải thích `g`, `h`, `f` và threshold trong bảng giám sát/log.

4. Nhóm local search:
   - Chọn `Tìm kiếm cục bộ`.
   - Chạy `Simple Hill Climbing`, `Steepest Ascent`, `Simulated Annealing`.
   - Chỉ ra cấu hình firewall/IDS/upgrade và score phòng thủ.

5. Nhóm CSP:
   - Chọn `CSP - Ràng buộc`.
   - Chạy `Backtracking`, `Forward Checking`, `Min-Conflicts`.
   - Chỉ ra zone coloring và log assignment/domain/conflict.

6. Nhóm môi trường phức tạp:
   - Chọn `Môi trường phức tạp`.
   - Chạy belief unobservable, partial observable và AND-OR.
   - Giải thích belief state, node bị ẩn và conditional plan.

7. Nhóm đối kháng:
   - Chọn `Môi trường đối kháng`.
   - Chạy `Minimax`, `Alpha-Beta`, `Expectimax`.
   - Nêu sự khác biệt: pruning của Alpha-Beta, chance node của Expectimax.

8. Chốt demo:
   - Nhấn `So sánh nhóm` để hiện bảng compare.
   - Nhấn `Đặt lại` để chứng minh app quay về trạng thái ban đầu.
   - Nhắc lại ứng dụng chỉ mô phỏng học thuật, không có chức năng hack thật hoặc kết nối mạng.

## Điểm nên nhấn mạnh khi vấn đáp

- BFS tối ưu số bước khi mọi cạnh có cost bằng nhau.
- UCS/A*/IDA* tối ưu theo chi phí.
- Greedy có thể nhanh nhưng không luôn tối ưu.
- Simulated Annealing có thể chấp nhận bước xấu để thoát local optimum.
- Forward Checking giảm domain sớm hơn Backtracking.
- Alpha-Beta không đổi kết quả Minimax, chỉ giảm số node xét.
- Expectimax dùng kỳ vọng xác suất nên có thể chọn khác Minimax.
