# M112 AGV 代码修改说明 / Code Changes Explained


## 0. 一句话总结 / Summary

**中文：** 我们把散在 `main.py`、`line_follow.py` 和 `kip/` 里的代码，重写成一个独立的 `agv/` 程序包。原来的文件**一个都没删、没改**。新代码的转弯是闭环的（看到线才停），不会因为一次读数出错就判断错路口，全程不倒车，而且出任何错都会停电机。所有可调的数字都集中在 `agv/config.py` 一个文件里。路线写成“步骤列表”，以后加 loading area、rack 或完整比赛流程，不用改底层驾驶代码。

**English:** The code that was spread across `main.py`, `line_follow.py` and `kip/` has been rebuilt as a separate `agv/` package. **No original file was deleted or changed.** In the new code, turns are closed-loop (the robot stops turning when it sees the line), one bad sensor reading can no longer cause a wrong junction decision, the robot never reverses along a line, and the motors always stop on any error. Every tunable number lives in one file, `agv/config.py`. Routes are written as lists of steps, so adding loading areas, racks or the full competition flow later does not require touching the low-level driving code.

---

## 1. 新增了哪些文件 / New files

| 文件 File Purpose |
|---|---|---|
| `agv/config.py` | 所有引脚号和可调参数。调参只改这个文件。`[TUNE]` = 要上车实测，`[CHECK]` = 要确认的接线/场地假设 | All pin numbers and tunable values. Tune only this file. `[TUNE]` = must be measured on the robot, `[CHECK]` = wiring/table assumption to confirm |

| `agv/hardware.py` | 电机、巡线传感器、按钮（可选）、琥珀灯、测距传感器（可选）。只有这个文件直接操作 `machine.Pin/PWM/Timer` | Motors, line sensors, optional button, amber light, optional rangefinder. The only file that touches `machine.Pin/PWM/Timer` |

| `agv/nav.py` | 驾驶动作：循线到第 n 个路口、走到拐角、轮轴对准路口、转 90°、原地掉头、进 rack 提前停 | Driving behaviours: follow to the n-th junction, follow to a corner, put the axle on a junction, 90° turn, 180° spin, stop short of a rack |

| `agv/table_map.py` | 场地地图和路线规划，把“从 A 到 B”变成步骤列表 | Table map and route planning: turns "go from A to B" into a list of steps |

| `agv/mission.py` | 任务流程：启动 → loading area 取货 → 掉头 → rack 卸货 → 回 start box | The mission: start → loading area (pickup) → turn round → rack (unload) → back to the start box |

| `agv/calibrate.py` | 调参用的小测试，每个参数对应一个函数 | Small calibration tests, one per parameter |

| `main_line_test.py` | 上车入口，在 Pico 上命名为 `main.py` | Entry point; save it on the Pico as `main.py` |

| `tools/sim_line_test.py` | 在电脑上运行的模拟器，用来检查逻辑 | Laptop simulator for checking the logic |

| `LINE_TEST_README.md` | 中文使用和调参说明 | Usage and tuning guide (Chinese) |

---

## 2. 逐项修改：原问题 → 新做法 → 好处 / Change by change: problem → fix → benefit

### 2.1 程序入口 / Program entry

* **原问题 Problem：** 根目录 `main.py` 实际在跑霍尔传感器测试的死循环，路线代码被注释掉，所以上电后小车不会走。`kip/main.py` 用 `while elapsed() < 300` 一直重复同一条路线，永远不会停。
  The root `main.py` actually runs an endless Hall-sensor test with the route code commented out, so the robot does not move on power-up. `kip/main.py` repeats the same route inside `while elapsed() < 300` and never stops.
* **新做法 Fix：** `main_line_test.py` → `mission.run_line_test()`。整条路线只跑一次，然后停车、关灯。
  `main_line_test.py` → `mission.run_line_test()`. The route runs once, then the robot stops and the light turns off.
* **好处 Benefit：** 上电就能直接做 line test，行为是确定的。
  It is ready for the line test straight from power-up, and its behaviour is predictable.

### 2.2 转弯：定时开环 → 闭环找线 / Turning: timed open loop → closed loop

