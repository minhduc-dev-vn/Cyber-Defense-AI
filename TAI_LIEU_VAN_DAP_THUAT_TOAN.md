# Tài liệu ôn vấn đáp cuối kì: Các thuật toán AI trong project Cyber-Defense-AI

## Mở đầu

Project **Cyber-Defense-AI** là một chương trình mô phỏng các thuật toán trí tuệ nhân tạo trong bối cảnh an ninh mạng. Thay vì trình bày thuật toán trên các ví dụ trừu tượng như mê cung hoặc đồ thị đơn giản, project mô hình hóa một hệ thống mạng gồm các máy trạm, router, switch, firewall, IDS, server và database. Mỗi node trong mạng có các thuộc tính như mức bảo mật, vùng mạng, độ rủi ro bị phát hiện và mức độ quan trọng. Các kết nối giữa node được biểu diễn bằng cạnh có chi phí.

Trong project, các thuật toán không chỉ trả về kết quả cuối cùng mà còn sinh ra từng bước thông qua `StepEvent`. Nhờ đó giao diện Pygame có thể hiển thị quá trình chạy thuật toán: node đang xét, frontier, explored, đường đi hiện tại, log giải thích và thống kê. Đây là điểm quan trọng khi vấn đáp, vì có thể nói rằng project không chỉ cài thuật toán để ra đáp án, mà còn trực quan hóa cách thuật toán suy luận.

File `Thuật toán cần báo cáo.txt` yêu cầu báo cáo 6 thuật toán:

1. UCS - Uniform Cost Search
2. Greedy Best-First Search
3. Simulated Annealing
4. AND-OR Graph Search
5. Forward Checking
6. Alpha-Beta Pruning trong nhóm đối kháng Minimax/Expectimax

Các thuật toán này đại diện cho nhiều nhóm bài toán AI khác nhau: tìm kiếm không có thông tin, tìm kiếm có heuristic, tìm kiếm cục bộ, lập kế hoạch trong môi trường không chắc chắn, bài toán thỏa ràng buộc và trò chơi đối kháng.

## Tổng quan mô hình project

Trước khi đi vào từng thuật toán, cần nắm được cách project biểu diễn bài toán.

Trong project, mạng máy tính được biểu diễn bởi lớp `NetworkGraph`. Mỗi node có thể là:

- `pc`: máy trạm
- `router`: bộ định tuyến
- `switch`: bộ chuyển mạch
- `firewall`: tường lửa
- `ids`: hệ thống phát hiện xâm nhập
- `server`: máy chủ
- `database`: cơ sở dữ liệu

Mỗi cạnh có `base_cost`. Khi tính chi phí thực tế để đi từ node này sang node khác, project không chỉ dùng `base_cost`, mà cộng thêm các yếu tố bảo mật:

```text
edge_cost = base_cost
          + security_level * SECURITY_WEIGHT
          + detection_risk * DETECTION_WEIGHT
          + firewall_penalty nếu đi qua firewall
          + ids_penalty nếu đi qua IDS
```

Vì vậy, trong project, một đường đi ngắn về số bước chưa chắc là đường đi tốt. Đường đi qua firewall hoặc server có thể rất đắt vì mức bảo mật và rủi ro bị phát hiện cao. Đây là nền tảng để giải thích vì sao các thuật toán như UCS, Greedy hay A* cho kết quả khác nhau.

Các thuật toán được chia theo nhóm:

- Nhóm tìm kiếm đường đi: BFS, DFS, UCS, Greedy, A*, IDA*
- Nhóm tìm kiếm cục bộ: Simple Hill Climbing, Steepest Hill Climbing, Simulated Annealing
- Nhóm CSP: Backtracking, Forward Checking, Min-Conflicts
- Nhóm môi trường phức tạp: Belief-State Search, Partial-Observable Search, AND-OR Graph Search
- Nhóm đối kháng: Minimax, Alpha-Beta, Expectimax

Tài liệu này tập trung vào 6 thuật toán cần báo cáo.

---

# 1. Uniform Cost Search - UCS

## 1.1. Khái niệm

Uniform Cost Search là thuật toán tìm kiếm đường đi có tổng chi phí nhỏ nhất từ trạng thái ban đầu đến trạng thái mục tiêu. UCS thuộc nhóm tìm kiếm không có thông tin, vì nó không sử dụng heuristic để ước lượng khoảng cách còn lại đến mục tiêu. Thuật toán chỉ dựa vào chi phí thực tế đã đi được, kí hiệu là `g(n)`.

Nếu BFS mở rộng node theo thứ tự độ sâu, DFS mở rộng node theo nhánh sâu nhất, thì UCS mở rộng node theo tổng chi phí nhỏ nhất. Do đó UCS đặc biệt phù hợp với đồ thị có trọng số, nơi mỗi cạnh có chi phí khác nhau.

Trong bối cảnh an ninh mạng của project, UCS có thể được hiểu là thuật toán giúp Hacker tìm đường xâm nhập có chi phí thấp nhất, trong đó chi phí bao gồm độ khó đi qua node, mức bảo mật và rủi ro bị phát hiện.

## 1.2. Nguyên lý hoạt động

UCS duy trì một hàng đợi ưu tiên, trong đó mỗi phần tử là một node đi kèm với chi phí từ Start đến node đó. Thuật toán luôn lấy node có chi phí nhỏ nhất ra để mở rộng.

Mã giả:

```text
frontier = priority queue
đưa Start vào frontier với cost = 0
g[Start] = 0
parent[Start] = None

while frontier không rỗng:
    current = node có g(current) nhỏ nhất

    if current là Goal:
        trả về đường đi từ Start đến current

    for mỗi neighbor của current:
        new_cost = g(current) + cost(current, neighbor)
        if neighbor chưa được tới hoặc new_cost nhỏ hơn cost cũ:
            g[neighbor] = new_cost
            parent[neighbor] = current
            đưa neighbor vào frontier
```

