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
        # Check if any crew already exists
        if db.query(models.Crew).count() == 0:
            print("🚀 초기 데이터가 없습니다. 20명의 테스트 크루를 생성합니다...")
            test_crews = [
    # 🟢 1 그룹: 카카오 계열 (7명) -> 1단계에서 카카오A(4명) / 카카오B(3명)로 칼 분할 검증용
    {"nickname": "카카오콘", "target_company": "카카오", "interest_keywords": "Java, Spring Boot, MSA, 인프라", "desired_job": "backend", "password": "password123"},
    {"nickname": "페이마스터", "target_company": "카카오페이", "interest_keywords": "Spring Boot, JPA, Querydsl, 데이터베이스", "desired_job": "backend", "password": "password123"},
    {"nickname": "뱅크보이", "target_company": "카카오뱅크", "interest_keywords": "Java, Spring, MySQL, 트랜잭션", "desired_job": "backend", "password": "password123"},
    {"nickname": "택시드라이버", "target_company": "카카오모빌리티", "interest_keywords": "Java, Spring Boot, AWS, CI/CD", "desired_job": "backend", "password": "password123"},
    {"nickname": "엔터라이언", "target_company": "카카오엔터테인먼트", "interest_keywords": "Java, Spring Boot, MSA, Docker", "desired_job": "backend", "password": "password123"},
    {"nickname": "웹툰러버", "target_company": "카카오웹툰", "interest_keywords": "Java, Spring, 대용량트래픽, 모니터링", "desired_job": "backend", "password": "password123"},
    {"nickname": "옐로우어피치", "target_company": "kakao", "interest_keywords": "Spring Boot, JPA, MySQL, 성능최적화", "desired_job": "backend", "password": "password123"},

    # 🟡 2 그룹: 네이버 계열 (4명) -> 1단계에서 정확히 네이버 조(4명)로 꽉 차고 락이 걸리는지 검증용
    {"nickname": "그린팩토리", "target_company": "네이버", "interest_keywords": "Java, Spring Boot, MSA, Docker", "desired_job": "backend", "password": "password123"},
    {"nickname": "라인크루", "target_company": "네이버파이낸셜", "interest_keywords": "Spring Boot, Docker, Kubernetes, AWS", "desired_job": "backend", "password": "password123"},
    {"nickname": "쿠키마스터", "target_company": "네이버웹툰", "interest_keywords": "Java, MSA, Spring Cloud, 인프라", "desired_job": "backend", "password": "password123"},
    {"nickname": "클로바AI", "target_company": "NAVER", "interest_keywords": "Java, Spring Boot, AWS, CI/CD", "desired_job": "backend", "password": "password123"},

    # 🔵 3 그룹: 토스 계열 (3명) -> 1단계에서 뼈대(3명) 형성 후 기술 핏이 맞는 낙오자를 유도하는지 검증용
    {"nickname": "금융혁신", "target_company": "토스", "interest_keywords": "Spring Boot, Redis, 동시성제어", "desired_job": "backend", "password": "password123"},
    {"nickname": "스마트커머스", "target_company": "토스페이먼츠", "interest_keywords": "Java, Spring, Redis, 성능최적화", "desired_job": "backend", "password": "password123"},
    {"nickname": "개미투자자", "target_company": "토스증권", "interest_keywords": "Java, Spring Boot, 대용량 데이터", "desired_job": "backend", "password": "password123"},

    # 🟣 4 그룹: 배민/우형 계열 (2명) -> 🛑 이번엔 3명 미만이라 1단계 뼈대 생성에 실패하고 낙오자 풀로 빠지는지 검증용
    {"nickname": "라이더", "target_company": "배민", "interest_keywords": "Java, Spring, MySQL, JPA", "desired_job": "backend", "password": "password123"},
    {"nickname": "우아한인턴", "target_company": "우아한형제들", "interest_keywords": "Java, Querydsl, MySQL, 아키텍처", "desired_job": "backend", "password": "password123"},

    # 🔴 5 그룹: 기타 소수 낙오자군 (4명) -> 기술 스택에 맞춰 빈자리로 스며들거나 5조를 형성할 인원
    {"nickname": "로켓배송", "target_company": "쿠팡", "interest_keywords": "Java, Spring, Redis, 대용량 데이터", "desired_job": "backend", "password": "password123"}, # -> 토스 조(Redis) 저격
    {"nickname": "이웃주민", "target_company": "당근마켓", "interest_keywords": "Java, Spring Boot, MySQL, JPA", "desired_job": "backend", "password": "password123"}, # -> 배민 크루들과의 결집 저격
    {"nickname": "패션피플", "target_company": "무신사", "interest_keywords": "Java, Spring Boot, MSA, Docker", "desired_job": "backend", "password": "password123"}, # -> 카카오B 조 인프라 핏 저격
    {"nickname": "트래블러", "target_company": "야놀자", "interest_keywords": "Java, Spring, 웹소켓, 실시간", "desired_job": "backend", "password": "password123"}
]
            
            for crew_data in test_crews:
                hashed_pw = auth.get_password_hash(crew_data["password"])
                db_crew = models.Crew(
                    nickname=crew_data["nickname"],
                    target_company=crew_data["target_company"],
                    interest_keywords=crew_data["interest_keywords"],
                    desired_job=crew_data["desired_job"],
                    hashed_password=hashed_pw
                )
                db.add(db_crew)
            
            db.commit()
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
    return templates.TemplateResponse(request=request, name="admin.html", context={"user": user, "crews": crews, "groups": groups, "active_page": "admin"})

@app.get("/results-page", response_class=HTMLResponse)
def results_page(request: Request, db: Session = Depends(database.get_db), user_session = Depends(login_required)):
    user = get_current_user(request)
    groups = crud.get_study_groups(db)
    return templates.TemplateResponse(request=request, name="results.html", context={"user": user, "groups": groups, "active_page": "results"})

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
    return {"message": f"{len(groups)}개의 조가 편성되었습니다.", "groups": groups}

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
