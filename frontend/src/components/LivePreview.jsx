export default function LivePreview({ code }) {
  if (!code) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        Generated UI will render here.
      </div>
    );
  }
  return (
    <iframe
      title="live-preview"
      srcDoc={code}
      className="w-full h-full bg-white rounded-lg"
      sandbox="allow-scripts"
    />
  );
}
