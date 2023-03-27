import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import jwt_decode from "jwt-decode";
import http from "../services/httpService";

const baseUrl = "https://apilab.learnit.ir/v1/index.php";
const config = {
  headers: {
    clientid: "JuJdAzSR",
    clientversion: "38",
    devicename: "Google+Android+SDK+built+for+x86",
    devicesdkversion: "29",
    "Content-Type": "application/json",
    Apikey: "PpAE(&9bskhHM8xC5W26t4GqDYIf@$eBSLN%Q*+v",
  },
};

export function PrivateRoute() {
  const access_token = localStorage.getItem("access_token");
  const refresh_token = localStorage.getItem("refresh_token");
  let currentUser;
  try {
    currentUser = jwt_decode(access_token);
  } catch (error) {
    console.log(error);
  }

  if (!currentUser) {
    console.log(access_token);
    return <Navigate to={"/login"} />;
  }

  const currentDate = new Date();
  const now = currentDate.getTime() / 1000;
  const expire = currentUser.exp;
  if (expire < now) {
    const data = { refresh_token };
    try {
      const res = http.post(
        `${baseUrl}/users/mobile/refresh_token`,
        data,
        config
      );
      localStorage.setItem("access_token", res.data.data.access_token);
    } catch (error) {
      console.log(error);
    }
  }
  return <Outlet />;
}
