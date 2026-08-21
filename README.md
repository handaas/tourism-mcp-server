# 文旅：文旅景区搜索

[该 MCP 服务以文旅景区搜索为核心，提供国标景区、乡村旅游重点村镇、餐饮民宿、星级饭店和出境游旅行社检索能力。](https://www.handaas.com/)

> 所属板块：综合信息

## 主要功能

- 国标文旅景区检索
- 乡村旅游重点村镇检索
- 餐饮民宿和星级饭店检索
- 出境游旅行社检索

## 服务设计说明

- 服务以景区发现为入口，并补充乡村旅游、住宿餐饮和旅行社资源，满足目的地资源组合查询场景。
- 服务提供 4 个只读 Tool，单次 Tool 调用只访问一个 Product ID。
- 翻页结果统一收口为 `total` 与 `resultList`。
- 成功响应自动兼容 Gateway业务 data和内部 `stat/data` 两种形态。
- 请求超时可通过 `HANDAAS_REQUEST_TIMEOUT` 配置，默认30秒。

## 环境要求

- Python 3.10+
- 依赖：`mcp`、`python-dotenv`、`requests`

## 本地快速启动

```bash
cd tourism-mcp-server
python3 -m venv mcp_env
source mcp_env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python server/mcp_server.py streamable-http
```

服务默认地址：`http://127.0.0.1:8000/mcp`。支持 `stdio`、`sse` 和 `streamable-http`。

## 环境变量

```env
INTEGRATOR_ID=your_integrator_id
SECRET_ID=your_secret_id
SECRET_KEY=your_secret_key
HANDAAS_REQUEST_TIMEOUT=30
```

真实凭据只能保存在本地 `.env` 或部署密钥中。

## Cursor / Cherry Studio配置

```json
{
  "mcpServers": {
    "tourism-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 可用 Tool 与 Product ID

| MCP Tool | 使用场景 | Product ID | 关键输入 |
| --- | --- | --- | --- |
| `tourism_scenic_area_search` | 搜索国标景区和运营主体 | `6a7c2b14dfa4a2f37b191ab2` | 名称、类别、省市、批次、分页 |
| `tourism_countryside_search` | 搜索全国乡村旅游重点村镇 | `6a7c2f6edfa4a2f37b191b5a` | 名称、批次、省市、分页 |
| `tourism_accommodation_search` | 搜索餐饮民宿、星级饭店及运营企业 | `6a7c31428c8d379dd486c56a` | 名称、类型、地区、成立日期、注册资本、状态、分页 |
| `tourism_travel_agency_search` | 搜索出境游旅行社和许可证信息 | `6a7c52df71276c00fb93e8dd` | 名称、地区、成立日期、注册资本、状态、分页 |

## Tool 选择指南

- 用户询问 A 级景区、景区评定或景区运营主体：使用 `tourism_scenic_area_search`。
- 用户询问乡村旅游重点村、重点镇或入选批次：使用 `tourism_countryside_search`。
- 用户询问民宿、餐饮住宿或星级饭店：使用 `tourism_accommodation_search`。
- 用户询问出境游旅行社、旅行社许可证或企业规模：使用 `tourism_travel_agency_search`。

## Tool 详细说明

### 1. tourism_scenic_area_search

**何时使用**：按名称、类别或地区发现国标景区，核对评定信息与运营主体。

**关键参数**：`taName` 支持模糊搜索；`taCategory`、省市和 `taBatchNumber` 用于进一步筛选；景区省份使用“北京”“广东”等短名；`pageSize` 最大 50。

**返回说明**：返回景区名称、类别、地区、评定年份、发布日期、地址和运营主体。

### 2. tourism_countryside_search

**何时使用**：查询全国乡村旅游重点村镇及其入选批次。

**关键参数**：可按村镇名称、批次、省份和城市筛选；支持分页。

**返回说明**：返回村镇名称、证号、地区、评定年份、发布日期和图片信息。

### 3. tourism_accommodation_search

**何时使用**：查询餐饮民宿、星级饭店及其背后的运营企业。

**关键参数**：`taType` 为旅宿类型；`address` 多级值使用“省份,城市,区县”；日期格式为 `YYYY-MM-DD`；注册资本单位为万元。

**返回说明**：返回旅宿名称、类型、证号、企业名称、主体 ID、法人、注册资本、地址和经营状态。

### 4. tourism_travel_agency_search

**何时使用**：查询出境游旅行社许可证、运营企业和业务规模。

**关键参数**：可按旅行社名称、地区、成立日期、注册资本和经营状态筛选；直辖市地区使用“上海”“北京”等短名；支持分页。

**返回说明**：返回旅行社中英文名称、许可证、企业主体、法人、注册资本、年营业额和业务标签。

## 使用示例

### 示例一：搜索景区

> 搜索北京名称包含“故宫”的国标景区，返回景区地址和运营主体。

```json
{
  "tool": "tourism_scenic_area_search",
  "arguments": {
    "taName": "故宫",
    "taProvince": "北京",
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

### 示例二：搜索乡村旅游重点村镇

> 查询浙江省入选的乡村旅游重点村镇。

```json
{
  "tool": "tourism_countryside_search",
  "arguments": {
    "taProvince": "浙江省",
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

### 示例三：搜索民宿和饭店

> 查找杭州正在经营的民宿，返回运营企业和注册信息。

```json
{
  "tool": "tourism_accommodation_search",
  "arguments": {
    "taType": "民宿",
    "address": "浙江省,杭州市",
    "operStatus": "存续",
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

### 示例四：搜索出境游旅行社

> 查询上海的出境游旅行社及许可证信息。

```json
{
  "tool": "tourism_travel_agency_search",
  "arguments": {
    "address": "上海",
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

## 使用注意事项

1. 成立日期和注册资本区间下限不得大于上限。
2. `address` 多级地区使用英文逗号分隔。
3. 所有搜索结果统一返回 `total/resultList`。
4. 筛选值无匹配时返回合法空结果，可减少条件后重试。

## 测试验证

```bash
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

单元测试使用 Mock 响应；真实验证通过本地 `.env` 调用 HandaaS Integrator Gateway。
