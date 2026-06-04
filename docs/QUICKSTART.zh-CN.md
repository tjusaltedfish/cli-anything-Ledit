# Codex/CLI-Anything 接入 L-Edit 快速上手

这个 harness 用 `cli-anything-ledit` 生成 Tanner L-Edit 可执行的
Tanner Command File，即 `.tco` 文件。L-Edit 里通过 Command Window 执行
`run "C:/.../脚本.tco"` 来画版图。注意 `run ...` 是 L-Edit Command
Window 命令，不是 PowerShell 命令。

## 1. 检查 L-Edit 状态

在普通 PowerShell 里运行：

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness
cli-anything-ledit --json inspect
```

当前这台机器上检测到的 L-Edit 路径是：

```text
C:\Program Files\Tanner EDA\Tanner Tools v16.3\ledit64.exe
```

如果输出里看到：

```json
"can_send_run_command": false
```

说明当前 L-Edit 进程暂时没有暴露可见窗口句柄，自动发送 `run` 命令可能失败。
可以先确认 L-Edit 主窗口在桌面上可见，再运行下面第 6 节的自动发送命令；如果仍然
失败，就用手动稳定路径：生成脚本，然后把 `.run.txt` 里的 `run` 命令粘到
L-Edit Command Window。

## 2. 一条 CLI 命令生成并验证阵列

推荐用 `draw-square-array`。它会同时生成 `.tco`、`.svg`、`.run.txt`、
`.open.ps1`，并自动验证方块数量、边界和首尾方块坐标。

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

cli-anything-ledit --json draw-square-array `
  --rows 6 `
  --cols 9 `
  --size 1.2 `
  --pitch-x 2.4 `
  --pitch-y 2.8 `
  --origin-x 5 `
  --origin-y 7 `
  --layer CURRENT `
  --cell TOP `
  --out .\outputs\acceptance_6x9.tco `
  --launch
```

成功时 JSON 里应看到：

```json
"ok": true,
"verified": true,
"box_count": 54,
"run_file": "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\outputs\\acceptance_6x9.run.txt",
"powershell_open_file": "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\outputs\\acceptance_6x9.open.ps1"
```

生成的四个文件是：

```text
outputs\acceptance_6x9.tco
outputs\acceptance_6x9.svg
outputs\acceptance_6x9.run.txt
outputs\acceptance_6x9.open.ps1
```

其中 `.tco` 是 L-Edit 执行的脚本，`.svg` 是预览图，`.run.txt` 里只有一行
L-Edit 命令。`.open.ps1` 是给 PowerShell 执行的辅助脚本：它会启动 L-Edit，
并把 L-Edit 的 `run ...` 命令复制到剪贴板。

## 3. 在 L-Edit 里绘制

注意：下面这行不是 PowerShell 命令，不能在 PowerShell 里执行。它只能粘贴到
L-Edit 的 Command Window 里执行。

打开 L-Edit 的 Command Window，执行 `.run.txt` 里的那一行。例如：

```text
run "C:/Users/ASUS/Documents/L_edit/agent-harness/outputs/acceptance_6x9.tco"
```

默认 `--layer CURRENT` 不会输出 `layer ...` 命令，而是画在 L-Edit 当前
激活的已有图层上。这样可以避开空库或工艺库里没有 `Metal1` 时的
`Can't find layer "Metal1"` 错误。如果你确认某个图层已存在，也可以传
`--layer 真实图层名`。

## 3a. 测试某个命名 layer 能不能用

如果你想画到 `Metal1` 这类命名 layer，先生成一个很小的探针脚本：

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

cli-anything-ledit --json layer-probe `
  --layer Metal1 `
  --cell TOP `
  --out .\outputs\probe_metal1.tco
```

然后把 `.run.txt` 里的这一类命令粘到 L-Edit Command Window：

```text
run "C:/Users/ASUS/Documents/L_edit/agent-harness/outputs/probe_metal1.tco"
```

