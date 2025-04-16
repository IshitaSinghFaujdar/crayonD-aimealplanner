// src/pages/ResetPasswordPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const ResetPasswordPage = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleReset = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:8000/reset_password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage(data.message);
        setError("");
      } else {
        setError(data.detail || "Reset failed. Try again.");
      }
    } catch (err) {
      console.error(err);
      setError("Something went wrong.");
    }
  };

  return (
    <section>
      {[...Array(400)].map((_, i) => (
        <span key={i}></span>
      ))}
      <div className="signin">
        <div className="content">
          <h2>AI Meal Planner</h2>
          <h3>Reset Password</h3>
          <form className="form" onSubmit={handleReset}>
            <div className="inputBox">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <i>Email</i>
            </div>

            {message && <p style={{ color: "lime" }}>{message}</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <div className="inputBox">
              <input type="submit" value="Send Reset Link" />
            </div>
          </form>
          <div className="links" style={{ marginTop: "10px" }}>
            <a onClick={() => navigate("/")}>Back to Login</a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ResetPasswordPage;
