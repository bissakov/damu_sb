from pathlib import Path

MONTHS = {
    "янв": "01",
    "фев": "02",
    "мар": "03",
    "апр": "04",
    "май": "05",
    "мая": "05",
    "маю": "05",
    "мае": "05",
    "июн": "06",
    "июл": "07",
    "авг": "08",
    "сен": "09",
    "окт": "10",
    "ноя": "11",
    "дек": "12",
    "қан": "01",
    "қаң": "01",
    "ақп": "02",
    "нау": "03",
    "сәу": "04",
    "cәү": "04",
    "cәу": "04",
    "мам": "05",
    "мау": "06",
    "шіл": "07",
    "там": "08",
    "қыр": "09",
    "қаз": "10",
    "каз": "10",
    "қар": "11",
    "жел": "12",
}


class Registry:
    def __init__(self) -> None:
        self.download_folder: Path = Path("downloads")
        self.download_folder.mkdir(parents=True, exist_ok=True)

        self.resources_folder: Path = Path("resources")
        self.database = self.resources_folder / "database.sqlite"
        self.token_cache_path = self.resources_folder / "token_cache.json"

        self.schema_json_path = self.resources_folder / "schemas.json"

        self.too_conclusion_template = (
            self.resources_folder / "too_conclusion_template.docx"
        )
        self.ip_conclusion_template = (
            self.resources_folder / "ip_conclusion_template.docx"
        )
