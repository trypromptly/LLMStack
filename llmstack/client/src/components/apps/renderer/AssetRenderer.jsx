import { memo, useCallback, useEffect, useState } from "react";
import { Box, CircularProgress, IconButton } from "@mui/material";
import { DownloadOutlined } from "@mui/icons-material";
import { axios } from "../../../data/axios";
import loadingImage from "../../../assets/images/loading.gif";
import MediaPlayer from "./MediaPlayer";
import InlineMarkdownRenderer from "./InlineMarkdownRenderer";

const MemoizedMediaPlayer = memo(MediaPlayer);

const Image = (props) => {
  const { url, alt, noDownload, styleJson } = props;
  const [showDownloadIcon, setShowDownloadIcon] = useState(false);

  return (
    <Box
      onMouseEnter={() => setShowDownloadIcon(true)}
      onMouseLeave={() => setShowDownloadIcon(false)}
      sx={{ position: "relative", marginBottom: "8px" }}
    >
      {showDownloadIcon && !noDownload && url && (
        <Box
          sx={{
            display: "flex",
            borderRadius: "4px 0 0 0",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "3px 0",
            position: "absolute",
            top: 0,
            left: 0,
            backgroundColor: "rgba(255, 255, 255, 0.8)",
          }}
        >
          <IconButton
            sx={{ color: "#333" }}
            onClick={() => {
              window.open(url, "_blank");
            }}
          >
            <DownloadOutlined fontSize="small" />
          </IconButton>
        </Box>
      )}
      <img
        src={url || loadingImage}
        alt={alt || "Asset"}
        style={{
          ...{
            display: "block",
            objectFit: "contain",
            maxWidth: "100%",
            borderRadius: "4px",
            boxShadow: "0px 0px 4px 0px #7d7d7d",
          },
          ...styleJson,
        }}
      />
    </Box>
  );
};

export const AssetRenderer = (props) => {
  const { url, type, noDownload, styleJson } = props;
  const [file, setFile] = useState(null);
  const loadFile = useCallback(async () => {
    if (url && url.startsWith("objref://")) {
      try {
        const urlParts = url.split("objref://")[1].split("/");
        const [category, assetId] = [urlParts[0], urlParts[1]];
        axios()
          .get(`/api/assets/${category}/${assetId}`)
          .then((response) => {
            setFile(response.data);
          })
          .catch((error) => {
            console.error(error);
          });
      } catch (error) {
        console.error(error);
      }
    }
  }, [url]);

  useEffect(() => {
    loadFile();
  }, [url, loadFile]);

  useEffect(() => {
    if (!window.MediaSource) {
      console.error(
        "MediaSource API is not supported in this browser. Asset streaming will not work. Will reload the file after 15 seconds to see if streaming asset is finalized.",
      );

      if (file && file.streaming) {
        // Set a timer to reload the file after 5 seconds
        setTimeout(() => {
          loadFile();
        }, 15000);
      }
    }
  }, [file, loadFile]);

  if (type && type.startsWith("image")) {
    return file?.url ? (
      <Image
        url={file?.url}
        alt={file?.name || "Loading"}
        noDownload={noDownload}
        styleJson={styleJson}
      />
    ) : (
      <Box>
        <CircularProgress size={12} />
        &nbsp; Loading image...
      </Box>
    );
  }

  if (type === "text/markdown") {
    return (
      <InlineMarkdownRenderer
        src={file?.url}
        streaming={file?.streaming || false}
      />
    );
  }

  if (type.startsWith("audio") || type.startsWith("video")) {
    if (file?.streaming && !window.MediaSource) {
      return null;
    }

    return (
      <MemoizedMediaPlayer
        controls
        src={file?.url}
        streaming={file?.streaming || false}
        autoPlay
        mimeType={type}
      />
    );
  }

  return <p>AssetRenderer</p>;
};