如果 L-Edit 仍然报 `Can't find layer "Metal1"`，说明当前文件/工艺库不能通过
普通 command-window 脚本使用这个层；此时请继续用 `--layer CURRENT`，或者先在
L-Edit 的 Setup > Layers 里手动建好/导入工艺层。更可靠的自动建层需要 UPI 宏
接口，例如文档里的 `LLayer_New(...)`，不属于普通 `.tco` 命令。

如果你想在 PowerShell 里执行一个文件，请运行 `.open.ps1`：

```powershell
powershell -ExecutionPolicy Bypass -File .\outputs\acceptance_6x9.open.ps1
```

它会启动 L-Edit，并把真正应该粘到 L-Edit Command Window 的 `run ...` 命令复制到剪贴板。

## 4. 常用参数

```text
--rows       行数
--cols       列数
--size       方块边长
--pitch      X/Y 相同周期
--pitch-x    X 方向周期
--pitch-y    Y 方向周期
--origin-x   左下角原点 X
--origin-y   左下角原点 Y
--layer      L-Edit 图层名；默认 CURRENT 表示使用当前激活图层
--cell       L-Edit cell 名
--out        输出 .tco 路径
--launch     生成后启动 L-Edit
```

如果 `--pitch-x/--pitch-y` 不填，只填 `--pitch`，则 X/Y 使用同一个周期。

## 5. PowerShell helper 版本

也可以使用 helper：

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

powershell -ExecutionPolicy Bypass -File .\scripts\New-LEditSquareArray.ps1 `
  -Rows 6 `
  -Cols 9 `
  -Size 1.2 `
  -PitchX 2.4 `
  -PitchY 2.8 `
  -OriginX 5 `
  -OriginY 7 `
  -Layer CURRENT `
  -Cell TOP `
  -Name acceptance_6x9 `
  -Launch
```

helper 默认也会验证生成结果，并返回 `verified: true`。

## 6. 自动发送 run 命令

注意：`--send-run-command` 和 `run-script` 使用的是交互式 SendKeys 路线，会把
L-Edit 切到前台并输入命令。它不是后台命令行执行。只有当你允许 Codex/脚本短暂接管
前台时再用这一节；平时建议先用第 6b 节的生成/验证命令，不会碰你的鼠标键盘。

交互式直接发送命令是：

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

cli-anything-ledit --json draw-square-array `
  --rows 4 `
  --cols 5 `
  --size 0.8 `
  --pitch 1.5 `
  --origin-x 10 `
  --origin-y 20 `
  --layer CURRENT `
  --cell TOP `
  --out .\outputs\codex_direct_send_4x5.tco `
  --send-run-command
```

成功时 JSON 里会看到：

```json
"verified": true,
"sent_run_command": true
```

它会自动完成三件事：

1. 生成 `.tco` 和 `.svg` 预览；
2. 验证脚本里的方块数量、边界、首尾坐标；
3. 把 `run "C:/.../xxx.tco"` 发送到当前 L-Edit Command Window。

PowerShell helper 也支持同样的自动发送：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\New-LEditSquareArray.ps1 `
  -Rows 6 `
  -Cols 9 `
  -Size 1.2 `
  -PitchX 2.4 `
  -PitchY 2.8 `
  -OriginX 5 `
  -OriginY 7 `
  -Layer CURRENT `
  -Cell TOP `
  -Name acceptance_6x9 `
  -SendRunCommand
