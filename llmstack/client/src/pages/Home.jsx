import { useParams } from "react-router-dom";
import { Button, useMediaQuery, useTheme, Stack } from "@mui/material";
import Grid from "@mui/material/Unstable_Grid2";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../data/atoms";
import { lazy, useState } from "react";

const StoreApp = lazy(() => import("../components/store/StoreApp"));
const Search = lazy(() => import("../components/store/Search"));

export default function HomePage() {
  const { appSlug = "super-agent" } = useParams();
  const isMobile = useRecoilValue(isMobileState);
  const theme = useTheme();
  const matchesMdDown = useMediaQuery(theme.breakpoints.down("md"));
  const [selectedTab, setSelectedTab] = useState("main");

  const defaultMobileTabStyle = {
    backgroundColor: "gray.main",
    color: "black",
    width: "50%",
  };

  const selectedMobileTabStyle = {
    backgroundColor: "corral.main",
    color: "white",
    width: "50%",

    "&:hover": {
      backgroundColor: "corral.dark",
    },
  };

  return (
    <Grid
      container
      sx={{
        height: isMobile ? "calc(100vh - 68px)" : "100%",
        margin: "auto",
        padding: 0,
        alignContent: "flex-start",
      }}
      columnGap={isMobile ? 1 : 4}
    >
      {isMobile && (
        <Stack
          sx={{
            display: "flex",
            width: "100%",
            padding: "8px",
            flexDirection: "row",
            justifyContent: "center",
            gap: 2,
            height: "30px",
          }}
        >
          <Button
            variant="contained"
            size="small"
            sx={
              selectedTab === "main"
                ? selectedMobileTabStyle
                : defaultMobileTabStyle
            }
            onClick={() => setSelectedTab("main")}
          >
            Arena
          </Button>
          <Button
            variant="contained"
            size="small"
            sx={
              selectedTab === "more"
                ? selectedMobileTabStyle
                : defaultMobileTabStyle
            }
            onClick={() => setSelectedTab("more")}
          >
            More Apps
          </Button>
        </Stack>
      )}
      {(!isMobile || selectedTab === "main") && (
        <Grid
          xs={12}
          md={7.5}
          sx={{
            height: isMobile ? "calc(100% - 68px)" : "calc(100% - 32px)",
            border: "1px solid #E8EBEE",
            boxShadow:
              "0px 2px 8px -2px #1018280F, 0px 4px 12px -2px #1018281A",
            borderRadius: "8px",
            flex: "1 !important",
            ml: 4,
            mt: 4,
            mb: 4,
            ...(matchesMdDown && {
              m: 2,
            }),
          }}
        >
          <StoreApp appSlug={appSlug} />
        </Grid>
      )}
      {(!isMobile || selectedTab === "more") && (
        <Grid
          xs={12}
          md={4.5}
          sx={{
            display: isMobile && selectedTab === "main" ? "none" : "block",
            mr: 4,
            ...(matchesMdDown && {
              m: 2,
            }),
          }}
        >
          <Search appSlug={appSlug} />
        </Grid>
      )}
    </Grid>
  );
}
