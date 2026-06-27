from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, ensure_sqlite_schema, get_db
from app.schemas import (
    GPRateRuleCreate,
    GPRateRuleRead,
    InternalResourceRuleCreate,
    InternalResourceRuleRead,
    MinimumGPRuleCreate,
    MinimumGPRuleRead,
    ParserTemplateCreate,
    ParserTemplateRead,
    ParserValidationCaseCreate,
    PartnerFeeRuleCreate,
    PartnerFeeRuleRead,
    RequiredChargeRuleCreate,
    RequiredChargeRuleRead,
    SeedDefaultsResponse,
    UserCreate,
    WorkCodeRuleCreate,
    WorkCodeRuleRead,
)
from app.services.approval_engine import GP_RATE_RULES, MINIMUM_GP_RULES, POINT_RULES
from app.services.auth_service import hash_password


router = APIRouter(prefix="/api/masters", tags=["Masters"])

ALLOWED_WORK_CODES = {
    "SE",
    "SE+",
    "SE++",
    "SE+++",
    "SI",
    "SI+",
    "SI++",
    "SI+++",
    "AE",
    "AE+",
    "AE++",
    "AE+++",
    "AI",
    "AI+",
    "AI++",
    "AI+++",
    "PJT",
}


DEFAULT_PARTNER_FEE_RULES = [
    PartnerFeeRuleCreate(
        partner_name="태웅로직스",
        mode="SEA",
        direction="EXPORT",
        unit_type="BL",
        currency="USD",
        amount=20,
        settlement_direction="LOTOS_COLLECT",
        note="태웅로직스 해상수출 USD20/BL",
    ),
    PartnerFeeRuleCreate(
        partner_name="J2K GLOBAL",
        mode="SEA",
        direction="EXPORT",
        container_type="20FT",
        unit_type="CNTR",
        currency="USD",
        amount=20,
        settlement_direction="LOTOS_COLLECT",
        note="J2K GLOBAL 해상수출 20FT USD20/CNTR",
    ),
    PartnerFeeRuleCreate(
        partner_name="J2K GLOBAL",
        mode="SEA",
        direction="EXPORT",
        container_type="40FT",
        unit_type="CNTR",
        currency="USD",
        amount=40,
        settlement_direction="LOTOS_COLLECT",
        note="J2K GLOBAL 해상수출 40FT USD40/CNTR",
    ),
    PartnerFeeRuleCreate(
        partner_name="J2K GLOBAL",
        mode="SEA",
        direction="EXPORT",
        unit_type="BL",
        currency="USD",
        amount=500,
        settlement_direction="LOTOS_COLLECT",
        special_condition="MIZUSHIMA_NAKASHIMA",
        valid_to=date(2026, 12, 31),
        note="J2K MIZUSHIMA 나카시마 프로펠러 USD500/BL",
    ),
    PartnerFeeRuleCreate(
        partner_name="J2K GLOBAL",
        mode="SEA",
        direction="IMPORT",
        container_type="20FT",
        unit_type="CNTR",
        currency="USD",
        amount=50,
        settlement_direction="PARTNER_CREDIT",
        special_condition="LOTOS_NOMI_HANKUK",
        note="J2K GLOBAL 수입 CREDIT USD50/20FT",
    ),
    PartnerFeeRuleCreate(
        partner_name="PNS NETWORKS",
        mode="SEA",
        direction="EXPORT",
        container_type="40HC",
        unit_type="CNTR",
        currency="USD",
        amount=15,
        settlement_direction="LOTOS_COLLECT",
        note="PNS NETWORKS 수출 40FT USD15/CNTR",
    ),
    PartnerFeeRuleCreate(
        partner_name="DONGSHIN SEA & AIR",
        mode="SEA",
        direction="IMPORT",
        unit_type="SHIPMENT",
        currency="JPY",
        amount=4000,
        settlement_direction="PARTNER_PAY",
        note="DONGSHIN SEA & AIR 수입 JPY4000/SHIPMENT",
    ),
    PartnerFeeRuleCreate(
        partner_name="EUNSAN",
        mode="SEA",
        direction="IMPORT",
        unit_type="BL",
        currency="USD",
        amount=15,
        settlement_direction="PARTNER_PAY",
        note="EUNSAN 수입 USD15/BL",
    ),
    PartnerFeeRuleCreate(
        partner_name="동원로엑스",
        mode="SEA",
        direction="EXPORT",
        unit_type="SHIP",
        currency="USD",
        amount=20,
        settlement_direction="LOTOS_COLLECT",
        note="동원로엑스 수출 USD20/SHIP",
    ),
    PartnerFeeRuleCreate(
        partner_name="동원로엑스",
        mode="SEA",
        direction="EXPORT",
        unit_type="BL",
        currency="USD",
        amount=10,
        settlement_direction="LOTOS_COLLECT",
        special_condition="ITOCHU",
        note="동원로엑스 ITOCHU 수출 USD10/BL",
    ),
]


