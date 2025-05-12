import openai

openai.api_key="sk-proj-MiesbTrH2Eyk09D37GFIT3BlbkFJu29iqkS6JTzbRMoMOksB"

response = openai.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "system", "content": "あなたは進路相談をする先生です。情報科学部の大学生に対してアドバイスをします。"},
    {"role": "user", "content": "情報科学部を卒業した後の進路で悩んでいます。大学で卒業するのと、大学院で卒業するのはどちらがいいですか？"}
  ]
)
print(response.choices[0].message.content)