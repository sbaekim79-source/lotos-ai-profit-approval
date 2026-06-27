# LOTOS AI Profit Approval System

Profit Sheet(P/L Sheet)瑜??낅줈?쒗븯硫?AI Rule Engine???섏씡?깆쓣 ?먮룞 ?ъ궗?섍퀬 `?뱀씤 / 議곌굔遺?뱀씤 / ??쒓???/ 諛섎젮` 寃곌낵瑜?異쒕젰?섎뒗 MVP ?쒖뒪?쒖엯?덈떎.

## 二쇱슂 湲곕뒫

- PDF / Excel Profit Sheet ?낅줈??- PDF / Excel raw text / table 異붿텧
- Profit Sheet ?먮룞 留ㅽ븨 ?꾨낫 ?앹꽦
- ?ъ슜?먭? 寃곗옱 ???꾨낫媛??섏젙
- ?섏젙??寃곗옱嫄?遺꾩꽍 諛?DB ???- 寃곗옱 ?대젰 議고쉶
- ??쒖씠??Dashboard
- Tariff DB 議고쉶
- Partner Fee / Minimum GP Master 愿由?- ??쒖씠??蹂닿퀬??Markdown 寃곗옱?ъ궗???앹꽦 諛??ㅼ슫濡쒕뱶

## ?쒖뒪??援ъ“

```text
lotos-ai-approval/
  backend/
    app/
      main.py
      schemas.py
      models.py
      database.py
      routers/
      services/
      sample_cases.py
    tests/
    uploads/
    requirements.txt
    Dockerfile
  frontend/
    src/
      api/
      components/
      pages/
    package.json
    Dockerfile
  docker-compose.yml
```

## ?ㅽ뻾 諛⑸쾿

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

?묒냽:

- Frontend: http://localhost:5173
- Swagger: http://localhost:8010/docs

Backend는 `8010`, Frontend는 `5173` 포트로 고정합니다. Frontend API URL은 `VITE_API_BASE_URL=http://localhost:8010` 기준입니다.

Docker:

```bash
docker compose up --build
```

## Backend API 紐⑸줉

System:

- `GET /health`
- `GET /api/db/status`

Upload / Parsing:

- `POST /api/uploads/profit-sheet`
- `GET /api/uploads`
- `GET /api/uploads/{upload_id}`
- `POST /api/uploads/{upload_id}/parse`
- `POST /api/uploads/{upload_id}/map-to-case`
- `POST /api/uploads/{upload_id}/analyze`
- `POST /api/uploads/{upload_id}/analyze-and-save`

Approval:

- `POST /api/approvals/analyze`
- `POST /api/approvals/analyze-and-save`
- `GET /api/approvals`
- `GET /api/approvals/{approval_case_id}`
- `GET /api/approvals/{approval_case_id}/report`
- `POST /api/approvals/analyze-sample/{sample_key}`
- `POST /api/approvals/analyze-sample-and-save/{sample_key}`

Dashboard:

- `GET /api/dashboard/summary`
- `GET /api/dashboard/monthly`
- `GET /api/dashboard/productivity`
- `GET /api/dashboard/low-margin`

`/api/dashboard/summary`? `/api/dashboard/low-margin`? 湲곕낯?곸쑝濡??꾩옱 ???ㅼ쟻留?議고쉶?⑸땲?? 湲곌컙??吏?뺥븯?ㅻ㈃ `start_date`, `end_date` query parameter瑜??ъ슜?⑸땲??

?붾퀎 ?ㅼ쟻 議고쉶:

```bash
curl "http://localhost:8010/api/dashboard/monthly?start_month=2026-01&end_month=2026-06"
```

Tariff:

- `GET /api/tariffs/transport`
- `GET /api/tariffs/transport/summary`
- `GET /api/tariffs/customs`
- `GET /api/tariffs/customs/summary`
- `GET /api/tariffs/warehouse`

Master:

- `POST /api/masters/seed-defaults`
- `GET /api/masters/partner-fees`
- `POST /api/masters/partner-fees`
- `GET /api/masters/minimum-gp`
- `POST /api/masters/minimum-gp`
- `GET /api/masters/gp-rate-rules`
- `POST /api/masters/gp-rate-rules`
- `GET /api/masters/work-code-rules`
- `POST /api/masters/work-code-rules`
- `GET /api/masters/internal-resource-rules`
- `POST /api/masters/internal-resource-rules`
- `GET /api/masters/required-charge-rules`
- `POST /api/masters/required-charge-rules`
- `PUT /api/masters/required-charge-rules/{rule_id}`
- `DELETE /api/masters/required-charge-rules/{rule_id}`

## Frontend ?붾㈃

- Dashboard: ?꾩옱 ??寃곗옱嫄댁닔, 珥앸ℓ異? 珥앹썝媛, 珥?GP, ?됯퇏 GP?? Decision 吏묎퀎, ?대떦?먮퀎 ?앹궛?? 怨좉컼蹂?GP, Partner Summary ?쒖떆
- Monthly: ?쒖옉 ??醫낅즺 ?붿쓣 ?좏깮?섏뿬 ?붾퀎 留ㅼ텧, ?먭?, GP, GP?? Decision 嫄댁닔, ?대떦???앹궛??議고쉶
- Upload: Profit Sheet ?낅줈?? ?먮룞 留ㅽ븨, editable form ?섏젙, 遺꾩꽍, ??? 寃곗옱?ъ궗???ㅼ슫濡쒕뱶
- Approvals: ??λ맂 寃곗옱 ?대젰 紐⑸줉怨??곸꽭 議고쉶
- Approval Detail: ?섏씡???뺣낫, Findings, ??쒖씠??寃곗옱?ъ궗??蹂닿린 諛?Markdown ?ㅼ슫濡쒕뱶
- Masters: 湲곕낯 Partner Fee / Minimum GP Master Seed 諛?議고쉶

?먮룞?뚯떛 寃곌낵??諛섎뱶??寃곗옱 ???뺤씤 諛??섏젙 媛?ν븯?꾨줉 ?ㅺ퀎?섏뼱 ?덉쑝硫? ?대뒗 Profit Sheet ?묒떇 李⑥씠濡??명븳 ?ㅽ뙋?뺤쓣 諛⑹??섍린 ?꾪븳 湲곕뒫?낅땲??

## 寃곗옱 湲곗?

2李?媛쒕컻遺??寃곗옱 湲곗?? 肄붾뱶 ?섎뱶肄붾뵫???꾨땲??Master DB 湲곗??쇰줈 ?댁쁺?⑸땲?? ?? Master 媛믪씠 ?놁쓣 寃쎌슦 ?쒖뒪???덉젙?깆쓣 ?꾪빐 湲곕낯 fallback rule???ъ슜?⑸땲??

