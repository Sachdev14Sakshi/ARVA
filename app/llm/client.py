from openai import OpenAI

def call_llm(api_key: str, system: str, user: str) -> str:
    r2 = OpenAI(api_key=api_key).chat.completions.create(
        model='gpt-4o-mini', temperature=0.0, max_tokens=256,
        messages=[
            {'role' :'system' ,'content' :system},
            {'role' :'user' ,'content' :user}
        ]
    )
    answer = r2.choices[0].message.content.strip()
    return answer
