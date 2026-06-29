# Cyber Defense AI Simulator

Ung dung mo phong cac thuat toan AI trong boi canh phong thu mang. Project dung Python + Pygame de ve ban do mang dang do thi, cho phep quan sat tung buoc thuat toan, log hanh dong, thong ke va so sanh ket qua.

## Trang thai hien tai

- Project da duoc cleanup: khong con `tools/`, `assets/`, `__pycache__/`, `.pytest_cache/`.
- File `context.md` cua project da duoc gom ra file `../context.md` o workspace cha.
- Thu muc `tests/` van duoc giu lai de kiem tra regression.
- Lan kiem tra gan nhat: `80 passed`.

## Chuc nang chinh

- Giao dien Pygame dang dashboard dark theme.
- Ban do mang truc quan voi node, edge, chi phi, path va trang thai.
- Chay tung buoc, chay tu dong, tam dung, reset va so sanh nhom thuat toan.
- Log thuat toan theo tung nhom AI.
- Panel thong tin node, chu thich, giam sat, ket qua va ke hoach/duong di.
- Ho tro cuon noi dung dai trong cac panel.
- Tab doi khang co vong choi Hacker vs AI Defender, chon diem xam nhap `PC1` hoac `PC2` va thao tac bang click tren map.

## Nhom thuat toan

| Nhom | Thuat toan |
|---|---|
| Tim kiem mu | BFS, DFS, UCS |
| Tim kiem co phi / heuristic | Greedy Best-First Search, A* Search, IDA* |
| Tim kiem cuc bo | Simple Hill Climbing, Steepest Ascent Hill Climbing, Simulated Annealing |
| CSP - Rang buoc | Backtracking, Forward Checking, Min-Conflicts |
| Moi truong phuc tap | Belief-State Search, Partial-Observable Belief Search, AND-OR Graph Search |
| Moi truong doi khang | Minimax, Alpha-Beta Pruning, Expectimax |

## Cau truc project

```text
Cyber-Defense-AI/
  algorithms/
    adversarial/
    complex_environment/
    csp/
    informed/
    local_search/
    uninformed/
  core/
  maps/
  tests/
  ui/
  main.py
  README.md
  requirements.txt
```

## Du lieu map

Project hien co 7 map JSON:

| File | Muc dich |
|---|---|
| `maps/pathfinding_basic.json` | Tim duong co ban cho BFS/DFS/UCS |
| `maps/weighted_network.json` | Mang co trong so cho UCS, Greedy, A*, IDA* |
| `maps/defense_optimization.json` | Local Search tren do thi trong so |
| `maps/csp_segmentation.json` | Phan vung mang bang CSP |
| `maps/belief_hidden.json` | Moi truong khong quan sat day du |
| `maps/belief_partial.json` | Moi truong quan sat mot phan |
| `maps/adversarial_game.json` | Van Hacker vs AI Defender |

## Cai dat

Yeu cau:

- Python 3.10+
- Pygame
- pytest neu muon chay test

Cai dependency:

```powershell
pip install -r requirements.txt
pip install pytest
```

## Chay ung dung

Tu thu muc `Cyber-Defense-AI/`:

```powershell
python main.py
```

## Chay test

```powershell
python -m pytest tests -q
```

Neu muon chay test ma khong tao cache:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider
```

## Dieu khien

- `Space`: chay / tam dung mo phong.
- `S`: chay mot buoc.
- `R`: reset van hien tai.
- `Esc`: thoat ung dung.
- Mouse wheel: cuon panel/log khi noi dung dai.
- Click node tren map: chon node de xem thong tin hoac thuc hien hanh dong trong tab doi khang.

## Ghi chu

- Day la ung dung mo phong hoc thuat, khong thuc hien tan cong/phong thu mang that.
- Cac thuat toan duoc tach khoi UI va tra ve `StepEvent` de giao dien co the animate tung buoc.
- Khong co license rieng trong repository hien tai.
