# LOTOS AI Profit Approval System 관리자 매뉴얼
## 1. 紐⑹쟻

??臾몄꽌??LOTOS AI Profit Approval System???댁쁺 ?섍꼍?먯꽌 ?ㅼ튂, ?ㅽ뻾, ?먭?, 諛깆뾽, ?μ븷 ??묓븯湲??꾪븳 愿由ъ옄???덉감?쒖엯?덈떎.

## 2. ?쒖뒪??援ъ꽦

- Backend: Python, FastAPI
- Frontend: React, TypeScript, Vite
- Database: SQLite ?먮뒗 PostgreSQL
- API 臾몄꽌: Swagger `/docs`
- 諛고룷: Docker Compose
- 二쇱슂 ????대뜑:
  - ?낅줈???뚯씪: `backend/uploads`
  - PDF 蹂닿퀬?? `backend/generated_reports`
  - Excel/JSON Export: `backend/exports`
  - 濡쒓렇: `backend/logs`
  - DB 諛깆뾽: `backend/backups`

## 3. ?ㅼ튂 諛⑸쾿

### Backend 濡쒖뺄 ?ㅼ튂

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

### Frontend 濡쒖뺄 ?ㅼ튂

```bash
cd frontend
pnpm install
pnpm run dev
```

?묒냽:

- Backend Swagger: `http://localhost:8010/docs`
- Frontend: `http://localhost:5173`

## 4. Docker ?ㅽ뻾

```bash
docker compose up --build
```

Docker ?ㅽ뻾 ??Backend, Frontend, PostgreSQL ?쒕퉬?ㅻ? ?④퍡 湲곕룞?????덉뒿?덈떎.

## 5. PostgreSQL ?ㅼ젙

?댁쁺 ?섍꼍?먯꽌??PostgreSQL ?ъ슜??沅뚯옣?⑸땲??

?덉떆 DATABASE_URL:

```text
postgresql+psycopg2://lotos_user:lotos_password@postgres:5432/lotos_ai_approval
```

docker-compose 湲곕낯媛?

- DB: `lotos_ai_approval`
- User: `lotos_user`
- Password: `lotos_password`
- Port: `5432`

?댁쁺 諛고룷 ??鍮꾨?踰덊샇??諛섎뱶??蹂寃쏀빀?덈떎.

## 6. .env ?ㅼ젙

?꾨줈?앺듃 猷⑦듃??`.env.example`??李멸퀬?섏뿬 `.env`瑜??묒꽦?⑸땲??

二쇱슂 ??ぉ:

```text
DATABASE_URL=sqlite:///./lotos_ai_approval.db
APP_ENV=development
SECRET_KEY=change-this-secret
UPLOAD_DIR=backend/uploads
REPORT_DIR=backend/generated_reports
LOG_DIR=backend/logs
BACKUP_DIR=backend/backups
EXPORT_DIR=backend/exports
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

?댁쁺 ?섍꼍?먯꽌???ㅼ쓬??諛섎뱶??蹂寃쏀빀?덈떎.

- `APP_ENV=production`
- `SECRET_KEY`
- PostgreSQL `DATABASE_URL`
- DB 怨꾩젙 鍮꾨?踰덊샇

## 7. Master Seed

珥덇린 Master ?곗씠?곗? 湲곕낯 ?ъ슜?먮? ?앹꽦?⑸땲??

Swagger ?먮뒗 API:

```http
POST /api/masters/seed-defaults
```

Seed ???

- Minimum GP
- Partner Fee
- GP Rate
- Work Code / Point
- Internal Resource Rule
- Required Charge Rule
- Parser Template
- Parser Validation Case
- 湲곕낯 ?ъ슜??
## 8. User ?앹꽦 諛?沅뚰븳愿由?
愿由ъ옄??`Masters` ?먮뒗 User API?먯꽌 ?ъ슜?먮? 愿由ы빀?덈떎.

Role:

- STAFF
- TEAM_MANAGER
- DIRECTOR
- CEO
- ADMIN

珥덇린 ?ъ슜?먮뒗 ?댁쁺 ?쒖옉 ??鍮꾨?踰덊샇瑜?蹂寃쏀빐???⑸땲??

?ъ슜??鍮꾪솢?깊솕???ㅼ젣 ??젣媛 ?꾨땲??`is_active=False` 泥섎━?낅땲??

## 9. DB Backup

### SQLite

Admin ?붾㈃ ?먮뒗 API?먯꽌 ?ㅽ뻾?⑸땲??

```http
POST /api/admin/backup-db
```

諛깆뾽 ?뚯씪? `backend/backups`???앹꽦?⑸땲??

### PostgreSQL

PostgreSQL? `pg_dump` ?ъ슜??沅뚯옣?⑸땲??

```bash
pg_dump -h localhost -U lotos_user lotos_ai_approval > backup.sql
```

?댁쁺?섍꼍?먯꽌?????⑥쐞 ?먮룞 諛깆뾽 ?ㅼ?以꾩쓣 援ъ꽦?⑸땲??

## 10. Log ?뺤씤

濡쒓렇 ?꾩튂:

- ?쇰컲 濡쒓렇: `backend/logs/app.log`
- ?먮윭 濡쒓렇: `backend/logs/error.log`

?뺤씤 ??ぉ:

- 500 ?먮윭 諛쒖깮 ?щ?
- API ?묐떟?쒓컙 利앷? ?щ?
- ?몄쬆 ?ㅽ뙣 諛섎났 ?щ?
- ?뚯씪 ?낅줈??Export ?ㅽ뙣 ?щ?

## 11. ?μ븷 ???
### Frontend ?묒냽 遺덇?

1. Frontend ?꾨줈?몄뒪 ?먮뒗 而⑦뀒?대꼫 ?곹깭 ?뺤씤
2. `http://localhost:5173` ?묎렐 ?뺤씤
3. `VITE_API_BASE_URL` ?ㅼ젙 ?뺤씤