```

如果自动发送失败，请看 JSON 里的 `send.error`。常见原因是 L-Edit 主窗口当前没有
暴露可枚举窗口句柄；把 L-Edit 主窗口切到前台或重新打开 Command Window 后再试。
手动在 Command Window 执行 `.run.txt` 里的命令仍然是兜底路径。

## 6a. 关于 UPI 宏批处理

`macro-square-array`、`macro-selection-action`、`macro-object-action`、
`macro-file-action`、`macro-layer-action`、`macro-cell-action`、
`macro-window-action` 和 `macro-smoke` 已经可以生成并编译 UPI 宏。生成和编译
不会碰前台窗口；只有加 `--execute` 时才会启动 `ledit64.exe -U <macro>`。

在当前已有 L-Edit 单实例进程存在时，`ledit64.exe -U <macro>` 会启动/转发到已有
进程，却没有触发 receipt 文件，因此还不能作为推荐执行路径。等关闭已有 L-Edit 后，
可以继续验证完全无窗口、无焦点的批处理路线。

## 6b. 不止方形矩阵：组合版图脚本

如果任务不是单纯方形矩阵，使用 `layout-script`。它读取一个 JSON 文件，生成一个
包含多种 L-Edit Command Window 操作的 `.tco`。当前已支持：

```text
comment       注释
cell          切换/创建 cell
layer         切换 layer
box           画矩形
square-array  方形矩阵快捷操作
path / wire   画线/路径
polygon       画多边形
text          放置文字/端口标签
width         设置线宽
goto          移动视图中心
instance      放置 cell instance
array         对当前选中 instance 做阵列
copy          复制当前选中对象
move          移动当前选中对象
paste         粘贴复制缓冲区对象
rotate        旋转当前选中对象
saveas        另存为 TDB
raw           直接插入一行 L-Edit 命令，但禁止嵌套 run
```

示例 JSON：

```json
{
  "title": "mixed layout",
  "cell": "TOP",
  "layer": "CURRENT",
  "operations": [
    {"op": "box", "x1": 0, "y1": 0, "x2": 4, "y2": 2},
    {"op": "path", "points": [[0, 4], [4, 4], [4, 8]], "width": 0.4},
    {"op": "polygon", "points": [[6, 0], [10, 0], [8, 4]]},
    {"op": "text", "label": "NET_A", "x": 0, "y": 6},
    {"op": "square-array", "rows": 2, "cols": 3, "size": 0.8, "pitch": 1.4, "origin_x": 12, "origin_y": 0},
    {"op": "instance", "cell": "SUBCELL", "x": 20, "y": 0},
    {"op": "copy"},
    {"op": "paste", "x": 24, "y": 0},
    {"op": "rotate", "angle": 90, "x": 0, "y": 0}
  ]
}
```

保存为 `outputs\layout.json` 后，推荐先生成并验证，不抢 L-Edit 前台：

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

cli-anything-ledit --json layout-script `
  .\outputs\layout.json `
  --out .\outputs\layout.tco

cli-anything-ledit --json verify-layout-script .\outputs\layout.tco
```

如果你明确允许脚本把 L-Edit 切到前台输入 Command Window 命令，再额外加
`--send-run-command`。

你也可以查看当前分层能力清单：

```powershell
cli-anything-ledit --json capabilities
```

这条路线覆盖的是稳定、可脚本化的绘图编辑层。L-Edit 所有 UI 里更复杂的部分，
比如工艺/图层设置对话框、DRC/提取配置、宏管理窗口、批处理 TDB 生成等，后面应当
继续作为 UPI 命令或专门 backend 命令扩展，而不是用一个巨大脆弱的鼠标录制脚本硬顶。

## 6c. 直接基础命令

如果你只是想画一个对象、移动一点、或者保存另存为，可以直接用单命令入口，不必
先写 JSON：

