// src/pages/SignupPage.jsx
import React, { useState } from "react";
import axios from "axios";

const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const handleSignup = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post("http://127.0.0.1:8000/signup", {
        email,
        password,
      });
      console.log("Signup success:", response.data);
      // Redirect to login or chat page
    } catch (err) {
      setError("Signup failed. Please try again.");
      console.error(err);
    }
  };

  return (
    <section>
      <div className="signin">
        <div className="content">
          <h2>AI Meal Planner</h2>
          <h3>Sign Up</h3>
          <form className="form" onSubmit={handleSignup}>
            <div className="inputBox">
              <input
                type="email"
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
            {error && <p style={{ color: "red" }}>{error}</p>}
            <div className="inputBox">
              <input type="submit" value="Sign Up" />
            </div>
          </form>
        </div>
      </div>
    </section>
  );
};

export default SignupPage;
