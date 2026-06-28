from mcp.server.fastmcp import FastMCP
import sqlite3, os, re, json, hashlib, io, zipfile, tarfile, gzip
import pandas as pd
from openai import OpenAI

try:
    import py7zr
    HAVE_7Z = True
except ImportError:
    HAVE_7Z = False

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mcp = FastMCP("Autonomous_Learner_Agent")
BASE_LOG_DIR = "/logs"
DB_PATH = "/app/db/universal_index.db"
LEARNED_PARSERS_FILE = "/app/db/learned_parsers.py"

# Local model used ONLY to write/learn new parsers - no cloud API, no quota.
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1")
PARSER_MODEL = os.getenv("PARSER_MODEL", "qwen2.5-coder:7b")
llm_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

# A "prompt line" is what marks the start of a new command in a CLI session
# transcript (PuTTY logs, SSH session logs, etc). Default matches typical
# ONTAP cluster/vserver prompts like "cluster1::> volume show" or
# "cluster1::*> ..." (advanced mode). Override per-environment if your
# prompts look different - no rebuild needed, just set PROMPT_REGEX in .env.
PROMPT_REGEX = os.getenv("PROMPT_REGEX") or r"^\S+::\*?>\s*(.*)$"

TEXT_EXTS = (".txt", ".log", ".json", ".ndjson", ".jsonl", ".out", ".csv")
MAX_EXTRACT_SIZE = int(os.getenv("MAX_EXTRACT_SIZE_MB", "100")) * 1024 * 1024
MAX_ARCHIVE_DEPTH = int(os.getenv("MAX_ARCHIVE_DEPTH", "4"))

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
if not os.path.exists(LEARNED_PARSERS_FILE):
    with open(LEARNED_PARSERS_FILE, "w") as f:
        f.write("# This file contains AI-generated parsers.\nimport re\n")


# ---------------------------------------------------------------------------
# Archive-transparent source iteration
# ---------------------------------------------------------------------------
def _iter_sources(base_dir: str):
    """Yields (virtual_path, text, error) for every log-ish source under
    base_dir, transparently descending into .zip / .tar / .tar.gz / .tgz /
    .tar.bz2 / .gz / .7z archives - including archives nested inside
    archives, up to MAX_ARCHIVE_DEPTH. virtual_path looks like
    'archive.zip::subdir/file.log' for nested members so each one still gets
    its own stable identity for the ingest manifest."""
    for root, _, files in os.walk(base_dir):
        for file in files:
            path = os.path.join(root, file)
            yield from _expand(path, path, depth=0)


def _expand(source, label: str, depth: int):
    if depth > MAX_ARCHIVE_DEPTH:
        yield (label, None, "archive nesting too deep, skipped")
        return
    lname = label.lower()
    try:
        if lname.endswith(".zip"):
            yield from _expand_zip(source, label, depth)
            return
        if lname.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar")):
            yield from _expand_tar(source, label, depth)
            return
        if lname.endswith(".7z"):
            yield from _expand_7z(source, label, depth)
            return
        if lname.endswith(".gz"):
            yield from _expand_gz(source, label, depth)
            return
    except Exception as e:
        yield (label, None, f"archive read error: {e}")
        return

    if not lname.endswith(TEXT_EXTS):
        return
    try:
        if isinstance(source, str):
            with open(source, "rb") as f:
                data = f.read(MAX_EXTRACT_SIZE)
        else:
            data = source[:MAX_EXTRACT_SIZE]
        yield (label, data.decode("utf-8", "ignore"), None)
    except Exception as e:
        yield (label, None, f"read error: {e}")


def _expand_zip(source, label, depth):
    with zipfile.ZipFile(source if isinstance(source, str) else io.BytesIO(source)) as zf:
        for info in zf.infolist():
            if info.is_dir() or info.file_size > MAX_EXTRACT_SIZE:
                continue
            data = zf.read(info.filename)
            yield from _expand(data, f"{label}::{info.filename}", depth + 1)


def _expand_tar(source, label, depth):
    if isinstance(source, str):
        tf = tarfile.open(source, mode="r:*")
    else:
        tf = tarfile.open(fileobj=io.BytesIO(source), mode="r:*")
    with tf:
        for member in tf.getmembers():
            if not member.isfile() or member.size > MAX_EXTRACT_SIZE:
                continue
            f = tf.extractfile(member)
            if not f:
                continue
            data = f.read()
            yield from _expand(data, f"{label}::{member.name}", depth + 1)


