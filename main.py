from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.routes import contacts, utils, auth, users


app = FastAPI()

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


# REDIRECT TO DOCS
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# STATIC PAGE
@app.get("/change_password/{token}", response_class=HTMLResponse)
async def change_password_page(request: Request, token: str):
    templates = Jinja2Templates(directory="src/services/templates")
    context = {"request": request, "host": request.base_url, "token": token}
    return templates.TemplateResponse("change_password.html", context)


app.include_router(contacts.router, prefix="/api")
app.include_router(utils.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
