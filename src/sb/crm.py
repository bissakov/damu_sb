from __future__ import annotations

import dataclasses
import json
import logging
import re
import traceback
from collections.abc import Generator
from datetime import date, datetime, timedelta
from json.decoder import JSONDecodeError
from pathlib import Path
from types import TracebackType
from typing import Any, Type, cast, override

import pandas as pd
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from sb.structures import Registry
from utils.request_handler import RequestHandler

logger = logging.getLogger("DAMU")


class Activity(BaseModel):
    id: str
    guarantee_id: str
    responsible_person: str
    guarantee: Guarantee | None = None
    files: list[GuaranteeFile] = dataclasses.field(default_factory=list)


class Guarantee(BaseModel):
    guarantee_id: str
    bank: str
    credit_period: int
    crediting_purpose: str
    credit_amount: float
    registration_date: datetime
    guarantee_amount: float
    guarantee_period: int


@dataclasses.dataclass
class GuaranteeFile:
    file_id: str
    file_path: Path
    created_on: datetime
    file_type: str


class Schemas:
    def __init__(self, schema_json_path: Path) -> None:
        self.schema_json_path = schema_json_path

        self.schemas: dict[str, Any]
        try:
            with open(schema_json_path, "r", encoding="utf-8") as f:
                self.schemas = json.load(f)
        except JSONDecodeError:
            with open(schema_json_path, "r", encoding="utf-8-sig") as f:
                self.schemas = json.load(f)

    def activities(self) -> dict[str, Any]:
        return self.schemas["activities"]

    def guarantee(self, guarantee_id: str) -> dict[str, Any]:
        schema = self.schemas["guarantee"]
        schema["filters"]["items"]["primaryColumnFilter"]["rightExpression"][
            "parameter"
        ]["value"] = guarantee_id
        return schema

    def guarantee_file(self, guarantee_id: str) -> dict[str, Any]:
        schema = self.schemas["guarantee_file"]
        schema["filters"]["items"]["entityFilterGroup"]["items"][
            "masterRecordFilter"
        ]["rightExpression"]["parameter"]["value"] = guarantee_id

        schema["filters"]["items"]["entityFilterGroup"]["items"][
            "0c40db70-f3e2-4fd2-a999-e7fa53fe60cf"
        ]["rightExpression"]["parameter"]["value"] = guarantee_id

        return schema


