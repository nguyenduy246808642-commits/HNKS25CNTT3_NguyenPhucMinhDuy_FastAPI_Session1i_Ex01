# lỗi
# Chưa kiểm tra phòng ban tồn tại: Code cũ thực hiện department.status trực tiếp. Nếu department_id không tồn tại, biến department sẽ là None dẫn đến lỗi AttributeError (gây ra lỗi 500 Internal Server Error).

# Kiểm tra số lượng nhân viên sai điều kiện: Sử dụng dấu > (current_count > department.max_employees) thay vì >= như yêu cầu nghiệp vụ.

# Trùng mã nhân viên (employee_code): Code cũ chỉ lọc trùng mã nhân viên trong cùng một phòng ban (Employee.department_id == data.department_id). Yêu cầu là mã nhân viên phải duy nhất trên toàn bộ hệ thống (không được trùng ở bất kỳ phòng ban nào).

# Status Code phản hồi: Cần thêm mã trạng thái thành công là 201 Created (status_code=201) thay vì mặc định 200 Ok.
# code 
from fastapi import status

@app.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    # 1. Kiểm tra phòng ban có tồn tại
    department = (
        db.query(Department)
        .filter(Department.id == data.department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phòng ban không tồn tại"
        )

    # 2. Kiểm tra trạng thái phòng ban
    if department.status == "INACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phòng ban đã ngừng hoạt động"
        )

    # 3. Kiểm tra số lượng nhân viên
    current_count = (
        db.query(Employee)
        .filter(Employee.department_id == data.department_id)
        .count()
    )

    if current_count >= department.max_employees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phòng ban đã đủ nhân viên"
        )

    # 4. Kiểm tra employee_code trên toàn hệ thống
    duplicate_employee = (
        db.query(Employee)
        .filter(Employee.employee_code == data.employee_code)
        .first()
    )

    if duplicate_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã nhân viên đã tồn tại"
        )

    # 5. Tạo nhân viên
    employee = Employee(
        employee_code=data.employee_code,
        full_name=data.full_name,
        department_id=data.department_id
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee
