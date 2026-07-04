import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { AuthField, AuthLayout } from "../components/AuthLayout";
import { Button } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export function PasswordResetPage() {
  const { resetPassword } = useAuth();

  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await resetPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the reset email.");
    } finally {
      setPending(false);
    }
  }

  if (sent) {
    return (
      <AuthLayout title="Check your email">
        <p className="text-sm text-ink-soft" role="status">
          If an account exists for{" "}
          <span className="font-semibold text-ink">{email}</span>, a password reset link is
          on its way.
        </p>
        <Link to="/login">
          <Button className="w-full">Back to log in</Button>
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Reset your password">
      <form onSubmit={(event) => void submit(event)} className="space-y-4">
        <AuthField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        {error && (
          <p role="alert" className="text-sm text-taegeuk-red">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "Sending…" : "Send reset link"}
        </Button>
      </form>
      <p className="text-sm text-ink-soft">
        Remembered it?{" "}
        <Link to="/login" className="font-semibold text-taegeuk-blue">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
