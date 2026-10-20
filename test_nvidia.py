from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "user", "content": "Reply with only: Hello!"}
    ],
    temperature=0.2,
    max_tokens=200
)

print(response.choices[0].message.content)