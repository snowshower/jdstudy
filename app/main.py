from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas, database, auth
import os

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="JD 분석 스터디 매칭 시스템")

# --- Startup Event: Initial Data Seed ---
@app.on_event("startup")
def seed_data():
    db = database.SessionLocal()
    try:
        if db.query(models.Crew).count() == 0:
            print("🚀 초기 데이터가 없습니다. 20명의 테스트 크루를 생성합니다...")
            test_crews = [
                # 1-4: 카카오/금융 중심 (Group 1 Target)
                {"nickname": "카카오덕후", "password": "password123", "desired_job": "backend", 
                 "companies": ["카카오", "금융권"],
                 "tech_stacks": ["Java", "Spring Boot", "JPA", "MySQL"]},
                {"nickname": "뱅크보이", "password": "password123", "desired_job": "backend", 
                 "companies": ["카카오", "토스"],
                 "tech_stacks": ["Java", "Spring Boot", "Redis", "Kafka"]},
                {"nickname": "페이마스터", "password": "password123", "desired_job": "backend", 
                 "companies": ["카카오", "금융권"],
                 "tech_stacks": ["Java", "Kotlin", "Spring Boot", "MSA"]},
                {"nickname": "금융꿈나무", "password": "password123", "desired_job": "backend", 
                 "companies": ["금융권", "토스"],
                 "tech_stacks": ["Java", "Spring Boot", "Querydsl", "JUnit5"]},

                # 5-8: 네이버/라인 중심 (Group 2 Target)
                {"nickname": "네이버러버", "password": "password123", "desired_job": "backend", 
                 "companies": ["네이버", "라인"],
                 "tech_stacks": ["Java", "Spring Boot", "Docker", "Kubernetes"]},
                {"nickname": "라인크루", "password": "password123", "desired_job": "backend", 
                 "companies": ["라인", "네이버"],
                 "tech_stacks": ["Java", "Go", "Docker", "AWS"]},
                {"nickname": "그린팩토리", "password": "password123", "desired_job": "backend", 
                 "companies": ["네이버", "카카오"],
                 "tech_stacks": ["Java", "Spring Boot", "MSA", "Event-Driven"]},
                {"nickname": "웹툰작가", "password": "password123", "desired_job": "backend", 
                 "companies": ["네이버", "카카오"],
                 "tech_stacks": ["Java", "Spring Boot", "Redis", "MongoDB"]},

                # 9-12: 쿠팡/우형/당근 (커머스/로컬 중심)
                {"nickname": "로켓배송", "password": "password123", "desired_job": "backend", 
                 "companies": ["쿠팡", "우아한형제들"],
                 "tech_stacks": ["Java", "Spring Boot", "Kafka", "Redis"]},
                {"nickname": "배민라이더", "password": "password123", "desired_job": "backend", 
                 "companies": ["우아한형제들", "쿠팡"],
                 "tech_stacks": ["Java", "Spring Boot", "JPA", "Querydsl"]},
                {"nickname": "당근이웃", "password": "password123", "desired_job": "backend", 
                 "companies": ["당근", "우아한형제들"],
                 "tech_stacks": ["Python", "FastAPI", "PostgreSQL", "Docker"]},
                {"nickname": "커머스왕", "password": "password123", "desired_job": "backend", 
                 "companies": ["쿠팡", "직방"],
                 "tech_stacks": ["Java", "Spring Boot", "MSA", "AWS"]},

                # 13-16: 글로벌/테크/유니콘 (몰로코/두나무/야놀자)
                {"nickname": "광고천재", "password": "password123", "desired_job": "backend", 
                 "companies": ["몰로코", "야놀자"],
                 "tech_stacks": ["Go", "Python", "Kubernetes", "Docker"]},
                {"nickname": "비트코인", "password": "password123", "desired_job": "backend", 
                 "companies": ["두나무", "금융권"],
                 "tech_stacks": ["Java", "Kotlin", "Spring Boot", "PostgreSQL"]},
                {"nickname": "여행가자", "password": "password123", "desired_job": "backend", 
                 "companies": ["야놀자", "직방"],
                 "tech_stacks": ["Java", "Spring Boot", "Redis", "AWS"]},
                {"nickname": "유니콘꿈", "password": "password123", "desired_job": "backend", 
                 "companies": ["센드버드", "몰로코"],
                 "tech_stacks": ["Python", "FastAPI", "PostgreSQL", "Kafka"]},

                # 17-20: 혼합/기타
                {"nickname": "파이썬술사", "password": "password123", "desired_job": "backend", 
                 "companies": ["당근", "야놀자"],
                 "tech_stacks": ["Python", "FastAPI", "Docker", "GitHub Actions"]},
                {"nickname": "코틀린짱", "password": "password123", "desired_job": "backend", 
                 "companies": ["카카오", "토스"],
                 "tech_stacks": ["Kotlin", "Spring Boot", "JPA", "JUnit5"]},
                {"nickname": "데브옵스", "password": "password123", "desired_job": "backend", 
                 "companies": ["네이버", "쿠팡"],
                 "tech_stacks": ["Go", "Kubernetes", "Terraform", "Jenkins"]},
                {"nickname": "스프링장인", "password": "password123", "desired_job": "backend", 
                 "companies": ["우아한형제들", "라인"],
                 "tech_stacks": ["Java", "Spring Boot", "Querydsl", "RestAssured"]},
            ]
            
            for crew_data in test_crews:
                crew_in = schemas.CrewCreate(**crew_data)
                crud.create_crew(db, crew_in)
            
            print("✅ 20명의 테스트 데이터 삽입이 완료되었습니다.")
    except Exception as e:
        print(f"❌ 데이터 삽입 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

# Session management
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files if directory exists
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user

class NotAuthenticatedException(Exception):
    pass

@app.exception_handler(NotAuthenticatedException)
async def auth_exception_handler(request: Request, exc: NotAuthenticatedException):
    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)

