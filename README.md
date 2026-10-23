# 文旅景区搜索

[该MCP服务提供国标景区搜索与详情、文旅规划明细、乡村旅游重点村镇、餐饮民宿、星级饭店和出境游旅行社查询功能。](https://www.handaas.com/)


## 主要功能

- 🏞️ 国标景区搜索
- 📋 国标景区详情（面积、特色、景点、文化价值和运营主体）
- 🗺️ 文旅规划明细（项目、建设规模、最新进展和相关单位）
- 🏡 乡村旅游重点村镇搜索
- 🏨 餐饮民宿与星级饭店搜索
- ✈️ 出境游旅行社搜索

## 环境要求

- Python 3.10+
- 依赖包：python-dotenv, requests, mcp

## 本地快速启动

### 1. 克隆项目
```bash
git clone https://github.com/handaas/tourism-mcp-server
cd tourism-mcp-server
```

### 2. 创建虚拟环境&安装依赖

```bash
python -m venv mcp_env && source mcp_env/bin/activate
pip install -r requirements.txt
```

### 3. 环境配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下环境变量：

```env
INTEGRATOR_ID=your_integrator_id
SECRET_ID=your_secret_id
SECRET_KEY=your_secret_key
HANDAAS_REQUEST_TIMEOUT=30
```

### 4. streamable-http启动服务

```bash
python server/mcp_server.py streamable-http
```

服务将在 `http://localhost:8000` 启动，MCP 地址为 `http://127.0.0.1:8000/mcp`。

#### 支持启动方式 stdio 或 sse 或 streamable-http

### 5. Cursor / Cherry Studio MCP配置

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

## STDIO版安装部署

### 设置Cursor / Cherry Studio MCP配置

```json
{
  "mcpServers": {
    "tourism-mcp-server": {
      "command": "uv",
      "args": ["run", "mcp", "run", "{workdir}/server/mcp_server.py"],
      "env": {
        "PATH": "{workdir}/mcp_env/bin:$PATH",
        "PYTHONPATH": "{workdir}/mcp_env",
        "INTEGRATOR_ID": "your_integrator_id",
        "SECRET_ID": "your_secret_id",
        "SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

## 使用官方Remote服务

当前服务暂未开放官方 Remote 地址。请使用本地 `stdio`、`sse` 或 `streamable-http` 方式运行；官方 Remote 地址开放后将在本节补充配置。

### 注意：integrator_id、secret_id、secret_key及Remote token需要登录 https://www.handaas.com/ 进行注册开通平台获取


## 可用工具

### 推荐查询流程

1. 用 `tourism_scenic_area_search` 搜索国标景区，或用 `tourism_countryside_search` 搜索乡村旅游重点村镇，获取结果中的 `taId` 并原样传给后续工具。2026-09-07 实测两类搜索均已返回 `taId`；旧版搜索接口文档中的 `_id` 为记录ID，以实际返回字段为准。
2. 将国标景区ID作为 `taId` 传给 `tourism_scenic_area_detail`，查询景区详细信息。
3. 将国标景区或乡村旅游景区ID作为 `taId` 传给 `tourism_planning_list`，分页查询规划明细。

景区ID应取自搜索接口实际返回的数据，不使用景区名称或运营主体的 `nameId` 代替。若搜索结果没有可用景区ID，应提示缺少关联标识，不猜测ID。
已实测通过“国标景区搜索 → 景区详情”及“乡村旅游搜索 → 文旅规划”的 `taId` 关联链。

### 1. tourism_scenic_area_search
**功能**: 国标文旅景区搜索

**参数**:
- `taName` (可选): 景区名称，支持模糊搜索
- `taCategory` (可选): 景区类别
- `taProvince` (可选): 省份短名，例如北京、广东
- `taCity` (可选): 城市
- `taBatchNumber` (可选): 评定批次
- `pageIndex` (可选): 页码
- `pageSize` (可选): 每页条数，默认10，最大10

**返回值**:
- `total`: 景区总数
- `resultList`: 景区列表
  - `taId`: 景区ID（2026-09-07 实测返回），用于后续详情和规划查询
  - `_id`: 景区记录ID（本地搜索文档字段），用于后续详情/规划查询的 `taId`
  - `taName`: 景区名称
  - `taCategory`: 景区类别
  - `taProvince`: 省份
  - `taCity`: 城市
  - `taRegion`: 区县
  - `taEvaluationYear`: 评定年份
  - `taPublishDate`: 发布日期
  - `taOperatingEntity`: 运营主体
  - `taAddressValue`: 地址
  - `taBatchNumber`: 批次号

### 2. tourism_countryside_search
**功能**: 乡村旅游重点村镇搜索

**参数**:
- `taName` (可选): 村镇名称
- `taBatchNumber` (可选): 入选批次
- `taProvince` (可选): 省份
- `taCity` (可选): 城市
- `pageIndex` (可选): 页码
- `pageSize` (可选): 每页条数，默认10，最大10

**返回值**:
- `total`: 村镇总数
- `resultList`: 重点村镇列表
  - `taId`: 景区ID（2026-09-07 实测返回），用于后续规划查询
  - `_id`: 村镇记录ID（本地搜索文档字段），用于后续规划查询的 `taId`
  - `taName`: 村镇名称
  - `taBatchNumber`: 批次号
  - `taLicenseNumber`: 证号
  - `taProvince`: 省份
  - `taCity`: 城市
  - `taRegion`: 区县
  - `taEvaluationYear`: 评定年份
  - `taPublishDate`: 发布日期

### 3. tourism_accommodation_search
**功能**: 餐饮民宿与星级饭店搜索

**参数**:
- `taName` (可选): 名称，支持模糊搜索
- `taType` (可选): 旅宿类型
- `address` (可选): 地区，多级值用“省份,城市,区县”表示
- `foundTimeBegin` / `foundTimeEnd` (可选): 成立日期区间
- `regCapitalMin` / `regCapitalMax` (可选): 注册资本区间，单位万元
- `operStatus` (可选): 经营状态
- `pageIndex` (可选): 页码
- `pageSize` (可选): 每页条数，默认10，最大10

**返回值**:
- `total`: 旅宿总数
- `resultList`: 旅宿及运营企业列表
  - `taName`: 旅宿名称
  - `taType`: 旅宿类型
  - `taLicenseNumber`: 证号
  - `name`: 运营企业名称
  - `nameId`: 企业主体ID
  - `legalRepresentative`: 法定代表人
  - `foundTime`: 成立时间
  - `regCapital`: 注册资本
  - `address`: 注册地址
  - `operStatus`: 经营状态

### 4. tourism_travel_agency_search
**功能**: 出境游旅行社搜索

**参数**:
- `taName` (可选): 旅行社名称
- `address` (可选): 地区，直辖市使用上海、北京等短名
- `foundTimeBegin` / `foundTimeEnd` (可选): 成立日期区间
- `regCapitalMin` / `regCapitalMax` (可选): 注册资本区间，单位万元
- `operStatus` (可选): 经营状态
- `pageIndex` (可选): 页码
- `pageSize` (可选): 每页条数，默认10，最大10

**返回值**:
- `total`: 旅行社总数
- `resultList`: 旅行社及运营企业列表
  - `taName`: 旅行社名称
  - `englishName`: 英文名称
  - `taLicenseNumber`: 许可证号
  - `name`: 企业名称
  - `nameId`: 企业主体ID
  - `legalRepresentative`: 法定代表人
  - `regCapital`: 注册资本
  - `annualTurnoverAlgValue`: 年营业额
  - `businessTags`: 业务标签
  - `operStatus`: 经营状态

### 5. tourism_scenic_area_detail
**功能**: 国标景区详情

**数据产品ID**: `6a98ec3fcc51ed421bf06fa2`

**参数**:
- `taId` (Schema 可选，实际调用请传入): 景区ID，来自 `tourism_scenic_area_search` 的实际搜索结果。按 PDF 文档保留可选性，但 2026-09-07 实测省略时上游返回 `21008 参数错误`；MCP 会保留该错误，不伪造成功结果。

**返回值**:
- `total`: 详情记录数，空结果为0
- `resultList`: 将上游详情对象包装为列表，保留原始字段与嵌套结构
  - `taName`: 景区名称
  - `taLandArea` / `taBuildingArea`: 占地面积 / 建筑面积，字符串原值；接口文档未注明单位，不推断或自动换算
  - `taFeatures`: 核心特色
  - `taAttractions`: 主要设施/景点，字符串列表
  - `taCultureValues`: 文化价值
  - `taIntroduction`: 简介
  - `taAddress`: 地址对象，含 `province`（省）、`city`（市）、`district`（区）、`value`（具体地址）
  - `taCategory`: 景区类型
  - `taBatchNumber`: 等级批次
  - `taOperatingEntity`: 运营主体列表，每项含 `nameId`（运营主体ID）和 `name`（运营主体名称）

**说明**: 此接口无分页参数；不得把景区详情中的嵌套列表拆成多条景区记录。

### 6. tourism_planning_list
**功能**: 文旅规划明细

**数据产品ID**: `6a995506a96d8a6e55377905`

**参数**:
- `taId` (必填): 景区ID，来自 `tourism_scenic_area_search` 或 `tourism_countryside_search` 的实际搜索结果，不接受空字符串
- `pageIndex` (可选): 页码，默认1，最小1
- `pageSize` (可选): 每页条数，默认10，最大10，最小1

**返回值**:
- `total`: 规划记录总数，保留上游总数而非当前页条数
- `resultList`: 规划记录列表，保留原始字段
  - `taPlanningType`: 类别
  - `taPlanningName`: 项目名称
  - `taPlanningDesc`: 建设内容与规模
  - `taPlanningNews`: 最新进展
  - `taPlanningCompany`: 相关单位

**说明**: `pageSize` 超过10、页码小于1或 `taId` 为空时返回参数错误，不调用上游接口。空页或空结果仅表示本次接口未返回规划数据，不能据此断言景区不存在或没有规划。

## 使用注意事项

1. **Tool选择**: 景区、重点村镇、旅宿和旅行社分别使用对应 Tool，不混用筛选参数。
2. **地区格式**: 旅宿多级地区使用英文逗号分隔，景区和直辖市筛选按 Tool 说明使用短名。
3. **区间校验**: 成立日期和注册资本下限不能大于上限。
4. **API限制**: 分页查询一页最多获取10条数据。
5. **合法空结果**: 未命中时返回 `total=0` 和 `resultList=[]`。
6. **详情与规划**: 景区详情不分页；规划查询需传入景区ID。面积等未声明单位的字段保留原值，不自行推断。

## 使用提问示例

### tourism_scenic_area_search (国标文旅景区搜索)
1. 搜索北京名称中包含“故宫”的景区
2. 查询杭州的国标景区
3. 查看指定批次评定的景区名单

### tourism_countryside_search (乡村旅游重点村镇搜索)
1. 查询浙江省的乡村旅游重点村镇
2. 搜索名称中包含“村”的重点村镇
3. 查看某一批次入选的重点村镇

### tourism_accommodation_search (餐饮民宿与星级饭店搜索)
1. 查找杭州正在经营的民宿
2. 查询上海的星级饭店及运营企业
3. 搜索注册资本超过1000万元的旅宿企业

### tourism_travel_agency_search (出境游旅行社搜索)
1. 查询上海的出境游旅行社
2. 搜索名称中包含“旅行社”的企业
3. 查看北京存续状态的出境游旅行社

### tourism_scenic_area_detail (国标景区详情)
1. 先搜索故宫景区，再查询其核心特色、主要景点和文化价值
2. 根据刚查到的景区ID，查看景区地址及运营主体
3. 查询指定国标景区的占地面积、建筑面积和简介，保留接口原始单位表达

### tourism_planning_list (文旅规划明细)
1. 搜索某个国标景区，查询其文旅规划项目名称和建设规模
2. 根据乡村旅游重点村镇搜索结果中的景区ID，查看规划最新进展和相关单位
3. 继续读取该景区文旅规划的第2页，每页10条

## 测试验证

```bash
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

离线测试覆盖6个工具的注册与只读标记、新增接口的参数契约、Product ID 路由、详情嵌套字段、规划分页边界、空结果及上游错误透传，不需要真实凭据。

2026-09-07 验证：18 个离线测试通过；真实 MCP 检查 23 项通过 22 项，覆盖6个工具及规划分页。规划非空样本共14条，第1页10条、第2页4条；详情嵌套字段与搜索对象一致。唯一已知差异是详情省略 `taId` 返回 `21008`，与 PDF 的可选标注不一致；传入有效ID的调用链正常。

接口依据：`国标景区详情_2026-09-07_15-14-48.pdf`、`文旅规划明细_2026-09-07_15-14-54.pdf`。真实接口验证需在本地 `.env` 配置有效凭据并开通对应数据产品后执行，测试输出不得提交真实业务响应或凭据。
