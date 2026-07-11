// place to ~/.config/mimocode/hooks/

import { execSync } from "child_process"
import { readFileSync } from "fs"
import { homedir } from "os"
import { join } from "path"

function run(cmd: string): string {
  try {
    return execSync(cmd, { timeout: 3000, encoding: "utf-8" }).trim()
  } catch {
    return ""
  }
}

function getSessionTopic(sessionID: string): string {
  try {
    const file = join(homedir(), ".local/share/mimocode/memory/sessions", sessionID, "checkpoint.md")
    const first = readFileSync(file, "utf-8").split("\n")[0] ?? ""
    const m = first.match(/^Topic:\s*(.+)/)
    return m?.[1]?.trim() ?? ""
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

function hasActiveSubagents(): boolean {
  return activeSubagents.size > 0
}

export default {
  "permission.ask": async (input: any) => {
    // if (hasActiveSubagents()) return
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
  },

  "session.post": async (input) => {
    if (hasActiveSubagents()) return
    if (waitingForPermission) return
    const topic = currentSessionID ? getSessionTopic(currentSessionID) : ""
    const suffix = topic ? ` — ${topic}` : ""
    if (input.outcome === "completed") {
      notify("MiMoCode", `活儿干完了${suffix}`)
    } else if (input.outcome === "error") {
      notify("MiMoCode", `出错了${suffix}: ${input.error ?? "未知错误"}`)
    }
  },
}
