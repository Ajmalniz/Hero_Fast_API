# main.py
from contextlib import asynccontextmanager
from typing import   Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException
from simple_hero_api import settings
from simple_hero_api.model import Hero, HeroCreate, HeroUpdate, Team,TeamCreate,TeamUpdate,TeamRead,HeroRead,HeroTeamRead,TeamHeroRead

connection_string = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(
      connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield
    
app = FastAPI(lifespan=lifespan, title="Hero API")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/heroes", response_model=list[HeroRead])
def read_hero(session: Annotated[Session, Depends(get_session)]):
        heroes = session.exec(select(Hero)).all()
        return heroes
@app.post("/heroes/", response_model=HeroRead)
def create_hero(hero: HeroCreate , session: Annotated[Session, Depends(get_session)]):
        hero_to_insert = Hero.model_validate(hero)
        session.add(hero_to_insert)
        session.commit()
        session.refresh(hero_to_insert)
        return hero_to_insert
@app.get("/heroes/{hero_id}", response_model=HeroTeamRead)
def get_hero_by_id(hero_id: int, session: Annotated[Session, Depends(get_session)]):
        hero = session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        return hero
@app.patch("/heroes/{hero_id}", response_model=HeroRead)
def update_hero(hero_id: int, hero: HeroUpdate, session: Annotated[Session, Depends(get_session)]):
        hero_to_update = session.get(Hero, hero_id)
        if not hero_to_update:
            raise HTTPException(status_code=404, detail="Hero not found")
        
        hero_data = hero.model_dump(exclude_unset=True)
        for key, value in hero_data.items():
            setattr(hero_to_update, key, value)
        session.add(hero_to_update)
        session.commit()
        session.refresh(hero_to_update)
        return hero_to_update
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: Annotated[Session, Depends(get_session)]):
        hero = session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        session.delete(hero)
        session.commit()
        return {"message": "Hero deleted successfully"}
#get all teams
@app.get("/teams", response_model=list[TeamRead])
def read_teams(session: Annotated[Session, Depends(get_session)]):
        teams = session.exec(select(Team)).all()
        return teams

#create a team
@app.post("/teams/", response_model=TeamRead)
def create_team(team: TeamCreate, session: Annotated[Session, Depends(get_session)]):
        team_to_insert = Team.model_validate(team)
        session.add(team_to_insert)
        session.commit()
        session.refresh(team_to_insert)
        return team_to_insert
#single team
@app.get("/teams/{team_id}", response_model=TeamHeroRead)
def get_team_by_id(team_id: int, session: Annotated[Session, Depends(get_session)]):
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team

#update team
@app.patch("/teams/{team_id}",response_model=TeamRead)
def update_team(team_id: int, team: TeamUpdate, session: Annotated[Session, Depends(get_session)]):
        team_to_update = session.get(Team, team_id)
        if not team_to_update:
            raise HTTPException(status_code=404, detail="Team not found")

        team_data = team.model_dump(exclude_unset=True)
        for key, value in team_data.items():
            setattr(team_to_update, key, value)
        session.add(team_to_update)
        session.commit()
        session.refresh(team_to_update)
        return team_to_update
#Team Delete
@app.delete("/teams/{team_id}")
def delete_team(team_id: int, session: Annotated[Session, Depends(get_session)]):
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        session.delete(team)
        session.commit()
        return {"message": "Team deleted successfully"}
