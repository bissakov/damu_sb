from datetime import datetime
from pathlib import Path

from sb.crm import Activity, Guarantee, GuaranteeFile

activities = [
    Activity(
        id="c1ca4fac-6363-48c9-968d-882acc0ab008",
        guarantee_id="107046",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="c1ca4fac-6363-48c9-968d-882acc0ab008",
            bank='АО "Народный Банк Казахстана"',
            credit_period=72,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=250000000.0,
            registration_date=datetime(2025, 6, 10, 16, 22, 6, 3000),
            guarantee_amount=122295443.63,
            guarantee_period=72,
        ),
        files=[],
    ),
    Activity(
        id="91b1e032-093a-43f8-8bb7-7cd3d8b0a2eb",
        guarantee_id="107049",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="91b1e032-093a-43f8-8bb7-7cd3d8b0a2eb",
            bank='АО "First Heartland Jusan Bank"',
            credit_period=84,
            crediting_purpose="Инвестиции",
            credit_amount=436414081.0,
            registration_date=datetime(2025, 6, 10, 16, 31, 47, 38000),
            guarantee_amount=270000000.0,
            guarantee_period=84,
        ),
        files=[],
    ),
    Activity(
        id="e084924b-616f-42b7-b48d-7b4807b897a8",
        guarantee_id="84743",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="e084924b-616f-42b7-b48d-7b4807b897a8",
            bank='АО "Исламский Банк "ADCB"',
            credit_period=36,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=500000000.0,
            registration_date=datetime(2023, 12, 13, 9, 17, 12, 131000),
            guarantee_amount=250000000.0,
            guarantee_period=36,
        ),
        files=[
            GuaranteeFile(
                id="87ceebb6-ebff-493b-b40d-ecf0b04c1d24",
                path=Path(
                    "downloads/e084924b-616f-42b7-b48d-7b4807b897a8/crm/Сведения о зарег.ЮЛ ТОО Зерде-Керамика.docx"
                ),
                created_on=datetime(2023, 12, 14, 12, 4, 58, 184000),
                type="Файл",
            ),
            GuaranteeFile(
                id="d893800f-65c0-4b09-8eb8-68bbb7bde69b",
                path=Path(
                    "downloads/e084924b-616f-42b7-b48d-7b4807b897a8/crm/Данные_для_СБ_ТОО_Зерде_Керамика.docx"
                ),
                created_on=datetime(2023, 12, 13, 10, 34, 54, 649000),
                type="Файл",
            ),
        ],
    ),
    Activity(
        id="15e4984f-6b59-4529-8654-6bd65db0ce91",
        guarantee_id="60986",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="15e4984f-6b59-4529-8654-6bd65db0ce91",
            bank='АО "ForteBank"',
            credit_period=84,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=44000000.0,
            registration_date=datetime(2022, 10, 6, 14, 48, 8, 198000),
            guarantee_amount=17000000.0,
            guarantee_period=84,
        ),
        files=[
            GuaranteeFile(
                id="21dad105-48e4-428a-ae4a-2bbe88b17b02",
                path=Path(
                    "downloads/15e4984f-6b59-4529-8654-6bd65db0ce91/crm/Заключение ДБ по ИП Триандофилиди.docx"
                ),
                created_on=datetime(2022, 10, 12, 17, 2, 16, 838000),
                type="Файл",
            ),
            GuaranteeFile(
                id="3c93e827-0f35-4bdc-8788-7fed0530747c",
                path=Path(
                    "downloads/15e4984f-6b59-4529-8654-6bd65db0ce91/crm/Приложение+для+СБ+№+26.docx"
                ),
                created_on=datetime(2022, 10, 11, 16, 43, 37, 105000),
                type="Файл",
            ),
        ],
    ),
    Activity(
        id="7e4587d1-eb11-458c-be3c-41d0f44d1c82",
        guarantee_id="107043",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="7e4587d1-eb11-458c-be3c-41d0f44d1c82",
            bank='АО "Банк ЦентрКредит"',
            credit_period=60,
            crediting_purpose="Инвестиции",
            credit_amount=117000000.0,
            registration_date=datetime(2025, 6, 10, 16, 16, 3, 766000),
            guarantee_amount=32500000.0,
            guarantee_period=60,
        ),
        files=[
            GuaranteeFile(
                id="9efdc375-7e1e-48db-896a-e375c74b5709",
                path=Path(
                    "downloads/7e4587d1-eb11-458c-be3c-41d0f44d1c82/crm/МО ИП Аянай 1,2 транши.docx"
                ),
                created_on=datetime(2025, 6, 10, 16, 24, 21, 337000),
                type="Файл",
            )
        ],
    ),
    Activity(
        id="3c786206-b655-4540-ab5d-342ed1b01da8",
        guarantee_id="107059",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="3c786206-b655-4540-ab5d-342ed1b01da8",
            bank='АО "Фридом Банк Казахстан"',
            credit_period=72,
            crediting_purpose="Инвестиции",
            credit_amount=600000000.0,
            registration_date=datetime(2025, 6, 11, 8, 53, 16, 907000),
            guarantee_amount=300000000.0,
            guarantee_period=72,
        ),
        files=[],
    ),
    Activity(
        id="4f66ebdf-442f-4b9f-b7d5-5282e3086b9a",
        guarantee_id="61276",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="4f66ebdf-442f-4b9f-b7d5-5282e3086b9a",
            bank='АО "First Heartland Jusan Bank"',
            credit_period=60,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=300000000.0,
            registration_date=datetime(2022, 10, 10, 15, 35, 30, 542000),
            guarantee_amount=150000000.0,
            guarantee_period=60,
        ),
        files=[
            GuaranteeFile(
                id="2d01a80d-cd5a-4160-bbf4-ef23c48670a1",
                path=Path(
                    "downloads/4f66ebdf-442f-4b9f-b7d5-5282e3086b9a/crm/ЭЗ_РФ TOO DEGIR MEN.docx"
                ),
                created_on=datetime(2022, 10, 12, 9, 38, 1, 968000),
                type="Файл",
            )
        ],
    ),
    Activity(
        id="b236a720-5a27-490b-bdba-b8c2d0545899",
        guarantee_id="107055",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="b236a720-5a27-490b-bdba-b8c2d0545899",
            bank='АО "Банк ЦентрКредит"',
            credit_period=84,
            crediting_purpose="Инвестиции",
            credit_amount=200000000.0,
            registration_date=datetime(2025, 6, 10, 17, 24, 50, 299000),
            guarantee_amount=129100000.0,
            guarantee_period=84,
        ),
        files=[
            GuaranteeFile(
                id="60292853-647d-4033-9846-892ac0fb1ddf",
                path=Path(
                    "downloads/b236a720-5a27-490b-bdba-b8c2d0545899/crm/№ 26 қосымша.docx"
                ),
                created_on=datetime(2025, 6, 10, 17, 28, 30, 460000),
                type="Файл",
            )
        ],
    ),
    Activity(
        id="8d4e7f07-a719-4030-8adf-679b046b7827",
        guarantee_id="107044",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="8d4e7f07-a719-4030-8adf-679b046b7827",
            bank='АО "Народный Банк Казахстана"',
            credit_period=60,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=138500000.0,
            registration_date=datetime(2025, 6, 10, 16, 17, 32, 977000),
            guarantee_amount=69250000.0,
            guarantee_period=60,
        ),
        files=[
            GuaranteeFile(
                id="e556db9b-acec-44dc-8eb6-cf7ce7f2db29",
                path=Path(
                    "downloads/8d4e7f07-a719-4030-8adf-679b046b7827/crm/№ 26 қосымша.docx"
                ),
                created_on=datetime(2025, 6, 10, 16, 21, 39, 220000),
                type="Файл",
            ),
            GuaranteeFile(
                id="69eb6044-c5f5-4516-bbf0-911cdac9072f",
                path=Path(
                    "downloads/8d4e7f07-a719-4030-8adf-679b046b7827/crm/ЖК_Байтасов Аскар Булатович.docx"
                ),
                created_on=datetime(2025, 6, 10, 16, 20, 45, 213000),
                type="Файл",
            ),
        ],
    ),
    Activity(
        id="5dfc8573-32fa-46d7-bca3-e41500154614",
        guarantee_id="24655",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="5dfc8573-32fa-46d7-bca3-e41500154614",
            bank='АО "First Heartland Jusan Bank"',
            credit_period=36,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=20000000.0,
            registration_date=datetime(2021, 2, 9, 16, 10, 25, 22000),
            guarantee_amount=17000000.0,
            guarantee_period=36,
        ),
        files=[],
    ),
    Activity(
        id="8c80a039-ca64-48ab-a26c-af490e74600d",
        guarantee_id="107048",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="8c80a039-ca64-48ab-a26c-af490e74600d",
            bank='АО "Народный Банк Казахстана"',
            credit_period=72,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=100000000.0,
            registration_date=datetime(2025, 6, 10, 16, 29, 21, 66000),
            guarantee_amount=50000000.0,
            guarantee_period=72,
        ),
        files=[
            GuaranteeFile(
                id="0fba3dc2-ef34-47b7-be79-d3df3d409495",
                path=Path(
                    "downloads/8c80a039-ca64-48ab-a26c-af490e74600d/crm/№ 26 қосымша.docx"
                ),
                created_on=datetime(2025, 6, 10, 16, 33, 4, 912000),
                type="Файл",
            ),
            GuaranteeFile(
                id="09c66edb-9102-424b-8d82-3c32583b15f1",
                path=Path(
                    "downloads/8c80a039-ca64-48ab-a26c-af490e74600d/crm/ЖК_Байтасов Аскар Булатович.docx"
                ),
                created_on=datetime(2025, 6, 10, 16, 32, 56, 620000),
                type="Файл",
            ),
        ],
    ),
    Activity(
        id="79f52b22-1d8c-488e-9355-912279bca7ed",
        guarantee_id="45367",
        responsible_person="Абилмажинов Болатхан Айтжанович",
        guarantee=Guarantee(
            guarantee_id="79f52b22-1d8c-488e-9355-912279bca7ed",
            bank='АО "Народный Банк Казахстана"',
            credit_period=36,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=60000000.0,
            registration_date=datetime(2022, 3, 15, 15, 58, 23, 654000),
            guarantee_amount=11031500.0,
            guarantee_period=36,
        ),
        files=[],
    ),
    Activity(
        id="7fa11018-fe4f-4182-b5b7-6cbf57a9b532",
        guarantee_id="106606",
        responsible_person="Килыбаев Айдын Серикович",
        guarantee=Guarantee(
            guarantee_id="7fa11018-fe4f-4182-b5b7-6cbf57a9b532",
            bank='АО "Банк ЦентрКредит"',
            credit_period=36,
            crediting_purpose="Пополнение оборотных средств",
            credit_amount=100000000.0,
            registration_date=datetime(2025, 5, 27, 12, 27, 24, 67000),
            guarantee_amount=43500000.0,
            guarantee_period=36,
        ),
        files=[],
    ),
]
