# gradio_frontend_6.py
import gradio as gr
import requests
import json

API_URL = "http://localhost:8000/chat"

def chat_fn(message, user_id):
    if not message.strip():
        return "❗ 请输入问题", ""
    payload = {"message": message, "user_id": user_id or "demo_user"}
    try:
        r = requests.post(API_URL, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["reply"], data.get("raw_sql_result") or ""
    except Exception as e:
        return f"❌ 接口异常：{e}", ""

# ---------- 兼容 Gradio 6.x 的界面 ----------
with gr.Blocks(title="Text2SQL 书店助手") as demo:
    gr.Markdown("## 📚 书店数据库智能查询助手")
    # gr.Markdown("自然语言 → SQL → 结果")

    with gr.Row():
        with gr.Column():
            user_id = gr.Textbox(label="会话 ID", value="demo_user", max_lines=1)
            message = gr.Textbox(label="输入问题", placeholder="例：余华一共写了多少本书？", lines=3)
            with gr.Row():
                ask_btn = gr.Button("🔍 查询", variant="primary")
                clear_btn = gr.Button("🗑️ 清除")
        with gr.Column():
            reply = gr.Textbox(label="💡 查询结果", lines=5, max_lines=10)
            raw_sql = gr.Code(label="原始 SQL 返回", language="json")

    gr.Examples(
        examples=[
            ["余华有几本书", "demo_user"],
            ["统计每个国家都有几个作者", "demo_user"],
            ["科幻小说的平均评分是多少", "demo_user"],
        ],
        inputs=[message, user_id],
        outputs=[reply, raw_sql],
        fn=chat_fn,
        cache_examples=False,
    )

    ask_btn.click(chat_fn, inputs=[message, user_id], outputs=[reply, raw_sql])
    clear_btn.click(lambda: ("", "", ""), outputs=[message, reply, raw_sql])

if __name__ == "__main__":
    # 主题 & css 放到 launch() 里即可
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        theme=gr.themes.Soft(),   # 内置主题
        css="""
        .gradio-container{font-family:HarmonyOS Sans SC,Roboto,Helvetica,Arial;}
        button{border-radius:8px !important;}
        """,
    )