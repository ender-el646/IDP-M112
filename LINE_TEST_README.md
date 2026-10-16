# Line Following Test 代码说明（M112）

新代码全部在 `agv/` 文件夹和 `main_line_test.py` 里。**原来的文件（根目录的 `main.py`、`line_follow.py`、`motor.py`、`line_sensor.py` 和 `kip/` 文件夹）一个都没改。**

```
agv/
  config.py      所有引脚和可调参数（只改这一个文件来调参）
  hardware.py    电机、巡线传感器、按钮、琥珀灯（只有这个文件直接碰 machine.Pin/PWM）
  nav.py         驾驶动作：循线到第 n 个路口、走到拐角、对准轴心、转 90°、原地掉头
  table_map.py   场地地图 + 路线规划（路线是一串步骤，可以打印、可以加新路线）
  mission.py     任务流程：按钮启动 → 去 loading area → 掉头 → 去 rack → 回 start box
  calibrate.py   调参用的小测试，每个参数对应一个
main_line_test.py  上车时把它作为 main.py 上传
tools/sim_line_test.py  电脑上运行的模拟器（不是给 Pico 用的）
```

## 1. 现有代码的主要问题

根目录版本（`main.py` / `line_follow.py`）：

1. **`main.py` 现在跑的是霍尔传感器测试的死循环**，路线代码整段被注释掉，上电后小车不会走。
2. **转弯全靠 `sleep` 定时**（`turn_left` 先直走 0.8 s 再转 0.82 s，`left180` 转 1.5 s），是开环控制。电池电压、地面、打滑一变，角度就不准，而且误差会一个弯一个弯地累积。
3. **路口判断只看一次读数、没有消抖**。一个噪声读数（比如 `0101`）就会被当成路口；`0000` 被定义成 `ENDING` 路口，线短暂丢一下 `follow_to_junction()` 就停车返回了。
4. **想用单帧图案区分左转/右转/十字不可靠**：车身有一点角度时，左右外侧传感器不会在同一帧压到横线上。
5. **纠偏是固定 30/50 的查表（开关式控制）**，容易左右摆。
6. **没有 `try/finally`**：程序报错或按 Ctrl‑C 后，电机会保持最后的 PWM 一直跑（README 里也写了 motor keeps running），这是安全问题。

`kip/` 版本（状态机，结构更好，新代码的路线思路参考了它）：

7. **大量倒车循线**（`reach_line(REVERSE)`、`follow_straight_line(..., REVERSE)`）。传感器装在车头，倒车时传感器在运动方向的后面，纠偏不稳定，倒得越远越容易丢线。
8. **`rotate_bot` 用 100% 速度定时 0.58 s 转 90°**，`u_turn` 是两次定时 90°，误差翻倍。
9. **`at_junction` 没有消抖**，并且车偏时外侧和内侧同时压线（如 `1100`）也会被误判为路口。
10. 在路口停下后 `rotation_from_front` 用循线的方式往前开，但这时传感器正压在横线上，纠偏读数是乱的。
11. **`main.py` 的 `while elapsed() < 300` 会不停重复这条路线**；回到 INITIAL 后停在主线路口上，没有开进 start box。
12. 没有启动按钮，没有琥珀灯闪烁（任务要求，也是 +10 分项），按钮也不能急停。
13. 两套 `motor.py` / `line_sensor.py` 重复存在，`kip/motor.py` 的注释和实际引脚对不上（`motor_right` 注释写 GP4/5，实际是 GP7/6），容易改了一份忘了另一份。

## 2. 新代码怎么走（默认路线：LA3 → B2L，对应 Line Test 1.png）

| 段 | 动作 |
|---|---|
| 出发 | 上电后等 3 s（`START_DELAY_MS`，用来把车放进 box）→ 琥珀灯开始闪 → 向前开到主线（第 1 个路口）→ 轴心对准路口 → 右转 |
| 去拐角 | 沿主线往右，经过 start box 右边线，**直到“前方线断了”的那个路口就是拐角**（不用数路口）→ 左转朝上 |
| 去 loading area 3 | 数左侧分支：第 1 个 → 左转 → 开到 loading area 白框停下 → 模拟取货 2 s |
| 去 rack B2L | 原地掉头 → 回到右侧主线 → 左转朝上 → 再数 3 个分支（LA4、B1L、B2L）→ 左转 → 沿 rack 线走 `RACK_APPROACH_MS` 后**提前停下，不开到线尽头** → 模拟卸货 2 s |
| 回家 | 掉头 → 回到右侧主线 → 右转朝下 → 走到拐角 → 右转 → 数 2 个路口（box 右边线、中线路口）→ 左转朝下 → 开到 box 下边线 → 稍微后退 → 停车，灯灭 |

比原代码可靠的地方：

* **转弯是闭环的**：先盲转一段（跳过起始的线），然后一直转到内侧传感器连续 2 次看到新线才停，有超时保护。定时只用来决定“盲转多久”和“超时多久”。
* **路口检测有消抖**：外侧传感器 + 内侧传感器连续 3 次压线才算路口，一个路口只计一次，离开后才能计下一个。
* **循线用比例+微分控制**（4 个传感器加权求线的位置），过路口时忽略外侧传感器。
* **不倒车循线**。掉头一律原地转 180°。
* **拐角靠“直行方向的线断了”识别**，不依赖 start box 边线的位置，也不怕邻近的 rack 分支离得太近。
* 任何情况（报错、丢线、Ctrl‑C）都会在 `finally` 里停电机、关灯。
* 现在不接按钮（`USE_BUTTON = False`），上电延时出发。以后装了按钮把它改成 True：第一次按 = 启动，运行中再按 = 急停。
* rack 停车不靠“线断了”：转进 rack 线后循线固定时间就停（`RACK_STOP_MODE = 'time'`）；如果装了 VL53L0X 测距，可以改成 `'tof'`，按距离停。线提前断了也会立即停，作为保险。
* 琥珀灯用硬件 Timer 闪，主程序忙的时候也照样闪；在 start box 里是灭的（评分要求）。

