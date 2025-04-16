from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase_client import get_chat_history, delete_chat, insert_chat_log
from auth import signup, login, reset_password, logout
from main import start_new_chat, process_input
import uuid
import asyncio
import nest_asyncio

nest_asyncio.apply()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AuthRequest(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    user_id: str
    user_email: str
    message: str
    chat_id: str

class DeleteChatRequest(BaseModel):
    user_id: str
    chat_id: str

# Routes
@app.post("/signup")
def signup_user(req: AuthRequest):
    signup(req.email, req.password)
    return {"message": "Signup attempted. Check console for details."}

@app.post("/login")
def login_user(req: AuthRequest):
    user_id = login(req.email, req.password)
    if user_id:
        return {"user_id": user_id, "email": req.email}
    return {"error": "Login failed."}

@app.post("/reset_password")
def reset(req: AuthRequest):
    reset_password(req.email)
    return {"message": "Password reset email sent."}

@app.post("/logout")
def log_out():
    logout()
    return {"message": "Logged out."}

@app.post("/new_chat")
def new_chat():
    chat_id = start_new_chat()
    return {"chat_id": chat_id}

@app.post("/chat")
def chat(req: ChatMessage):
    response = asyncio.get_event_loop().run_until_complete(
        process_input(req.message, user_email=req.user_email, user_id=req.user_id)
    )
    return {"response": response}

@app.get("/chat_history/{user_id}")
def history(user_id: str):
    return {"history": get_chat_history(user_id)}

@app.post("/delete_chat")
def delete(req: DeleteChatRequest):
    delete_chat(req.user_id, req.chat_id)
    return {"message": "Chat deleted"}