Điểm quan trọng là UCS không dừng khi vừa nhìn thấy goal trong frontier. UCS chỉ dừng khi goal được lấy ra khỏi priority queue. Lý do là tại thời điểm đó, goal là node có chi phí nhỏ nhất trong tất cả các node đang chờ xét, nên không còn đường nào rẻ hơn.

## 1.3. Tính chất

UCS có các tính chất sau:

- **Hoàn chỉnh**: UCS sẽ tìm được lời giải nếu lời giải tồn tại và chi phí các cạnh không âm.
- **Tối ưu**: UCS đảm bảo tìm được đường đi có tổng chi phí nhỏ nhất nếu mọi cạnh có chi phí không âm.
- **Không dùng heuristic**: UCS chỉ dựa vào chi phí thực tế `g(n)`.
- **Chi phí bộ nhớ có thể cao**: Vì phải lưu nhiều node trong priority queue.

Độ phức tạp thường phụ thuộc vào số node, số cạnh và phân bố chi phí. Nếu so với BFS, UCS có thể tốn thêm chi phí quản lý priority queue.

## 1.4. So sánh với thuật toán cùng nhóm

Trong project, UCS nằm trong nhóm tìm kiếm không có thông tin cùng BFS và DFS.

| Tiêu chí | BFS | DFS | UCS |
|---|---|---|---|
| Cách chọn node | Node nông nhất | Node sâu nhất | Node có tổng chi phí nhỏ nhất |
| Có xét trọng số cạnh không | Không | Không | Có |
| Tối ưu số bước | Có, nếu cạnh bằng nhau | Không | Không nhất thiết |
| Tối ưu chi phí | Chỉ khi mọi cạnh cùng cost | Không | Có, nếu cost không âm |
| Phù hợp | Đồ thị không trọng số | Tìm nhanh một nhánh | Đồ thị có trọng số |

Trong vấn đáp có thể nhấn mạnh:

> UCS là phiên bản tổng quát hơn BFS cho đồ thị có trọng số. Nếu mọi cạnh có cùng chi phí, UCS hoạt động gần giống BFS. Nhưng khi chi phí cạnh khác nhau, UCS tối ưu hơn BFS vì nó chọn theo tổng chi phí thay vì số bước.

## 1.5. UCS trong project Cyber-Defense-AI

File cài đặt: `algorithms/uninformed/ucs.py`

Trong project, UCS được áp dụng cho bài toán Hacker tìm đường đến Server hoặc Database với chi phí thấp nhất. Thuật toán sử dụng:

- `frontier`: priority queue chứa `(cost, node_id)`
- `g_cost`: lưu chi phí tốt nhất đã biết đến mỗi node
- `reached`: lưu parent để dựng lại đường đi
- `neighbors_with_cost()`: lấy các node kề và chi phí thực tế

Khi chạy trên `maps/weighted_network.json`, kết quả hiện tại là:

```text
success: True
steps: 8
expanded: 7
generated: 7
cost: 33.4
path: Hacker -> Switch_B -> PC_B -> Switch_C -> Database
```

Ý nghĩa kết quả:

- UCS chọn đường đến `Database` thay vì `Server` vì đường đến Database có tổng chi phí thấp hơn.
- Dù đường đi không nhất thiết ngắn nhất theo số bước, nhưng nó là đường có chi phí tốt nhất theo công thức của project.
- Điều này phản ánh thực tế an ninh mạng: một tuyến ngắn qua firewall hoặc server zone có thể rủi ro hơn tuyến dài nhưng ít bị phát hiện.

## 1.6. Cách giải thích khi demo

Khi demo UCS trên giao diện, có thể trình bày:

> Mỗi bước UCS lấy node có tổng chi phí từ Hacker đến node đó nhỏ nhất. Các node trong frontier được sắp theo `g(n)`. Khi thuật toán lấy được Database ra khỏi frontier, nó dừng vì đã chứng minh rằng không còn đường nào có chi phí thấp hơn.

Nếu giảng viên hỏi vì sao không chọn đường ngắn hơn, có thể trả lời:

> Vì UCS không tối ưu số bước, UCS tối ưu tổng chi phí. Trong project, chi phí bao gồm base cost, security level, detection risk và penalty của firewall/IDS, nên đường ít bước hơn chưa chắc rẻ hơn.

## 1.7. Câu hỏi vấn đáp mẫu

**Hỏi:** UCS có dùng heuristic không?

**Trả lời:** Không. UCS chỉ dùng chi phí thực tế đã đi được `g(n)`. Vì vậy UCS thuộc nhóm tìm kiếm không có thông tin.

**Hỏi:** Khi nào UCS tối ưu?

**Trả lời:** UCS tối ưu khi tất cả chi phí cạnh không âm. Khi goal được lấy ra khỏi priority queue, đó là đường có chi phí nhỏ nhất.

**Hỏi:** UCS khác Dijkstra không?

**Trả lời:** Về bản chất rất giống Dijkstra khi tìm đường ngắn nhất từ một nguồn. UCS thường được trình bày trong AI như một thuật toán tìm kiếm dừng khi gặp goal, còn Dijkstra thường tính khoảng cách ngắn nhất từ một nguồn đến nhiều node.

---

# 2. Greedy Best-First Search

## 2.1. Khái niệm

Greedy Best-First Search là thuật toán tìm kiếm có thông tin. Thuật toán sử dụng heuristic `h(n)` để ước lượng mức độ gần của node hiện tại đến mục tiêu. Khác với UCS, Greedy không quan tâm chi phí đã đi từ Start đến node hiện tại. Nó chỉ quan tâm node nào có vẻ gần goal nhất.

