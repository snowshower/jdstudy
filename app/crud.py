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

COMPANY_ALIASES = {
    "우형": "우아한형제들",
    "배민": "우아한형제들",
    "배달의민족": "우아한형제들",
    "우아한형제들": "우아한형제들",
    "woowahan": "우아한형제들",
    "baemin": "우아한형제들",
    "네이버": "네이버",
    "naver": "네이버",
    "토스": "토스",
    "toss": "토스",
    "viva": "토스",
    "비바리퍼블리카": "토스",
    "카카오": "카카오",
    "kakao": "카카오",
    "당근": "당근",
    "daangn": "당근",
    "라인": "라인",
    "line": "라인",
    "쿠팡": "쿠팡",
    "coupang": "쿠팡"
}

def normalize_company(s: str) -> str:
    if not s:
        return ""
    s = "".join(s.split()).lower()
    for alias, canonical in COMPANY_ALIASES.items():
        if alias.lower() in s:
            return canonical
    return s

def calculate_match_score(crew1: models.Crew, crew2: models.Crew):
    score = 0
    common_data = {"companies": [], "keywords": []}
    
    comp1_norm = normalize_company(crew1.target_company)
    comp2_norm = normalize_company(crew2.target_company)
    
    if comp1_norm and comp2_norm:
        if comp1_norm == comp2_norm:
            score += 100
            common_data["companies"].append(crew1.target_company)

    kw1 = set(k.strip() for k in (crew1.interest_keywords or "").split(",") if k.strip())
    kw2 = set(k.strip() for k in (crew2.interest_keywords or "").split(",") if k.strip())
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

    # [1단계: 기업별 버킷 분류 및 분할]
    company_buckets = {}
    for crew in all_crews:
        norm_name = normalize_company(crew.target_company)
        if not norm_name:
            norm_name = "기타"
        if norm_name not in company_buckets:
            company_buckets[norm_name] = []
        company_buckets[norm_name].append(crew)

    pre_groups = [] # [[member1, member2, ...], ...]
    outlier_pool = []

    for company, members in company_buckets.items():
        count = len(members)
        if company == "기타" or count <= 2:
            outlier_pool.extend(members)
            continue

        # 3~5명인 경우 단독 예비 조
        if 3 <= count <= 5:
            pre_groups.append(members)
        # 6명 이상인 경우 균등 분할 (3~4명 단위)
        else:
            # 최대한 4명에 가깝게 분할
            num_groups = count // 4
            if num_groups == 0: num_groups = 1
            
            avg = count // num_groups
            rem = count % num_groups
            
            start = 0
            for i in range(num_groups):
                size = avg + (1 if i < rem else 0)
                pre_groups.append(members[start:start+size])
                start += size

    # [2단계: 주류 조의 최소 정원(4명) 보장 및 잠금]
    final_groups_members = []
    
    for group in pre_groups:
        current_members = list(group)
        # 3명인 조는 낙오자 풀에서 기술 점수 높은 1명 영입
        if len(current_members) == 3:
            if outlier_pool:
                best_outlier_idx = -1
                max_score = -1
                
                for idx, outlier in enumerate(outlier_pool):
                    total_affinity = 0
                    for m in current_members:
                        s, _ = calculate_match_score(outlier, m)
                        total_affinity += s
                    
                    if total_affinity > max_score:
                        max_score = total_affinity
                        best_outlier_idx = idx
                
                if best_outlier_idx != -1:
                    current_members.append(outlier_pool.pop(best_outlier_idx))
        
        # 4~5명인 조는 확정
        final_groups_members.append(current_members)

    # [3단계: 진짜 낙오자 최종 분산 배치]
    # 현재 구성된 조가 하나도 없는 특수 상황 처리
    if not final_groups_members and outlier_pool:
        while outlier_pool:
            batch = outlier_pool[:5]
            outlier_pool = outlier_pool[5:]
            final_groups_members.append(batch)
    else:
        # 인원수가 적은 조부터 라운드 로빈 배치
        while outlier_pool:
            # 매번 가장 적은 조를 찾아서 1명 추가
            final_groups_members.sort(key=len)
            target_group = final_groups_members[0]
            
            if len(target_group) < 5:
                target_group.append(outlier_pool.pop(0))
            else:
                # 모든 조가 5명이면 새로운 조 생성
                batch = outlier_pool[:5]
                outlier_pool = outlier_pool[5:]
                final_groups_members.append(batch)

    # DB 저장
    created_groups = []
    for idx, members in enumerate(final_groups_members):
        # 1-indexed group counter
        group_obj = _finalize_and_create_group(db, idx + 1, members)
        created_groups.append(group_obj)

    db.commit()
    for g in created_groups:
        db.refresh(g)
    return created_groups

def _finalize_and_create_group(db: Session, counter: int, members: list):
    # Metadata Generation
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
    
    # 조 이름 결정 (주류 기업이 있으면 이름에 반영)
    primary_company = normalize_company(members[0].target_company) if members else "General"
    group_name = f"{primary_company} Group {counter}" if primary_company != "기타" else f"Backend Group {counter}"
    
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
    if not db_crew:
        return None
    
    if update_data.target_company is not None:
        db_crew.target_company = update_data.target_company
    if update_data.interest_keywords is not None:
        db_crew.interest_keywords = update_data.interest_keywords
    
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

# Insight Board CRUD
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
    for key, value in update_data.items():
        setattr(db_post, key, value)
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_insight_post(db: Session, post_id: int):
    db_post = db.query(models.InsightPost).filter(models.InsightPost.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    return db_post
