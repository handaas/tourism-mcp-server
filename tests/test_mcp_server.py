
import asyncio
import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from unittest import TestCase
from unittest.mock import Mock, patch

from mcp.server.fastmcp.exceptions import ToolError

SERVER_PATH = Path(__file__).parents[1] / "server" / "mcp_server.py"
SPEC = importlib.util.spec_from_file_location("tourism_mcp_server", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class ContractTests(TestCase):
    def test_registered_tools_and_annotations(self) -> None:
        tools = asyncio.run(server.mcp.list_tools())
        self.assertEqual(server.mcp.name, '文旅景区搜索')
        self.assertEqual(
            {tool.name for tool in tools},
            {
                'tourism_countryside_search',
                'tourism_accommodation_search',
                'tourism_travel_agency_search',
                'tourism_scenic_area_search',
                'tourism_scenic_area_detail',
                'tourism_planning_list',
            },
        )
        for tool in tools:
            self.assertEqual(tool.outputSchema.get("type"), "object")
            self.assertTrue(tool.annotations.readOnlyHint)
            self.assertFalse(tool.annotations.destructiveHint)
            self.assertTrue(tool.annotations.idempotentHint)
            self.assertGreaterEqual(len(tool.description or ""), 50)
            self.assertTrue(tool.annotations.openWorldHint)

    def test_new_tool_schemas_follow_documented_parameters(self) -> None:
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        for name in ('tourism_scenic_area_search', 'tourism_countryside_search'):
            self.assertIn('_id', tools[name].description)
            self.assertIn('taId', tools[name].description)
        detail = tools['tourism_scenic_area_detail'].inputSchema
        self.assertEqual(set(detail['properties']), {'taId'})
        self.assertNotIn('taId', detail.get('required', []))
        self.assertIsNone(detail['properties']['taId']['default'])

        planning = tools['tourism_planning_list'].inputSchema
        self.assertEqual(set(planning['properties']), {'taId', 'pageIndex', 'pageSize'})
        self.assertEqual(planning['required'], ['taId'])
        self.assertEqual(planning['properties']['taId']['type'], 'string')
        self.assertEqual(planning['properties']['pageIndex']['default'], 1)
        self.assertEqual(planning['properties']['pageSize']['default'], 10)

    def test_new_tools_dispatch_through_mcp(self) -> None:
        async def check() -> None:
            with patch.object(server, 'call_api', return_value={'taName': '测试景区'}) as call:
                _, structured = await server.mcp.call_tool('tourism_scenic_area_detail', {'taId': 'scenic-1'})
                self.assertEqual(structured, {'total': 1, 'resultList': [{'taName': '测试景区'}]})
                call.assert_called_once_with('6a98ec3fcc51ed421bf06fa2', {'taId': 'scenic-1'})
            with patch.object(server, 'call_api', return_value={'total': 0, 'resultList': []}) as call:
                _, structured = await server.mcp.call_tool('tourism_planning_list', {'taId': 'scenic-1'})
                self.assertEqual(structured, {'total': 0, 'resultList': []})
                call.assert_called_once_with(
                    '6a995506a96d8a6e55377905',
                    {'taId': 'scenic-1', 'pageIndex': 1, 'pageSize': 10},
                )
            for arguments in ({}, {'taId': None}):
                with self.subTest(arguments=arguments), patch.object(server, 'call_api') as call:
                    with self.assertRaises(ToolError):
                        await server.mcp.call_tool('tourism_planning_list', arguments)
                    call.assert_not_called()
            with patch.object(server, 'call_api') as call:
                _, structured = await server.mcp.call_tool(
                    'tourism_planning_list', {'taId': 'scenic-1', 'pageSize': 11}
                )
                self.assertEqual(structured['parameter'], 'pageSize')
                call.assert_not_called()

        asyncio.run(check())

    def test_new_tools_use_signed_gateway_payloads(self) -> None:
        credentials = {'INTEGRATOR_ID': 'test-integrator', 'SECRET_ID': 'test-secret-id', 'SECRET_KEY': 'test-secret-key'}
        cases: tuple[tuple[str, dict[str, Any], str, dict[str, Any], dict[str, Any]], ...] = (
            ('tourism_scenic_area_detail', {}, '6a98ec3fcc51ed421bf06fa2', {}, {}),
            ('tourism_scenic_area_detail', {'taId': 'scenic-1'}, '6a98ec3fcc51ed421bf06fa2',
             {'taId': 'scenic-1'}, {'taName': '测试景区'}),
            ('tourism_planning_list', {'taId': 'scenic-1'}, '6a995506a96d8a6e55377905',
             {'taId': 'scenic-1', 'pageIndex': 1, 'pageSize': 10}, {'total': 0, 'resultList': []}),
        )
        for name, arguments, product_id, params, data in cases:
            response = Mock(status_code=200)
            response.json.return_value = {'code': '1', 'data': data}
            with self.subTest(tool=name, arguments=arguments), patch.dict(os.environ, credentials, clear=True), patch.object(
                server.requests, 'post', return_value=response
            ) as post:
                result = getattr(server, name)(**arguments)
                self.assertNotIn('error', result)
                post.assert_called_once()
                self.assertEqual(post.call_args.args[0], server.GATEWAY_BASE_URL + '/test-integrator')
                payload = post.call_args.kwargs['data']
                self.assertEqual(payload['product_id'], product_id)
                self.assertEqual(json.loads(payload['params']), params)
                unsigned = {key: value for key, value in payload.items() if key != 'signature'}
                self.assertEqual(payload['signature'], server._build_signature(unsigned, 'test-secret-key'))

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
    def test_search_record_id_is_preserved_for_planning_queries(self) -> None:
        for name in ('tourism_scenic_area_search', 'tourism_countryside_search'):
            with self.subTest(tool=name), patch.object(server, 'call_api') as call:
                call.return_value = {'dataList': [{'_id': 'tourism-1', 'taName': '测试景区'}], 'dataTotal': 1}
                search = getattr(server, name)()
                record = search['resultList'][0]
                self.assertEqual(record['_id'], 'tourism-1')
                self.assertNotIn('taId', record)
                call.reset_mock()
                call.return_value = {'total': 0, 'resultList': []}
                server.tourism_planning_list(record['_id'])
                call.assert_called_once_with(
                    '6a995506a96d8a6e55377905',
                    {'taId': 'tourism-1', 'pageIndex': 1, 'pageSize': 10},
                )

    def test_scenic_detail_preserves_nested_document_fields(self) -> None:
        record = {
            'taName': '测试景区',
            'taLandArea': '100',
            'taBuildingArea': '20',
            'taFeatures': '测试特色',
            'taAttractions': ['测试景点'],
            'taCultureValues': '测试文化价值',
            'taIntroduction': '测试简介',
            'taAddress': {'province': '浙江', 'city': '杭州', 'district': '测试区', 'value': '测试地址'},
            'taCategory': '测试类别',
            'taBatchNumber': '测试批次',
            'taOperatingEntity': [{'nameId': 'company-1', 'name': '测试运营主体'}],
        }
        for response in (record, {'stat': 1, 'data': record}):
            with self.subTest(wrapped='stat' in response), patch.object(
                server, 'call_api', return_value=response
            ) as call:
                result = server.tourism_scenic_area_detail('scenic-1')
            call.assert_called_once_with('6a98ec3fcc51ed421bf06fa2', {'taId': 'scenic-1'})
            self.assertEqual(result, {'total': 1, 'resultList': [record]})

    def test_scenic_detail_omits_optional_id(self) -> None:
        with patch.object(server, 'call_api', return_value={}) as call:
            result = server.tourism_scenic_area_detail()
        call.assert_called_once_with('6a98ec3fcc51ed421bf06fa2', {})
        self.assertEqual(result, {'total': 0, 'resultList': []})

    def test_planning_route_defaults_and_preserves_fields(self) -> None:
        records = [{
            'taPlanningType': '测试类别',
            'taPlanningName': '测试规划项目',
            'taPlanningDesc': '测试建设内容与规模',
            'taPlanningNews': '测试进展',
            'taPlanningCompany': '测试相关单位',
        }]
        responses = (
            {'total': 21, 'resultList': records},
            {'stat': 1, 'data': {'total': 21, 'resultList': records}},
            {'dataTotal': 21, 'dataList': records},
        )
        for response in responses:
            with self.subTest(response=response), patch.object(
                server, 'call_api', return_value=response
            ) as call:
                result = server.tourism_planning_list('scenic-1')
            call.assert_called_once_with(
                '6a995506a96d8a6e55377905',
                {'taId': 'scenic-1', 'pageIndex': 1, 'pageSize': 10},
            )
            self.assertEqual(result, {'total': 21, 'resultList': records})

    def test_planning_passes_requested_page_to_api(self) -> None:
        for size in (1, 10):
            with self.subTest(size=size), patch.object(
                server, 'call_api', return_value={'total': 21, 'resultList': []}
            ) as call:
                result = server.tourism_planning_list('countryside-1', pageIndex=2, pageSize=size)
            call.assert_called_once_with(
                '6a995506a96d8a6e55377905',
                {'taId': 'countryside-1', 'pageIndex': 2, 'pageSize': size},
            )
            self.assertEqual(result, {'total': 21, 'resultList': []})

    def test_planning_rejects_invalid_pagination_before_api_call(self) -> None:
        cases = [(0, 10, 'pageIndex'), (-1, 10, 'pageIndex'), (1, 0, 'pageSize'), (1, 11, 'pageSize')]
        for page, size, parameter in cases:
            with self.subTest(page=page, size=size), patch.object(server, 'call_api') as call:
                result = server.tourism_planning_list('scenic-1', pageIndex=page, pageSize=size)
            self.assertEqual(result['parameter'], parameter)
            call.assert_not_called()

    def test_planning_rejects_blank_id_before_api_call(self) -> None:
        for ta_id in ('', '  '):
            with self.subTest(ta_id=ta_id), patch.object(server, 'call_api') as call:
                result = server.tourism_planning_list(ta_id)
            self.assertEqual(result['parameter'], 'taId')
            call.assert_not_called()

    def test_new_tools_preserve_empty_results_and_upstream_errors(self) -> None:
        cases = (
            ({'total': 0, 'resultList': []}, {'total': 0, 'resultList': []}),
            ({'error': '未开通数据产品', 'code': '403'}, {'error': '未开通数据产品', 'code': '403'}),
            ({'stat': 0, 'err': 'upstream', 'msg': '上游失败'}, {'error': '上游失败', 'code': 'upstream'}),
        )
        for name in ('tourism_scenic_area_detail', 'tourism_planning_list'):
            for response, expected in cases:
                with self.subTest(tool=name, response=response), patch.object(
                    server, 'call_api', return_value=response
                ):
                    self.assertEqual(getattr(server, name)('scenic-1'), expected)

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
