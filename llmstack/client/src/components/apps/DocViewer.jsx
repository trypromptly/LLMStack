import { Worker, Viewer } from "@react-pdf-viewer/core";

import { zoomPlugin } from "@react-pdf-viewer/zoom";
import "@react-pdf-viewer/zoom/lib/styles/index.css";
import { searchPlugin } from "@react-pdf-viewer/search";
import "@react-pdf-viewer/search/lib/styles/index.css";
import { pageNavigationPlugin } from "@react-pdf-viewer/page-navigation";
import "@react-pdf-viewer/page-navigation/lib/styles/index.css";
import { fullScreenPlugin } from "@react-pdf-viewer/full-screen";
import "@react-pdf-viewer/full-screen/lib/styles/index.css";
import { toolbarPlugin } from "@react-pdf-viewer/toolbar";
import "@react-pdf-viewer/toolbar/lib/styles/index.css";

import React, { useMemo, memo } from "react";
import { Box } from "@mui/material";

export const PDFViewer = memo(
  (props) => {
    const { file, ...sxProps } = props;
    const memoizedFileObject = useMemo(() => ({ fileUrl: file }), [file]);
    const fullScreenPluginInstance = fullScreenPlugin();
    const zoomPluginInstance = zoomPlugin();
    const searchPluginInstance = searchPlugin();
    const pageNavigationPluginInstance = pageNavigationPlugin();
    const toolbarPluginInstance = toolbarPlugin();
    const { renderDefaultToolbar, Toolbar } = toolbarPluginInstance;
    const transform = (slot) => {
      return {
        ...slot,
        Upload: () => <></>,
        Download: () => <></>,
        EnterFullScreen: () => <></>,
        SwitchTheme: () => <></>,
        Print: () => <></>,
        ShowProperties: () => <></>,
        Open: () => <></>,
        Rotate: () => <></>,
      };
    };
    toolbarPluginInstance.fullScreenPluginInstance = fullScreenPluginInstance;
    toolbarPluginInstance.zoomPluginInstance = zoomPluginInstance;
    toolbarPluginInstance.searchPluginInstance = searchPluginInstance;
    toolbarPluginInstance.pageNavigationPluginInstance =
      pageNavigationPluginInstance;
    toolbarPluginInstance.propertiesPluginInstance = null;

    return memoizedFileObject?.fileUrl ? (
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
        <Box sx={{ height: "300px", overflow: "scroll", ...sxProps }}>
          <Box>
            <Toolbar>{renderDefaultToolbar(transform)}</Toolbar>
          </Box>
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
