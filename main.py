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
    """
    Handle the RateLimitExceeded exception raised by SlowAPI.

    The exception is raised when the limit of requests set by SlowAPI is exceeded.
    The function returns a JSONResponse with a status code of 429 (Too Many Requests)
    and a message indicating that the limit of requests has been exceeded.

    Parameters
    ----------
    request : Request
        The request object
    exc : RateLimitExceeded
        The exception object

    Returns
    -------
    JSONResponse
        The response object

    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Limit of requests exceeded."},
    )


# REDIRECT TO DOCS
@app.get("/", include_in_schema=False)
async def root():
    """
    Redirect to the API documentation.

    This endpoint serves as a redirect to the FastAPI documentation page.
    It is not included in the OpenAPI schema.

    Returns:
        RedirectResponse: A response object that redirects to the "/docs" URL.

    """
    return RedirectResponse(url="/docs")


# STATIC PAGE
@app.get("/change_password/{token}", response_class=HTMLResponse)
async def change_password_page(request: Request, token: str):
    """
    Serve the change password HTML page.

    This endpoint serves a static HTML page where users can enter a new password
    after receiving a password reset token. The page is rendered using Jinja2 templates.

    Args:
        request (Request): The request object, providing request-specific information.
        token (str): The password reset token provided to the user.

    Returns:
        HTMLResponse: The rendered HTML page for changing the password.

    """
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
