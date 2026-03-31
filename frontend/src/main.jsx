import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/app.css";

// Frontend entry point mounted by Vite into the root DOM node.
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