### Backend ?묒냽 遺덇?

1. Backend ?꾨줈?몄뒪 ?먮뒗 而⑦뀒?대꼫 ?곹깭 ?뺤씤
2. `/health` ?몄텧 ?뺤씤
3. `backend/logs/error.log` ?뺤씤

### DB ?곌껐 ?ㅻ쪟

1. `/api/admin/system-status` ?뺤씤
2. DATABASE_URL ?뺤씤
3. PostgreSQL 而⑦뀒?대꼫 ?곹깭 ?뺤씤
4. DB 怨꾩젙/鍮꾨?踰덊샇 ?뺤씤

### ?뚯씪 ?낅줈???ㅽ뙣

1. `backend/uploads` ?대뜑 議댁옱 ?щ? ?뺤씤
2. ?뚯씪 沅뚰븳 ?뺤씤
3. ?덉슜 ?뺤옣???뺤씤

### PDF ?쒓? 源⑥쭚

?쒕쾭???쒓? ?고듃瑜??ㅼ튂?⑸땲??

沅뚯옣:

- NanumGothic
- NotoSansCJK
- Malgun Gothic

## 12. Alembic Migration

媛쒕컻?섍꼍?먯꽌??`Base.metadata.create_all`濡??뚯씠釉붿쓣 ?먮룞 ?앹꽦?????덉뒿?덈떎.

?댁쁺?섍꼍?먯꽌??Alembic migration ?ъ슜??沅뚯옣?⑸땲??

```bash
cd backend
alembic revision --autogenerate -m "schema update"
alembic upgrade head
```

?댁쁺 DB 諛섏쁺 ?꾩뿉??諛섎뱶??諛깆뾽???섑뻾?⑸땲??

## 13. ?댁쁺 諛고룷 ???뺤씤?ы빆

- `.env` ?댁쁺媛??ㅼ젙 ?꾨즺
- `SECRET_KEY` 蹂寃??꾨즺
- PostgreSQL ?곌껐 ?뺤씤
- Alembic migration ?곸슜
- `/health` ?뺤긽
- `/api/admin/system-status` ?뺤긽
- 湲곕낯 Master Seed ?꾨즺
- 湲곕낯 ?ъ슜??鍮꾨?踰덊샇 蹂寃?- Backup ?대뜑 諛??ㅼ?以??뺤씤
- 濡쒓렇 ?대뜑 沅뚰븳 ?뺤씤
- PDF ?쒓? ?고듃 ?뺤씤
- ?섑뵆 Profit Sheet濡?Upload, Analyze, Save, Workflow, PDF 異쒕젰 ?뚯뒪??- Excel Export 諛?ERP JSON Export ?뚯뒪??
## 14. ?댁쁺 以??뺢린?먭?

留ㅼ씪:

- Backup ?앹꽦 ?щ?
- Error Log ?뺤씤
- Audit Log 二쇱슂 ?대깽???뺤씤

留ㅼ＜:

- Parser Validation 寃곌낵 ?뺤씤
- Parser Improvement ?쒖븞 寃??- Master Rule 蹂寃??대젰 ?뺤씤
- Tariff DB 異뺤쟻 ?곗씠???뺤씤

留ㅼ썡:

- Dashboard ?붾퀎 ?ㅼ쟻 Export
- ?앹궛??Point ?뺤씤
- ?留덉쭊 ?덇굔 遺꾩꽍
- DB 諛깆뾽 蹂닿? ?뺤콉 ?먭?
