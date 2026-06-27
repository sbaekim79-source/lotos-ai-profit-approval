# LOTOS AI Profit Approval System 사용자 매뉴얼

## 1. 시스템 개요

LOTOS AI Profit Approval System은 Profit Sheet를 기준으로 수익성을 자동 심사하고, 실제 조직 결재 Workflow까지 연결하는 업무 시스템입니다.

주요 기능은 다음과 같습니다.

- Profit Sheet PDF/Excel 업로드
- AI 결재심사
- 자동 추출값 수동수정
- 담당자 상신, 팀장 승인, 본부장 승인, 대표 승인 Workflow
- 현재 월 중심 Dashboard
- Tariff DB 자동 축적
- 견적 자동생성
- 결재심사서 PDF 출력
- 결재이력, Dashboard, Tariff, 견적 Excel Export
- ERP/회계 연동용 JSON Export

## 2. 사용자 Role

| Role | 한글명 | 주요 업무 |
|---|---|---|
| STAFF | 담당자 | Profit Sheet 업로드, AI 분석, 수정, 저장, 결재상신 |
| TEAM_MANAGER | 팀장 | 상신 건 검토, 팀장 승인, 보완요청, 반려 |
| DIRECTOR | 본부장 | 팀장 승인 건 검토, 본부장 승인, 보완요청, 반려 |
| CEO | 대표 | 최종 승인, 대표검토 건 판단, 반려, 보완요청 |
| ADMIN | 관리자 | 사용자, Master, Backup, Audit Log, 시스템 상태 관리 |

## 3. 로그인 방법

1. 시스템 URL에 접속합니다.
2. 사용자 ID와 비밀번호를 입력합니다.
3. 로그인 후 우측 상단에서 본인의 표시명과 Role을 확인합니다.
4. 초기 비밀번호는 운영 시작 전에 반드시 변경합니다.

초기 계정 예시는 다음과 같습니다.

- `admin` / `admin1234`
- `staff` / `staff1234`
- `team_manager` / `manager1234`
- `director` / `director1234`
- `ceo` / `ceo1234`

## 4. 담당자 업무 절차

1. `Upload` 메뉴로 이동합니다.
2. Profit Sheet PDF 또는 Excel 파일을 선택하고 업로드합니다.
3. `Map to Case`를 실행하여 시스템이 추출한 결재 초안을 확인합니다.
4. 고객명, 거래구분, 업무구분, 운송/통관 여부, 매출/원가 항목을 확인합니다.
5. 추출값이 실제 Profit Sheet와 다르면 화면에서 직접 수정합니다.
6. `Analyze Edited Case`를 실행합니다.
7. AI Decision, GP, GP율, Minimum GP, Findings를 확인합니다.
8. 문제가 없거나 보완 후 `Analyze & Save Edited Case`를 실행합니다.
9. 저장된 결재건 상세 화면에서 `결재상신`을 실행합니다.
10. 보완요청을 받으면 지적사항을 확인하고 수정 후 재상신합니다.

담당자는 AI 분석 결과를 그대로 믿기보다 Profit Sheet 원본과 비교하여 금액과 업무구분이 맞는지 반드시 확인해야 합니다.

## 5. 팀장 업무 절차

1. `Workflows` 메뉴로 이동합니다.
2. `SUBMITTED` 상태의 결재건을 확인합니다.
3. AI Decision이 `APPROVED`인지, `CONDITIONAL_APPROVED`인지, `CEO_REVIEW`인지 확인합니다.
4. Findings에서 Minimum GP, 운송마진, 통관수익, Partner Fee, 비용누락, 자사자원 경고를 확인합니다.
5. 필요하면 결재심사서 PDF 또는 ERP Payload를 확인합니다.
6. 이상이 없으면 `Team Approve`를 실행합니다.
7. 정보가 부족하면 `Return`으로 보완요청합니다.
8. 수익성이나 기준 위반이 명확하면 `Reject`로 반려합니다.

## 6. 본부장 업무 절차

1. `Workflows` 메뉴에서 `TEAM_APPROVED` 상태 건을 확인합니다.
2. 저마진, 대표검토, 조건부승인 안건을 우선 확인합니다.
3. Dashboard의 Low Margin 또는 Approval Detail의 Findings를 확인합니다.
4. 필요 시 Summary PDF, Detail PDF, ERP Payload를 확인합니다.
5. 문제가 없으면 `Director Approve`를 실행합니다.
6. 추가 확인이 필요하면 `Return`으로 보완요청합니다.
7. 진행하면 안 되는 안건은 `Reject`로 반려합니다.

## 7. 대표 업무 절차

1. `Workflows` 메뉴에서 `DIRECTOR_APPROVED` 상태 건을 확인합니다.
2. `Summary PDF`를 열어 1페이지 요약을 확인합니다.
3. GP, GP율, 실GP율, Minimum GP 충족 여부를 확인합니다.
4. 대표검토 사유와 주요 Findings를 확인합니다.
5. Dashboard에서 현재 월 실적, 저마진 안건, 담당자별 생산성을 확인합니다.
6. 최종 승인할 경우 `CEO Approve`를 실행합니다.
7. 수익성 부족 또는 정책 위반이 있으면 `Reject`로 반려합니다.
8. 자료 보완이 필요하면 `Return`으로 보완요청합니다.