理쒖쥌 Decision:

- GP < 0: `REJECTED`
- ?꾨줈?앺듃 ?덇굔: `CEO_REVIEW`
- Minimum GP 誘몃떖: `CEO_REVIEW`
- Minimum GP 遺議깆븸??湲곗???10% ?대궡: `CONDITIONAL_APPROVED`
- ?댁넚留덉쭊 NG: `CONDITIONAL_APPROVED`
- 鍮꾩슜?꾨씫 WARN 議댁옱: `CEO_REVIEW`
- Partner Fee WARN 議댁옱: `CONDITIONAL_APPROVED`
- 洹???WARN 議댁옱: `CONDITIONAL_APPROVED`
- NG/WARN ?놁쓬: `APPROVED`

?짨P??湲곗?:

- SHIPPER: 15%
- FORWARDER: 10%
- PARTNER: 5%

## ?낅Т肄붾뱶 湲곗?

?꾨줈?앺듃:

- `is_project=True`: `PJT`

?댁긽:

- SEA EXPORT: `SE`
- SEA IMPORT: `SI`

??났:

- AIR EXPORT: `AE`
- AIR IMPORT: `AI`

遺媛 ?낅Т:

- ?듦? ?ы븿: `+`
- ?댁넚 ?ы븿: `++`
- ?묒뾽 ?ы븿: `+++`

?곗꽑?쒖쐞???묒뾽, ?댁넚, ?듦? ?쒖엯?덈떎.

## Minimum GP 湲곗?

| Code | Minimum GP |
|---|---:|
| SE | JPY 6,000 |
| SE+ | JPY 19,900 |
| SE++ | JPY 22,900 |
| SE+++ | JPY 22,900 |
| SI | JPY 8,000 |
| SI+ | JPY 27,800 |
| SI++ | JPY 30,800 |
| SI+++ | JPY 30,800 |
| AE | JPY 6,000 |
| AE+ | JPY 14,000 |
| AE++ | JPY 17,000 |
| AE+++ | JPY 17,000 |
| AI | JPY 6,000 |
| AI+ | JPY 14,000 |
| AI++ | JPY 17,000 |
| AI+++ | JPY 17,000 |

## Partner Fee 湲곗?

?꾩옱 MVP??Rule Engine??肄붾뱶 洹쒖튃怨?Master DB Seed ?곗씠?곕? ?④퍡 ?쒓났?⑸땲??

- ?쒖썒濡쒖쭅??SEA EXPORT: USD 20 / B/L, LOTOS_COLLECT
- J2K GLOBAL SEA EXPORT 20FT: USD 20 / CNTR, LOTOS_COLLECT
- J2K GLOBAL SEA EXPORT 40FT: USD 40 / CNTR, LOTOS_COLLECT
- J2K MIZUSHIMA NAKASHIMA: USD 500 / B/L, LOTOS_COLLECT
- J2K GLOBAL SEA IMPORT 20FT LOTOS NOMI/HANKUK: USD 50 / CNTR, PARTNER_CREDIT
- PNS NETWORKS EXPORT 40FT: USD 15 / CNTR, LOTOS_COLLECT
- DONGSHIN SEA & AIR IMPORT: JPY 4,000 / SHIPMENT, PARTNER_PAY
- EUNSAN IMPORT: USD 15 / B/L, PARTNER_PAY
- ?숈썝濡쒖뿊??EXPORT: USD 20 / SHIP, LOTOS_COLLECT
- ?숈썝濡쒖뿊??ITOCHU EXPORT: USD 10 / B/L, LOTOS_COLLECT

## Required Charge Master

?꾩닔 泥?뎄??ぉ Master???낅Т肄붾뱶, ?섏텧?? ?듦?/?댁넚/?앺뭹 ?щ????곕씪 諛섎뱶???뺤씤?댁빞 ??泥?뎄??ぉ???뺤쓽?섎ŉ, AI 寃곗옱 ???꾨씫 ?щ?瑜??먮룞?쇰줈 寃쎄퀬?⑸땲??

湲곕낯 Seed?먮뒗 ?댁긽?섏텧 SE 怨꾩뿴??THC, DOC, B/L, AFR/AMS/ENS/ISPS, ?댁긽?섏엯 SI 怨꾩뿴??THC, DOC, D/O, DUTY, CONSUMPTION_TAX, ?듦? ?ы븿 ?덇굔??CUSTOMS, ?댁넚 ?ы븿 ?덇굔??TRANSPORT, ?앺뭹/?됰룞 ?붾Ъ??FOOD_DECLARATION ?뺤씤 ??ぉ???ы븿?⑸땲?? ?댁쁺?먮뒗 Master ?붾㈃??Required Charge Rules ?뱀뀡?먯꽌 ??ぉ??異붽?, ?섏젙, 鍮꾪솢?깊솕?????덉뒿?덈떎.

## Internal Resource Rule

LOTOS媛 蹂댁쑀???듦?, 李쎄퀬, ?댁넚 ?먯썝???곗꽑 ?ъ슜?섎룄濡?PORT蹂?Rule??愿由ы븯硫? ?몄＜ ?ъ슜 ???ъ쑀 ?낅젰 ?щ?瑜?AI媛 寃利앺빀?덈떎.

Internal Resource Master?먯꽌 `CUSTOMS`, `WAREHOUSE`, `TRANSPORT` ?먯썝 ?좏삎蹂꾨줈 PORT, ?꾩튂紐? ?낆껜紐? ?곗꽑?쒖쐞, ?꾩닔 ?ъ슜 ?щ?瑜?愿由ы븷 ???덉뒿?덈떎. `mandatory=True`??PORT?먯꽌 ?몃? ?듦?, ?몃? 李쎄퀬, ?몃? ?댁넚???ъ슜?섎뒗 寃쎌슦 ?ъ쑀媛 ?놁쑝硫?`?먯궗?먯썝 NG`濡???쒓?????곸씠 ?섎ŉ, ?ъ쑀媛 ?덉쑝硫?`WARN`?쇰줈 議곌굔遺?뱀씤 ??곸씠 ?⑸땲??

## Tariff DB

Tariff DB??寃곗옱 ?꾨즺 ?곗씠?곕? 湲곕컲?쇰줈 ?먮룞 異뺤쟻?섎ŉ, ?ν썑 PORT-?⑺뭹吏, ?쎌뾽吏-PORT, ?듦??낆껜蹂?鍮꾩슜, 李쎄퀬?낆껜蹂?鍮꾩슜???쒖? 寃ъ쟻 ?먮즺濡??쒖슜?섍린 ?꾪븳 湲곕뒫?낅땲??

??????

- ?댁넚 Tariff: port, origin, destination, container_type, cost, revenue, GP
- ?듦? Tariff: port, direction, self_customs, revenue, expense, GP
- 李쎄퀬 Tariff: placeholder ?쒓났

