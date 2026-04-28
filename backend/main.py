from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal, User, Project, Review, Badge, init_db
from sqlalchemy.orm import Session
import uvicorn

app = FastAPI(title="Project-Тим API", description="Сервис поиска проектных партнеров для студентов", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    full_name: str
    email: str
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    skills: List[str] = []
    soft_skills: List[str] = []
    role: Optional[str] = None
    portfolio_links: List[str] = []
    about: Optional[str] = None
    interests: List[str] = []

class UserUpdate(BaseModel):
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    skills: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    role: Optional[str] = None
    portfolio_links: Optional[List[str]] = None
    about: Optional[str] = None
    interests: Optional[List[str]] = None

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

@app.get("/")
def read_root():
    return {
        "message": "Добро пожаловать в Project-Тим API!",
        "description": "Платформа для поиска проектных партнеров среди студентов",
        "version": "1.0.0",
        "features": ["Поиск по навыкам и ролям", "Репутационная система", "Геймификация", "Верификация компетенций"]
    }

@app.post("/users/", response_model=dict)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    db_user = User(
        full_name=user.full_name,
        email=user.email,
        university=user.university,
        faculty=user.faculty,
        course=user.course,
        skills=",".join(user.skills) if user.skills else "",
        soft_skills=",".join(user.soft_skills) if user.soft_skills else "",
        role=user.role,
        portfolio_links=",".join(user.portfolio_links) if user.portfolio_links else "",
        about=user.about,
        interests=",".join(user.interests) if user.interests else "",
        rating=5.0,
        level=1,
        team_coins=0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "message": "Пользователь успешно создан", "user": format_user(db_user)}

@app.get("/users/", response_model=List[dict])
def get_users(
    search: Optional[str] = None,
    skills: Optional[str] = None,
    role: Optional[str] = None,
    university: Optional[str] = None,
    min_rating: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") | 
            User.skills.ilike(f"%{search}%") |
            User.university.ilike(f"%{search}%")
        )
    if skills:
        for skill in skills.split(","):
            query = query.filter(User.skills.ilike(f"%{skill.strip()}%"))
    if role:
        query = query.filter(User.role == role)
    if university:
        query = query.filter(User.university.ilike(f"%{university}%"))
    if min_rating is not None:
        query = query.filter(User.rating >= min_rating)
    
    users = query.all()
    return [format_user(u) for u in users]

@app.get("/users/{user_id}", response_model=dict)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return format_user(user)

@app.put("/users/{user_id}", response_model=dict)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user_update.skills is not None:
        user.skills = ",".join(user_update.skills)
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.university is not None:
        user.university = user_update.university
    
    db.commit()
    db.refresh(user)
    return format_user(user)

@app.post("/projects/", response_model=dict)
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
    db.refresh(db_project)
    return {"id": db_project.id, "message": "Проект успешно создан"}

@app.get("/projects/", response_model=List[dict])
def get_projects(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    projects = query.all()
    return [{
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "required_skills": p.required_skills.split(",") if p.required_skills else [],
        "required_roles": p.required_roles.split(",") if p.required_roles else [],
        "creator_id": p.creator_id,
        "status": p.status,
        "created_at": str(p.created_at)
    } for p in projects]

@app.post("/reviews/", response_model=dict)
def create_review(review: ReviewCreate, reviewer_id: int, db: Session = Depends(get_db)):
    reviewee = db.query(User).filter(User.id == review.reviewee_id).first()
    if not reviewee:
        raise HTTPException(status_code=404, detail="Оцениваемый пользователь не найден")
    
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
    
    all_reviews = db.query(Review).filter(Review.reviewee_id == review.reviewee_id).all()
    if all_reviews:
        avg_rating = sum((r.professionalism + r.deadline_compliance + r.communication) / 3 for r in all_reviews) / len(all_reviews)
        reviewee.rating = round(avg_rating, 1)
    
    reviewee.team_coins += 10
    if reviewee.team_coins >= reviewee.level * 100:
        reviewee.level += 1
    
    db.commit()
    return {"message": "Отзыв успешно создан", "new_rating": reviewee.rating, "team_coins": reviewee.team_coins}

@app.get("/reviews/user/{user_id}", response_model=List[dict])
def get_user_reviews(user_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.reviewee_id == user_id).all()
    return [{
        "id": r.id,
        "reviewer_id": r.reviewer_id,
        "project_id": r.project_id,
        "professionalism": r.professionalism,
        "deadline_compliance": r.deadline_compliance,
        "communication": r.communication,
        "comment": r.comment,
        "created_at": str(r.created_at)
    } for r in reviews]

@app.get("/badges/user/{user_id}", response_model=List[dict])
def get_user_badges(user_id: int, db: Session = Depends(get_db)):
    badges = db.query(Badge).filter(Badge.user_id == user_id).all()
    return [{"id": b.id, "name": b.name, "description": b.description, "icon": b.icon, "earned_at": str(b.earned_at)} for b in badges]

def format_user(user: User) -> dict:
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

if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