* **原问题 Problem：** `turn_left()` 先直走 0.8 s 再转 0.82 s，`left180()` 转 1.5 s；`kip` 用 100% 速度转 0.58 s，掉头是两次 90°。电池电压、地面摩擦、打滑一变，角度就不准，而且误差会一个弯接一个弯地累积。
  `turn_left()` drives 0.8 s then spins 0.82 s, and `left180()` spins 1.5 s. `kip` spins at 100% for 0.58 s, and its U-turn is two 90° spins. Any change in battery voltage, floor friction or wheel slip changes the angle, and the error builds up turn after turn.
* **新做法 Fix：** `nav.turn()` / `nav.spin180()` 先“盲转”一段（跳过起点那条线和中途扫过的线），然后一直转，**直到内侧传感器连续 2 次看到新线才停**。定时只用来决定盲转多久和超时多久，超时会报错停车。
  `nav.turn()` and `nav.spin180()` first spin "blind" for a while (to skip the starting line and any lines swept mid-turn), then keep spinning **until an inner sensor sees the new line twice in a row**. Timing only sets the blind period and the timeout; on timeout the robot stops with an error.
* **好处 Benefit：** 每次转完都重新对准线，误差不会累积；电池电量变化也基本不影响。
  The robot is re-aligned on the line after every turn, so errors do not build up, and battery level matters much less.

### 2.3 转之前轮轴对准路口 / Axle on the junction before turning

* **原问题 Problem：** 传感器在车头，看到路口时轮轴还在后面。原代码要么不处理，要么在路口上继续循线往前开，而这时传感器读数是乱的。
  The sensors are at the front, so when they see a junction the axle is still behind it. The old code either ignored this or kept line-following across the junction, where the sensor readings are messy.
* **新做法 Fix：** `nav.to_axle()` 以低速往前开 `SENSOR_TO_AXLE_MS`，让转动中心正好在路口上。经过路口时只用内侧传感器纠偏。
  `nav.to_axle()` creeps forward for `SENSOR_TO_AXLE_MS` so the spin centre sits on the junction, steering with the inner sensors only.
* **好处 Benefit：** 原地转完正好落在新线上，转弯干净。
  After the spin the robot lands right on the new line, which gives clean turns.

### 2.4 路口检测加消抖 / Debounced junction detection

* **原问题 Problem：** 原代码只看一次读数就查表。一个噪声读数（如 `0101`）就算路口；`0000` 被当成 `ENDING` 路口，线短暂丢一下就停车。`kip` 的 `at_junction` 也没有消抖，车偏时 `1100` 会被误判成路口。另外想用单帧图案区分左/右/十字也不可靠，因为车有角度时两侧不会同时压线。
  The old code decided from a single reading. One noisy reading (e.g. `0101`) counted as a junction, and `0000` was an `ENDING` junction, so a brief line loss stopped the robot. `kip`'s `at_junction` had no debounce either, so a drifting `1100` counted as a junction. Telling left/right/cross apart from one frame is also unreliable, because when the robot is at an angle both sides do not hit the line in the same frame.
* **新做法 Fix：** 外侧传感器**和**内侧传感器同时看到白线，并且**连续 3 次**才算路口。同一个路口只计一次：两个外侧都回到黑色后才能计下一个。两个路口之间至少间隔 `JUNCTION_MIN_GAP_MS`。路口方向（L / R / LR）在整个路口窗口内累积判断。
  A junction needs an outer **and** an inner sensor on white **3 samples in a row**. Each junction is counted once; the next one can only be counted after both outer sensors return to black. Consecutive junctions must be at least `JUNCTION_MIN_GAP_MS` apart. The junction direction (L / R / LR) is built up over the whole junction window.
* **好处 Benefit：** 不会被噪声或车身摆动骗到，数路口可靠。
  Noise and wobble no longer fool it, so junction counting is reliable.

### 2.5 拐角不用数路口 / Corners found without counting

