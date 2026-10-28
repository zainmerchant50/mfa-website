#!/usr/bin/env python3
"""Make an .srt caption file from an audio or video file with Whisper (optional; our first videos have no voiceover).

Usage:
  python3 tools/video/captions.py VOICEOVER.mp4                    # -> VOICEOVER.srt next to it
  python3 tools/video/captions.py clip.wav -o out.srt --model base
  python3 tools/video/captions.py clip.mp4 --model /path/to/faster-whisper-tiny   # a model folder already on disk

One-time install (pick one; faster-whisper is lighter and needs no PyTorch):
  pip install --break-system-packages faster-whisper==1.2.1          # preferred
  pip install --break-system-packages openai-whisper                 # fallback (pulls in PyTorch, ~2 GB)

The first run downloads the model (tiny ~75 MB, base ~145 MB): faster-whisper from huggingface.co,
openai-whisper from openaipublic.azureedge.net. Where those hosts are blocked (the Claude cloud container
only reaches npm/pip/GitHub), run this on the Windows PC or Mac instead, or copy a downloaded model folder
over and pass its path with --model.

Check the .srt by eye before burning it in: names, form numbers and dollar figures are where Whisper slips,
and on-screen text must still follow the MFA copy rules (banned words, CPA claims, prices, street addresses).
"""
import argparse
import os
import sys


def ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_faster(path, model, lang):
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(path, language=lang, vad_filter=True)
    return [(s.start, s.end, s.text.strip()) for s in segs]


def segments_openai(path, model, lang):
    import whisper

    m = whisper.load_model(model)
    r = m.transcribe(path, language=lang, fp16=False)
    return [(s["start"], s["end"], s["text"].strip()) for s in r["segments"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("media", help="audio or video file (anything ffmpeg reads)")
    ap.add_argument("-o", "--out", help="output .srt (default: next to the input)")
    ap.add_argument("--model", default="tiny", help="tiny | base | a local model folder (default: tiny)")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()

    out = a.out or os.path.splitext(a.media)[0] + ".srt"
    try:
        segs = segments_faster(a.media, a.model, a.lang)
        engine = "faster-whisper"
    except ImportError:
        try:
            segs = segments_openai(a.media, a.model, a.lang)
            engine = "openai-whisper"
        except ImportError:
            sys.exit("Whisper is not installed. Run:  pip install --break-system-packages faster-whisper==1.2.1")

    with open(out, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate((x for x in segs if x[2]), 1):
            f.write(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n\n")
    print(f"{out}  ({len(segs)} segments, {engine}, model {a.model})")


if __name__ == "__main__":
    main()
