# Text2SQL Agent - 智能SQL查询助手
基于LangChain V1.0和智谱AI (GLM-4) 的自然语言转SQL查询系统，支持多表关联查询、对话历史记忆和 FastAPI 接口服务。

## 🌟 核心功能
- **自然语言转 SQL**：使用 GLM-4-plus 大模型理解用户意图，自动生成并执行 SQL
- **多表智能关联**：支持 authors、books 等多表查询，内置表结构注释优化查询准确性
- **对话历史记忆**：基于 MySQL 持久化存储多轮对话上下文，支持长会话连贯交互
- **原始结果返回**：同时返回 AI 解释和业务原始数据，便于二次开发
- **RESTful API**：基于 FastAPI 提供标准 HTTP 接口，易于集成到前端应用

## 🏗️ 技术栈
- **大语言模型**：智谱 AI (GLM-4-plus)
- **框架**：LangChain V1.0 + FastAPI
- **数据库**：MySQL 5.7+（业务数据 + 聊天记录存储）
- **驱动**：PyMySQL + SQLAlchemy
- **Python**：3.10+

## 🚀 快速开始
- **安装 Python 库**：执行 `pip install -r requirements.txt`（需 Python 3.10+）
- **运行后端服务**：启动 `main.py`（FastAPI，端口 **8000**）
- **运行前端服务**：启动 `gradio_frontend.py`（Gradio，端口 **7860**）
