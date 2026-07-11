// place to ~/.config/mimocode/hooks/

import { execSync } from "child_process"
import { homedir } from "os"
import { join } from "path"
import { mkdirSync } from "fs"

// --- Logging ---

const LOG_FILE = join(homedir(), ".local/share/mimocode/notify-hook.log")
mkdirSync(join(homedir(), ".local/share/mimocode"), { recursive: true })
const logFd = (() => { try { return require("fs").openSync(LOG_FILE, "a") } catch { return -1 } })()

function log(event: string, data: Record<string, any>) {
  return
  if (logFd < 0) return
  try {
    const ts = new Date().toISOString().slice(11, 23) // HH:MM:SS.mmm
    const line = JSON.stringify({ ts, event, ...data }) + "\n"
    require("fs").writeSync(logFd, line)
  } catch {}
}

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
  const focused = shouldNotify()
  log("notify", { title, message, focused })
  if (!focused) return
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

// --- Permission detection via timeout ---

const pendingTools = new Map<string, NodeJS.Timeout>()
const PERMISSION_TIMEOUT_MS = 10000

export default {
  "tool.execute.before": async (input: any, output: any) => {
    log("tool.execute.before", { input, output: { args: output?.args } })

    // Start timer for ALL tools (including subagents — they may need permission too)
    const callID = input.callID
    const timer = setTimeout(() => {
      pendingTools.delete(callID)
      waitingForPermission = true
      log("permission_timeout", { input, output })
      notify("MiMoCode", `Permission needed: ${input.tool}`)
    }, PERMISSION_TIMEOUT_MS)
    pendingTools.set(callID, timer)
  },

  "tool.execute.after": async (input: any, output: any) => {
    // log("tool.execute.after", { input, output })
    // Tool completed — cancel the timer
    const timer = pendingTools.get(input.callID)
    if (timer) {
      clearTimeout(timer)
      pendingTools.delete(input.callID)
    }
    waitingForPermission = false
  },

  "permission.ask": async (input: any) => {
    log("permission.ask", { input: JSON.stringify(input).slice(0, 500) })
    waitingForPermission = true
    const perm = input?.permission ?? input?.name ?? "unknown"
    notify("MiMoCode", `Permission needed: ${perm}`)
  },

  "actor.preStop": {
    run: async (input: any) => {
      log("actor.preStop", {
        actorID: input.actorID,
        agentType: input.agentType,
        mode: input.mode,
        task: (input.task ?? "").slice(0, 100),
      })
      if (input.mode === "subagent") activeSubagents.add(input.actorID)
    },
  },
  "actor.postStop": {
    run: async (input: any) => {
      log("actor.postStop", {
        actorID: input.actorID,
        agentType: input.agentType,
        mode: input.mode,
        outcome: input.outcome,
      })
      activeSubagents.delete(input.actorID)
    },
  },

  "session.pre": async (input: any) => {
    currentSessionID = input.sessionID ?? ""
    currentAgentID = input.agentID ?? ""
    log("session.pre", {
      sessionID: currentSessionID,
      agentID: currentAgentID,
      task_id: input.task_id,
    })
  },

  "session.post": async (input: any) => {
    const skipReason = hasActiveSubagents() ? "active_subagents"
      : waitingForPermission ? "waiting_permission"
        : (currentAgentID && !new Set(["build", "plan", "compose", "max"]).has(currentAgentID)) ? `background_agent:${currentAgentID}`
          : null

    log("session.post", {
      outcome: input.outcome,
      error: input.error?.slice(0, 200),
      currentSessionID,
      currentAgentID,
      activeSubagents: [...activeSubagents],
      waitingForPermission,
      skipReason,
    })

    if (skipReason) return
    const topic = currentSessionID ? getSessionTitle(currentSessionID) : ""
    const suffix = topic ? ` — ${topic}` : ""
    if (input.outcome === "completed") {
      notify("MiMoCode", `活儿干完了${suffix}`)
    } else if (input.outcome === "error") {
      notify("MiMoCode", `出错了${suffix}: ${input.error ?? "未知错误"}`)
    }
  },
}
