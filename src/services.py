from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _load_notebook_namespace() -> dict[str, Any]:
    notebook_path = Path(__file__).resolve().with_name("main.ipynb")
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    with notebook_path.open("r", encoding="utf-8") as f:
        notebook_json = json.load(f)

    namespace: dict[str, Any] = {"__name__": "notebook"}
    for cell in notebook_json.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if not source:
            continue
        cell_code = "".join(source)
        exec(cell_code, namespace)

    return namespace


def analyze_resume(pdf_path: str, user_input: str) -> Dict[str, Any]:
    if not pdf_path:
        raise ValueError("pdf_path is required")
    if not user_input:
        raise ValueError("user_input is required")

    namespace = _load_notebook_namespace()
    runner = namespace.get("run_resume_analysis")
    if not callable(runner):
        raise RuntimeError("The notebook does not expose a callable run_resume_analysis")

    return runner(pdf_path=pdf_path, user_input=user_input)
