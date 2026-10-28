# MFA listing videos

Made with `tools/video` (Remotion template + `props/*.json`). All are silent, H.264, 30 fps, 15 s
(Etsy listing videos must be 5 to 15 s; the same cut works for the shop-home video and for Reels / Shorts / TikTok).

| Video | 16:9 (1920x1080): Etsy listing + shop home | 9:16 (1080x1920): Reels / Shorts / TikTok |
|---|---|---|
| 1099 Self-Employed Tax Calculator | [/assets/videos/1099-self-employed-tax-calculator-16x9.mp4](https://mfa-advisory.com/assets/videos/1099-self-employed-tax-calculator-16x9.mp4) (1.9 MB) | [/assets/videos/1099-self-employed-tax-calculator-9x16.mp4](https://mfa-advisory.com/assets/videos/1099-self-employed-tax-calculator-9x16.mp4) (1.7 MB) |
| S Corp vs LLC Savings Calculator | [/assets/videos/s-corp-vs-llc-calculator-16x9.mp4](https://mfa-advisory.com/assets/videos/s-corp-vs-llc-calculator-16x9.mp4) (1.8 MB) | [/assets/videos/s-corp-vs-llc-calculator-9x16.mp4](https://mfa-advisory.com/assets/videos/s-corp-vs-llc-calculator-9x16.mp4) (1.9 MB) |
| The 1099 Kit | [/assets/videos/1099-kit-16x9.mp4](https://mfa-advisory.com/assets/videos/1099-kit-16x9.mp4) (2.1 MB) | [/assets/videos/1099-kit-9x16.mp4](https://mfa-advisory.com/assets/videos/1099-kit-9x16.mp4) (1.8 MB) |
| MFASZ shop overview (shop-home video) | [/assets/videos/mfasz-shop-home-16x9.mp4](https://mfa-advisory.com/assets/videos/mfasz-shop-home-16x9.mp4) (1.8 MB) | [/assets/videos/mfasz-shop-home-9x16.mp4](https://mfa-advisory.com/assets/videos/mfasz-shop-home-9x16.mp4) (2.0 MB) |

Re-render after a copy or image change:

```
cd tools/video && npm ci
node render.mjs props/<name>.json            # both sizes, written here
node render.mjs props/<name>.json --frames-only /tmp/check   # quick PNG stills to check the layout
```

On-screen copy is checked against the MFA copy rules before every render (banned words, CPA claims, prices, street addresses).
