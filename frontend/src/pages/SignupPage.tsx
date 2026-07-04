import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { AuthField, AuthLayout } from "../components/AuthLayout";
import { Button } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../lib/supabase";

export function SignupPage() {
  const { session, signUp } = useAuth();
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);

  if (session) return <Navigate to="/home" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await signUp(email, password, displayName);
      // With email confirmation enabled, Supabase creates the account but
      // returns no session until the address is verified.
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        void navigate("/home", { replace: true });
      } else {
        setNeedsConfirmation(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-up failed.");
    } finally {
      setPending(false);
    }
  }

  if (needsConfirmation) {
    return (
      <AuthLayout title="Check your email">
        <p className="text-sm text-ink-soft" role="status">
          We sent a confirmation link to <span className="font-semibold text-ink">{email}</span>.
          Open it to activate your account, then log in.
        </p>
        <Link to="/login">
          <Button className="w-full">Go to log in</Button>
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Create your account">
      <form onSubmit={(event) => void submit(event)} className="space-y-4">
        <AuthField
          id="display-name"
          label="Name"
          autoComplete="name"
          required
          maxLength={60}
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
        />
        <AuthField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <AuthField
          id="password"
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error && (
          <p role="alert" className="text-sm text-taegeuk-red">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "Creating account…" : "Start free"}
        </Button>
      </form>
      <p className="text-sm text-ink-soft">
        Already practicing?{" "}
        <Link to="/login" className="font-semibold text-taegeuk-blue">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
