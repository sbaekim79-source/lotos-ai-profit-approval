from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import OperationTestResultCreate, OperationTestResultRead
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/api/operation-tests", tags=["Operation Tests"])


@router.get("", response_model=list[OperationTestResultRead])
def list_operation_tests(
    result: str | None = None,
    tester: str | None = None,
    db: Session = Depends(get_db),
) -> list[OperationTestResultRead]:
    statement = select(models.OperationTestResult).order_by(
        models.OperationTestResult.created_at.desc()
    )
    if result:
        statement = statement.where(models.OperationTestResult.result == result)
    if tester:
        statement = statement.where(models.OperationTestResult.tester == tester)
    rows = db.execute(statement).scalars()
    return [_to_read(row) for row in rows]


@router.post("", response_model=OperationTestResultRead)
def create_operation_test(
    payload: OperationTestResultCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> OperationTestResultRead:
    row = models.OperationTestResult(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, request, "CREATE_OPERATION_TEST_RESULT", row)
    return _to_read(row)


@router.put("/{test_result_id}", response_model=OperationTestResultRead)
def update_operation_test(
    test_result_id: int,
    payload: OperationTestResultCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> OperationTestResultRead:
    row = db.get(models.OperationTestResult, test_result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Operation test result not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    _audit(db, request, "UPDATE_OPERATION_TEST_RESULT", row)
    return _to_read(row)


@router.delete("/{test_result_id}", response_model=OperationTestResultRead)
def hold_operation_test(
    test_result_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> OperationTestResultRead:
    row = db.get(models.OperationTestResult, test_result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Operation test result not found")
    row.result = "HOLD"
    db.commit()
    db.refresh(row)
    _audit(db, request, "HOLD_OPERATION_TEST_RESULT", row)
    return _to_read(row)


def _to_read(row: models.OperationTestResult) -> OperationTestResultRead:
    return OperationTestResultRead(
        id=row.id,
        test_case_id=row.test_case_id,
        test_name=row.test_name,
        tester=row.tester,
        result=row.result,
        issue=row.issue,
        action_taken=row.action_taken,
        tested_at=row.tested_at,
        created_at=row.created_at,
    )


def _audit(db: Session, request: Request, action: str, row: models.OperationTestResult) -> None:
    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action=action,
        entity_type="OPERATION_TEST_RESULT",
        entity_id=row.id,
        detail=f"{row.test_case_id} {row.result}",
        ip_address=request.client.host if request.client else None,
    )
