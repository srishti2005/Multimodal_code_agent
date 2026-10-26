# Multimodal Code Generation Agent

Generate frontend code from **text**, an **image** (screenshot/mockup), or **both** —
then let the agent render its own output, compare it against the reference
screenshot, and iteratively self-correct until it converges.

```
Text Prompt + UI Screenshot
        ↓
Text Understanding + Vision Analysis (multimodal LLM)
        ↓
Frontend Code Generation (HTML / CSS / JS, or React + Tailwind)
        ↓
Render in headless browser  →  Screenshot
        ↓
Visual Comparator (SSIM similarity vs. reference)
        ↓
Self-Correction Agent  →  loop until similarity target or max iterations
        ↓
Final Code + Live Preview
```

This is an open-source implementation of that workflow: a FastAPI backend
that drives the agent loop, and a React/Tailwind frontend with drag-and-drop
image upload, a Monaco code editor, and a live `iframe` preview.

## Repo layout

```
multimodal-code-agent/
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI routes: /generate, /refine, /validate
│   │   ├── agent.py      # the generate → render → compare → refine loop
│   │   ├── llm.py        # Anthropic vision+code calls (swap for any VLM)
│   │   ├── render.py     # Playwright: render HTML, take screenshot, collect console errors
│   │   ├── compare.py    # SSIM-based visual similarity scoring
│   │   └── models.py     # Pydantic request/response schemas
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx                     # main orchestrator
    │   └── components/
    │       ├── ImageUploader.jsx
    │       ├── LivePreview.jsx         # iframe srcDoc preview
    │       ├── CodeViewer.jsx          # Monaco editor
    │       └── IterationTimeline.jsx   # self-correction history
    └── package.json
```

## How it works

1. **Text → Code**: send only a prompt; the model generates a self-contained
   HTML document (React + Tailwind via CDN, or plain HTML/CSS/JS).
2. **Image → Code**: send only a screenshot; the vision model infers layout,
   components, colors, and text, then generates matching code.
3. **Image + Text → Code**: send both — the recommended mode. The image sets
   the visual target, the text adds functional/technical requirements.
4. **Self-correction loop** (when a reference image is provided and
   `auto_refine` is on): the generated page is rendered headlessly with
   Playwright, screenshotted, and compared to the reference via SSIM. If
   similarity is below the target (default 0.92), the vision model is asked
   to describe concrete differences, and that feedback drives another
   `refine_code()` call — up to `max_iterations` times.

Everything the agent generates is a **single self-contained HTML file**
(Tailwind + React + Babel loaded from CDN, no build step). That's what makes
instant `iframe` live preview possible without a bundler in the loop — you
can still export the JSX into a real Vite/CRA project afterward.

## Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium --with-deps

cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api` to the
backend on port 8000 (see `vite.config.js`).

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate` | POST | Text and/or image → code, optional auto self-correction loop |
| `/api/refine` | POST | One manual refinement step (user-written instructions) |
| `/api/validate` | POST | Render code headlessly, return console/page errors |
| `/api/health` | GET | Liveness check |

`POST /api/generate` body:

```json
{
  "prompt": "Recreate this as a responsive React app with Tailwind.",
  "image_base64": "<base64 PNG/JPEG, no data: prefix>",
  "image_media_type": "image/png",
  "framework": "react-tailwind",
  "auto_refine": true,
  "max_iterations": 3
}
```

## Swapping the model

`backend/app/llm.py` is the only file that talks to an AI provider. It's
written against the Anthropic Messages API (vision-capable Claude model), but
the rest of the app only depends on `generate_code()`, `refine_code()`, and
`describe_visual_diff()` — point those at GPT-4o, Gemini, or a self-hosted VLM
and everything else keeps working.

## Roadmap (matches the original project phases)

- [x] Phase 1 — Text-to-code generation
- [x] Phase 2 — Screenshot upload + multimodal understanding
- [x] Phase 3 — Screenshot + text → code
- [x] Phase 4 — Code execution / live preview
- [x] Phase 5 — Screenshot-based visual comparison
- [x] Phase 6 — Iterative self-correction
- [ ] Phase 7 — Formal evaluation harness (dataset of reference screenshots,
      batch scoring, baseline comparisons — see `Ideas for extending` below)

## Ideas for extending

- **Evaluation harness**: a `benchmark/` script that runs a folder of
  reference screenshots through `/api/generate` and reports mean SSIM,
  iteration count, and render-error rate — turns section 10 of the original
  planning doc into an actual reproducible eval.
- **Better similarity metric**: swap/augment SSIM with CLIP-embedding cosine
  similarity or a learned perceptual metric (LPIPS) for something less
  sensitive to pixel-level noise.
- **Component-level diffing**: use the vision model to output a structured
  list of detected components (buttons, cards, nav) for both images and diff
  those sets, instead of only comparing whole-page screenshots.
- **Multi-framework export**: add a Vue or Svelte prompt variant alongside
  React + Tailwind.
- **Auth/rate-limiting** and a job queue (e.g. Celery/RQ) if you want to run
  this as a shared multi-user service rather than locally.

## License

MIT — see [`LICENSE`](./LICENSE). Contributions welcome.
