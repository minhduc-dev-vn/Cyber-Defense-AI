# Cyber Defense AI

> **Tên đề tài:** Cyber Defense AI: Mô phỏng tìm kiếm, tối ưu, phân vùng mạng và đối kháng giữa Hacker với hệ thống phòng thủ  
> **Loại sản phẩm:** Ứng dụng desktop trực quan bằng Python + Pygame  
> **⚠️ Lưu ý an toàn:** Đây chỉ là mô phỏng game/đồ thị mạng phục vụ học thuật. Không triển khai hack thật, quét mạng, khai thác lỗ hổng, mã độc hoặc kết nối tới hệ thống bên ngoài.

---

## Mô tả

Ứng dụng mô phỏng mạng máy tính dưới dạng đồ thị trực quan:

- **Hacker** tìm đường từ node xuất phát tới `Server` hoặc `Database`
- **Defender** bảo vệ mạng bằng cách chặn node/cạnh, bố trí `Firewall`, `IDS`, tăng bảo mật và phân vùng security zone
- Ứng dụng có **6 nhóm thuật toán AI**, tổng cộng **18 thuật toán**

---

## Yêu cầu hệ thống

- Python 3.11 hoặc 3.12+
- Pygame 2.6+

---

## Cài đặt và Chạy

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## Chạy Tests

```bash
python -m pytest tests/ -v
# hoặc từng file test
python -m pytest tests/test_graph.py -v
```

---

## Cấu trúc thư mục

```
cyber_defense_ai/
│
├── main.py               # Entry point
├── requirements.txt
├── README.md
├── context.md            # Ngữ cảnh project cho AI tiếp tục
│
├── core/
│   ├── models.py         # Dataclass: Node, Edge, GameState, StepEvent, ...
│   ├── graph.py          # NetworkGraph class
│   ├── state.py          # AlgorithmState, GameplayState
│   ├── map_loader.py     # Đọc JSON map
│   ├── metrics.py        # AlgorithmMetrics, thống kê
│   ├── event_log.py      # EventLog - ghi log từng bước
│   ├── constants.py      # Hằng số: chi phí, màu sắc
│   └── utils.py          # Hàm tiện ích
│
├── algorithms/
│   ├── uninformed/       # BFS, DFS, UCS
│   ├── informed/         # GSA, A*, IDA*
│   ├── local_search/     # Simple HC, Steepest HC, SA
│   ├── complex_environment/ # Belief state, AND-OR
│   ├── csp/              # Backtracking, Forward Checking, Min-Conflicts
│   └── adversarial/      # Minimax, Alpha-Beta, Expectimax
│
├── ui/
│   ├── app.py            # Pygame app chính
│   ├── layout.py         # Bố cục vùng
│   ├── renderer.py       # Vẽ đồ thị
│   ├── controls.py       # Các nút điều khiển
│   ├── panels.py         # Panel bên trái
│   ├── graph_view.py     # Vùng hiển thị bản đồ
│   ├── log_view.py       # Vùng log
│   ├── stats_view.py     # Vùng thống kê
│   └── theme.py          # Màu sắc, font
│
├── maps/                 # 7 file JSON map mẫu
│
└── tests/                # Unit tests
```

---

## 18 Thuật toán

| # | Nhóm | Thuật toán | Bài toán |
|---|------|-----------|---------|
| 1 | Tìm kiếm mù | BFS | Hacker tìm đường tới Server |
| 2 | Tìm kiếm mù | DFS | Hacker tìm đường tới Server |
| 3 | Tìm kiếm mù | UCS | Hacker tìm đường chi phí thấp nhất |
| 4 | Heuristic | Greedy Search | Hacker tìm đường nhanh nhất theo ước lượng |
| 5 | Heuristic | A* | Hacker tìm đường tối ưu g+h |
| 6 | Heuristic | IDA* | Hacker tìm đường tối ưu, tiết kiệm bộ nhớ |
| 7 | Tìm kiếm cục bộ | Simple Hill Climbing | Defender tối ưu phòng thủ |
| 8 | Tìm kiếm cục bộ | Steepest Ascent HC | Defender tối ưu phòng thủ |
| 9 | Tìm kiếm cục bộ | Simulated Annealing | Defender tối ưu tránh local optimum |
| 10 | Môi trường phức tạp | Belief Unobservable | Defender chặn Hacker vô hình |
| 11 | Môi trường phức tạp | Belief Partial | Defender chặn Hacker qua IDS |
| 12 | Môi trường phức tạp | AND-OR Graph | Defender lập kế hoạch điều kiện |
| 13 | CSP | Backtracking | Phân vùng Security Zone |
| 14 | CSP | Forward Checking | Phân vùng Security Zone |
| 15 | CSP | Min-Conflicts | Phân vùng Security Zone |
| 16 | Đối kháng | Minimax | Hacker vs Defender game tree |
| 17 | Đối kháng | Alpha-Beta | Minimax tối ưu với pruning |
| 18 | Đối kháng | Expectimax | Game tree với chance nodes |

---

## Điều khiển UI

- **Tab nhóm**: Chọn 1 trong 6 nhóm thuật toán
- **Dropdown thuật toán**: Chọn thuật toán trong nhóm
- **Dropdown map**: Chọn bản đồ phù hợp
- **Start / Pause / Step / Reset**: Điều khiển animation
- **Tốc độ**: 0.5x, 1x, 2x, 4x
- **Random Seed**: Đảm bảo kết quả tái lập
- **Compare**: So sánh các thuật toán cùng nhóm
- **Show/Hide Details**: Bật tắt bảng frontier/domain/alpha-beta

---

## Quy ước màu sắc

| Đối tượng | Màu |
|-----------|-----|
| Hacker | Đỏ |
| Server/Database | Tím |
| Firewall | Cam đậm (viền dày) |
| IDS | Vàng (viền vàng) |
| Frontier | Cam |
| Explored | Xám |
| Current node | Vàng sáng |
| Final path | Đỏ/cam đậm |
| Blocked | Xám đậm |
| CSP zone | Màu riêng theo zone |