## ?앹궛??Point 湲곗?

?낅Т肄붾뱶蹂?Point:

- 湲곕낯 ?섏텧?? 1
- ?듦? ?ы븿: 1.5
- ?댁넚 ?ы븿: 2
- ?묒뾽 ?ы븿: 2.5
- ?꾨줈?앺듃: 0

?대떦?먮퀎 ?붽컙 ?깃툒:

- 120 ?댁긽: ?곗닔
- 80 ?댁긽 120 誘몃쭔: ?뺤긽
- 60 ?댁긽 80 誘몃쭔: 愿由?- 60 誘몃쭔: 媛쒖꽑

?낅Т肄붾뱶蹂?Point???대떦???앹궛???곗젙??吏곸젒 諛섏쁺?섎ŉ, ?댁쁺?먭? Master ?붾㈃?먯꽌 蹂寃쏀븷 ???덉뒿?덈떎. Master ?붾㈃??Work Code / Point ?뱀뀡?먯꽌 ?낅Т肄붾뱶 Rule??異붽?, ?섏젙, 鍮꾪솢?깊솕?????덉쑝硫?蹂寃쎈맂 Point???댄썑 ??λ릺??寃곗옱嫄댁쓽 Productivity Point??諛섏쁺?⑸땲??

## 寃곗옱?ъ궗??
寃곗옱?ъ궗?쒕뒗 ??쒖씠??蹂닿퀬?⑹쑝濡?Markdown ?뺤떇?쇰줈 ?앹꽦?섎ŉ, ?대? 寃곗옱?쒖뒪???먮뒗 硫붿씪 蹂몃Ц??蹂듭궗?섏뿬 ?ъ슜?????덉뒿?덈떎.

```bash
curl http://localhost:8010/api/approvals/{approval_case_id}/report
```

Frontend?먯꽌??Approval Detail ?먮뒗 Upload ???寃곌낵 ?붾㈃?먯꽌 `寃곗옱?ъ궗??蹂닿린`, `Markdown ?ㅼ슫濡쒕뱶` 踰꾪듉???ъ슜?⑸땲??