在电脑模拟器里（近似场地），默认路线和 A/B 两侧其他组合都能跑通，包括传感器噪声、左右电机差 10%、转向时间误差 ±20%、起步歪 6° 的情况。模拟器只能验证逻辑，**真实数值必须上车调**。

## 3. 上传和运行

1. 把 `agv/` 整个文件夹上传到 Pico 根目录（MicroPico：右键文件夹 → Upload to Pico）。
2. 把 `main_line_test.py` 上传到 Pico，并在 Pico 上命名为 `main.py`。
   **不要用 “Upload project” 上传整个仓库**，否则 Pico 上的 `main.py` 会被根目录那个霍尔测试覆盖。
3. 上电 → 3 s 内放进 start box（车在主线**下方**、车头朝 rack 方向，不要压在主线上）→ 自动出发。
4. 换目标：改 `agv/mission.py` 里的 `PICKUP` / `DROP`，或者 `mission.run_line_test('LA4', 'B1L')`。名字见 `table_map.PLACES`。

## 4. 需要实测的参数（按这个顺序调）

在 REPL 里 `from agv import calibrate as cal`，然后：

| 顺序 | 测试 | 调的参数（`config.py`） | 判断标准 |
|---|---|---|---|
| 1 | `cal.sensors()` | `LINE_SENSOR_PINS` 顺序、`LINE_WHITE`，传感器高度 | 从左到右 LO LI RI RO；白线 = 1。车在直线正中时内侧两个看到线，外侧两个看不到 |
| 2 | `cal.straight()` | `*_INVERT`、`LEFT_TRIM`/`RIGHT_TRIM`、`MIN_DUTY` | 往前走、走直线 |
| 3 | `cal.follow()` | `BASE_SPEED`、`KP`（先 `KD = 0`）、再 `KD` | 稳定跟线不摆 |
| 4 | `cal.axle()` | `SENSOR_TO_AXLE_MS`（**最关键**） | 传感器压在横线上开始，结束时轮轴正好在横线上 |
| 5 | `cal.spin('R')` / `cal.spin('R', C.TURN_180_MS)` | `TURN_SPEED`、`TURN_90_MS`、`TURN_180_MS` | 定时转刚好 90° / 180° |
| 6 | `cal.junctions(3)` | `JUNCTION_CONFIRM`、`JUNCTION_CLEAR`、`JUNCTION_MIN_GAP_MS` | 每个路口打印且只打印一次 |
| 7 | `cal.turn('L')`、`cal.corner()` | `TURN_BLIND_FRACTION`、`TURN_180_BLIND_FRACTION`、`LINE_END_CONFIRM` | 转完新线在两个内侧传感器之间；在拐角停 |
| 8 | `cal.rack()`（车刚转进 rack 线时运行） | `RACK_APPROACH_MS`（或 `'tof'` 模式的 `RACK_STOP_DISTANCE_MM`） | 车头离 rack 留一点空隙停下 |
| 9 | 整条路线 | `BAY_STOP_EXTRA_MS`、`PARK_MAX_MS`、`PARK_BACKOFF_MS`、`START_DELAY_MS` | 停车时整车在 box 里 |

现在的默认值是根据 kip 测过的 0.58 s/90°、0.6 s 到轴心（100% 速度）换算成较低速度估出来的，只是起点。

## 5. 需要确认的假设（`config.py` 里标了 [CHECK]）

* 现在没有按钮。以后装上（假设在 GP22，跳线 29，按下读 1）就设 `USE_BUTTON = True`。注意任务要求最终要有 start/stop 按钮。
* **琥珀灯在 GP28**（跳线 34，经三极管驱动）。
* 起点：车在 start box 里主线下方，车头朝 rack（已确认）。中线是否延伸进 box 下半部分：`CENTRE_LINE_IN_BOX`。
* 回程从拐角到中线路口会经过 **2 个路口**（box 边线 + 中线）：`JUNCTIONS_CORNER_TO_CENTRE`。
* A 侧 loading area 编号（下面的是 LA2、上面的是 LA1，按图）在 `table_map.PLACES`。
* 几何限制：在 loading area 停车时，**轮轴到侧边主线的距离要大于传感器到轮轴的距离**，否则掉头时会先扫到侧边主线。传感器尽量靠近轮轴、但又在车头前方，转弯最稳。
* `RACK_APPROACH_MS` 是从转进 rack 线算起的时间，所以每个 rack bay 用同一个值（各 bay 线长度一样的前提下）。电池电量会影响速度，比赛前用满电再确认一次；更稳的做法是装 VL53L0X 改用 `'tof'`。

## 6. 以后扩展到完整任务

* `Robot.pickup()` / `Robot.unload()` 是占位函数，以后放夹爪/执行器和霍尔传感器判断 N/S 极（红/绿灯）。
* 任意 loading area ↔ 任意 lower rack（同侧或跨侧）的路线 `table_map.bay_to_bay()` 已经有了；跨侧那段在模拟器里跑通过，没上过车。
* 上层 rack（走中线上坡道）、红绿灯红外信号、“bay 是否被占”检查，都可以作为新的步骤类型加进 `table_map.py` / `Robot.execute()`，不需要改 `nav.py`。
* 已知限制：从一个 rack bay 直接去相邻的 rack bay 时，转出来那一刻传感器可能已经压在下一条分支上，计数可能差 1。比赛流程总是 loading area ↔ rack，不受影响。
