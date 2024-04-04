import { useParams } from "react-router-dom";
import { useMediaQuery, useTheme } from "@mui/material";
import Grid from "@mui/material/Unstable_Grid2";
import StoreApp from "../components/store/StoreApp";
import Search from "../components/store/Search";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../data/atoms";

export default function HomePage() {
  const { appSlug = "super-agent" } = useParams();
  const isMobile = useRecoilValue(isMobileState);
  const theme = useTheme();
  const matchesMdDown = useMediaQuery(theme.breakpoints.down("md"));

  return (
    <Grid
      container
      sx={{
        height: "100%",
        margin: "auto",
        padding: 0,
      }}
      columnGap={4}
    >
      <Grid
        xs={12}
        md={7.5}
        sx={{
          height: isMobile ? "calc(100% - 120px)" : "auto",
          border: "1px solid #E8EBEE",
          boxShadow: "0px 2px 8px -2px #1018280F, 0px 4px 12px -2px #1018281A",
          borderRadius: "8px",
          flex: "1 !important",
          ml: 4,
          mt: 4,
          mb: 4,
          ...(matchesMdDown && {
            m: 1,
          }),
        }}
      >
        <StoreApp appSlug={appSlug} />
      </Grid>
      <Grid
        xs={12}
        md={4.5}
        sx={{
          mr: 4,
          ...(matchesMdDown && {
            m: 1,
            marginTop: 4,
          }),
        }}
      >
        <Search appSlug={appSlug} />
      </Grid>
    </Grid>
  );
}
