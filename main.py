# -*- coding: utf-8 -*
"""
文件路径：
D:\Project_AI_2026
##
python 3.10
llm_other_fuzhou

测试环境：
langchain==1.2.2
langchain-community==0.4.1
langchain-core==1.2.6
langsmith==0.6.1

pyjwt==2.10.1
##
"""

# Mysql5.7安装->导入表->创建代理->运行查询->反馈答案及原始结果

import os
# from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI          # 智谱AI聊天模型
from langchain_community.utilities import SQLDatabase            # SQL数据库封装
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit  # SQL代理与工具包
# from langchain_postgres import PostgresChatMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory  # MySQL聊天记录存储
# from langchain.memory import ConversationBufferMemory
from langchain_classic.memory import ConversationBufferMemory  # 对话记忆缓冲区
# import psycopg
import pymysql  # MySQL驱动（确保已安装）

# from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.callbacks.base import BaseCallbackHandler  # 回调基类
from sqlalchemy import create_engine  # SQLAlchemy引擎
from fastapi import FastAPI  # Web框架
from pydantic import BaseModel  # 数据模型
from typing import Optional  # 可选类型

# -------------------- 1. 基础配置 --------------------
# 设置智谱AI的API密钥（环境变量方式）
os.environ["ZHIPUAI_API_KEY"] = ""
# 业务数据库连接串（MySQL）
DB_URI = "mysql+pymysql://root:000006@localhost:3306/one"
# 聊天记录数据库连接串（可复用业务库）
CHAT_HISTORY_CONN = "mysql+pymysql://root:000006@localhost:3306/one"
CHAT_HISTORY_TABLE = "chat_history"  # 聊天记录表名
# PostgreSQL连接对象（已注释掉）
# psycopg_conn = psycopg.connect(CHAT_HISTORY_CONN)

# -------------------- 2. 数据库初始化 --------------------
# 创建SQLAlchemy引擎（带连接池预ping）
engine = create_engine(DB_URI, pool_pre_ping=True)

# 自定义表/视图说明，方便LLM理解字段含义
custom_table_info = {
    "authors": (
        "A table of authors.\n"
        "- id (SERIAL PRIMARY KEY): 作者唯一编号\n"
        "- name (VARCHAR): 作者姓名\n"
        "- birth_year (INTEGER): 出生年份\n"
        "- nationality (VARCHAR): 国籍\n"
    ),
    "books": (
        "A table of books.\n"
        "- id (SERIAL PRIMARY KEY): 图书唯一编号\n"
        "- title (VARCHAR): 书名\n"
        "- author_id (INTEGER): 外键，关联authors(id)\n"
        "- genre (VARCHAR): 图书类型\n"
        "- publication_year (INTEGER): 出版年份\n"
        "- rating (DECIMAL): 评分0-10\n"
    ),
    "books_with_authors": (
        "A view combining books and authors.\n"
        "- book_id (INTEGER): 图书编号\n"
        "- title (VARCHAR): 书名\n"
        "- genre (VARCHAR): 类型\n"
        "- publication_year (INTEGER): 出版年份\n"
        "- rating (DECIMAL): 评分\n"
        "- author_name (VARCHAR): 作者姓名\n"
        "- birth_year (INTEGER): 作者出生年\n"
        "- nationality (VARCHAR): 作者国籍\n"
    ),
}

# 初始化SQLDatabase（指定表、注释、支持视图）
db = SQLDatabase(
    engine=engine,
    include_tables=list(custom_table_info.keys()),  # 只暴露这三张表
    custom_table_info=custom_table_info,  # 表字段中文说明
    view_support=True  # 允许读取视图
)

# -------------------- 3. 大模型与工具包 --------------------
# 初始化智谱AI大模型
llm = ChatZhipuAI(model="glm-4-plus", temperature=0, verbose=True)
# 创建SQL工具包（内置查表、跑SQL等工具）
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# -------------------- 4. 回调处理器（捕获原始SQL结果） --------------------
class SQLResultHandler(BaseCallbackHandler):
    def __init__(self):
        self.latest_sql_result = None  # 保存最新SQL结果
        self.sql_run_ids = set()  # 记录SQL工具运行ID

    def on_tool_start(self, serialized, input_str, **kwargs):
        # 当SQL查询工具开始时记录run_id
        tool_name = serialized.get('name', 'unknown') if isinstance(serialized, dict) else str(serialized)
        if tool_name == "sql_db_query":
            self.sql_run_ids.add(kwargs.get('run_id'))

    def on_tool_end(self, output, **kwargs):
        # 当SQL查询工具结束时保存结果
        run_id = kwargs.get('run_id')
        if run_id in self.sql_run_ids:
            self.latest_sql_result = output
            self.sql_run_ids.discard(run_id)

    def get_latest_result(self):
        # 返回最近一次SQL查询结果
        return self.latest_sql_result

# -------------------- 5. 聊天记录与记忆 --------------------
# 获取会话级别的聊天记录对象（同步）
def get_session_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string=CHAT_HISTORY_CONN,  # MySQL连接串
        table_name=CHAT_HISTORY_TABLE  # 表名
    )

# 创建对话记忆缓冲区（同步）
def get_memory(session_id: str) -> ConversationBufferMemory:
    chat_history = get_session_history(session_id)
    return ConversationBufferMemory(
        chat_memory=chat_history,
        memory_key="history",  # 模板变量名
        return_messages=True  # 返回消息对象列表
    )

# 创建带记忆的SQL代理
def create_agent_with_memory(session_id: str):
    memory = get_memory(session_id)
    return create_sql_agent(
        toolkit=toolkit,
        llm=llm,
        agent_type="tool-calling",  # 工具调用模式
        agent_executor_kwargs={"memory": memory},  # 传入记忆对象
        verbose=True  # 打印调试信息
    )

# -------------------- 6. FastAPI接口定义 --------------------
app = FastAPI(title="Text_to_SQL Agent")  # 创建FastAPI应用

# 请求/响应模型
class ChatRequest(BaseModel):
    message: str  # 用户问题
    user_id: str  # 用户ID（作为会话ID）

class ChatResponse(BaseModel):
    reply: str  # 大模型回答
    raw_sql_result: Optional[str] = None  # 原始SQL结果（可选）

# 聊天接口（同步）
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    sql_handler = SQLResultHandler()  # 实例化回调
    agent = create_agent_with_memory(request.user_id)  # 为该用户创建带记忆代理
    response = agent.invoke(
        {"input": request.message},  # 用户问题
        {"callbacks": [sql_handler]}  # 挂载回调
    )
    # 返回回答+原始SQL
    return ChatResponse(
        reply=response["output"],
        raw_sql_result=sql_handler.get_latest_result()
    )

# -------------------- 7. 启动服务 --------------------
if __name__ == "__main__":
    import uvicorn
    # 运行FastAPI：0.0.0.0:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)