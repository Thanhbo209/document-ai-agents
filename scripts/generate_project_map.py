from __future__ import annotations

# ruff: noqa: E501
import ast
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "project-management-map.html"

SCAN_ROOTS = (
    "app",
    "web/app",
    "web/src/app",
    "web/components",
    "web/lib",
    "tests",
    "evals",
    "scripts",
    "docs",
    "infra",
    "alembic",
    "db/migrations",
)

EXTRA_DEVOPS_ROOTS = (
    "Dockerfile.api",
    "Dockerfile",
    "docker-compose.prod.yml",
    ".github",
)

IGNORED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "storage",
    "uploads",
    "artifacts",
}

IGNORED_FILE_NAMES = {
    ".env",
    "project-management-map.html",
}

IGNORED_SUFFIXES = {
    ".db",
    ".ico",
    ".pyo",
    ".pyc",
    ".sqlite",
    ".sqlite3",
}

PYTHON_SUFFIX = ".py"
TYPESCRIPT_SUFFIXES = {".ts", ".tsx"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".ps1", ".html", ".css"}

FEATURES = [
    "Authentication",
    "Workspace Tenancy",
    "Document Upload",
    "Text/PDF Ingestion",
    "Office/Table Ingestion",
    "OCR Ingestion",
    "Media Transcription",
    "Web Connector",
    "YouTube Connector",
    "Repo ZIP Connector",
    "Chunking",
    "Embeddings",
    "Vector Store",
    "Retrieval",
    "Grounded Answers",
    "Citations",
    "Source Drawer",
    "Structured Extraction",
    "Document Comparison",
    "Agent Tools",
    "Review Workflow",
    "Usage Metering",
    "Billing Plans",
    "Admin Console",
    "Audit Events",
    "Compliance Export/Delete",
    "Observability",
    "Deployment",
    "Evaluation Suite",
    "Dashboard UI",
]

SYSTEM_AREAS = [
    "Frontend Dashboard",
    "Frontend Admin Console",
    "Frontend API Client",
    "FastAPI Routes",
    "Auth / Tenancy",
    "Document Upload",
    "Ingestion Loaders",
    "Office / Table Ingestion",
    "OCR Ingestion",
    "Media Transcription",
    "Web / YouTube / Repo Connectors",
    "Chunking",
    "Embeddings",
    "Vector Store",
    "Retrieval / Reranking",
    "Grounded Answer Generation",
    "Citations / Source Drawer",
    "Structured Extraction",
    "Document Comparison / Reports",
    "Agent Tools / Orchestrator",
    "Review Workflow",
    "Usage Metering",
    "Billing Plans",
    "Admin / Support Console",
    "Audit Events",
    "Compliance Controls",
    "Observability",
    "Database Models",
    "Evals",
    "Tests",
    "Deployment / Infra",
    "Scripts",
]


@dataclass(frozen=True)
class FileRecord:
    path: Path
    rel_path: str
    suffix: str
    line_count: int
    category: str


def main() -> None:
    files = discover_files()
    data = build_project_data(files)
    html = render_html(data)
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    summary = data["summary"]
    print("Project map generated")
    print(f"Output: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Files scanned: {summary['total_files']}")
    print(f"Python files: {summary['python_files']}")
    print(f"TS/TSX files: {summary['typescript_files']}")
    print(f"FastAPI routes: {summary['fastapi_routes']}")
    print(f"Frontend components: {summary['frontend_components']}")
    print(f"Test functions: {summary['tests']}")


def discover_files() -> list[FileRecord]:
    records: list[FileRecord] = []
    seen: set[Path] = set()

    for root in SCAN_ROOTS:
        root_path = PROJECT_ROOT / root
        if not root_path.exists():
            continue

        if root_path.is_file():
            candidates = [root_path]
        else:
            candidates = [path for path in root_path.rglob("*") if path.is_file()]

        for path in candidates:
            resolved = path.resolve()
            if resolved in seen or should_ignore_path(path):
                continue
            seen.add(resolved)
            records.append(file_record(path))

    for extra in EXTRA_DEVOPS_ROOTS:
        path = PROJECT_ROOT / extra
        if not path.exists():
            continue
        if path.is_file() and path.resolve() not in seen and not should_ignore_path(path):
            seen.add(path.resolve())
            records.append(file_record(path))
        elif path.is_dir():
            for child in path.rglob("*"):
                if (
                    child.is_file()
                    and child.resolve() not in seen
                    and not should_ignore_path(child)
                ):
                    seen.add(child.resolve())
                    records.append(file_record(child))

    return sorted(records, key=lambda record: record.rel_path)


def should_ignore_path(path: Path) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    parts = set(rel.parts)

    if parts & IGNORED_DIR_NAMES:
        return True

    if path.name in IGNORED_FILE_NAMES:
        return True

    if path.name.startswith(".env"):
        return True

    return path.suffix.lower() in IGNORED_SUFFIXES


def file_record(path: Path) -> FileRecord:
    rel_path = path.relative_to(PROJECT_ROOT).as_posix()
    return FileRecord(
        path=path,
        rel_path=rel_path,
        suffix=path.suffix.lower(),
        line_count=count_lines(path),
        category=category_for_path(rel_path),
    )


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def build_project_data(files: list[FileRecord]) -> dict[str, Any]:
    py_files = [record for record in files if record.suffix == PYTHON_SUFFIX]
    ts_files = [record for record in files if record.suffix in TYPESCRIPT_SUFFIXES]
    text_files = [record for record in files if record.suffix in TEXT_SUFFIXES]

    python_items, routes, db_models, enums, python_imports = parse_python_files(py_files)
    router_prefixes = parse_router_prefixes()
    routes = [apply_route_prefix(route, router_prefixes) for route in routes]

    frontend_routes = parse_frontend_routes(files)
    api_clients = parse_frontend_api_clients(ts_files)
    frontend_components = parse_frontend_components(ts_files, api_clients)
    tests = parse_tests(py_files)
    eval_map = parse_evals(files)
    scripts = parse_scripts_and_devops(files)
    features = build_feature_map(files, routes, tests, eval_map, frontend_components)
    opportunities = build_refactor_opportunities(
        files=files,
        python_items=python_items,
        routes=routes,
        frontend_components=frontend_components,
        tests=tests,
    )
    dependencies = build_dependency_map(py_files, ts_files, python_imports)
    architecture = build_architecture_map(files, routes, python_items, frontend_components)
    roadmap = build_roadmap()

    summary = {
        "project_name": "rag-platform",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_files": len(files),
        "python_files": len(py_files),
        "typescript_files": len(ts_files),
        "backend_functions": sum(
            1 for item in python_items if item["kind"] in {"function", "method"}
        ),
        "backend_classes": sum(
            1 for item in python_items if item["kind"] in {"class", "dataclass", "protocol", "enum"}
        ),
        "frontend_components": len(frontend_components),
        "frontend_routes": len(frontend_routes),
        "fastapi_routes": len(routes),
        "database_models": len(db_models),
        "tests": sum(len(test_file["tests"]) for test_file in tests),
        "test_files": len(tests),
        "eval_cases": len(eval_map["cases"]),
        "scripts": len(scripts["scripts"]),
        "largest_files": sorted(files, key=lambda record: record.line_count, reverse=True)[:10],
        "hotspots": opportunities[:8],
        "text_files": len(text_files),
    }

    return {
        "files": files,
        "summary": summary,
        "python_items": python_items,
        "routes": routes,
        "db_models": db_models,
        "enums": enums,
        "frontend_routes": frontend_routes,
        "frontend_components": frontend_components,
        "api_clients": api_clients,
        "tests": tests,
        "eval_map": eval_map,
        "scripts": scripts,
        "features": features,
        "opportunities": opportunities,
        "dependencies": dependencies,
        "architecture": architecture,
        "roadmap": roadmap,
    }


def parse_python_files(
    files: list[FileRecord],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, list[str]],
]:
    python_items: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    db_models: list[dict[str, Any]] = []
    enums: list[dict[str, Any]] = []
    imports_by_file: dict[str, list[str]] = {}

    for record in files:
        source = read_text(record.path)
        if not source:
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        module_name = module_name_from_path(record.rel_path)
        access_map = extract_permission_access_map(tree)
        imports_by_file[record.rel_path] = extract_python_imports(tree)
        python_items.extend(extract_python_items(tree, record, module_name))
        routes.extend(extract_fastapi_routes(tree, record, module_name, access_map))

        if record.rel_path.startswith(("app/db/", "app/models/")):
            models, model_enums = extract_database_models(tree, record)
            db_models.extend(models)
            enums.extend(model_enums)

    return python_items, routes, db_models, enums, imports_by_file


def module_name_from_path(rel_path: str) -> str:
    if rel_path.endswith(".py"):
        return rel_path[:-3].replace("/", ".")
    return rel_path.replace("/", ".")


