from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.timezone import local_today
from app.models import AppSettings, Problem, ReviewRecord, Tag
from app.models.enums import Difficulty, Rating, ReviewStage
from app.services.problem_service import list_problems
from app.services.review_service import create_initial_review, record_review
from app.services.statistics_service import overview

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")
Db = Annotated[Session, Depends(get_db)]


def base_context(request: Request, db: Session, **extra):
    today = local_today()
    due_count = db.scalar(select(func.count(Problem.id)).where(Problem.is_archived.is_(False), Problem.next_review_at <= today, Problem.review_stage != ReviewStage.MASTERED)) or 0
    return {"request": request, "due_count": due_count, "today": today, "Rating": Rating, "ReviewStage": ReviewStage, "Difficulty": Difficulty, **extra}


def split_tags(value: str) -> list[str]:
    return list(dict.fromkeys(x.strip() for x in value.replace("，", ",").split(",") if x.strip()))


def get_or_create_tags(db: Session, value: str) -> list[Tag]:
    tags = []
    for name in split_tags(value):
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


@router.get("/")
def dashboard(request: Request, db: Db):
    today = local_today()
    due = list(db.scalars(select(Problem).where(Problem.is_archived.is_(False), Problem.next_review_at <= today, Problem.review_stage != ReviewStage.MASTERED).order_by(Problem.next_review_at).limit(5)).unique())
    upcoming = []
    for offset in range(1, 8):
        day = today + timedelta(days=offset)
        count = db.scalar(select(func.count(Problem.id)).where(Problem.is_archived.is_(False), Problem.next_review_at == day)) or 0
        upcoming.append((day, count))
    return templates.TemplateResponse(request, "dashboard.html", base_context(request, db, stats=overview(db, today), due=due, upcoming=upcoming))