* **原问题 Problem：** 从 start box 去右下拐角要经过 start box 边线，到底是数 1 个还是 2 个路口取决于车的尺寸。从 rack 往下走时，相邻 bay 的线可能离得太近，计数容易差 1。
  Between the start box and the bottom-right corner the robot crosses the start box edge, and whether that counts as 1 or 2 junctions depends on the robot's size. Going down from a rack, the neighbouring bay lines can be very close together, so the count can easily be off by one.
* **新做法 Fix：** `nav.follow_to_corner()` 在每个路口往前对准轮轴时检查一下：**如果正前方的线断了，这就是拐角**；没断就继续走。
  `nav.follow_to_corner()` checks at every junction while creeping onto the axle: **if the line straight ahead ends, this is the corner**; otherwise it carries on.
* **好处 Benefit：** 和 start box 边线的位置、bay 间距都无关，换一张桌子也能用（任务说明里写了四张桌子不完全一样）。
  It does not depend on where the box edge is or how far apart the bays are, so it works on any of the tables (the task sheet says the four tables are not identical).

### 2.6 不再倒车循线 / No reversing along lines

* **原问题 Problem：** `kip` 大量使用 `reach_line(REVERSE)`、`follow_straight_line(..., REVERSE)`。传感器在车头，倒车时传感器在运动方向的后面，纠偏不稳定，倒得越远越容易丢线。
  `kip` relies heavily on `reach_line(REVERSE)` and `follow_straight_line(..., REVERSE)`. With the sensors at the front, they are behind the direction of travel when reversing, so steering is unstable and the robot loses the line the further it reverses.
* **新做法 Fix：** 掉头一律用原地 180° 闭环转，然后向前循线。
  Every turn-round is a closed-loop 180° spin on the spot, followed by forward line following.
* **好处 Benefit：** 去掉了最容易丢线的一类动作。
  This removes the kind of move most likely to lose the line.

### 2.7 循线控制：查表 → 比例+微分 / Line following: lookup table → PD control

* **原问题 Problem：** 固定 30 / 50 的减速查表（开关式控制），容易左右摆动。
  A fixed slow-down of 30 or 50 from a lookup table (bang-bang control), which tends to wobble from side to side.
* **新做法 Fix：** 4 个传感器加权（-3, -1, +1, +3）算出线的位置误差，再用 `KP` 比例和 `KD` 微分修正左右轮速度。线短暂丢失时继续朝最后看到线的方向修正，丢太久（`LINE_LOST_MS`）就安全停车。
  The four sensors are weighted (-3, -1, +1, +3) to estimate the line position error, and `KP` (proportional) plus `KD` (derivative) adjust the wheel speeds. If the line is briefly lost, the robot keeps correcting towards where it last saw it; if it stays lost too long (`LINE_LOST_MS`), the robot stops safely.
* **好处 Benefit：** 跟线更平顺，可以调得更快，丢线也不会乱跑。
  Smoother tracking that can be tuned for more speed, and no runaway when the line is lost.

### 2.8 Rack 提前停车（组里反馈后修改）/ Stop short of the rack (changed after team feedback)

* **原问题 Problem：** 开到线的尽头再停，车头会撞到 rack。碰到桌上的设施要扣分并重来。
  Driving to the end of the line makes the nose hit the rack. Hitting table furniture costs points and forces a restart.
* **新做法 Fix：** 转进 rack 线后循线 `RACK_APPROACH_MS` 就停（`RACK_STOP_MODE = 'time'`）。装了 VL53L0X 的话可以改成 `'tof'`，按距离停。线如果提前断了也会马上停，作为保险。
  After turning into the rack line, the robot follows it for `RACK_APPROACH_MS` and stops (`RACK_STOP_MODE = 'time'`). With a VL53L0X fitted, switch to `'tof'` to stop by distance. If the line ends early, it stops immediately as a backup.
* **好处 Benefit：** 不会碰 rack，每个 bay 用同一个参数。
  No contact with the rack, and one parameter covers every bay.

### 2.9 安全 / Safety

* **原问题 Problem：** 没有 `try/finally`，程序报错或按 Ctrl‑C 后，电机会保持最后的 PWM 一直跑。没有琥珀灯闪烁。
  There was no `try/finally`, so after an error or Ctrl-C the motors kept running at the last PWM. There was no flashing amber light.
