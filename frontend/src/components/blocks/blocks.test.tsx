import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ExplainBlock } from "./ExplainBlock";
import { QuizBlock } from "./QuizBlock";
import type { ExplainPayload, QuizPayload } from "../../lib/types";

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
      <ExplainBlock payload={explainPayload} completing={false} onContinue={onContinue} />,
    );

    expect(screen.getByText("alphabet")).toBeInTheDocument(); // **bold** parsed
    expect(screen.getByText("ㅏ")).toBeInTheDocument();
    expect(screen.getByText("가요")).toBeInTheDocument();
    expect(screen.getByText("gayo · I go")).toBeInTheDocument();
    expect(screen.getByText(/Letters stack into blocks/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(onContinue).toHaveBeenCalledTimes(1);
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
