from src.tasks.models import TaskModel
from src.tasks.schemas import TaskSchema
from src.users.models import UserModel
from sqlalchemy.orm import Session
from fastapi import HTTPException

def create_task(body: TaskSchema,db: Session, user: UserModel):
    data= body.model_dump()
    # new_task= TaskModel(**data)
    new_task= TaskModel(title=data['title'], 
                        description=data['description'], 
                        is_completed=data['is_completed'],
                        user_id=user.id
                        )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


def get_tasks(db:Session, user: UserModel):
    tasks= db.query(TaskModel).filter(TaskModel.user_id==user.id).all()
    return tasks

def get_task_by_id(task_id:int, db:Session):
    task= db.query(TaskModel).filter(TaskModel.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def update_task(task_id:int, body: TaskSchema, db:Session, user: UserModel):
    task= db.query(TaskModel).filter(TaskModel.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this task")
    
    data= body.model_dump()

    for field, value in data.items():
        setattr(task, field, value)
        
    db.add(task)    
    db.commit()
    db.refresh(task)
    return task

def delete_task(task_id:int, db:Session, user: UserModel):
    task= db.query(TaskModel).filter(TaskModel.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this task")
    db.delete(task)
    db.commit()
    return None 