* **新做法 Fix：** `run_line_test()` 的 `finally` 里**无论如何都停电机、关灯**。丢线、转弯找不到线、超时都会抛 `NavError` 安全停车。琥珀灯用硬件 Timer 闪（2 Hz），主程序忙的时候也照样闪，回到 start box 后关闭（评分要求灯在 start 区是灭的）。按钮目前不接（`USE_BUTTON = False`，上电 3 s 后出发）；装上后设为 True，第一下按启动，运行中再按急停。
  `run_line_test()` always stops the motors and turns the light off in `finally`. A lost line, a turn that cannot find the line, or a timeout raises `NavError` and stops the robot safely. The amber light flashes at 2 Hz from a hardware timer, so it keeps flashing while the main code is busy, and it turns off back in the start box (the scoring requires the light to be off in the start area). There is no button for now (`USE_BUTTON = False`; the run starts 3 s after power-up); once one is fitted, set this to True: the first press starts the run and a press during the run is an emergency stop.
* **好处 Benefit：** 满足 H&S 要求，测试时不会失控，拿到灯光加分。
  It meets the H&S requirements, the robot cannot run away during testing, and it earns the light bonus.

### 2.10 结构和可扩展性 / Structure and extensibility

* **原问题 Problem：** 两套重复的 `motor.py` / `line_sensor.py`，`kip/motor.py` 的注释和引脚对不上，参数散落在各个文件里。
  There were two duplicate copies of `motor.py` / `line_sensor.py`, the comments in `kip/motor.py` did not match its pins, and parameters were scattered across files.
* **新做法 Fix：** 分层：`config` → `hardware` → `nav` → `table_map` → `mission`。场地用“槽位”描述：每侧竖线从下往上，1、2 = loading area，3–8 = 下层 rack bay（例如 B2L = B 侧第 4 个）。`table_map` 已经能生成三种路线：start→任意 bay，同侧或跨侧 bay→bay，bay→start。`Robot.pickup()` / `unload()` 是留给夹爪和霍尔传感器的位置。
  The code is layered: `config` → `hardware` → `nav` → `table_map` → `mission`. The table is described as "slots": on each side line from the bottom, 1 and 2 are the loading areas and 3–8 are the lower rack bays (e.g. B2L = slot 4 on side B). `table_map` can already build three kinds of route: start → any bay, bay → bay (same side or across), and bay → start. `Robot.pickup()` / `unload()` are placeholders for the gripper and the Hall sensor.
* **好处 Benefit：** 换路线只改两个名字（`PICKUP` / `DROP`）。做完整比赛时只需要补取放动作、N/S 极判断和上层 rack 路线，驾驶部分不用重写。
  Changing the route means changing two names (`PICKUP` / `DROP`). For the full competition we only need to add the pick/place actions, N/S pole detection and the upper-rack routes; the driving code stays as it is.

---

## 3. 怎么测试 / How to test

### 3.1 先在电脑上跑模拟器（不需要小车）/ Laptop simulator first (no robot needed)

```bash
cd IDP-M112
python3 tools/sim_line_test.py                                   # 默认路线 / default route LA3 -> B2L
python3 tools/sim_line_test.py pickup=LA1 drop=A3L noise=0.01    # 换路线 + 传感器噪声 / other route + sensor noise
python3 tools/sim_line_test.py mismatch=0.9 plot=run.png         # 左右电机差 10%，并画出轨迹 / 10% motor mismatch, saves a plot (needs Pillow)
```

最后一行显示 `RESULT PASS` 就表示路线跑完，并且整车停在 start box 里。**修改了 `nav.py` / `table_map.py` 以后先跑这个再上车。** 模拟器的场地尺寸是估计的，只用来检查逻辑，不能代替实车调参。

A final line of `RESULT PASS` means the route finished with the whole robot inside the start box. **Run this after any change to `nav.py` or `table_map.py`, before going to the table.** The simulated table size is estimated: it checks the logic, not the real numbers.

### 3.2 上传到 Pico / Upload to the Pico

