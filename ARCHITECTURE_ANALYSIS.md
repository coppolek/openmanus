# OpenManus 软件架构分析

## 一、项目概述

OpenManus 是一个开源的通用 AI 代理框架，旨在构建能够使用多种工具解决各种任务的智能代理系统。项目采用 Python 3.12+ 开发，支持多种 LLM 提供商（OpenAI、Azure、AWS Bedrock 等），并集成了丰富的工具生态。

## 二、整体架构

### 2.1 架构层次

OpenManus 采用分层架构设计，主要分为以下几个层次：

```
┌─────────────────────────────────────────┐
│         入口层 (Entry Points)           │
│  main.py / run_flow.py / run_mcp.py    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         代理层 (Agent Layer)             │
│  BaseAgent → ReActAgent → ToolCallAgent │
│  → Manus / DataAnalysis / MCPAgent      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         工具层 (Tool Layer)              │
│  BaseTool → ToolCollection              │
│  PythonExecute / BrowserUse / etc.      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      基础设施层 (Infrastructure)        │
│  LLM / Config / Sandbox / Memory        │
└─────────────────────────────────────────┘
```

### 2.2 核心组件

#### 1. 代理系统 (Agent System)

**继承层次结构：**

```
BaseAgent (抽象基类)
  ├── 状态管理 (AgentState: IDLE/RUNNING/FINISHED/ERROR)
  ├── 内存管理 (Memory)
  ├── 执行循环 (run/step)
  └── 卡死检测 (is_stuck/handle_stuck_state)
      │
      └── ReActAgent (ReAct 模式实现)
          ├── think() - 思考阶段（抽象方法，由子类实现）
          ├── act() - 行动阶段（抽象方法，由子类实现）
          └── step() - 执行单步：think → act
              │
              └── ToolCallAgent (工具调用代理)
                  ├── 工具选择与执行
                  ├── 工具结果处理
                  └── 特殊工具处理
                      │
                      ├── Manus (通用代理)
                      ├── DataAnalysis (数据分析代理)
                      └── MCPAgent (MCP 协议代理)
```

**关键特性：**
- **状态机管理**：通过 `AgentState` 枚举管理代理状态转换
- **内存系统**：使用 `Memory` 类维护对话历史，支持消息限制
- **执行控制**：通过 `max_steps` 限制最大执行步数，防止无限循环
- **卡死检测**：自动检测重复响应，触发策略调整
- **ReAct 模式**：采用 Reasoning + Acting 模式，将思考与行动分离
  - `think()`: 分析当前状态，决定下一步行动
  - `act()`: 执行决定的行动（如工具调用）
  - `step()`: 组合 think 和 act 的完整执行步骤

#### 2. 工具系统 (Tool System)

**工具架构：**

```
BaseTool (抽象基类)
  ├── name: str
  ├── description: str
  ├── parameters: dict
  ├── execute() - 抽象执行方法
  └── to_param() - 转换为函数调用格式
      │
      ├── PythonExecute (Python 代码执行)
      ├── BrowserUseTool (浏览器自动化)
      ├── StrReplaceEditor (字符串替换编辑器)
      ├── FileOperators (文件操作)
      ├── WebSearch (网络搜索，支持多搜索引擎)
      │   ├── GoogleSearch
      │   ├── BingSearch
      │   ├── DuckDuckGoSearch
      │   └── BaiduSearch
      ├── MCPClientTool (MCP 客户端工具)
      ├── AskHuman (人工交互)
      ├── Terminate (终止执行)
      ├── CreateChatCompletion (创建对话)
      ├── Bash (Bash 命令执行)
      ├── ComputerUseTool (计算机使用工具)
      ├── Crawl4AI (网页爬取)
      ├── Planning (规划工具)
      └── Sandbox Tools (沙箱工具)
          ├── SandboxBrowserTool
          ├── SandboxFilesTool
          ├── SandboxShellTool
          └── SandboxVisionTool
      └── Chart Visualization (数据可视化)
          ├── DataVisualization (数据可视化工具)
          └── ChartPrepare (图表准备工具)

ToolCollection (工具集合)
  ├── tools: List[BaseTool]
  ├── tool_map: Dict[str, BaseTool]
  ├── execute() - 执行指定工具
  └── to_params() - 转换为 LLM 函数调用参数
```

**工具结果处理：**

```python
ToolResult
  ├── output: Any - 工具输出
  ├── error: Optional[str] - 错误信息
  ├── base64_image: Optional[str] - 图像结果
  └── system: Optional[str] - 系统消息
```

