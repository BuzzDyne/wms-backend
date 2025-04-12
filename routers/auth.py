from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi_jwt_auth import AuthJWT

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt

from database import get_db, User_TM, Role_TM
from schemas import LoginForm, RegisterForm
from core.error_codes import ErrCode as E
from core.utils import validate_username, validate_password
from core.db_enums import UserTMStatus

router = APIRouter(tags=["Auth"], prefix="/auth")

ACCESS_TOKEN_EXP = timedelta(minutes=120)
REFRESH_TOKEN_EXP = timedelta(hours=9)


@router.post(
    "/signup",
    responses={
        400: {
            "description": "Bad Request - Multiple Error Scenarios",
            "content": {
                "application/json": {
                    "examples": {
                        "AUT_SUP_E01 - Username Exists": {
                            "value": {"detail": E.format_error(E.AUT_SUP_E01, "()")},
                        },
                        "AUT_SUP_E02 - Role is not Exists": {
                            "value": {"detail": E.format_error(E.AUT_SUP_E02, "()")},
                        },
                        "AUT_SUP_E03 - Username Invalid Format": {
                            "value": {"detail": E.format_error(E.AUT_SUP_E03, "()")},
                        },
                        "AUT_SUP_E04 - Password Invalid Format": {
                            "value": {"detail": E.format_error(E.AUT_SUP_E04, "()")},
                        },
                    }
                }
            },
        }
    },
)
def signup(
    payload: RegisterForm = Body(default=None),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize.jwt_required()

    new_username = payload.username.lower()
    new_password = payload.password
    new_rolename = payload.rolename.lower()

    # Check if username exists
    user = db.query(User_TM).filter(User_TM.username == new_username).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.AUT_SUP_E01, new_username),
        )

    # Check if rolename exists
    role = db.query(Role_TM).filter(Role_TM.role_name == new_rolename).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.AUT_SUP_E02, new_rolename),
        )

    if not validate_username(new_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.AUT_SUP_E03),
        )

    if not validate_password(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.AUT_SUP_E04),
        )

    # Add user to DB
    new_user = User_TM(
        username=new_username,
        password=bcrypt.hashpw(new_password.encode("UTF-8"), bcrypt.gensalt()),
        role_id=role.id,
        created_dt=datetime.now(),
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": f"Created user '{new_username}'"}


@router.post(
    "/login",
    responses={
        400: {
            "description": "Bad Request - Multiple Error Scenarios",
            "content": {
                "application/json": {
                    "examples": {
                        "AUT_SIN_E01 - Username not exists": {
                            "value": {"detail": E.format_error(E.AUT_SIN_E01, "()")},
                        },
                        "AUT_SIN_E02 - Incorrect password": {
                            "value": {"detail": E.format_error(E.AUT_SIN_E02, "()")},
                        },
                    }
                }
            },
        }
    },
)
def login(
    payload: LoginForm, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    input_username = payload.username.lower()

    user = db.query(User_TM).filter(User_TM.username == input_username).first()

    if not user or user.is_active != UserTMStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.AUT_SIN_E01),
        )

    db_pw = (
        user.password
        if isinstance(user.password, bytes)
        else user.password.encode("utf-8")
    )

    if not bcrypt.checkpw(payload.password.encode("utf-8"), db_pw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.AUT_SIN_E02),
        )

    token_payload = {"role_id": user.role_id, "user_id": user.id}

    user.last_login_dt = datetime.now()
    db.commit()
    db.refresh(user)

    access_token = Authorize.create_access_token(
        subject=user.username, user_claims=token_payload, expires_time=ACCESS_TOKEN_EXP
    )
    refresh_token = Authorize.create_refresh_token(
        subject=user.username, expires_time=REFRESH_TOKEN_EXP
    )

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get(
    "/refresh",
    responses={
        400: {
            "description": "Bad Request - Multiple Error Scenarios",
            "content": {
                "application/json": {
                    "examples": {
                        "AUT_REF_E01 - Username not exists": {
                            "value": {"detail": E.format_error(E.AUT_REF_E01, "()")},
                        },
                        "AUT_REF_E02 - User disabled": {
                            "value": {"detail": E.format_error(E.AUT_REF_E02, "()")},
                        },
                    }
                }
            },
        }
    },
)
def refresh(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()

    user = db.query(User_TM).filter(User_TM.username == current_user).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=E.format_error(E.AUT_REF_E01),
        )

    if user.is_active == UserTMStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=E.format_error(E.AUT_REF_E02),
        )

    token_payload = {"role_id": user.role_id, "user_id": user.id}

    new_access_token = Authorize.create_access_token(
        subject=current_user, user_claims=token_payload, expires_time=ACCESS_TOKEN_EXP
    )
    return {"access_token": new_access_token}