```powershell
cli-anything-ledit --json box --x1 0 --y1 0 --x2 4 --y2 2 --out .\outputs\box.tco
cli-anything-ledit --json path --point 0 0 --point 4 0 --point 4 4 --width 0.4 --out .\outputs\path.tco
cli-anything-ledit --json polygon --point 0 0 --point 4 0 --point 2 3 --out .\outputs\polygon.tco
cli-anything-ledit --json text --label NET_A --x 0 --y 6 --out .\outputs\text.tco
cli-anything-ledit --json instance --cell-name SUBCELL --x 20 --y 0 --out .\outputs\instance.tco
cli-anything-ledit --json array --cols 3 --rows 2 --pitch-x 5 --pitch-y 5 --out .\outputs\array.tco
cli-anything-ledit --json move --x 2 --y 0 --mode relative --out .\outputs\move.tco
cli-anything-ledit --json rotate --angle 90 --x 0 --y 0 --out .\outputs\rotate.tco
cli-anything-ledit --json saveas --path C:\tmp\layout_copy.tdb --out .\outputs\saveas.tco
```

这些命令默认只生成并验证 `.tco`，不会碰你正在用的 L-Edit 前台窗口。
如果你要真正让 L-Edit 执行 `.tco`，继续看上面的 `run-script` 或手动把
`.run.txt` 复制到 Command Window。

## 6d. UPI selection 宏

`macro-selection-action` 提供一层不靠键盘的选择集编辑宏，适合这类操作：

```powershell
cli-anything-ledit --json macro-selection-action --action select-all --compile
cli-anything-ledit --json macro-selection-action --action move --dx 1 --dy 0 --compile
cli-anything-ledit --json macro-selection-action --action group --group-name CodexGroup --compile
cli-anything-ledit --json macro-selection-action --action merge --compile
cli-anything-ledit --json macro-selection-action --action flatten --compile
```

支持的 action 包括 `select-all`、`deselect-all`、`cut`、`copy`、`clear`、
`paste`、`duplicate`、`group`、`ungroup`、`merge`、`flatten`、
`flip-horizontal`、`flip-vertical`、`snap-to-mfg-grid`、`move`、`rotate`。

## 6e. UPI object 宏

有些对象用 UPI 比普通 `.tco` Command Window 语法更稳，比如圆和 port：

```powershell
cli-anything-ledit --json macro-object-action `
  --kind circle `
  --x 0 `
  --y 0 `
  --radius 2 `
  --out .\outputs\object_circle_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-object-action `
  --kind port `
  --label IN `
  --x1 0 `
  --y1 0 `
  --x2 2 `
  --y2 1 `
  --layer CURRENT `
  --out .\outputs\object_port_nofocus.cpp `
  --compile
```

当前支持 `circle` 和 `port`。这些命令只生成/编译宏，不会自动执行，也不会抢你的
鼠标键盘。只有额外加 `--execute` 才会尝试让 L-Edit 通过 `-U` 加载宏。

## 6f. UPI selected-object 属性宏

这一层补的是当前选中对象的属性和转换操作：

```powershell
cli-anything-ledit --json macro-object-property-action `
  --action set-net-name `
  --net-name NET_A `
  --out .\outputs\object_prop_net_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-object-property-action `
  --action set-gds-datatype `
  --gds-datatype 12 `
  --out .\outputs\object_prop_gdsdt_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-object-property-action `
  --action change-layer `
  --layer Mask2 `
  --out .\outputs\object_prop_layer_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-object-property-action `
  --action snap-to-grid `
  --grid 0.25 `
  --out .\outputs\object_prop_snap_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-object-property-action `
  --action convert-to-polygon `
  --out .\outputs\object_prop_polygon_nofocus.cpp `
  --compile
```

当前支持的 action 是 `set-gds-datatype`、`set-net-name`、`clear-net-name`、
`change-layer`、`snap-to-grid`、`snap-to-mfg-grid`、`copy-to-layer`、
`delete`、`convert-to-polygon`。这些动作真正执行时作用于 L-Edit 当前 selection。

## 6g. UPI file/cell/view 宏

这一层补的是文件、cell 和视图相关的基础操作，也不走键盘输入：

```powershell
cli-anything-ledit --json macro-file-action `
  --action new `
  --path .\outputs\new_layout.tdb `
  --cell TOP `
  --out .\outputs\file_new_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-file-action `
  --action open-cell `
  --cell SUBCELL `
  --out .\outputs\file_open_cell_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-file-action `
  --action home-view `
  --out .\outputs\file_home_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-file-action `
  --action move-origin `
  --x 1.5 `
  --y -2 `
  --out .\outputs\file_move_origin_nofocus.cpp `
  --compile
