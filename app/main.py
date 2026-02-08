
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, select, Uuid, DateTime
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column 
from typing import Optional, Annotated
import uuid
from pydantic import BaseModel
from datetime import datetime
import tomllib

class ProductInput(BaseModel):
    name: str
class ProductOutput(BaseModel):
    id: int | None = None
    name: str
class ProductsListOutput(BaseModel):
    items: list[ProductOutput]
class Base(DeclarativeBase):
    pass
class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __init__(self, input: ProductInput):
        self.name = input.name
    def get_output(self) -> ProductOutput:
        return ProductOutput(id=self.id, name=self.name)
def get_products_list_output(products: list[Product]) -> ProductsListOutput:
    items = []
    for product in products:
        items.append(product.get_output())
    return ProductsListOutput(items=items)
database_url = ""
with open("/code/database_config.toml", "rb") as f:
    data = tomllib.load(f)
    database_url = data.get("url", "")
engine = create_engine(database_url, echo=True)
Base.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.post('/products/')
def create_product(input: ProductInput, session: SessionDep) -> ProductOutput:
    product = Product(input=input)
    session.add(product)
    session.commit()
    session.refresh(product)
    output = product.get_output()
    return output

@app.get('/products/')
def list_products(session: SessionDep) -> ProductsListOutput:
    stmt = select(Product)
    products = session.scalars(stmt).all()
    return get_products_list_output(products=products)
