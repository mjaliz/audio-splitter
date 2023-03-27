import React, { Component } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { PrivateRoute } from "./components/PrivateRoutes";
import HomeScreen from "./screens/HomeScreen";

import Login from "./screens/Login";

class App extends Component {
  render() {
    return (
      <div className="vh-100">
        <Router>
          <Routes>
            <Route element={<PrivateRoute />}>
              <Route path="/" element={<HomeScreen />} />
            </Route>
            <Route path="/login" element={<Login />} />
          </Routes>
        </Router>
      </div>
    );
  }
}

export default App;