Công thức đánh giá:

```text
f(n) = h(n)
```

Vì chỉ nhìn vào heuristic, Greedy thường chạy nhanh và mở rộng ít node. Tuy nhiên, nó không đảm bảo tìm được đường có chi phí thấp nhất.

## 2.2. Nguyên lý hoạt động

Greedy dùng priority queue, nhưng thay vì ưu tiên `g(n)`, nó ưu tiên `h(n)`.

Mã giả:

```text
frontier = priority queue
đưa Start vào frontier với priority = h(Start)

while frontier không rỗng:
    current = node có h(current) nhỏ nhất

    if current là Goal:
        trả về đường đi

    for mỗi neighbor:
        nếu neighbor chưa được reached:
            parent[neighbor] = current
            đưa neighbor vào frontier với priority = h(neighbor)
```

Đặc điểm của thuật toán là tính tham lam. Ở mỗi bước, Greedy chọn phương án có vẻ tốt nhất ngay trước mắt.

## 2.3. Tính chất

- **Không đảm bảo tối ưu**: Vì bỏ qua chi phí đã đi.
- **Có thể nhanh**: Nếu heuristic tốt, Greedy có thể đến goal rất nhanh.
- **Có thể bị đánh lừa**: Nếu node gần goal theo heuristic nhưng đường đi qua đó có chi phí cao.
- **Phụ thuộc mạnh vào heuristic**.

## 2.4. So sánh với UCS, A* và IDA*

Greedy thuộc nhóm tìm kiếm có heuristic cùng A* và IDA*. Nhưng để hiểu rõ, cũng nên so sánh với UCS.

| Thuật toán | Hàm ưu tiên | Có dùng chi phí đã đi? | Có dùng heuristic? | Tối ưu? |
|---|---|---|---|---|
| UCS | `g(n)` | Có | Không | Có nếu cost không âm |
| Greedy | `h(n)` | Không | Có | Không |
| A* | `g(n) + h(n)` | Có | Có | Có nếu heuristic admissible |
| IDA* | `g(n) + h(n)` theo ngưỡng | Có | Có | Có trong điều kiện phù hợp |

Greedy có thể được xem là thuật toán thiên về tốc độ, còn UCS thiên về đảm bảo tối ưu. A* là sự kết hợp của hai hướng này.

## 2.5. Greedy trong project Cyber-Defense-AI

File cài đặt: `algorithms/informed/greedy_search.py`

Project dùng heuristic:

```text
h(n) = số hop ngắn nhất từ n đến goal * minimum_edge_cost
```

Heuristic này cho biết node nào có vẻ gần goal hơn về mặt số bước. Tuy nhiên, nó không phản ánh đầy đủ các chi phí bảo mật như firewall penalty, security level hay detection risk.

Kết quả trên `maps/weighted_network.json`:

```text
success: True
steps: 6
expanded: 5
generated: 6
cost: 65.4
path: Hacker -> PC_A -> Router_A -> Firewall -> Server
```

Trong khi UCS trên cùng map tìm được:

```text
cost: 33.4
path: Hacker -> Switch_B -> PC_B -> Switch_C -> Database
```

Điều này cho thấy Greedy chọn đường có vẻ gần goal hơn nhưng tổng chi phí cao hơn. Đây là ví dụ rất tốt để trình bày nhược điểm của Greedy.

## 2.6. Cách giải thích khi demo

Khi demo, có thể nói:

> Greedy nhìn vào `h(n)` nên chọn nhánh đi qua `PC_A`, `Router_A`, `Firewall` vì nhánh này có vẻ gần Server hơn. Tuy nhiên, do Firewall và Server có chi phí bảo mật cao, tổng chi phí thực tế lớn. Điều này chứng minh Greedy nhanh nhưng không đảm bảo tối ưu.

## 2.7. Câu hỏi vấn đáp mẫu

**Hỏi:** Greedy có tối ưu không?

**Trả lời:** Không. Greedy chỉ chọn node có `h(n)` nhỏ nhất, không tính chi phí đã đi. Vì vậy nó có thể chọn đường nhìn gần goal nhưng chi phí thực tế cao.

**Hỏi:** Khi nào Greedy hoạt động tốt?

**Trả lời:** Khi heuristic phản ánh tốt khoảng cách thực tế đến goal và chi phí đường đi không quá khác biệt.

**Hỏi:** Vì sao Greedy trong project có cost cao hơn UCS?

**Trả lời:** Vì Greedy đi theo hướng có ít hop đến Server, nhưng đường đó đi qua Firewall và các node có mức bảo mật cao. UCS thì xét chi phí thực tế nên chọn đường rẻ hơn.

---

# 3. Simulated Annealing

## 3.1. Khái niệm

Simulated Annealing là thuật toán tìm kiếm cục bộ dựa trên ý tưởng mô phỏng quá trình tôi luyện kim loại. Trong luyện kim, vật liệu được nung nóng rồi làm nguội dần để đạt cấu trúc ổn định. Trong AI, thuật toán bắt đầu với mức "nhiệt độ" cao để dễ khám phá, sau đó giảm dần nhiệt độ để hội tụ.

Điểm đặc biệt của Simulated Annealing là nó có thể chấp nhận cả bước đi xấu. Đây là khác biệt quan trọng so với Hill Climbing.

Trong bài toán tối thiểu hóa:

- Nếu trạng thái mới tốt hơn: chấp nhận.
- Nếu trạng thái mới xấu hơn: có thể vẫn chấp nhận với xác suất nhất định.

Xác suất chấp nhận bước xấu:

```text
P = exp(-delta / T)
```

