import asyncio
import json
from datetime import datetime
from typing import Annotated  
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException, Query, WebSocket, WebSocketDisconnect  
from contextlib import asynccontextmanager
from sqlmodel import Field, SQLModel, Session, create_engine, select
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from parser import get_products
from fastapi.encoders import jsonable_encoder

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


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except RuntimeError:
                self.active_connections.remove(connection)


connection_manager = ConnectionManager()

class Products(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    description: str
    price: int

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

async def send_notification(event: str, product=None, details=None):
    message = {
        "event": event,
        "timestamp": str(datetime.utcnow()),
        "product": jsonable_encoder(product) if product else None,
        "details": details
    }
    await connection_manager.broadcast(json.dumps(message))

async def add_item(id, title, description, price):
    async with get_async_session() as session:
        existing_item = await session.get(Products, id)

        if existing_item:
            existing_item.title = title
            existing_item.description = description
            existing_item.price = price
            session.add(existing_item)
            await session.commit()
            await session.refresh(existing_item)
            return existing_item, False  # Обновлён
        else:
            item = Products(id=id, title=title, description=description, price=price)
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item, True  # Создан


async def background_add_item():
    products = await run_in_threadpool(get_products)
    updated_count = 0
    created_count = 0

    for id, title, description, price in products:
        item = await add_item(id, title, description, price)
        if item[1]:  # Маркер, создан ли товар
            created_count += 1
        else:
            updated_count += 1

    await send_notification(
        "parser_complete", 
        details={"created": created_count, "updated": updated_count}
    )


@app.get("/start_parser")
async def start_parser(background_tasks: BackgroundTasks):
    background_tasks.add_task(background_add_item)
    return {"status": "ok"}

@app.get("/products")
async def read_products(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100):
    stmt = select(Products).offset(offset).limit(limit)
    items = await session.scalars(stmt)
    products = items.all()
    return products

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

    await send_notification("update", product=product_db)
    return product_db

@app.post("/products/create")
async def create_item(item: Products, session: SessionDep):
    product_db = await session.get(Products, item.id)
    if product_db:
        raise HTTPException(status_code=400, detail="Product already exists")
    session.add(item)
    await session.commit()
    await session.refresh(item)
    await send_notification("create", product=item)
    return item

@app.delete("/products/{item_id}")
async def delete_item(item_id: int, session: SessionDep):
    product = await session.get(Products, item_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    await send_notification("delete", details={"product_id": item_id})
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "get_all_products":
                async with get_async_session() as session:
                    response = await read_products(session)
                    await websocket.send_text(json.dumps(jsonable_encoder(response), ensure_ascii=False))
                continue
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
