import { Box, IconButton, Card, CardMedia } from "@mui/material";
import { CloseOutlined, VideoCameraBackOutlined } from "@mui/icons-material";
import { useState, useCallback } from "react";

const FloatingVideoIcon = ({ onClick }) => {
  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 16,
        right: 16,
        zIndex: 1000,
        backgroundColor: "#2e7d32",
        borderRadius: "50%",
        padding: 1,
        boxShadow: 5,
      }}
    >
      <IconButton
        aria-label="open video"
        onClick={onClick}
        sx={{ color: "white" }}
      >
        <VideoCameraBackOutlined />
      </IconButton>
    </Box>
  );
};

export default function FloatingVideoPlayer({ videoUrl }) {
  const [isOpen, setIsOpen] = useState(false);

  // useCallback to prevent unnecessary re-renders
  const handleToggle = useCallback(() => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  }, []);

  return (
    <>
      {isOpen ? (
        <div
          style={{
            position: "fixed",
            bottom: "8px",
            right: "8px",
            zIndex: 1000,
            borderRadius: "2px",
            overflow: "hidden",
            boxShadow: "0 0 4px #ccc",
          }}
        >
          <Card>
            <CardMedia
              component="video"
              alt="sample video"
              src={videoUrl}
              controls
              autoPlay
              muted
              sx={{
                maxWidth: "300px",
                maxHeight: "200px",
              }}
            />
          </Card>
          <IconButton
            aria-label="close"
            onClick={handleToggle}
            sx={{
              position: "absolute",
              top: 0,
              right: 0,
              color: "black",
            }}
          >
            <CloseOutlined />
          </IconButton>
        </div>
      ) : (
        <FloatingVideoIcon onClick={handleToggle} />
      )}
    </>
  );
}