class CRM(RequestHandler):
    def __init__(
        self,
        user: str,
        password: str,
        base_url: str,
        download_folder: Path,
        user_agent: str,
        schema_json_path: Path,
    ) -> None:
        super().__init__(user, password, base_url, download_folder)
        self.client.headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://crm.fund.kz",
            "priority": "u=1, i",
            "referer": "https://crm.fund.kz/Login/NuiLogin.aspx?ReturnUrl=%2f%3fsimpleLogin&simpleLogin",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": user_agent,
            "x-request-source": "ajax-provider",
            "x-requested-with": "XMLHttpRequest",
        }

        self.schemas = Schemas(schema_json_path)
        self.is_logged_in = False

    def login(self) -> bool:
        credentials = {
            "UserName": self.user,
            "UserPassword": self.password,
            "TimeZoneOffset": -300,
        }

        logger.info("Fetching '.ASPXAUTH', 'BPMCSRF', and 'UserName' cookies")
        if not self.request(
            method="post",
            path="servicemodel/authservice.svc/login",
            json=credentials,  # type: ignore
            update_cookies=True,
        ):
            logger.error(
                "Request failed while fetching '.ASPXAUTH', 'BPMCSRF', and 'UserName' cookies"
            )
            self.is_logged_in = False
            return False
        logger.info(
            "Fetched '.ASPXAUTH', 'BPMCSRF', and 'UserName' cookies successfully"
        )

        logger.debug("Extracting 'BPMCSRF' token from cookies")
        self.client.headers["BPMCSRF"] = (
            self.client.cookies.get("BPMCSRF") or ""
        )
        logger.info("'BPMCSRF' token added to headers")

        logger.info("Login process completed successfully")
        self.is_logged_in = True
        return True

    def get_unfinished_activities(self) -> list[Activity] | None:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.activities()

        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if not hasattr(response, "json"):
            return None

        data = response.json()
        rows: list[dict[str, Any]] = data.get("rows", [])

        activities: list[Activity] = []
        for row in rows:
            guarantee = row.get("Guarantee", {})
            id = guarantee.get("value", "")
            if not id:
                continue

            activity = Activity(
                id=id,
                guarantee_id=guarantee.get("displayValue"),
                responsible_person=row.get("Owner", {}).get("displayValue"),
            )
            activities.append(activity)
        return activities

    def get_guarantee(self, guarantee_id: str) -> Guarantee | None:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.guarantee(guarantee_id)

        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if not hasattr(response, "json"):
            return None

        data = response.json()
        row: dict[str, Any] = rows[0] if (rows := data.get("rows", [])) else {}
        # bank = row.get("Bank", {}).get("displayValue")
        # credit_period = row.get("CreditPeriod")
        # crediting_purpose = row.get("CreditingPurpose", {}).get("displayValue")
        # credit_amount = row.get("CreditAmount")
        # registration_date_str = row.get("RegistrationDate")
        #
        # try:
        #     registration_date = datetime.fromisoformat(registration_date_str)
        # except ValueError as e:
        #     # FIXME TEMP
        #     raise e

        input_data = {
            "guarantee_id": guarantee_id,
            "bank": row.get("Bank", {}).get("displayValue"),
            "credit_period": row.get("CreditPeriod"),
            "crediting_purpose": row.get("CreditingPurpose", {}).get(
                "displayValue"
            ),
            "credit_amount": row.get("CreditAmount"),
            "registration_date": datetime.fromisoformat(
                row.get("RegistrationDate", "")
            ),
            "guarantee_amount": row.get("GuaranteeAmount"),
            "guarantee_period": row.get("GuaranteePeriod"),
        }

        guarantee = Guarantee(**input_data)
        return guarantee

    def download_guarantee_files(
        self, guarantee_id: str, download_folder: Path
    ) -> list[GuaranteeFile]:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.guarantee_file(guarantee_id)

        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return []

        if not hasattr(response, "json"):
            return []

        data = response.json()
        rows: list[dict[str, Any]] = data.get("rows", [])

        files: list[GuaranteeFile] = []
        for row in rows:
            file_id: str = row["Id"]
            file_name: str = row["Name"]

            if not file_name.endswith(".docx"):
                continue

            created_on = datetime.fromisoformat(cast(str, row["CreatedOn"]))
            file_type: str = row["Type"]["displayValue"]

            file_name, file_ext = file_name.rsplit(".", maxsplit=1)
            file_name = f"{file_name.strip()}.{file_ext}"

            file_path = download_folder / Path(
                f"{guarantee_id}/crm/{file_name}"
            )

            if not self.download_file(file_id, file_path, download_folder):
                raise Exception(
                    f"File {file_path.name!r} of {file_id!r} not downloaded"
                )

            guaranatee_file = GuaranteeFile(
                file_id=file_id,
                file_path=file_path,
                created_on=created_on,
                file_type=file_type,
            )

            files.append(guaranatee_file)

        return files

    def download_file(
        self, file_id: str, file_path: Path, download_folder: Path
    ) -> bool:
        if not self.is_logged_in:
            self.login()

        file_path.parent.mkdir(exist_ok=True, parents=True)

        response = self.request(
            method="get",
            path=f"0/rest/FileService/GetFile/0cf61736-d494-4029-8b1c-a33dd58edfc3/{file_id}",
        )
        if not response:
            self.is_logged_in = False
            return False

        with file_path.open("wb") as f:
            f.write(response.content)

        return True

    def find_project(self, protocol_id: str) -> dict[str, Any] | None:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.project_info(protocol_id)

        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if not hasattr(response, "json"):
            return None

        data = response.json()
        rows: list[dict[str, Any]] = data.get("rows")

        if not rows:
            return None

        row = rows[0]

        return row

    def get_project_data(self, project_id: str) -> dict[str, Any] | None:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.project(project_id)

        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if hasattr(response, "json"):
            data = response.json()
            rows = data.get("rows")
            assert isinstance(rows, list)
            return rows[0]  # type: ignore
        else:
            return None

    def fetch_agreement_data(self, project_id: str) -> dict[str, Any] | None:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.agreements(project_id)

        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if hasattr(response, "json"):
            data = response.json()
            rows = data.get("rows")
            assert isinstance(rows, list)
            if rows:
                return rows[0]  # type: ignore

        return None

    def fetch_vypiska_id(self, project_id: str) -> dict[str, Any] | None:
        if not self.is_logged_in:
            self.login()

        json_data = self.schemas.vypiska_project(project_id)
        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if not hasattr(response, "json"):
            return None

        data = response.json()
        rows = data.get("rows")
        assert isinstance(rows, list)

        vypiska_row = next(
            (
                row
                for row in rows
                if row.get("Type", {}).get("displayValue") == "Выписка ДС"
            ),
            None,
        )

        return vypiska_row

    def download_vypiska(
        self, contract_id: str, file_id: str, file_name: str
    ) -> bool:
        folder_path = self.download_folder / contract_id / "vypiska"
        folder_path.mkdir(exist_ok=True)

        file_path = folder_path / file_name

        response = self.request(
            method="get",
            path=f"0/rest/FileService/GetFile/7b332db9-3993-4136-ac32-09353333cc7a/{file_id}",
        )
        if not response:
            self.is_logged_in = False
            return False

        with file_path.open("wb") as f:
            f.write(response.content)

        return True

    def download_vypiskas(
        self, contract_id: str, project_id: str
    ) -> dict[str, Any] | None:
        if not self.is_logged_in:
            self.login()

        vypiska_row = self.fetch_vypiska_id(project_id=project_id)
        if not isinstance(vypiska_row, dict):
            return None

        vypiska_id = vypiska_row.get("Id")
        if not vypiska_id:
            return None

        json_data = self.schemas.vypiska(vypiska_id=vypiska_id)
        response = self.request(
            method="post",
            path="0/DataService/json/SyncReply/SelectQuery",
            json=json_data,
        )
        if not response:
            self.is_logged_in = False
            return None

        if not hasattr(response, "json"):
            return None

        data = response.json()
        rows = data.get("rows")
        assert isinstance(rows, list)

        for row in rows:
            file_id, file_name = row.get("Id"), row.get("Name")
            file_name = file_name.replace("/", " ").replace("\\", " ")
            if not file_id or not file_name:
                continue
            self.download_vypiska(
                contract_id=contract_id, file_id=file_id, file_name=file_name
            )

        return vypiska_row

    @override
    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.is_logged_in = False
        super().__exit__(exc_type, exc_val, exc_tb)
