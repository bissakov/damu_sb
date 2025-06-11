from __future__ import annotations

import dataclasses
import json
import logging
import os
import re
import time
import traceback
from collections.abc import Generator
from datetime import date, datetime, timedelta
from json.decoder import JSONDecodeError
from pathlib import Path
from time import sleep
from types import TracebackType
from typing import Any, Literal, NamedTuple, Type, TypedDict, cast, override
from urllib.parse import urljoin

import httpx
import pandas as pd
from dateutil.relativedelta import relativedelta
from httpx import Client, Cookies, Headers, RequestError, Response
from playwright.sync_api import Browser, FrameLocator, Page, sync_playwright
from pydantic import BaseModel, ValidationError, validator

from sb.structures import Registry
from utils.request_handler import RequestHandler

logger = logging.getLogger("DAMU")


class ElementNotFoundError(Exception): ...


class ServiceNotAvailableError(Exception): ...


class SessionNotAuthenticatedError(Exception): ...


class TokenError(Exception): ...


class CompanyNotFetchedRequestError(Exception): ...


class CompanyNotFetchedError(Exception): ...


class OwnerNotFetchedRequestError(Exception): ...


class OwnerNotFetchedError(Exception): ...


class CertificateNotFetchedRequestError(Exception): ...


class CertificateNotFetchedError(Exception): ...


class DataNotFetchedRequestError(Exception): ...


class DataNotFetchedError(Exception): ...


class Company(BaseModel):
    class Kato(BaseModel):
        id: int
        parent_id: int
        code: str
        name_kz: str
        name_ru: str

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
    kato: Kato
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
    def parse_dates(cls, v: str):
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
    status: bool
    total_count: int
    unpaid: int


class RawSummary(BaseModel):
    class Record(BaseModel):
        class Tag(BaseModel):
            tag: str
            recom: str | None

        status: str
        data: list[Tag]

    risk: Record
    attention: Record
    positive: Record


class CaseHistory(BaseModel):
    class Case(BaseModel):
        category: str
        number: str
        part: str
        type_id: int
        date: datetime | None
        id: int
        organ: str
        plaintiff: str | None
        defendant: str | None
        role: str | None
        result: str
        status: str | None
        year: int

    identifier: str
    content: list[Case]
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
        download_folder: Path,
        token_cache_path: Path,
        user_agent: str,
    ) -> None:
        super().__init__(user, password, base_url, download_folder)
        self.token_cache_path = token_cache_path
        self.user_agent = user_agent

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

    @property
    def token(self) -> Token:
        if self._token:
            if self._token.is_relevant():
                # logger.debug("Token exists and relevant")
                return self._token
            else:
                # logger.debug("Token has been expired, refreshing")
                self.refresh(self._token)
                return self._token

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
            raise CompanyNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise CompanyNotFetchedError()

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
            raise OwnerNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise OwnerNotFetchedError()

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
            raise CertificateNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise CertificateNotFetchedError()

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
        status: bool = data["status"] == "YES"
        total_count: int = data["total_count"]
        unpaid: int = data["unpaid"]

        adm_fines_status = AdmFinesStatus(
            status=status, total_count=total_count, unpaid=unpaid
        )
        return adm_fines_status

    def risk_tax_arrear_status(self, iin: str) -> bool:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/risk_factor_core/{iin}/tax-arrears/status",
            overwrite_path=True,
            headers=headers,
        )

        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        status = data["status"] == "YES"
        return status

    def risk_mock_taxpayer(self, iin: str) -> bool:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        response = self.request(
            method="get",
            path=f"https://gateway.kompra.kz/risk_factor_core/{iin}/mock_taxpayer/status",
            overwrite_path=True,
            headers=headers,
        )

        if not response:
            raise DataNotFetchedRequestError()

        if not hasattr(response, "json"):
            raise DataNotFetchedError()

        data = response.json()
        print(f"{response.text!r}")
        status = data["status"] == "YES"
        return status

    def _get_risks(self, iin: str) -> dict[str, bool]:
        with sync_playwright() as playwright:
            logger.info("Playwright started")
            browser = playwright.chromium.launch(headless=True)
            with browser:
                logger.info("Browser launched")
                context = browser.new_context(ignore_https_errors=True)

                page = context.new_page()
                page.goto(self.base_url)
                page.locator("button.button:nth-child(4)").click()

                page.locator("#auth-email").fill(self.user)
                page.locator('input[name="password"]').fill(self.password)

                with page.expect_response(
                    "https://kompra.kz/oauth/token"
                ) as info:
                    page.locator(
                        "form.ng-dirty:nth-child(1) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1)"
                    ).click()
                resp = info.value
                if resp.status != 200 and not resp.ok:
                    raise SessionNotAuthenticatedError()

                logger.info("Session authenticated")

                page.goto(f"https://kompra.kz/ru/card/company/{iin}")

                risks: dict[str, bool] = {}
                while True:
                    raw = page.evaluate(
                        "() => [...document.querySelectorAll('.details__risks .alert__header')].map(el => el.textContent.trim())"
                    )

                    for text in raw:
                        if "СЕРВИС НЕДОСТУПЕН" in text:
                            continue

                        try:
                            key, value = text.strip().split("  ")
                            status = value == "ДА"
                            if status:
                                risks[key.strip()] = status
                        except ValueError:
                            if "СЕРВИС НЕДОСТУПЕН" in text:
                                raise ServiceNotAvailableError()
                            logger.debug(f"Malformed string: {text}")
                            sleep(1)
                            break
                    else:
                        logger.debug(f"Risks count: {len(risks)}")
                        break

                logger.info(f"Risks fetched")
                logger.info(f"Risks count: {len(risks)}")
                return risks

    def get_risks(
        self, iin: str, max_retries: int = 5, time_between: int = 60
    ) -> dict[str, bool]:
        for _ in range(max_retries):
            try:
                return self._get_risks(iin)
            except ServiceNotAvailableError:
                logger.debug(
                    f"Service currently unavailable. Sleeping for {time_between}..."
                )
                sleep(time_between)
                continue
        raise ServiceNotAvailableError

    def get_reliability_summary(self, iin: str) -> set[str]:
        headers = self.client.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.token.access_token}"

        params = {"ip": "false"}

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

    def get_case_status(self, iin: str) -> bool:
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

        status = data["status"] == "YES"
        return status

    def get_case_history(self, iin: str) -> CaseHistory:
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
        print(data)
        case_history = CaseHistory(**data)
        return case_history

    @override
    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._token = None
        super().__exit__(exc_type, exc_val, exc_tb)
