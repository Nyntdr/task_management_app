from fastapi import APIRouter,Depends, Request,status, BackgroundTasks
from src.utils.db import get_db
from src.users import controller
from src.users.schemas import UserResponseSchema, UserSchema, LoginSchema
from sqlalchemy.orm import Session

user_routes=APIRouter(prefix="/users")

@user_routes.post("/register",response_model=UserResponseSchema,status_code=status.HTTP_201_CREATED)
async def register(body: UserSchema, bg_task: BackgroundTasks, db: Session = Depends(get_db)):
    return await controller.register(body,bg_task,db)

@user_routes.post("/login",status_code=status.HTTP_200_OK)
def login(body:LoginSchema, db:Session= Depends(get_db)):
    return controller.login_user(body,db)

@user_routes.get("/is_auth",response_model=UserResponseSchema,status_code=status.HTTP_200_OK)
def is_auth(request:Request, db:Session= Depends(get_db)):
    return controller.is_authenticated(request,db)