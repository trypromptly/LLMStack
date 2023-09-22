import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import loadingImage from "../../assets/images/loading.gif";
import ThemedJsonForm from "../ThemedJsonForm";
import validator from "@rjsf/validator-ajv8";
import { useState } from "react";

import { Button } from "@mui/material";

function FunctionFormComponent(props) {
  // Render a form component with submit button
  const [formData, setFormData] = useState({});
  const [submitBtnDisabled, setSubmitBtnDisabled] = useState(false);
  try {
    const form = JSON.parse(props.children[0]);
    return (
      <ThemedJsonForm
        schema={form}
        formData={formData}
        validator={validator}
        onChange={(e) => {
          setFormData(e.formData);
        }}
        submitBtn={
          <Button
            variant="contained"
            onClick={() => {
              setSubmitBtnDisabled(true);
              props.onFormSubmit(formData);
            }}
            disabled={submitBtnDisabled}
          >
            Submit
          </Button>
        }
      />
    );
  } catch (e) {
    console.log(e);
  }
  return <div>Unable to render form</div>;
}

export default function MarkdownRenderer(props) {
  return (
    <ReactMarkdown
      {...props}
      remarkPlugins={[remarkGfm]}
      components={{
        img: ({ node, ...props }) => {
          const { alt, src } = props;
          // We provide alt text and style as altText|style where style is a string
          const [altText, style] = alt.split("|");
          let styleJson = {};
          try {
            styleJson = JSON.parse(style);
          } catch (e) {
            // Do nothing
          }

          if (src.startsWith("data:audio/") || altText === "Audio") {
            return (
              <audio
                controls
                style={{ ...{ display: "block" }, ...styleJson }}
                src={src}
                autoPlay
              >
                {" "}
              </audio>
            );
          }
          // If src is a video that can be played on the browser, render it as a video
          if (
            src.endsWith(".mp4") ||
            src.endsWith(".webm") ||
            src.endsWith(".ogg")
          ) {
            return (
              <video
                controls
                style={{
                  ...{
                    display: "block",
                    maxWidth: "100%",
                    boxShadow: "0px 0px 10px 1px #7d7d7d",
                  },
                  ...styleJson,
                }}
                src={src}
              >
                Unable to load video
              </video>
            );
          }

          return (
            <img
              src={src || loadingImage}
              alt={altText}
              style={{
                ...{
                  display: "block",
                  maxWidth: "100%",
                  boxShadow: "0px 0px 10px 1px #7d7d7d",
                },
                ...styleJson,
              }}
            />
          );
        },
        a: ({ node, ...props }) => {
          return (
            <a {...props} target="_blank" rel="noreferrer nofollow">
              {props.children}
            </a>
          );
        },
        table: ({ node, ...props }) => {
          return (
            <table
              style={{
                borderCollapse: "collapse",
                border: "1px solid #ccc",
              }}
              {...props}
            >
              {props.children}
            </table>
          );
        },
        tr: ({ node, ...props }) => {
          return (
            <tr
              {...props}
              style={{
                border: "1px solid #ccc",
              }}
            >
              {props.children}
            </tr>
          );
        },
        th: ({ node, ...props }) => {
          return (
            <th
              {...props}
              style={{
                border: "1px solid #ccc",
              }}
            >
              {props.children}
            </th>
          );
        },
        td: ({ node, ...props }) => {
          return (
            <td
              {...props}
              style={{
                border: "1px solid #ccc",
              }}
            >
              {props.children}
            </td>
          );
        },
        code: ({ node, ...codeProps }) => {
          const language = codeProps.className;
          if (language === "language-function_form") {
            return (
              <FunctionFormComponent
                onFormSubmit={props.onFormSubmit}
                {...codeProps}
              />
            );
          }
          return <code {...codeProps}>{codeProps.children}</code>;
        },
      }}
    >
      {props.children || ""}
    </ReactMarkdown>
  );
}
