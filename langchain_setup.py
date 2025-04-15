# langchain_setup.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config import GOOGLE_API_KEY
# Load Gemini (from environment or your key file)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7,
    max_output_tokens=1024
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful nutrition assistant."),
    ("user", "{input}")
])

chain = prompt | llm

response = chain.invoke({"input": "Suggest a healthy dinner for someone with PCOD."})
print(response.content)
