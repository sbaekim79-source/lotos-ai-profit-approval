# LOTOS AI Profit Approval System 교육자료

## 1. 교육 목적

본 교육은 실제 사용자가 LOTOS AI Profit Approval System을 이용하여 Profit Sheet 업로드부터 AI 결재심사, Workflow 승인, Dashboard 확인, PDF/Excel 출력까지 수행할 수 있도록 하는 것을 목적으로 합니다.

교육 후 사용자는 다음 업무를 수행할 수 있어야 합니다.

- Profit Sheet 업로드
- 자동 파싱 및 Map to Case 실행
- 추출값 수동수정
- AI Analyze 및 Findings 확인
- Analyze & Save
- 결재상신 및 승인
- Dashboard 조회
- 결재심사서 PDF 출력
- Excel Export

## 2. 교육 대상

- 담당자 STAFF
- 팀장 TEAM_MANAGER
- 본부장 DIRECTOR
- 대표 CEO
- 관리자 ADMIN

## 3. 1시간 교육 과정

| 시간 | 내용 | 대상 |
|---|---|---|
| 0~10분 | 시스템 개요 및 Role 설명 | 전체 |
| 10~25분 | Profit Sheet 업로드, Map to Case, 수동수정 | 담당자 |
| 25~35분 | AI Analyze, Findings, Analyze & Save | 담당자, 팀장 |
| 35~45분 | Workflow 상신/승인/보완요청/반려 | 전체 |
| 45~52분 | Dashboard, PDF, Excel Export | 팀장, 본부장, 대표 |
| 52~58분 | Admin, Backup, Audit Log, Parser Validation | 관리자 |
| 58~60분 | Q&A 및 운영 체크리스트 안내 | 전체 |

## 4. 실습 준비

교육 전 준비사항:

- 교육용 사용자 계정 준비
- 샘플 Profit Sheet PDF 또는 Excel 준비
- Backend/Frontend 실행 확인
- Master Seed 완료
- 테스트용 DB Backup 완료

권장 실습 계정:

- 담당자: `staff`
- 팀장: `team_manager`
- 본부장: `director`
- 대표: `ceo`
- 관리자: `admin`

## 5. 실습 시나리오 1 - 샘플 Profit Sheet 업로드

1. `staff`로 로그인합니다.
2. `Upload` 메뉴로 이동합니다.
3. 샘플 Profit Sheet 파일을 업로드합니다.
4. 업로드 성공 후 upload_id가 표시되는지 확인합니다.
5. `Map to Case`를 실행합니다.
6. Template, Confidence, Warning을 확인합니다.

확인 포인트:

- 파일 확장자가 PDF/XLSX/XLS인지 확인
- 고객명과 업무구분이 자동 추출되었는지 확인
- Confidence가 낮으면 수동수정 필요

## 6. 실습 시나리오 2 - 자동추출값 수동수정

1. 기본정보에서 고객명, 거래구분, 파트너명을 확인합니다.
2. 업무구분에서 SEA/AIR, EXPORT/IMPORT, 통관/운송 여부를 확인합니다.
3. Revenue Items와 Expense Items 금액을 원본 Profit Sheet와 비교합니다.
4. 틀린 금액은 직접 수정합니다.
5. 필요하면 Revenue/Expense 행을 추가하거나 삭제합니다.

확인 포인트:

- TOTAL Revenue와 TOTAL Expense가 맞는지 확인
- 관세와 소비세가 대납성 금액으로 분리되었는지 확인
- 운송 매출/원가, 통관 매출/원가가 맞는지 확인

## 7. 실습 시나리오 3 - AI 결재심사

1. `Analyze Edited Case`를 클릭합니다.
2. AI Decision을 확인합니다.
3. Findings Table을 확인합니다.
4. Minimum GP, 운송마진, 통관수익, Partner Fee, 비용누락, 자사자원 항목을 설명합니다.
5. 문제 없으면 `Analyze & Save Edited Case`를 클릭합니다.

기대 결과:

- 저장 후 approval_case_id가 생성됩니다.
- 결재 상세 화면에서 결과를 확인할 수 있습니다.

## 8. 실습 시나리오 4 - 결재상신

1. 저장된 결재 상세 화면으로 이동합니다.
2. `결재상신` 버튼을 클릭합니다.
3. `Workflows` 메뉴에서 해당 건이 `SUBMITTED` 상태인지 확인합니다.

