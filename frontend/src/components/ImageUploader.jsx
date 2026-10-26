import { useRef } from "react";

export default function ImageUploader({ imagePreview, onImageSelected, onClear }) {
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result;
      const base64 = dataUrl.split(",")[1];
      onImageSelected({ base64, mediaType: file.type, previewUrl: dataUrl });
    };
    reader.readAsDataURL(file);
  };

  return (
    <div
      className="border-2 border-dashed border-slate-700 rounded-xl p-4 text-center cursor-pointer hover:border-indigo-500 transition-colors"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      {imagePreview ? (
        <div className="relative">
          <img src={imagePreview} alt="Reference UI" className="max-h-56 mx-auto rounded-lg" />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClear();
            }}
            className="absolute top-1 right-1 bg-slate-900/80 text-xs px-2 py-1 rounded-full hover:bg-red-600"
          >
            Remove
          </button>
        </div>
      ) : (
        <div className="text-slate-400 py-6">
          <p className="font-medium">Drop a UI screenshot / mockup here</p>
          <p className="text-sm">or click to browse (optional — text-only works too)</p>
        </div>
      )}
    </div>
  );
}