## 8. 관리자 업무 절차

관리자는 `Admin`과 `Masters` 메뉴를 중심으로 시스템 운영 기준을 관리합니다.

- User 관리: 사용자 생성, Role 변경, 비활성화
- Master 관리: Minimum GP, Partner Fee, 업무코드/Point, 필수 청구항목, Parser Template 관리
- Parser Validation: 실제 샘플 Profit Sheet 파싱 결과 검증
- Parser Improvement: 검증 실패 결과 기반 개선 제안 확인
- Backup: DB 백업 실행 및 백업 파일 확인
- Audit Log: 주요 변경, Export, Workflow 처리 기록 확인
- System Status: DB, uploads, reports, logs, backup 폴더 상태 확인
- Integrations: ERP/회계 연동 설정 및 JSON Export 이력 확인

## 9. AI Decision 의미

| Decision | 의미 | 업무상 해석 |
|---|---|---|
| APPROVED | 기준 충족 | 일반 승인 가능 |
| CONDITIONAL_APPROVED | 조건부승인 | 일부 WARN이 있어 조건 확인 후 승인 가능 |
| CEO_REVIEW | 대표검토 필요 | Minimum GP 미달, 비용누락 등 중요 확인 필요 |
| REJECTED | 반려 권고 | GP가 음수 등 진행 부적합 가능성이 큼 |

AI Decision은 시스템 판정이며, 최종 조직 결재 상태와는 별개입니다.

## 10. Workflow Status 의미

| Status | 의미 |
|---|---|
| DRAFT | 저장되었으나 아직 상신 전 |
| SUBMITTED | 담당자가 상신 완료 |
| TEAM_APPROVED | 팀장 승인 완료 |
| DIRECTOR_APPROVED | 본부장 승인 완료 |
| CEO_APPROVED | 대표 최종 승인 완료 |
| REJECTED | 결재 반려 |
| RETURNED | 보완요청 상태 |

## 11. Dashboard 사용법

Dashboard 기본 화면은 현재 월 실적만 표시합니다.

확인 항목:

- 총 결재건수
- 총매출, 총원가, 총 GP
- 평균 GP율
- Decision별 건수
- 담당자별 생산성 Point
- 거래처별 GP
- Partner별 수익성
- 저마진/대표검토 대상

상세 화면에서는 월별 실적, 기간별 실적, 담당자, 거래구분, 업무코드, 파트너, 고객명 조건으로 조회할 수 있습니다.

## 12. Quotes 사용법

1. `Quotes` 메뉴로 이동합니다.
2. 고객명, 거래구분, 운송모드, 수출입, 업무코드, POL/POD/PORT, 컨테이너 정보를 입력합니다.
3. 통관, 운송, 창고 포함 여부를 선택합니다.
4. 필요 시 수동 운송원가, 통관원가, Partner Fee를 입력합니다.
5. `견적 생성`을 실행합니다.
6. 추천 청구액, 예상 원가, 예상 GP, GP율, Minimum GP 반영 여부를 확인합니다.
7. `견적 생성 및 저장`을 실행하면 견적 이력에 저장됩니다.

견적은 Tariff DB와 Master Rule을 기반으로 산출되므로, 데이터가 부족한 경우 검토 필요 경고가 표시될 수 있습니다.

## 13. PDF / Excel 출력

사용 가능한 출력 기능:

- 결재심사서 Summary PDF
- 결재심사서 Detail PDF
- Markdown 결재심사서
- Dashboard Excel
- 결재이력 Excel
- 운송 Tariff Excel
- 통관 Tariff Excel
- 견적이력 Excel
- 생산성 Excel
- ERP/회계 연동용 JSON

Excel Export와 ERP JSON Export는 권한이 있는 사용자만 실행할 수 있습니다.

## 14. 자주 발생하는 오류

### 파일 업로드 실패

- PDF, XLSX, XLS 확장자인지 확인합니다.
- 파일이 열려 있거나 손상되지 않았는지 확인합니다.

### 파싱 결과 오류

- Profit Sheet 양식이 기존 Template과 다를 수 있습니다.
- Map to Case 후 반드시 수동 확인 및 수정합니다.
- 반복적으로 틀리는 경우 관리자에게 Parser Validation 등록을 요청합니다.

### 권한 없음

- 현재 로그인 Role로 실행할 수 없는 기능입니다.
- 팀장 승인, 본부장 승인, 대표 승인, Export 기능은 Role 제한이 있습니다.

### PDF 한글 깨짐

- 서버에 NanumGothic 또는 NotoSansCJK 등 한글 폰트 설치가 필요할 수 있습니다.

### DB 연결 오류

- 관리자에게 System Status 확인을 요청합니다.
- PostgreSQL 운영환경에서는 DATABASE_URL 설정을 확인해야 합니다.

## 15. 운영 체크리스트

매일 확인:

- DB Backup 실행 여부
- Audit Log 이상 여부
- 저마진 및 대표검토 안건
- RETURNED 상태 장기 미처리 건

매주 확인:

- Parser Validation 결과
- Parser Improvement 제안
- Master Rule 변경 이력
- Partner Fee Rule 최신성
- Tariff DB 축적 현황

월말 확인:

- Dashboard 월별 실적
- 담당자별 생산성 Point
- 거래처별 GP
- Partner별 수익성
- Excel Export 백업 보관
