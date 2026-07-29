from __future__ import annotations

from typing import Any, Dict

try:
    from .model import run_resume_analysis
except ImportError:  # pragma: no cover - allows running as a script
    from model import run_resume_analysis


def analyze_resume(pdf_path: str, user_input: str) -> Dict[str, Any]:
    if not pdf_path:
        raise ValueError("pdf_path is required")
    if not user_input:
        raise ValueError("user_input is required")

    return run_resume_analysis(pdf_path=pdf_path, user_input=user_input)
