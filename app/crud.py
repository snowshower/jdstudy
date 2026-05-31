from sqlalchemy.orm import Session
from . import models, schemas, auth
from collections import Counter

def get_crew_by_nickname(db: Session, nickname: str):
    return db.query(models.Crew).filter(models.Crew.nickname == nickname).first()

def create_crew(db: Session, crew: schemas.CrewCreate):
    hashed_password = auth.get_password_hash(crew.password)
    db_crew = models.Crew(
        nickname=crew.nickname,
        hashed_password=hashed_password,
        desired_job=crew.desired_job,
        target_company=crew.target_company,
        interest_keywords=crew.interest_keywords
    )
    db.add(db_crew)
    db.commit()
    db.refresh(db_crew)
    return db_crew

def get_crews(db: Session):
    return db.query(models.Crew).all()

def get_study_groups(db: Session):
    return db.query(models.StudyGroup).all()

def normalize_company(name: str) -> str:
    """[1. 문자열 정제 최우선 실행 및 마스터 사전 적용]"""
    if not name:
        return "기타"
    
    # 최우선 1순위: 공백 날리고 소문자 변환
    clean_target = name.replace(" ", "").lower()
    
    COMPANY_MAP = {
        # 🟢 네이버 계열
        "네이버": "네이버", "naver": "네이버", 
        "네이버웹툰": "네이버", "네이버파이낸셜": "네이버", "네이버클라우드": "네이버", "스노우": "네이버",
        
        # 🌌 라인 계열
        "라인": "라인", "line": "라인", 
        "라인플러스": "라인", "라인비즈플러스": "라인", "라인스튜디오": "라인", "라인넥스트": "라인",
        
        # 🟡 카카오 일반 계열 (금융 제외)
        "카카오": "카카오", "kakao": "카카오", 
        "카카오모빌리티": "카카오", "카카오엔터테인먼트": "카카오", "카카오웹툰": "카카오", "카카오브레인": "카카오", 
        "다음": "카카오", "daum": "카카오", "지메이커": "카카오",
        
        # 🟣 우아한형제들 (배달의민족) 계열
        "배민": "우아한형제들", "우형": "우아한형제들", "배달의민족": "우아한형제들", 
        "우아한형제들": "우아한형제들", "우아한": "우아한형제들", "b마트": "우아한형제들", "우아한청년들": "우아한형제들",
        
        # 🔵 토스 계열
        "토스": "토스", "toss": "토스", 
        "토스페이먼츠": "토스", "토스증권": "토스", "토스뱅크": "토스", "비바리퍼블리카": "토스",
        
        # 🟠 쿠팡 계열
        "쿠팡": "쿠팡", "coupang": "쿠팡", "쿠팡이츠": "쿠팡", "쿠팡플레이": "쿠팡",
        
        # 🟤 당근 계열
        "당근": "당근마켓", "당근마켓": "당근마켓", "daangn": "당근마켓",
        
        # 🔴 무신사 계열
        "무신사": "무신사", "musinsa": "무신사", "29cm": "무신사", "솔드아웃": "무신사",
        
        # ⚪ 기타 주요 대형 스타트업
        "직방": "직방", "zigbang": "직방", "호갱노노": "직방",
        "야놀자": "야놀자", "yanolja": "야놀자", "인터파크": "야놀자", "트리플": "야놀자", "데일리호텔": "야놀자",
        "몰로코": "몰로코", "moloco": "몰로코",
        "두나무": "두나무", "dunamu": "두나무", "업비트": "두나무", "upbit": "두나무",
        "센드버드": "센드버드", "sendbird": "센드버드",
        "오늘의집": "오늘의집", "버킷플레이스": "오늘의집", "컬리": "컬리", "마켓컬리": "컬리",
        "쏘카": "쏘카", "socar": "쏘카", "크림": "크림", "kream": "크림",
        "리디": "리디", "리디북스": "리디", "왓챠": "왓챠", "watcha": "왓챠", "데브시스터즈": "데브시스터즈",
        
        # 🏦 전통 금융권 및 테크핀 연합
        "신한은행": "금융권", "국민은행": "금융권", "kb국민은행": "금융권", "우리은행": "금융권", "하나은행": "금융권",
        "nh농협은행": "금융권", "농협은행": "금융권", "기업은행": "금융권", "ibk기업은행": "금융권", "케이뱅크": "금융권",
        "카카오뱅크": "금융권", "카카오페이": "금융권", "네이버페이": "금융권", 
        "페이코": "금융권", "payco": "금융권", "핀다": "금융권", "뱅크샐러드": "금융권",
        "미래에셋증권": "금융권", "삼성증권": "금융권", "신한카드": "금융권", "현대카드": "금융권"
    }

    # 1. 사전에서 완전 일치 확인
    if clean_target in COMPANY_MAP:
        return COMPANY_MAP[clean_target]
    
    # 2. 부분 일치 후순위 확인
    for key, val in COMPANY_MAP.items():
        if key in clean_target or clean_target in key:
            return val
            
    # 3. 사전에 없으면 원본 반환 (후에 기타 처리됨)
    return name

