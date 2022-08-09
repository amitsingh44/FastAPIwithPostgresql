from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, utils
from ..database import get_db
from ..schemas import UserCreate, UserOut


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get('/')
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    # Hash the password - user.password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get('/{id}', response_model=UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} not found")
    return user
