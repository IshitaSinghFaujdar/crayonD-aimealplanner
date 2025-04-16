// LoginPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./LoginPage.css";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const section = document.querySelector("section");
    for (let i = 0; i < 400; i++) {
      const span = document.createElement("span");
      section.insertBefore(span, section.firstChild);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (data.user_id) {
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("user_email", data.email);
        navigate("/chat"); // Redirect to chat page
      } else {
        alert("Login failed. Please check your credentials.");
      }
    } catch (error) {
      console.error("Error during login:", error);
      alert("An error occurred during login. Please try again later.");
    }
  };

  return (
    <section>
      <div className="signin">
        <div className="content">
          <h2>AI Meal Planner</h2>
          <h3>Sign In</h3>
          <form className="form" onSubmit={handleLogin}>
            <div className="inputBox">
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <i>Email</i>
            </div>
            <div className="inputBox">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <i>Password</i>
            </div>
            <div className="links">
            <a onClick={() => navigate("/reset")} style={{ cursor: "pointer" }}>
                Forgot Password?
              </a>
            <a onClick={() => navigate("/signup")}>Signup</a>
            </div>

            <div className="inputBox">
              <input type="submit" value="Login" />
            </div>
          </form>
        </div>
      </div>
    </section>
  );
};

export default LoginPage;
