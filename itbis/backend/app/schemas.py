from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class EmployeeCreate(BaseModel):
    employee_id: str
    name: str
    department: str
    designation: str
    manager_id: str | None = None


class EvidenceCreate(BaseModel):
    note: str
    added_by: str


class AlertCreate(BaseModel):
    employee_id: str
    severity: str
    message: str
