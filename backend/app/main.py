from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import auth, board

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.site_name, debug=settings.debug)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age,
    https_only=settings.app_env == "production",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["site_name"] = settings.site_name
templates.env.globals["site_tagline"] = settings.site_tagline
app.state.templates = templates

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(auth.router)
app.include_router(board.router)


@app.get("/")
def home():
    return RedirectResponse("/board")


@app.get("/health")
def health():
    return {"status": "ok"}
