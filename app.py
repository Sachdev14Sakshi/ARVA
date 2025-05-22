import gradio as gr
from gradio_calendar import Calendar
import sys, os
from app.services.search_service import generate_report,perform_search

sys.path.append(os.path.join(os.path.dirname(__file__), "app", "services"))

def on_search(api_key, message, history, start_cal, end_cal):
    history = history or []
    if not api_key:
        history.append({'role':'assistant','content':'⚠️ Please provide your API key.'})
        return history, history, message, ""
    try:
        logs, retrieved, answer = perform_search(api_key, message, start_cal, end_cal)
    except Exception as e:
        history.append({'role':'assistant','content':f"Error: {e}"})
        return history, history, message, ""
    history.append({'role':'user','content':message})
    history.append({
        'role':'assistant',
        'content': f"DB:\n{retrieved or 'No entries.'}\n\nLLM:\n{answer}"
    })
    #return history, history, "", "\n".join(logs)
    return history, "\n".join(logs), ""


def on_report(start_date, end_date):
    # generate_report returns a text report
    report = generate_report(
        start_cal=start_date,
        end_cal=end_date
    )
    return report

def create_demo():
    with gr.Blocks() as demo:
        gr.Markdown("# 🐾 Animal Rescue Assistant Demo")
        with gr.Row():
            with gr.Column(scale=3):
                chat = gr.Chatbot(label="Chat", type="messages")
                user_input = gr.Textbox(placeholder="Type your query…", show_label=False)
                start_cal = Calendar(label="From Date", type="date")
                end_cal = Calendar(label="To Date", type="date")
                key_input = gr.Textbox(label="OpenAI API Key", type="password")
                debug_logs = gr.Textbox(label="Debug Logs", lines=10, interactive=False)

                history = gr.State([])  # ← holds our chat history list

            with gr.Column(scale=1):
                report_out = gr.Textbox(label="Case Report", lines=10, interactive=False)
                gen_report = gr.Button("Generate Report")

        # Wire search: on Enter, call on_search and update chat and logs
        user_input.submit(
            fn=on_search,
            inputs=[key_input,user_input, history, start_cal, end_cal],
            outputs=[chat, debug_logs, user_input]
        )

        # Wire report button
        gen_report.click(
            fn=on_report,
            inputs=[start_cal, end_cal],
            outputs=[report_out],
            preprocess=False
        )

        return demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)), share=True)
