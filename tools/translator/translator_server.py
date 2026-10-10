from __future__ import annotations

import argparse
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


PLACEHOLDER_PATTERN = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)[^{}]*\}(?!\})")


def get_project_root() -> Path:
    # tools/translator/translator_server.py -> root is 2 parents up
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = get_project_root()
LANG_DIR = PROJECT_ROOT / "lang"
BACKUP_DIR = LANG_DIR / ".backups"
STATIC_DIR = Path(__file__).resolve().parent / "static"


def extract_placeholders(text: str) -> list[str]:
    if not text:
        return []
    return sorted(set(PLACEHOLDER_PATTERN.findall(text)))


def load_json_file(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    if path.exists():
        path.unlink()
    tmp_path.rename(path)


def list_available_languages() -> list[dict]:
    languages = []
    if not LANG_DIR.exists():
        return languages

    for p in sorted(LANG_DIR.glob("*.json")):
        try:
            data = load_json_file(p)
            meta = data.get("meta", {})
            locale = meta.get("locale") or p.stem
            name = meta.get("name") or locale
            translations = data.get("translations", {})
            languages.append({
                "locale": locale,
                "name": name,
                "filename": p.name,
                "is_source": locale == "en-US",
                "key_count": len(translations) if isinstance(translations, dict) else 0,
            })
        except Exception:
            continue
    return languages


def audit_locale(locale: str) -> dict:
    source_path = LANG_DIR / "en-US.json"
    target_path = LANG_DIR / f"{locale}.json"

    if not source_path.exists():
        return {"valid": False, "errors": ["Source language en-US.json not found."]}
    if not target_path.exists():
        return {"valid": False, "errors": [f"Target language {locale}.json not found."]}

    try:
        source_data = load_json_file(source_path)
        target_data = load_json_file(target_path)
    except Exception as e:
        return {"valid": False, "errors": [f"JSON read error: {e}"]}

    source_tr = source_data.get("translations", {})
    target_tr = target_data.get("translations", {})

    source_keys = set(source_tr)
    target_keys = set(target_tr)

    errors: list[str] = []
    warnings: list[str] = []

    # Missing keys
    missing_in_target = sorted(source_keys - target_keys)
    for k in missing_in_target:
        errors.append(f"Missing key in {locale}: {k}")

    # Extra keys
    extra_in_target = sorted(target_keys - source_keys)
    for k in extra_in_target:
        warnings.append(f"Extra key not found in en-US: {k}")

    # Empty and placeholder checks
    empty_keys: list[str] = []
    placeholder_mismatches: list[dict] = []
    identical_keys: list[str] = []

    for k in sorted(source_keys & target_keys):
        s_val = str(source_tr.get(k, ""))
        t_val = str(target_tr.get(k, ""))

        if not t_val.strip():
            empty_keys.append(k)
            errors.append(f"Empty translation: {k}")
            continue

        s_placeholders = extract_placeholders(s_val)
        t_placeholders = extract_placeholders(t_val)
        if s_placeholders != t_placeholders:
            placeholder_mismatches.append({
                "key": k,
                "source_placeholders": s_placeholders,
                "target_placeholders": t_placeholders,
            })
            errors.append(
                f"Placeholder mismatch for {k}: source={s_placeholders}, target={t_placeholders}"
            )

        if s_val == t_val and len(s_val) > 2 and not s_val.startswith("{"):
            identical_keys.append(k)

    return {
        "valid": len(errors) == 0,
        "locale": locale,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "total_source_keys": len(source_keys),
            "total_target_keys": len(target_keys),
            "missing_count": len(missing_in_target),
            "extra_count": len(extra_in_target),
            "empty_count": len(empty_keys),
            "placeholder_mismatch_count": len(placeholder_mismatches),
            "identical_count": len(identical_keys),
        },
    }


