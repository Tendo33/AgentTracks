# Meta Planner Agent 完整指南

## 目录

- [项目概述](#项目概述)
- [核心概念](#核心概念)
- [系统架构](#系统架构)
- [执行流程](#执行流程)
- [配置说明](#配置说明)
- [使用指南](#使用指南)
- [代码结构](#代码结构)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

---

## 项目概述

### 什么是 Meta Planner Agent？

Meta Planner Agent 是一个高级的AI代理系统，采用 **规划-执行** 模式来处理复杂的多步骤任务。它能够：

- 🧠 **智能任务分解**：将复杂任务自动分解为可管理的子任务
- 🤖 **动态工作代理**：根据任务需求动态创建专业的 Worker Agent
- 📊 **进度追踪**：通过结构化的路线图系统管理任务进度
- 💾 **状态持久化**：支持长时间运行任务的状态保存和恢复
- 🔄 **灵活模式**：可在简单 ReAct 模式和高级规划模式之间切换

### 适用场景

- 数据分析和报告生成
- 综合研究项目
- 多步骤内容创建
- 复杂问题解决
- 需要协调多个工具和操作的任务

---

## 核心概念

### 1. 规划-执行模式（Planning-Execution Pattern）

```
用户请求 → Meta Planner 分析 → 任务分解 → 创建 Workers → 执行子任务 → 汇总结果
```

- **Meta Planner（元规划器）**：负责理解需求、分解任务、协调执行
- **Worker Agent（工作代理）**：专门执行具体子任务的代理，配备相应工具

### 2. 三种运行模式

#### Dynamic Mode（动态模式，推荐）
```python
PLANNER_MODE=dynamic
```
- **特点**：根据任务复杂度自动选择模式
- **适用**：大多数场景，平衡灵活性和能力
- **行为**：
  - 简单任务：使用 ReAct 模式直接处理
  - 复杂任务：自动切换到规划模式

#### Enforced Mode（强制模式）
```python
PLANNER_MODE=enforced
```
- **特点**：所有任务都使用规划模式
- **适用**：已知需要规划的复杂任务
- **行为**：立即启用规划工具，直接进入规划-执行流程

#### Disable Mode（禁用模式）
```python
PLANNER_MODE=disable
```
- **特点**：只使用简单的 ReAct 模式
- **适用**：简单的单步任务
- **行为**：不进行任务分解，直接使用可用工具

### 3. 核心组件关系

```
┌─────────────────────────────────────────────────────────┐
│                    Meta Planner                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Planner Notebook (上下文状态)           │   │
│  │  • 用户输入历史                                  │   │
│  │  • 任务分析                                      │   │
│  │  • 路线图（Roadmap）                             │   │
│  │  • 生成的文件                                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────┐         ┌──────────────────────┐    │
│  │  Roadmap     │         │   Worker Manager     │    │
│  │  Manager     │◄───────►│                      │    │
│  │              │         │  • Worker Pool       │    │
│  │  • 任务分解  │         │  • Worker 创建       │    │
│  │  • 进度追踪  │         │  • Worker 执行       │    │
│  └──────────────┘         └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘
           │                          │
           ▼                          ▼
    ┌──────────────┐         ┌──────────────────┐
    │  子任务      │         │  Worker Agents    │
    │  规范        │         │  (ReAct Agents)   │
    │             │         │                  │
    │  • 描述     │         │  • 工具集         │
    │  • 输入     │         │  • 系统提示词     │
    │  • 期望输出 │         │  • 记忆           │
    │  • 所需工具 │         │                  │
    └──────────────┘         └──────────────────┘
```

---

## 系统架构

### 目录结构

```
02_meta_planner_agent/
├── main.py                          # 主入口文件
├── config.py                        # 配置管理（新增）
├── env.example                      # 环境变量示例（新增）
├── README.md                        # 简要说明
├── AGENT_GUIDE.md                   # 本文档（新增）
│
├── _meta_planner.py                 # Meta Planner 核心实现
│   ├── class MetaPlanner            # 主代理类
│   ├── Hook 函数                    # 生命周期钩子
│   └── 状态管理                     # 状态保存/加载
│
├── _planning_tools/                 # 规划工具包
│   ├── __init__.py
│   ├── _planning_notebook.py        # 数据结构定义
│   │   ├── PlannerNoteBook          # 规划笔记本
│   │   ├── RoadMap                  # 路线图
│   │   ├── SubTaskStatus            # 子任务状态
│   │   ├── WorkerInfo               # Worker 信息
│   │   └── WorkerResponse           # Worker 响应
│   │
│   ├── _roadmap_manager.py          # 路线图管理
│   │   └── class RoadmapManager
│   │       ├── decompose_task_and_build_roadmap()
│   │       ├── revise_roadmap()
│   │       └── get_next_unfinished_subtask()
│   │
│   └── _worker_manager.py           # Worker 管理
│       └── class WorkerManager
│           ├── create_worker()
│           ├── execute_worker()
│           └── show_current_worker_pool()
│
└── _built_in_long_sys_prompt/       # 系统提示词
    ├── meta_planner_sys_prompt.md   # Meta Planner 提示词
    ├── _worker_additional_sys_prompt.md  # Worker 附加提示
    └── _tool_usage_rules.md         # 工具使用规则
```

### 关键类图

```
┌─────────────────────────────────────────────────┐
│              ReActAgent                         │
│  (AgentScope 基础类)                            │
│                                                 │
│  • model: ChatModelBase                         │
│  • memory: MemoryBase                           │
│  • toolkit: Toolkit                             │
│  • reasoning() / acting()                       │
└─────────────────────────────────────────────────┘
                    ▲
                    │ 继承
                    │
┌─────────────────────────────────────────────────┐
│              MetaPlanner                        │
│  (核心规划代理)                                 │
│                                                 │
│  • planner_notebook: PlannerNoteBook            │
│  • roadmap_manager: RoadmapManager              │
│  • worker_manager: WorkerManager                │
│  • worker_full_toolkit: Toolkit                 │
│  • planner_mode: str                            │
│  • in_planner_mode: bool                        │
│                                                 │
│  方法：                                         │
│  • prepare_planner_tools()                      │
│  • enter_solving_complicated_task_mode()       │
│  • resume_planner_tools()                       │
└─────────────────────────────────────────────────┘
```

### 数据流

```
1. 用户输入
   ↓
2. Meta Planner 接收并记录到 PlannerNoteBook
   ↓
3. 判断是否需要进入规划模式
   ↓ (如果需要)
4. 调用 decompose_task_and_build_roadmap
   • 分析任务
   • 创建 RoadMap
   • 定义 SubTaskSpecification
   ↓
5. 获取下一个未完成子任务
   ↓
6. 创建或选择 Worker Agent
   • 确定所需工具
   • 编写系统提示词
   • 创建 ReActAgent
   ↓
7. 执行 Worker
   • 传递详细指令
   • Worker 执行推理-行动循环
   • 返回 WorkerResponse
   ↓
8. 更新路线图
   • 记录进度
   • 更新子任务状态
   • 保存生成的文件
   ↓
9. 重复步骤 5-8 直到所有子任务完成
   ↓
10. 汇总结果并返回给用户
```

---

## 执行流程

### 阶段 1: 初始化

```python
# main.py 中的初始化流程

1. 加载配置
   config = load_config()

2. 设置 MCP 客户端
   - Tavily MCP (搜索功能)
   - Filesystem MCP (文件操作)

3. 创建工具包
   - planner_toolkit: Meta Planner 的工具
   - worker_toolkit: Worker Agents 的完整工具集

4. 初始化 MetaPlanner
   - 配置模型
   - 设置内存
   - 注册工具
   - 配置钩子函数
```

### 阶段 2: 任务接收与分析

```
用户: "请研究 Meta 公司 2025 年 Q1 的股票表现并创建分析报告"

↓ MetaPlanner 分析

判断: 这是一个复杂任务，需要规划
- 涉及多个步骤（搜索、数据分析、报告编写）
- 需要多个工具（搜索、文件操作）
- 无法在 5 次迭代内完成

↓ 决策

调用: enter_solving_complicated_task_mode("meta_q1_stock_analysis")
```

### 阶段 3: 任务分解

```python
# Meta Planner 调用 decompose_task_and_build_roadmap

任务分解为：

子任务 1: "搜索 Meta Q1 2025 财报和股价数据"
  - 输入: Meta, Q1 2025, 股票, 财报
  - 期望输出: 关键财务指标、股价变化
  - 所需工具: tavily_search

子任务 2: "分析数据并识别趋势"
  - 输入: 子任务1的搜索结果
  - 期望输出: 趋势分析、关键发现
  - 所需工具: 无特殊工具

子任务 3: "创建 Markdown 格式的分析报告"
  - 输入: 子任务2的分析结果
  - 期望输出: meta_q1_analysis.md 文件
  - 所需工具: write_file

路线图状态：
[Planned] 子任务 1
[Planned] 子任务 2
[Planned] 子任务 3
```

### 阶段 4: Worker 创建与执行

```python
# 对每个子任务

1. get_next_unfinished_subtask_from_roadmap()
   → 返回子任务 1

2. create_worker(
     worker_name="meta_stock_researcher",
     tool_names=["tavily_search"],
     worker_system_prompt="""
       You are a financial research assistant.
       Your task is to search for Meta's Q1 2025 stock 
       performance and financial data.
       ...
     """
   )

3. execute_worker(
     subtask_idx=0,
     selected_worker_name="meta_stock_researcher",
     detailed_instruction="""
       Search for Meta's Q1 2025 financial report and 
       stock price changes. Focus on:
       - Revenue and profit
       - Stock price trends
       - Key business metrics
     """
   )

4. Worker 执行（内部 ReAct 循环）：
   思考 → 搜索 → 观察 → 思考 → 搜索 → 观察 → 总结
   
   返回 WorkerResponse：
   {
     "subtask_progress_summary": "找到了 Meta Q1 2025 的关键数据...",
     "next_step": "",
     "generated_files": {},
     "task_done": true
   }

5. revise_roadmap(
     action="revise_subtask",
     subtask_idx=0,
     new_status="Done",
     update_to_subtask=Update(...)
   )

路线图状态：
[Done] 子任务 1 ✓
[Planned] 子任务 2
[Planned] 子任务 3
```

### 阶段 5: 进度追踪与状态保存

```python
# 在每个关键步骤后自动保存状态

Hook: post_reasoning_hook
  → 保存: ./agent-states/run-20251031120000/state-post_reasoning-20251031120100.json

Hook: post_action_hook
  → 保存: ./agent-states/run-20251031120000/state-post-action-create_worker-20251031120200.json

状态文件内容：
{
  "planner_notebook": {
    "user_input": [...],
    "roadmap": {
      "original_task": "...",
      "decomposed_tasks": [...]
    },
    "files": {...}
  },
  "worker_pool": {...},
  "memory": [...]
}
```

### 阶段 6: 完成与结果返回

```python
# 所有子任务完成后

路线图状态：
[Done] 子任务 1 ✓
[Done] 子任务 2 ✓
[Done] 子任务 3 ✓

生成的文件：
{
  "/path/to/meta_agent_demo_env/meta_q1_stock_analysis/meta_q1_analysis.md": 
    "Meta Q1 2025 股票分析报告"
}

Meta Planner 汇总：
"任务已完成。我已经完成了对 Meta 公司 2025 年 Q1 股票表现的研究，
并创建了详细的分析报告。报告已保存在 meta_q1_analysis.md 文件中，
包含了财务数据、股价趋势和关键业务指标的综合分析。"
```

---

## 配置说明

### 环境变量配置

所有配置都通过环境变量管理，支持从 `.env` 文件加载。

#### 必需配置

```bash
# OpenAI API 密钥
OPENAI_API_KEY=sk-your-key-here

# Tavily API 密钥（搜索功能）
TAVILY_API_KEY=tvly-your-key-here
```

#### 模型配置

```bash
# API 基础 URL（默认：https://api.openai.com/v1）
OPENAI_BASE_URL=https://api.openai.com/v1

# 模型名称（默认：gpt-4-turbo）
CHAT_MODEL=gpt-4-turbo

# 温度参数（默认：0.7）
MODEL_TEMPERATURE=0.7

# 最大 token 数（默认：32000）
MODEL_MAX_TOKENS=32000

# 启用流式响应（默认：true）
MODEL_STREAM=true
```

#### 代理配置

```bash
# 代理名称（默认：Task-Meta-Planner）
AGENT_NAME=Task-Meta-Planner

# 工作目录（默认：./meta_agent_demo_env）
AGENT_OPERATION_DIR=/custom/path/to/workspace

# 状态保存目录（默认：./agent-states）
AGENT_STATE_SAVING_DIR=./agent-states

# Planner 最大迭代次数（默认：100）
AGENT_MAX_ITERS=100

# Worker 最大迭代次数（默认：20）
AGENT_WORKER_MAX_ITERS=20
```

#### 规划器配置

```bash
# 规划模式（默认：dynamic）
# 选项：disable, dynamic, enforced
PLANNER_MODE=dynamic
```

#### 工具配置

```bash
# 工具响应最大字符数（默认：40970）
TOOL_RESPONSE_BUDGET=40970
```

#### 日志配置

```bash
# 日志级别（默认：DEBUG）
LOG_LEVEL=DEBUG

# 启用 logfire（默认：false）
ENABLE_LOGFIRE=false
```

#### MCP 配置

```bash
# NPX 命令（默认：npx）
MCP_NPX_COMMAND=npx

# Tavily MCP 包（默认：tavily-mcp@latest）
MCP_TAVILY_PACKAGE=tavily-mcp@latest

# 文件系统 MCP 包
MCP_FILESYSTEM_PACKAGE=@modelcontextprotocol/server-filesystem
```

### 配置使用示例

```python
# 在代码中访问配置
from config import config

# 获取配置值
api_key = config.openai_api_key
model_name = config.chat_model
working_dir = config.get_agent_working_dir()

# 打印配置（隐藏敏感信息）
print(config.to_dict())
```

---

## 使用指南

### 快速开始

1. **安装依赖**

```bash
# 确保已安装 Python 3.11+
python --version

# 安装项目依赖
pip install -e .
```

2. **配置环境变量**

```bash
# 复制配置模板
cd agentscope_learning/02_meta_planner_agent
cp env.example .env

# 编辑 .env 文件，填入你的 API 密钥
nano .env
```

3. **运行代理**

```bash
# 启动交互式会话
python main.py
```

4. **开始对话**

```
Bob: 创建一个关于人工智能的综合研究报告

Task-Meta-Planner: [分析任务并开始执行...]
```

### 常见使用场景

#### 场景 1: 数据分析任务

```
用户输入：
"分析 ./data.csv 文件中的销售数据，识别趋势，并创建包含图表的报告"

执行流程：
1. Meta Planner 进入规划模式
2. 分解为子任务：
   - 读取 CSV 文件
   - 数据分析和趋势识别
   - 创建可视化
   - 编写报告
3. 创建数据分析 Worker
4. 依次执行各子任务
5. 生成最终报告
```

#### 场景 2: 研究项目

```
用户输入：
"研究阿里巴巴最新的季度业绩和竞争地位"

执行流程：
1. 使用 Tavily 搜索最新财报
2. 搜索竞争对手信息
3. 分析比较数据
4. 创建结构化报告
```

#### 场景 3: 状态恢复

```bash
# 如果任务中断，从保存的状态恢复
python main.py --load_state ./agent-states/run-20251031120000/state-post_reasoning-20251031120500.json

# 代理将从保存的状态继续执行
```

### 命令行参数

```bash
python main.py [OPTIONS]

OPTIONS:
  --load_state PATH    从指定的状态文件恢复执行
                       示例: --load_state ./agent-states/run-xxx/state-xxx.json
```

---

## 代码结构

### 核心类详解

#### 1. MetaPlanner 类

**位置**: `_meta_planner.py`

**继承**: `ReActAgent`

**关键属性**:
```python
class MetaPlanner(ReActAgent):
    # 工作目录
    agent_working_dir_root: str
    task_dir: str
    
    # 工具和状态
    worker_full_toolkit: Toolkit
    planner_notebook: PlannerNoteBook
    roadmap_manager: RoadmapManager
    worker_manager: WorkerManager
    
    # 模式控制
    planner_mode: Literal["disable", "dynamic", "enforced"]
    in_planner_mode: bool
    
    # 状态管理
    state_saving_dir: Optional[str]
    state_loading_reasoning_msg: Optional[Msg]
```

**关键方法**:
```python
def prepare_planner_tools(self, planner_mode):
    """准备规划工具"""
    # 创建 RoadmapManager 和 WorkerManager
    # 注册规划工具到 toolkit

async def enter_solving_complicated_task_mode(self, task_name):
    """进入规划模式"""
    # 创建任务目录
    # 更新系统提示词
    # 激活规划工具

def resume_planner_tools(self):
    """从保存的状态恢复规划工具"""
```

**生命周期钩子**:
```python
# pre_reply: 记录用户输入
update_user_input_pre_reply_hook()

# pre_reasoning: 加载状态、组合推理消息
planner_load_state_pre_reasoning_hook()
planner_compose_reasoning_msg_pre_reasoning_hook()

# post_reasoning: 加载状态、移除临时消息、保存状态
planner_load_state_post_reasoning_hook()
planner_remove_reasoning_msg_post_reasoning_hook()
planner_save_post_reasoning_state()

# post_acting: 保存状态
planner_save_post_action_state()
```

#### 2. RoadmapManager 类

**位置**: `_planning_tools/_roadmap_manager.py`

**职责**: 管理任务分解和路线图

**关键方法**:
```python
async def decompose_task_and_build_roadmap(
    self,
    user_latest_input: str,
    given_task_conclusion: str,
    detail_analysis_for_plan: str,
    decomposed_subtasks: list[SubTaskSpecification]
) -> ToolResponse:
    """分解任务并构建路线图"""
    # 保存分析结果
    # 创建子任务状态
    # 更新路线图

async def get_next_unfinished_subtask_from_roadmap(
    self
) -> ToolResponse:
    """获取下一个未完成的子任务"""
    # 遍历路线图
    # 返回第一个 Planned 或 In-process 的任务

async def revise_roadmap(
    self,
    action: Literal["add_subtask", "revise_subtask", "remove_subtask"],
    subtask_idx: int,
    subtask_specification: Optional[SubTaskSpecification],
    update_to_subtask: Optional[Update],
    new_status: Literal["Planned", "In-process", "Done"]
) -> ToolResponse:
    """修订路线图"""
    # 添加、修改或删除子任务
    # 更新子任务状态
```

#### 3. WorkerManager 类

**位置**: `_planning_tools/_worker_manager.py`

**职责**: 管理 Worker Agent 的创建和执行

**关键方法**:
```python
async def create_worker(
    self,
    worker_name: str,
    worker_system_prompt: str,
    tool_names: Optional[List[str]],
    agent_description: str
) -> ToolResponse:
    """创建 Worker Agent"""
    # 创建工具包
    # 添加系统提示词
    # 创建 ReActAgent
    # 注册到 worker pool

async def execute_worker(
    self,
    subtask_idx: int,
    selected_worker_name: str,
    detailed_instruction: str
) -> ToolResponse:
    """执行 Worker Agent"""
    # 获取 Worker
    # 创建任务消息
    # 执行 Worker (ReAct loop)
    # 返回 WorkerResponse
    # 更新路线图

async def show_current_worker_pool(
    self
) -> ToolResponse:
    """显示当前 Worker Pool"""
    # 列出所有可用的 Worker
```

#### 4. 数据结构类

**位置**: `_planning_tools/_planning_notebook.py`

```python
class PlannerNoteBook(BaseModel):
    """规划笔记本 - 存储整个会话的上下文"""
    time: str                       # 当前时间
    user_input: List[str]           # 用户输入历史
    detail_analysis_for_plan: str   # 任务分析
    roadmap: RoadMap                # 任务路线图
    files: Dict[str, str]           # 生成的文件
    full_tool_list: list[dict]      # 完整工具列表

class RoadMap(BaseModel):
    """路线图 - 任务分解结果"""
    original_task: str                      # 原始任务
    decomposed_tasks: List[SubTaskStatus]   # 分解的子任务列表

class SubTaskStatus(BaseModel):
    """子任务状态"""
    subtask_specification: SubTaskSpecification  # 子任务规范
    status: Literal["Planned", "In-process", "Done"]  # 状态
    updates: List[Update]           # 更新记录
    attempt: int                    # 尝试次数
    workers: List[WorkerInfo]       # 分配的 Workers

class SubTaskSpecification(BaseModel):
    """子任务规范"""
    subtask_description: str        # 描述
    input_intro: str                # 输入介绍
    exact_input: str                # 确切输入
    expected_output: str            # 期望输出
    desired_auxiliary_tools: str    # 所需工具

class WorkerInfo(BaseModel):
    """Worker 信息"""
    worker_name: str                # Worker 名称
    status: str                     # 状态
    create_type: Literal["built-in", "dynamic-built"]  # 创建类型
    description: str                # 描述
    tool_lists: List[str]           # 工具列表
    sys_prompt: str                 # 系统提示词

class WorkerResponse(BaseModel):
    """Worker 响应"""
    subtask_progress_summary: str   # 进度总结
    next_step: str                  # 下一步计划
    generated_files: dict           # 生成的文件
    task_done: bool                 # 是否完成
```

### 关键文件说明

#### main.py
- 程序入口
- 初始化配置、MCP 客户端、工具包
- 创建 MetaPlanner 实例
- 管理交互循环

#### config.py
- 配置管理
- 环境变量加载
- 参数验证
- 提供配置访问接口

#### _meta_planner.py
- MetaPlanner 核心实现
- 继承自 ReActAgent
- 实现规划-执行模式
- 管理状态持久化

#### _built_in_long_sys_prompt/
- **meta_planner_sys_prompt.md**: Meta Planner 的系统提示词
  - 定义规划角色和职责
  - 解释可用的规划工具
  - 提供规划策略指导

- **_worker_additional_sys_prompt.md**: Worker 的附加提示词
  - 定义 Worker 的角色
  - 指导任务执行方式
  - 说明响应格式要求

- **_tool_usage_rules.md**: 工具使用规则
  - 文件操作规则
  - 工作目录限制
  - 最佳实践

---

## 最佳实践

### 1. 任务设计

**好的任务描述**:
```
✅ "分析 sales_data.csv 文件，识别前3个销售趋势，并创建包含图表和建议的 Markdown 报告"

特点：
- 明确的输入（文件名）
- 具体的分析要求（前3个趋势）
- 清晰的输出格式（Markdown 报告 + 图表 + 建议）
```

**不好的任务描述**:
```
❌ "帮我看看销售情况"

问题：
- 输入不明确
- 分析目标模糊
- 输出要求不清
```

### 2. 模式选择

```python
# 简单查询 → disable 模式
"今天天气如何？"

# 中等复杂度 → dynamic 模式（推荐）
"研究特斯拉最新财报并总结关键点"

# 复杂项目 → enforced 模式
"创建一个完整的市场分析报告，包括：
1. 竞品分析
2. 市场趋势
3. SWOT 分析
4. 策略建议"
```

### 3. 工具配置

**为 Worker 选择合适的工具**:
```python
# 数据收集任务
tool_names = ["tavily_search"]

# 文件处理任务
tool_names = ["read_file", "write_file", "edit_file"]

# 复杂分析任务
tool_names = [
    "tavily_search",
    "read_file",
    "write_file",
    "execute_shell_command"
]
```

### 4. 状态管理

**定期检查状态文件**:
```bash
# 查看最新状态
ls -lt ./agent-states/run-*/

# 从最近的检查点恢复
python main.py --load_state $(ls -t ./agent-states/run-*/state-*.json | head -1)
```

### 5. 错误处理

**常见问题和解决方案**:

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| API 超时 | 任务太复杂，响应时间长 | 增加 `MODEL_MAX_TOKENS`，或分解任务 |
| Worker 卡死 | 迭代次数不足 | 增加 `AGENT_WORKER_MAX_ITERS` |
| 工具调用失败 | MCP 客户端连接问题 | 检查网络，重启 MCP 服务 |
| 状态文件过大 | 记忆过多 | 减少 `AGENT_MAX_ITERS`，定期清理状态 |

### 6. 性能优化

```python
# 1. 限制工具响应大小
TOOL_RESPONSE_BUDGET=20000  # 减少到 20KB

# 2. 使用更快的模型
CHAT_MODEL=gpt-3.5-turbo

# 3. 减少迭代次数
AGENT_MAX_ITERS=50
AGENT_WORKER_MAX_ITERS=10

# 4. 禁用流式响应（如果不需要）
MODEL_STREAM=false
```

---

## 故障排除

### 问题 1: 导入错误

```
ImportError: cannot import name 'config' from 'config'
```

**原因**: Python 内置 `config` 模块冲突

**解决方案**:
```python
# 在 main.py 中
from config import config as agent_config  # 使用别名

# 或修改 config.py 文件名
mv config.py agent_config.py
```

### 问题 2: API 密钥错误

```
ValueError: OPENAI_API_KEY environment variable is required
```

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确认 API 密钥已正确填写
3. 确保 `.env` 文件在正确的目录

```bash
# 验证环境变量
python -c "from config import config; print(config.openai_api_key[:10])"
```

### 问题 3: MCP 连接失败

```
Error: Failed to connect to MCP client
```

**解决方案**:
1. 检查 Node.js 和 npm 是否已安装
```bash
node --version
npm --version
```

2. 手动测试 MCP 包
```bash
npx -y tavily-mcp@latest
```

3. 检查网络连接和代理设置

### 问题 4: 状态恢复失败

```
Error: Invalid state file format
```

**解决方案**:
1. 验证状态文件格式
```bash
python -c "import json; print(json.load(open('state-xxx.json')))"
```

2. 使用较早的状态文件
```bash
# 列出所有状态文件
ls -lt ./agent-states/run-*/state-*.json

# 尝试较早的文件
python main.py --load_state ./agent-states/run-xxx/state-earlier.json
```

### 问题 5: 工作目录权限问题

```
PermissionError: [Errno 13] Permission denied
```

**解决方案**:
1. 检查工作目录权限
```bash
ls -ld ./meta_agent_demo_env
```

2. 使用自定义目录
```bash
# 在 .env 中设置
AGENT_OPERATION_DIR=/path/to/writable/directory
```

### 问题 6: Worker 执行超时

```
Warning: Worker exceeded max iterations
```

**解决方案**:
1. 增加 Worker 迭代次数
```bash
AGENT_WORKER_MAX_ITERS=30
```

2. 简化子任务
   - 将复杂子任务进一步分解
   - 提供更具体的指令

3. 检查是否陷入循环
   - 查看日志中的重复模式
   - 调整系统提示词

### 调试技巧

**1. 启用详细日志**:
```bash
LOG_LEVEL=DEBUG
python main.py 2>&1 | tee debug.log
```

**2. 检查内部状态**:
```python
# 在交互会话中
import json
print(json.dumps(agent.planner_notebook.model_dump(), indent=2))
```

**3. 测试单个组件**:
```python
# 测试配置加载
python -c "from config import config; print(config.to_dict())"

# 测试工具包
python -c "
from agentscope.tool import Toolkit
toolkit = Toolkit()
print(list(toolkit.tools.keys()))
"
```

**4. 使用 logfire（如果已配置）**:
```bash
ENABLE_LOGFIRE=true
python main.py

# 访问 logfire 仪表板查看详细追踪
```

---

## 高级话题

### 自定义 Worker 提示词

修改 `_built_in_long_sys_prompt/_worker_additional_sys_prompt.md`:

```markdown
# 添加领域特定知识
You are an expert in financial analysis...

# 添加输出格式要求
Always structure your analysis as:
1. Executive Summary
2. Detailed Findings
3. Recommendations

# 添加约束条件
Never make predictions without data support.
Always cite sources.
```

### 添加自定义工具

```python
# 在 main.py 中

from agentscope.tool import tool_function

@tool_function
async def custom_analysis_tool(data: str) -> dict:
    """自定义分析工具"""
    # 实现分析逻辑
    return {"result": "analysis complete"}

# 注册到 worker_toolkit
worker_toolkit.register_tool_function(custom_analysis_tool)
```

### 多 MCP 客户端集成

```python
# 添加更多 MCP 客户端
mcp_clients.append(
    StdIOStatefulClient(
        name="github_mcp",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
    )
)

mcp_clients.append(
    StdIOStatefulClient(
        name="postgres_mcp",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres"],
        env={"DATABASE_URL": os.getenv("DATABASE_URL")},
    )
)
```

### 状态分析和可视化

```python
# tools/analyze_state.py
import json
import matplotlib.pyplot as plt

def visualize_roadmap(state_file):
    """可视化任务路线图"""
    with open(state_file) as f:
        state = json.load(f)
    
    roadmap = state['planner_notebook']['roadmap']
    tasks = roadmap['decomposed_tasks']
    
    # 统计状态
    status_counts = {}
    for task in tasks:
        status = task['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # 绘图
    plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
    plt.title('Task Status Distribution')
    plt.show()

# 使用
visualize_roadmap('./agent-states/run-xxx/state-xxx.json')
```

---

## 贡献指南

### 报告问题

在 GitHub 上提交 Issue 时，请包含：
1. 错误描述
2. 重现步骤
3. 配置信息（隐藏敏感数据）
4. 相关日志
5. 系统环境（Python 版本、操作系统等）

### 代码风格

遵循 PEP 8 规范：
```bash
# 检查代码风格
pylint *.py

# 格式化代码
black *.py
```

---

## 参考资源

### 文档链接

- [AgentScope 官方文档](https://agentscope.io)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [Tavily API 文档](https://docs.tavily.com)
- [MCP 协议规范](https://modelcontextprotocol.io)

### 相关项目

- [LangChain](https://github.com/langchain-ai/langchain)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- [AgentGPT](https://github.com/reworkd/AgentGPT)

---

## 更新日志

### v1.1.0 (2025-01-31)
- ✨ 添加配置管理系统 (`config.py`)
- 📝 创建完整的配置文档 (`env.example`)
- 🔧 更新 `main.py` 使用集中配置
- 📚 创建详细的使用指南 (`AGENT_GUIDE.md`)

### v1.0.0 (2024-12-XX)
- 🎉 初始版本发布
- ✅ 实现 Meta Planner 核心功能
- ✅ 支持动态 Worker 创建
- ✅ 实现状态持久化

---

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

---

## 联系方式

- 作者: [您的名字]
- Email: [您的邮箱]
- GitHub: [项目仓库链接]

---

**最后更新**: 2025-01-31

