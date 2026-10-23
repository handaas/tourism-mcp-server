
"""HandaaS 文旅景区搜索 MCP 服务。"""

import json
import os
import sys
from hashlib import md5
from typing import Any, Literal
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


load_dotenv()

mcp = FastMCP(
    "文旅景区搜索",
    instructions=(
        '面向国标景区、乡村旅游重点村镇、餐饮民宿、星级饭店和出境游旅行社的分类型搜索与资源核验。'
        '先通过搜索获取景区ID，再查询国标景区详情或文旅规划明细；乡村旅游搜索结果也可用于规划查询。'
    ),
    dependencies=["python-dotenv", "requests"],
)

GATEWAY_BASE_URL = "https://console.handaas.com/api/v1/integrator/call_api"
DEFAULT_TIMEOUT_SECONDS = 30.0

PRODUCT_IDS = {
    'scenic_search': '6a7c2b14dfa4a2f37b191ab2',
    'scenic_detail': '6a98ec3fcc51ed421bf06fa2',
    'planning_list': '6a995506a96d8a6e55377905',
    'countryside_search': '6a7c2f6edfa4a2f37b191b5a',
    'accommodation_search': '6a7c31428c8d379dd486c56a',
    'travel_agency_search': '6a7c52df71276c00fb93e8dd',
}

READ_ONLY_TOOL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)


def _request_timeout() -> float:
    raw = os.environ.get("HANDAAS_REQUEST_TIMEOUT", "")
    try:
        value = float(raw) if raw else DEFAULT_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_TIMEOUT_SECONDS