def extract_python_imports(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("app"):
                imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app"):
                    imports.append(alias.name)
    return sorted(set(imports))


def extract_permission_access_map(tree: ast.AST) -> dict[str, str]:
    access_map: dict[str, str] = {}

    for node in tree.body if isinstance(tree, ast.Module) else []:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if call_name(node.value.func) != "require_workspace_permission":
            continue

        permission = "unknown"
        if node.value.args:
            permission = unparse(node.value.args[0])

        for target in node.targets:
            if isinstance(target, ast.Name):
                access_map[target.id] = permission

    return access_map


def extract_python_items(
    tree: ast.Module,
    record: FileRecord,
    module_name: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            items.append(class_item(node, record, module_name))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    items.append(function_item(child, record, module_name, parent=node.name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            items.append(function_item(node, record, module_name, parent=None))

    return items


def class_item(node: ast.ClassDef, record: FileRecord, module_name: str) -> dict[str, Any]:
    decorators = [unparse(decorator) for decorator in node.decorator_list]
    bases = [unparse(base) for base in node.bases]
    kind = "class"
    if any("dataclass" in decorator for decorator in decorators):
        kind = "dataclass"
    if any(base.endswith("Protocol") or base == "Protocol" for base in bases):
        kind = "protocol"
    if any(base.endswith("Enum") or base in {"Enum", "StrEnum"} for base in bases):
        kind = "enum"

    return {
        "name": node.name,
        "kind": kind,
        "file": record.rel_path,
        "line": node.lineno,
        "end_line": getattr(node, "end_lineno", node.lineno),
        "parent": "",
        "args": "",
        "returns": "",
        "docstring": first_docline(node),
        "decorators": decorators,
        "module": module_name,
        "feature": guess_feature(record.rel_path, node.name),
        "responsibility": guess_responsibility(node.name, record.rel_path),
        "refactor_note": refactor_note_for_item(
            node.name, node.lineno, getattr(node, "end_lineno", node.lineno)
        ),
    }


def function_item(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    record: FileRecord,
    module_name: str,
    parent: str | None,
) -> dict[str, Any]:
    decorators = [unparse(decorator) for decorator in node.decorator_list]
    return {
        "name": node.name,
        "kind": "method" if parent else "function",
        "file": record.rel_path,
        "line": node.lineno,
        "end_line": getattr(node, "end_lineno", node.lineno),
        "parent": parent or "",
        "args": format_arguments(node.args),
        "returns": unparse(node.returns) if node.returns else "",
        "docstring": first_docline(node),
        "decorators": decorators,
        "module": module_name,
        "feature": guess_feature(record.rel_path, node.name),
        "responsibility": guess_responsibility(node.name, record.rel_path),
        "refactor_note": refactor_note_for_item(
            node.name,
            node.lineno,
            getattr(node, "end_lineno", node.lineno),
        ),
    }


def extract_fastapi_routes(
    tree: ast.Module,
    record: FileRecord,
    module_name: str,
    access_map: dict[str, str],
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            route = parse_route_decorator(decorator)
            if route is None:
                continue
            route.update(
                {
                    "function": node.name,
                    "file": record.rel_path,
                    "line": node.lineno,
                    "module": module_name,
                    "permission": detect_permission_dependency(node, access_map),
                    "request_model": detect_request_model(node),
                    "response_model": route.get("response_model") or "",
                    "feature": guess_feature(record.rel_path, route["path"]),
                    "purpose": guess_route_purpose(route["method"], route["path"], node.name),
                    "risk": route_risk_note(node, route),
                }
            )
            routes.append(route)

    return routes


def parse_route_decorator(node: ast.AST) -> dict[str, Any] | None:
    if not isinstance(node, ast.Call):
        return None

    func = node.func
    method = ""
    if isinstance(func, ast.Attribute) and func.attr in {"get", "post", "patch", "delete", "put"}:
        value_name = unparse(func.value)
        if value_name not in {"router", "app"}:
            return None
        method = func.attr.upper()
    else:
        return None

    path = ""
    if node.args and isinstance(node.args[0], ast.Constant):
        path = str(node.args[0].value)

    response_model = ""
    for keyword in node.keywords:
        if keyword.arg == "response_model":
            response_model = unparse(keyword.value)

    return {
        "method": method,
        "path": path,
        "raw_path": path,
        "response_model": response_model,
    }


def detect_permission_dependency(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    access_map: dict[str, str],
) -> str:
    for default in node.args.defaults + node.args.kw_defaults:
        if default is None:
            continue
        text = unparse(default)
        if "Depends(" not in text:
            continue
        for access_name, permission in access_map.items():
            if access_name in text:
                return permission
        if "require_platform_admin" in text:
            return "platform admin"
        if "get_current_user" in text:
            return "authenticated user"
    return ""


def detect_request_model(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    ignored = {
        "BackgroundTasks",
        "Session",
        "UploadFile",
        "WorkspaceAccess",
        "str",
        "int",
        "float",
        "bool",
    }
    for arg in node.args.args + node.args.kwonlyargs:
        if not arg.annotation:
            continue
        annotation = unparse(arg.annotation)
        if annotation in ignored:
            continue
        if arg.arg in {"db", "access", "file", "workspace_id", "current_user"}:
            continue
        if annotation.endswith("Request") or annotation.endswith("Input"):
            return annotation
    return ""


def route_risk_note(node: ast.FunctionDef | ast.AsyncFunctionDef, route: dict[str, Any]) -> str:
    length = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
    if length > 80:
        return "Large route function; consider service extraction."
    if route["path"].startswith("/workspaces") and not detect_permission_dependency(node, {}):
        return "Workspace route; verify permission dependency."
    return ""


def parse_router_prefixes() -> dict[str, str]:
    main_path = PROJECT_ROOT / "app" / "main.py"
    if not main_path.exists():
        return {}

    tree = safe_parse(main_path)
    if tree is None:
        return {}

    aliases: dict[str, str] = {}
    prefixes: dict[str, str] = {}

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = node.module

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_name(node.func) != "app.include_router":
            continue
        if not node.args:
            continue

        router_alias = unparse(node.args[0])
        module = aliases.get(router_alias)
        if not module:
            continue

        prefix = ""
        for keyword in node.keywords:
            if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
                prefix = str(keyword.value.value)
        prefixes[module] = prefix

    return prefixes


def apply_route_prefix(route: dict[str, Any], prefixes: dict[str, str]) -> dict[str, Any]:
    prefix = prefixes.get(route["module"], "")
    if prefix and not route["path"].startswith(prefix):
        route = dict(route)
        route["path"] = f"{prefix}{route['path']}"
    return route


def extract_database_models(
    tree: ast.Module,
    record: FileRecord,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    models: list[dict[str, Any]] = []
    enums: list[dict[str, Any]] = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        bases = [unparse(base) for base in node.bases]
        if any(base in {"Enum", "StrEnum"} or base.endswith("Enum") for base in bases):
            enums.append(extract_enum(node, record))
            continue

        table_name = ""
        fields: list[dict[str, str]] = []
        relationships: list[str] = []
        indexes: list[str] = []

        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == "__tablename__":
                        if isinstance(child.value, ast.Constant):
                            table_name = str(child.value.value)
                    if isinstance(target, ast.Name) and target.id == "__table_args__":
                        indexes.append(unparse(child.value))
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                field_name = child.target.id
                value_text = unparse(child.value) if child.value else ""
                annotation = unparse(child.annotation)
                field = {
                    "name": field_name,
                    "annotation": annotation,
                    "definition": value_text,
                    "nullable": "nullable=True" if "nullable=True" in value_text else "",
                    "default": "default" if "default=" in value_text else "",
                    "sensitive": sensitive_field_note(field_name),
                }
                fields.append(field)
                if "relationship(" in value_text:
                    relationships.append(field_name)

        if table_name:
            models.append(
                {
                    "name": node.name,
                    "table": table_name,
                    "file": record.rel_path,
                    "line": node.lineno,
                    "fields": fields,
                    "relationships": relationships,
                    "indexes": indexes,
                    "status_fields": [
                        field["name"]
                        for field in fields
                        if "status" in field["name"] or "deleted" in field["name"]
                    ],
                    "feature": guess_feature(record.rel_path, node.name),
                }
            )

    return models, enums


def extract_enum(node: ast.ClassDef, record: FileRecord) -> dict[str, Any]:
    values: list[str] = []
    for child in node.body:
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    values.append(f"{target.id} = {unparse(child.value)}")
    return {
        "name": node.name,
        "file": record.rel_path,
        "line": node.lineno,
        "values": values,
        "feature": guess_feature(record.rel_path, node.name),
    }


def parse_frontend_routes(files: list[FileRecord]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    route_files = [
        record
        for record in files
        if record.rel_path.startswith(("web/app/", "web/src/app/"))
        and record.path.name in {"page.tsx", "layout.tsx"}
    ]

    for record in route_files:
        root_prefix = "web/src/app/" if record.rel_path.startswith("web/src/app/") else "web/app/"
        route_dir = record.rel_path.removeprefix(root_prefix).rsplit("/", 1)[0]
        route_path = "/" if not route_dir else f"/{route_dir}"
        if record.path.name == "layout.tsx":
            route_path = f"{route_path} (layout)"

        source = read_text(record.path)
        page_component = detect_page_component(source)
        api_calls = detect_api_call_names(source)
        child_components = detect_jsx_components(source)

        routes.append(
            {
                "route": route_path,
                "file": record.rel_path,
                "component": page_component,
                "type": frontend_route_type(route_path),
                "dashboard_shell": "yes" if "DashboardShell" in source else "unknown",
                "feature": guess_feature(record.rel_path, route_path),
                "api_calls": api_calls,
                "children": child_components,
                "risk": frontend_route_risk(record, source),
            }
        )

    return routes


def parse_frontend_components(
    files: list[FileRecord],
    api_clients: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    api_names = {client["name"] for client in api_clients if client["kind"] == "function"}
    components: list[dict[str, Any]] = []

    for record in files:
        if (
            not record.rel_path.startswith("web/components/")
            or record.suffix not in TYPESCRIPT_SUFFIXES
        ):
            continue

        source = read_text(record.path)
        for component in detect_components(source):
            props_type = detect_props_type(source, component["name"])
            imports = detect_ts_imports(source)
            children = [name for name in detect_jsx_components(source) if name != component["name"]]
            api_used = sorted(name for name in api_names if re.search(rf"\b{name}\b", source))
            components.append(
                {
                    "name": component["name"],
                    "file": record.rel_path,
                    "line": component["line"],
                    "category": component_category(record.rel_path),
                    "props": props_type,
                    "imports": imports,
                    "children": children,
                    "api_functions": api_used,
                    "feature": guess_feature(record.rel_path, component["name"]),
                    "responsibility": guess_responsibility(component["name"], record.rel_path),
                    "refactor_note": frontend_component_note(record, source),
                }
            )

    return components


def parse_frontend_api_clients(files: list[FileRecord]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    for record in files:
        if not record.rel_path.startswith("web/lib/") or record.suffix not in TYPESCRIPT_SUFFIXES:
            continue

        source = read_text(record.path)
        for match in re.finditer(r"export\s+(?:type|interface)\s+([A-Za-z0-9_]+)", source):
            entries.append(
                {
                    "name": match.group(1),
                    "kind": "type",
                    "file": record.rel_path,
                    "line": line_number(source, match.start()),
                    "method": "",
                    "endpoint": "",
                    "request_type": "",
                    "response_type": "",
                    "used_by": [],
                    "feature": guess_feature(record.rel_path, match.group(1)),
                }
            )

        for match in re.finditer(
            r"export\s+(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*"
            r"\((.*?)\)\s*(?::\s*([^{]+))?\s*{",
            source,
            re.DOTALL,
        ):
            function_source = extract_braced_block(source, match.end() - 1)
            entries.append(
                {
                    "name": match.group(1),
                    "kind": "function",
                    "file": record.rel_path,
                    "line": line_number(source, match.start()),
                    "method": detect_http_method(function_source),
                    "endpoint": detect_endpoint(function_source),
                    "request_type": detect_request_type(match.group(2)),
                    "response_type": clean_type(match.group(3) or ""),
                    "used_by": [],
                    "feature": guess_feature(record.rel_path, match.group(1)),
                }
            )

    usages = detect_frontend_api_usages(files, [entry["name"] for entry in entries])
    for entry in entries:
        entry["used_by"] = usages.get(entry["name"], [])

    return entries


def parse_tests(files: list[FileRecord]) -> list[dict[str, Any]]:
    test_files: list[dict[str, Any]] = []

    for record in files:
        if not record.rel_path.startswith("tests/") or record.suffix != ".py":
            continue

        tree = safe_parse(record.path)
        if tree is None:
            continue

        source = read_text(record.path)
        tests: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "test_"
            ):
                function_source = ast.get_source_segment(source, node) or ""
                tests.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "feature": guess_feature(record.rel_path, node.name),
                        "target": guess_test_target(record.rel_path, function_source),
                        "assertions": count_assertions(function_source),
                    }
                )

        if tests:
            test_files.append(
                {
                    "file": record.rel_path,
                    "feature": guess_feature(record.rel_path),
                    "tests": sorted(tests, key=lambda item: item["line"]),
                }
            )

    return test_files


def parse_evals(files: list[FileRecord]) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    datasets: list[dict[str, Any]] = []
    scorer_functions: list[dict[str, Any]] = []

    for record in files:
        if not record.rel_path.startswith("evals/"):
            continue

        if record.suffix == ".json":
            try:
                payload = json.loads(read_text(record.path))
            except json.JSONDecodeError:
                continue
            dataset_cases = payload if isinstance(payload, list) else payload.get("cases", [])
            datasets.append(
                {
                    "file": record.rel_path,
                    "case_count": len(dataset_cases),
                    "kind": "json dataset",
                }
            )
            for index, case in enumerate(dataset_cases):
                if isinstance(case, dict):
                    cases.append(
                        {
                            "id": case.get("id", f"{record.path.stem}-{index + 1}"),
                            "file": record.rel_path,
                            "query": case.get("query") or case.get("task") or case.get("input", ""),
                            "expected": case.get("expected_answer")
                            or case.get("expected")
                            or case.get("expected_fields", ""),
                            "required_terms": case.get("required_terms", []),
                            "required_citations": case.get("required_citations", []),
                            "feature": guess_feature(record.rel_path, str(case)),
                        }
                    )
        elif record.suffix == ".py":
            tree = safe_parse(record.path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    scorer_functions.append(
                        {
                            "name": node.name,
                            "file": record.rel_path,
                            "line": node.lineno,
                            "feature": guess_feature(record.rel_path, node.name),
                        }
                    )

    return {
        "datasets": datasets,
        "cases": cases,
        "scorers": scorer_functions,
        "recommendations": [
            "Add connector retrieval evals for web, YouTube, and repo citations.",
            "Add OCR/media noisy-input eval cases when deterministic fixtures exist.",
            "Add multi-document conflict evals for review and comparison workflows.",
        ],
    }


def parse_scripts_and_devops(files: list[FileRecord]) -> dict[str, Any]:
    scripts = []
    docs = []
    migrations = []
    deployment = []

    for record in files:
        if record.rel_path.startswith("scripts/"):
            scripts.append(
                {
                    "file": record.rel_path,
                    "purpose": script_purpose(record.rel_path),
                    "line_count": record.line_count,
                }
            )
        elif record.rel_path.startswith(("docs/", "infra/")):
            docs.append(
                {
                    "file": record.rel_path,
                    "purpose": doc_purpose(record.rel_path),
                    "line_count": record.line_count,
                }
            )
        elif "migrations" in record.rel_path or record.rel_path.startswith("alembic/"):
            migrations.append(
                {
                    "file": record.rel_path,
                    "purpose": "Database migration or Alembic support file",
                    "line_count": record.line_count,
                }
            )
        elif record.rel_path.startswith(("Dockerfile", "docker-compose", ".github/")):
            deployment.append(
                {
                    "file": record.rel_path,
                    "purpose": "Deployment or CI/CD configuration",
                    "line_count": record.line_count,
                }
            )

    return {
        "scripts": scripts,
        "docs": docs,
        "migrations": migrations,
        "deployment": deployment,
        "commands": [
            "ruff format .",
            "ruff check .",
            "pytest -q",
            "python -m evals.run",
            "cd web && npm run lint && npm run build",
            "python scripts/generate_project_map.py",
            "docker compose -f docker-compose.prod.yml up --build",
        ],
    }


def build_architecture_map(
    files: list[FileRecord],
    routes: list[dict[str, Any]],
    python_items: list[dict[str, Any]],
    components: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    areas = []
    for area in SYSTEM_AREAS:
        related_files = [
            record.rel_path for record in files if area_matches_path(area, record.rel_path)
        ][:8]
        related_routes = [
            f"{route['method']} {route['path']}"
            for route in routes
            if area_matches_text(area, f"{route['file']} {route['path']} {route['function']}")
        ][:6]
        related_items = [
            item["name"]
            for item in python_items
            if area_matches_text(area, f"{item['file']} {item['name']}")
        ][:8]
        related_components = [
            component["name"]
            for component in components
            if area_matches_text(area, f"{component['file']} {component['name']}")
        ][:6]
        areas.append(
            {
                "name": area,
                "purpose": architecture_purpose(area),
                "files": related_files,
                "routes": related_routes,
                "items": related_items + related_components,
                "status": architecture_status(area, related_files, related_routes, related_items),
                "improvements": architecture_improvements(area),
            }
        )
    return areas


def build_feature_map(
    files: list[FileRecord],
    routes: list[dict[str, Any]],
    tests: list[dict[str, Any]],
    eval_map: dict[str, Any],
    components: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feature_rows = []
    for feature in FEATURES:
        backend_files = [
            record.rel_path
            for record in files
            if record.rel_path.startswith("app/") and feature_matches_path(feature, record.rel_path)
        ][:10]
        frontend_files = [
            record.rel_path
            for record in files
            if record.rel_path.startswith("web/") and feature_matches_path(feature, record.rel_path)
        ][:10]
        api_routes = [
            f"{route['method']} {route['path']}"
            for route in routes
            if route["feature"] == feature or feature_matches_text(feature, route["path"])
        ][:10]
        related_tests = [
            test_file["file"]
            for test_file in tests
            if feature_matches_path(feature, test_file["file"])
            or any(test["feature"] == feature for test in test_file["tests"])
        ][:8]
        related_components = [
            component["file"]
            for component in components
            if component["feature"] == feature or feature_matches_path(feature, component["file"])
        ][:8]
        related_evals = [
            case["id"]
            for case in eval_map["cases"]
            if case["feature"] == feature or feature_matches_text(feature, str(case))
        ][:6]
        feature_rows.append(
            {
                "name": feature,
                "what": feature_description(feature),
                "backend_files": backend_files,
                "frontend_files": unique(frontend_files + related_components),
                "api_routes": api_routes,
                "database_models": feature_models(feature),
                "workers": feature_workers(feature, files),
                "tests": related_tests,
                "evals": related_evals,
                "status": feature_status(backend_files, frontend_files, api_routes, related_tests),
                "user_value": feature_user_value(feature),
                "priority": feature_priority(feature, related_tests),
                "next": feature_next_improvement(feature),
            }
        )
    return feature_rows


def build_refactor_opportunities(
    files: list[FileRecord],
    python_items: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    frontend_components: list[dict[str, Any]],
    tests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []

    for record in files:
        if record.suffix == ".py" and record.line_count > 300:
            opportunities.append(
                opportunity(
                    "High",
                    "Large Python file",
                    record.rel_path,
                    "",
                    "Harder to review and test.",
                    "Split by service or helper boundary.",
                    "Medium",
                )
            )
        if record.suffix == ".tsx" and record.line_count > 300:
            opportunities.append(
                opportunity(
                    "High",
                    "Large TSX file",
                    record.rel_path,
                    "",
                    "Component likely owns multiple responsibilities.",
                    "Extract presentational subcomponents.",
                    "Medium",
                )
            )
        if record.rel_path.startswith("app/routes/"):
            endpoint_count = sum(1 for route in routes if route["file"] == record.rel_path)
            if endpoint_count > 5:
                opportunities.append(
                    opportunity(
                        "High",
                        "Route file has many endpoints",
                        record.rel_path,
                        str(endpoint_count),
                        "Large route modules often mix validation and business logic.",
                        "Move orchestration into services.",
                        "Medium",
                    )
                )

        if record.rel_path.startswith("web/") and record.suffix in TYPESCRIPT_SUFFIXES:
            source = read_text(record.path)
            if re.search(r"\b[a-z_]+_id\b|JSON\.stringify", source):
                opportunities.append(
                    opportunity(
                        "High",
                        "Raw ID or JSON display risk",
                        record.rel_path,
                        "",
                        "Normal users should see friendly labels, not internal data.",
                        "Check display helpers and admin-only detail disclosure.",
                        "Low",
                    )
                )
            if re.search(r"#[0-9a-fA-F]{3,8}\b|bg-(slate|gray|blue|purple)-", source):
                opportunities.append(
                    opportunity(
                        "High",
                        "Possible hardcoded color usage",
                        record.rel_path,
                        "",
                        "Dashboard should use global tokens consistently.",
                        "Prefer semantic token classes or CSS variables.",
                        "Low",
                    )
                )

    for item in python_items:
        length = item["end_line"] - item["line"] + 1
        if item["kind"] in {"function", "method"} and length > 80:
            opportunities.append(
                opportunity(
                    "High",
                    "Long function or method",
                    item["file"],
                    f"{item['name']}:{item['line']}",
                    "Long functions are harder to reason about safely.",
                    "Extract helpers around clear behavior steps.",
                    "Medium",
                )
            )
        if not item["docstring"] and item["kind"] in {"class", "dataclass", "protocol"}:
            opportunities.append(
                opportunity(
                    "Medium",
                    "Class lacks docstring",
                    item["file"],
                    item["name"],
                    "Onboarding is harder for domain objects without a first-line purpose.",
                    "Add concise class docstring where helpful.",
                    "Low",
                )
            )

    route_counts = Counter(route["function"] for route in routes)
    for name, count in route_counts.items():
        if count > 1:
            opportunities.append(
                opportunity(
                    "Medium",
                    "Duplicate route function name",
                    "",
                    name,
                    "Duplicate names make logs and traces less clear.",
                    "Rename handlers to feature-specific names.",
                    "Low",
                )
            )

    component_names = Counter(component["name"] for component in frontend_components)
    for name, count in component_names.items():
        if count > 1:
            opportunities.append(
                opportunity(
                    "Medium",
                    "Duplicate component name",
                    "",
                    name,
                    "Duplicate component names make debugging harder.",
                    "Rename or consolidate components.",
                    "Low",
                )
            )

    tested_features = {test["feature"] for test_file in tests for test in test_file["tests"]}
    for feature in FEATURES:
        if feature not in tested_features and feature not in {"Dashboard UI", "Deployment"}:
            opportunities.append(
                opportunity(
                    "Medium",
                    "Feature may be under-tested",
                    "",
                    feature,
                    "No direct test function mapped to this feature.",
                    "Add focused regression tests.",
                    "Medium",
                )
            )

    return sorted(opportunities, key=lambda item: priority_rank(item["priority"]))


def opportunity(
    priority: str,
    issue: str,
    file: str,
    item: str,
    why: str,
    action: str,
    risk: str,
) -> dict[str, str]:
    return {
        "priority": priority,
        "issue": issue,
        "file": file,
        "item": item,
        "why": why,
        "action": action,
        "risk": risk,
    }


def build_dependency_map(
    py_files: list[FileRecord],
    ts_files: list[FileRecord],
    python_imports: dict[str, list[str]],
) -> dict[str, Any]:
    imported_by = Counter(imported for imports in python_imports.values() for imported in imports)
    frontend_imports: dict[str, list[str]] = {}
    frontend_imported_by = Counter()

    for record in ts_files:
        if not record.rel_path.startswith("web/"):
            continue
        imports = detect_ts_imports(read_text(record.path))
        frontend_imports[record.rel_path] = imports
        frontend_imported_by.update(imports)

    return {
        "backend": [
            {
                "file": record.rel_path,
                "module": module_name_from_path(record.rel_path),
                "imports": python_imports.get(record.rel_path, []),
            }
            for record in py_files
            if record.rel_path.startswith("app/")
        ],
        "backend_hot": imported_by.most_common(15),
        "frontend": [
            {
                "file": file,
                "imports": imports,
            }
            for file, imports in sorted(frontend_imports.items())
        ],
        "frontend_hot": frontend_imported_by.most_common(15),
        "circular_hints": detect_circular_hints(python_imports),
    }


def build_roadmap() -> list[dict[str, str]]:
    rows = [
        (
            "UX/UI",
            "Modern dashboard shell is present.",
            "Medium",
            "Continue reducing raw technical labels on normal-user pages.",
            "Medium",
            "Frontend",
        ),
        (
            "RAG Quality",
            "Golden QA evals pass locally.",
            "Medium",
            "Add connector and OCR/media eval cases.",
            "High",
            "ML/Product",
        ),
        (
            "Answer Relevance",
            "Grounded answer path exists with citations.",
            "Medium",
            "Add reranking and confidence calibration.",
            "Medium",
            "Backend/ML",
        ),
        (
            "Citations",
            "Source drawer and metadata plumbing exist.",
            "Low",
            "Render connector-specific source labels everywhere.",
            "Medium",
            "Frontend",
        ),
        (
            "Retrieval",
            "Local retrieval and vector runtime exist.",
            "High",
            "Benchmark retrieval against more datasets.",
            "High",
            "Backend/ML",
        ),
        (
            "Persistent Vector Store",
            "Current vector storage is local/in-memory oriented.",
            "High",
            "Add durable vector database adapter.",
            "High",
            "Backend",
        ),
        (
            "Background Workers",
            "FastAPI background tasks cover media.",
            "High",
            "Move long OCR/media/repo jobs to a real queue.",
            "High",
            "Platform",
        ),
        (
            "Ingestion Connectors",
            "Web, YouTube, and repo ZIP connectors exist.",
            "Medium",
            "Add connector UI and async status UX.",
            "Medium",
            "Full stack",
        ),
        (
            "OCR/Media",
            "Adapters and fake-tested workers exist.",
            "Medium",
            "Add production worker sizing and retry policy.",
            "Medium",
            "Platform",
        ),
        (
            "Security/Tenancy",
            "Workspace permissions and admin separation exist.",
            "Medium",
            "Add security review checklist and route audit automation.",
            "High",
            "Backend",
        ),
        (
            "Billing",
            "Internal plans enforce quota.",
            "Medium",
            "Prepare Stripe-compatible subscription update path.",
            "Low",
            "Backend/Product",
        ),
        (
            "Admin/Support",
            "Metadata-first console exists.",
            "Medium",
            "Add break-glass design doc before any private content access.",
            "Medium",
            "Product/Security",
        ),
        (
            "Compliance",
            "Export and soft deletion exist.",
            "High",
            "Implement permanent deletion worker and legal hold model.",
            "High",
            "Backend",
        ),
        (
            "Observability",
            "JSON logs, request IDs, metrics, health checks exist.",
            "Medium",
            "Add job-level metrics and alert docs.",
            "Medium",
            "Platform",
        ),
        (
            "Deployment",
            "Docker Compose production baseline exists.",
            "Medium",
            "Document resource sizing for OCR/Whisper/connectors.",
            "Medium",
            "Platform",
        ),
        (
            "Testing/Evals",
            "Backend tests and evals pass.",
            "Medium",
            "Add UI integration smoke tests.",
            "Medium",
            "QA",
        ),
        (
            "Documentation",
            "Architecture/demo/ingestion docs exist.",
            "Low",
            "Keep project map regenerated per milestone.",
            "Low",
            "Tech lead",
        ),
    ]
    return [
        {
            "area": area,
            "current": current,
            "risk": risk,
            "next": next_step,
            "priority": priority,
            "owner": owner,
        }
        for area, current, risk, next_step, priority, owner in rows
    ]


def render_html(data: dict[str, Any]) -> str:
    body = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>rag-platform Project Management Map</title>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        '<div class="app-shell">',
        render_sidebar(),
        '<main class="content">',
        render_header(data),
        render_controls(),
        render_executive_summary(data),
        render_architecture(data),
        render_routes(data),
        render_python_inventory(data),
        render_database(data),
        render_ingestion(data),
        render_frontend_routes(data),
        render_components(data),
        render_api_clients(data),
        render_features(data),
        render_tests(data),
        render_evals(data),
        render_scripts(data),
        render_refactors(data),
        render_dependencies(data),
        render_roadmap(data),
        "</main>",
        "</div>",
        f"<script>{JS}</script>",
        "</body>",
        "</html>",
    ]
    return "\n".join(body)


def render_sidebar() -> str:
    sections = [
        ("summary", "Executive Summary"),
        ("architecture", "System Map"),
        ("routes", "API Routes"),
        ("python", "Backend Inventory"),
        ("database", "Database"),
        ("ingestion", "Ingestion"),
        ("frontend-routes", "Frontend Routes"),
        ("components", "Components"),
        ("api-clients", "API Clients"),
        ("features", "Feature Map"),
        ("tests", "Tests"),
        ("evals", "Evals"),
        ("scripts", "Scripts/DevOps"),
        ("refactors", "Refactors"),
        ("dependencies", "Dependencies"),
        ("roadmap", "Roadmap"),
    ]
    links = "\n".join(
        f'<a href="#{section_id}">{escape(label)}</a>' for section_id, label in sections
    )
    return f"""
<aside class="sidebar">
  <div class="brand">rag-platform</div>
  <p class="sidebar-subtitle">Project Management Map</p>
  <nav>{links}</nav>
</aside>
"""


def render_header(data: dict[str, Any]) -> str:
    summary = data["summary"]
    return f"""
<section class="hero">
  <div>
    <p class="eyebrow">Generated {escape(summary["generated_at"])}</p>
    <h1>Interactive Project Management Map</h1>
    <p class="hero-text">
      A searchable, self-contained dashboard for architecture review, onboarding,
      refactor planning, and feature planning.
    </p>
  </div>
  <div class="hero-actions">
    <button type="button" onclick="expandAll()">Expand all</button>
    <button type="button" onclick="collapseAll()">Collapse all</button>
  </div>
</section>
"""


def render_controls() -> str:
    categories = [
        "",
        "backend",
        "frontend",
        "route",
        "component",
        "model",
        "test",
        "eval",
        "script",
        "risk",
    ]
    options = "\n".join(
        f'<option value="{escape(category)}">{"All categories" if not category else escape(category.title())}</option>'
        for category in categories
    )
    return f"""
<section class="toolbar">
  <input id="globalSearch" type="search" placeholder="Search files, routes, functions, features...">
  <select id="categoryFilter">{options}</select>
</section>
"""


def render_executive_summary(data: dict[str, Any]) -> str:
    summary = data["summary"]
    cards = [
        ("Total files", summary["total_files"]),
        ("Python files", summary["python_files"]),
        ("TS/TSX files", summary["typescript_files"]),
        ("Backend functions", summary["backend_functions"]),
        ("Backend classes", summary["backend_classes"]),
        ("Frontend components", summary["frontend_components"]),
        ("Frontend routes", summary["frontend_routes"]),
        ("FastAPI routes", summary["fastapi_routes"]),
        ("DB models", summary["database_models"]),
        ("Tests", summary["tests"]),
        ("Eval cases", summary["eval_cases"]),
        ("Scripts", summary["scripts"]),
    ]
    largest_rows = "".join(
        table_row(
            [
                copy_path(record.rel_path),
                str(record.line_count),
                badge(record.category),
            ],
            category="risk" if record.line_count > 300 else "backend",
        )
        for record in summary["largest_files"]
    )
    hotspot_rows = "".join(
        table_row(
            [
                badge(item["priority"]),
                escape(item["issue"]),
                copy_path(item["file"]) if item["file"] else escape(item["item"]),
                escape(item["action"]),
            ],
            category="risk",
        )
        for item in summary["hotspots"]
    )
    return f"""
<section id="summary" class="section">
  <div class="section-heading">
    <h2>Executive Summary</h2>
    <p>Project-wide scan totals, large files, and likely refactor hotspots.</p>
  </div>
  <div class="stat-grid">{"".join(stat_card(label, value) for label, value in cards)}</div>
  <div class="two-col">
    {table_card("Largest Files", ["File", "Lines", "Area"], largest_rows)}
    {table_card("Likely Refactor Hotspots", ["Priority", "Issue", "Item", "Suggested Action"], hotspot_rows)}
  </div>
</section>
"""


def render_architecture(data: dict[str, Any]) -> str:
    cards = []
    for area in data["architecture"]:
        files = inline_list(area["files"])
        routes = inline_list(area["routes"])
        items = inline_list(area["items"])
        cards.append(
            f"""
<article class="arch-card searchable" data-category="backend frontend" data-search="{search_text(area)}">
  <div class="card-top"><h3>{escape(area["name"])}</h3>{badge(area["status"])}</div>
  <p>{escape(area["purpose"])}</p>
  <dl>
    <dt>Important files</dt><dd>{files}</dd>
    <dt>Related routes</dt><dd>{routes}</dd>
    <dt>Functions/classes/components</dt><dd>{items}</dd>
    <dt>Improvement ideas</dt><dd>{escape(area["improvements"])}</dd>
  </dl>
</article>
"""
        )
    return section(
        "architecture",
        "System Architecture Overview",
        "Major product and platform areas.",
        f'<div class="arch-grid">{"".join(cards)}</div>',
    )


def render_routes(data: dict[str, Any]) -> str:
    routes_by_file = group_by(data["routes"], "file")
    groups = []
    for file, routes in routes_by_file.items():
        rows = "".join(
            table_row(
                [
                    badge(route["method"]),
                    escape(route["path"]),
                    escape(route["function"]),
                    str(route["line"]),
                    escape(route["permission"] or "public/internal"),
                    escape(route["request_model"] or "-"),
                    escape(route["response_model"] or "-"),
                    badge(route["feature"]),
                    escape(route["purpose"]),
                    escape(route["risk"] or "-"),
                ],
                category="route backend",
                search=route,
            )
            for route in routes
        )
        groups.append(
            details_block(
                f"{file} ({len(routes)} routes)",
                table(
                    [
                        "Method",
                        "Path",
                        "Function",
                        "Line",
                        "Permission",
                        "Request",
                        "Response",
                        "Feature",
                        "Purpose",
                        "Risk Notes",
                    ],
                    rows,
                ),
                open_by_default=False,
            )
        )

    summary_rows = route_summary_rows(data["routes"])
    content = table_card(
        "Route Summary By Feature",
        ["Feature", "Routes"],
        summary_rows,
    ) + "".join(groups)
    return section(
        "routes",
        "Backend API Route Inventory",
        "FastAPI endpoints grouped by source file.",
        content,
    )


def render_python_inventory(data: dict[str, Any]) -> str:
    groups = group_by(data["python_items"], lambda item: module_folder(item["file"]))
    blocks = []
    for folder, items in groups.items():
        rows = "".join(
            table_row(
                [
                    escape(item["name"]),
                    badge(item["kind"]),
                    copy_path(item["file"]),
                    str(item["line"]),
                    escape(item["parent"] or "-"),
                    escape(item["args"]),
                    escape(item["returns"] or "-"),
                    escape(item["docstring"] or "-"),
                    escape(", ".join(item["decorators"]) or "-"),
                    badge(item["feature"]),
                    escape(item["responsibility"]),
                    escape(item["refactor_note"] or "-"),
                ],
                category="backend",
                search=item,
            )
            for item in items
        )
        blocks.append(
            details_block(
                f"{folder} ({len(items)} items)",
                table(
                    [
                        "Name",
                        "Kind",
                        "File",
                        "Line",
                        "Parent",
                        "Args",
                        "Returns",
                        "Docstring",
                        "Decorators",
                        "Feature",
                        "Responsibility",
                        "Refactor Note",
                    ],
                    rows,
                ),
            )
        )
    return section(
        "python",
        "Backend Function and Class Inventory",
        "Every parsed function, method, and class under app/.",
        "".join(blocks),
    )


def render_database(data: dict[str, Any]) -> str:
    model_blocks = []
    for model in data["db_models"]:
        field_rows = "".join(
            table_row(
                [
                    escape(field["name"]),
                    escape(field["annotation"]),
                    escape(field["nullable"] or "-"),
                    escape(field["default"] or "-"),
                    escape(field["sensitive"] or "-"),
                    escape(shorten(field["definition"], 140)),
                ],
                category="model backend",
                search=field,
            )
            for field in model["fields"]
        )
        model_blocks.append(
            details_block(
                f"{model['name']} -> {model['table']}",
                f"""
<p>{copy_path(model["file"])} line {model["line"]} {badge(model["feature"])}</p>
<p><strong>Relationships:</strong> {inline_list(model["relationships"])}</p>
<p><strong>Status/lifecycle fields:</strong> {inline_list(model["status_fields"])}</p>
{table(["Field", "Type", "Nullable", "Default", "Sensitive", "Definition"], field_rows)}
""",
            )
        )

    enum_rows = "".join(
        table_row(
            [
                escape(enum["name"]),
                copy_path(enum["file"]),
                str(enum["line"]),
                escape(", ".join(enum["values"])),
                badge(enum["feature"]),
            ],
            category="model backend",
            search=enum,
        )
        for enum in data["enums"]
    )
    domain_map = """
<div class="flow">
  <span>User</span><span>Workspace</span><span>WorkspaceMember</span>
  <span>Document</span><span>DocumentFile</span><span>IngestionJob</span>
  <span>DocumentChunk</span><span>ConversationMessage</span><span>Citation</span>
  <span>ReviewItem</span><span>AuditEvent</span><span>UsageEvent</span>
  <span>WorkspaceSubscription</span>
</div>
"""
    content = (
        domain_map
        + "".join(model_blocks)
        + table_card(
            "Enums",
            ["Enum", "File", "Line", "Values", "Feature"],
            enum_rows,
        )
    )
    return section(
        "database",
        "Database Model Inventory",
        "SQLAlchemy models, relationships, lifecycle fields, and enums.",
        content,
    )


def render_ingestion(data: dict[str, Any]) -> str:
    ingestion_modules = [
        "text",
        "pdf",
        "office",
        "tables",
        "ocr",
        "transcribe",
        "web",
        "youtube",
        "repos",
        "loader",
        "types",
    ]
    rows = ""
    for module in ingestion_modules:
        module_items = [
            item
            for item in data["python_items"]
            if item["file"].startswith(f"app/ingestion/{module}.py")
        ]
        tests = [
            test_file["file"]
            for test_file in data["tests"]
            if module in test_file["file"]
            or any(module in test["name"] for test in test_file["tests"])
        ]
        rows += table_row(
            [
                badge(module),
                ingestion_input(module),
                "ExtractedTextBlock with source_metadata",
                ingestion_metadata(module),
                ingestion_citation(module),
                inline_list(tests[:5]),
                ingestion_limitations(module),
            ],
            category="backend",
            search={"module": module, "items": module_items},
        )
    flow = """
<div class="pipeline">
  <span>Upload / Connector</span><span>Loader</span><span>ExtractedTextBlock</span>
  <span>Chunker</span><span>Embedder</span><span>Vector Store</span>
  <span>Retriever</span><span>Answer Generator</span><span>Citations</span>
</div>
"""
    return section(
        "ingestion",
        "Ingestion Pipeline Map",
        "All supported ingestion sources normalize into ExtractedTextBlock records.",
        flow
        + table(
            [
                "Module",
                "Inputs",
                "Output",
                "Key Metadata",
                "Citation Metadata",
                "Tests",
                "Known Limitation",
            ],
            rows,
        ),
    )


def render_frontend_routes(data: dict[str, Any]) -> str:
    rows = "".join(
        table_row(
            [
                escape(route["route"]),
                copy_path(route["file"]),
                escape(route["component"] or "-"),
                badge(route["type"]),
                escape(route["dashboard_shell"]),
                badge(route["feature"]),
                inline_list(route["api_calls"]),
                inline_list(route["children"][:8]),
                escape(route["risk"] or "-"),
            ],
            category="frontend",
            search=route,
        )
        for route in data["frontend_routes"]
    )
    return section(
        "frontend-routes",
        "Frontend Route Inventory",
        "Next.js route files detected under web app roots.",
        table(
            [
                "Route",
                "File",
                "Page Component",
                "Type",
                "Dashboard Shell",
                "Feature",
                "API Calls",
                "Child Components",
                "Risk Notes",
            ],
            rows,
        ),
    )


def render_components(data: dict[str, Any]) -> str:
    groups = group_by(data["frontend_components"], "category")
    blocks = []
    for category, components in groups.items():
        rows = "".join(
            table_row(
                [
                    escape(component["name"]),
                    copy_path(component["file"]),
                    str(component["line"]),
                    escape(component["props"] or "-"),
                    inline_list(component["imports"][:6]),
                    inline_list(component["children"][:8]),
                    inline_list(component["api_functions"]),
                    badge(component["feature"]),
                    escape(component["responsibility"]),
                    escape(component["refactor_note"] or "-"),
                ],
                category="component frontend",
                search=component,
            )
            for component in components
        )
        blocks.append(
            details_block(
                f"{category} ({len(components)} components)",
                table(
                    [
                        "Component",
                        "File",
                        "Line",
                        "Props",
                        "Imports",
                        "Children",
                        "API Functions",
                        "Feature",
                        "Responsibility",
                        "Refactor Note",
                    ],
                    rows,
                ),
            )
        )
    return section(
        "components",
        "Frontend Component Inventory",
        "Every detected React component under web/components/.",
        "".join(blocks),
    )


def render_api_clients(data: dict[str, Any]) -> str:
    rows = "".join(
        table_row(
            [
                escape(client["name"]),
                badge(client["kind"]),
                escape(client["method"] or "-"),
                escape(client["endpoint"] or "-"),
                escape(client["request_type"] or "-"),
                escape(client["response_type"] or "-"),
                copy_path(client["file"]),
                inline_list(client["used_by"][:5]),
                badge(client["feature"]),
            ],
            category="frontend",
            search=client,
        )
        for client in data["api_clients"]
    )
    return section(
        "api-clients",
        "Frontend API Client Inventory",
        "Exported web/lib helpers, types, and API functions.",
        table(
            [
                "Function/Type",
                "Kind",
                "HTTP",
                "Endpoint",
                "Request Type",
                "Response Type",
                "File",
                "Used By",
                "Feature",
            ],
            rows,
        ),
    )


def render_features(data: dict[str, Any]) -> str:
    rows = "".join(
        table_row(
            [
                escape(feature["name"]),
                escape(feature["what"]),
                inline_list(feature["backend_files"]),
                inline_list(feature["frontend_files"]),
                inline_list(feature["api_routes"]),
                inline_list(feature["database_models"]),
                inline_list(feature["workers"]),
                inline_list(feature["tests"]),
                inline_list(feature["evals"]),
                badge(feature["status"]),
                escape(feature["user_value"]),
                badge(feature["priority"]),
                escape(feature["next"]),
            ],
            category="backend frontend",
            search=feature,
        )
        for feature in data["features"]
    )
    return section(
        "features",
        "Feature Map",
        "Product features mapped to code, routes, tests, and next improvements.",
        table(
            [
                "Feature",
                "What It Does",
                "Backend Files",
                "Frontend Files",
                "API Routes",
                "Database Models",
                "Workers",
                "Tests",
                "Evals",
                "Status",
                "User Value",
                "Priority",
                "Next Improvement",
            ],
            rows,
        ),
    )


def render_tests(data: dict[str, Any]) -> str:
    tested_features = Counter(test["feature"] for file in data["tests"] for test in file["tests"])
    coverage_rows = ""
    for feature in FEATURES:
        count = tested_features.get(feature, 0)
        status = "Covered" if count >= 2 else "Partial" if count == 1 else "Needs Tests"
        coverage_rows += table_row(
            [escape(feature), str(count), badge(status), test_recommendation(feature, status)],
            category="test",
        )

    file_blocks = []
    for test_file in data["tests"]:
        rows = "".join(
            table_row(
                [
                    escape(test["name"]),
                    str(test["line"]),
                    badge(test["feature"]),
                    escape(test["target"]),
                    str(test["assertions"]),
                ],
                category="test",
                search=test,
            )
            for test in test_file["tests"]
        )
        file_blocks.append(
            details_block(
                f"{test_file['file']} ({len(test_file['tests'])} tests)",
                table(["Test", "Line", "Feature", "Route/Module", "Assertions"], rows),
            )
        )
    return section(
        "tests",
        "Test Coverage Map",
        "All test files and test functions with feature coverage hints.",
        table_card(
            "Coverage Summary", ["Feature", "Tests", "Status", "Recommendation"], coverage_rows
        )
        + "".join(file_blocks),
    )


def render_evals(data: dict[str, Any]) -> str:
    dataset_rows = "".join(
        table_row(
            [copy_path(dataset["file"]), str(dataset["case_count"]), escape(dataset["kind"])],
            category="eval",
            search=dataset,
        )
        for dataset in data["eval_map"]["datasets"]
    )
    case_rows = "".join(
        table_row(
            [
                escape(str(case["id"])),
                copy_path(case["file"]),
                escape(shorten(str(case["query"]), 120)),
                escape(shorten(str(case["expected"]), 120)),
                escape(", ".join(map(str, case["required_terms"]))),
                escape(", ".join(map(str, case["required_citations"]))),
                badge(case["feature"]),
            ],
            category="eval",
            search=case,
        )
        for case in data["eval_map"]["cases"]
    )
    scorer_rows = "".join(
        table_row(
            [
                escape(scorer["name"]),
                copy_path(scorer["file"]),
                str(scorer["line"]),
                badge(scorer["feature"]),
            ],
            category="eval",
            search=scorer,
        )
        for scorer in data["eval_map"]["scorers"]
    )
    recommendations = "".join(
        f"<li>{escape(item)}</li>" for item in data["eval_map"]["recommendations"]
    )
    content = (
        table_card("Datasets", ["File", "Cases", "Kind"], dataset_rows)
        + table_card(
            "Eval Cases",
            ["ID", "File", "Query/Task", "Expected", "Terms", "Citations", "Feature"],
            case_rows,
        )
        + table_card(
            "Scorers and Runner Functions", ["Function", "File", "Line", "Feature"], scorer_rows
        )
        + f"<div class='panel'><h3>Recommended Future Eval Cases</h3><ul>{recommendations}</ul></div>"
    )
    return section(
        "evals", "Eval Map", "Datasets, cases, scorer functions, and behaviors protected.", content
    )


def render_scripts(data: dict[str, Any]) -> str:
    script_rows = "".join(
        table_row(
            [copy_path(item["file"]), escape(item["purpose"]), str(item["line_count"])],
            category="script",
            search=item,
        )
        for item in data["scripts"]["scripts"]
    )
    docs_rows = "".join(
        table_row(
            [copy_path(item["file"]), escape(item["purpose"]), str(item["line_count"])],
            category="script",
            search=item,
        )
        for item in data["scripts"]["docs"]
    )
    migration_rows = "".join(
        table_row(
            [copy_path(item["file"]), escape(item["purpose"]), str(item["line_count"])],
            category="script",
            search=item,
        )
        for item in data["scripts"]["migrations"]
    )
    deployment_rows = "".join(
        table_row(
            [copy_path(item["file"]), escape(item["purpose"]), str(item["line_count"])],
            category="script",
            search=item,
        )
        for item in data["scripts"]["deployment"]
    )
    command_list = "".join(
        f"<li><code>{escape(command)}</code></li>" for command in data["scripts"]["commands"]
    )
    content = (
        table_card("Scripts", ["File", "Purpose", "Lines"], script_rows)
        + table_card("Docs", ["File", "Purpose", "Lines"], docs_rows)
        + table_card("Migrations", ["File", "Purpose", "Lines"], migration_rows)
        + table_card("Deployment Files", ["File", "Purpose", "Lines"], deployment_rows)
        + f"<div class='panel'><h3>Quality and Operations Commands</h3><ul>{command_list}</ul></div>"
    )
    return section(
        "scripts",
        "Script and DevOps Inventory",
        "Scripts, docs, migrations, deployment files, and commands.",
        content,
    )


def render_refactors(data: dict[str, Any]) -> str:
    groups = group_by(data["opportunities"], "priority")
    blocks = []
    for priority in ["High", "Medium", "Low"]:
        rows = "".join(
            table_row(
                [
                    badge(item["priority"]),
                    escape(item["issue"]),
                    copy_path(item["file"]) if item["file"] else "-",
                    escape(item["item"] or "-"),
                    escape(item["why"]),
                    escape(item["action"]),
                    badge(item["risk"]),
                ],
                category="risk",
                search=item,
            )
            for item in groups.get(priority, [])
        )
        blocks.append(
            details_block(
                f"{priority} Priority ({len(groups.get(priority, []))})",
                table(
                    [
                        "Priority",
                        "Issue",
                        "File",
                        "Line/Item",
                        "Why It Matters",
                        "Suggested Action",
                        "Risk",
                    ],
                    rows,
                ),
                open_by_default=priority == "High",
            )
        )
    return section(
        "refactors",
        "Refactor Opportunity Dashboard",
        "Heuristic risk and refactor candidates detected by the scanner.",
        "".join(blocks),
    )


def render_dependencies(data: dict[str, Any]) -> str:
    backend_rows = "".join(
        table_row(
            [copy_path(item["file"]), escape(item["module"]), inline_list(item["imports"])],
            category="backend",
            search=item,
        )
        for item in data["dependencies"]["backend"]
    )
    backend_hot_rows = "".join(
        table_row([escape(name), str(count)], category="backend")
        for name, count in data["dependencies"]["backend_hot"]
    )
    frontend_rows = "".join(
        table_row(
            [copy_path(item["file"]), inline_list(item["imports"])],
            category="frontend",
            search=item,
        )
        for item in data["dependencies"]["frontend"]
    )
    frontend_hot_rows = "".join(
        table_row([escape(name), str(count)], category="frontend")
        for name, count in data["dependencies"]["frontend_hot"]
    )
    circular_rows = "".join(
        table_row([escape(a), escape(b)], category="risk")
        for a, b in data["dependencies"]["circular_hints"]
    )
    content = (
        table_card("Backend Local Imports", ["File", "Module", "Imports"], backend_rows)
        + table_card(
            "Backend Frequently Imported Modules", ["Module", "Import Count"], backend_hot_rows
        )
        + table_card("Frontend Imports", ["File", "Imports"], frontend_rows)
        + table_card(
            "Frontend Frequently Imported Paths", ["Import", "Import Count"], frontend_hot_rows
        )
        + table_card("Possible Circular Dependency Hints", ["Module A", "Module B"], circular_rows)
    )
    return section(
        "dependencies",
        "Module Dependency Map",
        "Readable import tables and possible circular dependency hints.",
        content,
    )


def render_roadmap(data: dict[str, Any]) -> str:
    rows = "".join(
        table_row(
            [
                escape(row["area"]),
                escape(row["current"]),
                badge(row["risk"]),
                escape(row["next"]),
                badge(row["priority"]),
                escape(row["owner"]),
            ],
            category="risk",
            search=row,
        )
        for row in data["roadmap"]
    )
    return section(
        "roadmap",
        "Management Roadmap View",
        "Future planning table for product, platform, and quality work.",
        table(
            [
                "Area",
                "Current State",
                "Risk",
                "Next Improvement",
                "Suggested Priority",
                "Owner Role",
            ],
            rows,
        ),
    )


def section(section_id: str, title: str, description: str, content: str) -> str:
    return f"""
<section id="{section_id}" class="section">
  <div class="section-heading">
    <h2>{escape(title)}</h2>
    <p>{escape(description)}</p>
  </div>
  {content}
</section>
"""


def table(headers: list[str], rows: str) -> str:
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    return f"""
<div class="table-wrap">
  <table>
    <thead><tr>{head}</tr></thead>
    <tbody>{rows or '<tr><td colspan="99">No items detected.</td></tr>'}</tbody>
  </table>
</div>
"""


def table_card(title: str, headers: list[str], rows: str) -> str:
    return f"""
<div class="panel">
  <h3>{escape(title)}</h3>
  {table(headers, rows)}
</div>
"""


def table_row(cells: list[str], category: str = "", search: Any | None = None) -> str:
    cell_html = "".join(f"<td>{cell}</td>" for cell in cells)
    search_value = escape(search_text(search or cells), quote=True)
    return f'<tr class="searchable" data-category="{escape(category)}" data-search="{search_value}">{cell_html}</tr>'


def details_block(title: str, content: str, open_by_default: bool = True) -> str:
    open_attr = " open" if open_by_default else ""
    return f"""
<details class="panel module-card"{open_attr}>
  <summary>{escape(title)}</summary>
  {content}
</details>
"""


def stat_card(label: str, value: Any) -> str:
    return f"""
<article class="stat-card searchable" data-category="summary" data-search="{escape(str(label))} {escape(str(value))}">
  <span>{escape(label)}</span>
  <strong>{escape(str(value))}</strong>
</article>
"""


def badge(label: Any) -> str:
    value = str(label or "unknown")
    key = value.lower().replace(" ", "-").replace("/", "-")
    return f'<span class="badge badge-{escape(key)}">{escape(value)}</span>'


def copy_path(path: str) -> str:
    if not path:
        return "-"
    safe_path = escape(path)
    return (
        f'<span class="path"><code>{safe_path}</code>'
        f'<button type="button" class="copy" data-copy="{safe_path}">Copy</button></span>'
    )


def inline_list(values: list[Any]) -> str:
    cleaned = [str(value) for value in values if str(value)]
    if not cleaned:
        return "-"
    return "<br>".join(escape(value) for value in cleaned)


def group_by(items: list[dict[str, Any]], key: str | Any) -> dict[Any, list[dict[str, Any]]]:
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        group_key = key(item) if callable(key) else item.get(key, "unknown")
        groups[group_key].append(item)
    return dict(sorted(groups.items(), key=lambda pair: str(pair[0])))


def safe_parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(read_text(path))
    except SyntaxError:
        return None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = call_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return unparse(node)


def first_docline(node: ast.AST) -> str:
    docstring = ast.get_docstring(node)
    if not docstring:
        return ""
    return docstring.strip().splitlines()[0]


def format_arguments(args: ast.arguments) -> str:
    names = [arg.arg for arg in args.posonlyargs + args.args]
    names.extend(f"*{arg.arg}" for arg in args.vararg or [])
    names.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg:
        names.append(f"**{args.kwarg.arg}")
    return ", ".join(names)


def line_number(source: str, position: int) -> int:
    return source.count("\n", 0, position) + 1


def clean_type(value: str) -> str:
    return " ".join(value.replace("\n", " ").split()).strip()


def extract_braced_block(source: str, start_index: int) -> str:
    depth = 0
    for index in range(start_index, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start_index : index + 1]
    return source[start_index:]


def detect_http_method(source: str) -> str:
    match = re.search(r"method:\s*[\"']([A-Z]+)[\"']", source)
    if match:
        return match.group(1)
    if "apiRequest" in source or "fetch(" in source:
        return "GET"
    return ""


def detect_endpoint(source: str) -> str:
    patterns = [
        r"apiRequest(?:<[^>]+>)?\(\s*`([^`]+)`",
        r"apiRequest(?:<[^>]+>)?\(\s*[\"']([^\"']+)[\"']",
        r"fetch\(\s*`([^`]+)`",
        r"fetch\(\s*[\"']([^\"']+)[\"']",
    ]
    for pattern in patterns:
        match = re.search(pattern, source)
        if match:
            return shorten(match.group(1), 120)
    return ""


def detect_request_type(arguments: str) -> str:
    match = re.search(r":\s*([A-Za-z0-9_<>| \[\]]+)", arguments)
    return clean_type(match.group(1)) if match else ""


def detect_frontend_api_usages(files: list[FileRecord], names: list[str]) -> dict[str, list[str]]:
    usages: dict[str, list[str]] = defaultdict(list)
    target_files = [
        record
        for record in files
        if record.rel_path.startswith(("web/components/", "web/src/app/", "web/app/"))
        and record.suffix in TYPESCRIPT_SUFFIXES
    ]
    for record in target_files:
        source = read_text(record.path)
        for name in names:
            if re.search(rf"\b{name}\b", source):
                usages[name].append(record.rel_path)
    return dict(usages)


def detect_page_component(source: str) -> str:
    for pattern in [
        r"export\s+default\s+function\s+([A-Za-z0-9_]+)",
        r"function\s+([A-Za-z0-9_]+)\s*\(",
    ]:
        match = re.search(pattern, source)
        if match:
            return match.group(1)
    return ""


def detect_components(source: str) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    patterns = [
        r"export\s+function\s+([A-Z][A-Za-z0-9_]*)\s*\(",
        r"function\s+([A-Z][A-Za-z0-9_]*)\s*\(",
        r"export\s+default\s+function\s+([A-Z][A-Za-z0-9_]*)\s*\(",
        r"(?:export\s+)?const\s+([A-Z][A-Za-z0-9_]*)\s*=",
    ]
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            components.append({"name": name, "line": line_number(source, match.start())})
    return sorted(components, key=lambda item: item["line"])


def detect_props_type(source: str, component_name: str) -> str:
    for candidate in [f"{component_name}Props", "Props"]:
        if re.search(rf"(?:type|interface)\s+{candidate}\b", source):
            return candidate
    match = re.search(rf"function\s+{component_name}\s*\(([^)]*)\)", source, re.DOTALL)
    if match and ":" in match.group(1):
        return clean_type(match.group(1).split(":", 1)[1])
    return ""


def detect_ts_imports(source: str) -> list[str]:
    imports = []
    for match in re.finditer(r"from\s+[\"']([^\"']+)[\"']", source):
        imports.append(match.group(1))
    for match in re.finditer(r"import\s+[\"']([^\"']+)[\"']", source):
        imports.append(match.group(1))
    return sorted(set(imports))


def detect_jsx_components(source: str) -> list[str]:
    names = re.findall(r"<([A-Z][A-Za-z0-9_]*)\b", source)
    return sorted(set(names))


def detect_api_call_names(source: str) -> list[str]:
    names = re.findall(
        r"\b([a-z][A-Za-z0-9_]*(?:Workspace|Document|Billing|Admin|Usage|Review|Query|Data)[A-Za-z0-9_]*)\s*\(",
        source,
    )
    return sorted(set(names))


def frontend_route_type(route_path: str) -> str:
    if route_path in {"/login", "/register", "/"}:
        return "public"
    if route_path.startswith("/admin"):
        return "admin"
    return "user"


def component_category(path: str) -> str:
    parts = path.split("/")
    if len(parts) >= 3:
        return parts[2]
    return "component"


def category_for_path(rel_path: str) -> str:
    if rel_path.startswith("app/"):
        return "backend"
    if rel_path.startswith("web/"):
        return "frontend"
    if rel_path.startswith("tests/"):
        return "test"
    if rel_path.startswith("evals/"):
        return "eval"
    if rel_path.startswith(("scripts/", "infra/", "docs/", "db/migrations")):
        return "script"
    return "other"


def module_folder(path: str) -> str:
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] == "app":
        return parts[1]
    return parts[0]


def guess_feature(path: str, text: str = "") -> str:
    combined = f"{path} {text}".lower()
    for feature in FEATURES:
        if feature_matches_text(feature, combined):
            return feature
    return "Dashboard UI" if path.startswith("web/") else "Document Upload"


def feature_matches_path(feature: str, path: str) -> bool:
    return feature_matches_text(feature, path)


def feature_matches_text(feature: str, text: str) -> bool:
    text = text.lower()
    keywords = {
        "Authentication": ["auth", "login", "register", "jwt", "password"],
        "Workspace Tenancy": ["tenant", "workspace", "membership"],
        "Document Upload": ["upload", "document", "documents"],
        "Text/PDF Ingestion": ["pdf", "text", "markdown"],
        "Office/Table Ingestion": ["office", "docx", "pptx", "csv", "xlsx", "table"],
        "OCR Ingestion": ["ocr", "tesseract", "image"],
        "Media Transcription": ["media", "transcribe", "whisper", "ffmpeg", "audio", "video"],
        "Web Connector": ["web.py", "web connector", "url", "fetch"],
        "YouTube Connector": ["youtube"],
        "Repo ZIP Connector": ["repo", "zip"],
        "Chunking": ["chunk"],
        "Embeddings": ["embed"],
        "Vector Store": ["vector"],
        "Retrieval": ["retrieval", "retriever", "rerank"],
        "Grounded Answers": ["answer", "grounded", "llm", "prompt"],
        "Citations": ["citation"],
        "Source Drawer": ["source-drawer", "source drawer"],
        "Structured Extraction": ["extraction", "extract"],
        "Document Comparison": ["compare", "comparison", "report"],
        "Agent Tools": ["agent", "orchestrator", "tool"],
        "Review Workflow": ["review"],
        "Usage Metering": ["usage", "meter"],
        "Billing Plans": ["billing", "plan", "subscription"],
        "Admin Console": ["admin", "support"],
        "Audit Events": ["audit"],
        "Compliance Export/Delete": ["compliance", "delete", "deletion", "export"],
        "Observability": ["observability", "metrics", "health", "ready", "logging", "request_id"],
        "Deployment": ["docker", "deploy", "infra"],
        "Evaluation Suite": ["eval"],
        "Dashboard UI": ["dashboard", "component", "page", "layout", "theme"],
    }
    return any(keyword in text for keyword in keywords.get(feature, []))


def guess_responsibility(name: str, path: str) -> str:
    lowered = f"{name} {path}".lower()
    if "route" in path or path.startswith("app/routes"):
        return "HTTP request handling and response shaping."
    if "repository" in lowered or "repositories" in path:
        return "Database access and persistence helper."
    if "worker" in lowered or "workers" in path:
        return "Background or worker-style processing."
    if "ingestion" in path:
        return "Normalize source content into extracted text blocks."
    if "component" in path or path.startswith("web/components"):
        return "Render reusable frontend UI."
    if "test_" in path:
        return "Regression test coverage."
    return "Project module behavior."


def refactor_note_for_item(name: str, line: int, end_line: int) -> str:
    del name
    length = end_line - line + 1
    if length > 80:
        return "Long item; inspect for extractable helper logic."
    return ""


def sensitive_field_note(field_name: str) -> str:
    lowered = field_name.lower()
    if any(token in lowered for token in ["password", "secret", "token", "hash"]):
        return "Sensitive"
    if any(token in lowered for token in ["content", "text", "payload"]):
        return "Private content possible"
    return ""


def guess_route_purpose(method: str, path: str, function_name: str) -> str:
    if method == "GET" and path.endswith("/health"):
        return "Health check."
    if "query" in path:
        return "Run or stream grounded query."
    if "upload" in path:
        return "Upload and ingest a document."
    if "connectors" in path:
        return "Ingest external connector source."
    if method == "GET":
        return "Read or list resource."
    if method == "POST":
        return "Create or trigger workflow."
    if method == "PATCH":
        return "Update resource."
    if method == "DELETE":
        return "Delete or deactivate resource."
    return function_name.replace("_", " ").capitalize()


def frontend_route_risk(record: FileRecord, source: str) -> str:
    if record.line_count > 250:
        return "Large page file; consider extracting sections."
    if "loading" not in source.lower() or "error" not in source.lower():
        return "Check loading/error states."
    return ""


def frontend_component_note(record: FileRecord, source: str) -> str:
    if record.line_count > 250:
        return "Large component; consider subcomponents."
    if "JSON.stringify" in source:
        return "Raw JSON display risk."
    return ""


def script_purpose(path: str) -> str:
    name = Path(path).name
    if "check" in name:
        return "Quality gate runner"
    if "smoke" in name:
        return "Smoke test helper"
    if "admin" in name:
        return "Admin account bootstrap"
    if "project_map" in name:
        return "Generate this project management map"
    return "Project utility script"


def doc_purpose(path: str) -> str:
    lowered = path.lower()
    if "architecture" in lowered:
        return "Architecture explanation"
    if "demo" in lowered:
        return "Demo script"
    if "ingestion" in lowered:
        return "Ingestion documentation"
    if "deploy" in lowered:
        return "Deployment guide"
    if "compliance" in lowered:
        return "Compliance posture"
    return "Project documentation"


def guess_test_target(path: str, source: str) -> str:
    for match in re.finditer(r'"/api/v1/([^"]+)"', source):
        return f"/api/v1/{match.group(1)}"
    if "load_document" in source:
        return "app.ingestion.loader"
    return path.replace("tests/test_", "").replace(".py", "")


def count_assertions(source: str) -> int:
    return source.count("assert ") + source.count("with pytest.raises")


def architecture_purpose(area: str) -> str:
    return {
        "Frontend Dashboard": "Workspace-facing UI for documents, chat, usage, billing, and settings.",
        "Frontend Admin Console": "Operator UI for metadata-first support and audit review.",
        "Frontend API Client": "Typed browser calls into FastAPI endpoints.",
        "FastAPI Routes": "HTTP boundary for auth, documents, query, billing, admin, and compliance.",
        "Auth / Tenancy": "JWT identity and workspace permission enforcement.",
        "Document Upload": "File persistence plus ingestion job creation.",
        "Ingestion Loaders": "Routes file/source types into normalized text blocks.",
        "Office / Table Ingestion": "Extracts DOCX, PPTX, CSV, and XLSX structure.",
        "OCR Ingestion": "Makes scanned PDFs and images searchable.",
        "Media Transcription": "Turns local audio/video into timestamped transcript chunks.",
        "Web / YouTube / Repo Connectors": "Ingests external pages, transcripts, and safe repo ZIPs.",
        "Chunking": "Splits extracted blocks into retrieval-sized chunks.",
        "Embeddings": "Converts chunk text to vector representations.",
        "Vector Store": "Stores vectors for retrieval.",
        "Retrieval / Reranking": "Finds relevant chunks for a query.",
        "Grounded Answer Generation": "Builds cited answers from retrieved context.",
        "Citations / Source Drawer": "Displays source evidence and metadata.",
        "Structured Extraction": "Extracts schema-like fields from documents.",
        "Document Comparison / Reports": "Compares and reports document differences.",
        "Agent Tools / Orchestrator": "Coordinates higher-level document operations.",
        "Review Workflow": "Human review queue and decision flow.",
        "Usage Metering": "Records usage events and summarizes quota consumption.",
        "Billing Plans": "Internal plan and quota enforcement.",
        "Admin / Support Console": "Platform metadata operations for support.",
        "Audit Events": "Operational and security audit trail.",
        "Compliance Controls": "Workspace export and soft-deletion posture.",
        "Observability": "Health, metrics, request IDs, and logs.",
        "Database Models": "SQLAlchemy domain model.",
        "Evals": "Deterministic quality evaluation suite.",
        "Tests": "Pytest regression suite.",
        "Deployment / Infra": "Docker Compose and operational docs.",
        "Scripts": "Local development, smoke, and quality automation.",
    }.get(area, "Project area.")


def architecture_status(area: str, files: list[str], routes: list[str], items: list[str]) -> str:
    if files or routes or items:
        return "Implemented"
    if area in {"Persistent Vector Store", "Background Workers"}:
        return "Limited"
    return "Review"


def architecture_improvements(area: str) -> str:
    if "Vector" in area:
        return "Add durable vector storage before production scale."
    if "Worker" in area or "Media" in area or "OCR" in area:
        return "Move long-running jobs to a queue with retries."
    if "Connector" in area:
        return "Add connector UI and async progress."
    if "Evals" in area:
        return "Add connector and OCR/media eval cases."
    return "Keep tests and docs aligned as the feature evolves."


def area_matches_path(area: str, path: str) -> bool:
    return area_matches_text(area, path)


def area_matches_text(area: str, text: str) -> bool:
    normalized = area.lower()
    text = text.lower()
    tokens = re.findall(r"[a-z]+", normalized)
    return any(token in text for token in tokens if len(token) > 3)


def route_summary_rows(routes: list[dict[str, Any]]) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for route in routes:
        grouped[route["feature"]].append(f"{route['method']} {route['path']}")
    return "".join(
        table_row(
            [badge(feature), inline_list(paths)],
            category="route",
            search={"feature": feature, "paths": paths},
        )
        for feature, paths in sorted(grouped.items())
    )


def ingestion_input(module: str) -> str:
    return {
        "text": "TXT, Markdown",
        "pdf": "PDF with OCR fallback",
        "office": "DOCX, PPTX",
        "tables": "CSV, XLSX",
        "ocr": "Scanned PDF pages and images",
        "transcribe": "TranscriptResult segments",
        "web": "Safe HTTPS URL",
        "youtube": "YouTube video ID or URL",
        "repos": "Repository ZIP archive",
        "loader": "Uploaded file path and InputType",
        "types": "Shared normalized dataclasses",
    }.get(module, "-")


def ingestion_metadata(module: str) -> str:
    return {
        "web": "url, final_url, title, content_type",
        "youtube": "video_id, timestamps, language, segment_count",
        "repos": "repo_name, file_path, language, line_start, line_end",
        "ocr": "page_number, ocr_confidence, low_confidence, bounding_boxes",
        "transcribe": "timestamps, language, segment windows",
        "office": "section, slide_number, table headers",
        "tables": "sheet_name, row ranges, column names, profile",
        "pdf": "page_number, OCR flag",
        "text": "filename, source_type",
        "loader": "Routes source types",
        "types": "ExtractedTextBlock, NormalizedDocument, InputType",
    }.get(module, "source_type")


def ingestion_citation(module: str) -> str:
    return {
        "web": "Website URL and title",
        "youtube": "Timestamp range",
        "repos": "File path and line range",
        "ocr": "Page and confidence",
        "transcribe": "Audio/video timestamp range",
        "office": "Slide/table/section context",
        "tables": "Sheet and row range",
    }.get(module, "Source metadata")


def ingestion_limitations(module: str) -> str:
    return {
        "web": "No browser-rendered JavaScript.",
        "youtube": "Requires transcript availability.",
        "repos": "ZIP only; not Git clone.",
        "ocr": "Quality depends on scan quality.",
        "transcribe": "No speaker diarization.",
        "office": "Complex nested content simplified.",
        "tables": "Merged cells may normalize imperfectly.",
    }.get(module, "-")


def feature_description(feature: str) -> str:
    return {
        "Authentication": "User registration, login, current-user identity, and JWT handling.",
        "Workspace Tenancy": "Workspace-scoped access control and lifecycle blocking.",
        "Document Upload": "Creates documents, files, jobs, chunks, and usage metrics.",
        "Text/PDF Ingestion": "Extracts searchable text from plain text, Markdown, and PDFs.",
        "Office/Table Ingestion": "Extracts paragraphs, slides, sheets, rows, and tables.",
        "OCR Ingestion": "Adds searchable text for scanned PDFs and image files.",
        "Media Transcription": "Converts media into timestamped transcript chunks.",
        "Web Connector": "Fetches safe public web pages and extracts readable text.",
        "YouTube Connector": "Turns available YouTube transcripts into timestamped chunks.",
        "Repo ZIP Connector": "Safely reads filtered repository ZIP files.",
        "Chunking": "Splits extracted blocks into retrieval chunks.",
        "Embeddings": "Embeds chunks for retrieval.",
        "Vector Store": "Stores and searches chunk vectors.",
        "Retrieval": "Finds source chunks for a user query.",
        "Grounded Answers": "Generates cited answers from retrieved context.",
        "Citations": "Tracks source evidence for answer claims.",
        "Source Drawer": "Shows friendly source context in the UI.",
        "Structured Extraction": "Extracts structured fields from documents.",
        "Document Comparison": "Compares document content and reports differences.",
        "Agent Tools": "Reusable tools orchestrated for document operations.",
        "Review Workflow": "Human review items and decisions.",
        "Usage Metering": "Records upload, chunk, query, and token usage.",
        "Billing Plans": "Plan-aware internal quota enforcement.",
        "Admin Console": "Platform support dashboard for operational metadata.",
        "Audit Events": "Records security and operational events.",
        "Compliance Export/Delete": "Workspace data export and soft-deletion controls.",
        "Observability": "Logs, request IDs, metrics, health, readiness.",
        "Deployment": "Docker and production-like compose setup.",
        "Evaluation Suite": "Deterministic local quality checks.",
        "Dashboard UI": "Modern SaaS workspace/admin interface.",
    }.get(feature, "Project feature.")


def feature_models(feature: str) -> list[str]:
    mapping = {
        "Authentication": ["User"],
        "Workspace Tenancy": ["Workspace", "WorkspaceMember"],
        "Document Upload": ["Document", "DocumentFile", "IngestionJob", "DocumentChunk"],
        "Review Workflow": ["ReviewItem"],
        "Usage Metering": ["UsageEvent"],
        "Billing Plans": ["WorkspaceSubscription"],
        "Audit Events": ["AuditEvent"],
        "Compliance Export/Delete": ["Workspace"],
        "Grounded Answers": ["ConversationMessage", "Citation"],
        "Citations": ["Citation", "DocumentChunk"],
    }
    return mapping.get(feature, [])


def feature_workers(feature: str, files: list[FileRecord]) -> list[str]:
    return [
        record.rel_path
        for record in files
        if record.rel_path.startswith("app/workers/")
        and feature_matches_path(feature, record.rel_path)
    ]


def feature_status(
    backend_files: list[str],
    frontend_files: list[str],
    api_routes: list[str],
    tests: list[str],
) -> str:
    if tests and (backend_files or frontend_files or api_routes):
        return "Covered"
    if backend_files or frontend_files or api_routes:
        return "Implemented"
    return "Needs Review"


def feature_user_value(feature: str) -> str:
    if "Connector" in feature or "Ingestion" in feature or feature == "Document Upload":
        return "Brings more enterprise knowledge sources into search."
    if feature in {"Grounded Answers", "Citations", "Source Drawer"}:
        return "Builds trust through evidence-backed answers."
    if feature in {"Admin Console", "Audit Events", "Compliance Export/Delete"}:
        return "Supports operations, governance, and customer trust."
    return "Supports the document AI platform experience."


def feature_priority(feature: str, tests: list[str]) -> str:
    if feature in {"Persistent Vector Store", "Background Workers"}:
        return "High"
    if not tests and feature not in {"Dashboard UI", "Deployment"}:
        return "Medium"
    return "Low"


def feature_next_improvement(feature: str) -> str:
    if feature in {"Web Connector", "YouTube Connector", "Repo ZIP Connector"}:
        return "Add frontend ingestion controls and async job progress."
    if feature == "Vector Store":
        return "Add durable vector database adapter."
    if feature == "Evaluation Suite":
        return "Add connector, OCR, and media cases."
    if feature == "Compliance Export/Delete":
        return "Add permanent deletion worker."
    return "Keep regression tests and docs current."


def test_recommendation(feature: str, status: str) -> str:
    if status == "Covered":
        return "Keep as regression coverage."
    return f"Add focused tests for {feature.lower()}."


def priority_rank(priority: str) -> int:
    return {"High": 0, "Medium": 1, "Low": 2}.get(priority, 3)


def unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def shorten(value: str, limit: int) -> str:
    value = " ".join(str(value).split())
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def search_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(search_text(part) for part in value.values())
    if isinstance(value, list | tuple | set):
        return " ".join(search_text(part) for part in value)
    return str(value)


def detect_circular_hints(imports_by_file: dict[str, list[str]]) -> list[tuple[str, str]]:
    module_by_file = {file: module_name_from_path(file) for file in imports_by_file}
    imports_by_module = {
        module_by_file[file]: set(imports) for file, imports in imports_by_file.items()
    }
    hints: list[tuple[str, str]] = []
    for module, imports in imports_by_module.items():
        for imported in imports:
            if module in imports_by_module.get(imported, set()):
                hints.append((module, imported))
    return sorted(set(hints))[:20]


CSS = r"""
:root {
  --bg: #0f172a;
  --panel: #111827;
  --panel-2: #1f2937;
  --text: #e5e7eb;
  --muted: #94a3b8;
  --border: #334155;
  --accent: #38bdf8;
  --danger: #fb7185;
  --warning: #fbbf24;
  --success: #34d399;
  --shadow: rgba(0, 0, 0, 0.28);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: inherit; }
code {
  color: #bae6fd;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 0.85em;
}
.app-shell { display: flex; min-height: 100vh; }
.sidebar {
  position: sticky;
  top: 0;
  width: 280px;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.96);
  padding: 24px 18px;
}
.brand { font-size: 1.1rem; font-weight: 800; letter-spacing: 0.02em; }
.sidebar-subtitle { color: var(--muted); font-size: 0.85rem; margin: 6px 0 20px; }
.sidebar nav { display: grid; gap: 6px; }
.sidebar a {
  padding: 9px 10px;
  border-radius: 10px;
  text-decoration: none;
  color: var(--muted);
  font-size: 0.92rem;
}
.sidebar a:hover { background: var(--panel-2); color: var(--text); }
.content { width: calc(100% - 280px); padding: 28px; }
.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-end;
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 28px;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.14), rgba(52, 211, 153, 0.08));
  box-shadow: 0 18px 60px var(--shadow);
}
.eyebrow { color: var(--accent); font-weight: 700; text-transform: uppercase; font-size: 0.75rem; }
h1 { margin: 8px 0; font-size: clamp(2rem, 4vw, 4rem); line-height: 1; }
h2 { margin: 0; font-size: 1.55rem; }
h3 { margin: 0 0 12px; font-size: 1.05rem; }
.hero-text { max-width: 760px; color: var(--muted); font-size: 1rem; line-height: 1.7; }
.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; }
button,
select,
input {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--panel);
  color: var(--text);
  padding: 10px 12px;
}
button { cursor: pointer; }
button:hover { border-color: var(--accent); }
.toolbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  gap: 12px;
  margin: 18px 0;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(17, 24, 39, 0.92);
  backdrop-filter: blur(12px);
}
.toolbar input { flex: 1; min-width: 220px; }
.section { margin: 28px 0; scroll-margin-top: 90px; }
.section-heading { margin: 0 0 16px; }
.section-heading p { color: var(--muted); margin: 6px 0 0; }
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
}
.stat-card,
.panel,
.arch-card {
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--panel);
  box-shadow: 0 10px 30px var(--shadow);
}
.stat-card { padding: 16px; }
.stat-card span { display: block; color: var(--muted); font-size: 0.82rem; }
.stat-card strong { display: block; margin-top: 8px; font-size: 1.65rem; }
.two-col {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.panel { padding: 18px; margin-bottom: 14px; overflow: hidden; }
details.panel summary {
  cursor: pointer;
  font-weight: 750;
  color: var(--text);
  margin: -4px 0 14px;
}
.arch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 14px;
}
.arch-card { padding: 18px; }
.card-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.arch-card p,
.arch-card dd,
.arch-card dt { color: var(--muted); }
.arch-card dl { display: grid; gap: 8px; }
.arch-card dt { font-weight: 700; color: var(--text); }
.table-wrap { overflow-x: auto; border-radius: 14px; border: 1px solid var(--border); }
table { border-collapse: collapse; width: 100%; min-width: 760px; }
th,
td {
  border-bottom: 1px solid var(--border);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  font-size: 0.86rem;
}
th {
  position: sticky;
  top: 0;
  background: var(--panel-2);
  color: var(--text);
  z-index: 1;
}
td { color: var(--muted); }
tr:last-child td { border-bottom: 0; }
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 0.74rem;
  color: var(--text);
  background: rgba(148, 163, 184, 0.12);
  white-space: nowrap;
}
.badge-high,
.badge-high-risk,
.badge-needs-tests { border-color: rgba(251, 113, 133, 0.6); color: var(--danger); }
.badge-medium,
.badge-partial,
.badge-limited { border-color: rgba(251, 191, 36, 0.6); color: var(--warning); }
.badge-low,
.badge-covered,
.badge-implemented,
.badge-succeeded { border-color: rgba(52, 211, 153, 0.6); color: var(--success); }
.path { display: inline-flex; align-items: center; gap: 8px; }
.copy {
  padding: 4px 7px;
  border-radius: 8px;
  font-size: 0.72rem;
}
.pipeline,
.flow {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0 0 16px;
}
.pipeline span,
.flow span {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 9px 12px;
  background: var(--panel);
  color: var(--text);
}
.hidden-by-filter { display: none !important; }
@media (max-width: 900px) {
  .app-shell { display: block; }
  .sidebar {
    position: relative;
    width: auto;
    height: auto;
  }
  .content { width: 100%; padding: 18px; }
  .hero { display: block; }
  .toolbar { position: relative; flex-direction: column; }
}
"""


JS = r"""
const searchInput = document.getElementById("globalSearch");
const categoryFilter = document.getElementById("categoryFilter");

function applyFilters() {
  const query = (searchInput.value || "").trim().toLowerCase();
  const category = categoryFilter.value;

  document.querySelectorAll(".searchable").forEach((element) => {
    const haystack = `${element.dataset.search || ""} ${element.textContent || ""}`.toLowerCase();
    const categories = element.dataset.category || "";
    const queryOk = !query || haystack.includes(query);
    const categoryOk = !category || categories.includes(category);
    element.classList.toggle("hidden-by-filter", !(queryOk && categoryOk));
  });
}

function expandAll() {
  document.querySelectorAll("details").forEach((details) => {
    details.open = true;
  });
}

function collapseAll() {
  document.querySelectorAll("details").forEach((details) => {
    details.open = false;
  });
}

document.querySelectorAll(".copy").forEach((button) => {
  button.addEventListener("click", async () => {
    const value = button.dataset.copy || "";
    try {
      await navigator.clipboard.writeText(value);
      button.textContent = "Copied";
      setTimeout(() => {
        button.textContent = "Copy";
      }, 1000);
    } catch {
      button.textContent = "Copy failed";
    }
  });
});

searchInput.addEventListener("input", applyFilters);
categoryFilter.addEventListener("change", applyFilters);
"""


if __name__ == "__main__":
    main()
