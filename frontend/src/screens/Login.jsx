import React, { useRef, useState } from "react";
import http from "../services/httpService";

const Login = () => {
  const [mobileNumber, setMobileNumber] = useState("");
  const [activationCode, setActivationCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(undefined);
  const [time, setTime] = useState(0);
  const tick = useRef();

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

  async function requestActivationCode() {
    const data = {
      mobile_number: mobileNumber,
      request_token1: "",
    };

    try {
      const res = await http.post(
        `${baseUrl}/users/mobile/request_code`,
        data,
        config
      );
      setRes(res.data);
      setTime(res.data.data.valid_time);
      tick.current = setInterval(() => setTime((time) => time - 1), 1000);
    } catch (error) {
      console.log(error);
    }
  }
  const handleSubmit = async (e) => {
    e.preventDefault();
    await requestActivationCode();
  };

  const handleActivationCodeChange = async (e) => {
    const code = e.target.value;
    setActivationCode(code);
    if (code.length === 5) {
      const data = {
        mobile_number: mobileNumber,
        activation_token: code,
        request_token: res.data.request_token,
        is_rooted: false,
        android_id: "111222111111aab",
        adver_id: "111221aa166",
        delete_session_: true,
      };
      try {
        setLoading(true);
        const res = await http.post(
          `${baseUrl}/users/mobile/activate`,
          data,
          config
        );
        localStorage.setItem("access_token", res.data.data.access_token);
        localStorage.setItem("refresh_token", res.data.data.refresh_token);
      } catch (error) {
        console.log(error);
      }
      setLoading(false);
      location = "/";
    }
  };
  return (
    <div className="container h-100 d-flex justify-content-center align-items-center">
      {res?.message !== undefined ? (
        <div>
          <div className="mb-3">
            <label htmlFor="activationCodeInput" className="form-label">
              Code
            </label>
            <input
              type="text"
              className="form-control"
              id="activationCodeInput"
              value={activationCode}
              onChange={handleActivationCodeChange}
            />
          </div>
          <div className="d-flex justify-content-between">
            <p>Activation code sent</p>
            {time > 0 && <span ref={tick}>{time} s</span>}
          </div>
          {loading && (
            <div className="d-flex justify-content-center items-center mt-3">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="phoneNumberInput" className="form-label">
              Phone Number
            </label>
            <input
              type="text"
              className="form-control"
              id="phoneNumberInput"
              value={mobileNumber}
              onChange={(e) => setMobileNumber(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary w-100">
            Activation Code
          </button>
        </form>
      )}
    </div>
  );
};

export default Login;
