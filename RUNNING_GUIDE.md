# OpenManus 程序运行入口与单元测试指南

## 一、程序运行入口

OpenManus 提供了多个程序运行入口，适用于不同的使用场景：

### 1. 主入口 - `main.py` (单代理模式)

**功能**：运行单个 Manus 代理，适用于大多数通用任务。

**运行方式**：

```bash
# 交互式运行（会提示输入）
python main.py

# 命令行参数运行
python main.py --prompt "你的任务描述"
```

**代码位置**：`/Users/zhuzhichao/code/OpenManus/main.py`

**主要流程**：
1. 创建并初始化 Manus 代理
2. 接收用户输入（命令行参数或交互式输入）
3. 执行代理任务
4. 清理资源

**示例**：
```bash
python main.py --prompt "帮我写一个 Python 函数来计算斐波那契数列"
```

---

### 2. 多代理流程入口 - `run_flow.py`

**功能**：运行多代理协作流程，支持规划式任务分解和多个专业代理协作。

**运行方式**：

```bash
python run_flow.py
```

**代码位置**：`/Users/zhuzhichao/code/OpenManus/run_flow.py`

**主要特性**：
- 支持多个代理协作（Manus + DataAnalysis）
- 使用 PlanningFlow 进行任务规划
- 支持 60 分钟超时控制
- 可通过配置启用数据分析代理

**配置启用数据分析代理**：
在 `config/config.toml` 中添加：
```toml
[runflow]
use_data_analysis_agent = true
```

**主要流程**：
1. 创建代理集合（Manus + 可选 DataAnalysis）
2. 创建 PlanningFlow
3. 执行流程并等待结果
4. 输出执行时间和结果

---

### 3. MCP 协议入口 - `run_mcp.py`

**功能**：运行基于 MCP (Model Context Protocol) 协议的代理，支持通过 MCP 协议连接外部工具服务器。

**运行方式**：

```bash
# 默认模式（stdio 连接）
python run_mcp.py

# 交互式模式
python run_mcp.py --interactive

# SSE 连接模式
python run_mcp.py --connection sse --server-url http://127.0.0.1:8000/sse

# 单次提示执行
python run_mcp.py --prompt "你的任务"
```

**代码位置**：`/Users/zhuzhichao/code/OpenManus/run_mcp.py`

**命令行参数**：
- `--connection, -c`: 连接类型，可选 `stdio` 或 `sse`（默认：stdio）
- `--server-url`: SSE 连接的服务器 URL（默认：http://127.0.0.1:8000/sse）
- `--interactive, -i`: 交互式模式
- `--prompt, -p`: 单次提示执行

**主要流程**：
1. 初始化 MCP 连接（stdio 或 SSE）
2. 创建 MCPAgent
3. 运行代理（交互式/单次/默认模式）
4. 清理资源

---

### 4. MCP 服务器入口 - `run_mcp_server.py`

**功能**：启动 OpenManus 的 MCP (Model Context Protocol) 服务器，允许其他客户端通过 MCP 协议连接并使用 OpenManus 的功能。

**运行方式**：

```bash
# 默认运行（使用 stdio 传输）
python run_mcp_server.py

# 使用 SSE 传输
python run_mcp_server.py --transport sse
```

**代码位置**：`/Users/zhuzhichao/code/OpenManus/run_mcp_server.py`

**主要特性**：
- 提供 MCP 协议服务器
- 支持 stdio 和 SSE 两种传输方式
- 允许外部客户端连接并使用 OpenManus 工具

**使用场景**：
- 作为 MCP 服务器供其他应用调用
- 集成到支持 MCP 协议的 IDE 或工具中

---

### 5. 沙箱模式入口 - `sandbox_main.py`

**功能**：运行在 Docker 沙箱环境中的 Manus 代理，提供隔离的执行环境。

**运行方式**：

```bash
# 交互式运行
python sandbox_main.py

# 命令行参数运行
python sandbox_main.py --prompt "你的任务"
```

**代码位置**：`/Users/zhuzhichao/code/OpenManus/sandbox_main.py`

**主要特性**：
- 使用 SandboxManus 代理
- 在 Docker 容器中执行任务
- 提供资源限制和隔离

**前置要求**：
- 需要 Docker 环境
- 需要在配置中启用沙箱设置

---

### 6. 通过安装后的命令运行

如果通过 `setup.py` 安装了包，可以使用命令行工具：

```bash
# 安装包
pip install -e .

# 使用命令行工具
openmanus
```

**配置位置**：`setup.py` 中的 `entry_points` 配置指向 `main:main`

---

## 二、运行单元测试

### 2.1 测试框架

项目使用 **pytest** 作为测试框架，并支持异步测试（`pytest-asyncio`）。

### 2.2 测试文件位置

所有测试文件位于 `tests/` 目录下：

```
tests/
└── sandbox/
    ├── test_client.py          # 沙箱客户端测试
    ├── test_docker_terminal.py  # Docker 终端测试
    ├── test_sandbox_manager.py  # 沙箱管理器测试
    └── test_sandbox.py         # 沙箱核心功能测试
```

### 2.3 运行测试

#### 基本运行方式