```

当前支持的 action 是 `new`、`open`、`save`、`saveas`、`close`、
`open-cell`、`home-view`、`move-origin`、`clear-cell`。其中 `new`、`open`、
`saveas` 需要 `--path`。这些命令默认只生成/编译宏，不会启动或唤醒 L-Edit；
只有额外加 `--execute` 才会尝试让 L-Edit 通过 `-U` 加载宏。

## 6h. UPI layer 宏

这一层补的是图层管理和选中对象改层，适合解决 `Metal1` 不存在、需要先建层或切层
的问题：

```powershell
cli-anything-ledit --json macro-layer-action `
  --action ensure `
  --layer Mask1 `
  --out .\outputs\layer_ensure_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-layer-action `
  --action set-current `
  --layer Mask1 `
  --out .\outputs\layer_set_current_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-layer-action `
  --action change-selection-layer `
  --source-layer Mask1 `
  --target-layer Mask2 `
  --out .\outputs\layer_change_selection_nofocus.cpp `
  --compile
```

当前支持的 action 是 `ensure`、`set-current`、`delete`、`rename`、
`change-selection-layer`。`ensure` 会在 layer 不存在时创建它，然后设为当前层；
`change-selection-layer` 会在目标 layer 不存在时创建目标 layer。这些命令仍然默认只
生成/编译宏，不会启动或唤醒 L-Edit。

## 6i. UPI cell 宏

这一层补的是 cell 管理和 cell 级操作：

```powershell
cli-anything-ledit --json macro-cell-action `
  --action ensure `
  --cell TOP `
  --out .\outputs\cell_ensure_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-cell-action `
  --action copy `
  --source-cell TOP `
  --target-cell TOP_COPY `
  --out .\outputs\cell_copy_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-cell-action `
  --action flatten `
  --cell TOP `
  --out .\outputs\cell_flatten_nofocus.cpp `
  --compile
```

当前支持的 action 是 `ensure`、`open`、`copy`、`rename`、`delete`、`clear`、
`flatten`。这些命令默认只生成/编译宏，不会启动或唤醒 L-Edit。

## 6i. UPI window/view 宏

这一层补的是基础窗口和视图动作，仍然不靠键盘输入：

```powershell
cli-anything-ledit --json macro-window-action `
  --action home-visible-cell `
  --out .\outputs\window_home_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-window-action `
  --action make-first-layout-visible `
  --out .\outputs\window_layout_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-window-action `
  --action save-visible-image `
  --path .\outputs\visible_window.png `
  --out .\outputs\window_save_image_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-window-action `
  --action new-text-window `
  --text "hello from Codex" `
  --out .\outputs\window_text_nofocus.cpp `
  --compile
```

当前支持的 action 是 `home-visible-cell`、`make-first-layout-visible`、
`save-visible-image`、`new-text-window`、`load-text-window`、
`close-visible-window`。其中 `save-visible-image` 和 `load-text-window` 需要
`--path`。`close-visible-window` 会拒绝关闭最后一个窗口，避免把会话关空。

## 6j. UPI import/export 宏

这一层补的是 GDS/CIF 导入和 GDS 导出，适合把版图交换格式纳入 CLI 流程：

```powershell
cli-anything-ledit --json macro-io-action `
  --action import-gds `
  --path C:\tmp\input.gds `
  --log-path .\outputs\import_gds.log `
  --out .\outputs\io_import_gds_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-io-action `
  --action import-cif `
  --path C:\tmp\input.cif `
  --polygon-as-rect `
  --out .\outputs\io_import_cif_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-io-action `
  --action export-gds `
  --path .\outputs\export_layout.gds `
  --cell TOP `
  --out .\outputs\io_export_gds_nofocus.cpp `
  --compile