#### 3. LLM 接口层 (LLM Interface)

**设计特点：**
- **多提供商支持**：OpenAI、Azure OpenAI、AWS Bedrock
- **单例模式**：每个配置名称对应一个 LLM 实例
- **Token 管理**：自动计算和跟踪 token 使用量，支持限制检查
- **多模态支持**：支持文本和图像输入（GPT-4o、Claude 等）
- **重试机制**：使用 `tenacity` 实现指数退避重试
- **流式响应**：支持流式和非流式响应

**核心方法：**
- `ask()` - 基础文本对话
- `ask_with_images()` - 带图像的对话
- `ask_tool()` - 工具调用模式

#### 4. 沙箱系统 (Sandbox System)

**Docker 沙箱实现：**

```
DockerSandbox
  ├── 容器管理 (创建/启动/停止/清理)
  ├── 命令执行 (run_command)
  ├── 文件操作 (read_file/write_file)
  ├── 文件传输 (copy_from/copy_to)
  └── 资源限制 (内存/CPU/网络)
```

**安全特性：**
- 路径遍历防护
- 资源限制（内存、CPU）
- 网络隔离选项
- 超时控制

#### 5. 配置系统 (Configuration System)

**配置结构：**

```python
AppConfig
  ├── llm: Dict[str, LLMSettings] - LLM 配置（支持多配置）
  ├── sandbox: SandboxSettings - 沙箱配置
  ├── browser_config: BrowserSettings - 浏览器配置
  ├── search_config: SearchSettings - 搜索配置
  ├── mcp_config: MCPSettings - MCP 协议配置
  ├── run_flow_config: RunflowSettings - 流程配置
  └── daytona_config: DaytonaSettings - Daytona 配置
```

**配置加载：**
- 从 `config/config.toml` 加载配置
- 支持配置覆盖和默认值
- 线程安全的单例模式

#### 6. 流程编排 (Flow Orchestration)

**流程类型：**

```
BaseFlow (抽象基类)
  ├── agents: Dict[str, BaseAgent] - 代理集合
  ├── primary_agent_key: str - 主代理标识
  └── execute() - 执行流程
      │
      └── PlanningFlow (规划流程)
          └── 多代理协作执行
```

**FlowFactory：**
- 工厂模式创建不同类型的流程
- 支持动态添加代理

#### 7. MCP 协议支持 (Model Context Protocol)

**MCP 集成：**

```
MCPClients
  ├── connect_sse() - SSE 连接
  ├── connect_stdio() - 标准输入输出连接
  ├── disconnect() - 断开连接
  └── tools: List[MCPClientTool] - MCP 工具列表
```

**支持特性：**
- SSE (Server-Sent Events) 连接
- stdio (标准输入输出) 连接
- 动态工具发现和注册
- 多服务器连接管理

## 三、设计模式

### 3.1 继承与多态

- **代理继承链**：BaseAgent → ReActAgent → ToolCallAgent → 具体代理
- **工具继承**：所有工具继承自 BaseTool，实现统一的接口

### 3.2 工厂模式

- **FlowFactory**：根据类型创建不同的流程实例
- **Agent 工厂方法**：Manus.create() 用于异步初始化

### 3.3 单例模式

- **Config**：全局配置单例，线程安全
- **LLM**：每个配置名称对应一个单例实例

### 3.4 策略模式

- **工具选择策略**：ToolChoice (NONE/AUTO/REQUIRED)
- **搜索引擎策略**：支持多个搜索引擎和回退机制

### 3.5 观察者模式

- **状态转换**：通过 `state_context` 上下文管理器管理状态
- **消息系统**：Memory 维护消息历史，代理观察消息变化

## 四、数据流

### 4.1 单代理执行流程

```
用户输入
  ↓
Agent.run(request)
  ↓
Memory.add_message(user_message)
  ↓
循环执行 (最多 max_steps 次):
  ├── Agent.step()
  │   ├── think() - LLM 思考
  │   │   ├── LLM.ask_tool(messages, tools)
  │   │   └── 返回工具调用或文本响应
  │   │
  │   └── act() - 执行工具
  │       ├── ToolCollection.execute(tool_name, args)
  │       ├── BaseTool.execute(**kwargs)
  │       └── 返回 ToolResult
  │
  └── Memory.add_message(tool_result)
  ↓
Agent.state = FINISHED
  ↓
返回结果
```

