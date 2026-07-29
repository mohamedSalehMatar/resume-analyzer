from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from .services import analyze_resume
except ImportError:  # pragma: no cover - allows running as a script
    from services import analyze_resume

app = FastAPI(title="Resume Analyzer API")


class ResumeRequest(BaseModel):
    pdf_path: str = "./dataset/cv1.pdf"
    user_input: str = "Analyze this resume."


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze_resume_endpoint(request: ResumeRequest) -> dict:
    try:
        return analyze_resume(request.pdf_path, request.user_input)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