def _work_rule_payload(code: str, point: float) -> WorkCodeRuleCreate:
    if code == "PJT":
        return WorkCodeRuleCreate(
            code=code,
            name="Project",
            point=point,
            description="Project case",
        )
    mode = "SEA" if code[0] == "S" else "AIR"
    direction = "EXPORT" if code[1] == "E" else "IMPORT"
    plus_count = code.count("+")
    return WorkCodeRuleCreate(
        code=code,
        name=code,
        mode=mode,
        direction=direction,
        has_customs=plus_count >= 1,
        has_transport=plus_count >= 2,
        has_work=plus_count >= 3,
        point=point,
        description=f"{code} 기본 Point",
    )


DEFAULT_GP_RATE_RULES = [
    GPRateRuleCreate(
        trade_type=trade_type,
        minimum_gp_rate=rate,
        description=f"{trade_type} 기본 실GP율",
    )
    for trade_type, rate in GP_RATE_RULES.items()
]

DEFAULT_WORK_CODE_RULES = [
    _work_rule_payload(code, point) for code, point in POINT_RULES.items()
]

DEFAULT_USERS = [
    UserCreate(username="admin", display_name="관리자", role="ADMIN", password="admin1234"),
    UserCreate(username="staff", display_name="담당자", role="STAFF", password="staff1234"),
    UserCreate(
        username="team_manager",
        display_name="팀장",
        role="TEAM_MANAGER",
        password="manager1234",
    ),
    UserCreate(username="director", display_name="본부장", role="DIRECTOR", password="director1234"),
    UserCreate(username="ceo", display_name="대표", role="CEO", password="ceo1234"),
]

DEFAULT_PARSER_VALIDATION_CASES = [
    ParserValidationCaseCreate(
        case_name="TOWA_SI_PLUS_PLUS",
        expected_customer_name="TOWA",
        expected_code="SI++",
        expected_gp_jpy=24493,
        expected_decision="CEO_REVIEW|CONDITIONAL_APPROVED",
        expected_transport_revenue_jpy=61000,
        expected_transport_expense_jpy=60000,
        expected_customs_revenue_jpy=11800,
        expected_consumption_tax_jpy=300300,
        tolerance_jpy=500,
    ),
    ParserValidationCaseCreate(
        case_name="KANGKOKU_HIROBA_SI_PLUS_PLUS",
        expected_customer_name="KANGKOKU HIROBA",
        expected_code="SI++",
        expected_gp_jpy=145177,
        expected_decision="APPROVED",
        expected_transport_revenue_jpy=78000,
        expected_transport_expense_jpy=65000,
        expected_customs_revenue_jpy=11800,
        expected_customs_duty_jpy=1131700,
        expected_consumption_tax_jpy=1071200,
        tolerance_jpy=500,
    ),
    ParserValidationCaseCreate(
        case_name="HUMAN_MADE_SE_PLUS_PLUS",
        expected_customer_name="HUMAN MADE",
        expected_code="SE++",
        expected_gp_jpy=32800,
        expected_decision="APPROVED",
        expected_transport_revenue_jpy=31000,
        expected_transport_expense_jpy=25000,
        expected_customs_revenue_jpy=11800,
        tolerance_jpy=500,
    ),
    ParserValidationCaseCreate(
        case_name="PNS_SE",
        expected_customer_name="SUMITOMO CHEMICAL",
        expected_code="SE",
        expected_gp_jpy=20798,
        expected_decision="APPROVED",
        expected_partner_fee_usd=30,
        tolerance_jpy=500,
    ),
    ParserValidationCaseCreate(
        case_name="DONGSHIN_SI",
        expected_customer_name="STAR WORLD",
        expected_code="SI",
        expected_gp_jpy=11128,
        expected_decision="APPROVED",
        expected_partner_fee_jpy=4000,
        tolerance_jpy=500,
    ),
]

DEFAULT_INTERNAL_RESOURCE_RULES = [
    *[
        InternalResourceRuleCreate(
            resource_type="CUSTOMS",
            port=port,
            location_name=port,
            priority=1,
            mandatory=True,
            description=f"{port} 자사통관 우선 PORT",
        )
        for port in ["TOKYO", "YOKOHAMA", "KOBE", "OSAKA", "HAKATA"]
    ],
    *[
        InternalResourceRuleCreate(
            resource_type="WAREHOUSE",
            port=port,
            location_name=port,
            priority=1,
            mandatory=True,
            description=f"{port} 자사창고 우선 PORT",
        )
        for port in ["TOKYO", "HAKATA"]
    ],
]


