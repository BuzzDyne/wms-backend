from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from routers import auth, picklist, stock, mapping, user, inbound
from fastapi.responses import JSONResponse

from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel

from _cred import AuthSecret

app = FastAPI()

origins = [
    "http://localhost",
    "http://herculex.my.id",
    "https://herculex.my.id",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api_v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(picklist.router, prefix=API_PREFIX)
app.include_router(stock.router, prefix=API_PREFIX)
app.include_router(mapping.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=API_PREFIX)
app.include_router(inbound.router, prefix=API_PREFIX)


# region AuthJWT
class Settings(BaseModel):
    authjwt_secret_key: str = AuthSecret["SECRET_KEY"]
    authjwt_access_token_expires = timedelta(
        minutes=AuthSecret["ACCESS_TOKEN_EXPIRE_MINUTES"]
    )


@AuthJWT.load_config
def get_config():
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# endregion


@app.get(API_PREFIX + "/health-check")
async def root():
    return JSONResponse(
        content={"status": "OK", "message": "Service is healthy"}, status_code=200
    )
