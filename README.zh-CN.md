> **中文** | [English](README.md)

# cli-anything-Ledit

一个 **CLI-Anything** 工具，用于从命令行自动化 [Tanner L-Edit](https://www.sw.siemens.com/ic-design/tanner-eda/) 版图操作。无需手动操作 GUI，即可生成 Tanner 命令文件（`.tco`）、编译执行 UPI 宏、通过 SendKeys 控制 L-Edit 窗口，以及验证版图几何。

> **CLI-Anything** 是一种方法论：为任何仅支持 GUI 的 EDA 工具包装可脚本化的命令行接口，使 AI Agent（Codex、Claude、GPT 等）和 CI 流水线能够确定性地驱动它。

## 亮点

- **30+ CLI 命令**，覆盖版图绘制、Cell/Layer/File 管理、DRC、寄生提取、Via 填充、Grid 设置、工艺信息查询等
- **两层自动化接口**
  - *命令窗口脚本*（`.tco`）——轻量级，无需编译器
  - *UPI C++ 宏*（`.cpp` → `.upi`）——完整访问 L-Edit 内部 API
- **JSON 回执**——每条命令都输出机器可读的 JSON 结果
- **内建验证**——方阵几何验证（box 数量、边界、首尾 box）
- **SVG 预览**——在打开 L-Edit 之前即可视觉检查
- **路径可配置**——所有 Tanner 工具链路径均可通过环境变量覆盖

## 快速开始

### 前置条件

- **Windows** 系统，已安装 Tanner L-Edit v16.3（或兼容版本）
- **Python ≥ 3.10**
- **PowerShell**（用于 SendKeys 集成，可选）
- **MinGW g++**（Tanner 自带，用于 UPI 宏编译，可选）

### 安装

**一键安装**（Windows PowerShell）：

```powershell
.\install.ps1
```

**一键安装**（Linux/macOS）：

```bash
bash install.sh
```

**pip 安装**（任意平台）：

```bash
pip install cli-anything-ledit
```

从源码安装：

```bash
git clone https://github.com/tjusaltedfish/cli-anything-Ledit.git
cd cli-anything-Ledit
pip install -e .
```

带开发工具：

```bash
pip install -e ".[dev]"
```

### 验证安装

```bash
cli-anything-ledit --json inspect
```

预期输出：

```json
{
  "ok": true,
  "ledit_exe": "C:\\Program Files\\Tanner EDA\\Tanner Tools v16.3\\ledit64.exe",
  "ledit_exe_exists": true,
  "process_count": 0
}
```

### 生成第一个方阵

```bash
cli-anything-ledit --json draw-square-array \
  --rows 4 --cols 6 --size 2 --pitch 5 \
  --layer CURRENT --out outputs/my_array.tco
```

生成三个文件：

| 文件 | 用途 |
|------|------|
| `outputs/my_array.tco` | Tanner 命令文件，粘贴到 L-Edit 执行 |
| `outputs/my_array.svg` | 版图 SVG 预览图 |
| `outputs/my_array.run.txt` | 可直接粘贴的 `run` 命令 |

在 L-Edit 命令窗口中执行：

```
run "C:/path/to/outputs/my_array.tco"
```

## 命令参考

### 版图命令

| 命令 | 说明 |
|------|------|
| `draw-square-array` | 一步完成方阵的生成、验证和预览 |
| `square-array` | 生成方阵 `.tco`（不验证） |
| `box` | 绘制单个矩形 |
| `path` | 绘制折线路径 |
| `polygon` | 绘制多边形 |
| `text` | 放置文本标注 |
| `instance` | 放置 cell 实例 |
| `array` | 创建实例阵列 |
| `layout-script` | 执行多操作 JSON 版图规范 |
| `layer-probe` | 测试当前设计是否接受某个命名 layer |

### UPI 宏命令

每个 `macro-*` 命令生成 C++ 源码。加 `--compile` 编译为 `.upi` DLL，加 `--execute` 启动 L-Edit 执行。

| 命令 | 功能域 |
|------|--------|
| `macro-square-array` | 通过 UPI 绘制方阵 |
| `macro-selection-action` | 复制、移动、分组、合并、打散、翻转、旋转 |
| `macro-object-action` | 创建圆、弧、环、扇形 |
| `macro-file-action` | 新建、打开、保存、另存、关闭、回到主视图 |
| `macro-layer-action` | 确保、切换、删除、重命名 layer |
| `macro-cell-action` | 确保、打开、复制、重命名、删除、打散 cell |
| `macro-window-action` | 主视图、保存截图、文本窗口 |
| `macro-io-action` | GDS/CIF 导入导出 |
| `macro-grid-action` | 制造网格、显示网格、对齐网格 |
| `macro-drc-action` | 运行 DRC、管理标记、加载结果 |
| `macro-extract-action` | 寄生提取、网表、LVS |
| `macro-via-action` | Via 定义、填充、查找、计数 |
| `macro-object-property-action` | GDS datatype、网名、layer 变更 |
| `macro-basepoint-action` | 基点模式和坐标 |
| `macro-layer-params-action` | GDS/CIF 参数、电容、电阻率、可见性 |
| `macro-technology-action` | 工艺名称、单位、lambda |
| `macro-cell-info-action` | 列出 cell、获取名称、获取可见性 |
| `macro-net-info-action` | 列出网络、统计网络数 |
| `macro-smoke` | 最小化 UPI 冒烟测试宏 |

### 工具命令

| 命令 | 说明 |
|------|------|
| `inspect` | 检测 L-Edit 路径、运行进程和能力 |
| `capabilities` | 列出所有自动化层及其命令 |
| `verify-script` | 验证 `.tco` 文件的命令结构 |
| `upi-preflight` | 检查 UPI 执行是否安全 |
| `launch` | 启动新的 L-Edit 实例 |
| `run-script` | 向聚焦的 L-Edit 窗口发送 `run` 命令 |

### PowerShell 辅助脚本

```powershell
# 生成、验证并预览方阵
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5

# 自动启动 L-Edit
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5 -Launch

# 向可见的 L-Edit 窗口发送 run 命令
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5 -SendRunCommand
```

## 环境变量配置

所有 Tanner 工具链路径均可通过环境变量覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LEDIT_EXE` | 自动检测 | `ledit64.exe` 路径 |
| `LEDIT_DOC` | `C:\Program Files\Tanner EDA\...\ledit.pdf` | L-Edit 文档路径 |
| `LEDIT_GCC` | `C:\Program Files\Tanner EDA\...\g++.exe` | MinGW g++ 路径 |
| `LEDIT_UPI_INCLUDE` | `C:\Program Files\Tanner EDA\...\upi\Include` | UPI 头文件目录 |
| `LEDIT_UPI_LINK_LIB` | `<UPI_INCLUDE>/libupilink-gcc4.6.3-x64.a` | UPI 链接库 |
| `LEDIT_DEFAULT_OUTPUT_DIR` | `outputs` | 默认输出目录 |

示例：

```bash
set LEDIT_EXE=D:\Tanner\v16.3\ledit64.exe
set LEDIT_GCC=D:\Tanner\v16.3\mingw64\bin\g++.exe
cli-anything-ledit --json inspect
```

## 架构

```
cli_anything/ledit/
├── __init__.py           # 包元数据
├── __main__.py           # python -m 入口
├── config.py             # 集中路径配置（环境变量 + 默认值）
├── ledit_cli.py          # Click CLI，30+ 命令和 REPL
├── core/
│   ├── macro_writer.py   # C++ UPI 宏代码生成
│   ├── script_writer.py  # .tco 命令文件生成
│   ├── session.py        # 进程内命令历史
│   └── verify.py         # 几何验证（box 数量、边界）
├── utils/
│   └── ledit_backend.py  # L-Edit 进程管理、编译、SendKeys
└── tests/
    ├── test_core.py      # 单元测试
    └── test_full_e2e.py  # 端到端 CLI 测试
```

**设计原则：**

- 每条命令返回 JSON 回执，包含 `"ok": true/false`
- 生成文件具有确定性（无时间戳、无随机数）
- 除非显式请求（`--execute`、`run-script`），否则不触碰 GUI
- 默认安全：运行前验证、执行前预检

## 组合版图脚本

对于多步骤版图，将 JSON 规范传给 `layout-script`：

```bash
cli-anything-ledit --json layout-script layout.json --out outputs/design.tco
```

`layout.json` 示例：

```json
{
  "title": "混合版图",
  "cell": "TOP",
  "operations": [
    {"op": "cell", "name": "TOP"},
    {"op": "layer", "name": "Metal1"},
    {"op": "box", "x1": 0, "y1": 0, "x2": 10, "y2": 5},
    {"op": "square-array", "rows": 3, "cols": 3, "size": 1, "pitch": 2, "x": 15, "y": 0},
    {"op": "path", "points": [[0, 8], [10, 8], [10, 12]], "width": 0.5},
    {"op": "polygon", "points": [[20, 0], [25, 0], [22.5, 4]]},
    {"op": "text", "label": "OUT", "x": 22, "y": 5},
    {"op": "save"}
  ]
}
```

## 测试

```bash
pip install -e ".[dev]"
pytest
```

测试覆盖范围：

- 方阵几何生成与验证
- 所有 UPI 宏构建器（cell、layer、file、DRC、提取、via 等）
- CLI 入口和 JSON 回执验证
- 脚本验证（命令结构、box 数量、边界）
- 进程检查和预检

## 示例

### 灰度光刻测试掩模

参见 [`examples/grayscale_test/`](examples/grayscale_test/)：使用可编程像素阵列生成灰度光刻测试掩模版图的真实用例。

### DRC + 提取工作流

```bash
# 对当前 cell 运行 DRC
cli-anything-ledit --json macro-drc-action --action run --compile --execute

# 提取网表
cli-anything-ledit --json macro-extract-action --action run \
  --def-file C:\path\extract.def --spice-out outputs\out.sp \
  --write-node-names --compile --execute
```

## 许可证

[MIT](LICENSE)

## 贡献

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/my-feature`）
3. 运行测试（`pytest`）
4. 提交 Pull Request

## 致谢

基于 [Click](https://click.palletsprojects.com/) CLI 框架构建。