```

当前支持的 action 是 `import-gds`、`import-cif`、`export-gds`。导入支持
`--overwrite none|top|all`；GDS 导入支持 `--use-gds-datatype` /
`--ignore-gds-datatype`；GDS 导出支持 `--cell`、`--include-hierarchy` /
`--flat`、`--hidden-objects` / `--visible-only`。

## 6k. UPI grid 宏

这一层补的是制造网格、显示网格、主网格和鼠标吸附网格：

```powershell
cli-anything-ledit --json macro-grid-action `
  --action set-manufacturing-grid `
  --value 0.1 `
  --out .\outputs\grid_mfg_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-grid-action `
  --action set-display-grid `
  --value 1 `
  --out .\outputs\grid_display_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-grid-action `
  --action set-snap-grid `
  --value 1 `
  --x 0.25 `
  --y 0.5 `
  --out .\outputs\grid_snap_nofocus.cpp `
  --compile
```

当前支持的 action 是 `set-manufacturing-grid`、`set-display-grid`、
`set-snap-grid`、`set-major-grid`。数值使用当前 L-Edit 显示单位，宏内部会通过
`LFile_DispUtoIntU` 转成 L-Edit internal units。

## 6l. UPI DRC / marker 宏

这一层补的是 DRC 检查、DRC 结果和 marker 相关操作：

```powershell
cli-anything-ledit --json macro-drc-action `
  --action set-rule-set `
  --rule-set "DRC Standard Rule Set" `
  --out .\outputs\drc_rule_set_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-drc-action `
  --action set-flags `
  --flag-acute `
  --flag-all-angle `
  --flag-off-grid `
  --out .\outputs\drc_flags_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-drc-action `
  --action run `
  --x1 0 `
  --y1 0 `
  --x2 10 `
  --y2 20 `
  --out .\outputs\drc_run_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-drc-action `
  --action run-command-file `
  --path C:\tmp\rules.cal `
  --out .\outputs\drc_command_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-drc-action `
  --action status `
  --out .\outputs\drc_status_nofocus.cpp `
  --compile
```

当前支持的 action 是 `run`、`run-command-file`、`set-rule-set`、
`set-tolerance`、`set-flags`、`open-summary`、`open-statistics`、
`load-results`、`clear-markers`、`show-global-markers`、
`hide-global-markers`、`status`。DRC 区域参数是 `--x1 --y1 --x2 --y2`；
不传区域时对当前可见 cell 全部运行。
## 6m. UPI extraction / netlist 宏

这一层接的是 extraction、netlist、LVS 等相关操作：

```powershell
cli-anything-ledit --json macro-extract-action `
  --action run `
  --def-file C:\path\extract.def `
  --spice-out .\outputs\out.sp `
  --write-node-names `
  --out .\outputs\extract_run_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-extract-action `
  --action run-command-file `
  --path C:\path\lvs.cal `
  --spice-out .\outputs\out.sp `
  --out .\outputs\extract_cmd_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-extract-action `
  --action run-hiper `
  --out .\outputs\extract_hiper_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-extract-action `
  --action set-options `
  --def-file C:\path\extract.def `
  --spice-out .\outputs\out.sp `
  --write-node-names `
  --write-parasitic-cap `
  --out .\outputs\extract_opts_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-extract-action `
  --action open-summary `
  --out .\outputs\extract_summary_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-extract-action `
  --action open-statistics `
  --out .\outputs\extract_stats_nofocus.cpp `
  --compile