def calculate_match_score(crew1: models.Crew, crew2: models.Crew):
    score = 0
    common_data = {"companies": [], "keywords": []}
    
    comp1 = normalize_company(crew1.target_company)
    comp2 = normalize_company(crew2.target_company)
    
    if comp1 != "기타" and comp1 == comp2:
        score += 100
        common_data["companies"].append(crew1.target_company)

    kw1 = set(k.strip().lower() for k in (crew1.interest_keywords or "").split(",") if k.strip())
    kw2 = set(k.strip().lower() for k in (crew2.interest_keywords or "").split(",") if k.strip())
    common_kw = kw1 & kw2
    if common_kw:
        score += len(common_kw) * 20
        common_data["keywords"].extend(list(common_kw))
        
    return score, common_data

def perform_matching(db: Session):
    # 0. 초기화
    db.query(models.GroupMember).delete()
    db.query(models.StudyGroup).delete()
    db.commit()

    all_crews = db.query(models.Crew).all()
    if not all_crews:
        return []

    # [1단계: 무조건 5개의 빈 조(Group Object) 공간 먼저 확보하기]
    # 기업 정규화 및 인원수 카운팅
    normalized_names = [normalize_company(c.target_company) for c in all_crews]
    domain_counts = Counter([n for n in normalized_names if n != "기타"])
    
    # 상위 도메인 슬롯 추출 (6명 이상인 경우 2개 슬롯으로 분할)
    slot_candidates = []
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        if count >= 6:
            slot_candidates.append({"domain": domain, "suffix": "A", "count": 4})
            slot_candidates.append({"domain": domain, "suffix": "B", "count": count - 4})
        else:
            slot_candidates.append({"domain": domain, "suffix": "", "count": count})
    
    # 인원수 많은 순으로 상위 5개 슬롯 확정
    slot_candidates.sort(key=lambda x: x["count"], reverse=True)
    top_5_slots = slot_candidates[:5]
    
    # 5개가 부족하면 generic 슬롯으로 채움
    while len(top_5_slots) < 5:
        top_5_slots.append({"domain": "기타", "suffix": str(len(top_5_slots)+1), "count": 0})

    # 5개의 조 메모리 공간 생성: [멤버리스트, 매칭용도메인, 표시접미사]
    groups_data = []
    for slot in top_5_slots:
        groups_data.append([[], slot["domain"], slot["suffix"]])

    # [2단계: 1차 기업 매칭 시 '최대 4명' 컷 오프 강제 채우기]
    unassigned_pool = []
    for crew in all_crews:
        norm = normalize_company(crew.target_company)
        placed = False
        # 확보된 5개 조 중 도메인이 일치하고 인원이 4명 미만인 곳 탐색
        for g in groups_data:
            if g[1] == norm and len(g[0]) < 4:
                g[0].append(crew)
                placed = True
                break
        if not placed:
            unassigned_pool.append(crew)

    # [3단계: 4명 하드 캡 기준 잔여 기술 매칭]
    # 낙오자 풀에 있는 크루들을 인원이 4명 미만인 조에 기술 점수 기반으로 배정
    while unassigned_pool:
        outlier = unassigned_pool.pop(0)
        # 이미 4명인 조는 후보군에서 원천 배제 (Hard Cap)
        available_indices = [idx for idx, g in enumerate(groups_data) if len(g[0]) < 4]
        
        if not available_indices:
            # 모든 조가 4명이 찼을 때 (20명 초과 데이터 등) - 인원 적은 조부터 5명까지 허용
            groups_data.sort(key=lambda x: len(x[0]))
            groups_data[0][0].append(outlier)
            continue

        best_group_idx = -1
        max_tech_score = -1
        kw_outlier = set(k.strip().lower() for k in (outlier.interest_keywords or "").split(",") if k.strip())

        for idx in available_indices:
            m_list = groups_data[idx][0]
            tech_score = 0
            for member in m_list:
                kw_member = set(k.strip().lower() for k in (member.interest_keywords or "").split(",") if k.strip())
                tech_score += len(kw_outlier & kw_member)
            
            if tech_score > max_tech_score:
                max_tech_score = tech_score
                best_group_idx = idx
                
        # 매칭된 기술 핏이 있거나, 없어도 빈자리가 있는 가장 작은 조에 배정
        if best_group_idx == -1:
            best_group_idx = min(available_indices, key=lambda i: len(groups_data[i][0]))
            
        groups_data[best_group_idx][0].append(outlier)

    # DB 저장 (결과는 무조건 5개 조로 고정)
    created_groups = []
    for idx, (members, domain, suffix) in enumerate(groups_data):
        if not members: continue
        group_obj = _finalize_and_create_group(db, idx + 1, members, domain, suffix)
        created_groups.append(group_obj)

    db.commit()
    for g in created_groups:
        db.refresh(g)
    return created_groups

