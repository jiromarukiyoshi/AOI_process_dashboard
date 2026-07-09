import datetime
import logging
import re
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


AOI_PROJECT_NO = "F0002"
TRACE_SUMMARY_VIEW = "FCSEUC_TRACE_SUMMARY_V"
COMPLETED_STATUS = "作業終了"
EXCLUDED_STATUS = "削除"
PACK_PRODUCT_CODES = {"FFC00000005", "FFC00000006", "10021052698", "10021052720"}
CASH_PRODUCT_CODES = {
    "10022112247",
    "FFC00000009",
    "FFC00000010",
    "FFC00000011",
    "FFC00000012",
    "FFC00000013",
    "FFC00000014",
    "FFC00000015",
    "FFC00000017",
    "13001222527",
    "13001222528",
    "13001222532",
    "13001222531",
    "13001223107",
    "13001222938",
    "13001222937",
}
ORACLE_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_#$]*$")
logger = logging.getLogger(__name__)


class ShipmentDatesView(APIView):
    def get(self, request):
        try:
            if settings.AOI_USE_MOCK_DATA:
                return Response(sorted({row["ship_date"] for row in build_mock_source_rows()}))

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT DISTINCT "FFC出荷日"
                    FROM {oracle_name(TRACE_SUMMARY_VIEW)}
                    WHERE "FFC案件NO" = :project_no
                    ORDER BY "FFC出荷日"
                    """,
                    {"project_no": AOI_PROJECT_NO},
                )
                return Response([date_to_str(row[0]) for row in cursor.fetchall()])
        except Exception as exc:
            logger.exception("Failed to fetch AOI shipment dates.")
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AoiDashboardView(APIView):
    def get(self, request):
        try:
            ship_date = request.query_params.get("ship_date")
            if not ship_date:
                dates = sorted({row["ship_date"] for row in self.fetch_source_rows(None)})
                ship_date = dates[0] if dates else datetime.date.today().isoformat()
            parse_date(ship_date)

            rows = self.fetch_source_rows(ship_date)
            payload = build_dashboard_payload(rows, ship_date)
            return Response(payload)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Failed to fetch AOI dashboard data.")
            if not settings.AOI_USE_MOCK_DATA:
                rows = [row for row in build_mock_source_rows() if row["ship_date"] == request.query_params.get("ship_date")]
                if rows:
                    return Response(build_dashboard_payload(rows, request.query_params.get("ship_date")))
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def fetch_source_rows(self, ship_date):
        if settings.AOI_USE_MOCK_DATA:
            rows = build_mock_source_rows()
            if ship_date:
                rows = [row for row in rows if row["ship_date"] == ship_date]
            return rows

        params = {"project_no": AOI_PROJECT_NO}
        date_clause = ""
        if ship_date:
            date_clause = 'AND "FFC出荷日" = TO_DATE(:ship_date, \'YYYY-MM-DD\')'
            params["ship_date"] = ship_date

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    "FFC出荷日",
                    "FFC出荷NO",
                    "枝番",
                    "店舗番号",
                    "店名",
                    "製品コード",
                    "ステータス（Fコード）"
                FROM {oracle_name(TRACE_SUMMARY_VIEW)}
                WHERE "FFC案件NO" = :project_no
                {date_clause}
                """,
                params,
            )
            return [
                {
                    "ship_date": date_to_str(row[0]),
                    "ffc_shipment_no": row[1],
                    "branch_no": row[2],
                    "store_no": row[3],
                    "store_name": row[4],
                    "product_code": row[5],
                    "status_code": row[6],
                }
                for row in cursor.fetchall()
            ]


def build_dashboard_payload(source_rows, ship_date):
    shipments = defaultdict(new_shipment)

    for row in source_rows:
        status_code = row["status_code"]
        if status_code == EXCLUDED_STATUS:
            continue

        shipment = shipments[row["ffc_shipment_no"]]
        shipment["ship_date"] = row["ship_date"]
        shipment["ffc_shipment_no"] = row["ffc_shipment_no"]
        shipment["store_no"] = row["store_no"]
        shipment["store_name"] = row["store_name"]

        product_code = str(row["product_code"])
        branch_no = str(row["branch_no"])
        is_done = status_code == COMPLETED_STATUS

        if product_code in PACK_PRODUCT_CODES:
            shipment["pack_total"].add(branch_no)
            if is_done:
                shipment["pack_done"].add(branch_no)
        if product_code in CASH_PRODUCT_CODES:
            shipment["cash_total"].add(branch_no)
            if is_done:
                shipment["cash_done"].add(branch_no)

    response_rows = []
    for shipment in shipments.values():
        pack_done = len(shipment["pack_done"])
        pack_total = len(shipment["pack_total"])
        cash_done = len(shipment["cash_done"])
        cash_total = len(shipment["cash_total"])
        pack_complete = is_complete(pack_done, pack_total)
        cash_complete = is_complete(cash_done, cash_total)
        overall_complete = pack_complete and cash_complete

        response_rows.append(
            {
                "ffc_shipment_no": shipment["ffc_shipment_no"],
                "store_no": shipment["store_no"],
                "store_name": shipment["store_name"],
                "pack": f"{pack_done}/{pack_total}",
                "cash": f"{cash_done}/{cash_total}",
                "status": "完了" if overall_complete else "未完",
                "pack_done": pack_done,
                "pack_total": pack_total,
                "cash_done": cash_done,
                "cash_total": cash_total,
                "pack_complete": pack_complete,
                "cash_complete": cash_complete,
                "overall_complete": overall_complete,
            }
        )

    response_rows.sort(key=lambda item: item["ffc_shipment_no"])
    total = len(response_rows)
    pack_done_stores = sum(1 for row in response_rows if row["pack_complete"])
    cash_done_stores = sum(1 for row in response_rows if row["cash_complete"])
    overall_done_stores = sum(1 for row in response_rows if row["overall_complete"])

    return {
        "ship_date": ship_date,
        "summary": {
            "pack": summary_item(pack_done_stores, total),
            "cash": summary_item(cash_done_stores, total),
            "overall": summary_item(overall_done_stores, total),
        },
        "rows": response_rows,
    }


