from pydantic import BaseModel
from datetime import datetime

class ProductoBase(BaseModel):
    nombre: str
    precio: int

class LogBase(BaseModel):
    pregunta: str
    respuesta: str
    created_at: datetime
  

class ProductoCreate(ProductoBase):
    pass

class ProductoOut(ProductoBase):
    id: int

    class Config:
        orm_mode = True
    
class LogOut(LogBase):
    id: int

    class Config:
        orm_mode = True