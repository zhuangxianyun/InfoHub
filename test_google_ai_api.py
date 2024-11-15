import google.generativeai as genai

# 直接使用 API 密钥进行配置
genai.configure(api_key="AIzaSyACzCVraXyyNSxly5oDPto-7mJkYRz3ahc")

# 调用生成文本的方法
response = genai.generate_text(
    model="models/text-bison-001",  # 确保使用正确的模型名称
    prompt="Explain how AI works",
    max_output_tokens=100
)


# 打印生成的文本
print(response['candidates'][0]['output'])
