# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends
from starlette.config import Config
from starlette.datastructures import Secret
from fastapi import HTTPException

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None

class HeroCreate(SQLModel):
    name: str
    secret_name: str
    age: Optional[int] = None

class HeroUpdate(SQLModel):
     name : Optional[str] = None
     secret_name: Optional[str] = None
     age: Optional[int] = None
connection_string = str(DATABASE_URL).replace("postgresql", "postgresql+psycopg")
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

@app.get("/heroes", response_model=list[Hero])
def read_todos(session: Annotated[Session, Depends(get_session)]):
        heroes = session.exec(select(Hero)).all()
        return heroes
@app.post("/heroes/", response_model=Hero)
def create_todo(hero: HeroCreate , session: Annotated[Session, Depends(get_session)]):
        hero_to_insert = Hero.model_validate(hero)
        session.add(hero_to_insert)
        session.commit()
        session.refresh(hero_to_insert)
        return hero_to_insert
@app.get("/heroes/{hero_id}", response_model=Hero)
def get_hero_by_id(hero_id: int, session: Annotated[Session, Depends(get_session)]):
        hero = session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        return hero
@app.patch("/heroes/{hero_id}", response_model=Hero)
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