@router.get("/problems")
def problems_page(request: Request, db: Db, rating: str | None = None, difficulty: str | None = None, tag: str | None = None, due: str | None = None, search: str | None = None, sort: str = "next_review_at", order: str = "asc", page: int = Query(1, ge=1)):
    items, total = list_problems(db, today=local_today(), rating=rating, difficulty=difficulty, tag=tag, due=due, search=search, sort=sort, order=order, page=page, page_size=25)
    return templates.TemplateResponse(request, "problems/list.html", base_context(request, db, problems=items, total=total, page=page, pages=max(1, (total + 24) // 25), tags=list(db.scalars(select(Tag).order_by(Tag.name))), filters={"rating": rating or "", "difficulty": difficulty or "", "tag": tag or "", "due": due or "", "search": search or "", "sort": sort, "order": order}))


@router.get("/problems/new")
def new_problem_page(request: Request, db: Db):
    return templates.TemplateResponse(request, "problems/form.html", base_context(request, db, problem=None, error=None))


@router.post("/problems/new")
async def create_problem_page(request: Request, db: Db):
    form = await request.form()
    try:
        leetcode_id = int(str(form.get("leetcode_id", "")))
        title = str(form.get("title", "")).strip()
        if leetcode_id <= 0 or not title or len(title) > 200:
            raise ValueError
        if db.scalar(select(Problem.id).where(Problem.leetcode_id == leetcode_id)):
            existing = db.scalar(select(Problem).where(Problem.leetcode_id == leetcode_id))
            return templates.TemplateResponse(request, "problems/form.html", base_context(request, db, problem=None, error=f"题目 #{leetcode_id} 已存在", existing=existing), status_code=409)
        problem = Problem(
            leetcode_id=leetcode_id, title=title, title_en=str(form.get("title_en", "")).strip() or None,
            leetcode_url=str(form.get("leetcode_url", "")).strip() or None, difficulty=Difficulty(str(form.get("difficulty", "UNKNOWN"))),
            rating=Rating(str(form.get("initial_rating", "RED"))), review_stage=ReviewStage.RED_D1,
            mistake_reason=str(form.get("mistake_reason", "")).strip() or None, my_solution=str(form.get("my_solution", "")).strip() or None,
            correct_solution=str(form.get("correct_solution", "")).strip() or None, key_points=str(form.get("key_points", "")).strip() or None,
            time_complexity=str(form.get("time_complexity", "")).strip() or None, space_complexity=str(form.get("space_complexity", "")).strip() or None,
            code=str(form.get("code", "")).rstrip() or None, tags=get_or_create_tags(db, str(form.get("tags", ""))),
        )
        db.add(problem)
        solved_on = date.fromisoformat(str(form.get("solved_on", local_today().isoformat())))
        if solved_on > local_today():
            raise ValueError
        create_initial_review(db, problem, problem.rating, review_date=solved_on)
        db.commit()
        return RedirectResponse(f"/problems/{problem.id}", status_code=303)
    except (ValueError, IntegrityError):
        db.rollback()
        return templates.TemplateResponse(request, "problems/form.html", base_context(request, db, problem=None, error="请检查题号、标题、难度和评级。"), status_code=422)


@router.get("/problems/{problem_id}")
def problem_detail(problem_id: int, request: Request, db: Db):
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "problems/detail.html", base_context(request, db, problem=problem))


@router.get("/problems/{problem_id}/edit")
def edit_problem_page(problem_id: int, request: Request, db: Db):
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "problems/form.html", base_context(request, db, problem=problem, error=None))


@router.post("/problems/{problem_id}/edit")
async def edit_problem(problem_id: int, request: Request, db: Db):
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise HTTPException(404)
    form = await request.form()
    title = str(form.get("title", "")).strip()
    if not title:
        return templates.TemplateResponse(request, "problems/form.html", base_context(request, db, problem=problem, error="题目名称不能为空。"), status_code=422)
    for field in ("title_en", "leetcode_url", "mistake_reason", "my_solution", "correct_solution", "key_points", "time_complexity", "space_complexity", "code"):
        setattr(problem, field, str(form.get(field, "")).strip() or None)
    problem.title = title
    problem.difficulty = Difficulty(str(form.get("difficulty", "UNKNOWN")))
    problem.tags = get_or_create_tags(db, str(form.get("tags", "")))
    db.commit()
    return RedirectResponse(f"/problems/{problem_id}", status_code=303)


@router.post("/problems/{problem_id}/delete")
def delete_problem_page(problem_id: int, db: Db):
    problem = db.get(Problem, problem_id)
    if problem:
        problem.is_archived = True
        db.commit()
    return RedirectResponse("/problems", status_code=303)


@router.post("/problems/{problem_id}/schedule")
def schedule_problem_page(problem_id: int, db: Db, next_review_at: Annotated[date, Form()]):
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise HTTPException(404)
    problem.next_review_at = next_review_at
    db.commit()
    return RedirectResponse(f"/problems/{problem_id}", status_code=303)


@router.get("/review")
def review_page(request: Request, db: Db, problem_id: int | None = None, completed: int = 0, red: int = 0, yellow: int = 0, green: int = 0):
    today = local_today()
    due_stmt = select(Problem).where(Problem.is_archived.is_(False), Problem.next_review_at <= today, Problem.review_stage != ReviewStage.MASTERED).order_by(Problem.next_review_at)
    queue = list(db.scalars(due_stmt).unique())
    problem = db.get(Problem, problem_id) if problem_id else (queue[0] if queue else None)
    return templates.TemplateResponse(request, "review/index.html", base_context(request, db, problem=problem, queue=queue, completed=completed, red=red, yellow=yellow, green=green))


@router.post("/review/{problem_id}")
def complete_review(problem_id: int, db: Db, rating: Annotated[Rating, Form()], duration_minutes: Annotated[str, Form()] = "", used_hint: Annotated[bool, Form()] = False, viewed_solution: Annotated[bool, Form()] = False, note: Annotated[str, Form()] = "", completed: Annotated[int, Form()] = 0, red: Annotated[int, Form()] = 0, yellow: Annotated[int, Form()] = 0, green: Annotated[int, Form()] = 0):
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise HTTPException(404)
    duration = int(duration_minutes) if duration_minutes.strip() else None
    if duration is not None and not 0 <= duration <= 600:
        raise HTTPException(422, "耗时须在 0–600 分钟之间")
    record_review(db, problem, rating, duration_minutes=duration, used_hint=used_hint, viewed_solution=viewed_solution, note=note)
    db.commit()
    counts = {"red": red, "yellow": yellow, "green": green}
    counts[rating.value.lower()] += 1
    return RedirectResponse(f"/review?completed={completed + 1}&red={counts['red']}&yellow={counts['yellow']}&green={counts['green']}", status_code=303)


@router.get("/problems/{problem_id}/history")
def problem_history(problem_id: int, request: Request, db: Db):
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise HTTPException(404)
    records = list(db.scalars(select(ReviewRecord).where(ReviewRecord.problem_id == problem_id).order_by(ReviewRecord.reviewed_at.desc())))
    return templates.TemplateResponse(request, "history.html", base_context(request, db, records=records, selected_problem=problem, problems=[]))


@router.get("/history")
def history_page(request: Request, db: Db, rating: str | None = None, problem_id: int | None = None, tag: str | None = None, days: int = 30):
    stmt = select(ReviewRecord).join(Problem).where(Problem.is_archived.is_(False), ReviewRecord.reviewed_at >= datetime.combine(local_today() - timedelta(days=days), datetime.min.time()))
    if rating: stmt = stmt.where(ReviewRecord.rating == rating)
    if problem_id: stmt = stmt.where(ReviewRecord.problem_id == problem_id)
    if tag: stmt = stmt.where(Problem.tags.any(Tag.name == tag))
    records = list(db.scalars(stmt.order_by(ReviewRecord.reviewed_at.desc()).limit(500)))
    problems = list(db.scalars(select(Problem).where(Problem.is_archived.is_(False)).order_by(Problem.leetcode_id)))
    tags = list(db.scalars(select(Tag).order_by(Tag.name)))
    return templates.TemplateResponse(request, "history.html", base_context(request, db, records=records, problems=problems, tags=tags, selected_problem=None, filters={"rating": rating or "", "problem_id": problem_id, "tag": tag or "", "days": days}))


@router.get("/statistics")
def statistics_page(request: Request, db: Db):
    return templates.TemplateResponse(request, "statistics.html", base_context(request, db, stats=overview(db, local_today())))


@router.get("/settings")
def settings_page(request: Request, db: Db):
    settings = db.get(AppSettings, 1) or AppSettings(id=1)
    return templates.TemplateResponse(request, "settings.html", base_context(request, db, settings=settings, saved=False))


@router.post("/settings")
async def save_settings(request: Request, db: Db):
    form = await request.form()
    settings = db.get(AppSettings, 1) or AppSettings(id=1)
    for field in ("red_interval", "yellow_first_interval", "yellow_repeat_interval", "green_first_interval", "green_second_interval"):
        setattr(settings, field, max(1, int(str(form.get(field, "1")))))
    settings.notifications_enabled = form.get("notifications_enabled") is not None
    settings.notification_time = str(form.get("notification_time", "08:00"))
    db.add(settings)
    db.commit()
    return templates.TemplateResponse(request, "settings.html", base_context(request, db, settings=settings, saved=True))
