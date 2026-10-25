<div align="center">

<img src="logo.png" width="96" alt="EraPuller Logo" />

# 跨时代的拉取器 · EraPuller

**把 GitHub 上的好项目，一键拉回你的电脑 —— 不懂 Git 也能用**

简体中文 · English · 日本語 ｜ 轻量 · 免费 · 开源

</div>

---

## ✨ 为什么是"跨时代"

GitHub 上拉取软件通常要在黑色终端里敲 `git clone`，普通人很难驾驭。
**EraPuller（跨时代的拉取器）** 用漂亮的图形界面把它变成"粘贴地址 → 点一下 → 完成"。

- 🖥️ **全中文界面**（可一键切换 English / 日本語）
- 🚀 **两种拉取模式**
  - **快速下载 (ZIP)**：无需安装 Git，直接下载代码压缩包，普通用户首选
  - **完整克隆 (Git)**：完整克隆全部历史记录，开发者专用
- 🔍 **粘贴即解析**：自动获取仓库名称、描述、Star、Fork、语言、许可证、默认分支
- 📂 **自由选择保存位置**，完成后一键打开文件夹 / 复制路径
- 🎨 **现代深色 UI**：渐变光效、玻璃拟态卡片、动态进度条、实时日志
- 💡 **无网络信息也能拉**：即使仓库信息获取失败，仍可基于地址直接拉取

## 📸 界面预览

![EraPuller 界面预览](docs/screenshot.png)

## 🚀 快速开始

### 直接运行（推荐普通用户）
1. 安装 [Python 3.10+](https://www.python.org/downloads/)（勾选 *Add to PATH*）
2. 安装 Git（可选，仅"完整克隆"模式需要）：[git-scm.com](https://git-scm.com/)
3. 安装依赖并启动：

```bash
pip install -r requirements.txt
python main.py
```

### 打包成独立 EXE
双击运行 `build.bat`，或手动执行：

```bash
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "EraPuller" --icon "icon.ico" main.py
```

生成的可执行文件位于 `dist/EraPuller.exe`，双击即用，无需安装任何环境。

## 🧰 支持输入的地址格式

```
https://github.com/owner/repo
https://github.com/owner/repo.git
https://github.com/owner/repo/tree/feature/branch   （指定分支）
git@github.com:owner/repo.git
owner/repo
```

## 📁 项目结构

```
EraPuller/
├── main.py               # 程序入口
├── app/
│   ├── main_window.py    # 主窗口（无边框 + 玻璃卡片 + 状态机）
│   ├── widgets.py        # 自定义控件（渐变按钮 / 分段切换 / 进度条 / Toast）
│   ├── workers.py        # 后台线程（仓库信息 / ZIP 下载 / Git 克隆）
│   ├── github.py         # GitHub 地址解析与 API
│   ├── i18n.py           # 中 / 英 / 日 文案
│   ├── icons.py          # 程序化图标绘制（零图片资源）
│   └── theme.py          # 配色与全局样式
├── scripts/
│   ├── make_icon.py      # 重新生成品牌图标
│   └── e2e_test.py       # 端到端功能验证
└── build.bat             # 一键打包脚本
```

## 🛠️ 技术栈

- **Python 3.10+** + **PySide6 (Qt 6)** — 原生性能，无浏览器内核负担
- 标准库 `urllib` / `subprocess` — 零多余依赖
- **PyInstaller** 打包为单文件 EXE

## 📜 许可证

[MIT License](LICENSE)

---

<div align="center">Made with ❤️ for people who just want the code.</div>
