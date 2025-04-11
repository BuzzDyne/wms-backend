from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, User_TM, Role_TM
from schemas import RegisterForm, ChangePasswordRequest
from core.db_enums import UserTMStatus
from datetime import datetime
import bcrypt
from core.utils import validate_password, validate_username

router = APIRouter(tags=["User"], prefix="/user")


@router.get("/")
def get_all_users(db: Session = Depends(get_db)):
    users = (
        db.query(User_TM)
        .filter(
            User_TM.is_active == UserTMStatus.ACTIVE,
            User_TM.username != "System",  # Exclude "System" user
        )
        .order_by(User_TM.created_dt.desc())
        .all()
    )
    return {"msg": "Successfully retrieved active users", "data": users}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User_TM).filter(User_TM.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if user.is_active == UserTMStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with ID {user_id} is already inactive.",
        )

    # Check if the user has role_id = 1
    if user.role_id == 1:
        active_admins = (
            db.query(User_TM)
            .filter(User_TM.role_id == 1, User_TM.is_active == UserTMStatus.ACTIVE)
            .count()
        )
        print(f"Active admins count: {active_admins}")
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last active owner.",
            )

    user.is_active = UserTMStatus.INACTIVE
    db.commit()

    return {"msg": f"User with ID {user_id} successfully deactivated."}


@router.post("/")
def create_user(payload: RegisterForm, db: Session = Depends(get_db)):
    username = payload.username.lower()
    password = payload.password
    rolename = payload.rolename.lower()

    # Validate username
    if not validate_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username does not meet the required format.",
        )

    # Validate password
    if not validate_password(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet the required format.",
        )

    # Check if username exists (active or inactive)
    existing_user = db.query(User_TM).filter(User_TM.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already exists.",
        )

    # Check if role exists
    role = db.query(Role_TM).filter(Role_TM.role_name == rolename).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{rolename}' does not exist.",
        )

    # Create new user
    new_user = User_TM(
        username=username,
        password=bcrypt.hashpw(password.encode("UTF-8"), bcrypt.gensalt()),
        role_id=role.id,
        created_dt=datetime.now(),
        is_active=UserTMStatus.ACTIVE,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": f"User '{username}' successfully created.", "data": new_user}


@router.put("/{user_id}/change-password")
def change_password(
    user_id: int, payload: ChangePasswordRequest, db: Session = Depends(get_db)
):
    user = db.query(User_TM).filter(User_TM.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if user.is_active == UserTMStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with ID {user_id} is inactive.",
        )

    # Validate password
    if not validate_password(payload.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet the required format.",
        )

    # Hash the new password
    hashed_password = bcrypt.hashpw(
        payload.new_password.encode("UTF-8"), bcrypt.gensalt()
    )
    user.password = hashed_password
    db.commit()

    return {"msg": f"Password for user with ID {user_id} successfully updated."}
