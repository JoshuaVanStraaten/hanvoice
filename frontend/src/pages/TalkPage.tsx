/** Scenario list. Starting a scenario creates a session on the backend and
 * drops the learner straight into the conversation with Minji's opener. */

import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { Button, Card, ErrorNote, Spinner } from "../components/ui";
import { useScenarios } from "../hooks/queries";
import { apiPost } from "../lib/api";
import { goalLabel } from "../lib/goals";
import type { StartConversationResponse } from "../lib/types";

export function TalkPage() {
  const scenarios = useScenarios();
  const navigate = useNavigate();

  const startConversation = useMutation({
    mutationFn: (scenarioSlug: string) =>
      apiPost<StartConversationResponse>("/conversations", { scenario_slug: scenarioSlug }),
    onSuccess: (response) => {
      // The opener's TTS audio only exists in this response — hand it to the
      // conversation page via navigation state so it can autoplay once.
      void navigate(`/talk/${response.session.id}`, {
        state: { openingAudio: response.audio_base64 },
      });
    },
  });

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Talk</h1>
        <p className="text-sm text-ink-soft">
          Real conversations, in character, in Korean. Minji is patient — promise.
        </p>
      </header>

      {startConversation.isError && (
        <ErrorNote
          error={startConversation.error}
          retry={() => startConversation.reset()}
        />
      )}

      {scenarios.isPending && <Spinner label="Loading scenarios" />}
      {scenarios.isError && (
        <ErrorNote error={scenarios.error} retry={() => void scenarios.refetch()} />
      )}

      {scenarios.isSuccess && (
        <ul className="space-y-3">
          {scenarios.data.map((scenario) => (
            <li key={scenario.id}>
              <Card className="space-y-2 border-taegeuk-red/30">
                <div className="flex items-center justify-between">
                  <h2 className="font-bold">{scenario.title}</h2>
                  <span className="text-xs text-ink-soft">
                    {"★".repeat(scenario.difficulty)} difficulty
                  </span>
                </div>
                <p className="text-sm text-ink-soft">{scenario.description}</p>
                <ul className="space-y-1 text-sm text-ink-soft">
                  {scenario.completion_goals.map((goal) => (
                    <li key={goal}>· {goalLabel(goal)}</li>
                  ))}
                </ul>
                <Button
                  variant="speak"
                  disabled={startConversation.isPending}
                  onClick={() => startConversation.mutate(scenario.slug)}
                >
                  {startConversation.isPending ? "Starting…" : "Start talking"}
                </Button>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