def login_required(request: Request):
    user = request.session.get("user")
    if not user:
        raise NotAuthenticatedException()
    return user

# Admin Credentials
ADMIN_ID = "snowshower"
ADMIN_PW = "haemoglo0130"

def admin_required(request: Request):
    user = request.session.get("user")
    if not user or not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return user

# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request=request, name="base.html", context={"user": user, "active_page": "home"})

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/results-page")
    return templates.TemplateResponse(request=request, name="login.html", context={"user": user, "active_page": "login"})

@app.get("/signup-page", response_class=HTMLResponse)
def signup_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/results-page")
    return templates.TemplateResponse(request=request, name="signup.html", context={"user": user, "active_page": "signup"})

@app.get("/admin-page", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    user = get_current_user(request)
    crews = crud.get_crews(db)
    groups = crud.get_study_groups(db)
    
    for crew in crews:
        crew.company_list = [c.strip() for c in crew.companies.split(',')] if crew.companies else []
        crew.tech_list = [t.strip() for t in crew.tech_stacks.split(',')] if crew.tech_stacks else []
        
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"user": user, "crews": crews, "groups": groups, "active_page": "admin"}
    )

@app.get("/results-page", response_class=HTMLResponse)
def results_page(request: Request, db: Session = Depends(database.get_db), user_session = Depends(login_required)):
    user = get_current_user(request)
    groups = crud.get_study_groups(db)
    
    for group in groups:
        for member in group.members:
            crew_obj = member.crew if hasattr(member, 'crew') else member
            crew_obj.company_list = [c.strip() for c in crew_obj.companies.split(',')] if crew_obj.companies else []
            crew_obj.tech_list = [t.strip() for t in crew_obj.tech_stacks.split(',')] if crew_obj.tech_stacks else []
            
    return templates.TemplateResponse(
        request=request, 
        name="results.html", 
        context={"user": user, "groups": groups, "active_page": "results"}
    )

@app.get("/board-page", response_class=HTMLResponse)
def board_page(request: Request, db: Session = Depends(database.get_db), user_session = Depends(login_required)):
    user = get_current_user(request)
    posts = crud.get_insight_posts(db)
    return templates.TemplateResponse(request=request, name="board.html", context={"user": user, "posts": posts, "active_page": "board"})

@app.get("/board-page/{post_id}", response_class=HTMLResponse)
def post_detail_page(post_id: int, request: Request, db: Session = Depends(database.get_db), user_session = Depends(login_required)):
    user = get_current_user(request)
    post = crud.get_insight_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return templates.TemplateResponse(request=request, name="post_detail.html", context={"user": user, "post": post, "active_page": "board"})

# --- API Routes ---

