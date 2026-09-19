import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";

export function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("roshni@linguini.app");
  const [password, setPassword] = useState("noodles");

  return (
    <div className="stack">
      <div className="center-text stack-2" style={{ alignItems: "center" }}>
        <img
          className="mascot"
          src="/linguini-logo.png"
          width={120}
          height={120}
          alt="Linguini mascot"
        />
        <h1>Welcome back</h1>
        <p className="muted">Your café session is waiting where you left it.</p>
      </div>
      <form
        className="stack"
        onSubmit={(event) => {
          event.preventDefault();
          navigate("/home");
        }}
      >
        <div className="field">
          <label className="field__label" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            className="input"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="field">
          <label className="field__label" htmlFor="login-password">
            Password
          </label>
          <input
            id="login-password"
            className="input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <Button block type="submit">
          Log in
        </Button>
      </form>
      
      <p className="small muted center-text">
        New here?{" "}
        <button type="button" className="btn btn--quiet" onClick={() => navigate("/onboarding")}>
          Create an account
        </button>
      </p>
    </div>
  );
}
