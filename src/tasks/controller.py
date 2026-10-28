from src.tasks.models import TaskModel
from src.tasks.schemas import TaskSchema
from sqlalchemy.orm import Session
from fastapi import HTTPException

def create_task(body: TaskSchema,db: Session):
    data= body.model_dump()
    # new_task= TaskModel(**data)
    new_task= TaskModel(title=data['title'], 
                        description=data['description'], 
                        is_completed=data['is_completed']
                        )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Task created successfully","data": new_task}

def get_tasks(db:Session):
    tasks= db.query(TaskModel).all()
    return {"message": "Tasks retrieved successfully","data": tasks}

def get_task_by_id(task_id:int, db:Session):
    task= db.query(TaskModel).filter(TaskModel.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task retrieved successfully","data": task}


def update_task(task_id:int, body: TaskSchema, db:Session):
    task= db.query(TaskModel).filter(TaskModel.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    data= body.model_dump()

    for field, value in data.items():
        setattr(task, field, value)
        
    db.add(task)    
    db.commit()
    db.refresh(task)
    return {"message": "Task updated successfully","data": task}

def delete_task(task_id:int, db:Session):
    task= db.query(TaskModel).filter(TaskModel.id==task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}