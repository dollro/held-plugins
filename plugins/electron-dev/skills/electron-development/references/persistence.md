# Persistence

Where user data lives, which storage to pick, and how to keep it intact across upgrades, crashes and corrupted disks. Main (or a utility process) owns every file; renderers read and write through the IPC contract.

## Where Data Lives

| `app.getPath(...)` | Holds | Notes |
|-|-|-|
| `userData` | settings, databases, secrets ciphertext | Per user, survives updates. Derived from the app name: set `productName`/`name` before first release and never rename |
| `sessionData` | Chromium data: cookies, cache, IndexedDB, localStorage | Defaults to `userData`; move it to keep Chromium files apart |
| `logs` | log files | Set with `app.setAppLogsPath()` (debugging.md) |
| `temp` | scratch files | Can be cleaned by the OS at any time |
| `crashDumps` | crashReporter minidumps | |

- **Never write into the app bundle or `app.asar`.** It is read-only in signed installs, replaced on every update, and writing to it breaks code signatures and ASAR integrity.
- Resolve paths after `ready` (or at least after any `setPath` call); never cache them at module load before `setPath` runs.
- **`app.setPath('userData', dir)` must run before `ready`.** Uses: a portable build that keeps data next to the executable, and tests that need a fresh profile per run:

```typescript
// src/main/main.ts, before app.whenReady()
import { app } from 'electron';
import path from 'node:path';

const testProfile = process.env.ATLAS_TEST_USER_DATA; // set by the Playwright launcher only
if (testProfile && path.isAbsolute(testProfile)) app.setPath('userData', testProfile);
```

## Choosing Storage

| Need | Choose | Trade-offs |
|-|-|-|
| A few dozen settings, window state | JSON file in main, atomic writes | Simple, human-readable; whole file rewritten on save; no queries |
| Documents, lists, search, history, anything that grows | SQLite in main or a utilityProcess | Transactions, indexes, migrations; native module to build and sign |
| Renderer-only cache (offline UI data, drafts of a view) | IndexedDB in the renderer | No native code; lives in `sessionData` per partition; main cannot query it; cleared by `clearStorageData` |
| Secrets (tokens, API keys) | `safeStorage` ciphertext in `userData` | See security.md "Secrets with safeStorage" |

- `localStorage` is synchronous, string-only and small; use it at most for trivial view preferences.
- Data that main needs (sync, menus, search, export) belongs in main's storage, not in IndexedDB.
- One owner per file. Two processes writing the same JSON file or opening the same SQLite database for writing without coordination is how data gets lost.

## Small Settings: Atomic JSON Writes

A crash or power loss in the middle of `writeFile` leaves a truncated file. Write to a temp file in the same directory, flush it, then rename over the original; the rename is atomic on the same filesystem.

```typescript
// src/main/json-store.ts
import { app } from 'electron';
import { readFileSync } from 'node:fs';
import { open, rename, rm } from 'node:fs/promises';
import path from 'node:path';

const resolve = (name: string) => path.join(app.getPath('userData'), name);
const queues = new Map<string, Promise<void>>(); // serialize writes per file

export function readJson<T>(name: string): T | null {
  try { return JSON.parse(readFileSync(resolve(name), 'utf8')) as T; }
  catch { return null; } // missing or corrupt → caller falls back to defaults
}

export function writeJsonAtomic(name: string, data: unknown): Promise<void> {
  const prev = queues.get(name) ?? Promise.resolve();
  const next = prev.catch(() => {}).then(async () => {
    const target = resolve(name);
    const tmp = `${target}.${process.pid}.tmp`;
    const fh = await open(tmp, 'w', 0o600);
    try {
      await fh.writeFile(JSON.stringify(data));
      await fh.sync(); // data on disk before the rename makes it visible
    } finally {
      await fh.close();
    }
    try { await rename(tmp, target); }
    catch (err) { await rm(tmp, { force: true }); throw err; }
  });
  queues.set(name, next);
  return next;
}
```

- Validate what you read with zod and fall back to defaults field by field; a settings file from a newer app version or a hand edit must not crash startup.
- Reading synchronously at startup is fine for a few KB; never read or write large files synchronously in main.
- On Windows, `rename` can fail with `EPERM`/`EBUSY` while antivirus or indexing holds the file; retry a few times with a short delay.

## SQLite

`better-sqlite3` is the common choice: fast, synchronous API, prebuilt binaries for most platforms.

**Build and packaging** (build-config.md "Native Modules"): Forge rebuilds it against Electron's ABI; mark it `external` in the main (and worker) Vite config; keep it in `dependencies`; with Forge's Vite plugin, copy it and its dependencies (`bindings`, `file-uri-to-path`, ...) into the build yourself, because the plugin packages only `.vite/` output; unpack `.node` files from the ASAR (Forge's auto-unpack-natives plugin, or electron-builder's `asarUnpack`); build per architecture.

**Main or utility process.** The API is synchronous: every query blocks the process it runs in.

- Main is acceptable for small, indexed queries that take well under a millisecond (settings, lookups by id).
- Full-text indexing, imports, large scans, migrations on big databases and `VACUUM` go to a `utilityProcess` that owns the database, with main forwarding requests (or a MessagePort brokered to the renderer, process-architecture.md).
- Never load a native module in the renderer.

