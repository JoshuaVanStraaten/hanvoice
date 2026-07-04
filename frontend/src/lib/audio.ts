/** Browser-side audio conversion. MediaRecorder produces webm/opus (Chrome)
 * or mp4/AAC (Safari) — Azure's short-audio REST API decodes neither. Every
 * recording is normalized here to 16 kHz mono PCM WAV, the format Azure's
 * speech services are happiest with. */

const TARGET_SAMPLE_RATE = 16_000;

/** Upload filename extension matching a recording blob's MIME type. */
export function extensionFor(audio: Blob): string {
  if (audio.type.includes("wav")) return "wav";
  if (audio.type.includes("mp4")) return "mp4";
  return "webm";
}

function writeAscii(view: DataView, offset: number, text: string): void {
  for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i));
}

/** Mono float samples → RIFF/PCM16 WAV blob. */
export function encodeWavPcm16(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  writeAscii(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeAscii(view, 8, "WAVE");
  writeAscii(view, 12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  writeAscii(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const clamped = Math.max(-1, Math.min(1, samples[i] ?? 0));
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}

/** Decode any browser recording and resample to 16 kHz mono WAV. */
export async function toWav16kMono(recording: Blob): Promise<Blob> {
  const ctx = new AudioContext();
  try {
    const decoded = await ctx.decodeAudioData(await recording.arrayBuffer());
    const offline = new OfflineAudioContext(
      1,
      Math.max(1, Math.ceil(decoded.duration * TARGET_SAMPLE_RATE)),
      TARGET_SAMPLE_RATE,
    );
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();
    const rendered = await offline.startRendering();
    return encodeWavPcm16(rendered.getChannelData(0), TARGET_SAMPLE_RATE);
  } finally {
    await ctx.close();
  }
}