```bash
# 运行所有测试
pytest

# 运行指定目录的测试
pytest tests/

# 运行指定测试文件
pytest tests/sandbox/test_client.py

# 运行指定测试函数
pytest tests/sandbox/test_client.py::test_sandbox_creation

# 详细输出模式
pytest -v

# 更详细的输出（显示打印语句）
pytest -s

# 显示覆盖率
pytest --cov=app --cov-report=html
```

#### 运行特定测试

```bash
# 运行所有沙箱相关测试
pytest tests/sandbox/

# 运行单个测试文件
pytest tests/sandbox/test_sandbox.py -v

# 运行匹配模式的测试
pytest -k "test_sandbox" -v
```

#### 异步测试运行

由于项目大量使用异步代码，测试需要 `pytest-asyncio` 支持：

```bash
# 确保安装了 pytest-asyncio
pip install pytest pytest-asyncio

# 运行异步测试
pytest tests/ -v
```

### 2.4 测试示例

查看 `tests/sandbox/test_client.py` 可以看到测试示例：

```python
@pytest.mark.asyncio
async def test_sandbox_creation(local_client: LocalSandboxClient):
    """Tests sandbox creation with specific configuration."""
    config = SandboxSettings(
        image="python:3.12-slim",
        work_dir="/workspace",
        memory_limit="512m",
        cpu_limit=0.5,
    )
    
    await local_client.create(config)
    result = await local_client.run_command("python3 --version")
    assert "Python 3.10" in result
```

### 2.5 测试前置要求

#### 依赖安装

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 或安装所有依赖（包括测试依赖）
pip install -r requirements.txt
```

#### Docker 环境（沙箱测试）

运行沙箱相关测试需要 Docker 环境：

```bash
# 确保 Docker 正在运行
docker ps

# 如果 Docker 未运行，启动 Docker 服务
# macOS: 启动 Docker Desktop
# Linux: sudo systemctl start docker
```

### 2.6 测试配置

项目使用标准的 pytest 配置，无需额外的 `pytest.ini` 或 `pyproject.toml` 配置。

测试文件使用以下装饰器：
- `@pytest.mark.asyncio` - 标记异步测试
- `@pytest_asyncio.fixture` - 异步测试 fixture

### 2.7 常见测试命令

```bash
# 运行所有测试并显示详细输出
pytest -v

# 运行测试并显示覆盖率
pytest --cov=app --cov-report=term-missing

# 只运行失败的测试
pytest --lf

# 运行上次失败的测试
pytest --ff

# 并行运行测试（需要 pytest-xdist）
pytest -n auto

# 运行测试并生成 HTML 报告
pytest --html=report.html --self-contained-html
```

### 2.8 测试最佳实践

1. **测试隔离**：每个测试应该独立运行，不依赖其他测试的状态
2. **资源清理**：使用 fixture 确保测试后清理资源（如 Docker 容器）
3. **异步测试**：使用 `@pytest.mark.asyncio` 标记异步测试
4. **测试命名**：测试函数名以 `test_` 开头
5. **断言清晰**：使用清晰的断言消息

### 2.9 调试测试

```bash
# 运行测试并在失败时进入调试器
pytest --pdb

# 运行测试并显示详细输出
pytest -vv

# 运行特定测试并显示打印输出
pytest tests/sandbox/test_client.py::test_sandbox_creation -s
```

---

## 三、快速开始示例

### 3.1 运行主程序

```bash
# 1. 确保已安装依赖
pip install -r requirements.txt

# 2. 配置 LLM API（编辑 config/config.toml）
cp config/config.example.toml config/config.toml
# 编辑 config.toml 添加你的 API key

# 3. 运行主程序
python main.py
```

### 3.2 运行测试

```bash
# 1. 安装测试依赖
pip install pytest pytest-asyncio

# 2. 确保 Docker 运行（用于沙箱测试）
docker ps

# 3. 运行测试
pytest tests/ -v
```

---

## 四、总结

### 程序入口选择指南

| 入口文件 | 适用场景 | 特点 |
|---------|---------|------|
| `main.py` | 通用任务 | 单代理，简单直接 |
| `run_flow.py` | 复杂任务 | 多代理协作，任务规划 |
| `run_mcp.py` | MCP 工具集成 | 支持外部 MCP 服务器 |
| `run_mcp_server.py` | MCP 服务器 | 提供 MCP 协议服务 |
| `sandbox_main.py` | 安全执行 | Docker 隔离环境 |

### 测试运行总结

- **测试框架**：pytest + pytest-asyncio
- **测试位置**：`tests/sandbox/`
- **运行命令**：`pytest tests/ -v`
- **前置要求**：Docker（用于沙箱测试）

---

## 五、故障排查

### 5.1 程序运行问题

**问题**：`ModuleNotFoundError`
```bash
# 解决：确保在项目根目录运行，或安装包
pip install -e .
```

**问题**：配置未找到
```bash
# 解决：复制示例配置
cp config/config.example.toml config/config.toml
```

### 5.2 测试运行问题

**问题**：`pytest: command not found`
```bash
# 解决：安装 pytest
pip install pytest pytest-asyncio
```

**问题**：Docker 相关测试失败
```bash
# 解决：确保 Docker 正在运行
docker ps
```

**问题**：异步测试失败
```bash
# 解决：确保安装了 pytest-asyncio
pip install pytest-asyncio
```

---

如有其他问题，请参考项目 README 或提交 Issue。
