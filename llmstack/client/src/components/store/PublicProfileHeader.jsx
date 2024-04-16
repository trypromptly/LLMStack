import { useEffect, useState } from "react";
import { Avatar, Box, Card, Typography } from "@mui/material";
import { axios } from "../../data/axios";

function PublicProfileHeader({ username, sessionData }) {
  const [publicProfile, setPublicProfile] = useState(null);

  useEffect(() => {
    // Fetch public profile data
    if (!username) return;

    axios()
      .get(`/api/profiles/${username}`)
      .then((response) => {
        setPublicProfile(response.data);
      })
      .catch((error) => {
        console.error(error);
      });
  }, [username]);

  return (
    <Card
      sx={{
        backgroundColor: "#F3F5F8",
        boxShadow: "none",
        display: "flex",
        flexDirection: "column",
        border: "1px solid #E8EBEE",
        borderRadius: "8px 8px 0 0",
        p: 4,
        gap: 2,
        height: "auto",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          textAlign: "left",
          width: "100%",
        }}
      >
        <Box
          sx={{
            display: "flex",
            width: "100%",
            gap: 4,
            alignItems: "center",
          }}
        >
          <Avatar
            src={publicProfile?.avatar}
            alt={publicProfile?.name}
            variant="square"
            sx={{ borderRadius: 2, cursor: "pointer" }}
            onClick={() => (window.location.href = `/u/${username}`)}
          />
          <Box sx={{ width: "100%" }}>
            <Box sx={{ width: "100%", display: "flex", alignItems: "center" }}>
              <Typography
                component="h1"
                sx={{
                  fontSize: "16px",
                  lineHeight: "20px",
                  fontWeight: 600,
                }}
              >
                {sessionData?.metadata?.title ||
                  publicProfile?.name ||
                  username}
              </Typography>
            </Box>
            <Typography
              color="corral.main"
              sx={{ display: "inline", fontSize: "14px" }}
            >
              {username}
            </Typography>
          </Box>
        </Box>
      </Box>
      {sessionData &&
        sessionData.metadata &&
        sessionData.metadata.description && (
          <Box>
            <Typography
              color="primary.main"
              variant="body1"
              sx={{ fontSize: "14px", padding: 0, textAlign: "left" }}
            >
              {sessionData?.metadata.description}
            </Typography>
          </Box>
        )}
    </Card>
  );
}

export default PublicProfileHeader;
