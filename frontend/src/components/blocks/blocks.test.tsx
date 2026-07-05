import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExplainBlock } from "./ExplainBlock";
import { QuizBlock } from "./QuizBlock";
import { WriteBlock } from "./WriteBlock";
import { apiGet } from "../../lib/api";
import type { ExplainPayload, QuizPayload } from "../../lib/types";

vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiGet: vi.fn(),
}));

const playSpy = vi.fn(() => Promise.resolve());
vi.stubGlobal(
  "Audio",
  class {
    constructor(public src: string) {}
    play = playSpy;
  },
);

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
  playSpy.mockClear();
});

function withQueryClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>;
}

const explainPayload: ExplainPayload = {
  segments: [
    { type: "text", body: "Hangul is an **alphabet**, not pictographs." },
    { type: "chars", items: [{ ko: "ㅏ", label: "a", note: "open 'ah'" }] },
    { type: "example", items: [{ ko: "가요", roman: "gayo", en: "I go" }] },
    { type: "tip", body: "Letters stack into blocks." },
  ],
};

describe("ExplainBlock", () => {
  it("renders every segment kind and continues", () => {
    const onContinue = vi.fn();
    render(
      <ExplainBlock
        blockId={7}
        payload={explainPayload}
        completing={false}
        onContinue={onContinue}
      />,
    );

    expect(screen.getByText("alphabet")).toBeInTheDocument(); // **bold** parsed
    expect(screen.getByText("ㅏ")).toBeInTheDocument();
    expect(screen.getByText("가요")).toBeInTheDocument();
    expect(screen.getByText("gayo · I go")).toBeInTheDocument();
    expect(screen.getByText(/Letters stack into blocks/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(onContinue).toHaveBeenCalledTimes(1);
  });

  it("plays carrier audio for a char card, fetching once", async () => {
    vi.mocked(apiGet).mockResolvedValue({ audio_base64: "bXAz" });
    render(
      <ExplainBlock
        blockId={7}
        payload={explainPayload}
        completing={false}
        onContinue={vi.fn()}
      />,
    );

    const button = screen.getByRole("button", { name: "Hear ㅏ (sounds like 아)" });
    fireEvent.click(button);
    await waitFor(() => expect(playSpy).toHaveBeenCalledTimes(1));
    expect(apiGet).toHaveBeenCalledWith(
      `/lessons/blocks/7/audio?text=${encodeURIComponent("아")}`,
    );

    fireEvent.click(button);
    await waitFor(() => expect(playSpy).toHaveBeenCalledTimes(2));
    expect(apiGet).toHaveBeenCalledTimes(1); // cached after first fetch
  });

  it("offers audio on example rows", () => {
    render(
      <ExplainBlock
        blockId={7}
        payload={explainPayload}
        completing={false}
        onContinue={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Hear 가요" })).toBeInTheDocument();
  });
});

describe("WriteBlock audio", () => {
  it("lets the learner hear the target before writing it", async () => {
    vi.mocked(apiGet).mockResolvedValue({ audio_base64: "bXAz" });
    render(
      withQueryClient(
        <WriteBlock
          blockId={9}
          payload={{ target: "ㄱ", hint: "One stroke." }}
          onPassed={vi.fn()}
          onContinue={vi.fn()}
        />,
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Hear ㄱ (sounds like 가)" }));
    await waitFor(() => expect(playSpy).toHaveBeenCalledTimes(1));
    expect(apiGet).toHaveBeenCalledWith(
      `/lessons/blocks/9/audio?text=${encodeURIComponent("가")}`,
    );
  });
});

const quizPayload: QuizPayload = {
  question: "Hangul is…",
  choices: ["Thousands of pictographs", "An alphabet in syllable blocks"],
  answer: 1,
  explanation: "24 letters that stack into blocks.",
};

describe("QuizBlock", () => {
  it("keeps Continue hidden until the right answer, then continues", () => {
    const onCorrectContinue = vi.fn();
    render(
      <QuizBlock
        payload={quizPayload}
        completing={false}
        onCorrectContinue={onCorrectContinue}
      />,
    );

    expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("option", { name: "Thousands of pictographs" }));
    expect(screen.getByText(/Not quite/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("option", { name: "An alphabet in syllable blocks" }));
    expect(screen.getByText(/Correct/)).toBeInTheDocument();
    expect(screen.getByText("24 letters that stack into blocks.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(onCorrectContinue).toHaveBeenCalledTimes(1);
  });
});
