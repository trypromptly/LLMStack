import { Worker, Viewer } from "@react-pdf-viewer/core";

import { toolbarPlugin } from "@react-pdf-viewer/toolbar";
import "@react-pdf-viewer/toolbar/lib/styles/index.css";
import "@react-pdf-viewer/core/lib/styles/index.css";
import "@react-pdf-viewer/default-layout/lib/styles/index.css";
import React, { useMemo, memo, useRef } from "react";
import { Box } from "@mui/material";

const PDFViewerToolbarSlots = (props) => {
  const {
    CurrentPageInput,
    GoToNextPage,
    GoToPreviousPage,
    NumberOfPages,
    ZoomIn,
    ZoomOut,
  } = props;
  return (
    <>
      <div style={{ padding: "0px 2px" }}>
        <ZoomOut />
      </div>
      <div style={{ padding: "0px 2px" }}>
        <ZoomIn />
      </div>
      <div style={{ padding: "0px 2px", marginLeft: "auto" }}>
        <GoToPreviousPage />
      </div>
      <div style={{ padding: "0px 2px", width: "4rem" }}>
        <CurrentPageInput />
      </div>
      <div style={{ padding: "0px 2px" }}>
        / <NumberOfPages />
      </div>
      <div style={{ padding: "0px 2px" }}>
        <GoToNextPage />
      </div>
    </>
  );
};

export const PDFViewer = memo(
  (props) => {
    const viewerRef = useRef(null);

    const { file, ...sxProps } = props;
    const memoizedFileObject = useMemo(() => ({ fileUrl: file }), [file]);
    const toolbarPluginInstance = toolbarPlugin();
    const { Toolbar } = toolbarPluginInstance;

    return memoizedFileObject?.fileUrl ? (
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
        <Box
          sx={{
            height: "300px",
            overflow: "scroll",
            position: "relative",
            ...sxProps,
          }}
          ref={viewerRef}
          id="pdf-viewer-container"
        >
          <div
            style={{
              alignItems: "center",
              backgroundColor: "#eeeeee",
              border: "1px solid rgba(0, 0, 0, 0.2)",
              borderRadius: "2px",
              bottom: "16px",
              display: "flex",
              left: "50%",
              padding: "4px",
              position: "absolute",
              transform: "translate(-50%, 0)",
              zIndex: 1,
            }}
          >
            <Toolbar>
              {(toolbarSlot) => {
                const {
                  CurrentPageInput,
                  GoToNextPage,
                  GoToPreviousPage,
                  NumberOfPages,
                  ZoomIn,
                  ZoomOut,
                } = toolbarSlot;
                return (
                  <PDFViewerToolbarSlots
                    CurrentPageInput={CurrentPageInput}
                    GoToNextPage={GoToNextPage}
                    GoToPreviousPage={GoToPreviousPage}
                    NumberOfPages={NumberOfPages}
                    ZoomIn={ZoomIn}
                    ZoomOut={ZoomOut}
                  />
                );
              }}
            </Toolbar>
          </div>

          <Viewer
            fileUrl={memoizedFileObject.fileUrl}
            plugins={[toolbarPluginInstance]}
          />
        </Box>
      </Worker>
    ) : null;
  },
  (prev, next) => {
    return prev.file === next.file;
  },
);