def _required_charge_defaults() -> list[RequiredChargeRuleCreate]:
    rules: list[RequiredChargeRuleCreate] = []
    for code in ["SE", "SE+", "SE++", "SE+++"]:
        for charge_name, keywords in [
            ("THC", "THC"),
            ("DOC", "DOC,DOCUMENT"),
            ("B/L", "B/L,BL FEE,BILL OF LADING"),
        ]:
            rules.append(
                RequiredChargeRuleCreate(
                    code=code,
                    mode="SEA",
                    direction="EXPORT",
                    charge_name=charge_name,
                    keywords=keywords,
                    required_when="ALWAYS",
                    severity="WARN",
                    description=f"{code} sea export required charge",
                )
            )
        rules.append(
            RequiredChargeRuleCreate(
                code=code,
                mode="SEA",
                direction="EXPORT",
                charge_name="AFR/AMS/ENS/ISPS",
                keywords="AFR,AMS,ENS,ISPS",
                required_when="EXPORT",
                severity="WARN",
                description="sea export optional check charge",
            )
        )

    for code in ["SI", "SI+", "SI++", "SI+++"]:
        for charge_name, keywords, required_when in [
            ("THC", "THC", "ALWAYS"),
            ("DOC", "DOC,DOCUMENT", "ALWAYS"),
            ("D/O", "D/O,DO FEE,DELIVERY ORDER", "ALWAYS"),
            ("DUTY", "DUTY,관세,関税", "IMPORT"),
            ("CONSUMPTION_TAX", "CONSUMPTION TAX,VAT,소비세,消費税", "IMPORT"),
        ]:
            rules.append(
                RequiredChargeRuleCreate(
                    code=code,
                    mode="SEA",
                    direction="IMPORT",
                    charge_name=charge_name,
                    keywords=keywords,
                    required_when=required_when,
                    severity="WARN",
                    description=f"{code} sea import required charge",
                )
            )

    rules.extend(
        [
            RequiredChargeRuleCreate(
                code="ANY",
                mode="ANY",
                direction="ANY",
                charge_name="CUSTOMS",
                keywords="CUSTOMS,CUSTOM,통관,通関",
                required_when="CUSTOMS",
                severity="WARN",
                description="customs included case required charge",
            ),
            RequiredChargeRuleCreate(
                code="ANY",
                mode="ANY",
                direction="ANY",
                charge_name="TRANSPORT",
                keywords="DRAYAGE,TRUCKING,TRANSPORT,DELIVERY,운송,배송",
                required_when="TRANSPORT",
                severity="WARN",
                description="transport included case required charge",
            ),
            RequiredChargeRuleCreate(
                code="ANY",
                mode="ANY",
                direction="ANY",
                charge_name="FOOD_DECLARATION",
                keywords="FOOD DECLARATION,FOOD,식품신고,食品",
                required_when="FOOD",
                severity="WARN",
                description="food or frozen cargo required charge",
            ),
        ]
    )
    return rules


DEFAULT_REQUIRED_CHARGE_RULES = _required_charge_defaults()


COMMON_REVENUE_KEYWORDS = "REVENUE,BILLING,DEBIT,請求,청구,매출"
COMMON_EXPENSE_KEYWORDS = "EXPENSE,COST,CREDIT,支払,原価,비용,원가"
COMMON_PROFIT_KEYWORDS = "PROFIT,GP,GROSS PROFIT,差益,이익"
COMMON_DUTY_KEYWORDS = "DUTY,関税,관세"
COMMON_CONSUMPTION_TAX_KEYWORDS = "CONSUMPTION TAX,VAT,消費税,소비세"
COMMON_TRANSPORT_KEYWORDS = (
    "DRAYAGE,TRUCKING,TRANSPORT,DELIVERY,運送,配送,운송,배송"
)
COMMON_CUSTOMS_KEYWORDS = "CUSTOMS,CUSTOM,通関,통관"
COMMON_PARTNER_FEE_KEYWORDS = "PARTNER FEE,AGENT FEE,CREDIT,パートナー,파트너"
COMMON_FOOD_KEYWORDS = "FOOD,FROZEN,食品,식품,냉동"

