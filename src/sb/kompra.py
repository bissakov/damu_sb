from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from time import sleep
from types import TracebackType
from typing import Any, Literal, NamedTuple, Type, override

from playwright.sync_api import sync_playwright
from pydantic import BaseModel, ConfigDict, ValidationError, validator
from pydantic.alias_generators import to_camel

from utils.request_handler import RequestHandler

logger = logging.getLogger("DAMU")


class ElementNotFoundError(Exception): ...


class ServiceNotAvailableError(Exception): ...


class SessionNotAuthenticatedError(Exception): ...


class TokenError(Exception): ...


class DataNotFetchedRequestError(Exception): ...


class DataNotFetchedError(Exception): ...


class Status(StrEnum):
    YES = "YES"
    NO = "NO"
    SYNC = "SYNC"
    INIT = "INIT"


class Company(BaseModel):
    class Oked(BaseModel):
        code: str
        name_kz: str
        name_ru: str

    class Krp(BaseModel):
        code: int
        name_kz: str
        name_ru: str

    id: int
    identifier: str
    name: str
    full_name: str
    register_date: datetime | None
    last_register_date: datetime | None
    secondary_oked: str | None
    law_address: str
    ownership: str
    ip: bool
    oked: Oked
    kbe: str
    krp: Krp
    astana_hub: bool
    gos_register: bool
    big_taxpayer: bool
    opi: bool
    region: str


class Owner(BaseModel):
    class Person(BaseModel):
        id: int
        name: str
        identifier: str | None
        person: bool

    identifier: str
    status: str
    last_updated: datetime
    owner: Person
    appointment_date: datetime
    founder: list[Person]
    founders_count: int
    header_organization: str | None
    owner_loss_date: str | None
    owner_risk_factor_status: bool
    founders_fl_risk_factor: str
    founders_ul_risk_factor: str

    @validator("last_updated", "appointment_date", pre=True)
    def parse_dates(cls, v: str) -> datetime:
        return datetime.strptime(v, "%d.%m.%Y")


class Certificate(BaseModel):
    id: int
    created: datetime
    last_updated: datetime
    identifier: str
    status: str
    edoc_ru: str
    edoc_kk: str

    @validator("created", "last_updated", pre=True)
    def parse_dates(cls, v: str):
        return datetime.fromisoformat(v)


class Properties(NamedTuple):
    auto: bool
    property: bool
    land: bool


class AdmFinesStatus(NamedTuple):
    status: Status
    total_count: int
    unpaid: int


class TaxArrear(BaseModel):
    class TaxOrg(BaseModel):
        class TaxPayer(BaseModel):
            class BccArrear(BaseModel):
                bcc: str
                bcc_name_ru: str
                bcc_name_kz: str
                tax_arrear: float
                poena_arrear: float
                percent_arrear: float
                fine_arrear: float
                total_arrear: float

            iin_bin: str
            name_ru: str
            name_kz: str
            bcc_arrears_info: list[BccArrear]
            tax_arrear: float
            poena_arrear: float
            percent_arrear: float
            fine_arrear: float
            total_arrear: float

        char_code: str
        name_ru: str
        name_kz: str
        report_acrual_date: datetime
        total_arrear: float
        total_tax_arrear: float
        pension_contribution_arrear: float
        social_contribution_arrear: float
        social_healthInsurance_arrear: float
        tax_payer_info: list[TaxPayer]

    send_time: str
    iin_bin: str
    total_arrear: float
    total_tax_arrear: float
    pension_contribution_arrear: float
    social_contribution_arrear: float
    social_health_insurance_arrear: float
    tax_org_info: list[TaxOrg]
    name: str


class RawSummary(BaseModel):
    class Record(BaseModel):
        class Tag(BaseModel):
            tag: str
            recom: str | None

        status: str
        data: list[Tag]

        @validator("status", pre=True)
        def parse_status(cls, status: str) -> Status:
            return Status(status)

    risk: Record
    attention: Record
    positive: Record


