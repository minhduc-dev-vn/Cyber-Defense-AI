"""
constants.py — Hằng số toàn project Cyber Defense AI.

Tất cả tham số cấu hình, trọng số chi phí và màu sắc giao diện.
"""

# ─── Chi phí và trọng số ──────────────────────────────────────────────────────
SECURITY_WEIGHT: float = 1.5       # Hệ số nhân với security_level trong edge cost
DETECTION_WEIGHT: float = 2.0      # Hệ số nhân với detection_risk
FIREWALL_PENALTY: float = 10.0     # Phạt khi đi qua node Firewall
IDS_DETECTION_PENALTY: float = 5.0 # Phạt khi đi qua node IDS
MIN_EDGE_COST: float = 1.0         # Chi phí cạnh tối thiểu (không âm)

# ─── Đánh giá local search ───────────────────────────────────────────────────
DEFENSE_VALUE_BLOCK_PATH: int = 10   # Thưởng mỗi đường bị chặn
DEFENSE_VALUE_PROTECTED: int = 5     # Thưởng mỗi node quan trọng được bảo vệ
DEFENSE_VALUE_SLOW_DOWN: int = 3     # Thưởng mỗi lượt Hacker bị chậm
DEFENSE_VALUE_RESOURCE_COST: int = 2 # Phạt mỗi tài nguyên dùng
DEFENSE_VALUE_OPEN_PATH: int = 8     # Phạt mỗi đường Hacker còn đi tới Server

RISK_COST_OPEN_PATH: int = 10        # Phạt mỗi đường Hacker còn tới Server
RISK_COST_PATH_RISK: int = 5         # Phạt mỗi đường nguy hiểm
RISK_COST_DEFENSE_COST: int = 2      # Phạt chi phí phòng thủ
RISK_COST_PROTECTED: int = 3         # Thưởng mỗi node được bảo vệ

# ─── Đánh giá game đối kháng ─────────────────────────────────────────────────
EVAL_HACKER_DATABASE: int = 1000
EVAL_HACKER_SERVER: int = 500
EVAL_HACKER_NEAR_SERVER: int = 100
EVAL_HACKER_LOW_SECURITY: int = 20
EVAL_HACKER_DETECTED: int = -150
EVAL_HACKER_NO_PATH: int = -300

# ─── Simulated Annealing mặc định ────────────────────────────────────────────
SA_DEFAULT_T0: float = 100.0
SA_DEFAULT_ALPHA: float = 0.95
SA_DEFAULT_TMIN: float = 0.1
SA_DEFAULT_MAX_STEPS: int = 1000

# ─── Expectimax xác suất IDS ────────────────────────────────────────────────
IDS_DETECT_PROB: float = 0.70
IDS_MISS_PROB: float = 0.30
FIREWALL_BLOCK_PROB: float = 0.80
FIREWALL_FAIL_PROB: float = 0.20

# ─── UI kích thước ──────────────────────────────────────────────────────────
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 800
CONTROL_PANEL_WIDTH: int = 280
LOG_PANEL_HEIGHT: int = 200
GRAPH_AREA_MARGIN: int = 20

NODE_RADIUS: int = 26
EDGE_WIDTH: int = 2
ARROW_SIZE: int = 8

FPS: int = 60

# ─── Tốc độ animation (giây/bước) ────────────────────────────────────────────
SPEED_OPTIONS: dict[str, float] = {
    "0.5x": 1.2,
    "1x": 0.6,
    "2x": 0.3,
    "4x": 0.15,
}
DEFAULT_SPEED: str = "1x"

# ─── Màu sắc giao diện ───────────────────────────────────────────────────────
# Màu nền
COLOR_BG = (18, 22, 36)
COLOR_PANEL_BG = (26, 30, 46)
COLOR_PANEL_BORDER = (50, 60, 90)

# Màu node theo trạng thái
COLOR_NODE_DEFAULT = (60, 120, 200)
COLOR_NODE_HACKER = (220, 50, 50)
COLOR_NODE_SERVER = (140, 60, 200)
COLOR_NODE_DATABASE = (100, 40, 180)
COLOR_NODE_FIREWALL = (220, 100, 30)
COLOR_NODE_IDS = (200, 180, 30)
COLOR_NODE_ROUTER = (50, 160, 100)
COLOR_NODE_SWITCH = (40, 140, 180)
COLOR_NODE_PC = (70, 130, 220)

# Màu trạng thái thuật toán
COLOR_FRONTIER = (255, 140, 0)
COLOR_EXPLORED = (100, 100, 110)
COLOR_CURRENT = (255, 230, 50)
COLOR_FINAL_PATH = (255, 60, 60)
COLOR_BLOCKED = (50, 50, 60)

# Màu cạnh
COLOR_EDGE_DEFAULT = (80, 90, 120)
COLOR_EDGE_FINAL = (255, 80, 80)
COLOR_EDGE_BLOCKED = (40, 40, 50)

# Màu CSP Zone
CSP_ZONE_COLORS: dict[str, tuple[int, int, int]] = {
    "User Zone": (70, 130, 220),
    "DMZ": (220, 150, 50),
    "Server Zone": (140, 60, 200),
    "Quarantine Zone": (200, 50, 50),
    None: (60, 120, 200),
}

# Màu text
COLOR_TEXT_PRIMARY = (220, 230, 255)
COLOR_TEXT_SECONDARY = (140, 150, 180)
COLOR_TEXT_LOG = (180, 200, 180)
COLOR_TEXT_WARNING = (255, 180, 50)
COLOR_TEXT_ERROR = (255, 80, 80)
COLOR_TEXT_SUCCESS = (80, 220, 120)

# Màu nút
COLOR_BTN_NORMAL = (50, 80, 140)
COLOR_BTN_HOVER = (70, 110, 180)
COLOR_BTN_ACTIVE = (40, 200, 120)
COLOR_BTN_DISABLED = (50, 55, 70)
COLOR_BTN_TEXT = (220, 230, 255)

# ─── Loại node hợp lệ ────────────────────────────────────────────────────────
VALID_NODE_KINDS = frozenset(["pc", "router", "switch", "firewall", "ids", "server", "database"])

# ─── Zone hợp lệ ─────────────────────────────────────────────────────────────
VALID_ZONES = frozenset(["User Zone", "DMZ", "Server Zone", "Quarantine Zone"])

# ─── Tên map ─────────────────────────────────────────────────────────────────
MAP_NAMES: dict[str, str] = {
    "pathfinding_basic": "Bản đồ cơ bản (BFS/DFS)",
    "weighted_network": "Mạng có trọng số (UCS/A*/IDA*)",
    "defense_optimization": "Tối ưu phòng thủ (Local Search)",
    "belief_hidden": "Ẩn hoàn toàn (Belief Unobservable)",
    "belief_partial": "Quan sát một phần (Belief Partial)",
    "csp_segmentation": "Phân vùng CSP",
    "adversarial_game": "Trò chơi đối kháng (Minimax)",
}
