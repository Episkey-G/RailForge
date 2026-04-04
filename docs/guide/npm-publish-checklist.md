# npm 发布前检查清单

## 1. 仓库状态

- [ ] `git status --short` 为空
- [ ] 所有改动已提交
- [ ] 已推送到远端主分支

## 2. 测试

- [ ] `../.venv/bin/python -m pytest -q`
- [ ] `node installer/bin/railforge.mjs doctor`
- [ ] `node installer/bin/railforge.mjs update --target /tmp/rf-product-demo`
- [ ] `node installer/bin/railforge.mjs config-model --target /tmp/rf-product-demo --lead-writer codex_cli`
- [ ] `node installer/bin/railforge.mjs probe-mcp --target /tmp/rf-product-demo`
- [ ] `node installer/bin/railforge.mjs help`
- [ ] `node installer/bin/railforge.mjs uninstall --target /tmp/rf-product-demo`

## 3. 包元数据

- [ ] `installer/package.json` 中的 `name`、`version`、`license`、`repository`、`homepage`、`bugs` 正确
- [ ] `bin` 入口正确指向 `bin/railforge.mjs`
- [ ] `files` 字段只包含发布需要的内容

## 4. 文档

- [ ] `README.md` 已包含安装说明
- [ ] `docs/guide/commands.md` 已包含主工作流命令说明
- [ ] `docs/guide/faq.md` 已覆盖常见问题
- [ ] `docs/guide/release-notes.md` 已更新

## 5. npm 账号

- [ ] `npm whoami` 成功
- [ ] npm 账号有对应包名的发布权限
- [ ] 若首次发布公开包，已确认包名可用

## 6. 发布命令

建议顺序：

```bash
cd installer
npm pack --dry-run
npm publish --access public
```

## 7. 发布后验证

- [ ] `npm view railforge-workflow version`
- [ ] 新终端中运行 `npx railforge-workflow help`
- [ ] 新目录中运行 `npx railforge-workflow doctor`
