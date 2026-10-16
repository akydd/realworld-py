import re
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from app.api import users
from app.services.custom_errors import AuthenticationException

app = FastAPI()

app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI with Uvicorn!"}


_KEY_RE = re.compile(r"Key \((?P<columns>.+?)\)=")


def unique_violation_columns(exc: IntegrityError) -> list[str] | None:
    err = exc.orig
    while err is not None:
        if getattr(err, "sqlstate", None) == "23505":  # unique_violation
            m = _KEY_RE.search(getattr(err, "detail", "") or "")
            if m:
                return [c.strip() for c in m.group("columns").split(",")]
            err = getattr(err, "__cause__", None)
    return None


@app.exception_handler(IntegrityError)
async def duplicate_exception_handler(request: Request, e: IntegrityError):
    cols = unique_violation_columns(e)
    if cols:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=jsonable_encoder(
                {"errors": {c: ["has already been taken"] for c in cols}}
            ),
        )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=jsonable_encoder({"errors": {"something": "has already been taken"}}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, e: RequestValidationError):
    err: dict[str, list[str]] = {}
    for error in e.errors():
        err[error["loc"][-1]] = [error["msg"]]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=jsonable_encoder({"errors": err}),
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(
    request: Request, e: AuthenticationException
):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=jsonable_encoder({"errors": {"credentials": ["invalid"]}}),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception):
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder({"errors": {"unknown_error": [str(e)]}}),
    )
