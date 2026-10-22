/**
 * cai-log — atribución y control de cambios del proyecto CAI
 * ---------------------------------------------------------------------------
 * Plugin de OpenCode (V2). Se carga automáticamente desde
 * `.opencode/plugins/cai-log.ts`.
 *
 * Qué hace:
 *   1. Recuerda al agente, una vez por sesión, el orden de lectura obligatorio
 *      y las prohibiciones del proyecto (AGENTS.md + 12.01).
 *   2. Registra qué archivos toca la sesión y con qué modelo de IA trabaja.
 *   3. Antes de cada `git commit`:
 *        - exige que el mensaje cite un REG-AAAA-NNN que exista en el registro;
 *        - exige justificación cuando el commit elimina archivos;
 *        - cierra la sesión en la bitácora (12.03) si no está cerrada.
 *
 * Qué NO hace:
 *   - No decide nada. Solo registra y bloquea lo que la política prohíbe.
 *   - No borra, no mueve y no reescribe entradas existentes.
 *
 * Referencia: sistema cai/12 - Registro de Cambios/12.01 Política de Cambios
 * y Trazabilidad.md · ADR-0017
 */

import { execFileSync } from "node:child_process"
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { dirname, join, relative, resolve } from "node:path"

const VAULT = "sistema cai"
const REGISTRO = `${VAULT}/12 - Registro de Cambios/12.02 Registro de Cambios.md`
const BITACORA = `${VAULT}/12 - Registro de Cambios/12.03 Bitácora de Sesiones con IA.md`

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
  commands: string[]
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
      commands: [],
      reminded: false,
    }
    sessions.set(sessionID, s)
  }
  return s
}

/** Ejecuta git en el worktree y devuelve la salida (o "" si falla). */
function git(worktree: string, args: string[]): string {
  try {
    return execFileSync("git", args, {
      cwd: worktree,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    })
  } catch {
    return ""
  }
}

/** Rutas tocadas que Git ve como eliminadas. */
function deletedFiles(worktree: string): string[] {
  const out = git(worktree, ["status", "--porcelain"])
  const deleted: string[] = []
  for (const line of out.split("\n")) {
    if (!line) continue
    const code = line.slice(0, 2)
    // " D" = borrado en el árbol de trabajo, "D " = borrado en el índice
    if (code.includes("D")) deleted.push(line.slice(3).trim())
  }
  return deleted
}

/** Archivos con cambios pendientes (modificados, nuevos o eliminados). */
function changedFiles(worktree: string): string[] {
  const out = git(worktree, ["status", "--porcelain"])
  const files: string[] = []
  for (const line of out.split("\n")) {
    if (!line) continue
    files.push(line.slice(3).trim())
  }
  return files
}

/** Lee un archivo del worktree; devuelve "" si no existe. */
function readIn(worktree: string, rel: string): string {
  const p = join(worktree, rel)
  try {
    return existsSync(p) ? readFileSync(p, "utf8") : ""
  } catch {
    return ""
  }
}

/** Escribe un archivo del worktree creando los directorios necesarios. */
function writeIn(worktree: string, rel: string, content: string) {
  const p = join(worktree, rel)
  mkdirSync(dirname(p), { recursive: true })
  writeFileSync(p, content, "utf8")
}

/** Inserta texto entre los marcadores de ancla de un documento. */
function insertBetween(content: string, start: string, end: string, block: string): string {
  const i = content.indexOf(start)
  const j = content.indexOf(end)
  if (i === -1 || j === -1 || j < i) return content
  const head = content.slice(0, i + start.length)
  const tail = content.slice(j)
  return `${head}\n${block}\n${tail}`
}

function nowParaguay(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  // Paraguay es UTC-3 todo el año
  const utc = new Date(d.getTime() + 3 * 60 * 60 * 1000)
  return `${utc.getFullYear()}-${pad(utc.getMonth() + 1)}-${pad(utc.getDate())} ${pad(
    utc.getHours(),
  )}:${pad(utc.getMinutes())} (−03)`
}

/** Siguiente correlativo SES-AAAA-NNN a partir del contenido de la bitácora. */
function nextSesId(bitacora: string): string {
  const ids = [...bitacora.matchAll(/SES-(\d{4})-(\d{3})/g)].map((m) => m[2])
  const max = ids.reduce((acc, id) => Math.max(acc, parseInt(id, 10)), 0)
  return `SES-${new Date().getFullYear()}-${String(max + 1).padStart(3, "0")}`
}