Trong đó:

- `delta = h(next) - h(current)`
- `T` là nhiệt độ hiện tại
- `delta > 0` nghĩa là trạng thái mới xấu hơn

Khi `T` cao, xác suất chấp nhận bước xấu cao. Khi `T` giảm, thuật toán trở nên thận trọng hơn.

## 3.2. Nguyên lý hoạt động

Mã giả:

```text
current = trạng thái ban đầu
T = T0

while T > Tmin:
    next = chọn ngẫu nhiên một neighbor
    delta = value(next) - value(current)

    if delta <= 0:
        current = next
    else:
        chấp nhận next với xác suất exp(-delta / T)

    T = T * alpha
```

Trong project, bài toán được mô hình hóa theo hướng tìm đường đến goal, nên trạng thái là node hiện tại. Hàm heuristic là chi phí đường ngắn nhất còn lại từ node hiện tại đến Server.

## 3.3. So sánh với Hill Climbing

| Tiêu chí | Simple Hill Climbing | Steepest Hill Climbing | Simulated Annealing |
|---|---|---|---|
| Cách chọn neighbor | Chọn neighbor tốt hơn đầu tiên | Xét tất cả neighbor, chọn tốt nhất | Chọn neighbor ngẫu nhiên |
| Có nhận bước xấu không | Không | Không | Có, theo xác suất |
| Dễ kẹt cực trị địa phương | Có | Có | Ít hơn |
| Tính ngẫu nhiên | Thấp | Thấp | Cao |
| Đảm bảo tối ưu | Không | Không | Không trong thời gian hữu hạn |

Simulated Annealing có ưu điểm là thoát được cực trị địa phương. Tuy nhiên, do có yếu tố ngẫu nhiên, kết quả có thể khác nhau nếu đổi seed hoặc tham số nhiệt độ.

## 3.4. Simulated Annealing trong project

File cài đặt: `algorithms/local_search/simulated_annealing.py`

Map sử dụng: `maps/defense_optimization.json`

Trong project:

- `current` là node hiện tại của Hacker.
- Neighbor là các node kề trong graph.
- `h(n)` là chi phí đường ngắn nhất từ node `n` đến Server.
- Mục tiêu là đến Server, tức `h(n) = 0`.

Các tham số hiện tại đã được chỉnh để phù hợp demo:

```text
T0 = 5.0
alpha = 0.85
Tmin = 0.1
seed = 42
```

Kết quả chạy:

```text
success: True
steps: 16
cost: 21.0
accepted_worse_moves: 2
path:
Hacker -> PC1 -> Switch1 -> PC1 -> Hacker -> PC1 -> Switch1 -> Router -> FW_Slot1 -> Server
```

Kết quả này có ý nghĩa:

- Thuật toán không đi thẳng hoàn toàn.
- Có lúc quay lại node cũ, ví dụ `Switch1 -> PC1 -> Hacker`.
- Đây không phải lỗi, mà là biểu hiện của việc chấp nhận bước xấu.
- Cuối cùng thuật toán vẫn tìm được Server.

## 3.5. Cách giải thích khi demo

Có thể trình bày:

> Simulated Annealing trong project chọn ngẫu nhiên một node kề. Nếu node đó làm heuristic giảm, thuật toán chấp nhận ngay. Nếu heuristic tăng, thuật toán vẫn có thể chấp nhận với xác suất `exp(-delta/T)`. Vì vậy ta thấy đường đi có thể quay lại, nhưng điều này giúp thuật toán tránh bị kẹt ở cực trị địa phương.

Nếu giảng viên hỏi vì sao đường đi không tối ưu, trả lời:

> Vì Simulated Annealing không phải thuật toán tìm đường tối ưu như UCS hay A*. Đây là thuật toán tìm kiếm cục bộ có tính xác suất, mục tiêu là tìm lời giải đủ tốt, không đảm bảo ngắn nhất.

## 3.6. Câu hỏi vấn đáp mẫu

**Hỏi:** Tại sao Simulated Annealing chấp nhận bước xấu?

**Trả lời:** Để tránh kẹt ở cực trị địa phương. Nếu chỉ luôn chọn bước tốt hơn, thuật toán có thể dừng tại một trạng thái không phải tối ưu toàn cục.

**Hỏi:** Vai trò của nhiệt độ là gì?

**Trả lời:** Nhiệt độ quyết định mức độ sẵn sàng chấp nhận bước xấu. Nhiệt độ cao giúp khám phá nhiều hơn, nhiệt độ thấp giúp hội tụ.

**Hỏi:** Simulated Annealing có đảm bảo tối ưu không?

**Trả lời:** Không đảm bảo trong số bước hữu hạn. Nó là thuật toán heuristic có tính xác suất.

---

# 4. AND-OR Graph Search

## 4.1. Khái niệm

AND-OR Graph Search là thuật toán dùng cho bài toán lập kế hoạch trong môi trường không chắc chắn. Trong môi trường như vậy, một hành động không nhất thiết chỉ dẫn đến một kết quả duy nhất. Thay vào đó, cùng một hành động có thể dẫn đến nhiều kết quả khác nhau.

Do đó, lời giải không phải là một đường đi đơn giản, mà là một kế hoạch có điều kiện.

Cấu trúc AND-OR gồm:

- **OR node**: tác nhân được chọn một hành động trong nhiều hành động.
- **AND node**: môi trường tạo ra nhiều kết quả có thể xảy ra, và kế hoạch phải xử lý được tất cả kết quả đó.

Ví dụ:

```text
Thử cô lập Firewall
    Nếu thành công: hệ thống an toàn
    Nếu thất bại: chặn Router và Switch
```

