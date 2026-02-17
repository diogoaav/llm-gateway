"""UI page routes"""
from typing import Union
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.auth import verify_login, create_session, destroy_session, get_current_user, login_required
from app.db.database import get_db
from app.db import crud

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not verify_login(username, password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
        )
    session_id = create_session(username)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response


@router.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        destroy_session(session_id)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_id")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Depends(login_required),
):
    if isinstance(username, RedirectResponse):
        return username
    gateways = crud.get_all_gateways(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "gateways": gateways},
    )


@router.get("/gateways/new", response_class=HTMLResponse)
async def gateway_new(
    request: Request,
    username: str = Depends(login_required),
):
    if isinstance(username, RedirectResponse):
        return username
    return templates.TemplateResponse("gateway_form.html", {"request": request, "gateway": None})


@router.get("/gateways/{gateway_id}/edit", response_class=HTMLResponse)
async def gateway_edit(
    request: Request,
    gateway_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(login_required),
):
    if isinstance(username, RedirectResponse):
        return username
    gateway = crud.get_gateway_by_id(db, gateway_id)
    if not gateway:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("gateway_form.html", {"request": request, "gateway": gateway})


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Depends(login_required),
):
    if isinstance(username, RedirectResponse):
        return username
    gateways = crud.get_all_gateways(db)
    gateway_names = {g.id: g.name for g in gateways}
    logs_list = crud.get_request_logs(db, limit=200)
    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "logs": logs_list, "gateways": gateways, "gateway_names": gateway_names},
    )


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Depends(login_required),
):
    if isinstance(username, RedirectResponse):
        return username
    gateways = crud.get_all_gateways(db)
    usage = crud.get_token_usage(db, days=30)
    gateway_totals = {g.id: crud.get_gateway_totals(db, g.id) for g in gateways}
    gateway_names = {g.id: g.name for g in gateways}
    return templates.TemplateResponse(
        "stats.html",
        {"request": request, "gateways": gateways, "usage": usage, "gateway_totals": gateway_totals, "gateway_names": gateway_names},
    )