DEFAULT_PARSER_TEMPLATES = [
    ParserTemplateCreate(
        template_name="LOTOS_STANDARD_PDF",
        description="LOTOS standard PDF profit sheet parser template",
        mode="ANY",
        direction="ANY",
        file_type="PDF",
        customer_keyword="CUSTOMER,Customer,고객,CONSIGNEE,SHIPPER",
        partner_keyword="PARTNER,AGENT,파트너",
        revenue_section_keywords=COMMON_REVENUE_KEYWORDS,
        expense_section_keywords=COMMON_EXPENSE_KEYWORDS,
        profit_keywords=COMMON_PROFIT_KEYWORDS,
        duty_keywords=COMMON_DUTY_KEYWORDS,
        consumption_tax_keywords=COMMON_CONSUMPTION_TAX_KEYWORDS,
        transport_keywords=COMMON_TRANSPORT_KEYWORDS,
        customs_keywords=COMMON_CUSTOMS_KEYWORDS,
        partner_fee_keywords=COMMON_PARTNER_FEE_KEYWORDS,
        food_keywords=COMMON_FOOD_KEYWORDS,
        is_default=True,
    ),
    ParserTemplateCreate(
        template_name="LOTOS_EXPORT_PDF",
        description="LOTOS export PDF parser template with B/L and export charge keywords",
        mode="ANY",
        direction="EXPORT",
        file_type="PDF",
        customer_keyword="CUSTOMER,Customer,고객,CONSIGNEE,SHIPPER",
        partner_keyword="PARTNER,AGENT,파트너",
        revenue_section_keywords=f"{COMMON_REVENUE_KEYWORDS},B/L,BL FEE,DOC,THC,AFR,AMS,ENS,ISPS,CY,CFS",
        expense_section_keywords=f"{COMMON_EXPENSE_KEYWORDS},B/L,BL FEE,DOC,THC,AFR,AMS,ENS,ISPS,CY,CFS",
        profit_keywords=COMMON_PROFIT_KEYWORDS,
        duty_keywords=COMMON_DUTY_KEYWORDS,
        consumption_tax_keywords=COMMON_CONSUMPTION_TAX_KEYWORDS,
        transport_keywords=COMMON_TRANSPORT_KEYWORDS,
        customs_keywords=COMMON_CUSTOMS_KEYWORDS,
        partner_fee_keywords=COMMON_PARTNER_FEE_KEYWORDS,
        food_keywords=COMMON_FOOD_KEYWORDS,
        is_default=False,
    ),
    ParserTemplateCreate(
        template_name="LOTOS_IMPORT_PDF",
        description="LOTOS import PDF parser template with D/O, duty and consumption tax keywords",
        mode="ANY",
        direction="IMPORT",
        file_type="PDF",
        customer_keyword="CUSTOMER,Customer,고객,CONSIGNEE,SHIPPER",
        partner_keyword="PARTNER,AGENT,파트너",
        revenue_section_keywords=f"{COMMON_REVENUE_KEYWORDS},D/O,DO FEE,DUTY,CONSUMPTION TAX,VAT,DELIVERY ORDER,ETA",
        expense_section_keywords=f"{COMMON_EXPENSE_KEYWORDS},D/O,DO FEE,DUTY,CONSUMPTION TAX,VAT,DELIVERY ORDER,ETA",
        profit_keywords=COMMON_PROFIT_KEYWORDS,
        duty_keywords=COMMON_DUTY_KEYWORDS,
        consumption_tax_keywords=COMMON_CONSUMPTION_TAX_KEYWORDS,
        transport_keywords=COMMON_TRANSPORT_KEYWORDS,
        customs_keywords=COMMON_CUSTOMS_KEYWORDS,
        partner_fee_keywords=COMMON_PARTNER_FEE_KEYWORDS,
        food_keywords=COMMON_FOOD_KEYWORDS,
        is_default=False,
    ),
    ParserTemplateCreate(
        template_name="LOTOS_EXCEL",
        description="LOTOS Excel profit sheet parser template",
        mode="ANY",
        direction="ANY",
        file_type="EXCEL",
        customer_keyword="CUSTOMER,Customer,고객,CONSIGNEE,SHIPPER",
        partner_keyword="PARTNER,AGENT,파트너",
        revenue_section_keywords=COMMON_REVENUE_KEYWORDS,
        expense_section_keywords=COMMON_EXPENSE_KEYWORDS,
        profit_keywords=COMMON_PROFIT_KEYWORDS,
        duty_keywords=COMMON_DUTY_KEYWORDS,
        consumption_tax_keywords=COMMON_CONSUMPTION_TAX_KEYWORDS,
        transport_keywords=COMMON_TRANSPORT_KEYWORDS,
        customs_keywords=COMMON_CUSTOMS_KEYWORDS,
        partner_fee_keywords=COMMON_PARTNER_FEE_KEYWORDS,
        food_keywords=COMMON_FOOD_KEYWORDS,
        is_default=False,
    ),
]


def _to_partner_fee_rule_read(rule: models.PartnerFeeRule) -> PartnerFeeRuleRead:
    return PartnerFeeRuleRead(
        id=rule.id,
        partner_name=rule.partner_name,
        mode=rule.mode,
        direction=rule.direction,
        container_type=rule.container_type,
        unit_type=rule.unit_type,
        currency=rule.currency,
        amount=rule.amount,
        settlement_direction=rule.settlement_direction,
        special_condition=rule.special_condition,
        valid_from=rule.valid_from,
        valid_to=rule.valid_to,
        is_active=rule.is_active,
        note=rule.note,
    )


