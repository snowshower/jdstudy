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
        companies=", ".join(crew.companies) if crew.companies else None,
        tech_stacks=", ".join(crew.tech_stacks) if crew.tech_stacks else None
    )
    db.add(db_crew)
    db.commit()
    db.refresh(db_crew)
    return db_crew

def get_crews(db: Session):
    return db.query(models.Crew).all()

def get_study_groups(db: Session):
    return db.query(models.StudyGroup).all()

def calculate_match_score(crew1: models.Crew, crew2: models.Crew):
    """
    Simplified Scoring system: Intersection count for Companies and Tech Stacks.
    """
    score = 0
    common_data = {"companies": [], "techs": []}
    
    # Parse stored strings
    c1_list = [c.strip() for c in crew1.companies.split(',')] if crew1.companies else []
    c2_list = [c.strip() for c in crew2.companies.split(',')] if crew2.companies else []
    t1_list = [t.strip() for t in crew1.tech_stacks.split(',')] if crew1.tech_stacks else []
    t2_list = [t.strip() for t in crew2.tech_stacks.split(',')] if crew2.tech_stacks else []
    
    # 1. Company Overlap (Intersection)
    comps1 = set(c1_list)
    comps2 = set(c2_list)
    common_comp = comps1 & comps2
    if common_comp:
        score += len(common_comp) * 15  # Weighted high
        common_data["companies"].extend(list(common_comp))
                
    # 2. Tech Stack Overlap (Jaccard Similarity for fine-tuning)
    techs1 = set(t1_list)
    techs2 = set(t2_list)
    if techs1 or techs2:
        intersection = techs1 & techs2
        union = techs1 | techs2
        jaccard = len(intersection) / len(union) if union else 0
        score += jaccard * 10
        common_data["techs"].extend(list(intersection))
        
    return score, common_data

def perform_matching(db: Session):
    # 0. Initialize
    db.query(models.GroupMember).delete()
    db.query(models.StudyGroup).delete()
    db.commit()

    all_crews = db.query(models.Crew).all()
    if not all_crews:
        return []

    # Target: groups of exactly 4.
    total_groups = len(all_crews) // 4
    if total_groups == 0: total_groups = 1
    
    unassigned = list(all_crews)
    groups_members = [[] for _ in range(total_groups)]
    
    if unassigned:
        groups_members[0].append(unassigned.pop(0))
        
    while unassigned:
        crew = unassigned.pop(0)
        best_group_idx = -1
        max_avg_score = -1
        
        available_indices = [i for i, g in enumerate(groups_members) if len(g) < 4]
        
        if not available_indices:
            groups_members.append([crew])
            continue
            
        for idx in available_indices:
            current_group = groups_members[idx]
            if not current_group:
                score = 0
            else:
                total_score = 0
                for member in current_group:
                    s, _ = calculate_match_score(crew, member)
                    total_score += s
                score = total_score / len(current_group)
            
            if score > max_avg_score:
                max_avg_score = score
                best_group_idx = idx
                
        groups_members[best_group_idx].append(crew)

    created_groups = []
    for idx, members in enumerate(groups_members):
        if not members: continue
        group_obj = _create_group_object(db, idx + 1, members)
        created_groups.append(group_obj)

    db.commit()
    for g in created_groups:
        db.refresh(g)
    return created_groups

def _create_group_object(db: Session, counter: int, members: list):
    all_comps = []
    all_techs = []
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            _, common = calculate_match_score(members[i], members[j])
            all_comps.extend(common["companies"])
            all_techs.extend(common["techs"])
    
    top_comps = [item[0] for item in Counter(all_comps).most_common(2)]
    top_techs = [item[0] for item in Counter(all_techs).most_common(2)]
    
    group_name = f"Matching Group {counter}"
    if top_comps:
        group_name = f"{top_comps[0]} Focused Group ({counter})"
    
    db_group = models.StudyGroup(
        name=group_name,
        common_companies=", ".join(top_comps) if top_comps else "다양한 기업",
        common_keywords=", ".join(top_techs) if top_techs else "다양한 기술"
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

def delete_crew(db: Session, crew_id: int):
    db_crew = get_crew(db, crew_id)
    if db_crew:
        db.delete(db_crew)
        db.commit()
    return db_crew

def update_crew_admin(db: Session, crew_id: int, update_data: schemas.CrewUpdateAdmin):
    db_crew = get_crew(db, crew_id)
    if not db_crew: return None
    
    if update_data.companies is not None:
        db_crew.companies = ", ".join(update_data.companies) if update_data.companies else None
            
    if update_data.tech_stacks is not None:
        db_crew.tech_stacks = ", ".join(update_data.tech_stacks) if update_data.tech_stacks else None
            
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
