import { MCP_GROUPS } from './mcp.mjs'

export function renderHeader() {
  const mcpSummary = MCP_GROUPS.map((group) => `- ${group.title}: ${group.items.map((item) => item.label).join(', ')}`)
  return [
    '╔════════════════════════════════════════════════════════════╗',
    '║                                                            ║',
    '║                ██████╗  ███████╗  ███████╗                 ║',
    '║                ██╔══██╗ ██╔════╝  ██╔════╝                 ║',
    '║                ██████╔╝ █████╗    █████╗                   ║',
    '║                ██╔══██╗ ██╔══╝    ██╔══╝                   ║',
    '║                ██║  ██║ ██║       ██║                      ║',
    '║                ╚═╝  ╚═╝ ╚═╝       ╚═╝                      ║',
    '║                                                            ║',
    '║                  RailForge Spec Workflow                   ║',
    '║                 Codex + Claude + Gemini                   ║',
    '║                                                            ║',
    '╚════════════════════════════════════════════════════════════╝',
    '',
    '? RailForge 主菜单',
    ' ────────────── Codex CLI ───────────────',
    '❯   1. 初始化 RailForge 配置  - 安装 spec 工作流',
    '    2. 更新工作流             - 更新命令与 skills',
    '    3. 配置 MCP               - 代码检索与辅助工具',
    '    4. 配置模型路由           - Hosted Codex / Claude / Gemini',
    ' ──────────────── 其他工具 ────────────────',
    '    T. 实用工具               - doctor, probes, diagnostics',
    '    C. 配置 MCP               - 单独生成 .mcp.json',
    ' ───────────────── RailForge ─────────────────',
    '    H. 帮助                   - 查看 spec 工作流入口',
    '    -. 卸载 RailForge         - 移除工作流配置',
    '    Q. 退出',
    '',
    'MCP 分组：',
    ...mcpSummary
  ].join('\n')
}

export function mainMenuChoices() {
  return [
    { name: '1. 初始化 RailForge 配置      - 安装 spec 工作流', value: 'init' },
    { name: '2. 更新工作流               - 更新命令与 skills', value: 'update' },
    { name: '3. 配置 MCP                 - 代码检索与辅助工具', value: 'config-mcp' },
    { name: '4. 配置模型路由             - Hosted Codex / Claude / Gemini', value: 'config-model' },
    { name: 'T. 实用工具                 - doctor, probes, diagnostics', value: 'tools' },
    { name: 'C. 检查宿主 CLI             - Codex / Claude / Gemini / jq', value: 'check-cli' },
    { name: 'H. 帮助                     - 查看 spec 工作流入口', value: 'help' },
    { name: '-. 卸载 RailForge           - 移除工作流配置', value: 'uninstall' },
    { name: 'Q. 退出', value: 'quit' },
  ]
}

export function mcpMenuChoices() {
  return [
    { name: '1. 代码检索 MCP           - ace-tool / ace-tool-rs / fast-context / ContextWeaver', value: 'code-retrieval' },
    { name: '2. 联网搜索 MCP           - grok-search', value: 'web-search' },
    { name: '3. 辅助工具 MCP           - Context7 / Playwright / DeepWiki / Exa', value: 'auxiliary' },
    { name: '4. 写入项目 .mcp.json      - 同步镜像配置', value: 'write-config' },
    { name: '5. 探测 MCP 配置           - probe-mcp', value: 'probe' },
    { name: 'B. 返回主菜单', value: 'back' },
  ]
}

export function modelMenuChoices() {
  return [
    { name: '1. Hosted Codex 默认主写作', value: 'hosted_codex' },
    { name: '2. Codex CLI fallback 主写作', value: 'codex_cli' },
    { name: 'B. 返回主菜单', value: 'back' },
  ]
}