Đây là kế hoạch điều kiện. Nó không chỉ nói "làm A", mà còn nói "nếu kết quả là X thì làm gì, nếu kết quả là Y thì làm gì".

## 4.2. Nguyên lý hoạt động

Thuật toán tìm kiếm trên cây kế hoạch:

```text
AND-OR-SEARCH(state):
    if state là goal:
        return plan rỗng

    for mỗi action:
        plans = {}
        for mỗi outcome của action:
            subplan = AND-OR-SEARCH(result(outcome))
            if subplan thất bại:
                action này thất bại
        nếu mọi outcome đều có subplan:
            return plan gồm action và các subplan

    return failure
```

Điểm cốt lõi:

- Ở OR node, chỉ cần chọn một action tốt.
- Ở AND node, tất cả outcome của action đó đều phải giải được.

## 4.3. So sánh với các thuật toán môi trường phức tạp

Trong project, AND-OR nằm cùng nhóm với Belief-State Search và Partial-Observable Search.

| Thuật toán | Vấn đề chính | Kết quả trả về |
|---|---|---|
| Belief-State Search | Không biết chính xác trạng thái thật | Tập trạng thái có thể |
| Partial-Observable Search | Có quan sát một phần | Belief được cập nhật theo quan sát |
| AND-OR Graph Search | Hành động có nhiều kết quả | Kế hoạch điều kiện |

AND-OR phù hợp khi tác nhân phải lập kế hoạch trước cho nhiều khả năng xảy ra.

## 4.4. AND-OR trong project

File cài đặt: `algorithms/complex_environment/and_or_graph.py`

Trong project:

- Defender không chắc Hacker đang ở đâu.
- Tập vị trí có thể của Hacker gọi là `belief`.
- Defender thử các hành động cô lập node như Router, Switch, Firewall.
- Mỗi hành động có thể thành công hoặc có outcome dự phòng.
- Mục tiêu là làm cho mọi vị trí có thể của Hacker không còn đường đến goal.

Kết quả trên `maps/belief_hidden.json`:

```text
success: True
steps: 24
expanded: 13
plan:
Try isolate Firewall
  If success -> Safe with blocked=['Firewall']
  If fallback -> Safe with blocked=['Router', 'Switch']
```

Ý nghĩa:

- Nếu chặn Firewall thành công, mọi khả năng tấn công bị vô hiệu hóa.
- Nếu không thể chặn Firewall trực tiếp, phương án dự phòng là chặn Router và Switch.
- Vì cả hai outcome đều dẫn đến trạng thái an toàn, kế hoạch hợp lệ.

## 4.5. Cách giải thích khi demo

Khi demo, có thể nói:

> AND-OR không tìm một đường đi cho Hacker, mà tìm kế hoạch phòng thủ cho Defender trong môi trường không chắc chắn. Một hành động phòng thủ có thể có nhiều kết quả, nên thuật toán phải đảm bảo tất cả nhánh kết quả đều an toàn.

## 4.6. Câu hỏi vấn đáp mẫu

**Hỏi:** Vì sao gọi là AND-OR?

**Trả lời:** Vì có hai loại node. OR node là nơi agent chọn một hành động trong nhiều hành động. AND node là nơi hành động có nhiều kết quả, và tất cả kết quả đó đều phải có kế hoạch xử lý.

**Hỏi:** AND-OR khác tìm kiếm đường đi thông thường như thế nào?

**Trả lời:** Tìm kiếm đường đi thông thường trả về một path. AND-OR trả về một kế hoạch điều kiện, vì môi trường có nhiều outcome.

**Hỏi:** Trong project, AND-OR dùng để làm gì?

**Trả lời:** Dùng để lập kế hoạch phòng thủ khi Defender không chắc vị trí Hacker và không chắc hành động cô lập node sẽ có kết quả nào.

---

# 5. Forward Checking

## 5.1. Khái niệm CSP

Forward Checking là kỹ thuật giải bài toán thỏa ràng buộc, gọi là CSP - Constraint Satisfaction Problem.

Một CSP gồm:

- **Variables**: các biến cần gán giá trị
- **Domains**: miền giá trị có thể của từng biến
- **Constraints**: các ràng buộc cần thỏa

Ví dụ trong project:

- Variables: các node mạng
- Domains: các vùng mạng như User Zone, DMZ, Server Zone, Quarantine Zone
- Constraints: server phải ở Server Zone, máy bị compromise phải ở Quarantine, hai node kề nhau không được cùng zone,...

## 5.2. Forward Checking là gì?

Backtracking cơ bản sẽ thử gán giá trị cho biến, nếu sai thì quay lui. Forward Checking cải tiến bằng cách sau khi gán một biến, nó kiểm tra trước các biến chưa gán và loại bỏ những giá trị chắc chắn không còn hợp lệ.

Ví dụ:

Nếu gán:

```text
PC1 = User Zone
```

và `PC1` nối với `Router`, đồng thời ràng buộc là hai node kề nhau không được cùng zone, thì Forward Checking sẽ xóa `User Zone` khỏi domain của `Router`.

Nếu domain của biến nào đó bị rỗng, thuật toán biết ngay nhánh này thất bại và quay lui sớm.

## 5.3. Nguyên lý hoạt động

Mã giả:

```text
Backtrack(assignment):
    if mọi biến đã được gán:
        return assignment

    var = chọn biến chưa gán

    for value in domain[var]:
        if value nhất quán với assignment:
            gán var = value
            lưu lại domains cũ
            prune domain của các biến liên quan

            if không domain nào rỗng:
                result = Backtrack(assignment)
                if result thành công:
                    return result

            khôi phục domains
            bỏ gán var

    return failure
```

## 5.4. So sánh với Backtracking và Min-Conflicts

