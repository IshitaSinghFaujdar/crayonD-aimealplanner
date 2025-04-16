# 🍱 AI-Powered Meal Planning Chatbot

This is a full-stack AI-powered food and meal planning chatbot that helps users plan meals, find quick recipes, suggest healthy substitutes, and understand the nutritional impact of ingredients. It uses Gemini for smart embeddings and Supabase for long-term memory and authentication.

---

## 🔧 Tech Stack

- **Frontend**: React (Vite)
- **Backend**: Python (FastAPI-style modular logic)
- **Database**: Supabase (PostgreSQL + Auth)
- **LLM & Embeddings**: Gemini Pro + Embeddings
- **Other APIs**: Spoonacular, OpenFoodFacts, Edamam, Serper

---

## 🧠 What the Chatbot Can Do

The chatbot has 4 major tools:

1. **🗓️ Weekly Meal Planner**  
   Plans your week of meals based on preferences, budget, time, and goals.

2. **⏱️ Quick Meal Finder**  
   Helps you find real-time recipe suggestions with filters (diet, time, ingredients, cost).

3. **♻️ Substitute Finder**  
   Suggests healthy alternatives for ingredients (e.g., dairy-free, gluten-free swaps).

4. **❤️ Food + Health Explainer**  
   Explains how certain meals or ingredients impact health (PCOD, diabetes, etc.).

---

## ⚙️ Features

- ✅ Signup / Login / Reset Password
- ✅ Context-aware chat (short and long-term memory)
- ✅ Recipe Liking & Recall
- ✅ Long-term preference matching using Gemini embeddings
- ✅ New Chat / Delete Chat functionality
- ✅ Real API integrations
- ✅ Organized modular backend
- ✅ Semantic preference detection via chat

---

## ⚠️ Known Limitations

- ❌ Not using LangChain agents yet.
- 🐢 Responses can be **slow (40–60s)** due to real-time API calls + LLM processing.
- 💬 Sometimes lacks full memory management (working on trimming old context better).
- 🔐 Make sure you do **NOT push `.env`** or hardcode secrets in public repos!

---

## 📁 Folder Structure

```bash
mealplanner/
│
├── frontend/               # React frontend (Vite + Tailwind)
│   └── package.json        # Start frontend: npm install && npm run dev
│
├── *.py                    # Backend scripts (chat, tools, auth, main)
├── .env                    # 🔒 API keys & credentials (ignored by Git)
└── requirements.txt        # Python dependencies


# In root directory
python -m venv venv
venv\Scripts\activate        # or source venv/bin/activate on Linux/Mac
pip install -r requirements.txt

# Start backend
python main.py


cd frontend
npm install
npm run dev


## Future Plans
⏳ Migrate to LangChain for better tool routing

🚀 Improve response speed using async parallel calls

🧠 Better memory compression / summarization for long chats

📱 Mobile-responsive UI + dark mode