def load_locale_data(locale: str) -> dict:
    source_path = LANG_DIR / "en-US.json"
    target_path = LANG_DIR / f"{locale}.json"

    if not source_path.exists():
        raise FileNotFoundError("Source language en-US.json not found")
    if not target_path.exists():
        raise FileNotFoundError(f"Target language pack {locale}.json not found")

    source_data = load_json_file(source_path)
    target_data = load_json_file(target_path)

    source_tr = source_data.get("translations", {})
    target_tr = target_data.get("translations", {})

    items = []
    namespaces: dict[str, int] = {}
    stats = {
        "total": len(source_tr),
        "translated": 0,
        "untranslated": 0,
        "identical": 0,
        "placeholder_mismatch": 0,
    }

    for key, source_text in source_tr.items():
        namespace = key.split(".")[0] if "." in key else "other"
        namespaces[namespace] = namespaces.get(namespace, 0) + 1

        target_text = target_tr.get(key, "")
        source_ph = extract_placeholders(source_text)
        target_ph = extract_placeholders(target_text)

        is_empty = not target_text.strip()
        ph_match = source_ph == target_ph
        is_identical = bool(target_text) and target_text == source_text

        status = "translated"
        if is_empty:
            status = "untranslated"
            stats["untranslated"] += 1
        elif not ph_match:
            status = "placeholder_mismatch"
            stats["placeholder_mismatch"] += 1
        elif is_identical:
            status = "identical"
            stats["identical"] += 1
            stats["translated"] += 1
        else:
            stats["translated"] += 1

        items.append({
            "key": key,
            "namespace": namespace,
            "source": source_text,
            "target": target_text,
            "source_placeholders": source_ph,
            "target_placeholders": target_ph,
            "status": status,
        })

    # Sort namespaces by frequency
    sorted_namespaces = sorted(
        [{"name": k, "count": v} for k, v in namespaces.items()],
        key=lambda x: (-x["count"], x["name"])
    )

    return {
        "locale": locale,
        "meta": target_data.get("meta", {}),
        "stats": stats,
        "namespaces": sorted_namespaces,
        "items": items,
    }


def save_locale_data(locale: str, meta: dict, translations: dict) -> dict:
    target_path = LANG_DIR / f"{locale}.json"

    # 1. Create backup if file exists
    backup_file = None
    if target_path.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"{locale}_{timestamp}.json"
        shutil.copy2(target_path, backup_file)

    # 2. Build full payload
    meta_payload = {
        "locale": meta.get("locale") or locale,
        "name": meta.get("name") or locale,
        "version": meta.get("version", 1),
    }

    payload: dict = {
        "meta": meta_payload,
        "translations": translations,
    }

    # Only include aliases for en-US if present
    if locale == "en-US":
        existing = load_json_file(target_path) if target_path.exists() else {}
        if "aliases" in existing:
            payload["aliases"] = existing["aliases"]

    # 3. Save JSON
    save_json_file(target_path, payload)

    return {
        "success": True,
        "backup": str(backup_file.relative_to(PROJECT_ROOT)) if backup_file else None,
        "key_count": len(translations),
    }


def create_new_locale(locale: str, name: str, copy_source: bool = False) -> dict:
    locale = locale.strip()
    name = name.strip()
    if not locale:
        raise ValueError("Mã ngôn ngữ (Locale) không được để trống")
    if not name:
        raise ValueError("Tên hiển thị (Name) không được để trống")

    target_path = LANG_DIR / f"{locale}.json"
    if target_path.exists():
        raise FileExistsError(f"Gói ngôn ngữ {locale}.json đã tồn tại!")

    source_path = LANG_DIR / "en-US.json"
    source_data = load_json_file(source_path)
    source_tr = source_data.get("translations", {})

    target_tr = {}
    for k, v in source_tr.items():
        target_tr[k] = v if copy_source else ""

    payload = {
        "meta": {
            "locale": locale,
            "name": name,
            "version": 1,
        },
        "translations": target_tr,
    }

    save_json_file(target_path, payload)
    return {
        "locale": locale,
        "name": name,
        "filename": f"{locale}.json",
        "key_count": len(target_tr),
    }


def export_locale_csv(locale: str) -> str:
    import csv

    data = load_locale_data(locale)
    output = io.StringIO()
    # Write UTF-8 BOM so Excel opens properly
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(["Key", "Namespace", "Source (en-US)", f"Translation ({locale})", "Placeholders", "Status"])

    for item in data["items"]:
        writer.writerow([
            item["key"],
            item["namespace"],
            item["source"],
            item["target"],
            ", ".join(item["source_placeholders"]),
            item["status"],
        ])

    return output.getvalue()


class TranslatorRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        # Suppress noisy GET log spam for static files
        if args and str(args[0]).startswith("GET /static"):
            return
        super().log_message(format, *args)

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/":
            self.path = "/index.html"
            return super().do_GET()

        if path.startswith("/static/"):
            self.path = path[len("/static"):]
            return super().do_GET()

        if path == "/api/languages":
            self.send_json_response(list_available_languages())
            return

        if path == "/api/load":
            locale = query.get("locale", ["vi-VN"])[0]
            try:
                data = load_locale_data(locale)
                self.send_json_response(data)
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/audit":
            locale = query.get("locale", ["vi-VN"])[0]
            result = audit_locale(locale)
            self.send_json_response(result)
            return

        if path == "/api/export-csv":
            locale = query.get("locale", ["vi-VN"])[0]
            try:
                csv_data = export_locale_csv(locale)
                content = csv_data.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header(
                    "Content-Disposition", f'attachment; filename="mcw_lang_{locale}.csv"'
                )
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        return super().do_GET()

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            json_body = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self.send_json_response({"error": f"Invalid JSON payload: {e}"}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/save":
            locale = json_body.get("locale")
            meta = json_body.get("meta", {})
            translations = json_body.get("translations", {})
            if not locale:
                self.send_json_response({"error": "Missing locale"}, status=HTTPStatus.BAD_REQUEST)
                return
            try:
                res = save_locale_data(locale, meta, translations)
                self.send_json_response(res)
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if path == "/api/create-language":
            locale = json_body.get("locale", "")
            name = json_body.get("name", "")
            copy_source = bool(json_body.get("copy_source", False))
            try:
                res = create_new_locale(locale, name, copy_source)
                self.send_json_response(res)
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/import-csv":
            import csv
            locale = json_body.get("locale")
            csv_text = json_body.get("csv_text", "")
            if not locale or not csv_text:
                self.send_json_response({"error": "Missing locale or csv_text"}, status=HTTPStatus.BAD_REQUEST)
                return
            try:
                reader = csv.reader(io.StringIO(csv_text.strip()))
                header = next(reader, None)
                if not header:
                    raise ValueError("Empty CSV file")
                
                # Try finding Key column and Translation column
                key_col = 0
                val_col = 3 if len(header) > 3 else 1
                for idx, col in enumerate(header):
                    col_lower = col.strip().lower()
                    if "key" in col_lower:
                        key_col = idx
                    elif "translation" in col_lower or "dịch" in col_lower:
                        val_col = idx

                imported: dict[str, str] = {}
                for row in reader:
                    if len(row) > max(key_col, val_col):
                        k = row[key_col].strip()
                        v = row[val_col]
                        if k:
                            imported[k] = v

                self.send_json_response({
                    "success": True,
                    "imported_count": len(imported),
                    "translations": imported,
                })
            except Exception as e:
                self.send_json_response({"error": f"Import error: {e}"}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_json_response({"error": "Endpoint not found"}, status=HTTPStatus.NOT_FOUND)

    def send_json_response(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def find_free_port(starting_port: int = 8765, max_attempts: int = 50) -> int:
    for port in range(starting_port, starting_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return starting_port


def main() -> None:
    parser = argparse.ArgumentParser(description="MCW Launcher Translation Studio")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    port = find_free_port(args.port)
    server_address = (args.host, port)
    httpd = HTTPServer(server_address, TranslatorRequestHandler)

    url = f"http://{args.host}:{port}/"
    print("=" * 60)
    print("   MCW LAUNCHER TRANSLATION STUDIO")
    print("=" * 60)
    print(f"[+] Server running at:     {url}")
    print(f"[*] Language packs dir:    {LANG_DIR}")
    print(f"[*] Automatic backups dir: {BACKUP_DIR}")
    print("[*] Press Ctrl + C to stop the server.")
    print("=" * 60)

    if not args.no_browser:
        def open_browser():
            import time
            time.sleep(0.6)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMCW Translation Studio stopped. Goodbye!")
        httpd.server_close()



if __name__ == "__main__":
    main()
