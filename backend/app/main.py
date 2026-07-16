from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.api.routes import router  # noqa: E402

app = FastAPI(title="Scout")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
