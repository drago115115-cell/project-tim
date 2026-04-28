from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal, User, Project, Review, Badge, init_db
from sqlalchemy.orm import Session

# Создаем приложение FastAPI
app = FastAPI(title="Project-Тим API", version="1.0.0")

# Добавляем поддержку CORS (для соединения с фронтендом)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Вспомогательные функции ---

def get_db():
    """Функция для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def format_user(user: User) -> dict:
    """Функция для красивого представления пользователя в JSON."""
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "university": user.university,
        "faculty": user.faculty,
        "course": user.course,
        "skills": user.skills.split(",") if user.skills else [],
        "soft_skills": user.soft_skills.split(",") if user.soft_skills else [],
        "role": user.role,
        "portfolio_links": user.portfolio_links.split(",") if user.portfolio_links else [],
        "about": user.about,
        "interests": user.interests.split(",") if user.interests else [],
        "rating": user.rating,
        "level": user.level,
        "team_coins": user.team_coins,
        "created_at": str(user.created_at)
    }

# --- Модели Pydantic (описание данных, которые мы ждем от пользователя) ---

class UserCreate(BaseModel):
    full_name: str
    email: str
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    skills: List[str] = []
    role: Optional[str] = None
    about: Optional[str] = None

class ProjectCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str] = []
    required_roles: List[str] = []
    status: str = "open"

class ReviewCreate(BaseModel):
    reviewee_id: int
    project_id: int
    professionalism: int
    deadline_compliance: int
    communication: int
    comment: Optional[str] = None

# --- Эндпоинты API ---

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в Project-Тим API!", "version": "1.0.0"}

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email уже используется")
    
    db_user = User(
        full_name=user.full_name,
        email=user.email,
        university=user.university,
        faculty=user.faculty,
        course=user.course,
        skills=",".join(user.skills) if user.skills else "",
        role=user.role,
        about=user.about,
        rating=5.0,
        level=1,
        team_coins=0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Пользователь создан", "user": format_user(db_user)}

@app.get("/users/")
def get_users(search: Optional[str] = None, role: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") | 
            User.skills.ilike(f"%{search}%")
        )
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return [format_user(u) for u in users]

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return format_user(user)

@app.post("/projects/")
def create_project(project: ProjectCreate, creator_id: int, db: Session = Depends(get_db)):
    db_project = Project(
        title=project.title,
        description=project.description,
        required_skills=",".join(project.required_skills) if project.required_skills else "",
        required_roles=",".join(project.required_roles) if project.required_roles else "",
        creator_id=creator_id,
        status=project.status
    )
    db.add(db_project)
    db.commit()
    return {"message": "Проект создан", "project_id": db_project.id}

@app.post("/reviews/")
def create_review(review: ReviewCreate, reviewer_id: int, db: Session = Depends(get_db)):
    db_review = Review(
        reviewer_id=reviewer_id,
        reviewee_id=review.reviewee_id,
        project_id=review.project_id,
        professionalism=review.professionalism,
        deadline_compliance=review.deadline_compliance,
        communication=review.communication,
        comment=review.comment
    )
    db.add(db_review)
    
    reviewee = db.query(User).filter(User.id == review.reviewee_id).first()
    if reviewee:
        all_reviews = db.query(Review).filter(Review.reviewee_id == review.reviewee_id).all()
        if all_reviews:
            avg = sum((r.professionalism + r.deadline_compliance + r.communication) / 3 for r in all_reviews) / len(all_reviews)
            reviewee.rating = round(avg, 1)
        reviewee.team_coins += 10
        db.commit()
    return {"message": "Отзыв сохранен", "new_rating": reviewee.rating if reviewee else None}

# --- Инициализация БД при запуске ---
if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int("8000"))
