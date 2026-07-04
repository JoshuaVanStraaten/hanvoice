import { describe, expect, it } from "vitest";

import { encodeWavPcm16, extensionFor } from "./audio";

describe("encodeWavPcm16", () => {
  it("writes a valid RIFF/PCM16 mono header", async () => {
    const samples = new Float32Array([0, 0.5, -0.5, 1]);
    const blob = encodeWavPcm16(samples, 16_000);
    expect(blob.type).toBe("audio/wav");
    expect(blob.size).toBe(44 + samples.length * 2);

    const view = new DataView(await blob.arrayBuffer());
    const ascii = (offset: number, length: number) =>
      Array.from({ length }, (_, i) => String.fromCharCode(view.getUint8(offset + i))).join("");
    expect(ascii(0, 4)).toBe("RIFF");
    expect(ascii(8, 4)).toBe("WAVE");
    expect(view.getUint16(20, true)).toBe(1); // PCM
    expect(view.getUint16(22, true)).toBe(1); // mono
    expect(view.getUint32(24, true)).toBe(16_000);
    expect(view.getUint32(40, true)).toBe(samples.length * 2); // data size
  });

  it("clamps out-of-range samples instead of overflowing", async () => {
    const blob = encodeWavPcm16(new Float32Array([2, -2]), 16_000);
    const view = new DataView(await blob.arrayBuffer());
    expect(view.getInt16(44, true)).toBe(0x7fff);
    expect(view.getInt16(46, true)).toBe(-0x8000);
  });
});

describe("extensionFor", () => {
  it("maps MIME types to upload extensions", () => {
    expect(extensionFor(new Blob([], { type: "audio/wav" }))).toBe("wav");
    expect(extensionFor(new Blob([], { type: "audio/mp4" }))).toBe("mp4");
    expect(extensionFor(new Blob([], { type: "audio/webm;codecs=opus" }))).toBe("webm");
  });
});