```

当前支持的 action 是 `run`、`run-command-file`、`run-hiper`、
`set-options`、`open-summary`、`open-statistics`。`run` 使用
`LExtract_Run` API，需要 `--def-file` 和 `--spice-out`。
`set-options` 通过 `LExtract_GetOptionsEx840` / `LExtract_SetOptionsEx840`
读取并修改当前提取选项，支持
`--write-node-names`、`--write-node-capacitance`、`--write-parasitic-cap`。

## 6n. UPI via 宏

这一层接的是过孔定义和填充操作：

```powershell
cli-anything-ledit --json macro-via-action `
  --action add `
  --lower-layer Metal1 --upper-layer Metal2 `
  --via-cell VIA1 --pitch-x 0.5 --pitch-y 0.5 `
  --out .\outputsia_add_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-via-action `
  --action count `
  --out .\outputsia_count_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-via-action `
  --action find --via-def-name VIA1 `
  --out .\outputsia_find_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-via-action `
  --action fill --via-def-name VIA1 `
  --x1 0 --y1 0 --x2 10 --y2 10 `
  --out .\outputsia_fill_nofocus.cpp `
  --compile
```

当前支持的 action 是 `add`、`delete-all`、`fill`、`find`、`find-by-layer`、`count`。

## 6o. UPI basepoint 宏

这一层接的是基准点模式和 cell 基准点坐标：

```powershell
cli-anything-ledit --json macro-basepoint-action `
  --action get-mode `
  --out .\outputsp_get_mode_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-basepoint-action `
  --action set-mode --enabled `
  --out .\outputsp_set_mode_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-basepoint-action `
  --action set --x 1.5 --y 2.5 `
  --out .\outputsp_set_nofocus.cpp `
  --compile
```

当前支持的 action 是 `get-mode`、`set-mode`、`get`、`set`。

## 6p. UPI layer-params 宏

这一层接的是图层参数（GDS number/datatype、CIF name、电容、电阻等）：

```powershell
cli-anything-ledit --json macro-layer-params-action `
  --action get --layer Metal1 `
  --out .\outputs\lp_get_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-layer-params-action `
  --action set --layer Metal1 `
  --gds-number 10 --gds-datatype 0 `
  --cap 1.5 --rho 0.05 `
  --out .\outputs\lp_set_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-layer-params-action `
  --action set-cap --layer Metal1 --cap 2.0 `
  --out .\outputs\lp_set_cap_nofocus.cpp `
  --compile

cli-anything-ledit --json macro-layer-params-action `
  --action set-rho --layer Metal1 --rho 0.1 `
  --out .\outputs\lp_set_rho_nofocus.cpp `
  --compile
```

当前支持的 action 是 `get`、`set`、`set-cap`、`set-rho`、`set-fringe-cap`。
`set` action 支持 `--gds-number`、`--gds-datatype`、`--cif-name`、`--cap`、`--rho`、
`--fringe-cap`、`--locked`/`--unlocked`、`--hidden`/`--visible`。


## 6q. UPI 执行前检查

真正加 `--execute` 之前，先跑 preflight。它只检查 L-Edit 进程、宏文件和将要执行的
命令，不会启动 L-Edit：

```powershell
cli-anything-ledit --json upi-preflight `
  --macro .\outputs\cell_ensure_nofocus.upi
```

默认策略是 clean-instance：如果已经有 `ledit64.exe` 在运行，preflight 会返回
`ready: false`，并说明 blocker。这样可以避免已有单实例 L-Edit 吞掉或拦截
`-U <macro>`。只有你明确要测试已有进程行为时，才加：

```powershell
cli-anything-ledit --json upi-preflight `
  --macro .\outputs\cell_ensure_nofocus.upi `
  --allow-existing-process
```

这只会把 blocker 降级成 warning，不会执行宏。

## 7. 排错

如果出现 `Error launching app`，并且路径包含：

```text
C:\Program Files\WindowsApps\OpenAI...type=action
```

那是 Codex/OpenAI 桌面端 action 链接的问题，不是 L-Edit，也不是 `.tco`
脚本的问题。使用本文件里的普通 PowerShell 命令即可绕开。
