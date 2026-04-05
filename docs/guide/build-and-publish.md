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

## 三、GitHub Release 手动更新

当不需要跨平台 CI 构建、只需更新当前平台二进制时，可以直接用 `gh` CLI 上传：

### 打包并上传

```bash
# 1. 打包两个二进制
python -m PyInstaller railforge-darwin-arm64.spec --distpath dist/ --noconfirm
python -m PyInstaller railforge-codeagent-darwin-arm64.spec --distpath dist/ --noconfirm

# 2. 刷新 manifest（用 scripts/build_binaries.py 或手动）
python scripts/build_binaries.py   # 会清空 dist/ 再重建

# 3. 上传到已有 Release（--clobber 替换同名资产）
gh release upload railforge-preset \
  dist/railforge-darwin-arm64 \
  dist/railforge-codeagent-darwin-arm64 \
  dist/manifest-darwin-arm64.json \
  dist/manifest.txt \
  --clobber

# 4. 验证
gh release view railforge-preset --json assets --jq '.assets[] | "\(.name) \(.size)"'
```

### 部署到本机

```bash
cp dist/railforge-darwin-arm64 ~/.codex/bin/railforge
cp dist/railforge-codeagent-darwin-arm64 ~/.codex/bin/railforge-codeagent

# 验证
~/.codex/bin/railforge --version
~/.codex/bin/railforge --help
```

---

## 四、完整发布流程（推荐顺序）

一次完整发布包含三个目标：git 仓库、GitHub Release、npm registry。

### 步骤 1：代码提交

```bash
# 确认测试通过
python -m pytest tests/ -q

# 提交改动（只添加相关文件，不用 git add -A）
git add <相关文件>
git commit -m "fix/feat/release: 描述"
```

### 步骤 2：打包二进制

```bash
# 完整打包（推荐）
python scripts/build_binaries.py

# 或单独打包
python -m PyInstaller railforge-darwin-arm64.spec --distpath dist/ --noconfirm
python -m PyInstaller railforge-codeagent-darwin-arm64.spec --distpath dist/ --noconfirm
```

### 步骤 3：更新 GitHub Release

```bash
# 方法 A：手动上传（仅当前平台）
gh release upload railforge-preset dist/* --clobber

# 方法 B：通过 CI tag 触发（跨平台）
git tag -d railforge-preset 2>/dev/null
git push origin :refs/tags/railforge-preset 2>/dev/null
git tag railforge-preset
git push origin railforge-preset
```

### 步骤 4：部署到本机

```bash
cp dist/railforge-darwin-arm64 ~/.codex/bin/railforge
cp dist/railforge-codeagent-darwin-arm64 ~/.codex/bin/railforge-codeagent
```

### 步骤 5：发布 npm 安装器（如需）

```bash
# 递增版本号
# 编辑 installer/package.json 中的 version

# 提交版本变更
git add installer/package.json
git commit -m "release: installer 0.x.y"

# 发布（npm 启用了 2FA 会要求 OTP）
cd installer
npm publish --access public --otp=<验证码>

# 验证
npm view railforge-workflow version
```

### 步骤 6：推送到远端

```bash
git push origin <branch>
```

### 步骤 7：验证

```bash
# GitHub Release
gh release view railforge-preset

# npm
npx railforge-workflow@latest help

# 本地二进制
~/.codex/bin/railforge --version
~/.codex/bin/railforge spec-init
```

---

## 五、版本号管理

| 文件 | 字段 | 说明 |
|------|------|------|
| `railforge/__init__.py` | `__version__` | Python 核心版本 |
| `pyproject.toml` | `project.version` | 需与上面保持一致 |
| `installer/package.json` | `version` | npm 安装器版本（独立递增） |
| `installer/package.json` | `railforgeBinaryVersion` | 安装器下载的二进制版本（需与 Python 版本匹配） |

三条规则：
1. Python 核心版本变化时，`__init__.py` 和 `pyproject.toml` 必须同步
2. 安装器版本独立于 Python 版本递增
3. 安装器发布新版时，`railforgeBinaryVersion` 需指向对应的 GitHub Release 二进制版本

---

## 六、目录和文件参考

```
项目根/
  railforge/__init__.py          # __version__ = "x.y.z"
  pyproject.toml                 # project.version
  installer/package.json         # version + railforgeBinaryVersion
  scripts/build_binaries.py      # 构建脚本
  .github/workflows/build-binaries.yml  # CI 构建（tag 触发）
  railforge-darwin-arm64.spec    # macOS arm64 PyInstaller spec
  railforge-codeagent-darwin-arm64.spec
  dist/                          # 构建产出（git ignored）
  build/                         # 构建中间文件（git ignored）
  CHANGELOG.md                   # 版本更新日志
  docs/guide/release-notes.md    # 发布说明
  docs/guide/npm-publish-checklist.md  # npm 发布检查清单
```