class CaseType(IntEnum):
    CIVIL = 1
    CRIMINAL = 2
    ADMIN = 3


class Case(BaseModel):
    category: str
    number: str
    part: str
    type_id: CaseType
    date: datetime | None
    id: int
    organ: str
    plaintiff: str | None
    defendant: str | None
    role: str | None
    result: str
    status: str | None
    year: int

    @validator("type_id", pre=True)
    def parse_status(cls, type_id: int) -> CaseType:
        return CaseType(type_id)


class Cases:
    def __init__(self, cases: list[Case] | None = None) -> None:
        if cases:
            self._cases: list[Case] = cases
        else:
            self._cases = []

    def append(self, case: Case) -> None:
        if not isinstance(case, Case):
            raise TypeError(f"Expected item of type {self._type.__name__}")
        self._cases.append(case)

    def __getitem__(self, index: int) -> Case:
        return self._cases[index]

    def __len__(self) -> int:
        return len(self._cases)

    def __iter__(self):
        return iter(self._cases)

    def has_cases(self, case_type: CaseType, max_delta: int = 3) -> bool:
        if case_type != CaseType.CRIMINAL:
            today = datetime.fromisoformat(os.environ["today"])
            return any(
                abs(today.year - case.year) <= max_delta
                for case in self
                if case.type_id == case_type
            )
        else:
            return any(case.type_id == case_type for case in self)

    def remove_cases(self, case_type: CaseType) -> None:
        self._cases = [case for case in self if case.type_id != case_type]

    def __repr__(self) -> str:
        return str(self._cases)