## ?뚯뒪??
Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run build
```

Docker:

```bash
docker compose up --build
```

## ?ν썑 媛쒖꽑?ы빆

- ?ㅼ젣 Profit Sheet ?묒떇蹂?Parser Template 異붽?
- Partner Fee Rule DB 議고쉶 湲곕컲 ?꾪솚 怨좊룄??- Minimum GP Rule DB 議고쉶 湲곕컲 ?꾪솚
- ?ъ슜??沅뚰븳愿由?- 寃곗옱 Workflow ?뱀씤???④퀎 異붽?
- PDF 寃곗옱??異쒕젰
- ERP/?뚭퀎?쒖뒪???곕룞
- 嫄곕━ 湲곕컲 ?댁넚 Tariff ?먮룞異붿쿇
- 嫄곕옒泥섎퀎 紐⑺몴 GP ?먮룞?ㅼ젙
 
## STEP 25 Dashboard

Dashboard 湲곕낯 ?붾㈃? ?꾩옱 ???ㅼ쟻留??쒖떆?쒕떎. ?곸꽭 硫붾돱?먯꽌???붾퀎 ?ㅼ쟻, 湲곌컙蹂??ㅼ쟻, ?대떦?먮퀎 ?앹궛?? ?留덉쭊 ?덇굔??議곌굔蹂꾨줈 議고쉶?????덈떎.

Dashboard API:

- `GET /api/dashboard/summary`
  - 湲곕낯媛? ?꾩옱 ??1??~ ?꾩옱??  - 湲곌컙 議곌굔: `start_date`, `end_date`, `work_month`
  - 異붽? 議곌굔: `pic`, `trade_type`, `code`, `partner_name`, `customer_name`
- `GET /api/dashboard/monthly-performance`
  - ?붾퀎 寃곗옱 ?ㅼ쟻 議고쉶
  - 議곌굔: `start_month`, `end_month`, `pic`, `trade_type`, `code`
- `GET /api/dashboard/productivity/monthly`
  - ?대떦?먮퀎 ?붽컙 ?앹궛??Point 議고쉶
  - 議곌굔: `start_month`, `end_month`, `pic`
- `GET /api/dashboard/low-margin`
  - ?留덉쭊, 議곌굔遺?뱀씤, ??쒓??? 諛섎젮 ???議고쉶
  - 湲곕낯媛? ?꾩옱 ??  - 議곌굔: `start_date`, `end_date`, `work_month`, `pic`, `trade_type`, `code`, `partner_name`, `customer_name`

Frontend Dashboard:

- Summary: ?꾩옱 ???먮뒗 ?좏깮 湲곌컙???꾩껜 ?붿빟
- Monthly Performance: ?붾퀎 留ㅼ텧, ?먭?, GP, Decision 吏묎퀎
- Productivity: ?대떦?먮퀎 ?붽컙 Point? ?깃툒
- Low Margin: ?留덉쭊 諛???쒓???????덇굔
- 湲곌컙 ?꾨━?? ?꾩옱 ?? ?꾩썡, ?대쾲 遺꾧린, ?ъ슜??吏??
?좎쭨/???뺤떇:

- ?좎쭨: `YYYY-MM-DD`
- ?? `YYYY-MM`
 
## STEP 26 Parser Template

Parser Template? Profit Sheet ?묒떇蹂??ㅼ썙?쒖? 異붿텧 湲곗???DB濡?愿由ы븯??湲곕뒫?대떎. ?ν썑 LOTOS ?쒖??묒떇, ?뚰듃?덈퀎 ?묒떇, Excel ?묒떇蹂꾨줈 Template??異붽??섏뿬 ?뚯떛 ?뺥솗?꾨? ?믪씪 ???덈떎.

湲곕낯 Template:

- `LOTOS_STANDARD_PDF`: PDF 怨듯넻 湲곕낯 Template
- `LOTOS_EXPORT_PDF`: ?섏텧 PDF??B/L, DOC, THC, AFR, AMS, ENS, ISPS ?ㅼ썙??媛뺥솕
- `LOTOS_IMPORT_PDF`: ?섏엯 PDF??D/O, DUTY, CONSUMPTION TAX, VAT ?ㅼ썙??媛뺥솕
- `LOTOS_EXCEL`: Excel Profit Sheet??怨듯넻 Template

Master API:

- `GET /api/masters/parser-templates`
- `POST /api/masters/parser-templates`
- `PUT /api/masters/parser-templates/{template_id}`
- `DELETE /api/masters/parser-templates/{template_id}`

?낅줈???먮룞 留ㅽ븨 API???좏깮??Template ?뺣낫瑜??④퍡 諛섑솚?쒕떎.

```json
{
  "template_used": {
    "template_name": "LOTOS_IMPORT_PDF",
    "file_type": "PDF",
    "direction": "IMPORT"
  }
}
```
 
## STEP 27 Quote API

寃ъ쟻 ?먮룞?앹꽦 湲곕뒫? 寃곗옱瑜??듯빐 異뺤쟻??Tariff DB? Master Rule???쒖슜?섏뿬 ?덉긽 ?먭?, 沅뚯옣 泥?뎄?? ?덉긽 GP, GP?⑥쓣 ?곗텧?쒕떎.

Quotes ?붾㈃? 寃곗옱瑜??듯빐 異뺤쟻??Tariff DB? Master Rule??湲곕컲?쇰줈 ?댁넚鍮? ?듦?鍮? Partner Fee, Minimum GP瑜?諛섏쁺??沅뚯옣 寃ъ쟻???앹꽦?쒕떎.

二쇱슂 諛섏쁺 湲곗?:

- ?댁넚鍮? `transport_tariffs` ?됯퇏 ?먭? ?먮뒗 ?섎룞 ?낅젰 ?먭?
- ?듦?鍮? `customs_tariffs` ?됯퇏 ?먭? ?먮뒗 ?섎룞 ?낅젰 ?먭?
- Partner Fee: `partner_fee_rules` Master 湲곗?, USD???꾩떆 ?섏쑉 `160 JPY/USD` ?곸슜
- Minimum GP: `minimum_gp_rules` Master 湲곗?, ?놁쑝硫?fallback rule ?ъ슜
- Target GP Rate: `gp_rate_rules` Master 湲곗?, ?놁쑝硫?嫄곕옒援щ텇蹂?fallback rule ?ъ슜

Quote API:

- `POST /api/quotes/generate`
  - 寃ъ쟻 ?붿껌媛믪쓣 湲곗??쇰줈 沅뚯옣 寃ъ쟻??怨꾩궛?쒕떎.
- `POST /api/quotes/generate-and-save`
  - 寃ъ쟻 怨꾩궛 ??`quote_cases`, `quote_items`????ν븳??
- `GET /api/quotes`
  - ??λ맂 寃ъ쟻 ?대젰 紐⑸줉??議고쉶?쒕떎.
- `GET /api/quotes/{quote_case_id}`
  - ??λ맂 寃ъ쟻 ?곸꽭? 寃ъ쟻 ??ぉ??議고쉶?쒕떎.

?덉떆 ?붿껌:

```json
{
  "customer_name": "TEST CUSTOMER",
  "trade_type": "SHIPPER",
  "partner_name": null,
  "mode": "SEA",
  "direction": "IMPORT",
  "code": "SI++",
  "pol": "BUSAN",
  "pod": "TOKYO",
  "port": "TOKYO",
  "origin": "BUSAN",
  "destination": "TOKYO",
  "container_type": "20DC",
  "container_count": 1,
  "include_customs": true,
  "include_transport": true
}
```

?묐떟?먮뒗 `TRANSPORT`, `CUSTOMS`, `PARTNER_FEE`, `BASIC_MARGIN`, `GP_RATE_ADJUSTMENT` ?깆쓽 寃ъ쟻 ??ぉ怨?`QUOTABLE` ?먮뒗 `NEED_REVIEW` ?먯젙 ?뚰듃媛 ?ы븿?쒕떎.
 
## STEP 29 Approval Workflow

AI Decision? ?섏씡??諛?湲곗? 異⑹” ?щ???????쒖뒪???먯젙?대ŉ, Workflow Status???ㅼ젣 議곗쭅 ??寃곗옱 吏꾪뻾 ?곹깭瑜??섎??쒕떎.

Workflow ?④퀎:

- `DRAFT`: ?대떦???곸떊 ??- `SUBMITTED`: ?대떦???곸떊 ?꾨즺, ????뱀씤 ?湲?- `TEAM_APPROVED`: ????뱀씤 ?꾨즺, 蹂몃????뱀씤 ?湲?- `DIRECTOR_APPROVED`: 蹂몃????뱀씤 ?꾨즺, ????뱀씤 ?湲?- `CEO_APPROVED`: ???理쒖쥌 ?뱀씤
- `REJECTED`: 諛섎젮
- `RETURNED`: 蹂댁셿?붿껌

Workflow API:

- `GET /api/workflows`
- `GET /api/workflows/{workflow_id}`
- `POST /api/workflows/{workflow_id}/submit`
- `POST /api/workflows/{workflow_id}/team-approve`
- `POST /api/workflows/{workflow_id}/director-approve`
- `POST /api/workflows/{workflow_id}/ceo-approve`
- `POST /api/workflows/{workflow_id}/reject`
- `POST /api/workflows/{workflow_id}/return`

??λ맂 寃곗옱嫄댁? AI ?먯젙怨?蹂꾧컻濡???긽 `DRAFT` ?곹깭??Workflow瑜??먮룞 ?앹꽦?쒕떎. Workflows ?붾㈃?먯꽌 ?곹깭蹂?議고쉶, ?곸떊, ?뱀씤, 諛섎젮, 蹂댁셿?붿껌??泥섎━?????덈떎.

## STEP 30 User Role / Workflow Authorization

2李?媛쒕컻?먯꽌??媛꾨떒??Header 湲곕컲 ?ъ슜??Role 愿由щ? ?곸슜?쒕떎. ?ㅼ젣 ?댁쁺 諛고룷 ?쒖뿉??濡쒓렇?? 鍮꾨?踰덊샇, SSO ?먮뒗 ?щ궡 怨꾩젙 ?곕룞?쇰줈 ?뺤옣?????덈떎.

### 湲곕낯 ?ъ슜??
`POST /api/masters/seed-defaults` ?ㅽ뻾 ???꾨옒 ?ъ슜?먭? ?먮룞 ?앹꽦?쒕떎.

- `admin` / 愿由ъ옄 / `ADMIN`
- `staff` / ?대떦??/ `STAFF`
- `team_manager` / ???/ `TEAM_MANAGER`
- `director` / 蹂몃???/ `DIRECTOR`
- `ceo` / ???/ `CEO`

### ?몄쬆 諛⑹떇

MVP?먯꽌??紐⑤뱺 API ?붿껌 Header???꾩옱 ?ъ슜?먮챸???꾨떖?쒕떎.

```http
X-USER-NAME: staff
```

Frontend ?곷떒??User dropdown?먯꽌 ?ъ슜?먮? ?좏깮?섎㈃ `localStorage`????λ릺怨? Axios ?붿껌??`X-USER-NAME` Header媛 ?먮룞 ?ы븿?쒕떎.

### Workflow 沅뚰븳

- `STAFF`: 寃곗옱嫄??앹꽦, DRAFT/RETURNED 嫄??곸떊 媛?? ?뱀씤 遺덇?
- `TEAM_MANAGER`: SUBMITTED 嫄?????뱀씤, 蹂댁셿?붿껌, 諛섎젮 媛??- `DIRECTOR`: TEAM_APPROVED 嫄?蹂몃????뱀씤, 蹂댁셿?붿껌, 諛섎젮 媛??- `CEO`: DIRECTOR_APPROVED 嫄?????뱀씤, 蹂댁셿?붿껌, 諛섎젮 媛??- `ADMIN`: 紐⑤뱺 Workflow ?곹깭 蹂寃?媛??
沅뚰븳???놁쑝硫?API??`403 Forbidden`??諛섑솚?섎ŉ, Frontend??"沅뚰븳???놁뒿?덈떎." 硫붿떆吏瑜??쒖떆?쒕떎.

### User Master API

- `GET /api/users`
- `POST /api/users`
- `PUT /api/users/{user_id}`
- `DELETE /api/users/{user_id}`

`DELETE`???ㅼ젣 ??젣媛 ?꾨땲??`is_active=False`濡?鍮꾪솢?깊솕?쒕떎. Master ?붾㈃??User / Role Master ?뱀뀡?먯꽌 ?ъ슜??異붽?, ?섏젙, 鍮꾪솢?깊솕瑜??섑뻾?????덈떎.

### AI Decision怨?Workflow Status

AI Decision? ?섏씡??諛?湲곗? 異⑹” ?щ???????쒖뒪???먯젙?대ŉ, Workflow Status???ㅼ젣 議곗쭅 ??寃곗옱 吏꾪뻾 ?곹깭瑜??섎??쒕떎. ?덈? ?ㅼ뼱 AI Decision??`CONDITIONAL_APPROVED`?щ룄 Workflow??`DRAFT`?먯꽌 ?쒖옉???대떦???곸떊, ????뱀씤, 蹂몃????뱀씤, ????뱀씤 ?④퀎瑜?嫄곗튇??

## STEP 31 PDF Approval Reports

PDF 寃곗옱?쒕뒗 Markdown 寃곗옱?ъ궗?쒕? 湲곕컲?쇰줈 ?앹꽦?섎ŉ, ??쒖씠??蹂닿퀬??Summary? ?곸꽭寃?좎슜 Detail ??醫낅쪟瑜??쒓났?쒕떎. ?앹꽦??PDF??`backend/generated_reports/` ?대뜑????λ릺怨? ?뚯씪 ?뺣낫??`approval_report_files` ?뚯씠釉붿뿉 湲곕줉?쒕떎.

### PDF 醫낅쪟

- `SUMMARY`: ??쒖씠??蹂닿퀬??1?섏씠吏 ?붿빟 PDF
- `DETAIL`: 湲곕낯?뺣낫, ?섏씡??遺꾩꽍, Findings, Partner Fee, ?꾩닔 泥?뎄??ぉ, ?먯궗?먯썝, Workflow ?대젰源뚯? ?ы븿?섎뒗 ?곸꽭 PDF

### PDF API

- `POST /api/approvals/{approval_case_id}/report/pdf?report_type=SUMMARY`
- `POST /api/approvals/{approval_case_id}/report/pdf?report_type=DETAIL`
- `GET /api/approvals/{approval_case_id}/report/files`
- `GET /api/reports/files/{report_file_id}/download`

PDF ?앹꽦 API??`X-USER-NAME` Header 湲곕컲 沅뚰븳???뺤씤?쒕떎. `TEAM_MANAGER`, `DIRECTOR`, `CEO`, `ADMIN` Role??PDF瑜??앹꽦?????덉쑝硫? 沅뚰븳???놁쑝硫?`403 Forbidden`??諛섑솚?쒕떎.

### Frontend

Approval Detail ?붾㈃怨?Workflow ?곸꽭 ?붾㈃?먯꽌 Summary PDF / Detail PDF瑜??앹꽦?섍퀬 ?ㅼ슫濡쒕뱶?????덈떎.

### ?쒓? ?고듃

ReportLab 湲곕낯 ?고듃???쒓???源⑥쭏 ???덉쑝誘濡??쒕쾭?먯꽌 ?꾨옒 ?고듃瑜??곗꽑 ?먯깋?섏뿬 ?ъ슜?쒕떎.

- Malgun Gothic
- NanumGothic
- AppleGothic
- NotoSansCJK

?쒓? 異쒕젰??源⑥쭏 寃쎌슦 ?쒕쾭??NanumGothic ?먮뒗 NotoSansCJK ?고듃瑜??ㅼ튂?댁빞 ?쒕떎.

## STEP 32 Operations / Backup / Audit

2李??댁쁺 ?뚯뒪?몃? ?꾪빐 濡쒓렇, 媛먯궗 濡쒓렇, DB 諛깆뾽, ?쒖뒪???곹깭 ?먭? 湲곕뒫??異붽??덈떎.

### 濡쒓렇 ?뚯씪 ?꾩튂

- Application log: `backend/logs/app.log`
- Error log: `backend/logs/error.log`

紐⑤뱺 API ?붿껌? method, path, status_code, duration_ms, `X-USER-NAME` 湲곗? ?ъ슜?먮챸??`app.log`??湲곕줉?쒕떎. ?덉긽?섏? 紐삵븳 ?쒕쾭 ?ㅻ쪟??`error.log`?먮룄 湲곕줉?쒕떎.

### ????대뜑

- ?낅줈???뚯씪: `backend/uploads/`
- PDF 寃곗옱?? `backend/generated_reports/`
- DB 諛깆뾽 ?뚯씪: `backend/backups/`
- 濡쒓렇 ?뚯씪: `backend/logs/`

### Audit Log

二쇱슂 ?댁쁺 ?대깽?몃뒗 `audit_logs` ?뚯씠釉붿뿉 湲곕줉?쒕떎.

- 寃곗옱嫄????- Workflow ?곸떊/?뱀씤/諛섎젮/蹂댁셿?붿껌
- Master Rule ?앹꽦/?섏젙/鍮꾪솢?깊솕
- PDF ?앹꽦
- 寃ъ쟻 ?앹꽦 諛????- DB 諛깆뾽

議고쉶 API:

- `GET /api/audit-logs`

Query Parameter:

- `user_name`
- `action`
- `entity_type`
- `start_date`
- `end_date`

### Admin API

Admin API??`X-USER-NAME: admin` ?먮뒗 `ADMIN` Role ?ъ슜?먮쭔 ?ъ슜?????덈떎.

- `GET /api/admin/system-status`
- `POST /api/admin/backup-db`
- `GET /api/admin/backups`

### Admin ?붾㈃

Frontend ?곷떒 User媛 `admin`??寃쎌슦?먮쭔 Admin 硫붾돱媛 ?쒖떆?쒕떎. Admin ?붾㈃?먯꽌 ?쒖뒪???곹깭, DB 諛깆뾽 ?ㅽ뻾, 諛깆뾽 紐⑸줉, Audit Log瑜??뺤씤?????덈떎.

### ?μ븷 ???뺤씤 ?쒖꽌

1. `GET /health`濡?Backend 湲곕룞 ?곹깭 ?뺤씤
2. `GET /api/admin/system-status`濡?DB 諛??꾩닔 ?대뜑 ?곹깭 ?뺤씤
3. `backend/logs/error.log`?먯꽌 ?쒕쾭 ?ㅻ쪟 ?뺤씤
4. `backend/logs/app.log`?먯꽌 ?붿껌蹂?status_code? 泥섎━ ?쒓컙 ?뺤씤
5. `GET /api/audit-logs`濡?二쇱슂 ?곗씠??蹂寃??대젰 ?뺤씤
6. ?꾩슂 ??`POST /api/admin/backup-db`濡??꾩옱 DB瑜?諛깆뾽?????먯씤 議곗궗

## STEP 33 Operation Test Scenarios

?댁쁺 ?꾩뿉??`docs/OPERATION_TEST_SCENARIOS.md` 湲곗??쇰줈 ?꾩껜 ?먮쫫??寃利앺븯怨? Operation Test ?붾㈃??寃곌낵瑜?湲곕줉?쒕떎.

?댁쁺 ?뚯뒪??踰붿쐞:

- Profit Sheet Upload / Parse / Map to Case
- Manual Edit / AI Analyze / Save
- Workflow Submit / Team Approve / Director Approve / CEO Approve
- Dashboard 諛섏쁺 諛?湲곌컙蹂?議고쉶
- Tariff DB ?뺤씤
- Quote Generate
- PDF Summary / Detail ?앹꽦
- 沅뚰븳 ?ㅻ쪟 ?뺤씤
- DB Backup

?뚯뒪??寃곌낵??`operation_test_results` ?뚯씠釉붿뿉 ??λ릺硫? API? Frontend ?붾㈃?먯꽌 議고쉶/?깅줉/?섏젙/HOLD 泥섎━媛 媛?ν븯??

Operation Test API:

- `GET /api/operation-tests`
- `POST /api/operation-tests`
- `PUT /api/operation-tests/{id}`
- `DELETE /api/operation-tests/{id}`

## STEP 34 Parser Validation

Parser Validation? ?ㅼ젣 Profit Sheet ?뚯씪???먮룞?뚯떛 寃곌낵媛 湲곕?媛믨낵 ?쇱튂?섎뒗吏 寃利앺븯??湲곕뒫?대떎. ?섑뵆 ?뚯씪蹂?湲곕? GP, ?낅Т肄붾뱶, 二쇱슂 鍮꾩슜 ??ぉ??湲곗??쇰줈 `PASS` / `PARTIAL` / `FAIL`???먯젙?쒕떎.

湲곕낯 寃利?耳?댁뒪??`POST /api/masters/seed-defaults` ?ㅽ뻾 ???깅줉?쒕떎.

- `TOWA_SI_PLUS_PLUS`
- `KANGKOKU_HIROBA_SI_PLUS_PLUS`
- `HUMAN_MADE_SE_PLUS_PLUS`
- `PNS_SE`
- `DONGSHIN_SI`

Parser Validation API:

- `GET /api/parser-validation/cases`
- `POST /api/parser-validation/cases`
- `PUT /api/parser-validation/cases/{case_id}`
- `DELETE /api/parser-validation/cases/{case_id}`
- `POST /api/parser-validation/cases/{case_id}/run`
- `POST /api/parser-validation/run-all`
- `GET /api/parser-validation/results`

?ъ슜 ?먮쫫:

1. `POST /api/uploads/profit-sheet`濡??ㅼ젣 PDF ?먮뒗 Excel Profit Sheet瑜??낅줈?쒗븳??
2. `GET /api/parser-validation/cases`?먯꽌 寃利?耳?댁뒪瑜??뺤씤?쒕떎.
3. `POST /api/parser-validation/cases/{case_id}/run`??`upload_id`瑜??꾨떖?섏뿬 寃利앹쓣 ?ㅽ뻾?쒕떎.
4. `GET /api/parser-validation/results` ?먮뒗 Frontend??Operation Test ?붾㈃?먯꽌 寃곌낵瑜??뺤씤?쒕떎.

Frontend?먯꽌??Operation Test ?붾㈃??Parser Validation ?뱀뀡?먯꽌 寃利?耳?댁뒪瑜??깅줉/?섏젙?섍퀬, ?낅줈???뚯씪??`upload_id`瑜??낅젰??寃利앹쓣 ?ㅽ뻾?????덈떎. 寃곌낵 ?쒖뿉??湲곕? 肄붾뱶, ?ㅼ젣 肄붾뱶, 湲곕? GP, ?ㅼ젣 GP, 李⑥씠, 湲곕? Decision, ?ㅼ젣 Decision, confidence, diff summary媛 ?④퍡 ?쒖떆?쒕떎.

## STEP 35 Parser Improvement

Parser Improvement 湲곕뒫? 寃利??ㅽ뙣 寃곌낵瑜?湲곕컲?쇰줈 ?대뼡 Template ?ㅼ썙???먮뒗 留ㅽ븨 洹쒖튃??蹂댁셿?댁빞 ?섎뒗吏 ?쒖븞?쒕떎. ?댁쁺?먮뒗 ?쒖븞??寃?좏븳 ??`Apply` ?먮뒗 `Reject`?????덈떎.

媛쒖꽑 ?쒖븞? Parser Validation 寃곌낵媛 `PARTIAL` ?먮뒗 `FAIL`?????먮룞 ?앹꽦?쒕떎. ?덈? ?ㅼ뼱 ?댁넚 留ㅼ텧??湲곕?媛믨낵 ?ㅻⅤ硫?`TRANSPORT_MISMATCH` ?쒖븞???앹꽦?섍퀬, 愿???먮뒗 ?뚮퉬?멸? ?ㅻⅤ硫?`TAX_MISMATCH` ?쒖븞???앹꽦?쒕떎.

Parser Improvement API:

- `GET /api/parser-improvements/suggestions`
- `POST /api/parser-improvements/suggestions/{suggestion_id}/apply`
- `POST /api/parser-improvements/suggestions/{suggestion_id}/reject`

Apply ?숈옉:

- ?쒖븞??`suggested_keyword`? `template_id`媛 ?덉쑝硫?Parser Template??愿??keyword field???ㅼ썙?쒕? 異붽??쒕떎.
- ?대? 議댁옱?섎뒗 ?ㅼ썙?쒕뒗 以묐났 異붽??섏? ?딅뒗??
- ?곸슜 ?대젰? Audit Log??`APPLY_PARSER_IMPROVEMENT`濡?湲곕줉?쒕떎.

Frontend?먯꽌??Operation Test ?붾㈃??Parser Improvement Suggestions ?뱀뀡?먯꽌 ?쒖븞???뺤씤?섍퀬 Apply ?먮뒗 Reject瑜??ㅽ뻾?????덈떎.

## STEP 36 SQLite / PostgreSQL ?댁쁺?섍꼍 ?꾪솚

媛쒕컻?섍꼍?먯꽌??SQLite瑜?湲곕낯?쇰줈 ?ъ슜?섍퀬, ?댁쁺?섍꼍?먯꽌??`DATABASE_URL` ?섍꼍蹂?섎? ?듯빐 PostgreSQL濡??꾪솚?????덈떎. `DATABASE_URL`???놁쑝硫?SQLite媛 ?ъ슜?쒕떎.

?섍꼍蹂???덉떆??`.env.example`???쒓났?쒕떎.

```env
DATABASE_URL=sqlite:///./lotos_ai_approval.db
APP_ENV=development
SECRET_KEY=change-this-secret
UPLOAD_DIR=backend/uploads
REPORT_DIR=backend/generated_reports
LOG_DIR=backend/logs
BACKUP_DIR=backend/backups
```

### SQLite 媛쒕컻?섍꼍

```bash
cd backend
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

