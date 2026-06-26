# Cyber Defense AI

Cyber Defense AI là ứng dụng desktop bằng Python + Pygame để mô phỏng các thuật toán AI trong bối cảnh phòng thủ mạng. Dự án dùng đồ thị mạng nhỏ để minh họa tìm đường, tối ưu phòng thủ, phân vùng CSP, belief-state và trò chơi đối kháng Hacker/Defender.

Đây là mô phỏng học thuật. Ứng dụng không quét mạng, không khai thác lỗ hổng, không tạo payload và không kết nối tới hệ thống bên ngoài.

## Tính năng chính

- Giao diện Pygame trực quan với bản đồ mạng, log thuật toán, bảng giám sát, kết quả và đường đi.
- 6 nhóm thuật toán, tổng cộng 18 thuật toán.
- Chạy tự động, tạm dừng, chạy từng bước, đặt lại và so sánh nhóm.
- Animation frontier/explored/current/final path, zone coloring, fog of war, plan tree và pruning/chance data.
- 7 map JSON mẫu cho từng nhóm thuật toán.
- Unit test cho core graph, 18 thuật toán, UI wiring và Phase 8 stability.

## Cài đặt

Yêu cầu:

- Python 3.11 trở lên
- Pygame 2.6 trở lên

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Chạy test

Từ thư mục `Cyber-Defense-AI`:

```bash
python -m pytest tests -q
```

Kiểm tra riêng Phase 8:

```bash
python -m pytest tests/test_phase8_polish.py -q
```

## Tạo screenshot demo

```bash
python tools/render_demo_assets.py
```

Script sẽ tạo:

- `screenshots/demo_1366x768.png`
- `screenshots/demo_1920x1080.png`

## Điều khiển giao diện

- Tab trên cùng: chọn 1 trong 6 nhóm thuật toán.
- Dropdown thuật toán: chọn thuật toán trong nhóm hiện tại.
- Dropdown bản đồ: chọn map phù hợp với nhóm.
- `Chạy`: bắt đầu animation.
- `Dừng`: tạm dừng animation.
- `Bước`: chạy từng bước khi đang sẵn sàng hoặc tạm dừng.
- `Đặt lại`: đưa lượt chạy hiện tại về trạng thái ban đầu.
- Tốc độ mô phỏng: `0.5x`, `1x`, `2x`, `4x`.
- `So sánh nhóm`: chạy các thuật toán cùng nhóm và hiển thị bảng so sánh.

Chi tiết nội bộ như frontier, explored, current, domain, belief, alpha/beta hoặc plan được hiển thị trong panel giám sát/log khi thuật toán cung cấp dữ liệu.

## Danh sách thuật toán

| Nhóm | Thuật toán | Vai trò mô phỏng |
|---|---|---|
| Tìm kiếm mù | BFS | Tìm đường theo chiều rộng |
| Tìm kiếm mù | DFS | Tìm đường theo chiều sâu |
| Tìm kiếm mù | UCS | Tìm đường chi phí thấp nhất |
| Tìm kiếm có phí | Greedy Best-First Search | Chọn node theo heuristic `h` |
| Tìm kiếm có phí | A* | Chọn node theo `f = g + h` |
| Tìm kiếm có phí | IDA* | A* theo ngưỡng lặp, tiết kiệm bộ nhớ |
| Tìm kiếm cục bộ | Simple Hill Climbing | Tối ưu cấu hình phòng thủ |
| Tìm kiếm cục bộ | Steepest Ascent Hill Climbing | Chọn neighbor tốt nhất |
| Tìm kiếm cục bộ | Simulated Annealing | Chấp nhận bước xấu theo xác suất để thoát local optimum |
| Môi trường phức tạp | Belief Unobservable | Defender lập kế hoạch khi không thấy hacker |
| Môi trường phức tạp | Belief Partial Observable | Cập nhật belief từ quan sát IDS |
| Môi trường phức tạp | AND-OR Graph Search | Tạo conditional plan cho action không chắc chắn |
| CSP | Backtracking | Phân vùng security zone |
| CSP | Forward Checking | Phân vùng zone với lọc domain sớm |
| CSP | Min-Conflicts | Sửa assignment đang conflict |
| Môi trường đối kháng | Minimax | Hacker/Defender tối ưu đối kháng |
| Môi trường đối kháng | Alpha-Beta Pruning | Minimax có cắt nhánh |
| Môi trường đối kháng | Expectimax | Game tree có chance node |

## Map mẫu

- `pathfinding_basic.json`: BFS/DFS/UCS cơ bản.
- `weighted_network.json`: Greedy/A*/IDA* và chi phí có trọng số.
- `defense_optimization.json`: local search tối ưu phòng thủ.
- `belief_hidden.json`: belief-state không quan sát.
- `belief_partial.json`: belief-state quan sát một phần.
- `csp_segmentation.json`: phân vùng security zone.
- `adversarial_game.json`: Minimax/Alpha-Beta/Expectimax.

## Cấu trúc dự án

```text
Cyber-Defense-AI/
  main.py
  requirements.txt
  README.md
  DEMO_SCRIPT.md
  tools/
    render_demo_assets.py
  algorithms/
    uninformed/
    informed/
    local_search/
    complex_environment/
    csp/
    adversarial/
  core/
    graph.py
    map_loader.py
    models.py
    state.py
    metrics.py
    event_log.py
    constants.py
    utils.py
  maps/
  tests/
  ui/
```

## Demo

Kịch bản thuyết trình nằm ở `DEMO_SCRIPT.md`. Nên demo theo thứ tự: tìm kiếm mù, heuristic, local search, CSP, môi trường phức tạp, đối kháng, sau đó dùng `So sánh nhóm` và `Đặt lại` để kết thúc.