| Thuật toán | Cách hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| Backtracking | Thử gán, sai thì quay lui | Đơn giản, đầy đủ | Có thể phát hiện lỗi muộn |
| Forward Checking | Gán xong thì prune domain tương lai | Phát hiện thất bại sớm | Tốn chi phí quản lý domain |
| Min-Conflicts | Bắt đầu bằng assignment đầy đủ rồi sửa xung đột | Tốt cho bài toán lớn | Không đảm bảo luôn tìm lời giải |

Forward Checking vẫn là backtracking, nhưng thông minh hơn vì kiểm tra tương lai.

## 5.5. Forward Checking trong project

File cài đặt: `algorithms/csp/forward_checking.py`

Bài toán trong project là phân vùng mạng an toàn. Các zone gồm:

- User Zone
- DMZ
- Server Zone
- Quarantine Zone

Domain ban đầu được tạo trong `algorithms/csp/common.py`:

- Server/Database chỉ có thể là `Server Zone`
- Node bị compromise phải là `Quarantine Zone`
- PC không bị compromise có thể là `User Zone`, `DMZ`, hoặc `Quarantine Zone`

Ràng buộc:

- Node server/database phải ở Server Zone.
- Node compromised phải ở Quarantine Zone.
- PC không được ở Server Zone.
- Hai node kề nhau không được cùng zone.
- User PC không được chung zone với server/database nếu có kết nối.

Kết quả trên `maps/csp_segmentation.json`:

```text
success: True
steps: 18
expanded: 8
conflicts: []
assignments:
PC2 = Quarantine Zone
Server = Server Zone
Database = Server Zone
PC1 = User Zone
Switch = DMZ
Router = User Zone
Firewall = DMZ
DMZ_Node = User Zone
```

Ý nghĩa:

- Thuật toán đã tìm được cách phân vùng mạng không vi phạm ràng buộc.
- `conflicts = []` cho biết lời giải cuối cùng hợp lệ.
- Việc prune domain giúp giảm số nhánh phải thử.

## 5.6. Cách giải thích khi demo

Có thể nói:

> Mỗi node mạng là một biến CSP. Mỗi biến có domain là các zone mạng. Forward Checking lần lượt gán zone cho node, sau đó loại bỏ các zone không còn hợp lệ ở các node kề. Nếu domain của node nào bị rỗng, thuật toán quay lui ngay, nhờ vậy tránh thử những nhánh chắc chắn sai.

## 5.7. Câu hỏi vấn đáp mẫu

**Hỏi:** Forward Checking khác Backtracking ở điểm nào?

**Trả lời:** Backtracking chỉ kiểm tra ràng buộc với biến đã gán. Forward Checking sau khi gán một biến sẽ cập nhật domain của các biến chưa gán để phát hiện lỗi sớm.

**Hỏi:** Forward Checking có làm mất lời giải không?

**Trả lời:** Không, vì nó chỉ loại các giá trị chắc chắn vi phạm ràng buộc với assignment hiện tại.

**Hỏi:** Vì sao phân vùng mạng phù hợp với CSP?

**Trả lời:** Vì ta cần gán mỗi node vào một zone sao cho thỏa nhiều ràng buộc bảo mật. Đây đúng là dạng bài toán biến - miền giá trị - ràng buộc.

---

# 6. Nhóm thuật toán đối kháng - Minimax, Alpha-Beta, Expectimax

## 6.1. Luật mô hình đối kháng

Nhóm đối kháng dùng cho bài toán có nhiều tác nhân với mục tiêu trái ngược nhau. Trong project, trò chơi được mô hình hóa như cuộc đấu giữa Hacker và Defender:

- **Hacker là MAX**: muốn tối đa hóa điểm tấn công.
- **Defender là MIN**: muốn làm điểm của Hacker thấp nhất.
- **Chance node**: dùng trong Expectimax để mô hình hóa yếu tố xác suất như IDS phát hiện hoặc bỏ sót Hacker.

Điểm quan trọng là Minimax và Alpha-Beta giả định đối thủ chơi tối ưu. Defender không chọn ngẫu nhiên trong hai thuật toán này; Defender luôn chọn hành động gây bất lợi nhất cho Hacker. Expectimax mới dùng giá trị kỳ vọng cho các kết quả xác suất.

## 6.2. State và action trong project

File dùng chung: `algorithms/adversarial/common.py`

Một `GameState` trong mode đối kháng gồm:

- Vị trí hiện tại của Hacker.
- Các node bị chặn.
- Các cạnh bị chặn.
- Các IDS và firewall đang tồn tại.
- Các node đã được nâng cấp.
- Trạng thái Hacker đã bị phát hiện hay chưa.
- Lượt hiện tại là Hacker, Defender hoặc chance.
- Số lượt còn lại và lịch sử hành động.

Action của Hacker:

- `move`: di chuyển sang node kề nếu node/cạnh không bị chặn.
- `scan`: quét node hiện tại, đổi lại có thể bị phát hiện.

Action của Defender:

- `block_node`: chặn một node để cắt đường đi.
- `deploy_ids`: kích hoạt IDS để tăng khả năng phát hiện.
- `upgrade`: nâng cấp node nếu không có IDS sẵn.

Trong code có khai báo thêm `block_edge`, nhưng hàm sinh action hiện tại chủ yếu chọn `block_node`, `deploy_ids` và `upgrade`. Vì vậy khi demo nên nói theo hành động thực tế mà thuật toán đang sinh ra.

## 6.3. Hàm đánh giá

Các thuật toán đối kháng trong project đều quy về điểm của Hacker bằng hàm `hacker_value()`. Điểm càng cao thì càng tốt cho Hacker, càng thấp thì càng tốt cho Defender.

Các mốc điểm chính:

