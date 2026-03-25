from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.pro_player import ProPlayer
from services.riot import get_account_by_riot_id

router = APIRouter(prefix="/admin", tags=["admin"])

class LinkAccountSchema(BaseModel):
    pro_id: int
    game_name: str
    tag: str
    region: str

class UpdateProSchema(BaseModel):
    name: str | None = None
    team: str | None = None
    role: str | None = None
    region: str | None = None
    accent_color: str | None = None
    is_active: bool | None = None

class CreateProSchema(BaseModel):
    name: str
    team: str
    role: str
    region: str
    accent_color: str = "#00e5ff"

@router.get("/pros")
def list_pros(db: Session = Depends(get_db)):
    pros = db.query(ProPlayer).order_by(ProPlayer.region, ProPlayer.team, ProPlayer.role).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "team": p.team,
            "role": p.role,
            "region": p.region,
            "accent_color": p.accent_color,
            "has_puuid": p.riot_puuid is not None,
            "riot_puuid": p.riot_puuid,
            "photo_url": p.photo_url,
            "is_active": p.is_active,
        }
        for p in pros
    ]

@router.post("/pros/link-account")
async def link_account(body: LinkAccountSchema, db: Session = Depends(get_db)):
    pro = db.query(ProPlayer).filter(ProPlayer.id == body.pro_id).first()
    if not pro:
        raise HTTPException(404, "Joueur introuvable")

    # Vérifier si le puuid est déjà utilisé
    try:
        account = await get_account_by_riot_id(body.game_name, body.tag, body.region)
        puuid = account["puuid"]

        existing = db.query(ProPlayer).filter(
            ProPlayer.riot_puuid == puuid,
            ProPlayer.id != body.pro_id
        ).first()
        if existing:
            raise HTTPException(400, f"Ce compte est déjà lié à {existing.name} ({existing.team})")

        pro.riot_puuid = puuid
        db.commit()
        return {
            "success": True,
            "pro": pro.name,
            "account": f"{body.game_name}#{body.tag}",
            "puuid": puuid[:20] + "..."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@router.delete("/pros/{pro_id}")
def delete_pro(pro_id: int, db: Session = Depends(get_db)):
    pro = db.query(ProPlayer).filter(ProPlayer.id == pro_id).first()
    if not pro:
        raise HTTPException(404, "Joueur introuvable")
    db.delete(pro)
    db.commit()
    return {"success": True, "deleted": pro.name}

@router.put("/pros/{pro_id}")
def update_pro(pro_id: int, body: UpdateProSchema, db: Session = Depends(get_db)):
    pro = db.query(ProPlayer).filter(ProPlayer.id == pro_id).first()
    if not pro:
        raise HTTPException(404, "Joueur introuvable")
    if body.name is not None: pro.name = body.name
    if body.team is not None: pro.team = body.team
    if body.role is not None: pro.role = body.role
    if body.region is not None: pro.region = body.region
    if body.accent_color is not None: pro.accent_color = body.accent_color
    if body.is_active is not None: pro.is_active = body.is_active
    db.commit()
    return {"success": True, "pro": pro.name}

@router.post("/pros")
def create_pro(body: CreateProSchema, db: Session = Depends(get_db)):
    pro = ProPlayer(
        name=body.name,
        team=body.team,
        role=body.role,
        region=body.region,
        accent_color=body.accent_color,
        is_active=True,
    )
    db.add(pro)
    db.commit()
    db.refresh(pro)
    return {"success": True, "id": pro.id, "name": pro.name}

@router.delete("/pros/{pro_id}/unlink")
def unlink_account(pro_id: int, db: Session = Depends(get_db)):
    pro = db.query(ProPlayer).filter(ProPlayer.id == pro_id).first()
    if not pro:
        raise HTTPException(404, "Joueur introuvable")
    pro.riot_puuid = None
    db.commit()
    return {"success": True, "pro": pro.name}