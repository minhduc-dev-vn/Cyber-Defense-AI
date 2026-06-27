# context.md

## Phiên làm việc hiện tại

### Files đã sửa
- `core/state.py`
- `algorithms/adversarial/common.py`
- `algorithms/adversarial/minimax.py`
- `algorithms/adversarial/alpha_beta.py`
- `algorithms/adversarial/expectimax.py`
- `maps/adversarial_game.json`
- `ui/panels.py`
- `ui/app.py`

### Logic mới cho tab `Môi trường đối kháng`
- Tab này được chỉnh theo mô hình **Human Hacker vs AI Defender**.
- Người dùng chọn hành động Hacker ngay trong tab:
  - `Move`
  - `Scan`
  - `Attack`
- Người dùng chọn target node bằng dropdown hoặc click trực tiếp lên bản đồ.
- AI đóng vai Defender và phản ứng bằng logic Minimax-like / Alpha-Beta.
- Hành động Defender ưu tiên:
  - `Block node`
  - `Block edge`
  - `Deploy IDS`
  - `Upgrade`
- Hàm đánh giá được tách riêng trong `algorithms/adversarial/common.py`.

### Cách hoạt động
- `ControlPanel` hiện có cụm nút riêng cho tab đối kháng.
- `Human vs AI` là chế độ mô phỏng tương tác Hacker-Defender, còn `Minimax` và `Expectimax` là chế độ AI search trên cùng map.
- Mỗi lượt mô phỏng sinh `StepEvent` để UI animate.
- Hacker actions được tạo từ `hacker_actions(...)`.
- Defender actions được tạo từ `defender_actions(...)`.
- `Minimax` và `Alpha-Beta` dùng cùng bộ hành động và cùng hàm đánh giá.
- `Expectimax` dùng chance node với xác suất IDS phát hiện / bỏ sót.
- Map `adversarial_game.json` được chỉnh lại để phù hợp mô phỏng tương tác Hacker-Defender.

### Kiểm tra đã chạy
- Chạy test adversarial + UI:
  - `python -m pytest tests/test_adversarial.py tests/test_ui_phases.py -q`
- Kết quả: 9 tests passed.
- Chạy ứng dụng:
  - `python main.py`
- Ứng dụng đã khởi động lại thành công.

### Lưu ý
- Các nhóm thuật toán khác không bị chỉnh logic cốt lõi.
- Tab đối kháng hiện đã có điều khiển Hacker riêng, phù hợp yêu cầu mô phỏng AI minh họa.
