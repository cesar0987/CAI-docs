/**
 * cai-log — atribución y bloqueo de comandos destructivos (proyecto CAI)
 * ---------------------------------------------------------------------------
 * Plugin de OpenCode (V2). Se carga automáticamente desde
 * `.opencode/plugins/cai-log.ts`.
 *
 * Qué hace:
 *   1. Recuerda al agente, una vez por sesión, el orden de lectura obligatorio
 *      y las prohibiciones del proyecto (AGENTS.md + 12.01).
 *   2. Registra el modelo, el agente y los archivos tocados de la sesión en
 *      `.cai/sessions/` (fuera del control de versiones).
 *   3. Bloquea comandos destructivos: borrado, `push` a `main`, reescritura de
 *      historia y limpieza forzada.
 *
 * Qué NO hace (ADR-0018):
 *   - No interpreta comandos de commit ni adivina mensajes.
 *   - No verifica la trazabilidad: eso lo hace `bin/cai-log.py verificar`,
 *     invocado por el hook `commit-msg` con el mensaje real.
 *   - No escribe en la bóveda: el histórico solo lo modifica `bin/cai-log.py`,
 *     que agrega entradas sin tocar las anteriores.
 *
 * Referencia: sistema cai/12 - Registro de Cambios/12.01 Política de Cambios
 * y Trazabilidad.md · ADR-0017 · ADR-0018
 */

import { mkdirSync, writeFileSync } from "node:fs"
import { join, relative, resolve } from "node:path"

const BOOTSTRAP = [
  "PROYECTO CAI — antes de actuar, lee en este orden:",
  "1) AGENTS.md (raíz del repositorio)",
  "2) sistema cai/12 - Registro de Cambios/12.01 Política de Cambios y Trazabilidad.md",
  "3) sistema cai/12 - Registro de Cambios/12.03 Bitácora de Sesiones con IA.md (sesiones en curso)",
  "4) el documento objetivo y sus documentos 'related'",
  "5) sistema cai/11 - Decisiones ADR/Índice de ADRs.md y los ADR que apliquen",
  "",
  "Prohibido: borrar archivos o entradas de registro; editar un ADR aceptado sin",
  "escribir uno nuevo que lo sustituya; cerrar un cambio sin entrada REG en 12.02;",
  "tocar datos reales de personas; escribir credenciales; hacer push a main;",
  "reescribir historia publicada; tocar lo que no se pidió.",
  "",
  "Obligatorio: declarar el alcance; clasificar la severidad (N1-N4); citar el ID de",
  "origen; verificar con un comando; registrar en 12.02 y en 12.03 con el modelo exacto",
  "(proveedor/modelo#variante); actualizar los índices; anotar lo pendiente.",
  "",
  "El commit exige un REG-AAAA-NNN en el mensaje: lo verifica el hook commit-msg.",
].join("\n")

type SessionState = {
  sessionID: string
  providerID: string
  modelID: string
  variant?: string
  agent: string
  operator: string
  startedAt: string
  touched: Set<string>
  reminded: boolean
}

const sessions = new Map<string, SessionState>()

function state(sessionID: string): SessionState {
  let s = sessions.get(sessionID)
  if (!s) {
    s = {
      sessionID,
      providerID: "desconocido",
      modelID: "desconocido",
      agent: "desconocido",
      operator: process.env.CAI_OPERADOR || "no declarado",
      startedAt: new Date().toISOString(),
      touched: new Set<string>(),
      reminded: false,
    }
    sessions.set(sessionID, s)
  }
  return s
}

/** Comandos que el proyecto prohíbe ejecutar, sin importar el contexto. */
const DESTRUCTIVOS: RegExp[] = [
  /(^|[;&|]\s*)rm\s+(-[a-zA-Z]*\s+)*[^\s&|;]+/,
  /(^|[;&|]\s*)git\s+clean\b/,
  /(^|[;&|]\s*)git\s+reset\s+--hard\b/,
  /(^|[;&|]\s*)git\s+push\b[^;&|]*(--force|-f\b)/,
  /(^|[;&|]\s*)git\s+push\b[^;&|]*\bmain\b/,
  /(^|[;&|]\s*)unlink\s+/,
  /(^|[;&|]\s*)shred\s+/,
  /(^|[;&|]\s*)find\b[^;&|]*-delete\b/,
]

export default {
  id: "cai.log",
  async setup(ctx: any) {
    const worktree: string =
      ctx?.location?.project?.canonical || ctx?.location?.directory || process.cwd()

    // ----------------------------------------------------------------
    // 1. Recordatorio de entrada (una vez por sesión)
    // ----------------------------------------------------------------
    await ctx.session.hook("context", (event: any) => {
      const s = state(event.sessionID)
      if (event.model) {
        s.providerID = event.model.providerID ?? s.providerID
        s.modelID = event.model.id ?? s.modelID
        s.variant = event.model.variant ?? s.variant
      }
      if (event.agent) s.agent = event.agent
      if (!s.reminded) {
        s.reminded = true
        event.system.push({ type: "text", text: BOOTSTRAP })
      }
    })

    // ----------------------------------------------------------------
    // 2. Archivos tocados y comandos destructivos
    // ----------------------------------------------------------------
    await ctx.tool.hook("execute.before", (event: any) => {
      const s = state(event.sessionID)
      const tool = String(event.tool || "")
      const input = event.input || {}

      if (["write", "edit", "patch", "multi_edit"].includes(tool)) {
        const p = input.path || input.filePath || input.file
        if (typeof p === "string" && p.length > 0) {
          s.touched.add(relative(worktree, resolve(worktree, p)))
        }
        return
      }

      if (tool === "bash" || tool === "shell" || tool === "execute") {
        const cmd = typeof input.command === "string" ? input.command : ""
        if (!cmd) return

        for (const re of DESTRUCTIVOS) {
          if (re.test(cmd)) {
            throw new Error(
              "[cai-log] Comando bloqueado por la política del proyecto CAI: " +
                "nada se borra y la historia publicada no se reescribe.\n" +
                "Para retirar un documento, márcalo como 'deprecated' o 'superseded' y " +
                "redirige los enlaces. Ver: sistema cai/12 - Registro de Cambios/" +
                "12.01 Política de Cambios y Trazabilidad.md §3 y §9.\n" +
                "Comando rechazado: " +
                cmd,
            )
          }
        }
      }
    })

    // ----------------------------------------------------------------
    // 3. Persistencia del estado de sesión (fuera del control de versiones)
    // ----------------------------------------------------------------
    await ctx.tool.hook("execute.after", (event: any) => {
      const s = sessions.get(event.sessionID)
      if (!s) return
      try {
        const dir = join(worktree, ".cai", "sessions")
        mkdirSync(dir, { recursive: true })
        writeFileSync(
          join(dir, `${s.sessionID}.json`),
          JSON.stringify(
            {
              sessionID: s.sessionID,
              providerID: s.providerID,
              modelID: s.modelID,
              variant: s.variant,
              agent: s.agent,
              operator: s.operator,
              startedAt: s.startedAt,
              touched: [...s.touched],
            },
            null,
            2,
          ),
          "utf8",
        )
      } catch {
        /* el estado es una ayuda, nunca un bloqueo */
      }
    })
  },
}