def _to_minimum_gp_rule_read(rule: models.MinimumGPRule) -> MinimumGPRuleRead:
    return MinimumGPRuleRead(
        id=rule.id,
        code=rule.code,
        minimum_gp_jpy=rule.minimum_gp_jpy,
        description=rule.description,
        is_active=rule.is_active,
    )


def _to_gp_rate_rule_read(rule: models.GPRateRule) -> GPRateRuleRead:
    return GPRateRuleRead(
        id=rule.id,
        trade_type=rule.trade_type,
        minimum_gp_rate=rule.minimum_gp_rate,
        description=rule.description,
        is_active=rule.is_active,
    )


def _to_work_code_rule_read(rule: models.WorkCodeRule) -> WorkCodeRuleRead:
    return WorkCodeRuleRead(
        id=rule.id,
        code=rule.code,
        name=rule.name,
        mode=rule.mode,
        direction=rule.direction,
        has_customs=rule.has_customs,
        has_transport=rule.has_transport,
        has_work=rule.has_work,
        point=rule.point,
        description=rule.description,
        is_active=rule.is_active,
    )


def _to_internal_resource_rule_read(
    rule: models.InternalResourceRule,
) -> InternalResourceRuleRead:
    return InternalResourceRuleRead(
        id=rule.id,
        resource_type=rule.resource_type,
        port=rule.port,
        location_name=rule.location_name,
        vendor_name=rule.vendor_name,
        priority=rule.priority,
        mandatory=rule.mandatory,
        description=rule.description,
        is_active=rule.is_active,
    )


def _to_required_charge_rule_read(
    rule: models.RequiredChargeRule,
) -> RequiredChargeRuleRead:
    return RequiredChargeRuleRead(
        id=rule.id,
        code=rule.code,
        mode=rule.mode,
        direction=rule.direction,
        charge_name=rule.charge_name,
        keywords=rule.keywords,
        required_when=rule.required_when,
        severity=rule.severity,
        description=rule.description,
        is_active=rule.is_active,
    )


def _to_parser_template_read(rule: models.ParserTemplate) -> ParserTemplateRead:
    return ParserTemplateRead(
        id=rule.id,
        template_name=rule.template_name,
        description=rule.description,
        mode=rule.mode,
        direction=rule.direction,
        file_type=rule.file_type,
        customer_keyword=rule.customer_keyword,
        partner_keyword=rule.partner_keyword,
        revenue_section_keywords=rule.revenue_section_keywords,
        expense_section_keywords=rule.expense_section_keywords,
        profit_keywords=rule.profit_keywords,
        duty_keywords=rule.duty_keywords,
        consumption_tax_keywords=rule.consumption_tax_keywords,
        transport_keywords=rule.transport_keywords,
        customs_keywords=rule.customs_keywords,
        partner_fee_keywords=rule.partner_fee_keywords,
        food_keywords=rule.food_keywords,
        is_default=rule.is_default,
        is_active=rule.is_active,
    )


