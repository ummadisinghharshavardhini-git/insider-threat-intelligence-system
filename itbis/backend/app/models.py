from pydantic import BaseModel, EmailStr
from typing import Optional


class User(BaseModel):
    id: Optional[int] = None
    email: EmailStr
    role: str


class Employee(BaseModel):
    id: Optional[int] = None
    employee_id: str
    name: str
    department: str
    designation: str
    manager_id: Optional[str] = None
