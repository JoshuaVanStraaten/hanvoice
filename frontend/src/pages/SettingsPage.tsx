import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { AuthField } from "../components/AuthLayout";
import { Button, Card, ErrorNote, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useMe, useUpdateProfile } from "../hooks/queries";

function ProfileForm({
  initialName,
  initialLanguage,
}: {
  initialName: string;
  initialLanguage: string;
}) {
  const [displayName, setDisplayName] = useState(initialName);
  const [nativeLanguage, setNativeLanguage] = useState(initialLanguage);
  const update = useUpdateProfile();

  function submit(event: FormEvent) {
    event.preventDefault();
    update.mutate({ display_name: displayName, native_language: nativeLanguage });
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <AuthField
        id="display-name"
        label="Name"
        required
        maxLength={60}
        value={displayName}
        onChange={(event) => setDisplayName(event.target.value)}
      />
      <AuthField
        id="native-language"
        label="Native language"
        maxLength={40}
        value={nativeLanguage}
        onChange={(event) => setNativeLanguage(event.target.value)}
      />
      {update.isError && <ErrorNote error={update.error} retry={() => update.reset()} />}
      <div className="flex items-center gap-3">
        <Button type="submit" disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save changes"}
        </Button>
        {update.isSuccess && (
          <span className="text-sm font-semibold text-jade" role="status">
            Saved
          </span>
        )}
      </div>
    </form>
  );
}

export function SettingsPage() {
  const me = useMe();
  const { signOut } = useAuth();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Profile</h1>
      </header>

      {me.isPending && <Spinner label="Loading profile" />}
      {me.isError && <ErrorNote error={me.error} retry={() => void me.refetch()} />}

      {me.isSuccess && (
        <>
          <Card className="space-y-4">
            <ProfileForm
              initialName={me.data.profile.display_name}
              initialLanguage={me.data.profile.native_language}
            />
          </Card>

          <Card className="flex items-center justify-between">
            <div>
              <p className="font-bold">
                {me.data.plan.name}
                {me.data.has_founder_pass && (
                  <span className="ml-2 rounded-full bg-taegeuk-blue px-2.5 py-0.5 text-[11px] font-semibold text-white">
                    Founder
                  </span>
                )}
              </p>
              <p className="text-sm text-ink-soft">Your current plan</p>
            </div>
            <Link to="/subscription" className="text-sm font-semibold text-taegeuk-blue">
              Manage
            </Link>
          </Card>
        </>
      )}

      <Card>
        <Button variant="quiet" onClick={() => void signOut()}>
          Sign out
        </Button>
      </Card>
    </div>
  );
}