def _validate_work_code_payload(
    payload: WorkCodeRuleCreate,
    db: Session,
    current_rule_id: int | None = None,
) -> None:
    if payload.code not in ALLOWED_WORK_CODES:
        raise HTTPException(status_code=400, detail="Invalid work code")
    if payload.point < 0:
        raise HTTPException(status_code=400, detail="Point must be greater than or equal to 0")
    if payload.is_active:
        duplicate = db.execute(
            select(models.WorkCodeRule).where(
                models.WorkCodeRule.code == payload.code,
                models.WorkCodeRule.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if duplicate is not None and duplicate.id != current_rule_id:
            raise HTTPException(status_code=400, detail="Active work code already exists")


def _create_partner_fee_rule(
    db: Session,
    payload: PartnerFeeRuleCreate,
) -> models.PartnerFeeRule:
    rule = models.PartnerFeeRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/partner-fees", response_model=PartnerFeeRuleRead)
def create_partner_fee_rule(
    payload: PartnerFeeRuleCreate,
    db: Session = Depends(get_db),
) -> PartnerFeeRuleRead:
    return _to_partner_fee_rule_read(_create_partner_fee_rule(db, payload))


@router.get("/partner-fees", response_model=list[PartnerFeeRuleRead])
def list_partner_fee_rules(
    partner_name: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> list[PartnerFeeRuleRead]:
    statement = select(models.PartnerFeeRule).order_by(models.PartnerFeeRule.id)
    if partner_name is not None:
        statement = statement.where(
            models.PartnerFeeRule.partner_name.ilike(f"%{partner_name}%")
        )
    if is_active is not None:
        statement = statement.where(models.PartnerFeeRule.is_active == is_active)
    return [
        _to_partner_fee_rule_read(rule) for rule in db.execute(statement).scalars()
    ]


@router.post("/minimum-gp", response_model=MinimumGPRuleRead)
def upsert_minimum_gp_rule(
    payload: MinimumGPRuleCreate,
    db: Session = Depends(get_db),
) -> MinimumGPRuleRead:
    rule = db.execute(
        select(models.MinimumGPRule).where(models.MinimumGPRule.code == payload.code)
    ).scalar_one_or_none()
    if rule is None:
        rule = models.MinimumGPRule(**payload.model_dump())
        db.add(rule)
    else:
        rule.minimum_gp_jpy = payload.minimum_gp_jpy
        rule.description = payload.description
        rule.is_active = payload.is_active
    db.commit()
    db.refresh(rule)
    return _to_minimum_gp_rule_read(rule)


@router.get("/minimum-gp", response_model=list[MinimumGPRuleRead])
def list_minimum_gp_rules(db: Session = Depends(get_db)) -> list[MinimumGPRuleRead]:
    rules = db.execute(
        select(models.MinimumGPRule).order_by(models.MinimumGPRule.code)
    ).scalars()
    return [_to_minimum_gp_rule_read(rule) for rule in rules]


@router.post("/gp-rate-rules", response_model=GPRateRuleRead)
def upsert_gp_rate_rule(
    payload: GPRateRuleCreate,
    db: Session = Depends(get_db),
) -> GPRateRuleRead:
    rule = db.execute(
        select(models.GPRateRule).where(
            models.GPRateRule.trade_type == payload.trade_type
        )
    ).scalar_one_or_none()
    if rule is None:
        rule = models.GPRateRule(**payload.model_dump())
        db.add(rule)
    else:
        rule.minimum_gp_rate = payload.minimum_gp_rate
        rule.description = payload.description
        rule.is_active = payload.is_active
    db.commit()
    db.refresh(rule)
    return _to_gp_rate_rule_read(rule)


@router.get("/gp-rate-rules", response_model=list[GPRateRuleRead])
def list_gp_rate_rules(db: Session = Depends(get_db)) -> list[GPRateRuleRead]:
    rules = db.execute(
        select(models.GPRateRule).order_by(models.GPRateRule.trade_type)
    ).scalars()
    return [_to_gp_rate_rule_read(rule) for rule in rules]


@router.post("/work-code-rules", response_model=WorkCodeRuleRead)
def upsert_work_code_rule(
    payload: WorkCodeRuleCreate,
    db: Session = Depends(get_db),
) -> WorkCodeRuleRead:
    rule = db.execute(
        select(models.WorkCodeRule).where(models.WorkCodeRule.code == payload.code)
    ).scalar_one_or_none()
    _validate_work_code_payload(
        payload,
        db,
        current_rule_id=rule.id if rule is not None else None,
    )
    if rule is None:
        rule = models.WorkCodeRule(**payload.model_dump())
        db.add(rule)
    else:
        for key, value in payload.model_dump().items():
            setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return _to_work_code_rule_read(rule)


@router.get("/work-code-rules", response_model=list[WorkCodeRuleRead])
def list_work_code_rules(db: Session = Depends(get_db)) -> list[WorkCodeRuleRead]:
    rules = db.execute(
        select(models.WorkCodeRule).order_by(models.WorkCodeRule.code)
    ).scalars()
    return [_to_work_code_rule_read(rule) for rule in rules]


@router.put("/work-code-rules/{rule_id}", response_model=WorkCodeRuleRead)
def update_work_code_rule(
    rule_id: int,
    payload: WorkCodeRuleCreate,
    db: Session = Depends(get_db),
) -> WorkCodeRuleRead:
    rule = db.get(models.WorkCodeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Work code rule not found")
    _validate_work_code_payload(payload, db, current_rule_id=rule_id)
    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return _to_work_code_rule_read(rule)


@router.delete("/work-code-rules/{rule_id}", response_model=WorkCodeRuleRead)
def deactivate_work_code_rule(
    rule_id: int,
    db: Session = Depends(get_db),
) -> WorkCodeRuleRead:
    rule = db.get(models.WorkCodeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Work code rule not found")
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return _to_work_code_rule_read(rule)


@router.post("/internal-resource-rules", response_model=InternalResourceRuleRead)
def upsert_internal_resource_rule(
    payload: InternalResourceRuleCreate,
    db: Session = Depends(get_db),
) -> InternalResourceRuleRead:
    rule = db.execute(
        select(models.InternalResourceRule).where(
            models.InternalResourceRule.resource_type == payload.resource_type,
            models.InternalResourceRule.port == payload.port,
        )
    ).scalar_one_or_none()
    if rule is None:
        rule = models.InternalResourceRule(**payload.model_dump())
        db.add(rule)
    else:
        rule.location_name = payload.location_name
        rule.vendor_name = payload.vendor_name
        rule.priority = payload.priority
        rule.mandatory = payload.mandatory
        rule.description = payload.description
        rule.is_active = payload.is_active
    db.commit()
    db.refresh(rule)
    return _to_internal_resource_rule_read(rule)


@router.get("/internal-resource-rules", response_model=list[InternalResourceRuleRead])
def list_internal_resource_rules(
    resource_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[InternalResourceRuleRead]:
    statement = select(models.InternalResourceRule).order_by(
        models.InternalResourceRule.resource_type,
        models.InternalResourceRule.port,
    )
    if resource_type is not None:
        statement = statement.where(
            models.InternalResourceRule.resource_type == resource_type
        )
    rules = db.execute(statement).scalars()
    return [_to_internal_resource_rule_read(rule) for rule in rules]


@router.put("/internal-resource-rules/{rule_id}", response_model=InternalResourceRuleRead)
def update_internal_resource_rule(
    rule_id: int,
    payload: InternalResourceRuleCreate,
    db: Session = Depends(get_db),
) -> InternalResourceRuleRead:
    rule = db.get(models.InternalResourceRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Internal resource rule not found")
    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return _to_internal_resource_rule_read(rule)


@router.delete("/internal-resource-rules/{rule_id}", response_model=InternalResourceRuleRead)
def deactivate_internal_resource_rule(
    rule_id: int,
    db: Session = Depends(get_db),
) -> InternalResourceRuleRead:
    rule = db.get(models.InternalResourceRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Internal resource rule not found")
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return _to_internal_resource_rule_read(rule)


@router.post("/required-charge-rules", response_model=RequiredChargeRuleRead)
def create_required_charge_rule(
    payload: RequiredChargeRuleCreate,
    db: Session = Depends(get_db),
) -> RequiredChargeRuleRead:
    rule = models.RequiredChargeRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _to_required_charge_rule_read(rule)


@router.get("/required-charge-rules", response_model=list[RequiredChargeRuleRead])
def list_required_charge_rules(
    code: str | None = None,
    mode: str | None = None,
    direction: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> list[RequiredChargeRuleRead]:
    statement = select(models.RequiredChargeRule).order_by(
        models.RequiredChargeRule.code,
        models.RequiredChargeRule.charge_name,
    )
    if code is not None:
        statement = statement.where(models.RequiredChargeRule.code == code)
    if mode is not None:
        statement = statement.where(models.RequiredChargeRule.mode == mode)
    if direction is not None:
        statement = statement.where(models.RequiredChargeRule.direction == direction)
    if is_active is not None:
        statement = statement.where(models.RequiredChargeRule.is_active == is_active)
    rules = db.execute(statement).scalars()
    return [_to_required_charge_rule_read(rule) for rule in rules]


@router.put("/required-charge-rules/{rule_id}", response_model=RequiredChargeRuleRead)
def update_required_charge_rule(
    rule_id: int,
    payload: RequiredChargeRuleCreate,
    db: Session = Depends(get_db),
) -> RequiredChargeRuleRead:
    rule = db.get(models.RequiredChargeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Required charge rule not found")
    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return _to_required_charge_rule_read(rule)


@router.delete("/required-charge-rules/{rule_id}", response_model=RequiredChargeRuleRead)
def deactivate_required_charge_rule(
    rule_id: int,
    db: Session = Depends(get_db),
) -> RequiredChargeRuleRead:
    rule = db.get(models.RequiredChargeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Required charge rule not found")
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return _to_required_charge_rule_read(rule)


@router.post("/parser-templates", response_model=ParserTemplateRead)
def upsert_parser_template(
    payload: ParserTemplateCreate,
    db: Session = Depends(get_db),
) -> ParserTemplateRead:
    rule = db.execute(
        select(models.ParserTemplate).where(
            models.ParserTemplate.template_name == payload.template_name
        )
    ).scalar_one_or_none()
    if rule is None:
        rule = models.ParserTemplate(**payload.model_dump())
        db.add(rule)
    else:
        for key, value in payload.model_dump().items():
            setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return _to_parser_template_read(rule)


@router.get("/parser-templates", response_model=list[ParserTemplateRead])
def list_parser_templates(
    file_type: str | None = None,
    mode: str | None = None,
    direction: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> list[ParserTemplateRead]:
    statement = select(models.ParserTemplate).order_by(
        models.ParserTemplate.file_type,
        models.ParserTemplate.direction,
        models.ParserTemplate.template_name,
    )
    if file_type is not None:
        statement = statement.where(models.ParserTemplate.file_type == file_type)
    if mode is not None:
        statement = statement.where(models.ParserTemplate.mode == mode)
    if direction is not None:
        statement = statement.where(models.ParserTemplate.direction == direction)
    if is_active is not None:
        statement = statement.where(models.ParserTemplate.is_active == is_active)
    rules = db.execute(statement).scalars()
    return [_to_parser_template_read(rule) for rule in rules]


@router.put("/parser-templates/{template_id}", response_model=ParserTemplateRead)
def update_parser_template(
    template_id: int,
    payload: ParserTemplateCreate,
    db: Session = Depends(get_db),
) -> ParserTemplateRead:
    rule = db.get(models.ParserTemplate, template_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Parser template not found")
    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return _to_parser_template_read(rule)


@router.delete("/parser-templates/{template_id}", response_model=ParserTemplateRead)
def deactivate_parser_template(
    template_id: int,
    db: Session = Depends(get_db),
) -> ParserTemplateRead:
    rule = db.get(models.ParserTemplate, template_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Parser template not found")
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return _to_parser_template_read(rule)


@router.post("/seed-defaults", response_model=SeedDefaultsResponse)
def seed_defaults(db: Session = Depends(get_db)) -> SeedDefaultsResponse:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    partner_fee_rules_created = 0
    for payload in DEFAULT_PARTNER_FEE_RULES:
        existing = db.execute(
            select(models.PartnerFeeRule).where(
                models.PartnerFeeRule.partner_name == payload.partner_name,
                models.PartnerFeeRule.mode == payload.mode,
                models.PartnerFeeRule.direction == payload.direction,
                models.PartnerFeeRule.unit_type == payload.unit_type,
                models.PartnerFeeRule.amount == payload.amount,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(models.PartnerFeeRule(**payload.model_dump()))
            partner_fee_rules_created += 1

    minimum_gp_rules_upserted = 0
    for code, minimum_gp_jpy in MINIMUM_GP_RULES.items():
        upsert_minimum_gp_rule(
            MinimumGPRuleCreate(
                code=code,
                minimum_gp_jpy=minimum_gp_jpy,
                description=f"{code} 기본 Minimum GP",
                is_active=True,
            ),
            db,
        )
        minimum_gp_rules_upserted += 1

    gp_rate_rules_upserted = 0
    for payload in DEFAULT_GP_RATE_RULES:
        upsert_gp_rate_rule(payload, db)
        gp_rate_rules_upserted += 1

    work_code_rules_upserted = 0
    for payload in DEFAULT_WORK_CODE_RULES:
        upsert_work_code_rule(payload, db)
        work_code_rules_upserted += 1

    internal_resource_rules_upserted = 0
    for payload in DEFAULT_INTERNAL_RESOURCE_RULES:
        upsert_internal_resource_rule(payload, db)
        internal_resource_rules_upserted += 1

    required_charge_rules_upserted = 0
    for payload in DEFAULT_REQUIRED_CHARGE_RULES:
        existing = db.execute(
            select(models.RequiredChargeRule).where(
                models.RequiredChargeRule.code == payload.code,
                models.RequiredChargeRule.mode == payload.mode,
                models.RequiredChargeRule.direction == payload.direction,
                models.RequiredChargeRule.charge_name == payload.charge_name,
                models.RequiredChargeRule.required_when == payload.required_when,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(models.RequiredChargeRule(**payload.model_dump()))
        else:
            for key, value in payload.model_dump().items():
                setattr(existing, key, value)
        required_charge_rules_upserted += 1

    parser_templates_upserted = 0
    for payload in DEFAULT_PARSER_TEMPLATES:
        upsert_parser_template(payload, db)
        parser_templates_upserted += 1

    users_upserted = 0
    for payload in DEFAULT_USERS:
        user_data = payload.model_dump(exclude={"password"})
        if payload.password:
            user_data["hashed_password"] = hash_password(payload.password)
        existing = db.execute(
            select(models.User).where(models.User.username == payload.username)
        ).scalar_one_or_none()
        if existing is None:
            db.add(models.User(**user_data))
        else:
            for key, value in user_data.items():
                setattr(existing, key, value)
        users_upserted += 1

    parser_validation_cases_upserted = 0
    for payload in DEFAULT_PARSER_VALIDATION_CASES:
        existing = db.execute(
            select(models.ParserValidationCase).where(
                models.ParserValidationCase.case_name == payload.case_name
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(models.ParserValidationCase(**payload.model_dump()))
        else:
            for key, value in payload.model_dump().items():
                setattr(existing, key, value)
        parser_validation_cases_upserted += 1

    db.commit()
    return SeedDefaultsResponse(
        partner_fee_rules_created=partner_fee_rules_created,
        minimum_gp_rules_upserted=minimum_gp_rules_upserted,
        gp_rate_rules_upserted=gp_rate_rules_upserted,
        work_code_rules_upserted=work_code_rules_upserted,
        internal_resource_rules_upserted=internal_resource_rules_upserted,
        required_charge_rules_upserted=required_charge_rules_upserted,
        parser_templates_upserted=parser_templates_upserted,
        users_upserted=users_upserted,
        parser_validation_cases_upserted=parser_validation_cases_upserted,
    )
