# AgentTracks - AI Agent框架学习项目

🤖 **一个专门用于学习和比较主流AI Agent框架的实战项目**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Learning](https://img.shields.io/badge/Learning-Project-orange.svg)](#)

## 🎯 项目目标

这个项目的目的是帮助开发者**学习和理解**当前主流的AI Agent框架，通过实际代码示例掌握每个框架的：

- ✨ **核心概念**和设计理念
- 🔧 **API使用**和开发模式  
- 🛠️ **工具集成**和扩展能力
- 🔄 **工作流编排**和状态管理
- 📊 **框架对比**和选型参考

## 📚 涵盖的框架

| 框架 | 学习重点 | 示例数量 | 难度 |
|------|----------|----------|------|
| **LangGraph** | 工作流编排、状态管理 | 🔄 完整项目 | ⭐⭐⭐⭐ |
| **Pydantic AI** | 类型安全、工具装饰器 | 📝 15+ 示例 | ⭐⭐⭐ |
| **Agno** | 多智能体协作 | 🤝 3个示例 | ⭐⭐⭐ |
| **OpenAI Agents SDK** | 官方框架、快速开始 | 🚀 2个示例 | ⭐⭐ |
| **PocketFlow** | 轻量级工作流 | 🏗️ RAG示例 | ⭐⭐⭐ |

## 🏗️ 项目结构

```
AgentTracks/
├── langgraph/llamabot/          # 🔄 LangGraph完整实现
│   ├── app.py                   # FastAPI + WebSocket服务
│   ├── agents/                  # 各种Agent模式实现
│   │   ├── base_agent.py        # 基础Agent类
│   │   ├── react_agent/         # ReAct模式Agent
│   │   └── write_html_agent/    # 顺序工作流Agent
│   └── tests/                   # 完整测试套件
├── pydantic_ai/                 # 📝 Pydantic AI学习示例
│   ├── 01_agent_demo.py        # 基础Agent使用
│   ├── 01.1_agent_run.py        # Agent运行方式
│   ├── 02_tools_decorator.py    # 工具装饰器
│   ├── 02.4_multi_agent.py      # 多Agent协作
│   └── examples/                # 实际应用案例
├── agno/                        # 🤝 Agno框架学习
│   ├── 0.1_research_agent.py    # 研究Agent
│   └── 0.2_teams.py            # 团队协作
├── openai_agents_sdk/           # 🚀 OpenAI官方SDK
│   ├── 01_hello_chatbot.py      # 聊天机器人
│   └── 02_first_agent.py        # 第一个Agent
├── pocketflow/                  # 🏗️ PocketFlow工作流
│   └── simple_rag/              # RAG实现示例
└── chainlit/                    # 🎨 Chainlit UI界面
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone https://github.com/Tendo33/AgentTracks.git
cd AgentTracks

# 安装uv包管理器
pip install uv

# 安装依赖
uv sync
```

### 2. 配置API密钥
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加OpenAI API密钥
OPENAI_API_KEY="your_openai_api_key"
```

### 3. 开始学习

#### 🔰 **新手建议学习路径：**

1. **OpenAI Agents SDK** - 最简单入门
   ```bash
   cd openai_agents_sdk
   python 01_hello_chatbot.py
   ```

2. **Pydantic AI** - 类型安全和工具使用
   ```bash
   cd pydantic_ai
   python 01_agent_demo.py
   ```

3. **Agno** - 多智能体概念
   ```bash
   cd agno
   python 0.0_demo.py
   ```

4. **PocketFlow** - 工作流基础
   ```bash
   cd pocketflow/simple_rag
   python main.py
   ```

5. **LangGraph** - 完整项目实践
   ```bash
   cd langgraph/llamabot
   uvicorn app:app --reload
   ```

## 📖 学习指南

### LangGraph学习要点
- **StateGraph**: 状态管理和节点编排
- **工作流模式**: ReAct、顺序、条件分支
- **检查点**: 持久化和会话管理
- **工具集成**: ToolNode和工具条件
- **流式处理**: 实时响应和事件流

### Pydantic AI学习要点
- **类型安全**: 强类型Agent定义
- **工具装饰器**: `@tool`使用模式
- **流式响应**: 实时输出处理
- **多Agent**: Agent间协作模式
- **依赖注入**: Agent依赖管理

### Agno学习要点
- **Agent概念**: 基础Agent构建
- **团队协作**: 多Agent通信
- **研究模式**: 信息搜集和处理
- **工具使用**: 外部工具集成

### OpenAI Agents SDK学习要点
- **官方标准**: OpenAI设计理念
- **快速开发**: 简洁的API设计
- **工具集成**: Function calling
- **会话管理**: 对话状态维护

### PocketFlow学习要点
- **轻量级**: 简单易用的工作流
- **节点模式**: 分步骤处理
- **RAG实现**: 检索增强生成
- **状态传递**: 节点间数据流

## 🛠️ 实践练习

### 练习1: 创建自己的Agent
选择任意框架，实现一个天气查询Agent：
```python
# 示例要求
- 获取用户位置
- 查询天气信息
- 提供穿衣建议
- 处理错误情况
```

### 练习2: 多Agent协作
使用支持多Agent的框架，实现：
```python
# 协作场景
- 研究Agent: 搜集信息
- 分析Agent: 处理数据  
- 决策Agent: 给出建议
```

### 练习3: 工具开发
为任意框架开发新工具：
```python
# 工具示例
- 文件读写工具
- API调用工具
- 数据库操作工具
- 计算器工具
```

## 🔍 框架对比

| 特性 | LangGraph | Pydantic AI | Agno | OpenAI SDK | PocketFlow |
|------|-----------|-------------|------|-------------|------------|
| **学习曲线** | 陡峭 | 平缓 | 中等 | 平缓 | 平缓 |
| **类型安全** | 中等 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **工具集成** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **多Agent** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **工作流** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **生产就绪** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 📚 扩展学习

### 官方文档
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [Pydantic AI文档](https://ai.pydantic.dev/)
- [Agno文档](https://github.com/agno-ai/agno)
- [OpenAI Agents SDK](https://platform.openai.com/docs/agents)
- [PocketFlow文档](https://github.com/pocketflow/pocketflow)

### 推荐资源
- **视频教程**: 各框架官方YouTube频道
- **博客文章**: Medium、Dev.to上的实践分享
- **社区讨论**: Reddit、Discord相关社区
- **实践项目**: GitHub上的开源项目

## 🧪 测试和验证

每个框架都包含相应的测试代码：

```bash
# LangGraph完整测试
cd langgraph/llamabot
python run_tests.py all

# 单独运行示例测试
cd pydantic_ai
python 01_agent_demo.py

# 验证安装和依赖
python -c "import langgraph, pydantic_ai, agno; print('All frameworks installed successfully')"
```

## 🤝 贡献和学习

### 分享你的学习心得
- 提交PR添加新的学习示例
- 完善现有代码注释
- 补充框架对比文档
- 分享你的学习笔记

### 学习社区
- 提出问题和疑惑
- 分享学习经验
- 讨论最佳实践
- 探索新的框架特性

## 📝 学习笔记模板

### 框架学习记录
```markdown
## [框架名称] 学习笔记

### 核心概念
- 概念1: 说明
- 概念2: 说明

### 代码模式
```python
# 关键代码模式
```

### 学习心得
1. 优点
2. 缺点
3. 适用场景

### 练习成果
- 完成的练习
- 遇到的问题
- 解决方案
```

## 📈 进阶学习路径

### 第一阶段: 基础概念 (1-2周)
- 理解Agent基本概念
- 掌握1-2个简单框架
- 完成基础练习

### 第二阶段: 框架深入 (2-3周)  
- 学习复杂框架特性
- 实现多Agent系统
- 集成外部工具

### 第三阶段: 项目实践 (3-4周)
- 构建完整应用
- 性能优化
- 部署和监控

---

**🎯 学习目标**: 通过这个项目，你将掌握主流AI Agent框架的使用方法，理解不同框架的设计理念，具备根据项目需求选择合适框架的能力。

**💡 学习建议**: 建议按照难度顺序学习，每个框架都要动手实践，对比它们的异同点，找到最适合自己项目需求的框架。

**🔄 持续更新**: AI Agent领域发展迅速，项目会持续更新新的框架和示例，欢迎关注和贡献！