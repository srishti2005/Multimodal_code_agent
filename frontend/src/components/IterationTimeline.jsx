export default function IterationTimeline({ iterations, onSelect, selectedIndex }) {
  if (!iterations?.length) return null;

  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {iterations.map((it, idx) => (
        <button
          key={it.iteration}
          onClick={() => onSelect(idx)}
          className={`shrink-0 px-3 py-2 rounded-lg text-xs border transition-colors ${
            idx === selectedIndex
              ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
              : "border-slate-700 text-slate-400 hover:border-slate-500"
          }`}
        >
          <div className="font-semibold">
            {it.iteration === 0 ? "Initial" : `Refine #${it.iteration}`}
          </div>
          {typeof it.similarity === "number" && (
            <div>{(it.similarity * 100).toFixed(1)}% match</div>
          )}
        </button>
      ))}
    </div>
  );
}
