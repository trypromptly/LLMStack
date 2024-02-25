import { pdfjs } from "react-pdf";
import { Document, Page } from "react-pdf";

import React, { useMemo, useState, memo } from "react";
import {
  CircularProgress,
  Box,
  TextField,
  IconButton,
  Stack,
} from "@mui/material";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.js",
  import.meta.url,
).toString();

const ZOOM_FACTOR = 1.2; // Adjust this value for finer control over zoom level changes.

export const PDFViewer = memo(
  (props) => {
    const { file, ...sxProps } = props;
    const memoizedFileObject = useMemo(() => ({ url: file }), [file]);

    const [numPages, setNumPages] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [zoom, setZoom] = useState(1); // Setting initial zoom level to 1.

    const nextPage = () => {
      setCurrentPage((prevPage) => Math.min(prevPage + 1, numPages));
    };

    const prevPage = () => {
      setCurrentPage((prevPage) => Math.max(prevPage - 1, 1));
    };

    const zoomIn = () => {
      setZoom((prevZoom) => prevZoom * ZOOM_FACTOR);
    };

    const zoomOut = () => {
      setZoom((prevZoom) => prevZoom / ZOOM_FACTOR);
    };

    console.log("Rendring PDFViewer");
    return memoizedFileObject?.url ? (
      <Stack
        sx={{
          width: "100%",
          height: "400px",
          position: "relative",
          ...sxProps,
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            padding: "10px",
          }}
        >
          <Stack direction="row" spacing={2}>
            <IconButton
              variant="contained"
              onClick={prevPage}
              disabled={currentPage === 1}
            >
              <ArrowBackIcon />
            </IconButton>
            <TextField
              sx={{ width: "50px" }}
              variant="outlined"
              size="small"
              value={currentPage}
              onChange={(e) => {
                const page = parseInt(e.target.value, 10);
                if (page >= 1 && page <= numPages) {
                  setCurrentPage(page);
                }
              }}
            />
            <IconButton
              variant="contained"
              onClick={nextPage}
              disabled={currentPage === numPages}
            >
              <ArrowForwardIcon />
            </IconButton>
          </Stack>
          <Stack direction="row" spacing={2}>
            <IconButton onClick={zoomIn} color="primary" aria-label="zoom in">
              <ZoomInIcon />
            </IconButton>
            <IconButton onClick={zoomOut} color="primary" aria-label="zoom out">
              <ZoomOutIcon />
            </IconButton>
          </Stack>
        </Box>
        <Box sx={{ width: "100%", height: "100%", overflow: "auto" }}>
          <Document
            file={memoizedFileObject}
            loading={<CircularProgress />}
            onLoadSuccess={({ numPages }) => {
              setNumPages(numPages);
            }}
          >
            <Page
              key={`page_${currentPage}`}
              className={`page_${currentPage}`}
              pageNumber={currentPage}
              scale={zoom}
            />
          </Document>
        </Box>
      </Stack>
    ) : null;
  },
  (prev, next) => {
    return prev.file === next.file;
  },
);