1. 把 `agv/` 整个文件夹上传到 Pico 根目录（MicroPico：右键 → Upload to Pico）。
   Upload the whole `agv/` folder to the Pico root (MicroPico: right-click → Upload to Pico).
2. 把 `main_line_test.py` 上传到 Pico 并命名为 `main.py`。**不要用 “Upload project”**，否则根目录那个霍尔测试 `main.py` 会覆盖它。
   Upload `main_line_test.py` and save it on the Pico as `main.py`. **Do not use "Upload project"**, or the root Hall-test `main.py` will overwrite it.
3. 如果要用测距模式（`'tof'`），`libs/VL53L0X/` 也要在 Pico 上。
   For the `'tof'` mode, `libs/VL53L0X/` must also be on the Pico.

### 3.3 分步调参（按顺序，每步通过了再做下一步）/ Step-by-step tuning (in order; pass each step before the next)

在 REPL 里输入 / In the REPL:

```python
from agv import calibrate as cal
```

| # | 测试 Test | 调的参数 Parameter | 通过标准（中文） | Pass criterion (English) |
|---|---|---|---|---|
| 1 | `cal.sensors()` | `LINE_SENSOR_PINS` 顺序、`LINE_WHITE`、传感器高度 | 从左到右依次是 LO LI RI RO，白线读 1；车在直线中间时只有内侧两个读 1 | Order is LO LI RI RO from left to right, white reads 1; when centred on a straight line only the two inner sensors read 1 |
| 2 | `cal.straight()` | `*_INVERT`, `LEFT_TRIM`, `RIGHT_TRIM` | 向前走，并且走直线 | Drives forward and straight |
| 3 | `cal.follow()` | `BASE_SPEED`, `KP`（先设 `KD=0`）, `KD` | 跟线平稳不摆 | Tracks the line smoothly without wobbling |
| 4 | `cal.axle()` | `SENSOR_TO_AXLE_MS` ⭐ | 传感器压在横线上开始，结束时轮轴正好在横线上 | Start with the sensors on a cross line; the axle ends exactly on it |
| 5 | `cal.spin('R')`, `cal.spin('R', C.TURN_180_MS)` | `TURN_SPEED`, `TURN_90_MS`, `TURN_180_MS` | 定时转刚好 90° / 180° | The timed spin is exactly 90° / 180° |
| 6 | `cal.junctions(3)` | `JUNCTION_CONFIRM / CLEAR / MIN_GAP_MS` | 每个路口打印且只打印一次 | Each junction is printed exactly once |
| 7 | `cal.turn('L')`, `cal.corner()` | `TURN_BLIND_FRACTION`, `TURN_180_BLIND_FRACTION`, `LINE_END_CONFIRM` | 转完新线在两个内侧传感器之间；在拐角处停下 | After a turn the new line is between the inner sensors; stops at the corner |
| 8 | `cal.rack()` | `RACK_APPROACH_MS`（或 `RACK_STOP_DISTANCE_MM`） | 车头离 rack 留一点空隙停下 | Stops with a small gap between the nose and the rack |
| 9 | 整条路线 Full route | `PARK_MAX_MS`, `PARK_BACKOFF_MS`, `START_DELAY_MS` | 见 3.4 | See 3.4 |

每个 `cal.*` 测试结束或按 Ctrl‑C 时都会自动停电机。
Every `cal.*` test stops the motors when it ends or on Ctrl-C.

### 3.4 整条路线测试 / Full-route test

1. Pico 连着电脑：在 REPL 运行 `from agv import mission; mission.run_line_test()`，可以看到每一步的打印（`junction 1/3 L`、`corner`、`turn L`、`rack: approach time reached`……），哪一步出错一目了然。
   With the Pico connected to the laptop, run `from agv import mission; mission.run_line_test()` in the REPL and watch the printout for each step (`junction 1/3 L`, `corner`, `turn L`, `rack: approach time reached`, …), so it is obvious which step goes wrong.