export default {
  id: "cai.log",
  async setup(ctx: any) {
    const worktree: string = ctx?.location?.project?.canonical || ctx?.location?.directory || process.cwd()

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
    // 2. Seguimiento de archivos tocados
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
        s.commands.push(cmd)

        // ---- 2.a. Comandos destructivos: se niegan en el acto ----
        const destructivos: RegExp[] = [
          /(^|[;&|]\s*)rm\s+(-[a-zA-Z]*\s+)*[^\s&|;]+/,
          /(^|[;&|]\s*)git\s+clean\b/,
          /(^|[;&|]\s*)git\s+reset\s+--hard\b/,
          /(^|[;&|]\s*)git\s+push\b[^;&|]*(--force|-f\b)/,
          /(^|[;&|]\s*)git\s+push\b[^;&|]*\bmain\b/,
          /(^|[;&|]\s*)unlink\s+/,
          /(^|[;&|]\s*)shred\s+/,
          /(^|[;&|]\s*)find\b[^;&|]*-delete\b/,
        ]
        for (const re of destructivos) {
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

        // ---- 2.b. Antes de commitear: control del registro ----
        if (/(^|[;&|]\s*)git\s+commit\b/.test(cmd) && !/--no-verify/.test(cmd)) {
          const problemas: string[] = []

          const registro = readIn(worktree, REGISTRO)
          const bitacora = readIn(worktree, BITACORA)
          const pendientes = changedFiles(worktree)
          const borrados = deletedFiles(worktree)

          // 2.b.1 El mensaje debe citar un REG que exista en el registro
          const mensaje = (cmd.match(/-m\s+"([^"]*)"/) || cmd.match(/-m\s+'([^']*)'/) || [])[1] || ""
          const citados = [...mensaje.matchAll(/REG-\d{4}-\d{3}/g)].map((m) => m[0])
          if (citados.length === 0) {
            problemas.push(
              "El mensaje del commit no cita ningún identificador REG-AAAA-NNN.\n" +
                "    Cada commit debe apuntar a su entrada del registro. Ejemplo:\n" +
                "      git commit -m 'fix(billing): corregir imputacion parcial (REG-2026-005)'",
            )
          } else {
            const inexistentes = citados.filter((id) => !registro.includes(id))
            if (inexistentes.length > 0) {
              problemas.push(
                `El mensaje cita ${inexistentes.join(", ")} pero esa entrada no existe en ` +
                  `${REGISTRO}.\n    Escribí la entrada primero (bin/cai-log cambio ...) y después commiteá.`,
              )
            }
          }

          // 2.b.2 Eliminaciones: requieren justificación explícita
          if (borrados.length > 0) {
            const entrada = citados.length > 0 ? (registro.split(citados[0])[1] ?? "") : ""
            const justifica = /depre|retir|elimin|sustituid|reemplaz/i.test(entrada)
            if (!justifica) {
              problemas.push(
                `El commit elimina ${borrados.length} archivo(s) y la entrada del registro no ` +
                  `justifica el retiro:\n` +
                  borrados.map((f) => `      - ${f}`).join("\n") +
                  "\n    En este proyecto NADA SE BORRA: se marca 'deprecated'/'superseded' y se " +
                  "redirigen los enlaces. Registrá el cambio con --tipo deprecación y explicá el motivo.",
              )
            }
          }

          // 2.b.3 La bitácora debe tener la sesión registrada
          const sesionMarcada = bitacora.includes(`<!-- SES-${s.sessionID} -->`)

          if (!sesionMarcada) {
            // Se cierra la sesión automáticamente con la información técnica disponible.
            const id = nextSesId(bitacora)
            const tocados = [...s.touched].filter((f) => pendientes.includes(f))
            const lista = tocados.length > 0 ? tocados : pendientes
            const bloque = [
              `---`,
              ``,
              `## ${id} · Sesión cerrada automáticamente por el plugin \`cai-log\``,
              ``,
              `| Campo | Valor |`,
              `|---|---|`,
              `| **Inicio** | ${s.startedAt} |`,
              `| **Fin** | ${nowParaguay()} |`,
              `| **Operador** | ${s.operator} |`,
              `| **Herramienta** | OpenCode · agente \`${s.agent}\` |`,
              `| **Proveedor** | \`${s.providerID}\` |`,
              `| **Modelo** | \`${s.modelID}\` |`,
              `| **Variante** | \`${s.variant ?? "default"}\` |`,
              `| **Objetivo** | *(completar)* |`,
              `| **Área** | ${areaDe(lista)} |`,
              `| **Archivos tocados** | ${lista.length > 0 ? lista.map((f) => `\`${f}\``).join(", ") : "—"} |`,
              `| **Verificación** | *(completar)* |`,
              `| **Resultado** | pendiente de revisión |`,
              `| **Entradas de registro** | ${citados.join(", ") || "—"} |`,
              `| **Pendiente** | Completar objetivo, verificación y resultado |`,
              ``,
              `<!-- SES-${s.sessionID} -->`,
              ``,
            ].join("\n")
            writeIn(worktree, BITACORA, insertBetween(bitacora, "<!-- SES-ENTRIES:START -->", "<!-- SES-ENTRIES:END -->", bloque))
            console.log(`[cai-log] Sesión ${id} registrada automáticamente en ${BITACORA}.`)
          }

          // 2.b.4 Debe haber cambios que registrar
          if (pendientes.length === 0 && s.touched.size === 0) {
            problemas.push("No hay cambios para commitear.")
          }

          if (problemas.length > 0) {
            throw new Error(
              "[cai-log] Commit bloqueado por la política de trazabilidad del proyecto CAI:\n" +
                problemas.map((p) => "  • " + p).join("\n") +
                "\n\n  Referencia: sistema cai/12 - Registro de Cambios/12.01 Política de Cambios y Trazabilidad.md" +
                "\n  Para commitear de todos modos: git commit --no-verify (deja rastro de la decisión)",
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
              commands: s.commands.slice(-50),
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

/** Deduce la carpeta de la bóveda a la que pertenecen los archivos tocados. */
function areaDe(archivos: string[]): string {
  const areas = new Set<string>()
  for (const f of archivos) {
    const m = f.match(/^(sistema cai\/[^/]+)\//)
    if (m) areas.add(m[1])
    else areas.add("raíz del repositorio")
  }
  if (areas.size === 0) return "—"
  return [...areas].join(", ")
}
