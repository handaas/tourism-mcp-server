
import asyncio
import importlib.util
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

SERVER_PATH = Path(__file__).parents[1] / "server" / "mcp_server.py"
SPEC = importlib.util.spec_from_file_location("tourism_mcp_server", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class ContractTests(TestCase):
    def test_registered_tools_and_annotations(self) -> None:
        tools = asyncio.run(server.mcp.list_tools())
        self.assertEqual(server.mcp.name, '文旅：文旅景区搜索')
        self.assertEqual({tool.name for tool in tools}, {'tourism_countryside_search', 'tourism_accommodation_search', 'tourism_travel_agency_search', 'tourism_scenic_area_search'})
        for tool in tools:
            self.assertEqual(tool.outputSchema.get("type"), "object")
            self.assertTrue(tool.annotations.readOnlyHint)
            self.assertFalse(tool.annotations.destructiveHint)
            self.assertTrue(tool.annotations.idempotentHint)
            self.assertGreaterEqual(len(tool.description or ""), 50)
            self.assertTrue(tool.annotations.openWorldHint)

    def test_missing_credentials_blocks_http(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch.object(server.requests, "post") as post:
            result = server.call_api("product", {})
        self.assertEqual(result, {"error": "INTEGRATOR_ID 未配置"})
        post.assert_not_called()

    def test_backend_envelope_and_pagination_are_normalized(self) -> None:
        wrapped = {"stat": 1, "data": {"dataList": [{"id": 1}], "dataTotal": 3}}
        self.assertEqual(server._normalize_paged(wrapped), {"total": 3, "resultList": [{"id": 1}]})
        self.assertEqual(server._normalize_single({"stat": 1, "data": {"id": 1}}), {"total": 1, "resultList": [{"id": 1}]})
        self.assertEqual(server._normalize_single({"stat": 1, "data": {}}), {"total": 0, "resultList": []})

    def test_invalid_pagination_is_actionable(self) -> None:
        error = server._pagination_error(0, 10)
        self.assertEqual(error["parameter"], "pageIndex")
        error = server._pagination_error(1, 11)
        self.assertEqual(error["parameter"], "pageSize")

    def test_empty_business_response_is_normalized(self) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {"code": "10001", "msgCN": "查询数据为空"}
        credentials = {"INTEGRATOR_ID": "integrator", "SECRET_ID": "secret-id", "SECRET_KEY": "secret-key"}
        with patch.dict(os.environ, credentials, clear=True), patch.object(server.requests, "post", return_value=response):
            result = server.call_api("product", {})
        self.assertEqual(result, {"total": 0, "resultList": []})


class RoutingTests(TestCase):
    def test_all_product_routes(self) -> None:
        cases = [
            (lambda: server.tourism_scenic_area_search(taName="景区"), "scenic_search"),
            (lambda: server.tourism_countryside_search(taName="村"), "countryside_search"),
            (lambda: server.tourism_accommodation_search(taName="饭店"), "accommodation_search"),
            (lambda: server.tourism_travel_agency_search(taName="旅行社"), "travel_agency_search"),
        ]
        for invoke, route in cases:
            with self.subTest(route=route), patch.object(server, "call_api", return_value={"dataList": [], "dataTotal": 0}) as call:
                result = invoke()
            self.assertEqual(result, {"total": 0, "resultList": []})
            self.assertEqual(call.call_args.args[0], server.PRODUCT_IDS[route])

    def test_invalid_company_ranges_are_rejected(self) -> None:
        with patch.object(server, "call_api") as call:
            result = server.tourism_accommodation_search(regCapitalMin=20, regCapitalMax=10)
        self.assertEqual(result["parameter"], "regCapitalMin")
        call.assert_not_called()