2. 再不连电脑测：上电 → 3 s 内把车放进 start box（主线下方、车头朝 rack，不要压线）→ 不碰它，看能不能跑完：出 box → 右转 → 拐角 → LA3 停 2 s → 掉头 → B2L 前停 2 s → 掉头 → 回到 box。
   Then test untethered: power on → within 3 s place the robot in the start box (below the main line, facing the racks, not on the line) → hands off, and check it completes: out of the box → right turn → corner → stop at LA3 for 2 s → turn round → stop before B2L for 2 s → turn round → back into the box.
3. 换其他目标再测几次，比如 `mission.run_line_test('LA4', 'B1L')`、`('LA1', 'A3L')`，确认在别的 bay 也能走。
   Repeat with other targets, e.g. `mission.run_line_test('LA4', 'B1L')` or `('LA1', 'A3L')`, to check other bays work too.
4. 满电和半电各跑一次。如果半电时转弯或停车位置明显变了，就把对应的 `[TUNE]` 参数调到中间值。
   Run once on a full battery and once half-charged. If the turns or stopping points change noticeably, set the affected `[TUNE]` values in between.

### 3.5 出问题怎么查 / Troubleshooting

| 现象 Symptom | 可能原因 Likely cause | 怎么做 What to do |
|---|---|---|
| `navigation error: line lost` | 循线速度太快 / `KP` 太小 / 传感器高度不对 | 降低 `BASE_SPEED`，加大 `KP`，重新做 `cal.sensors()` / Lower `BASE_SPEED`, raise `KP`, redo `cal.sensors()` |
| `turn L: line not found` | `TURN_90_MS` 太小（超时），或转弯速度太低转不动 | 重做第 5 步；必要时提高 `TURN_SPEED` / `MIN_DUTY` / Redo step 5; raise `TURN_SPEED` / `MIN_DUTY` if needed |
| 转完偏离新线 / Off the new line after a turn | `SENSOR_TO_AXLE_MS` 不准 | 重做第 4 步 / Redo step 4 |
| 路口数多了 / Too many junctions counted | 车摆动或噪声 | 提高 `JUNCTION_CONFIRM`，或先把循线调稳 / Raise `JUNCTION_CONFIRM`, or tune line following first |
| 路口数少了 / Junctions missed | 速度太快，压线的采样次数不够 | 降低 `BASE_SPEED` 或 `JUNCTION_CONFIRM` / Lower `BASE_SPEED` or `JUNCTION_CONFIRM` |
| 掉头停在错误的线上 / 180° stops on the wrong line | 盲转比例太小 | 提高 `TURN_180_BLIND_FRACTION` / Raise `TURN_180_BLIND_FRACTION` |
| 碰到 rack / Hits the rack | `RACK_APPROACH_MS` 太大 | 减小，或改用 `'tof'` / Reduce it, or switch to `'tof'` |
| 停车不在 box 里 / Parks outside the box | `PARK_BACKOFF_MS` / `PARK_MAX_MS` | 第 9 步调整 / Adjust in step 9 |

---

## 4. 还需要确认的假设 / Assumptions still to confirm

* 左电机 GP4/5，右电机 GP7/6，DIR=1 为前进（来自原代码）。
  Left motor on GP4/5, right motor on GP7/6, DIR = 1 is forward (taken from the original code).
* 琥珀灯 GP28（经三极管驱动）。按钮以后装在 GP22（跳线 29）。
  Amber light on GP28 (driven through a transistor). The button will go on GP22 (jumper 29) later.
* 中线是否延伸进 start box 下半部分 → `CENTRE_LINE_IN_BOX`。
  Whether the centre line continues into the lower half of the start box → `CENTRE_LINE_IN_BOX`.
* A 侧 loading area 编号：下面是 LA2，上面是 LA1（按 Line Test 图）。
  A-side loading area numbering: the lower one is LA2, the upper one LA1 (from the Line Test picture).
* 已知限制：从一个 rack bay 直接去**相邻**的 rack bay，计数可能差 1。比赛流程总是 loading area ↔ rack，不受影响。
  Known limit: going directly from one rack bay to the **adjacent** rack bay can miscount by one. The competition flow is always loading area ↔ rack, so it is not affected.