### 4.2 多代理流程执行

```
用户输入
  ↓
FlowFactory.create_flow(FlowType.PLANNING)
  ↓
PlanningFlow.execute(input_text)
  ↓
主代理 (Manus) 规划任务
  ↓
根据任务类型选择代理
  ├── 数据分析任务 → DataAnalysis Agent
  └── 通用任务 → Manus Agent
  ↓
代理执行并返回结果
  ↓
整合结果并返回
```

### 4.3 工具调用流程

```
LLM 响应 (包含 tool_calls)
  ↓
ToolCallAgent.act()
  ↓
遍历 tool_calls:
  ├── 解析工具名称和参数
  ├── ToolCollection.execute(name, args)
  ├── BaseTool.execute(**kwargs)
  ├── 处理特殊工具 (如 Terminate)
  └── 返回 ToolResult
  ↓
Memory.add_message(tool_result)
  ↓
继续下一轮思考
```

## 五、关键特性

### 5.1 异步执行

- 整个系统基于 `asyncio` 实现异步执行
- 所有 I/O 操作（LLM 调用、文件操作、网络请求）都是异步的
- 支持并发工具执行

### 5.2 错误处理

- **TokenLimitExceeded**：Token 限制异常，不重试
- **SandboxTimeoutError**：沙箱超时异常
- **ToolError**：工具执行错误
- 重试机制：LLM 调用使用 tenacity 实现自动重试

### 5.3 扩展性

- **工具扩展**：通过继承 BaseTool 轻松添加新工具
- **代理扩展**：通过继承 ToolCallAgent 创建专用代理
- **流程扩展**：通过继承 BaseFlow 创建新的流程类型
- **MCP 集成**：支持通过 MCP 协议动态添加外部工具

### 5.4 安全性

- **沙箱隔离**：Docker 容器隔离执行环境
- **路径安全**：防止路径遍历攻击
- **资源限制**：内存、CPU、网络限制
- **超时控制**：防止无限执行

## 六、模块依赖关系

```
main.py / run_flow.py / run_mcp.py
  ↓
app.agent.manus / data_analysis / mcp
  ↓
app.agent.toolcall / react / base
  ↓
app.tool.* (各种工具)
  ↓
app.llm (LLM 接口)
  ↓
app.config (配置管理)
  ↓
app.sandbox.* (沙箱系统)
  ↓
app.schema (数据模型)
```

## 七、技术栈

### 7.1 核心依赖

- **Pydantic**：数据验证和模型定义
- **OpenAI SDK**：LLM API 调用
- **Tenacity**：重试机制
- **Docker SDK**：容器管理
- **Playwright**：浏览器自动化
- **Tiktoken**：Token 计算

### 7.2 异步框架

- **asyncio**：异步执行框架
- **aiofiles**：异步文件操作
- **httpx**：异步 HTTP 客户端

### 7.3 工具库

- **browser-use**：浏览器自动化工具
- **crawl4ai**：网页爬取
- **googlesearch-python**：搜索引擎集成

## 八、架构优势

1. **模块化设计**：清晰的层次结构，易于理解和维护
2. **可扩展性**：通过继承和组合轻松扩展功能
3. **类型安全**：使用 Pydantic 进行数据验证
4. **异步高效**：充分利用异步 I/O 提升性能
5. **工具生态**：丰富的内置工具和 MCP 协议支持
6. **多 LLM 支持**：支持多种 LLM 提供商
7. **安全隔离**：沙箱系统提供安全的执行环境

## 九、潜在改进方向

1. **持久化存储**：添加对话历史持久化
2. **监控与日志**：增强监控和日志系统
3. **性能优化**：工具并发执行优化
4. **测试覆盖**：增加单元测试和集成测试
5. **文档完善**：API 文档和架构文档
6. **配置管理**：支持环境变量和动态配置
7. **插件系统**：更灵活的插件加载机制

## 十、总结

OpenManus 采用清晰的分层架构，通过代理-工具-基础设施的三层设计实现了高度模块化和可扩展的系统。核心设计理念包括：

- **抽象与多态**：通过基类定义统一接口，子类实现具体功能
- **组合优于继承**：工具系统通过组合方式灵活集成
- **异步优先**：全面采用异步编程提升性能
- **安全第一**：沙箱隔离和资源限制保障安全
- **协议支持**：MCP 协议支持实现工具生态扩展

整体架构设计合理，具有良好的可维护性和扩展性，适合作为 AI 代理框架的基础架构。
