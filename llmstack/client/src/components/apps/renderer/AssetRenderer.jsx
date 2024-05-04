import { memo, useEffect, useState } from "react";
import { Box, IconButton } from "@mui/material";
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
      sx={{ position: "relative" }}
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

  useEffect(() => {
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

  if (type && type.startsWith("image")) {
    return (
      <Image
        url={file?.url || loadingImage}
        alt={file?.name || "Loading"}
        noDownload={noDownload}
        styleJson={styleJson}
      />
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
