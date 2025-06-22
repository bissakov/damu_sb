import logging
import pickle
from datetime import date, datetime
from pathlib import Path

import pytz

from sb.crm import Activity


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        filename = record.filename.rsplit(".", maxsplit=1)[0]
        record.file_line = f"{filename}:{record.lineno}".ljust(18)
        return super().format(record)


def setup_logger(_today: date | None = None) -> None:
    log_format = "[%(asctime)s] %(levelname)-5s %(file_line)s %(message)s"
    formatter = CustomFormatter(log_format, datefmt="%H:%M:%S")

    damu = logging.getLogger("DAMU")
    damu.setLevel(logging.DEBUG)

    formatter.converter = lambda *args: datetime.now(
        pytz.timezone("Asia/Almaty")
    ).timetuple()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    log_folder = Path("logs")
    log_folder.mkdir(exist_ok=True, parents=True)

    if _today is None:
        _today = datetime.now(pytz.timezone("Asia/Almaty")).date()

    today_str = _today.strftime("%d.%m.%y")
    year_month_folder = log_folder / _today.strftime("%Y/%B")
    year_month_folder.mkdir(parents=True, exist_ok=True)
    logger_file = year_month_folder / f"{today_str}.log"

    file_handler = logging.FileHandler(logger_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    damu.addHandler(stream_handler)
    damu.addHandler(file_handler)


def prettify_number(n: float) -> str:
    return f"{n:,.2f}".replace(",", " ").replace(".", ",")
