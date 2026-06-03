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
        # 기존 데이터 삭제
        db.query(models.Crew).delete()
        db.commit()

        print("🚀 기존 데이터를 삭제하고 17명의 실제 매칭 데이터를 적재합니다...")
        
        matching_data = [
            {
                "group_name": "핀테크 금융 인프라 A조",
                "members": [
                    {"nickname": "모카", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼", "companies": "우아한형제들, 토스, 당근마켓, 네이버쇼핑, 카카오모빌리티"},
                    {"nickname": "에덴", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼", "companies": "토스뱅크, 우형, 당근, 네이버(쇼핑)"},
                    {"nickname": "샤를", "domains": "핀테크 / 금융, 포털 / 글로벌 빅테크 / 인프라", "companies": "토스뱅크, 네이버 쇼핑, 현대자동차"},
                    {"nickname": "이안", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼, 컨텐츠 / 엔터테인먼트 / 미디어, 포털 / 글로벌 빅테크 / 인프라", "companies": "네이버, 카카오, 토스, 당근, 우아한형제들, 현대자동차"}
                ]
            },
            {
                "group_name": "핀테크 금융 인프라 B조",
                "members": [
                    {"nickname": "로지", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼", "companies": "우아한형제들, 토스뱅크, 토스증권, 카카오뱅크, 네이버 파이낸셜"},
                    {"nickname": "마이찬", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼", "companies": "우아한형제, 딜리버리히어로, 네이버 파이낸셜, 네이버 클라우드, 토스뱅크, 토스증권, 카카오 뱅크"},
                    {"nickname": "카야", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼", "companies": "토스뱅크, 우아한형제들, 카카오뱅크"},
                    {"nickname": "피노", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼", "companies": "토스뱅크, 우아한형제들, 네이버, 카카오"},
                    {"nickname": "스타크", "domains": "핀테크 / 금융, 커머스 / 로컬 플랫폼, 컨텐츠 / 엔터테인먼트 / 미디어, 포털 / 글로벌 빅테크 / 인프라", "companies": "토스"}
                ]
            },
            {
                "group_name": "올라운드 커머스 플랫폼조",
                "members": [
                    {"nickname": "바니", "domains": "커머스 / 로컬 플랫폼, 컨텐츠 / 엔터테인먼트 / 미디어, 포털 / 글로벌 빅테크 / 인프라", "companies": "우아한형제들, 당근, 네이버, 라인, 지그재그, 무신사, 올리브영, 야놀자"},
                    {"nickname": "이삭", "domains": "커머스 / 로컬 플랫폼, 포털 / 글로벌 빅테크 / 인프라", "companies": "올리브영, 쿠팡"},
                    {"nickname": "러키", "domains": "커머스 / 로컬 플랫폼", "companies": "당근"},
                    {"nickname": "피즈", "domains": "커머스 / 로컬 플랫폼, 컨텐츠 / 엔터테인먼트 / 미디어, 포털 / 글로벌 빅테크 / 인프라", "companies": "네카라쿠배 토스"}
                ]
            },
            {
                "group_name": "컨텐츠 플랫폼 미디어 인프라조",
                "members": [
                    {"nickname": "소낙눈", "domains": "커머스 / 로컬 플랫폼, 컨텐츠 / 엔터테인먼트 / 미디어", "companies": "우아한형제들, 네이버, 치지직, 야놀자, 위버스컴퍼니, 디어유, 샌드박스네트워크, 레진엔터테인먼트"},
                    {"nickname": "이산", "domains": "커머스 / 로컬 플랫폼, 컨텐츠 / 엔터테인먼트 / 미디어, 포털 / 글로벌 빅테크 / 인프라", "companies": "우아한형제들, 네이버웹툰, 밀리의서재, 교보문고, 티빙, 리디, 라프텔, 핏펫, 엠넷플러스, 네이버랩스, 라인, 쿠팡, 알라딘, NOL, 오늘의 집, 네이버 플러스 스토어, 가비아"},
                    {"nickname": "초록", "domains": "컨텐츠 / 엔터테인먼트 / 미디어, 포털 / 글로벌 빅테크 / 인프라", "companies": "치지직, 우아한형제들, 토스 증권, 카카오웹툰, 네이버웹툰, 업스테이지, 네이버 검색, 네이버 쇼핑, 두나무, 놀유니버스, 야놀자, 여기어때"},
                    {"nickname": "도우너", "domains": "커머스 / 로컬 플랫폼, 포털 / 글로벌 빅테크 / 인프라", "companies": "네이버, 카카오, 우아한형제들"}
                ]
            }
        ]

        for group in matching_data:
            group_name = group["group_name"]
            for member in group["members"]:
                crew_in = schemas.CrewCreate(
                    nickname=member["nickname"],
                    password="1234",
                    group_name=group_name,
                    survey_domains=member["domains"],
                    survey_companies=member["companies"]
                )
                crud.create_crew(db, crew_in)
        
        print(f"✅ 17명의 실제 데이터 적재가 완료되었습니다.")
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

@app.get("/mypage", response_class=HTMLResponse)
def mypage(request: Request, user_session = Depends(login_required)):
    user = get_current_user(request)
    return templates.TemplateResponse(request=request, name="mypage.html", context={"user": user, "active_page": "mypage"})

@app.get("/admin-page", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(database.get_db), admin = Depends(admin_required)):
    user = get_current_user(request)
    crews = crud.get_crews(db)
    
    # Process for template rendering
    processed_crews = [schemas.CrewResponse.model_validate(c) for c in crews]
        
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"user": user, "crews": processed_crews, "active_page": "admin"}
    )

@app.get("/results-page", response_class=HTMLResponse)
def results_page(request: Request, db: Session = Depends(database.get_db), user_session = Depends(login_required)):
    user = get_current_user(request)
    crews = crud.get_crews(db)
    
    # Grouping crews by group_name
    groups_dict = {}
    for crew in crews:
        processed_crew = schemas.CrewResponse.model_validate(crew)
        g_name = crew.group_name
        if g_name not in groups_dict:
            groups_dict[g_name] = {"name": g_name, "members": []}
        groups_dict[g_name]["members"].append(processed_crew)
    
    groups = list(groups_dict.values())
            
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

@app.post("/login")
def login(login_data: schemas.LoginRequest, request: Request, db: Session = Depends(database.get_db)):
    db_crew = crud.get_crew_by_nickname(db, nickname=login_data.nickname)
    # Check if user exists and verify password (using the password column which stores hash)
    if not db_crew or not auth.verify_password(login_data.password, db_crew.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="닉네임 또는 비밀번호가 잘못되었습니다."
        )
    
    # Store user info in session
    request.session["user"] = {"nickname": db_crew.nickname, "id": db_crew.id, "is_admin": False}
    return {"message": "로그인 성공"}

@app.post("/api/update-password")
def update_password(data: schemas.PasswordUpdate, request: Request, db: Session = Depends(database.get_db), user_session = Depends(login_required)):
    db_crew = crud.get_crew(db, user_session["id"])
    if not db_crew or not auth.verify_password(data.current_password, db_crew.password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
    
    crud.update_crew_password(db, user_session["id"], data.new_password)
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

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