- Hacker vào `Database`: `+1000`.
- Hacker vào `Server`: `+500`.
- Hacker càng gần Server/Database thì điểm càng tăng.
- Hacker đứng ở node bảo mật thấp thì được cộng lợi thế.
- Hacker bị IDS phát hiện: `-150`.
- Hacker không còn đường tới goal: `-300`.

Do đó Defender trong vai MIN sẽ chọn hành động làm giá trị `hacker_value()` nhỏ nhất.

## 6.4. Minimax

Minimax là thuật toán gốc của nhóm đối kháng xác định. Thuật toán xây cây game đến một độ sâu giới hạn. Ở tầng Hacker thì chọn giá trị lớn nhất, ở tầng Defender thì chọn giá trị nhỏ nhất.

Mã giả:

```text
Minimax(state, depth):
    if depth == 0 hoặc state terminal:
        return evaluate(state)

    if state là lượt MAX:
        value = -infinity
        for action in actions(state):
            value = max(value, Minimax(result(state, action), depth - 1))
        return value

    if state là lượt MIN:
        value = +infinity
        for action in actions(state):
            value = min(value, Minimax(result(state, action), depth - 1))
        return value
```

Trong project, Minimax nằm ở `algorithms/adversarial/minimax.py`. Thuật toán thử từng hành động gốc của Hacker, giả lập Defender phản ứng tối ưu, rồi chọn hành động có điểm cuối cùng cao nhất cho Hacker.

## 6.5. Alpha-Beta Pruning

Alpha-Beta là phiên bản tối ưu của Minimax. Nó không thay đổi luật chọn nước đi, chỉ giảm số nhánh phải duyệt.

Alpha-Beta dùng hai biến:

- `alpha`: giá trị tốt nhất mà MAX hiện có thể đảm bảo.
- `beta`: giá trị tốt nhất mà MIN hiện có thể đảm bảo.

Nếu trong quá trình duyệt:

```text
alpha >= beta
```

thì nhánh còn lại có thể bị cắt, vì nó chắc chắn không làm thay đổi quyết định cuối cùng.

Mã giả:

```text
AlphaBeta(state, depth, alpha, beta):
    if depth == 0 hoặc state terminal:
        return evaluate(state)

    if state là lượt MAX:
        value = -infinity
        for action in actions(state):
            value = max(value, AlphaBeta(result(state, action), depth - 1, alpha, beta))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    if state là lượt MIN:
        value = +infinity
        for action in actions(state):
            value = min(value, AlphaBeta(result(state, action), depth - 1, alpha, beta))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value
```

File cài đặt: `algorithms/adversarial/alpha_beta.py`

Khi chạy trên `maps/adversarial_game.json`, Alpha-Beta chọn nước đi đầu cho Hacker và ghi thêm số nhánh bị cắt trong `pruned_branches`. Nếu cùng depth, cùng action và cùng hàm đánh giá, Alpha-Beta cho cùng quyết định với Minimax nhưng thường xét ít trạng thái hơn.

## 6.6. Expectimax

Expectimax dùng khi môi trường có yếu tố xác suất. Trong project, yếu tố xác suất là IDS có thể:

- Phát hiện Hacker với xác suất `0.70`.
- Bỏ sót Hacker với xác suất `0.30`.

File cài đặt: `algorithms/adversarial/expectimax.py`

Trong Expectimax của project có ba loại tầng:

- MAX node: Hacker chọn hành động có điểm kỳ vọng cao nhất.
- MIN node: Defender vẫn chọn hành động làm điểm Hacker thấp nhất.
- Chance node: kết quả phát hiện/bỏ sót được tính bằng kỳ vọng xác suất.

Công thức tại chance node:

```text
expected_value = p1 * value(outcome1) + p2 * value(outcome2) + ...
```

Vì vậy, Expectimax không nói rằng Defender chơi ngẫu nhiên. Trong project này, Defender vẫn là MIN; phần ngẫu nhiên chỉ nằm ở kết quả IDS phát hiện hay không phát hiện.

## 6.7. So sánh ba thuật toán

| Thuật toán | Luật chọn | Có xác suất? | Có cắt tỉa? | Vai trò trong project |
|---|---|---|---|---|
| Minimax | MAX chọn max, MIN chọn min | Không | Không | Mô phỏng Hacker và Defender đều chơi tối ưu |
| Alpha-Beta | Giống Minimax | Không | Có | Tối ưu Minimax bằng cách bỏ nhánh không ảnh hưởng kết quả |
| Expectimax | MAX/MIN kết hợp chance node | Có | Không trong bản hiện tại | Tính kỳ vọng khi IDS có xác suất phát hiện hoặc bỏ sót |

Điểm cần nhớ:

- Minimax là nền tảng.
- Alpha-Beta là Minimax có cắt tỉa, không phải thuật toán chọn nước đi khác.
- Expectimax dùng expected value cho kết quả ngẫu nhiên, không dùng `min` ở chance node.

## 6.8. Cách giải thích khi demo

Có thể nói:

> Ở nhóm đối kháng, project mô hình hóa Hacker là MAX và Defender là MIN. Minimax duyệt cây nước đi, Hacker chọn nhánh có điểm cao nhất còn Defender chọn nhánh làm điểm Hacker thấp nhất. Alpha-Beta giữ nguyên luật Minimax nhưng dùng `alpha` và `beta` để cắt các nhánh chắc chắn không ảnh hưởng đến quyết định. Expectimax bổ sung chance node để tính xác suất IDS phát hiện hoặc bỏ sót Hacker.

## 6.9. Câu hỏi vấn đáp mẫu

**Hỏi:** Minimax, Alpha-Beta và Expectimax khác nhau thế nào?

