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

# ─── UI kích thước mặc định (chỉ mang tính fallback) ───────────────────────
WINDOW_WIDTH: int = 1366
WINDOW_HEIGHT: int = 768

NODE_RADIUS: int = 32
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
COLOR_BG = (10, 13, 20)              # Nền xanh đen gần đen (Header/Map)
COLOR_PANEL_BG = (16, 22, 34)        # Nền panel tối xanh
COLOR_PANEL_BORDER = (38, 50, 75)    # Viền rõ

# Màu node theo trạng thái
COLOR_NODE_DEFAULT = (40, 100, 180)  # Xanh lam trầm
COLOR_NODE_HACKER = (235, 60, 60)    # Đỏ Hacker
COLOR_NODE_SERVER = (160, 70, 220)   # Tím Server
COLOR_NODE_DATABASE = (130, 50, 190) # Tím đậm Database
COLOR_NODE_FIREWALL = (240, 120, 30) # Cam Firewall
COLOR_NODE_IDS = (230, 180, 40)      # Vàng IDS
COLOR_NODE_ROUTER = (45, 180, 95)    # Xanh lá Router
COLOR_NODE_SWITCH = (35, 140, 160)   # Xanh Switch
COLOR_NODE_PC = (50, 120, 200)       # Xanh PC (Node mặc định)

# Màu trạng thái thuật toán
COLOR_FRONTIER = (255, 150, 20)      # Cam Frontier
COLOR_EXPLORED = (90, 100, 115)      # Xám Explored
COLOR_CURRENT = (255, 220, 50)       # Vàng sáng Current Node
COLOR_FINAL_PATH = (235, 60, 60)     # Đỏ / Cam đậm cho đường đi
COLOR_BLOCKED = (55, 60, 70)         # Xám đậm

# Màu cạnh
COLOR_EDGE_DEFAULT = (70, 85, 110)
COLOR_EDGE_FINAL = (240, 90, 90)
COLOR_EDGE_BLOCKED = (45, 50, 60)

# Màu CSP Zone
CSP_ZONE_COLORS: dict[str, tuple[int, int, int]] = {
    "User Zone": (50, 120, 200),
    "DMZ": (240, 140, 50),
    "Server Zone": (160, 70, 220),
    "Quarantine Zone": (210, 60, 60),
    None: (40, 100, 180),
}

# Màu text
COLOR_TEXT_PRIMARY = (235, 240, 255) # Sáng rõ
COLOR_TEXT_SECONDARY = (140, 160, 190)
COLOR_TEXT_LOG = (190, 210, 230)
COLOR_TEXT_WARNING = (255, 170, 60)
COLOR_TEXT_ERROR = (255, 75, 75)
COLOR_TEXT_SUCCESS = (60, 210, 110)

# Màu nút & Tab
COLOR_BTN_NORMAL = (28, 40, 65)      # Xanh navy tối
COLOR_BTN_HOVER = (45, 65, 100)
COLOR_BTN_ACTIVE = (20, 100, 220)    # Xanh dương active
COLOR_BTN_DISABLED = (30, 36, 48)
COLOR_BTN_TEXT = (255, 255, 255)

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
