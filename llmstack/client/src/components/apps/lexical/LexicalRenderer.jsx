import { ReactMarkdown } from "react-markdown/lib/react-markdown";
import "./LexicalEditor.css";

export default function LexicalRenderer({ text }) {
  const domParser = new DOMParser();
  const doc = domParser.parseFromString(text, "text/html");

  return String(text).startsWith("<") ? (
    <div
      className="LexicalRenderer__wrapper"
      dangerouslySetInnerHTML={{ __html: doc.body.innerHTML }}
    />
  ) : (
    <ReactMarkdown>{text}</ReactMarkdown>
  );
}
