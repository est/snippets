// place to ~/.config/mimocode/hooks/

import { execSync } from "child_process"
import { homedir } from "os"
import { join } from "path"

function run(cmd: string): string {
  try {
    return execSync(cmd, { timeout: 3000, encoding: "utf-8" }).trim()
  } catch {
    return ""
  }
}

function getSessionTitle(sessionID: string): string {
  try {
    const db = join(homedir(), ".local/share/mimocode/mimocode.db")
    return run(`sqlite3 "${db}" "SELECT title FROM session WHERE id = '${sessionID}'"`)
  } catch {
    return ""
  }
}

// --- Focus detection ---

function isTmuxPaneActive(): boolean {
  if (!process.env.TMUX_PANE) return false
  const active = run("tmux list-panes -F '#{pane_id} #{pane_active}' | awk '$2==1 {print $1}'")
  return !!active && process.env.TMUX_PANE === active
}

function isNonTmuxTerminalFocused(): boolean {
  const ancestors = new Set<number>()
  let cur = process.pid
  for (let i = 0; i < 20; i++) {
    ancestors.add(cur)
    const ppid = run(`ps -o ppid= -p ${cur}`)
    if (!ppid) break
    cur = parseInt(ppid, 10)
    if (isNaN(cur)) break
  }
  const frontPid = run(`lsappinfo info -only pid $(lsappinfo front) 2>/dev/null | grep -o '[0-9]*'`)
  if (!frontPid) return false
  return ancestors.has(parseInt(frontPid, 10))
}

function shouldNotify(): boolean {
  if (process.env.TMUX) return !isTmuxPaneActive()
  return !isNonTmuxTerminalFocused()
}

function esc(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')
}

function notify(title: string, message: string) {
  if (!shouldNotify()) return
  try {
    execSync(
      `osascript -e 'display notification "${esc(message)}" with title "${esc(title)}" sound name "Glass"'`,
      { timeout: 3000 }
    )
  } catch {}
}

// --- Subagent tracking ---

const activeSubagents = new Set<string>()
let waitingForPermission = false
let currentSessionID = ""
let currentAgentID = ""

function hasActiveSubagents(): boolean {
  return activeSubagents.size > 0
}

export default {
  "tool.execute.before": async (input, output) => {
    if (hasActiveSubagents()) return
    const tool = input.tool
    const args = output?.args ?? {}

    // Only predict for file-modifying tools — bash can't be reliably predicted
    let needsPermission = false
    let perm = ""
    if (tool === "edit" || tool === "write" || tool === "multiedit" || tool === "notebook-edit") {
      const p = args.file_path ?? args.path ?? ""
      if (p && !p.startsWith(process.cwd())) { needsPermission = true; perm = "external directory" }
    }
    if (needsPermission) {
      waitingForPermission = true
      notify("MiMoCode", `Permission needed: ${perm}`)
    }
  },

  "permission.ask": async (input: any) => {
    waitingForPermission = true
    const perm = input?.permission ?? input?.name ?? "unknown"
    notify("MiMoCode", `Permission needed: ${perm}`)
  },

  "tool.execute.after": async () => {
    waitingForPermission = false
  },

  "actor.preStop": {
    run: async (input) => {
      if (input.mode === "subagent") activeSubagents.add(input.actorID)
    },
  },
  "actor.postStop": {
    run: async (input) => {
      activeSubagents.delete(input.actorID)
    },
  },

  "session.pre": async (input: any) => {
    currentSessionID = input.sessionID ?? ""
    currentAgentID = input.agentID ?? ""
  },

  "session.post": async (input) => {
    if (hasActiveSubagents()) return
    if (waitingForPermission) return
    // Only notify for main agents, skip background tasks (checkpoint-writer, dream, distill, etc.)
    const MAIN_AGENTS = new Set(["build", "plan", "compose", "max"])
    if (currentAgentID && !MAIN_AGENTS.has(currentAgentID)) return
    const topic = currentSessionID ? getSessionTitle(currentSessionID) : ""
    const suffix = topic ? ` — ${topic}` : ""
    if (input.outcome === "completed") {
      notify("MiMoCode", `活儿干完了${suffix}`)
    } else if (input.outcome === "error") {
      notify("MiMoCode", `出错了${suffix}: ${input.error ?? "未知错误"}`)
    }
  },
}
