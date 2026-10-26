import Editor from "@monaco-editor/react";

export default function CodeViewer({ code, onChange }) {
  return (
    <Editor
      height="100%"
      defaultLanguage="html"
      theme="vs-dark"
      value={code || "<!-- Generated code will appear here -->"}
      onChange={(value) => onChange?.(value ?? "")}
      options={{ minimap: { enabled: false }, fontSize: 13, wordWrap: "on" }}
    />
  );
}