`APP_ENV=development`?먯꽌??`Base.metadata.create_all`???덉슜?섏뿬 媛쒕컻 DB ?뚯씠釉붿쓣 ?먮룞 ?앹꽦?쒕떎.

### PostgreSQL Docker ?ㅽ뻾

`docker-compose.yml`?먮뒗 `postgres:16` ?쒕퉬?ㅺ? ?ы븿?섏뼱 ?덈떎.

```bash
docker compose up --build
```

Backend??Docker ?섍꼍?먯꽌 ?꾨옒 DB URL???ъ슜?쒕떎.

```text
postgresql+psycopg2://lotos_user:lotos_password@postgres:5432/lotos_ai_approval
```

### Alembic Migration

?댁쁺?섍꼍?먯꽌??`APP_ENV=production`?쇰줈 ?ㅼ젙?섍퀬 ?먮룞 `create_all` ???Alembic migration ?ъ슜??沅뚯옣?쒕떎.

珥덇린 migration ?앹꽦:

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
```

Migration ?곸슜:

```bash
alembic upgrade head
```

Docker backend 而⑦뀒?대꼫?먯꽌 ?ㅽ뻾?섎뒗 寃쎌슦:

```bash
docker compose exec backend alembic upgrade head
```

### Admin System Status

`GET /api/admin/system-status` ?묐떟?먮뒗 ?꾨옒 ?뺣낫媛 異붽??쒕떎.

- `database_type`: `sqlite` ?먮뒗 `postgresql`
- `database_url_masked`: 鍮꾨?踰덊샇媛 留덉뒪?밸맂 DB URL
- `app_env`: ?꾩옱 ?ㅽ뻾 ?섍꼍

### Backup

SQLite 紐⑤뱶?먯꽌??湲곗〈泥섎읆 `POST /api/admin/backup-db`媛 DB ?뚯씪??`BACKUP_DIR`濡?蹂듭궗?쒕떎.

PostgreSQL 紐⑤뱶?먯꽌??API媛 ?섎룞 諛깆뾽 ?꾩슂 硫붿떆吏瑜?諛섑솚?쒕떎. PostgreSQL 諛깆뾽? `pg_dump`瑜??ъ슜?쒕떎.

```bash
pg_dump -h localhost -U lotos_user lotos_ai_approval > backup.sql
```

?댁쁺 諛고룷 ?쒖뿉??DB 鍮꾨?踰덊샇, `SECRET_KEY`, 諛깆뾽 ?뚯씪 蹂닿? ?꾩튂瑜??щ궡 蹂댁븞 湲곗???留욊쾶 蹂꾨룄濡?愿由ы빐???쒕떎.

## STEP 37 JWT Login / Authentication

3李?媛쒕컻遺??JWT 湲곕컲 濡쒓렇???몄쬆???ъ슜?쒕떎. 媛쒕컻?섍꼍?먯꽌??湲곗〈 `X-USER-NAME` Header fallback???ъ슜?????덉쑝?? ?댁쁺?섍꼍(`APP_ENV=production`)?먯꽌??`Authorization: Bearer {token}` ?몄쬆???ъ슜?댁빞 ?쒕떎.

Auth API:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/change-password`

