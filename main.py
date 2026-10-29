from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.db import Base, engine
from src.tasks.router import task_routes
from src.users.router import user_routes

Base.metadata.create_all(bind=engine) #only create tables if they don't exist, it won't drop existing tables

app=FastAPI(title="Task Management App")

# Allow requests from your Vue dev server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_routes)
app.include_router(user_routes)