# LOTOS AI Profit Approval System 운영 테스트 시나리오

## 1. 테스트 목적

- Profit Sheet 업로드부터 AI 결재, Workflow 승인, PDF 출력, Dashboard 반영까지 정상 작동 여부 확인
- Parser 정확도 확인
- 결재 기준 적용 여부 확인
- Partner Fee 검증 여부 확인
- Tariff DB 축적 여부 확인
- 권한관리 정상 작동 여부 확인

## 2. 테스트 범위

- Upload
- Parse
- Map to Case
- Manual Edit
- AI Analyze
- Save
- Workflow
- Dashboard
- Tariff
- Quotes
- Master
- PDF Report
- Audit Log
- Backup

## 3. 기본 테스트 시나리오

### TC-001 Health Check

- URL: `/health`
- 기대결과: status ok

### TC-002 Master Seed

- POST `/api/masters/seed-defaults`
- 기대결과: 기본 Master 데이터 생성

### TC-003 Profit Sheet Upload

- PDF 업로드
- 기대결과: upload_id 생성

### TC-004 Parse

- 업로드 파일 parse
- 기대결과: raw_text, raw_tables 반환

### TC-005 Map to Case

- map-to-case 실행
- 기대결과: ApprovalCaseInput 후보 생성, template_used 표시

### TC-006 Manual Edit

- 화면에서 고객명, 업무코드, 금액 수정
- 기대결과: 수정값이 Analyze 요청에 반영

### TC-007 Analyze

- AI 결재심사 실행
- 기대결과: code, GP, decision, findings 표시

### TC-008 Analyze and Save

- 결재 결과 저장
- 기대결과: approval_case_id 생성

### TC-009 Workflow Submit

- STAFF로 상신
- 기대결과: DRAFT -> SUBMITTED

### TC-010 Team Approve

- TEAM_MANAGER로 승인
- 기대결과: SUBMITTED -> TEAM_APPROVED

### TC-011 Director Approve

- DIRECTOR로 승인
- 기대결과: TEAM_APPROVED -> DIRECTOR_APPROVED

### TC-012 CEO Approve

- CEO로 승인
- 기대결과: DIRECTOR_APPROVED -> CEO_APPROVED

### TC-013 PDF Summary 생성

- Summary PDF 생성
- 기대결과: PDF 다운로드 가능

### TC-014 PDF Detail 생성

- Detail PDF 생성
- 기대결과: PDF 다운로드 가능

### TC-015 Dashboard 반영

- 저장된 결재건이 현재월 Dashboard에 반영
- 기대결과: 총건수, GP, 담당자 Point 반영

### TC-016 기간별 Dashboard 조회

- work_month 또는 start_date/end_date 조회
- 기대결과: 지정 기간 데이터만 표시

### TC-017 Tariff DB 확인

- Transport/Customs Tariff 조회
- 기대결과: 저장된 결재건의 원가 데이터 반영

### TC-018 Quote Generate

- Tariff 기반 견적 생성
- 기대결과: 권장 견적, 예상 GP 표시

### TC-019 권한 오류

- STAFF가 team-approve 시도
- 기대결과: 403 권한 없음

### TC-020 Backup

- ADMIN으로 DB Backup 실행
- 기대결과: backup 파일 생성

## 4. 샘플별 기대 결과

TOWA:

- code SI++
- GP 24,493
- Minimum GP 미달
- 운송마진 미달
- Decision: CEO_REVIEW 또는 CONDITIONAL_APPROVED

KANGKOKU HIROBA:

- code SI++
- GP 145,177
- Decision: APPROVED

HUMAN MADE:

- code SE++
- GP 32,800
- Decision: APPROVED

PNS:

- code SE
- GP 20,798
- Partner Fee USD30 OK
- Decision: APPROVED

DONGSHIN:

- code SI
- GP 11,128
- Partner Fee JPY4000 OK
- Decision: APPROVED

## 5. 테스트 결과 기록 양식

| TC ID | 테스트명 | 담당자 | 실행일 | 결과 | 이슈 | 조치 |
|---|---|---|---|---|---|---|
| TC-001 | Health Check |  |  |  |  |  |
| TC-002 | Master Seed |  |  |  |  |  |
| TC-003 | Profit Sheet Upload |  |  |  |  |  |
| TC-004 | Parse |  |  |  |  |  |
| TC-005 | Map to Case |  |  |  |  |  |
| TC-006 | Manual Edit |  |  |  |  |  |
| TC-007 | Analyze |  |  |  |  |  |
| TC-008 | Analyze and Save |  |  |  |  |  |
| TC-009 | Workflow Submit |  |  |  |  |  |
| TC-010 | Team Approve |  |  |  |  |  |
| TC-011 | Director Approve |  |  |  |  |  |
| TC-012 | CEO Approve |  |  |  |  |  |
| TC-013 | PDF Summary 생성 |  |  |  |  |  |
| TC-014 | PDF Detail 생성 |  |  |  |  |  |
| TC-015 | Dashboard 반영 |  |  |  |  |  |
| TC-016 | 기간별 Dashboard 조회 |  |  |  |  |  |
| TC-017 | Tariff DB 확인 |  |  |  |  |  |
| TC-018 | Quote Generate |  |  |  |  |  |
| TC-019 | 권한 오류 |  |  |  |  |  |
| TC-020 | Backup |  |  |  |  |  |