```typescript
// src/main/db.ts (or src/workers/db-worker.ts)
import Database from 'better-sqlite3';
import { app } from 'electron';
import path from 'node:path';
import { migrate } from './migrations';

export function openDatabase(): Database.Database {
  const file = path.join(app.getPath('userData'), 'atlas.db');
  const db = new Database(file);
  db.pragma('journal_mode = WAL');   // readers don't block the writer, fewer fsyncs
  db.pragma('synchronous = NORMAL'); // safe with WAL; FULL if every commit must survive power loss
  db.pragma('foreign_keys = ON');    // off by default in SQLite
  db.pragma('busy_timeout = 5000');
  migrate(db, file);
  return db;
}
```

In a utility process, `app` is not available; pass the database path from main as an argument or in the first message.

- Use prepared statements with bound parameters; never build SQL from renderer strings.
- Wrap multi-statement writes in `db.transaction(...)`.
- Close the database on shutdown (`db.close()`), so the WAL is checkpointed (app-lifecycle.md "Graceful Shutdown").

**`node:sqlite`** (Node's built-in SQLite) would remove the native-module build step. Whether it is available and stable in the Node bundled with the targeted Electron major is an **open question** (sources.md); evaluate it, but do not make it the default until confirmed.

## Schema Migrations

Forward-only, numbered, run at startup in main before any window opens, each in a transaction. Track the schema version in `PRAGMA user_version`.

```typescript
// src/main/migrations.ts
import type Database from 'better-sqlite3';

const migrations: Array<(db: Database.Database) => void> = [
  (db) => db.exec(`CREATE TABLE document (id TEXT PRIMARY KEY, name TEXT NOT NULL, updated_at INTEGER NOT NULL)`),
  (db) => db.exec(`CREATE INDEX document_updated ON document(updated_at)`),
  // append only; never edit or reorder a shipped migration
];

export function migrate(db: Database.Database, file: string): void {
  const current = db.pragma('user_version', { simple: true }) as number;
  if (current > migrations.length) {
    throw new Error(`Database is newer (v${current}) than this app (v${migrations.length})`); // downgrade
  }
  if (current === migrations.length) return;
  backupBeforeMigration(db, file, current); // see below
  for (let v = current; v < migrations.length; v++) {
    db.transaction(() => {
      migrations[v](db);
      db.pragma(`user_version = ${v + 1}`);
    })();
  }
}
```

- A database newer than the app happens after a rollback or a downgrade (auto-update.md "Rollout and Rollback Safety"). Refuse to open it with a clear message rather than corrupt it; additive migrations make older builds tolerant.
- Changes SQLite cannot do with `ALTER TABLE` (dropping or changing columns on older SQLite) use the create-new-table, copy, drop, rename pattern inside the transaction.
- Test every migration from every shipped version against a fixture database in Vitest.

## Backups and Corruption

```typescript
import { copyFileSync } from 'node:fs';

function backupBeforeMigration(db: Database.Database, file: string, version: number): void {
  db.pragma('wal_checkpoint(TRUNCATE)');               // fold the WAL into the main file
  copyFileSync(file, `${file}.v${version}.bak`);        // keep the last one or two
}

export function checkIntegrity(db: Database.Database): boolean {
  return db.pragma('quick_check', { simple: true }) === 'ok'; // integrity_check is thorough but slower
}
```

- For backups while the app is running, use `db.backup(destination)` (online backup API, async in better-sqlite3), not a file copy of a live WAL database.
- Run `quick_check` at startup on a schedule (e.g. weekly) or after an unclean shutdown, in the utility process for large databases.
- Restore path: if the check fails or opening throws `SQLITE_CORRUPT`/`SQLITE_NOTADB`, close the database, move the broken file aside (keep it for support), restore the newest backup, tell the user what was lost, and report the event to crash reporting. Never silently start with an empty database.
- Recover settings the same way: a corrupt JSON file is renamed to `*.corrupt` and replaced by defaults, with a log entry.

## Secrets

Never store tokens or keys in plain JSON, SQLite or `localStorage`. Use `safeStorage` (security.md "Secrets with safeStorage"); keep the ciphertext in its own file in `userData`, and handle the Linux `basic_text` backend explicitly.

## Export and Deletion (Privacy)

- **Export**: main shows `dialog.showSaveDialog`, serializes from its own storage and writes the file; the renderer triggers it via a contract channel (`data:export`) and never supplies the path.
- **Delete account / reset app**: one main-side function that closes the database and workers, deletes the app's files in `userData`, clears Chromium storage for every session/partition (`session.clearStorageData()`, `clearCache()`), removes secrets, then relaunches (`app.relaunch(); app.exit(0)`).
- **Uninstall**: installers usually leave `userData` behind. Document where data lives; offer "delete my data" inside the app rather than relying on the uninstaller.
- Logs and crash dumps may contain personal data; include them in deletion and keep retention short.

## Checklist

- [ ] All user data under `userData` / `sessionData`; nothing written to the bundle or ASAR
- [ ] Settings validated on read, written atomically, one owner per file
- [ ] SQLite: WAL, foreign keys on, prepared statements, heavy work off main
- [ ] Migrations forward-only via `user_version`, run before windows, backup first, downgrade refused
- [ ] Corruption detected and restored from backup, never silently reset
- [ ] Secrets only through `safeStorage`; export and delete-all implemented in main
