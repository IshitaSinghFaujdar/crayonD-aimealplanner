import React from 'react';
import ReactDOM from 'react-dom/client'; // Import from 'react-dom/client' (React 18)
import './index.css'; // Your styles
import App from './App.jsx';

const root = ReactDOM.createRoot(document.getElementById('root')); // Create root
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
