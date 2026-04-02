from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import seo

app = FastAPI(title="SimSEO", description="See your page through a search engine's eyes.")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(seo.router)


@app.get("/", include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