확인 포인트:

- STAFF는 본인 건을 상신할 수 있습니다.
- STAFF는 승인 버튼을 사용할 수 없습니다.

## 9. 실습 시나리오 5 - 팀장승인

1. `team_manager`로 로그인합니다.
2. `Workflows` 메뉴로 이동합니다.
3. `SUBMITTED` 상태 결재건을 선택합니다.
4. AI Decision과 Findings를 확인합니다.
5. 문제가 없으면 `Team Approve`를 클릭합니다.
6. 보완이 필요하면 `Return`, 반려가 필요하면 `Reject`를 설명합니다.

기대 결과:

- 승인 시 상태가 `TEAM_APPROVED`로 변경됩니다.

## 10. 실습 시나리오 6 - 본부장/대표 승인

1. `director`로 로그인하여 `TEAM_APPROVED` 건을 승인합니다.
2. `ceo`로 로그인하여 `DIRECTOR_APPROVED` 건을 확인합니다.
3. Summary PDF를 생성하고 다운로드합니다.
4. 대표 승인 시 `CEO_APPROVED` 상태가 되는지 확인합니다.

## 11. 실습 시나리오 7 - Dashboard 조회

1. `Dashboard` 메뉴로 이동합니다.
2. 현재 월 실적을 확인합니다.
3. Monthly Performance 탭에서 월별 실적을 확인합니다.
4. Productivity 탭에서 담당자별 Point를 확인합니다.
5. Low Margin 탭에서 저마진 안건을 확인합니다.
6. 기간, 담당자, 거래구분, 업무코드 필터를 변경하여 조회합니다.

## 12. 실습 시나리오 8 - PDF / Excel 출력

1. Approval Detail에서 Summary PDF와 Detail PDF를 생성합니다.
2. Dashboard에서 Dashboard Excel과 Productivity Excel을 다운로드합니다.
3. Approvals에서 결재이력 Excel을 다운로드합니다.
4. Quotes에서 견적이력 Excel을 다운로드합니다.
5. Admin에서 운송/통관 Tariff Excel을 다운로드합니다.

권한 설명:

- Excel Export는 TEAM_MANAGER, DIRECTOR, CEO, ADMIN 권한이 필요합니다.
- STAFF는 Export 권한이 없습니다.

## 13. 실습 시나리오 9 - 관리자 기능

1. `admin`으로 로그인합니다.
2. `Masters`에서 Work Code, Minimum GP, Partner Fee Rule을 확인합니다.
3. `Admin`에서 System Status를 확인합니다.
4. DB Backup을 실행합니다.
5. Audit Log를 조회합니다.
6. Integrations에서 ERP 설정과 JSON Export를 확인합니다.
7. Operation Test에서 테스트 결과를 등록합니다.

## 14. Q&A

자주 묻는 질문:

### Q. AI Decision이 APPROVED이면 바로 최종 승인인가요?

아닙니다. AI Decision은 시스템 심사 결과이며, 실제 조직 결재는 Workflow Status로 별도 관리됩니다.

### Q. 파싱 결과가 틀리면 어떻게 하나요?

담당자가 화면에서 직접 수정한 뒤 Analyze를 실행합니다. 반복 오류는 관리자에게 Parser Validation 등록을 요청합니다.

### Q. PDF 한글이 깨지면 어떻게 하나요?

서버에 NanumGothic 또는 NotoSansCJK 폰트를 설치해야 합니다.

### Q. 대표검토는 어떤 경우 발생하나요?

Minimum GP 미달, 비용누락, 자사자원 NG 등 중요 기준 위반 시 발생할 수 있습니다.

### Q. Export 파일은 어디에 저장되나요?

Excel과 JSON Export 파일은 `backend/exports` 아래에 저장됩니다.

## 15. 교육 완료 체크

교육 후 각 사용자는 아래 항목을 수행해 봅니다.

| 항목 | 완료 |
|---|---|
| 로그인 및 비밀번호 변경 |
| Profit Sheet 업로드 |
| Map to Case 실행 |
| 수동수정 |
| Analyze 실행 |
| Analyze & Save |
| 결재상신 |
| 팀장승인 |
| Dashboard 조회 |
| PDF 출력 |
| Excel Export |
| Backup 및 Audit Log 확인 |
