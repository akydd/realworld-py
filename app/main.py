from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api import users


import app.services.custom_errors as errors

app = FastAPI()

app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI with Uvicorn!"}


@app.exception_handler(errors.DuplicateException)
async def duplicate_exception_handler(request: Request, e: errors.DuplicateException):
    return JSONResponse(
        status_code=409,
        content=jsonable_encoder({"errors": {e.field: e.message}}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, e: RequestValidationError):
    err: dict[str, list[str]] = {}
    for error in e.errors():
        err[error["loc"][-1]] = [error["msg"]]

    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"errors": err}),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception):
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder({"errors": {"unknown_error": [str(e)]}}),
    )