濡쒓렇????

```json
{
  "username": "admin",
  "password": "admin1234"
}
```

?묐떟:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "display_name": "愿由ъ옄",
    "role": "ADMIN"
  }
}
```

珥덇린 怨꾩젙:

- `admin` / `admin1234`
- `staff` / `staff1234`
- `team_manager` / `manager1234`
- `director` / `director1234`
- `ceo` / `ceo1234`

珥덇린 鍮꾨?踰덊샇???댁쁺 ??諛섎뱶??蹂寃쏀빐???쒕떎. 鍮꾨?踰덊샇???됰Ц?쇰줈 ??ν븯吏 ?딄퀬 bcrypt hash濡???ν븳?? JWT `SECRET_KEY`??`.env` ?먮뒗 諛고룷 ?섍꼍蹂?섎줈 愿由ы빐???섎ŉ, 湲곕낯媛?`change-this-secret`? ?댁쁺?섍꼍?먯꽌 ?ъ슜?섎㈃ ???쒕떎.

Frontend??濡쒓렇???깃났 ??Access Token怨??ъ슜???뺣낫瑜?`localStorage`????ν븯怨? 紐⑤뱺 API ?붿껌??`Authorization: Bearer {token}` Header瑜??먮룞 異붽??쒕떎. 濡쒓렇?꾩썐 ????λ맂 ?좏겙怨??ъ슜???뺣낫????젣?쒕떎.

沅뚰븳 ?곸슜:

- Workflow ?뱀씤/諛섎젮/蹂댁셿?붿껌
- Admin API
- User Master ?앹꽦/?섏젙/鍮꾪솢?깊솕
- PDF ?앹꽦 API
- ?댁쁺?섍꼍??Master ?섏젙 API

AI Decision怨?Workflow Status??湲곗〈泥섎읆 遺꾨━?섏뼱 ?덉쑝硫? JWT ?몄쬆? ?ㅼ젣 議곗쭅 ??寃곗옱 Workflow 沅뚰븳 寃利앹뿉 ?ъ슜?쒕떎.

`DELETE`???ㅼ젣 ??젣媛 ?꾨땲???뚯뒪??寃곌낵瑜?`HOLD`濡?蹂寃쏀븳??
## Documentation

?댁쁺 諛?援먯쑁??臾몄꽌??`docs` ?대뜑?먯꽌 愿由ы븳??

- `docs/USER_MANUAL.md`: ?대떦?? ??? 蹂몃??? ??? 愿由ъ옄 愿?먯쓽 ?ъ슜??留ㅻ돱??- `docs/ADMIN_MANUAL.md`: ?ㅼ튂, Docker ?ㅽ뻾, PostgreSQL, Backup, Log, ?μ븷 ???愿由ъ옄 留ㅻ돱??- `docs/TRAINING_GUIDE.md`: 1?쒓컙 援먯쑁 怨쇱젙怨??ㅼ뒿 ?쒕굹由ъ삤
- `docs/OPERATION_TEST_SCENARIOS.md`: ?댁쁺 ?뚯뒪???쒕굹由ъ삤? 泥댄겕由ъ뒪??
臾몄꽌 ?ㅼ슫濡쒕뱶 API:

- `GET /api/docs/user-manual`
- `GET /api/docs/admin-manual`
- `GET /api/docs/training-guide`

Frontend??`Help` 硫붾돱?먯꽌 ?낅Т ?덉감 ?붿빟怨?臾몄꽌 ?ㅼ슫濡쒕뱶 留곹겕瑜??뺤씤?????덈떎.

## STEP 39 ERP / Accounting Integration Preparation

蹂??④퀎?먯꽌??ERP/?뚭퀎?쒖뒪??吏곸젒 ?곕룞 ???④퀎濡? 寃곗옱 諛?寃ъ쟻 ?곗씠?곕? ?쒖? JSON Payload濡??앹꽦?섍퀬 Export?????덈룄濡??쒕떎. ?ν썑 API/Webhook 諛⑹떇?쇰줈 ?몃? ?쒖뒪???꾩넚???뺤옣?????덈떎.

Integration 湲곕뒫:

- Integration Setting 愿由? `ERP`, `ACCOUNTING`, `GROUPWARE` ???몃? ?쒖뒪?쒕퀎 ?곕룞 諛⑹떇???깅줉?쒕떎.
- Approval Payload 誘몃━蹂닿린: `GET /api/integrations/approval/{approval_case_id}/payload`
- Quote Payload 誘몃━蹂닿린: `GET /api/integrations/quote/{quote_case_id}/payload`
- Approval JSON Export: `POST /api/integrations/export/approval/{approval_case_id}`
- Quote JSON Export: `POST /api/integrations/export/quote/{quote_case_id}`
- Integration ?뚯씪 ?ㅼ슫濡쒕뱶: `GET /api/integrations/files/{log_id}/download`
- Integration Log 議고쉶: `GET /api/integrations/logs`

JSON ?뚯씪? `backend/exports/integration` ?대뜑????λ맂?? Export ?ㅽ뻾 寃곌낵??`integration_logs`??湲곕줉?섍퀬, `audit_logs`?먮뒗 `INTEGRATION_EXPORT` action?쇰줈 媛먯궗 湲곕줉???⑤뒗??

Webhook ?ㅼ젙???덇퀬 endpoint URL???깅줉??寃쎌슦 ?대쾲 ?④퀎?먯꽌???ㅼ젣 ?몃? ?꾩넚???섑뻾?섏? ?딄퀬 `PENDING` ?곹깭??Integration Log留??앹꽦?쒕떎. ?ㅼ젣 HTTP ?꾩넚, ?ъ떆?? ?ㅽ뙣 ?뚮┝? ?ν썑 ?④퀎?먯꽌 援ы쁽?쒕떎.

沅뚰븳:

- Payload 議고쉶/Export: `DIRECTOR`, `CEO`, `ADMIN`
- Integration Setting ?앹꽦/?섏젙/鍮꾪솢?깊솕: `ADMIN`

## STEP 38 Excel Export

?댁쁺?먮뒗 寃곗옱?대젰, Dashboard, Tariff DB, 寃ъ쟻?대젰, ?앹궛???곗씠?곕? Excel濡??ㅼ슫濡쒕뱶?섏뿬 ?붾퀎 遺꾩꽍, 嫄곕옒泥섎퀎 GP 遺꾩꽍, ?묐젰?낆껜 ?④? 鍮꾧탳???쒖슜?????덈떎.

Export API:

- `GET /api/exports/approvals.xlsx`
- `GET /api/exports/dashboard.xlsx`
- `GET /api/exports/tariffs/transport.xlsx`
- `GET /api/exports/tariffs/customs.xlsx`
- `GET /api/exports/quotes.xlsx`
- `GET /api/exports/productivity.xlsx`

Excel ?뚯씪? `EXPORT_DIR`????λ릺硫?湲곕낯 ?꾩튂??`backend/exports`?대떎. ?ㅼ슫濡쒕뱶 ?ㅽ뻾 ??`export_files` ?뚯씠釉붿뿉 ?뚯씪 ?대젰????λ릺怨? `audit_logs`?먮뒗 `EXPORT_EXCEL` action?쇰줈 ?ㅽ뻾 ?ъ슜?먯? ?꾪꽣 議곌굔??湲곕줉?쒕떎.

沅뚰븳:

- Export 媛?? `TEAM_MANAGER`, `DIRECTOR`, `CEO`, `ADMIN`
- `STAFF`??Export 遺덇?

Frontend ?ㅼ슫濡쒕뱶 ?꾩튂:

- Dashboard: Dashboard Excel, Productivity Excel
- Approvals: 寃곗옱?대젰 Excel
- Quotes: 寃ъ쟻?대젰 Excel
- Admin: ?댁넚 Tariff Excel, ?듦? Tariff Excel

## OCR for Scanned PDFs

이미지 스캔 PDF는 PDF 내부에 텍스트 레이어가 없어 일반 PDF 파서만으로는 내용을 추출할 수 없다. 시스템은 이미지형 PDF를 감지하면 `ocr_status`, `page_diagnostics`, `warnings`를 반환한다.

- Docker 환경: Backend 이미지에 `tesseract-ocr`, 영어/일본어/한국어 OCR 데이터를 설치하여 OCR을 시도한다.
- 로컬 Windows 환경: Tesseract가 설치되어 있지 않으면 OCR은 실행되지 않고 "OCR 엔진 설치 필요" 경고가 표시된다.
- OCR 결과도 Profit Mapper로 전달되지만, 스캔 품질에 따라 오인식이 발생할 수 있으므로 결재 전 Upload 화면에서 추출값을 반드시 확인/수정해야 한다.

Windows 로컬 OCR 사용 시에는 Tesseract 설치 후 `tesseract` 명령이 PATH에서 실행되는지 확인한다.
