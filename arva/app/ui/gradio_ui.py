import gradio as gr
from search_service import generate_report
from search_service import perform_search


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
    return history, history, "", "\n".join(logs)


def on_report(evt: gr.EventData, start_date, end_date):
    return generate_report(start_cal=start_date, end_cal=end_date)

def create_demo():
    with gr.Blocks() as demo:
        gr.Markdown("# 🐾 Animal Rescue Assistant Demo")
        with gr.Row():
            with gr.Column(scale=3):
                chat = gr.Chatbot(label="Chat")
                user_input = gr.Textbox(placeholder="Type your query and press Enter…", show_label=False)
                start_cal = gr.Calendar(label="From Date", type="date")
                end_cal = gr.Calendar(label="To Date", type="date")
                key_input = gr.Textbox(label="OpenAI API Key", type="password")
                debug_logs = gr.Textbox(label="Debug Logs", lines=10, interactive=False)

            with gr.Column(scale=1):
                report_out = gr.Textbox(label="Case Report", lines=10, interactive=False)
                gen_report = gr.Button("Generate Report")

        gen_report.click(
            fn=on_report,
            inputs=[start_cal, end_cal],
            outputs=[report_out]
        )
        # Wire search: on Enter, call on_search and update chat and logs
        user_input.submit(
            fn=on_search,
            inputs=[key_input, user_input, start_cal, end_cal],
            outputs=[chat, debug_logs]
        )

        # Wire report button


        return demo
demo = create_demo()
