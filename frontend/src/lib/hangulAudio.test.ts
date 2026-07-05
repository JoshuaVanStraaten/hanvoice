import { describe, expect, it } from "vitest";

import { audioTextFor, isCarrier } from "./hangulAudio";

describe("audioTextFor", () => {
  it("maps consonants to their ㅏ-carrier syllable", () => {
    expect(audioTextFor("ㄱ")).toBe("가");
    expect(audioTextFor("ㅁ")).toBe("마");
    expect(audioTextFor("ㅎ")).toBe("하");
  });

  it("maps vowels to their silent-ㅇ carrier", () => {
    expect(audioTextFor("ㅏ")).toBe("아");
    expect(audioTextFor("ㅡ")).toBe("으");
    expect(audioTextFor("ㅣ")).toBe("이");
  });

  it("passes full syllables and words through", () => {
    expect(audioTextFor("한")).toBe("한");
    expect(audioTextFor("한국")).toBe("한국");
  });

  it("prefers an authored override", () => {
    expect(audioTextFor("ㄱ", "그")).toBe("그");
  });
});

describe("isCarrier", () => {
  it("is true only when the played text differs from the glyph", () => {
    expect(isCarrier("ㄱ")).toBe(true);
    expect(isCarrier("한")).toBe(false);
    expect(isCarrier("ㄱ", "그")).toBe(true);
    expect(isCarrier("한", "한")).toBe(false);
  });
});
