/** The café conversation with Minji. Chat bubbles show Hangul first; a
 * single toggle reveals romanization and English. Corrections arrive on
 * Minji's messages and render as chips. Speaking is red, as always. */

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { RecordButton } from "../components/RecordButton";
import { Button, Card, ErrorNote, Spinner } from "../components/ui";
import { useActivityInvalidation, useScenarios } from "../hooks/queries";
import { useRecorder } from "../hooks/useRecorder";
import { apiGet, apiPost, apiPostForm } from "../lib/api";
import { allGoalsDone, goalStates } from "../lib/goals";
import type {
  ConversationDetail,
  ConversationMessage,
  ConversationSession,
  TurnResponse,
} from "../lib/types";

function playBase64Audio(base64: string): void {
  // Autoplay can be blocked before a user gesture; replay buttons cover that.
  void new Audio(`data:audio/mpeg;base64,${base64}`).play().catch(() => undefined);
}

function MessageBubble({
  message,
  showHints,
  audio,
}: {
  message: ConversationMessage;
  showHints: boolean;
  audio: string | undefined;
}) {
  const isUser = message.role === "user";
  return (
    <li className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] space-y-1 rounded-(--radius-card) p-3 ${
          isUser ? "bg-taegeuk-blue text-white" : "border border-line bg-paper-raised"
        }`}
      >
        {!isUser && message.contextual_correction && (
          <p className="rounded-lg bg-taegeuk-red/10 px-2 py-1 text-xs font-medium text-taegeuk-red">
            {message.contextual_correction}
          </p>
        )}
        <p className="hangul-display text-lg" lang="ko">
          {message.hangul}
        </p>
        {showHints && (message.romanized || message.english) && (
          <p className={`text-xs ${isUser ? "text-white/80" : "text-ink-soft"}`}>
            {[message.romanized, message.english].filter(Boolean).join(" · ")}
          </p>
        )}
        {!isUser && audio && (
          <button
            type="button"
            onClick={() => playBase64Audio(audio)}
            className="text-xs font-semibold text-taegeuk-red"
          >
            ▶ Play again
          </button>
        )}
      </div>
    </li>
  );
}

export function ConversationPage() {
  const { sessionId = "" } = useParams();
  const location = useLocation();
  const queryClient = useQueryClient();
  const scenarios = useScenarios();
  const recorder = useRecorder();
  const invalidateActivity = useActivityInvalidation();

  const [showHints, setShowHints] = useState(true);
  const [draft, setDraft] = useState("");
  /** TTS audio is per-response only; keep it by message id for replays. */
  const [audioByMessage, setAudioByMessage] = useState<Record<number, string>>({});
  const endOfChatRef = useRef<HTMLDivElement>(null);
  const openerHandled = useRef(false);

  const conversation = useQuery({
    queryKey: ["conversation", sessionId],
    queryFn: () => apiGet<ConversationDetail>(`/conversations/${sessionId}`),
  });

  // The opener's audio arrives via navigation state; autoplay it exactly once.
  const openingAudio =
    (location.state as { openingAudio?: string | null } | null)?.openingAudio ?? null;
  useEffect(() => {
    if (openingAudio && !openerHandled.current && conversation.isSuccess) {
      openerHandled.current = true;
      playBase64Audio(openingAudio);
    }
  }, [openingAudio, conversation.isSuccess]);

  useEffect(() => {
    endOfChatRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [conversation.data?.messages.length]);

  const takeTurn = useMutation({
    mutationFn: (input: { text?: string; audio?: Blob }) => {
      const form = new FormData();
      if (input.audio) {
        const extension = input.audio.type.includes("mp4") ? "mp4" : "webm";
        form.append("audio", input.audio, `turn.${extension}`);
      }
      if (input.text) form.append("text", input.text);
      return apiPostForm<TurnResponse>(`/conversations/${sessionId}/turns`, form);
    },
    onSuccess: (turn) => {
      queryClient.setQueryData<ConversationDetail>(["conversation", sessionId], (old) =>
        old
          ? {
              session: { ...old.session, goals_completed: turn.goals_completed },
              messages: [...old.messages, turn.user_message, turn.assistant_message],
            }
          : old,
      );
      if (turn.audio_base64) {
        setAudioByMessage((current) => ({
          ...current,
          [turn.assistant_message.id]: turn.audio_base64 as string,
        }));
        playBase64Audio(turn.audio_base64);
      }
      setDraft("");
      invalidateActivity();
    },
  });

  const complete = useMutation({
    mutationFn: () => apiPost<ConversationSession>(`/conversations/${sessionId}/complete`),
    onSuccess: (session) => {
      queryClient.setQueryData<ConversationDetail>(["conversation", sessionId], (old) =>
        old ? { ...old, session } : old,
      );
      invalidateActivity();
    },
  });

  async function handleMicPress() {
    if (recorder.isRecording) {
      const audio = await recorder.stop();
      if (audio) takeTurn.mutate({ audio });
      return;
    }
    await recorder.start();
  }

  function handleTextSubmit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (text) takeTurn.mutate({ text });
  }

  if (conversation.isPending) return <Spinner label="Loading conversation" />;
  if (conversation.isError) {
    return (
      <ErrorNote error={conversation.error} retry={() => void conversation.refetch()} />
    );
  }

  const { session, messages } = conversation.data;
  const openerId = messages.find((m) => m.role === "assistant")?.id;
  const scenario = scenarios.data?.find((item) => item.id === session.scenario_id);
  const goals = goalStates(scenario?.completion_goals ?? [], session.goals_completed);
  const readyToWrapUp = allGoalsDone(goals) && session.status === "active";
  const isCompleted = session.status !== "active";
  const busy = takeTurn.isPending || complete.isPending;

  return (
    <div className="flex min-h-[calc(100dvh-9.5rem)] flex-col gap-4">
      <header className="flex items-center justify-between">
        <div>
          <Link to="/talk" className="text-sm font-semibold text-taegeuk-blue">
            ← Scenarios
          </Link>
          <h1 className="text-xl font-bold">{scenario?.title ?? "Conversation"}</h1>
        </div>
        <button
          type="button"
          onClick={() => setShowHints((value) => !value)}
          className="text-sm font-semibold text-taegeuk-blue"
          aria-pressed={showHints}
        >
          {showHints ? "Hide hints" : "Show hints"}
        </button>
      </header>

      {/* Goal checklist */}
      {goals.length > 0 && (
        <div className="flex flex-wrap gap-1.5" aria-label="Scenario goals">
          {goals.map((state) => (
            <span
              key={state.goal}
              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                state.done ? "bg-jade/10 text-jade" : "bg-line text-ink-soft"
              }`}
            >
              {state.done ? "✓ " : ""}
              {state.goal}
            </span>
          ))}
        </div>
      )}

      {/* Chat */}
      <ul className="flex-1 space-y-3" aria-live="polite">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            showHints={showHints}
            audio={
              audioByMessage[message.id] ??
              (message.id === openerId ? (openingAudio ?? undefined) : undefined)
            }
          />
        ))}
        {takeTurn.isPending && <Spinner label="Minji is replying" />}
        <div ref={endOfChatRef} />
      </ul>

      {takeTurn.isError && (
        <ErrorNote error={takeTurn.error} retry={() => takeTurn.reset()} />
      )}
      {recorder.error && (
        <p role="alert" className="text-sm text-taegeuk-red">
          {recorder.error}
        </p>
      )}

      {/* Completed state */}
      {isCompleted && (
        <Card className="space-y-2 border-jade/40 text-center">
          <p className="hangul-display text-2xl text-jade" lang="ko">
            잘했어요!
          </p>
          <p className="text-sm text-ink-soft">
            Scenario complete — you ordered like a local.
          </p>
          <Link to="/talk">
            <Button>Back to scenarios</Button>
          </Link>
        </Card>
      )}

      {/* Wrap-up prompt once every goal is checked */}
      {readyToWrapUp && !isCompleted && (
        <Card className="flex items-center justify-between gap-3 border-jade/40">
          <p className="text-sm">All goals reached — wrap up when you&apos;re ready.</p>
          <Button onClick={() => complete.mutate()} disabled={busy}>
            Finish
          </Button>
        </Card>
      )}

      {/* Input row */}
      {!isCompleted && (
        <form
          onSubmit={handleTextSubmit}
          className="sticky bottom-20 flex items-center gap-2 rounded-full border border-line bg-paper-raised p-1.5"
        >
          <RecordButton
            isRecording={recorder.isRecording}
            onPress={() => void handleMicPress()}
            disabled={busy}
          />
          <label htmlFor="turn-text" className="sr-only">
            Type your reply in Korean
          </label>
          <input
            id="turn-text"
            value={draft}
            maxLength={500}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={recorder.isRecording ? "Listening…" : "…or type in Korean"}
            disabled={busy || recorder.isRecording}
            className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none placeholder:text-ink-soft/70"
          />
          <Button type="submit" variant="quiet" disabled={busy || !draft.trim()}>
            Send
          </Button>
        </form>
      )}
    </div>
  );
}