**Trả lời:** Minimax dùng MAX-MIN trong môi trường đối kháng xác định. Alpha-Beta là Minimax có cắt tỉa nên nhanh hơn nhưng giữ nguyên kết quả nếu cùng điều kiện. Expectimax thêm chance node để tính giá trị kỳ vọng khi có kết quả xác suất.

**Hỏi:** Alpha-Beta có làm thay đổi kết quả của Minimax không?

**Trả lời:** Không. Alpha-Beta chỉ bỏ qua các nhánh chắc chắn không ảnh hưởng đến quyết định cuối cùng. Nếu cùng depth, cùng action và cùng hàm đánh giá, kết quả chọn nước đi giống Minimax.

**Hỏi:** Khi nào xảy ra cắt tỉa Alpha-Beta?

**Trả lời:** Khi `alpha >= beta`. Nghĩa là MAX đã có lựa chọn đủ tốt, còn MIN đã có giới hạn khiến nhánh hiện tại không thể trở thành lựa chọn tốt hơn.

**Hỏi:** Expectimax có nghĩa là Defender chọn ngẫu nhiên không?

**Trả lời:** Không trong project này. Defender vẫn là MIN. Phần ngẫu nhiên nằm ở chance node, ví dụ IDS phát hiện Hacker với xác suất `0.70` hoặc bỏ sót với xác suất `0.30`.

**Hỏi:** Vì sao nhóm đối kháng phù hợp với bài toán Hacker vs Defender?

**Trả lời:** Vì mục tiêu hai bên trái ngược nhau. Hacker muốn tiến tới Server/Database để tăng điểm, còn Defender muốn chặn đường, kích hoạt IDS hoặc làm Hacker bị phát hiện để giảm điểm Hacker.

---

# Kết luận chung

Sáu thuật toán trong báo cáo đại diện cho sáu hướng giải quyết bài toán AI khác nhau.

UCS thể hiện tư duy tối ưu chi phí trong đồ thị có trọng số. Greedy thể hiện sức mạnh và rủi ro của heuristic. Simulated Annealing minh họa tìm kiếm cục bộ có yếu tố xác suất và khả năng thoát cực trị địa phương. AND-OR Graph Search cho thấy cách lập kế hoạch trong môi trường không chắc chắn. Forward Checking biểu diễn bài toán phân vùng mạng như một CSP và giải bằng cách lan truyền ràng buộc. Nhóm đối kháng mô hình hóa cuộc đấu giữa Hacker và Defender bằng Minimax, Alpha-Beta và Expectimax.

Điểm mạnh của project là mỗi thuật toán đều được đặt vào một ngữ cảnh an ninh mạng cụ thể. Do đó khi vấn đáp, không nên chỉ nói lý thuyết khô, mà nên gắn với project:

- Node là thiết bị mạng.
- Edge là kết nối.
- Cost là chi phí/rủi ro tấn công.
- Goal là Server hoặc Database.
- Defender có thể chặn, cô lập, phát hiện hoặc phân vùng mạng.

Nếu cần trả lời ngắn gọn trước hội đồng, có thể dùng bảng sau.

| Thuật toán | Một câu dễ nhớ | Vai trò trong project |
|---|---|---|
| UCS | Chọn node có `g(n)` nhỏ nhất | Tìm đường tấn công có chi phí thấp nhất |
| Greedy | Chọn node có `h(n)` nhỏ nhất | Minh họa heuristic nhanh nhưng không tối ưu |
| Simulated Annealing | Chấp nhận bước xấu theo xác suất | Tìm kiếm cục bộ trên đường đi có thể quay lui |
| AND-OR | Lập kế hoạch cho mọi outcome | Kế hoạch phòng thủ khi kết quả không chắc chắn |
| Forward Checking | Gán biến và prune domain tương lai | Phân vùng mạng thỏa ràng buộc bảo mật |
| Nhóm đối kháng | MAX-MIN, cắt tỉa hoặc chance node | Hacker/Defender suy luận đối kháng |

## Phần trả lời mẫu khi được hỏi tổng quan project

Nếu giảng viên hỏi: "Project của em áp dụng AI như thế nào?", có thể trả lời:

> Project của em mô phỏng các thuật toán AI trong bối cảnh phòng thủ mạng. Hệ thống mạng được biểu diễn bằng đồ thị, trong đó node là các thiết bị như PC, Router, Firewall, IDS, Server và Database; cạnh là các kết nối có chi phí. Các thuật toán tìm kiếm được dùng để mô phỏng Hacker tìm đường xâm nhập, CSP dùng để phân vùng mạng an toàn, AND-OR dùng để lập kế hoạch phòng thủ trong môi trường không chắc chắn, còn nhóm đối kháng dùng Minimax, Alpha-Beta và Expectimax cho trò chơi giữa Hacker và Defender. Mỗi thuật toán sinh ra từng StepEvent để giao diện hiển thị quá trình suy luận, không chỉ hiển thị kết quả cuối cùng.

## Phần cần học thuộc nhanh

- UCS: tối ưu chi phí bằng `g(n)`, dùng priority queue.
- Greedy: nhanh vì dùng `h(n)`, nhưng không đảm bảo tối ưu.
- Simulated Annealing: có thể đi xấu hơn nhờ xác suất `exp(-delta/T)`.
- AND-OR: OR là chọn hành động, AND là mọi kết quả đều phải có kế hoạch.
- Forward Checking: sau khi gán biến thì loại giá trị không hợp lệ khỏi domain tương lai.
- Minimax: Hacker là MAX, Defender là MIN.
- Alpha-Beta: giống Minimax nhưng cắt nhánh khi `alpha >= beta`.
- Expectimax: thêm chance node, tính giá trị kỳ vọng cho phát hiện/bỏ sót IDS.
