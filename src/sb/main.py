import logging
import os
import pickle
import sys
from datetime import datetime
from pathlib import Path
from time import sleep

import dotenv
import pytz

project_folder = Path(__file__).resolve().parent.parent.parent
os.environ["project_folder"] = str(project_folder)
os.chdir(project_folder)
sys.path.append(str(project_folder))
sys.path.append(str(project_folder / "utils"))

from sb.conclusion import (
    fill_conclusion_ip,
    fill_conclusion_too,
    get_guarant_list,
    get_participant_list,
)
from sb.crm import CRM, Activity
from sb.kompra import CaseType, Kompra, Status
from sb.structures import Registry
from utils.utils import setup_logger

today = datetime.now(pytz.timezone("Asia/Almaty")).date()
os.environ["today"] = today.isoformat()
setup_logger(today)

logger = logging.getLogger("DAMU")


def main() -> None:
    logger.info("START process")

    dotenv.load_dotenv(".env")

    kompra_user = os.environ["KOMPRA_USERNAME"]
    kompra_password = os.environ["KOMPRA_PASSWORD"]
    kompra_base_url = os.environ["KOMPRA_BASE_URL"]

    registry = Registry()

    crm = CRM(
        user=os.environ["CRM_USERNAME"],
        password=os.environ["CRM_PASSWORD"],
        base_url=os.environ["CRM_BASE_URL"],
        download_folder=registry.download_folder,
        user_agent=os.environ["USER_AGENT"],
        schema_json_path=registry.schema_json_path,
    )

    kompra = Kompra(
        user=kompra_user,
        password=kompra_password,
        base_url=kompra_base_url,
        api_token=os.environ["KOMPRA_API_TOKEN"],
        download_folder=registry.download_folder,
        token_cache_path=registry.token_cache_path,
        user_agent=os.environ["USER_AGENT"],
    )

    logger.info("Data loaded")

    # with crm:
    #     activities = crm.get_unfinished_activities()
    #
    #     if not activities:
    #         logger.info("0 activities found...")
    #         return
    #
    #     logger.info(f"Found {len(activities)} unfinished activities...")
    #
    #     for activity in activities:
    #         logger.info(
    #             f"Working on {activity.id=!r} of {activity.responsible_person!r}"
    #         )
    #         activity.guarantee = crm.get_guarantee(activity.id)
    #         logger.info(f"Guarantee data fetched - {activity.guarantee=!r}")
    #         activity.files = crm.download_guarantee_files(
    #             activity.id, registry.download_folder
    #         )
    #         logger.info(f"Found {len(activity.files)} attached files")
    #
    #         for file in activity.files:
    #             if file.path.exists():
    #                 logger.info(f"{file.path.name} downloaded")
    #             else:
    #                 logger.error(f"{file.path.name} was not downloaded")
    #
    #     if __debug__:
    #         with open("resources/data.pkl", "wb") as f:
    #             pickle.dump(activities, f)
    #
    # print(len(activities))
    # return

    with open("resources/data.pkl", "rb") as f:
        activities: list[Activity] = pickle.load(f)

    with kompra:
        for activity in activities:
            assert activity.guarantee

            file = next((file for file in activity.files if file.is_26), None)
            if not file:
                continue

            participants = file.get_participants()
            if not participants:
                continue

            logger.info(f"Working on {file.path.as_posix()!r}")

            participant = next(
                (p for p in participants if p.is_too), participants[0]
            )
            logger.info(f"{participant=!r}")

            iin = participant.iin

            # NOTE: TEMP
            # relations = kompra.get_relations(iin=iin, is_too=participant.is_too)
            # logger.info(f"{relations=!r}")

            enterprise = kompra.get_enterprise(iin)
            logger.info(f"{enterprise=!r}")

            risks = kompra.get_risks(type="browser", iin=iin)

            if risks.get("Налоговая задолженность", False):
                tax_arrear = kompra.get_tax_arrears(iin)
                logger.info(f"{tax_arrear=!r}")

            if kompra.get_case_status(iin) == Status.YES:
                cases = kompra.get_case_history(iin)

                if risks.get("Административные правонарушения", False):
                    if cases.has_cases(CaseType.ADMIN):
                        # TODO
                        logger.info("Has ADMIN cases in the past 3 years")
                    else:
                        logger.info(
                            "No 'Административные правонарушения' in the past 3 years"
                        )
                        risks.pop("Административные правонарушения", None)
                        cases.remove_cases(CaseType.ADMIN)

                if cases.has_cases(CaseType.CRIMINAL):
                    risks["Уголовные разбирательства"] = True
                    # TODO
                    logger.info("Has CRIMINAL cases")
                else:
                    logger.info(
                        "No history of 'Уголовные разбирательства' found"
                    )
                    cases.remove_cases(CaseType.CRIMINAL)

                if cases.has_cases(CaseType.CIVIL):
                    # TODO
                    logger.info("Has CIVIL cases in the past 3 years")
                    risks["Гражданские разбирательства"] = True
                else:
                    logger.info(
                        "No 'Гражданские разбирательства' in the past 3 years"
                    )
                    cases.remove_cases(CaseType.CIVIL)

                logger.info(f"{cases=!r}")
            logger.info(f"{risks=!r}")

            guarant_list = get_guarant_list(participants)

            schema_status = kompra.get_relation_status(iin)
            logger.info(f"{schema_status=!r}")

            if schema_status in [Status.NO, Status.INIT]:
                kompra.start_schema_generation(iin)

            while (status := kompra.get_relation_status(iin)) != Status.YES:
                logger.info(
                    "Waiting until relation schema is completed. "
                    f"Current status - {status}..."
                )
                sleep(5)

            affiliates = kompra.get_affiliates(iin)
            logger.info(f"{affiliates=!r}")

            if participant.is_too:
                owner = kompra.get_owner(iin)
                logger.info(f"{owner=!r}")

                participant_list = get_participant_list(participants)

                owner_participant = next(
                    p for p in participants if "руководитель" in p.role.lower()
                )

                fill_conclusion_too(
                    template_path=str(registry.too_conclusion_template),
                    company=enterprise,
                    owner=owner_participant,
                    activity=activity,
                    participant_list=participant_list,
                    guarant_list=guarant_list,
                )
            else:
                fill_conclusion_ip(
                    template_path=str(registry.ip_conclusion_template),
                    enterprise=enterprise,
                    activity=activity,
                    guarant_list=guarant_list,
                )

            print("=" * 200)


if __name__ == "__main__":
    try:
        main()
    finally:
        logger.info("FINISH process")
