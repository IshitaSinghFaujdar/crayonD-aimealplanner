import React, { useState, useEffect } from "react";
import axios from "axios";
import "./AppLayout.css";
import { FiTrash2 } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
const ChatApp = () => {
  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");
  const userEmail = localStorage.getItem("user_email");
  const [chatId, setChatId] = useState("");
  const [message, setMessage] = useState("");
  const [chatLogs, setChatLogs] = useState({});
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    fetchHistory();
    startNewChat();
  }, []);

  const fetchHistory = async () => {
    const res = await axios.get(`http://localhost:8000/chat_history/${userId}`);
    const logs = res.data.history;

    const grouped = {};
    logs.forEach((log) => {
      if (!grouped[log.chat_id]) grouped[log.chat_id] = [];
      grouped[log.chat_id].push(log);
    });

    Object.keys(grouped).forEach(chatId =>
      grouped[chatId].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    );

    setChatLogs(grouped);
  };

  const startNewChat = async () => {
    const res = await axios.post("http://localhost:8000/new_chat");
    setChatId(res.data.chat_id);
    setMessages([]);
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    const res = await axios.post("http://localhost:8000/chat", {
      user_id: userId,
      user_email: userEmail,
      message,
      chat_id: chatId,
    });

    const reply = res.data.response;
    const newMsgs = [...messages, { role: "user", text: message }, { role: "ai", text: reply }];
    setMessages(newMsgs);
    setMessage("");
    fetchHistory();
  };

  const loadChat = (id) => {
    setMessages([]);
    setChatId(id);
    setTimeout(() => {
      const logs = chatLogs[id] || [];
      const sessionMsgs = logs.flatMap(log => [
        { role: "user", text: log.message },
        { role: "ai", text: log.response },
      ]);
      setMessages(sessionMsgs);
    }, 50);
  };

  const renderChatTitle = (logs) => {
    const firstMsg = logs.find(log => log.message)?.message || "New Chat";
    return firstMsg.length > 40 ? firstMsg.slice(0, 40) + "..." : firstMsg;
  };

  const deleteChat = async (chatIdToDelete) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this chat?");
    if (confirmDelete) {
      await axios.post(`http://localhost:8000/delete_chat`, {
        user_id: userId,
        chat_id: chatIdToDelete,
      });
      const updatedChatLogs = { ...chatLogs };
      delete updatedChatLogs[chatIdToDelete];
      setChatLogs(updatedChatLogs);
      if (chatId === chatIdToDelete) {
        setMessages([]);
        setChatId("");
      }
    }
  };

  const logout = () => {
    localStorage.clear();
    navigate("/"); // or navigate to login page
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>My ChatBot</h2>
        </div>

        <button className="new-chat-btn" onClick={startNewChat}>+ New Chat</button>

        <div className="chat-history">
          {Object.entries(chatLogs).reverse().map(([id, logs]) => (
            <div
              key={id}
              className={`chat-title ${chatId === id ? "active" : ""}`}
              onClick={() => loadChat(id)}
            >
              {renderChatTitle(logs)}
              <button
                className="delete-chat-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteChat(id);
                }}
              >
                  <FiTrash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        <button className="logout-btn" onClick={logout}>Logout</button>
      </div>

      <div className="chat-area">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <span>{msg.text}</span>
            </div>
          ))}
        </div>
        <div className="input-area">
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default ChatApp;
