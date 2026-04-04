import { MCP_GROUPS } from './mcp.mjs'

export function renderMainMenu() {
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