def _expand_gz(source, label, depth):
    fileobj = open(source, "rb") if isinstance(source, str) else io.BytesIO(source)
    try:
        with gzip.GzipFile(fileobj=fileobj) as gz:
            data = gz.read(MAX_EXTRACT_SIZE)
    finally:
        if isinstance(source, str):
            fileobj.close()
    inner_label = label[:-3] if lname_ends_gz(label) else label + ".decompressed"
    yield from _expand(data, inner_label, depth + 1)


def lname_ends_gz(label: str) -> bool:
    return label.lower().endswith(".gz")


def _expand_7z(source, label, depth):
    if not HAVE_7Z:
        yield (label, None, "py7zr not installed - .7z archive skipped")
        return
    with py7zr.SevenZipFile(source if isinstance(source, str) else io.BytesIO(source), mode="r") as sz:
        for name, bio in sz.readall().items():
            data = bio.read()
            if len(data) > MAX_EXTRACT_SIZE:
                continue
            yield from _expand(data, f"{label}::{name}", depth + 1)


# ---------------------------------------------------------------------------
# JSON / NDJSON - structured logs need NO learning step at all
# ---------------------------------------------------------------------------
def _looks_like_json(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    try:
        json.loads(stripped)
        return True
    except Exception:
        pass
    lines = [l for l in stripped.splitlines() if l.strip()][:20]
    if not lines:
        return False
    ok = sum(1 for l in lines if _try_json(l))
    return ok >= max(1, int(len(lines) * 0.8))


def _try_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except Exception:
        return False


def _iter_json_records(text: str):
    """Handles a plain JSON object, a JSON array, REST-API-style wrapper
    objects (e.g. ONTAP's {"records": [...], "num_records": N}), and NDJSON
    (one JSON object per line) - covers ONTAP REST API dumps, Harvest-style
    poller output, and line-delimited audit logs alike."""
    stripped = text.strip()
    try:
        data = json.loads(stripped)
        if isinstance(data, list):
            for rec in data:
                if isinstance(rec, dict):
                    yield rec
            return
        if isinstance(data, dict):
            for key in ("records", "results", "data", "events", "items"):
                val = data.get(key)
                if isinstance(val, list):
                    for rec in val:
                        if isinstance(rec, dict):
                            yield rec
                    return
            yield data
            return
    except Exception:
        pass
    for line in stripped.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                yield rec
        except Exception:
            continue


def _flatten(rec: dict, parent_key: str = "") -> dict:
    items = {}
    for k, v in rec.items():
        new_key = f"{parent_key}.{k}" if parent_key else str(k)
        if isinstance(v, dict):
            items.update(_flatten(v, new_key))
        elif isinstance(v, list):
            items[new_key] = json.dumps(v)
        else:
            items[new_key] = v
    return items


def _json_table_name(rec: dict, fallback: str) -> str:
    # Common discriminator field names across ONTAP REST objects, S3-style
    # audit events, and metrics exporters. Add your own here later if your
    # Harvest/S3-audit payloads use a different field name for "what kind of
    # record is this".
    for key in ("op_type", "event_type", "type", "category", "object", "action", "operation"):
        val = rec.get(key)
        if isinstance(val, str) and val.strip():
            return _safe_name(val)
    return _safe_name(fallback)


# ---------------------------------------------------------------------------
# CLI / transcript logs (PuTTY session logs etc.) - split into command blocks
# ---------------------------------------------------------------------------
def _split_into_blocks(text: str, prompt_re):
    """Splits a transcript at prompt-line boundaries into (command, output_lines)
    blocks. If NOTHING matches the prompt pattern (i.e. this isn't a CLI
    transcript at all - a plain EMS/messages-style log file, say), falls back
    to treating the WHOLE file as a single block, preserving the original
    whole-file learning behaviour for non-transcript logs."""
    lines = text.splitlines()
    blocks = []
    current_cmd, current_output = None, []
    for line in lines:
        m = prompt_re.match(line)
        if m:
            if current_cmd is not None:
                blocks.append((current_cmd, current_output))
            cmd = m.group(1).strip()
            current_cmd = cmd if cmd else None
            current_output = []
        elif current_cmd is not None:
            current_output.append(line)
    if current_cmd is not None:
        blocks.append((current_cmd, current_output))
    return blocks


def _command_family(cmd_line: str) -> str:
    """Reduces a typed command to a stable 'family' name, e.g.
    'volume show -vserver svm1 -fields size' -> 'volume_show'. This is the
    key thing that lets ONE parser cover the same command run thousands of
    times across different files/sessions/dates, instead of learning a new
    (and wrong) parser per file."""
    no_flags = re.sub(r'-{1,2}\S+(\s+"[^"]*"|\s+\S+)?', "", cmd_line)
    tokens = [t for t in no_flags.split() if not re.match(r"^[\d.:/_-]+$", t)]
    family = "_".join(tokens[:3]).lower()
    family = re.sub(r"[^a-z0-9_]", "", family)
    return family or "cmd"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _init_tables(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS ingest_manifest (
        content_hash    TEXT PRIMARY KEY,
        source_path     TEXT,
        status          TEXT,
        units_total     INTEGER,
        units_matched   INTEGER,
        units_unmatched INTEGER,
        ingested_at     TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS parser_registry (
        family        TEXT PRIMARY KEY,
        parser_name   TEXT,
        sample_source TEXT,
        learned_at    TEXT
    )""")
    conn.commit()


def _safe_name(raw: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw).strip().lower()).strip("_")
    if name and name[0].isdigit():
        name = "t_" + name
    return name or "logtype"


def _extract_code(raw: str) -> str:
    code = raw.strip()
    code = re.sub(r"^```(python)?", "", code).strip()
    code = re.sub(r"```$", "", code).strip()
    return code


def _test_parser(code: str, func_name: str, sample: str):
    ns = {}
    try:
        exec(code, {"re": re}, ns)
    except Exception as e:
        return False, f"Generated code does not even compile/run: {e}"
    func = ns.get(func_name)
    if not func:
        return False, f"Function {func_name} was not defined by the generated code."
    try:
        result = func(sample)
    except Exception as e:
        return False, f"Parser raised an exception on the sample: {e}"
    if not isinstance(result, list) or not result:
        return False, "Parser did not return a non-empty list."
    if not isinstance(result[0], dict):
        return False, "Parser must return a list of dicts."
    return True, "ok"


def _call_local_llm(prompt: str) -> str:
    resp = llm_client.chat.completions.create(
        model=PARSER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return resp.choices[0].message.content


def _safe_append(conn, table: str, rows: list) -> int:
    """Appends rows to `table`, creating it if needed and auto-extending its
    schema (ALTER TABLE ADD COLUMN) if a row has fields the table doesn't
    have yet. This is what lets evolving JSON shapes - new Harvest metric
    labels, new audit-event fields, etc. - keep ingesting without breaking,
    instead of throwing 'no such column' on the first schema drift."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    for col in df.columns:
        df[col] = df[col].apply(lambda v: json.dumps(v) if isinstance(v, (dict, list)) else v)
    try:
        existing_cols = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
    except Exception:
        existing_cols = set()
    if existing_cols:
        for col in df.columns:
            if col not in existing_cols:
                try:
                    conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" TEXT')
                except Exception:
                    pass
    df.to_sql(table, conn, if_exists="append", index=False)
    return len(df)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def learn_log_format(log_sample: str, log_type_name: str) -> str:
    """OFFLINE: Teaches the system a new log/command format using the LOCAL
    Ollama model - no cloud, no internet, no rate limit. `log_sample` can be
    a raw block of CLI output (a command plus its output) or a plain log
    excerpt; `log_type_name` is a short name (e.g. 'volume_show',
    'ems_events'). The parser is self-tested against your sample and only
    kept if it actually works."""
    family = _safe_name(log_type_name)
    func_name = f"parse_{family}"
    sample = log_sample[:3000]

    prompt = f"""Write a single Python function named `{func_name}(text_content)` that
parses the raw text below into a list of dictionaries (one dict per
record/row, with sensible field names inferred from the structure).

Rules:
- Return ONLY raw python code. No markdown fences, no explanation.
- You may only use the `re` module (already imported for you) and builtins.
- Never raise on a malformed line - skip lines you can't parse.
- Always return a list, even if some lines were skipped.

SAMPLE:
{sample}
"""
    last_error = "unknown"
    for _ in range(2):
        raw = _call_local_llm(prompt)
        code = _extract_code(raw)
        ok, msg = _test_parser(code, func_name, sample)
        if ok:
            with open(LEARNED_PARSERS_FILE, "a") as f:
                f.write(f"\n\n{code}\n")
            conn = sqlite3.connect(DB_PATH)
            _init_tables(conn)
            conn.execute(
                "INSERT OR REPLACE INTO parser_registry (family, parser_name, sample_source, learned_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (family, func_name, log_type_name),
            )
            conn.commit()
            conn.close()
            return f"Success! Learned '{family}' -> {func_name} (self-tested OK)."
        last_error = msg
        prompt += f"\n\nYour previous attempt failed self-test:\n{last_error}\nReturn a corrected function only."
    return f"Failed to learn '{family}' after retries. Last error: {last_error}"


@mcp.tool()
def unsupervised_auto_discovery() -> str:
    """Scans BASE_LOG_DIR, transparently descending into zip/tar/tar.gz/tgz/
    tar.bz2/gz/7z archives (including nested archives). JSON/NDJSON content
    is detected automatically and needs NO learning step. Everything else is
    split into command blocks at prompt boundaries (or treated as one whole
    block if it isn't a CLI transcript at all) and clustered by command
    family - so the local LLM is called once per distinct COMMAND, not once
    per file and not once per block."""
    conn = sqlite3.connect(DB_PATH)
    _init_tables(conn)
    known_families = {row[0] for row in conn.execute("SELECT family FROM parser_registry")}
    conn.close()

    prompt_re = re.compile(PROMPT_REGEX)
    clusters = {}
    scanned = json_count = cli_count = archive_errors = 0

    for label, text, err in _iter_sources(BASE_LOG_DIR):
        if err:
            archive_errors += 1
            continue
        scanned += 1
        if _looks_like_json(text):
            json_count += 1
            continue

        cli_count += 1
        blocks = _split_into_blocks(text, prompt_re)
        if not blocks:
            fallback = re.sub(r"[\d\W_]+", "", os.path.basename(label).split(".")[0]).lower() or "log"
            blocks = [(fallback, text.splitlines())]

        for cmd, output_lines in blocks:
            family = _command_family(cmd)
            if family in known_families or family in clusters:
                continue
            block_text = f"COMMAND: {cmd}\n" + "\n".join(output_lines[:60])
            clusters[family] = (block_text, label)

    summary = [
        f"Scanned {scanned} log sources ({json_count} JSON/NDJSON - no learning needed, "
        f"{cli_count} transcript/plain-text style). {archive_errors} archive/read errors skipped."
    ]
    if not clusters:
        summary.append("No new command/log formats to learn - everything matches what's already known.")
        return "\n".join(summary)

    summary.append(f"Found {len(clusters)} new distinct format(s) to learn.")
    for family, (block_text, example_source) in clusters.items():
        outcome = learn_log_format(block_text, family)
        summary.append(f"'{family}' (seen in {example_source}): {outcome}")
    return "\n".join(summary)


@mcp.tool()
def auto_ingest_directory() -> str:
    """Applies everything learned so far to BASE_LOG_DIR (including inside
    archives). JSON/NDJSON sources are parsed generically - tables are
    created/extended automatically as new fields appear, no parser needed.
    Transcript sources are split into command blocks and matched against
    learned parsers by command family. Safe to re-run any time new logs are
    dropped in - already-ingested sources are skipped via a content-hash
    manifest, so nothing is reprocessed or duplicated."""
    parsers = {}
    try:
        exec(open(LEARNED_PARSERS_FILE).read(), {"re": re}, parsers)
    except Exception as e:
        return f"Error loading learned parsers: {e}"

    conn = sqlite3.connect(DB_PATH)
    _init_tables(conn)
    registry = dict(conn.execute("SELECT family, parser_name FROM parser_registry").fetchall())
    already = {row[0] for row in conn.execute("SELECT content_hash FROM ingest_manifest WHERE status IN ('ingested','empty')")}
    prompt_re = re.compile(PROMPT_REGEX)

    new_sources = matched_units = unmatched_units = errors = 0

    for label, text, err in _iter_sources(BASE_LOG_DIR):
        if err:
            errors += 1
            conn.execute(
                "INSERT OR REPLACE INTO ingest_manifest (content_hash, source_path, status, units_total, units_matched, units_unmatched, ingested_at) "
                "VALUES (?,?,?,?,?,?, datetime('now'))",
                (hashlib.sha256(label.encode()).hexdigest(), label, "error", 0, 0, 0),
            )
            continue

        chash = _content_hash(text)
        if chash in already:
            continue
        new_sources += 1

        if _looks_like_json(text):
            total = 0
            grouped = {}
            for rec in _iter_json_records(text):
                total += 1
                table = _json_table_name(rec, fallback=os.path.basename(label))
                grouped.setdefault(table, []).append(_flatten(rec))
            matched = sum(_safe_append(conn, t, rows) for t, rows in grouped.items())
            matched_units += matched
            unmatched_units += max(0, total - matched)
            conn.execute(
                "INSERT OR REPLACE INTO ingest_manifest (content_hash, source_path, status, units_total, units_matched, units_unmatched, ingested_at) "
                "VALUES (?,?,?,?,?,?, datetime('now'))",
                (chash, label, "ingested" if total else "empty", total, matched, max(0, total - matched)),
            )
            continue

        blocks = _split_into_blocks(text, prompt_re)
        if not blocks:
            fallback = re.sub(r"[\d\W_]+", "", os.path.basename(label).split(".")[0]).lower() or "log"
            blocks = [(fallback, text.splitlines())]

        total, matched = len(blocks), 0
        for cmd, output_lines in blocks:
            family = _command_family(cmd)
            parser_name = registry.get(family)
            if not parser_name or parser_name not in parsers:
                continue
            block_text = f"COMMAND: {cmd}\n" + "\n".join(output_lines) if output_lines else cmd
            try:
                rows = parsers[parser_name](block_text)
                if rows:
                    for row in rows:
                        row.setdefault("_source_command", cmd)
                    _safe_append(conn, family, rows)
                matched += 1
            except Exception:
                continue
        matched_units += matched
        unmatched_units += (total - matched)
        conn.execute(
            "INSERT OR REPLACE INTO ingest_manifest (content_hash, source_path, status, units_total, units_matched, units_unmatched, ingested_at) "
            "VALUES (?,?,?,?,?,?, datetime('now'))",
            (chash, label, "ingested" if total else "empty", total, matched, total - matched),
        )

    conn.commit()
    conn.close()
    return (
        f"Ingestion complete. New sources processed: {new_sources}. "
        f"Units matched/written: {matched_units}. Units unmatched (need learning): {unmatched_units}. "
        f"Archive/read errors: {errors}."
    )


@mcp.tool()
def get_ingest_status() -> str:
    """Quick visibility into what's ingested, pending, or unmatched."""
    conn = sqlite3.connect(DB_PATH)
    _init_tables(conn)
    rows = conn.execute("SELECT status, COUNT(*) FROM ingest_manifest GROUP BY status").fetchall()
    formats = conn.execute("SELECT parser_name, family FROM parser_registry").fetchall()
    conn.close()
    status_lines = "\n".join(f"  {s}: {c}" for s, c in rows) or "  (manifest is empty - nothing ingested yet)"
    formats_lines = "\n".join(f"  {p} (family: {f})" for p, f in formats) or "  (no command/log formats learned yet)"
    return f"Ingest manifest:\n{status_lines}\n\nLearned formats:\n{formats_lines}"


@mcp.tool()
def get_database_schema() -> str:
    """Returns the structure of the log data tables (internal bookkeeping
    tables are hidden)."""
    conn = sqlite3.connect(DB_PATH)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('ingest_manifest','parser_registry');"
    ).fetchall()
    schema = "\n".join(
        f"Table {t[0]} | Columns: {', '.join(c[1] for c in conn.execute(f'PRAGMA table_info({t[0]})'))}"
        for t in tables
    )
    conn.close()
    return schema if schema else "Empty DB. Run unsupervised_auto_discovery then auto_ingest_directory."


@mcp.tool()
def execute_sql_query(query: str) -> str:
    """Executes a READ-ONLY SQL query against the index. Enforced at the
    connection level (SQLite opened in mode=ro)."""
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    except Exception as e:
        return f"Could not open database read-only: {e}"
    try:
        return pd.read_sql_query(query, conn).to_string(index=False)
    except Exception as e:
        return f"Query error: {e}"
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
