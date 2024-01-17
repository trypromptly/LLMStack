import { ContentCopyOutlined } from "@mui/icons-material";
import { Box, Button, Stack, Typography } from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { useState } from "react";
import AceEditor from "react-ace";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import loadingImage from "../../assets/images/loading.gif";
import ThemedJsonForm from "../ThemedJsonForm";
import { HeyGenRealtimeAvatar } from "./HeyGenRealtimeAvatar";
import StreamingVideoPlayer from "./StreamingVideoPlayer";

function FunctionFormComponent(props) {
  // Render a form component with submit button
  const [formData, setFormData] = useState({});
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
      />
    );
  } catch (e) {
    console.log(e);
  }
  return <div>Unable to render form</div>;
}

export default function MarkdownRenderer(props) {
  const messageId = props.messageId;
  const runProcessor = props.runProcessor;

  return (
    <ReactMarkdown
      {...props}
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        "promptly-heygen-realtime-avatar": ({ node, ...props }) => {
          return (
            <HeyGenRealtimeAvatar
              node={node}
              {...props}
              runProcessor={runProcessor}
            />
          );
        },
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

          if (src.startsWith("data:videostream/")) {
            return (
              <StreamingVideoPlayer
                streamKey={src.replace("data:videostream/", "")}
                messageId={messageId}
              />
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
          return language ? (
            <Stack sx={{ maxWidth: "90%" }}>
              <Box
                sx={{
                  backgroundColor: "#CCC",
                  padding: "5px",
                  color: "#000",
                  fontWeight: "400",
                  fontSize: "14px",
                  borderRadius: "5px 5px 0px 0px",
                }}
              >
                <Typography sx={{ textTransform: "none" }}>
                  {language?.split("-")[1].charAt(0).toUpperCase() +
                    language?.split("-")[1].slice(1)}
                  <Button
                    startIcon={<ContentCopyOutlined />}
                    sx={{
                      textTransform: "none",
                      padding: "0px 5px",
                      float: "right",
                      color: "#000",
                    }}
                    onClick={() => {
                      navigator.clipboard.writeText(codeProps.children[0]);
                    }}
                  >
                    Copy code
                  </Button>
                </Typography>
              </Box>
              <AceEditor
                mode={language?.split("-")[1] || "text"}
                theme="dracula"
                value={codeProps.children[0]}
                editorProps={{ $blockScrolling: true }}
                setOptions={{
                  useWorker: false,
                  showGutter: false,
                  maxLines: Infinity,
                }}
                style={{
                  borderRadius: "0px 0px 5px 5px",
                  width: "100%",
                }}
              />
            </Stack>
          ) : (
            <code {...codeProps}>{codeProps.children}</code>
          );
        },
      }}
    >
      {props.children || ""}
    </ReactMarkdown>
  );
}
