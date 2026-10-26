import { useState } from "react";
import axios from "axios";
import ImageUploader from "./components/ImageUploader.jsx";
import LivePreview from "./components/LivePreview.jsx";
import CodeViewer from "./components/CodeViewer.jsx";
import IterationTimeline from "./components/IterationTimeline.jsx";

const api = axios.create({ baseURL: "/api" });

export default function App() {
  const [prompt, setPrompt] = useState(
    "Create a responsive React login page with email, password, forgot-password link, and a Google login button."
  );
  const [image, setImage] = useState(null); // { base64, mediaType, previewUrl }
  const [framework, setFramework] = useState("react-tailwind");
  const [autoRefine, setAutoRefine] = useState(true);
  const [maxIterations, setMaxIterations] = useState(3);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [iterations, setIterations] = useState([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [refineNote, setRefineNote] = useState("");
  const [refining, setRefining] = useState(false);

  const selected = iterations[selectedIdx];

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/generate", {
        prompt,
        image_base64: image?.base64 ?? null,
        image_media_type: image?.mediaType ?? "image/png",
        framework,
        auto_refine: Boolean(image) && autoRefine,
        max_iterations: maxIterations,
      });
      const data = res.data;
      const list =
        data.iterations?.length > 0
          ? data.iterations
          : [{ iteration: 0, code: data.code, similarity: data.final_similarity, screenshot_base64: data.preview_screenshot_base64 }];
      setIterations(list);
      setSelectedIdx(list.length - 1);
    } catch (e) {
      setError(e?.response?.data?.detail ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManualRefine = async () => {
    if (!selected || !refineNote.trim()) return;
    setRefining(true);
    setError(null);
    try {
      const res = await api.post("/refine", {
        code: selected.code,
        instructions: refineNote,
        image_base64: image?.base64 ?? null,
        image_media_type: image?.mediaType ?? "image/png",
        framework,
      });
      const next = {
        iteration: (selected.iteration ?? 0) + 1,
        code: res.data.code,
        similarity: res.data.similarity,
        feedback: refineNote,
        screenshot_base64: res.data.screenshot_base64,
      };
      const updated = [...iterations, next];
      setIterations(updated);
      setSelectedIdx(updated.length - 1);
      setRefineNote("");
    } catch (e) {
      setError(e?.response?.data?.detail ?? e.message);
    } finally {
      setRefining(false);
    }
  };

  const handleCodeEdit = (newCode) => {
    if (!iterations.length) return;
    const updated = [...iterations];
    updated[selectedIdx] = { ...updated[selectedIdx], code: newCode };
    setIterations(updated);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Multimodal Code Generation Agent</h1>
          <p className="text-xs text-slate-400">Text + Screenshot → Code → Live Preview → Self-Correction</p>
        </div>
        <a
          href="https://github.com/"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          Open Source · MIT
        </a>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4 p-4">
        {/* Left: controls */}
        <section className="space-y-4">
          <div>
            <label className="text-sm font-medium">Requirements</label>
            <textarea
              className="mt-1 w-full h-28 rounded-lg bg-slate-900 border border-slate-700 p-2 text-sm"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder='e.g. "Convert this dashboard into a responsive React app with Tailwind."'
            />
          </div>

          <div>
            <label className="text-sm font-medium">Reference screenshot (optional)</label>
            <div className="mt-1">
              <ImageUploader
                imagePreview={image?.previewUrl}
                onImageSelected={(img) => setImage(img)}
                onClear={() => setImage(null)}
              />
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-sm font-medium">Framework</label>
              <select
                className="mt-1 w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-sm"
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
              >
                <option value="react-tailwind">React + Tailwind</option>
                <option value="html-css-js">HTML / CSS / JS</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium">Max refine iterations</label>
              <input
                type="number"
                min={0}
                max={6}
                className="mt-1 w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-sm"
                value={maxIterations}
                onChange={(e) => setMaxIterations(Number(e.target.value))}
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefine}
              onChange={(e) => setAutoRefine(e.target.checked)}
              disabled={!image}
            />
            Auto self-correct against reference screenshot
          </label>

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2 font-medium"
          >
            {loading ? "Generating…" : "Generate UI"}
          </button>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <IterationTimeline iterations={iterations} onSelect={setSelectedIdx} selectedIndex={selectedIdx} />

          {selected?.feedback && (
            <div className="text-xs bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-400">
              <span className="font-semibold text-slate-300">Feedback used: </span>
              {selected.feedback}
            </div>
          )}

          {iterations.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <label className="text-sm font-medium">Manual refine instructions</label>
              <textarea
                className="w-full h-16 rounded-lg bg-slate-900 border border-slate-700 p-2 text-sm"
                value={refineNote}
                onChange={(e) => setRefineNote(e.target.value)}
                placeholder="e.g. Make the sidebar collapsible on mobile."
              />
              <button
                onClick={handleManualRefine}
                disabled={refining || !refineNote.trim()}
                className="w-full rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-50 py-2 text-sm"
              >
                {refining ? "Refining…" : "Apply refinement"}
              </button>
            </div>
          )}
        </section>

        {/* Right: preview + code */}
        <section className="grid grid-rows-2 gap-4 min-h-[70vh]">
          <div className="rounded-xl border border-slate-800 overflow-hidden">
            <LivePreview code={selected?.code} />
          </div>
          <div className="rounded-xl border border-slate-800 overflow-hidden">
            <CodeViewer code={selected?.code} onChange={handleCodeEdit} />
          </div>
        </section>
      </main>
    </div>
  );
}