def _finalize_and_create_group(db: Session, counter: int, members: list, primary_domain: str, suffix: str = ""):
    all_comps = []
    all_kws = []
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            _, common = calculate_match_score(members[i], members[j])
            all_comps.extend(common["companies"])
            all_kws.extend(common["keywords"])
    
    top_comps = [item[0] for item in Counter(all_comps).most_common(2)]
    filtered_kws = [kw for kw in all_kws if kw.lower() not in ["java", "spring", "spring boot"]]
    top_kws = [item[0] for item in Counter(filtered_kws).most_common(2)]
    
    # 조 이름 결정
    if primary_domain and primary_domain != "기타":
        group_name = f"{primary_domain} {suffix}".strip() + f" Group ({counter}조)"
    else:
        group_name = f"Backend Group {counter}조"
    
    db_group = models.StudyGroup(
        name=group_name,
        common_companies=", ".join(top_comps) if top_comps else "다양한 기업",
        common_keywords=", ".join(top_kws) if top_kws else "다양한 기술"
    )
    db.add(db_group)
    db.flush()
    for m in members:
        db_member = models.GroupMember(group_id=db_group.id, crew_id=m.id)
        db.add(db_member)
    return db_group

# Admin Functions
def get_crew(db: Session, crew_id: int):
    return db.query(models.Crew).filter(models.Crew.id == crew_id).first()

def update_crew_admin(db: Session, crew_id: int, update_data: schemas.CrewUpdateAdmin):
    db_crew = get_crew(db, crew_id)
    if not db_crew: return None
    if update_data.target_company is not None: db_crew.target_company = update_data.target_company
    if update_data.interest_keywords is not None: db_crew.interest_keywords = update_data.interest_keywords
    db.commit()
    db.refresh(db_crew)
    return db_crew

def move_member(db: Session, crew_id: int, new_group_id: int):
    db_member = db.query(models.GroupMember).filter(models.GroupMember.crew_id == crew_id).first()
    if not db_member:
        db_member = models.GroupMember(crew_id=crew_id, group_id=new_group_id)
        db.add(db_member)
    else:
        db_member.group_id = new_group_id
    db.commit()
    db.refresh(db_member)
    return db_member

def clear_matching(db: Session):
    db.query(models.GroupMember).delete()
    db.query(models.StudyGroup).delete()
    db.commit()

def get_insight_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.InsightPost).order_by(models.InsightPost.created_at.desc()).offset(skip).limit(limit).all()

def get_insight_post(db: Session, post_id: int):
    return db.query(models.InsightPost).filter(models.InsightPost.id == post_id).first()

def create_insight_post(db: Session, post: schemas.InsightPostCreate, author_nickname: str):
    db_post = models.InsightPost(**post.model_dump(), author_nickname=author_nickname)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_insight_post(db: Session, db_post: models.InsightPost, post_update: schemas.InsightPostUpdate):
    update_data = post_update.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(db_post, key, value)
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_insight_post(db: Session, post_id: int):
    db_post = db.query(models.InsightPost).filter(models.InsightPost.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    return db_post
