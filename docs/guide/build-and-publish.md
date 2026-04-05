# RailForge 打包和发布指南

## 概览

RailForge 有两个独立的发布产物：

| 产物 | 版本源 | 发布目标 |
|------|--------|---------|
| Python 二进制 (`railforge`, `railforge-codeagent`) | `railforge/__init__.py` | GitHub Release |
| npm 安装器 (`railforge-workflow`) | `installer/package.json` | npm registry |

---

## 一、Python 二进制打包

### 前提

```bash
pip install .[dev]  # 安装 pyinstaller 和 pytest
```

### 本地打包

```bash
# 方法 1：使用构建脚本（推荐，自动生成 manifest）
python scripts/build_binaries.py

# 方法 2：使用 PyInstaller spec 文件（仅打包单个二进制）
python -m PyInstaller railforge-darwin-arm64.spec --distpath dist/ --noconfirm
python -m PyInstaller railforge-codeagent-darwin-arm64.spec --distpath dist/ --noconfirm
```

产出文件在 `dist/` 目录：

```
dist/
  railforge-darwin-arm64          # 主二进制
  railforge-codeagent-darwin-arm64 # codeagent 二进制
  manifest-darwin-arm64.json      # 资产清单 (sha256 + size)
  manifest.txt                    # 简文本清单
```

### 部署到本机

```bash
cp dist/railforge-darwin-arm64 ~/.codex/bin/railforge
cp dist/railforge-codeagent-darwin-arm64 ~/.codex/bin/railforge-codeagent
```

### 验证

```bash
~/.codex/bin/railforge --version
~/.codex/bin/railforge --help
~/.codex/bin/railforge spec-init  # 应在 workspace 内运行
```

### CI 打包（GitHub Actions）

推送 `railforge-preset` tag 触发跨平台构建：

```bash
git tag railforge-preset
git push origin railforge-preset
```

CI 流程（`.github/workflows/build-binaries.yml`）：
1. 在 macOS / Linux / Windows 三平台并行构建
2. 上传构建产物到 GitHub Actions artifacts
3. tag 触发时自动发布到 GitHub Release（`softprops/action-gh-release`）

### PyInstaller spec 文件

| 文件 | 入口 | 产物名 |
|------|------|--------|
| `railforge-darwin-arm64.spec` | `railforge/__main__.py` | `railforge-darwin-arm64` |
| `railforge-codeagent-darwin-arm64.spec` | `railforge/codeagent/__main__.py` | `railforge-codeagent-darwin-arm64` |

spec 文件通常不需要手动修改。以下情况需要重新生成：
- 新增了 Python 外部依赖（需要加 `hiddenimports`）
- 新增了需要打包的数据文件（需要加 `datas`）
- 改变了入口文件路径

重新生成 spec：
```bash
python -m PyInstaller --onefile --name railforge-darwin-arm64 railforge/__main__.py
```

---

## 二、npm 安装器发布

### 版本管理

| 字段 | 文件 | 说明 |
|------|------|------|
| `version` | `installer/package.json` | 安装器自身版本 |
| `railforgeBinaryVersion` | `installer/package.json` | 对应的 Python 二进制版本 |

两个版本号独立递增。当 Python 二进制有新功能时，`railforgeBinaryVersion` 需要同步更新。

### 发布前检查

完整检查清单见 [docs/guide/npm-publish-checklist.md](npm-publish-checklist.md)。

快速检查：

```bash
# 1. 测试
python -m pytest tests/ -q
node installer/bin/railforge.mjs doctor
node installer/bin/railforge.mjs help

# 2. 包内容预览
cd installer && npm pack --dry-run

# 3. 确认版本号
node -e "console.log(require('./installer/package.json').version)"
```

### 发布

```bash
cd installer
npm publish --access public
```

### 发布后验证

```bash
npm view railforge-workflow version
npx railforge-workflow help
npx railforge-workflow doctor
```

---

## 三、完整发布流程（推荐顺序）

### 1. 版本号更新

```bash
# Python 版本
# 编辑 railforge/__init__.py 中的 __version__
# 编辑 pyproject.toml 中的 version

# 安装器版本（如需发布安装器）
# 编辑 installer/package.json 中的 version 和 railforgeBinaryVersion
```

### 2. 更新文档

- 更新 `CHANGELOG.md`
- 更新 `docs/guide/release-notes.md`

### 3. 测试

```bash
python -m pytest tests/ -q              # 全量测试
~/.codex/bin/railforge --version        # 验证当前二进制版本
```

### 4. 提交和打 tag

```bash
git add -A
git commit -m "release: v0.x.y"
git tag railforge-preset                # 触发 CI 构建
git push origin main --tags
```

### 5. 等待 CI 完成

- 检查 GitHub Actions 构建状态
- 确认 GitHub Release 资产已上传

### 6. 发布安装器（如需）

```bash
cd installer
npm publish --access public
```

### 7. 本地验证

```bash
npx railforge-workflow                  # 安装/更新
~/.codex/bin/railforge spec-init        # 验证功能
```

---

## 四、目录和文件参考

```
项目根/
  railforge/__init__.py          # __version__ = "x.y.z"
  pyproject.toml                 # project.version
  installer/package.json         # version + railforgeBinaryVersion
  scripts/build_binaries.py      # 构建脚本
  .github/workflows/build-binaries.yml  # CI 构建
  railforge-darwin-arm64.spec    # macOS arm64 PyInstaller spec
  railforge-codeagent-darwin-arm64.spec
  dist/                          # 构建产出（git ignored）
  build/                         # 构建中间文件（git ignored）
```