@app.post("/admin/login")
def admin_login(login_data: schemas.LoginRequest, request: Request):
    if login_data.nickname == ADMIN_ID and login_data.password == ADMIN_PW:
        request.session["user"] = {"nickname": ADMIN_ID, "is_admin": True}
        return {"message": "관리자 로그인 성공"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="관리자 계정 정보가 잘못되었습니다."
    )

@app.get("/admin/dashboard")
def admin_dashboard(db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    crews = crud.get_crews(db)
    return {"crews": crews}

@app.post("/admin/match")
def trigger_matching(db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    groups = crud.perform_matching(db)
    return {"message": f"{len(groups)}개의 조가 편성되었습니다.", "groups": [schemas.GroupResponse.model_validate(g) for g in groups]}

@app.post("/admin/clear-match")
def admin_clear_matching(db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    crud.clear_matching(db)
    return {"message": "매칭 데이터가 초기화되었습니다."}

@app.put("/admin/crew/{crew_id}")
def admin_update_crew(crew_id: int, update_data: schemas.CrewUpdateAdmin, db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    crew = crud.update_crew_admin(db, crew_id, update_data)
    if not crew:
        raise HTTPException(status_code=404, detail="크루를 찾을 수 없습니다.")
    return {"message": "크루 정보가 수정되었습니다."}

@app.delete("/admin/crew/{crew_id}")
def admin_delete_crew(crew_id: int, db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    crew = crud.delete_crew(db, crew_id)
    if not crew:
        raise HTTPException(status_code=404, detail="크루를 찾을 수 없습니다.")
    return {"message": "크루가 삭제되었습니다."}

@app.post("/admin/move-member")
def admin_move_member(request: schemas.MoveMemberRequest, db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    crud.move_member(db, request.crew_id, request.new_group_id)
    return {"message": "그룹 이동이 완료되었습니다."}

@app.post("/register", response_model=schemas.CrewResponse, status_code=status.HTTP_201_CREATED)
def register_crew(crew: schemas.CrewCreate, db: Session = Depends(database.get_db)):
    db_crew = crud.get_crew_by_nickname(db, nickname=crew.nickname)
    if db_crew:
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 크루명입니다. 로그인해 주세요."
        )
    return crud.create_crew(db=db, crew=crew)

@app.post("/login")
def login(login_data: schemas.LoginRequest, request: Request, db: Session = Depends(database.get_db)):
    db_crew = crud.get_crew_by_nickname(db, nickname=login_data.nickname)
    if not db_crew or not auth.verify_password(login_data.password, db_crew.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="닉네임 또는 비밀번호가 잘못되었습니다."
        )
    
    # Store user info in session
    request.session["user"] = {"nickname": db_crew.nickname, "id": db_crew.id, "is_admin": False}
    return {"message": "로그인 성공"}

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/results", response_model=schemas.MatchingResultResponse)
def matching_results(db: Session = Depends(database.get_db), user = Depends(login_required)):
    groups = crud.get_study_groups(db)
    if not groups:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="현재 매칭 준비 중입니다."
        )
    return {"groups": groups}

@app.get("/board", response_model=list[schemas.InsightPostResponse])
def list_insight_posts(db: Session = Depends(database.get_db), user = Depends(login_required)):
    return crud.get_insight_posts(db)

@app.post("/board", response_model=schemas.InsightPostResponse, status_code=status.HTTP_201_CREATED)
def create_insight_post(post: schemas.InsightPostCreate, db: Session = Depends(database.get_db), user = Depends(login_required)):
    return crud.create_insight_post(db, post, author_nickname=user["nickname"])

@app.put("/board/{post_id}", response_model=schemas.InsightPostResponse)
def update_insight_post(post_id: int, post_update: schemas.InsightPostUpdate, db: Session = Depends(database.get_db), user = Depends(login_required)):
    db_post = crud.get_insight_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    if db_post.author_nickname != user["nickname"]:
        raise HTTPException(status_code=403, detail="본인의 게시글만 수정할 수 있습니다.")
    
    return crud.update_insight_post(db, db_post, post_update)

@app.delete("/board/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insight_post(post_id: int, db: Session = Depends(database.get_db), user = Depends(login_required)):
    db_post = crud.get_insight_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # Author can delete, Admin can delete anything
    is_admin = user.get("is_admin", False)
    if not is_admin and db_post.author_nickname != user["nickname"]:
        raise HTTPException(status_code=403, detail="본인의 게시글만 삭제하거나 관리자 권한이 필요합니다.")
    
    crud.delete_insight_post(db, post_id)
    return None
