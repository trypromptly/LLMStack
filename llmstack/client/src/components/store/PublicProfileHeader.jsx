import { Avatar, Box, Card, Typography } from "@mui/material";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../../data/atoms";

function PublicProfileHeader({ name, avatar, username }) {
  const isMobile = useRecoilValue(isMobileState);

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
        gap: 4,
        height: isMobile ? "40px" : "72px",
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
            src={avatar}
            alt={name}
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
                {name}
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
    </Card>
  );
}

export default PublicProfileHeader;
