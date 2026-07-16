# lỗi
# Chưa kiểm tra phòng ban tồn tại: Code cũ thực hiện department.status trực tiếp. Nếu department_id không tồn tại, biến department sẽ là None dẫn đến lỗi AttributeError (gây ra lỗi 500 Internal Server Error).

# Kiểm tra số lượng nhân viên sai điều kiện: Sử dụng dấu > (current_count > department.max_employees) thay vì >= như yêu cầu nghiệp vụ.

# Trùng mã nhân viên (employee_code): Code cũ chỉ lọc trùng mã nhân viên trong cùng một phòng ban (Employee.department_id == data.department_id). Yêu cầu là mã nhân viên phải duy nhất trên toàn bộ hệ thống (không được trùng ở bất kỳ phòng ban nào).

# Status Code phản hồi: Cần thêm mã trạng thái thành công là 201 Created (status_code=201) thay vì mặc định 200 Ok.
# code 
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    Session
)

DATABASE_URL = “sqlite:///./company.db”
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    max_employees = Column(Integer, nullable=False)

    employees = relationship(
        "Employee",
        back_populates="department"
    )

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), nullable=False)
    full_name = Column(String(100), nullable=False)
    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False
    )

    department = relationship(
        "Department",
        back_populates="employees"
    )

Base.metadata.create_all(bind=engine)

class DepartmentCreate(BaseModel):
    name: str
    status: str
    max_employees: int

class EmployeeCreate(BaseModel):
    employee_code: str
    full_name: str
    department_id: int

class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    full_name: str
    department_id: int
    model_config = ConfigDict(from_attributes=True)

class DepartmentDetailResponse(BaseModel):
    id: int
    name: str
    status: str
    max_employees: int
    employees: List[EmployeeResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

app = FastAPI(
    title="Department Employee API"
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.post("/departments")
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db)
):
    department = Department(
        name=data.name,
        status=data.status,
        max_employees=data.max_employees
    )
    db.add(department)
    db.commit()
    db.refresh(department)

    return department


@app.get(
    "/departments/{department_id}",
    response_model=DepartmentDetailResponse
)
def get_department_detail(
    department_id: int,
    db: Session = Depends(get_db)
):
    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Phòng ban không tồn tại"
        )

    return department
@app.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=201  # Đáp ứng yêu cầu 6: Trả về 201 Created khi tạo thành công
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    department = (
        db.query(Department)
        .filter(Department.id == data.department_id)
        .first()
    )
    if department is None:
        raise HTTPException(
            status_code=404,  
            detail="Phòng ban không tồn tại"
        )

    if department.status == "INACTIVE":
        raise HTTPException(
            status_code=400,  # Trả về 400 Bad Request
            detail="Phòng ban đã ngừng hoạt động"
        )

    current_count = (
        db.query(Employee)
        .filter(Employee.department_id == data.department_id)
        .count()
    )
    if current_count >= department.max_employees:
        raise HTTPException(
            status_code=400,  # Trả về 400 Bad Request
            detail="Phòng ban đã đủ số lượng nhân viên tối đa"
        )

    duplicate_employee = (
        db.query(Employee)
        .filter(Employee.employee_code == data.employee_code)
        .first()
    )
    if duplicate_employee:
        raise HTTPException(
            status_code=400,  # Trả về 400 Bad Request
            detail="Mã nhân viên đã tồn tại trên hệ thống"
        )

    employee = Employee(
        employee_code=data.employee_code,
        full_name=data.full_name,
        department_id=data.department_id
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee