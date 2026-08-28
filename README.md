# 文旅：文旅景区搜索

[该MCP服务提供国标景区、乡村旅游重点村镇、餐饮民宿、星级饭店和出境游旅行社查询功能。](https://www.handaas.com/)


## 主要功能

- 🏞️ 国标景区搜索
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

## 使用注意事项

1. **Tool选择**: 景区、重点村镇、旅宿和旅行社分别使用对应 Tool，不混用筛选参数。
2. **地区格式**: 旅宿多级地区使用英文逗号分隔，景区和直辖市筛选按 Tool 说明使用短名。
3. **区间校验**: 成立日期和注册资本下限不能大于上限。
4. **API限制**: 分页查询一页最多获取10条数据。
5. **合法空结果**: 未命中时返回 `total=0` 和 `resultList=[]`。

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

## 测试验证

```bash
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

当前服务包含 7 个离线单元测试。真实接口验证需在本地 `.env` 配置有效凭据后执行，测试输出不得提交真实业务响应或凭据。