def _credential(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("your_"):
        return None
    return value


def _compact_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def _build_signature(call_params: dict[str, str], secret_key: str) -> str:
    plain = "".join(str(call_params[key]) for key in sorted(call_params))
    return md5(f"{plain}{secret_key}".encode("utf-8")).hexdigest()


def call_api(product_id: str, params: dict[str, Any]) -> Any:
    """调用 HandaaS Integrator Gateway并返回业务 data。"""
    integrator_id = _credential("INTEGRATOR_ID")
    secret_id = _credential("SECRET_ID")
    secret_key = _credential("SECRET_KEY")
    if not integrator_id:
        return {"error": "INTEGRATOR_ID 未配置"}
    if not secret_id:
        return {"error": "SECRET_ID 未配置"}
    if not secret_key:
        return {"error": "SECRET_KEY 未配置"}
    if not product_id:
        return {"error": "Product ID 不能为空"}

    call_params = {
        "product_id": product_id,
        "secret_id": secret_id,
        "params": json.dumps(
            _compact_params(params), ensure_ascii=False, separators=(",", ":")
        ),
    }
    call_params["signature"] = _build_signature(call_params, secret_key)
    url = f"{GATEWAY_BASE_URL}/{quote(integrator_id, safe='')}"
    try:
        response = requests.post(url, data=call_params, timeout=_request_timeout())
    except requests.RequestException:
        return {"error": "HandaaS 网关请求失败，请稍后重试"}
    if response.status_code != 200:
        return {
            "error": "HandaaS 网关返回非成功状态",
            "statusCode": response.status_code,
        }
    try:
        payload = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        return {"error": "HandaaS 网关返回了无法解析的响应"}
    if not isinstance(payload, dict):
        return {"error": "HandaaS 网关返回格式异常"}
    if "data" in payload:
        return payload["data"]
    error = payload.get("msgCN") or payload.get("message") or "HandaaS 网关未返回 data"
    if str(payload.get("code")) == "10001" or error == "查询数据为空":
        return {"total": 0, "resultList": []}
    result = {"error": error}
    if payload.get("code") is not None:
        result["code"] = payload["code"]
    return result


def _unwrap_backend_data(result: Any) -> Any:
    """兼容 Product API直接返回业务 data或保留内部 stat/data 外层。"""
    if not isinstance(result, dict) or "error" in result:
        return result
    if "stat" not in result:
        return result
    if result.get("stat") != 1:
        return {
            "error": result.get("msg") or "上游数据接口返回失败",
            "code": result.get("err"),
        }
    return result.get("data")


def _pagination_error(page_index: int, page_size: int, maximum: int = 10) -> dict[str, Any] | None:
    if page_index < 1:
        return {"error": "pageIndex 必须大于等于 1", "parameter": "pageIndex"}
    if page_size < 1 or page_size > maximum:
        return {"error": f"pageSize 必须在 1 到 {maximum} 之间", "parameter": "pageSize"}
    return None


def _normalize_paged(result: Any) -> Any:
    result = _unwrap_backend_data(result)
    if not isinstance(result, dict) or "error" in result:
        return result
    if isinstance(result.get("resultList"), list):
        records = result["resultList"]
        total = result.get("total", len(records))
        return {"total": total, "resultList": records}
    if isinstance(result.get("dataList"), list):
        records = result["dataList"]
        total = result.get("dataTotal", result.get("dataCount", len(records)))
        return {"total": total, "resultList": records}
    return result


def _normalize_single(result: Any) -> Any:
    result = _unwrap_backend_data(result)
    if not isinstance(result, dict) or "error" in result:
        return result
    if set(result) == {"total", "resultList"} and isinstance(result.get("resultList"), list):
        return result
    if not result:
        return {"total": 0, "resultList": []}
    return {"total": 1, "resultList": [result]}


def _number_range_error(
    minimum: int | float | None,
    maximum: int | float | None,
    minimum_name: str,
    maximum_name: str,
) -> dict[str, Any] | None:
    if minimum is not None and maximum is not None and minimum > maximum:
        return {
            "error": f"{minimum_name} 不能大于 {maximum_name}",
            "parameter": minimum_name,
        }
    return None


def _date_range_error(
    start: str | None,
    end: str | None,
    start_name: str,
    end_name: str,
) -> dict[str, Any] | None:
    if start and end and start > end:
        return {
            "error": f"{start_name} 不能晚于 {end_name}",
            "parameter": start_name,
        }
    return None

@mcp.tool(
    title="国标文旅景区检索",
    description=(
        "按景区名称、景区类别、省份、城市和评定批次搜索国标景区。taName 支持模糊搜索，"
        "其他条件按筛选值匹配；景区省份使用北京、广东等短名。返回景区类别、地址、评定信息和运营主体，pageSize 最大 10。"
        "结果中的景区记录ID（搜索文档字段 _id，若实际返回 taId 则直接使用）可作为 taId "
        "传给 tourism_scenic_area_detail 或 tourism_planning_list。"
    ),
    annotations=READ_ONLY_TOOL,
)
def tourism_scenic_area_search(
    taName: str | None = None,
    taCategory: str | None = None,
    taProvince: str | None = None,
    taCity: str | None = None,
    taBatchNumber: str | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """按名称、类别、省市和批次分页检索国标景区。"""
    if error := _pagination_error(pageIndex, pageSize): return error
    return _normalize_paged(call_api(PRODUCT_IDS["scenic_search"], locals()))


@mcp.tool(
    title="国标景区详情",
    description=(
        "根据国标景区搜索结果中的景区ID查询名称、占地面积、建筑面积、核心特色、主要设施/景点、"
        "文化价值、简介、地址、景区类型、等级批次及运营主体。taId 按接口文档为可选，建议先调用"
        "tourism_scenic_area_search 获取ID后传入；不传时不保证返回指定景区。返回 total 与 resultList，"
        "保留地址字典和运营主体列表，面积字段按上游原值返回，不推断单位。"
    ),
    annotations=READ_ONLY_TOOL,
)
def tourism_scenic_area_detail(taId: str | None = None) -> dict[str, Any]:
    """按景区ID查询国标景区详情，保留地址、景点和运营主体的嵌套结构。"""
    return _normalize_single(
        call_api(PRODUCT_IDS["scenic_detail"], _compact_params({"taId": taId}))
    )


@mcp.tool(
    title="文旅规划明细",
    description=(
        "根据景区ID分页查询文旅规划类别、项目名称、建设内容与规模、最新进展和相关单位。"
        "taId 必填，来自 tourism_scenic_area_search 或 tourism_countryside_search 的搜索结果，"
        "不能以名称代替ID；pageIndex 从 1 开始，pageSize 默认 10、最大 10。"
        "返回 total 与 resultList，保留规划记录原始字段；空结果仅表示接口本次未返回规划数据。"
    ),
    annotations=READ_ONLY_TOOL,
)
def tourism_planning_list(taId: str, pageIndex: int = 1, pageSize: int = 10) -> dict[str, Any]:
    """按国标景区或乡村旅游景区ID分页查询文旅规划明细。"""
    if not taId.strip():
        return {"error": "taId 不能为空，请先通过国标景区或乡村旅游搜索获取景区ID", "parameter": "taId"}
    if error := _pagination_error(pageIndex, pageSize):
        return error
    return _normalize_paged(
        call_api(PRODUCT_IDS["planning_list"], {"taId": taId, "pageIndex": pageIndex, "pageSize": pageSize})
    )


@mcp.tool(
    title="乡村旅游重点村镇检索",
    description=(
        "按村镇名称、入选批次、省份和城市搜索全国乡村旅游重点村镇。"
        "返回名称、证号、地区、评定年份、发布日期和图片信息，支持分页并返回 total 与 resultList。"
        "结果中的景区记录ID（搜索文档字段 _id，若实际返回 taId 则直接使用）可作为 taId "
        "传给 tourism_planning_list 查询文旅规划。"
    ),
    annotations=READ_ONLY_TOOL,
)
def tourism_countryside_search(
    taName: str | None = None,
    taBatchNumber: str | None = None,
    taProvince: str | None = None,
    taCity: str | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """按名称、入选批次和省市分页检索乡村旅游重点村镇。"""
    if error := _pagination_error(pageIndex, pageSize): return error
    return _normalize_paged(call_api(PRODUCT_IDS["countryside_search"], locals()))


@mcp.tool(
    title="餐饮民宿与星级饭店检索",
    description=(
        "搜索餐饮民宿、星级饭店及其运营企业。可按名称、旅宿类型、省市区、成立日期、"
        "注册资本（万元）和经营状态筛选；address 多级值用逗号分隔，pageSize 最大 10。"
    ),
    annotations=READ_ONLY_TOOL,
)
def tourism_accommodation_search(
    taName: str | None = None,
    taType: str | None = None,
    address: str | None = None,
    foundTimeBegin: str | None = None,
    foundTimeEnd: str | None = None,
    regCapitalMin: int | None = None,
    regCapitalMax: int | None = None,
    operStatus: str | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """分页检索餐饮民宿、星级饭店及其运营企业。"""
    if error := _pagination_error(pageIndex, pageSize): return error
    if error := _date_range_error(foundTimeBegin, foundTimeEnd, "foundTimeBegin", "foundTimeEnd"): return error
    if error := _number_range_error(regCapitalMin, regCapitalMax, "regCapitalMin", "regCapitalMax"): return error
    return _normalize_paged(call_api(PRODUCT_IDS["accommodation_search"], locals()))


@mcp.tool(
    title="出境游旅行社检索",
    description=(
        "搜索具备出境游相关资质的旅行社及其运营企业。可按名称、省市区、成立日期、"
        "注册资本（万元）和经营状态筛选；直辖市地区可使用上海、北京等短名。返回许可证、企业主体、规模和业务标签等信息。"
    ),
    annotations=READ_ONLY_TOOL,
)
def tourism_travel_agency_search(
    taName: str | None = None,
    address: str | None = None,
    foundTimeBegin: str | None = None,
    foundTimeEnd: str | None = None,
    regCapitalMin: int | None = None,
    regCapitalMax: int | None = None,
    operStatus: str | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """分页检索出境游旅行社许可证、企业状态和规模。"""
    if error := _pagination_error(pageIndex, pageSize): return error
    if error := _date_range_error(foundTimeBegin, foundTimeEnd, "foundTimeBegin", "foundTimeEnd"): return error
    if error := _number_range_error(regCapitalMin, regCapitalMax, "regCapitalMin", "regCapitalMax"): return error
    return _normalize_paged(call_api(PRODUCT_IDS["travel_agency_search"], locals()))


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    transport = arguments[0] if arguments else "stdio"
    if transport not in {"stdio", "sse", "streamable-http"}:
        print("启动方式必须是 stdio、sse 或 streamable-http", file=sys.stderr)
        return 2
    mcp.run(transport=transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
