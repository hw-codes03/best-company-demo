# Metrics: who found the outdated persona?

Synthetic data only. Best Company, its people and every `example.com` address are fictional.

Scored per distinct image file: 40 files, of which **20** really show the outdated persona (Jordan Vale) and must be replaced. Only `evaluate.py` reads the answer key.

- **Precision**: of the files a method flagged, the share that really needed replacing.
- **Recall**: of the files that really needed replacing, the share the method flagged.

| Method | Flagged | Correct | Wrong | Missed | Precision | Recall |
|---|---|---|---|---|---|---|
| Client audit | 18 | 15 | 3 | 5 | 83.3% | 75.0% |
| Crawler | 20 | 20 | 0 | 0 | 100.0% | 100.0% |
| Baseline | 31 | 20 | 11 | 0 | 64.5% | 100.0% |
| AI review | 20 | 20 | 0 | 0 | 100.0% | 100.0% |

## Where each one failed

### Client audit

A manual list from the client. **Missed 5:** 3 × only on a footer-only page missing from the sitemap; 1 × an ordinary image on a normal page; 1 × only lazy-loaded via data-src. **Wrongly flagged 3:** 2 × the Jordan Vail look-alike (decoy); 1 × the approved persona, Priya Nair. The misses cluster where a manual audit wouldn't look: pages reachable only from the footer and images that only load when scrolled into view.

| File | Outcome | Why |
|---|---|---|
| `/assets/ar-SA/hero-15.png` | missed | only on a footer-only page missing from the sitemap |
| `/assets/ar-SA/quote-08.png` | missed | an ordinary image on a normal page |
| `/assets/ar-SA/sig-14.png` | missed | only on a footer-only page missing from the sitemap |
| `/assets/ar-SA/team-16.png` | missed | only on a footer-only page missing from the sitemap |
| `/assets/en-US/quote-09.png` | missed | only lazy-loaded via data-src |
| `/assets/ar-SA/quote-13.png` | wrongly flagged | the approved persona, Priya Nair |
| `/assets/ar-SA/sig-12.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |
| `/assets/en-US/quote-11.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |

### Crawler

Follows every link (including footer-only pages), reads both src and data-src, then checks the pixels for a round teal avatar. **Missed nothing.** **No false alarms.**

### Baseline

Never looks at the picture: it flags anything whose alt text or filename suggests a person. **Missed nothing.** **Wrongly flagged 11:** 6 × the approved persona, Priya Nair; 5 × the Jordan Vail look-alike (decoy). Filenames and alt text say *a person* is pictured, not *which* person, so every approved-persona and decoy image looks the same to it.

| File | Outcome | Why |
|---|---|---|
| `/assets/ar-SA/quote-13.png` | wrongly flagged | the approved persona, Priya Nair |
| `/assets/ar-SA/sig-12.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |
| `/assets/ar-SA/team-09.png` | wrongly flagged | the approved persona, Priya Nair |
| `/assets/en-US/quote-11.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |
| `/assets/en-US/sig-08.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |
| `/assets/en-US/team-02.png` | wrongly flagged | the approved persona, Priya Nair |
| `/assets/en-US/team-03.png` | wrongly flagged | the approved persona, Priya Nair |
| `/assets/en-US/team-10.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |
| `/assets/ja-JP/hero-02.png` | wrongly flagged | the Jordan Vail look-alike (decoy) |
| `/assets/ja-JP/quote-09.png` | wrongly flagged | the approved persona, Priya Nair |
| `/assets/ja-JP/team-03.png` | wrongly flagged | the approved persona, Priya Nair |

### AI review

An AI model looked at every picture, 4 batches of up to 10, and judged name, email and avatar in each locale's script. **Missed nothing.** **No false alarms.** 0 image(s) fell below the 0.7 confidence threshold and went to needs_review. It labelled 5 of 5 decoys correctly.

## Caveats

- **The data is clean and synthetic.** Images are flat renders with crisp text and exact colours. Real photos, compression and screenshots would make both the pixel detector and the AI review less reliable.
- **The AI review was not blind.** The same assistant wrote the generator, so it already knew how the personas and decoys look. It judged only what was visible in each picture and recorded evidence for every call, but an independent reviewer would be a fairer test.
- **The crawler's detector relies on avatar colour**, as the client brief describes it. A look-alike in the same teal would fool it. The AI review also checks name and email, so it would not be fooled.

## Answer-key isolation

No pipeline code mentions the answer key. The crawler and classifiers also run with a guard that blocks any attempt to open `answer_key/`.
