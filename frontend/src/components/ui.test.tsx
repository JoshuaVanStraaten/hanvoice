import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiError } from "../lib/api";
import { ErrorNote, MeterBar, ScoreRing, SkeletonCards } from "./ui";

describe("SkeletonCards", () => {
  it("announces itself as a labelled loading status", () => {
    render(<SkeletonCards count={2} label="Loading lessons" />);
    expect(screen.getByRole("status", { name: "Loading lessons" })).toBeInTheDocument();
  });
});

describe("ScoreRing", () => {
  it("renders the rounded score with an accessible label", () => {
    render(<ScoreRing score={87.4} label="Accuracy" />);
    expect(
      screen.getByRole("img", { name: "Accuracy: 87 out of 100" }),
    ).toBeInTheDocument();
  });

  it("clamps out-of-range scores", () => {
    render(<ScoreRing score={140} label="Overall" />);
    expect(
      screen.getByRole("img", { name: "Overall: 100 out of 100" }),
    ).toBeInTheDocument();
  });
});

describe("MeterBar", () => {
  it("shows used/limit counts", () => {
    render(<MeterBar used={3} limit={10} label="Pronunciation checks" />);
    expect(screen.getByText("3 / 10")).toBeInTheDocument();
  });
});

describe("ErrorNote", () => {
  it("offers retry for ordinary errors", () => {
    render(<ErrorNote error={new Error("boom")} retry={() => {}} />);
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("points quota errors at plans instead of retry", () => {
    const quota = new ApiError(429, "quota_exceeded", "Daily limit reached.");
    render(<ErrorNote error={quota} retry={() => {}} />);
    expect(screen.getByRole("link", { name: "See plans" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
  });
});
