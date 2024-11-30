import asyncio
from typing import Annotated  
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException, Query  
from contextlib import asynccontextmanager
from sqlmodel import Field, SQLModel, Session, create_engine, select
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from parser import get_products

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("lifespan start")
    create_db_and_tables()
    await startup_event()
    yield
    print("lifespan end")


app = FastAPI(lifespan=lifespan) 

sqlite_url = "sqlite:///parser.db"
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

class Products(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title:str
    description:str
    price:int

async def startup_event():
    asyncio.create_task(background_parser_async()) 

async def background_parser_async():
    while True:
        print("Starting get products")
        await asyncio.sleep(60 * 60 * 6)
        products = await run_in_threadpool(get_products)
        
        for id, title, description, price in products:
            await add_item(id, title, description, price)

def get_async_session():
    sqlite_url = "sqlite+aiosqlite:///parser.db"
    engine_2 = create_async_engine(sqlite_url)
    db_session = async_sessionmaker(engine_2)
    return db_session()

async def get_session():
    async with get_async_session() as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

async def add_item(id, title, description, price):
    async with get_async_session() as session:
        # Проверяем, существует ли товар с таким кодом
        existing_item = await session.get(Products, id)  # Предполагается, что code является уникальным идентификатором

        if existing_item:
            # Если товар существует, обновляем его данные
            existing_item.title = title
            existing_item.description = description
            existing_item.price = price
            session.add(existing_item)  # Добавляем обновленный товар
        else:
            # Если товара нет, создаем новый
            item = Products(id=id, title=title, description=description, price=price)
            session.add(item)  # Добавляем новый товар

        await session.commit()  # Сохраняем изменения
        await session.refresh(existing_item if existing_item else item)  # Обновляем объект
    return existing_item if existing_item else item  # Возвращаем обновленный или новый товар

async def background_add_item():
    products = await run_in_threadpool(get_products)  # Получаем массив продуктов
    for id, title, description, price in products:  # Проходим по каждому продукту
        await add_item(id, title, description, price)  # Добавляем продукт в базу данных



@app.get("/start_parser")
async def start_parser(background_tasks: BackgroundTasks):
    # было asyncio.create_task(background_add_item())
    background_tasks.add_task(background_add_item)
    return {"status": "ok"}

@app.get("/products")
async def read_products(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100):
    stmt = select(Products).offset(offset).limit(limit)

    items = await session.scalars(stmt)
    return items.all()
    
@app.get("/products/{item_id}")
async def read_item(item_id: int, session: SessionDep):
    product = await session.get(Products, item_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{item_id}")
async def update_item(item_id: int, data: Products, session: SessionDep):
    product_db = await session.get(Products, item_id)
    if not product_db:
        raise HTTPException(status_code=404, detail="Product not found")    
    product_data = data.model_dump(exclude_unset=True)
    for field, value in product_data.items():
        setattr(product_db, field, value)
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    return product_db

@app.post("/products/create")
async def create_item(item: Products, session: SessionDep):
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@app.delete("/products/{item_id}")
async def delete_item(item_id: int, session: SessionDep):
    product = await session.get(Products, item_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return {"status": "ok"}