class CaseHistory(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    identifier: str
    content: Cases
    size: int
    total_pages: int
    total_elements: int
    current_page: int
    type_1_count: int  # Гражданский
    type_2_count: int  # Уголовный
    type_3_count: int  # Административный
    plaintiff_count: int
    defendant_count: int
    no_role_count: int

    @validator("content", pre=True)
    def parse_content(cls, content: list[dict[str, Any]]) -> Cases:
        return Cases([Case(**case) for case in content])


class Relation(BaseModel):
    identifier: str
    name: str


class Affiliate(NamedTuple):
    id: str
    name: str


class RawRiskAPI(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    class RiskType(BaseModel):
        id: int
        name: str

    class TaxDebt(BaseModel):
        class TaxOrg(BaseModel):
            class TaxPayer(BaseModel):
                class BccArrear(BaseModel):
                    bcc: str
                    bcc_name_ru: str
                    bcc_name_kz: str
                    tax_arrear: float
                    poena_arrear: float
                    percent_arrear: float
                    fine_arrear: float
                    total_arrear: float

                iin_bin: str
                name_ru: str
                name_kz: str
                bcc_arrears_info: list[BccArrear]
                tax_arrear: float
                poena_arrear: float
                percent_arrear: float
                fine_arrear: float
                total_arrear: float

            name_kz: str
            name_ru: str
            char_code: str
            total_arrear: str
            tax_payer_info: list[TaxPayer]

        name: str
        iin_bin: str
        send_time: datetime
        tax_org_info: list[TaxOrg]

    class DebtorLeaveRK(BaseModel):
        sum: int
        date: datetime
        debtor: str
        number: str
        status: str | None
        essence: str
        claimant: str
        debtor_bin: str | None
        debtor_iin: str
        ip_start_date: datetime
        ban_start_date: datetime
        court_executive: str
        document_executive: str

    type: RiskType
    content: list[TaxDebt | DebtorLeaveRK] | dict[str, Any]
    status: Status

    @validator("status", pre=True)
    def parse_status(cls, status: str) -> Status:
        return Status(status)


class Token(NamedTuple):
    access_token: str
    refresh_token: str
    expiry_ts: float

    def save(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(self._asdict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> Token:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        expiry_ts = data["expiry_ts"]
        token_cache = Token(access_token, refresh_token, expiry_ts)
        return token_cache

    def is_relevant(self) -> bool:
        return time.time() < self.expiry_ts


class Kompra(RequestHandler):
    def __init__(
        self,
        user: str,
        password: str,
        base_url: str,
        api_token: str,
        download_folder: Path,
        token_cache_path: Path,
        user_agent: str,
    ) -> None:
        super().__init__(user, password, base_url, download_folder)
        self.token_cache_path = token_cache_path
        self.user_agent = user_agent
        self.api_token = api_token

        self._token: Token | None = None

        self.client.headers = {
            "user-agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    @property
    def token(self) -> Token:
        if self._token:
            if self._token.is_relevant():
                # logger.debug("Token exists and relevant")
                return self._token
            else:
                # logger.debug("Token has been expired, refreshing")
                if not self.refresh(self._token):
                    self.login()

                if self._token:
                    return self._token
                else:
                    raise TokenError(
                        "Something went wrong while load/refreshing access token"
                    )

        if self.token_cache_path.exists():
            if self.token_cache_path.stat().st_size == 0:
                self.token_cache_path.unlink()
                self._token = None
            # logger.debug("Loading token from disk")
            self._token = Token.load(self.token_cache_path)
            return self._token
        else:
            self.login()
            if self._token:
                return self._token
            else:
                raise TokenError(
                    "Something went wrong while load/refreshing access token"
                )

        if not self._token:
            raise TokenError(
                "Something went wrong while load/refreshing access token"
            )

    def login(self) -> bool:
        logger.info("Fetching token")

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": "Basic d2ViX2FwcDpxd2VydHk=",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
            "priority": "u=1, i",
            "referer": self.base_url,
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
        }

        data = {
            "grant_type": "password",
            "username": self.user,
            "password": self.password,
        }

        response = self.request(
            method="post", path="oauth/token", headers=headers, data=data
        )
        if not response:
            return False

        if not hasattr(response, "json"):
            return False

        data = response.json()

        if not {"access_token", "refresh_token", "expires_in"} <= data.keys():
            raise Exception(f"Auth exception - {data!r}")

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        expires_in = data["expires_in"]
        expiry_ts = time.time() + expires_in - 30

        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expiry_ts=expiry_ts,
        )
        token.save(self.token_cache_path)

        logger.info("Successfully captured new token")

        self._token = token

        return True

    def refresh(self, token: Token) -> bool:
        logger.info("Refreshing old token")

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": "Basic d2ViX2FwcDpxd2VydHk=",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
            "priority": "u=1, i",
            "referer": self.base_url,
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
        }

        data = {
            "grant_type": "refresh_token",
            "username": self.user,
            "password": self.password,
            "refresh_token": token.refresh_token,
        }

        response = self.request(
            method="post", path="oauth/token", headers=headers, data=data
        )
        if not response:
            return False

        if not hasattr(response, "json"):
            return False

        data = response.json()

        if not {"access_token", "refresh_token", "expires_in"} <= data.keys():
            raise Exception(f"Auth exception - {data!r}")

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        expires_in = data["expires_in"]
        expiry_ts = time.time() + expires_in - 30

        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expiry_ts=expiry_ts,
        )
        token.save(self.token_cache_path)

        logger.info("Successfully refreshed old token")

        self._token = token
        return True

    def get_enterprise(self, iin: str) -> Company:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/company/{iin}",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()

        company = Company(**data)
        return company

    def get_owner(self, iin: str) -> Owner:
        if not self.token:
            self.login()
        assert self.token

        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/company/management/{iin}",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()

        # logger.info(f"{data=!r}")

        try:
            owner = Owner(**data)
        except ValidationError as err:
            for e in err.errors():
                logger.error(e)
            raise err

        return owner

    def get_certificate(self, iin: str) -> Certificate:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        params = {"ignore_cache": "false"}

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/egov_services/{iin}/reg-certificate",
            overwrite_path=True,
            params=params,
            headers=headers,
        )

        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        certificate = Certificate(**data)
        return certificate

    def get_properties(self, iin: str) -> Properties:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/property/{iin}/status",
            overwrite_path=True,
            headers=headers,
        )

        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        auto: bool = data["auto_status"] == "YES"
        property: bool = data["property_status"] == "YES"
        land: bool = data["land_status"] == "YES"

        properties = Properties(auto=auto, property=property, land=land)
        return properties

    def get_adm_fines(self, iin: str) -> AdmFinesStatus:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/adm_fines/{iin}/status",
            overwrite_path=True,
            headers=headers,
        )

        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        status: Status = Status(data["status"])
        total_count: int = data["total_count"]
        unpaid: int = data["unpaid"]

        adm_fines_status = AdmFinesStatus(
            status=status, total_count=total_count, unpaid=unpaid
        )
        return adm_fines_status

    def _get_risks(self, iin: str) -> dict[str, bool]:
        context = self.browser.new_context(ignore_https_errors=True)
        with context:
            page = context.new_page()
            page.goto(self.base_url)
            page.locator("button.button:nth-child(4)").click()

            page.locator("#auth-email").fill(self.user)
            page.locator('input[name="password"]').fill(self.password)

            with page.expect_response("https://kompra.kz/oauth/token") as info:
                page.locator(
                    "form.ng-dirty:nth-child(1) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1)"
                ).click()
            resp = info.value
            if resp.status != 200 and not resp.ok:
                logger.error(f"Status - {resp.status}, text - {resp.json()}")
                raise SessionNotAuthenticatedError()

            logger.info("Session authenticated")

            page.goto(f"https://kompra.kz/ru/card/company/{iin}")
            sleep(5)

            risks: dict[str, str] = {}
            for current_retry in range(5):
                raw = page.evaluate(
                    "() => [...document.querySelectorAll('.details__risks .alert__header')].map(el => el.textContent.trim())"
                )

                has_malformed = False

                for text in raw:
                    key, value = f"{text.strip()}  ".split("  ", maxsplit=1)
                    logger.debug(f"{key=!r}, {value=!r}")
                    has_malformed = not value or value == "СЕРВИС НЕДОСТУПЕН"
                    risks[key.strip()] = value.strip()
                else:
                    logger.debug(f"Risks count: {len(risks)}")
                    if not has_malformed:
                        break

            res = {
                key: val == "ДА"
                for key, val in risks.items()
                if val and val != "СЕРВИС НЕДОСТУПЕН"
            }

            logger.info("Risks fetched")
            logger.info(f"Risks count: {len(res)}")

            return res

    def _get_risks_api(self, iin: str) -> dict[str, bool]:
        params = {"identifier": iin, "api-token": self.api_token}

        response = self.request(
            method="get", path="/api/v2/reliability-list", params=params
        )

        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        raw_risks: list[RawRiskAPI] = []
        for row in data:
            try:
                raw_risks.append(RawRiskAPI(**row))
            except ValidationError as err:
                for e in err.errors():
                    logger.error(e)
                raise err

        risks: dict[str, bool] = {
            row.type.name: status
            for row in raw_risks
            if (status := (row.status == "YES"))
        }

        return risks

    def get_risks(
        self,
        type: Literal["api", "browser"],
        iin: str,
        max_retries: int = 5,
        time_between: int = 10,
    ) -> dict[str, bool]:
        _get_risks = self._get_risks_api if type == "api" else self._get_risks

        risks = None

        for _ in range(max_retries):
            try:
                risks = _get_risks(iin)
                return risks
            except ServiceNotAvailableError:
                logger.debug(
                    f"Service currently unavailable. Sleeping for {time_between}..."
                )
                sleep(time_between)
                continue

        if not risks:
            raise ValueError()

        return risks

    def get_relations(self, iin: str, is_too: bool) -> list[Relation]:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        params = {"page": "1", "page_size": "20"}
        path = (
            f"https://gateway.kompra.kz/participation/{iin}/list"
            if is_too
            else f"https://gateway.kompra.kz/participation/fl/{iin}/list"
        )

        response = self.request(
            method="get",
            path=path,
            overwrite_path=True,
            params=params,
            headers=headers,
        )
        if not response:
            # raise DataNotFetchedRequestError()
            return []

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        relations = [Relation(**row) for row in data.get("content", [])]
        return relations

    def get_relation_status(self, iin: str) -> Status:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/relations/{iin}/status",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        status = Status(data["status"])
        return status

    def start_schema_generation(self, iin: str) -> Status:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/relations/{iin}/start",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        status = Status(data["status"])
        while status != Status.YES:
            status = self.get_relation_status(iin)
            logger.info(
                "Waiting until relation schema is completed. "
                f"Current status - {status}..."
            )
            sleep(5)

        return status

    def get_relation_schema(self, iin: str) -> dict[str, Any]:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/relations/{iin}/content",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        return data

    def get_affiliates(self, iin: str) -> list[Affiliate]:
        def add_affiliate(
            _affiliates: list[Affiliate], obj: dict[str, Any]
        ) -> None:
            if not obj:
                return

            id = obj.get("identifier", "")
            name = obj.get("ip_name") or obj.get("name", "")
            affiliate = Affiliate(id=id, name=name)
            if affiliate not in _affiliates:
                _affiliates.append(affiliate)

        schema = self.get_relation_schema(iin)

        affiliates: list[Affiliate] = []
        for node in (schema.get("content") or {}).values():
            add_affiliate(affiliates, node)
            add_affiliate(affiliates, node.get("owner") or {})

            records = (
                node.get("founders", [])
                + node.get("founded", [])
                + node.get("directed", [])
                + node.get("involvement", [])
                + node.get("branch", [])
            )
            for record in records:
                add_affiliate(affiliates, record)
        return affiliates

    def get_tax_arrears(self, iin: str) -> TaxArrear:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/risk_factor_core/fl/{iin}/tax-arrears/details",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        tax_arrear = TaxArrear(**data)
        return tax_arrear

    def get_reliability_summary(self, iin: str) -> set[str]:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        raw_summary: RawSummary | None = None
        risk_is_synced = False
        current_retry = 0
        while not risk_is_synced or current_retry < 5:
            raw_summary = None
            response = self.request(
                method="get",
                path=f"https://gateway.kompra.kz/company/{iin}/reliability_summary",
                overwrite_path=True,
                headers=headers,
            )

            if not response:
                raise DataNotFetchedRequestError()

            if not hasattr(response, "json"):
                raise DataNotFetchedError()

            data = response.json()
            raw_summary = RawSummary(**data)

            logger.debug(f"Raw summary: {raw_summary}")

            logger.debug(f"Risk status: {raw_summary.risk.status}")
            logger.debug(f"Attention status: {raw_summary.attention.status}")

            current_retry += 1

            if raw_summary.risk.status == "YES" or current_retry >= 5:
                risk_is_synced = True
                break
            sleep(5)

        assert raw_summary

        summary = set(
            [
                tag.tag
                for tag in raw_summary.risk.data
                if " степень риска" not in tag.tag
            ]
            + [
                tag.tag
                for tag in raw_summary.attention.data
                if " степень риска" not in tag.tag
            ]
        )

        return summary

    def get_case_status(self, iin: str) -> Status:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/cases/{iin}/status",
            overwrite_path=True,
            headers=headers,
        )
        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()

        status = Status(data["status"])
        return status

    def get_case_history(self, iin: str) -> Cases:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        json_data = {"type_id": [], "role": [], "year": []}
        params = {"page": "1", "page_size": "20"}

        response = self.request(
            method="post",
            path=f"https://gateway.kompra.kz/cases/{iin}/list",
            overwrite_path=True,
            json=json_data,
            params=params,
            headers=headers,
        )

        if not response:
            sleep(60)

            response = self.request(
                method="post",
                path=f"https://gateway.kompra.kz/cases/{iin}/list",
                overwrite_path=True,
                json=json_data,
                params=params,
                headers=headers,
            )
            if not response:
                raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        case_history = CaseHistory(**data)
        cases = case_history.content
        return cases

    @override
    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._token = None
        self.browser.close()
        self.playwright.stop()
        super().__exit__(exc_type, exc_val, exc_tb)