def new_shipment():
    return {
        "ship_date": "",
        "ffc_shipment_no": "",
        "store_no": "",
        "store_name": "",
        "pack_total": set(),
        "pack_done": set(),
        "cash_total": set(),
        "cash_done": set(),
    }


def summary_item(done, total):
    return {"done": done, "total": total, "rate": round(done / total * 100) if total else 0}


def is_complete(done, total):
    return done == total


def parse_date(value):
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"出荷日はYYYY-MM-DD形式で指定してください: {value}") from exc


def date_to_str(value):
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def oracle_name(object_name):
    schema = settings.AOI_SOURCE_DB_SCHEMA
    object_name = object_name.strip().upper()
    if not ORACLE_IDENTIFIER_RE.fullmatch(object_name):
        raise ValueError(f"Oracle object name is invalid: {object_name}")
    if not schema:
        return object_name
    if not ORACLE_IDENTIFIER_RE.fullmatch(schema):
        raise ValueError(f"Oracle schema name is invalid: {schema}")
    return f"{schema}.{object_name}"


def build_mock_source_rows():
    shipments = [
        ("2026-06-18", "F000200001", "11", "大仁店", 4, 4, 4, 4),
        ("2026-06-18", "F000200002", "22", "三島店", 3, 3, 3, 3),
        ("2026-06-18", "F000200003", "35", "沼津店", 2, 5, 1, 5),
        ("2026-06-18", "F000200004", "48", "富士店", 6, 6, 2, 6),
        ("2026-06-18", "F000200005", "52", "静岡店", 5, 5, 5, 5),
        ("2026-06-18", "F000200006", "67", "清水店", 1, 4, 4, 4),
        ("2026-06-18", "F000200007", "74", "藤枝店", 0, 3, 0, 3),
        ("2026-06-18", "F000200008", "86", "焼津店", 7, 7, 7, 7),
        ("2026-06-18", "F000200009", "91", "島田店", 3, 4, 4, 4),
        ("2026-06-18", "F000200010", "105", "掛川店", 2, 2, 2, 2),
        ("2026-06-19", "F000200011", "118", "浜松店", 5, 5, 5, 5),
        ("2026-06-19", "F000200012", "121", "磐田店", 4, 4, 1, 4),
        ("2026-06-19", "F000200013", "134", "袋井店", 0, 3, 0, 3),
        ("2026-06-19", "F000200014", "146", "菊川店", 2, 2, 2, 2),
        ("2026-06-19", "F000200015", "152", "御前崎店", 2, 6, 6, 6),
        ("2026-06-20", "F000200021", "211", "長泉店", 6, 6, 6, 6),
        ("2026-06-20", "F000200022", "222", "裾野店", 5, 5, 5, 5),
        ("2026-06-20", "F000200023", "233", "御殿場店", 4, 7, 3, 7),
        ("2026-06-20", "F000200024", "244", "小山店", 0, 4, 0, 4),
        ("2026-06-20", "F000200025", "255", "函南店", 4, 4, 1, 4),
    ]

    rows = []
    for ship_date, shipment_no, store_no, store_name, pack_done, pack_total, cash_done, cash_total in shipments:
        rows.extend(
            build_category_rows(
                ship_date,
                shipment_no,
                store_no,
                store_name,
                PACK_PRODUCT_CODES,
                pack_done,
                pack_total,
            )
        )
        rows.extend(
            build_category_rows(
                ship_date,
                shipment_no,
                store_no,
                store_name,
                CASH_PRODUCT_CODES,
                cash_done,
                cash_total,
            )
        )
    return rows


def build_category_rows(ship_date, shipment_no, store_no, store_name, product_codes, done, total):
    rows = []
    codes = sorted(product_codes)
    for index in range(1, total + 1):
        status_code = COMPLETED_STATUS if index <= done else "作業中"
        branch_no = f"{index:03d}"
        for product_code in codes[:2]:
            rows.append(
                {
                    "ship_date": ship_date,
                    "ffc_shipment_no": shipment_no,
                    "branch_no": branch_no,
                    "store_no": store_no,
                    "store_name": store_name,
                    "product_code": product_code,
                    "status_code": status_code,
                }
            )
    return rows
