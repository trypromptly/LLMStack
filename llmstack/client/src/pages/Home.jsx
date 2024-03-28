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
        padding: 2,
      }}
      columnGap={2}
    >
      <Grid
        xs={12}
        md={7.5}
        sx={{
          height: isMobile ? "calc(100% - 120px)" : "auto",
          border: "solid 1px #ddd",
          borderRadius: "8px 8px 4px 4px",
          flex: "1 !important",
        }}
      >
        <StoreApp appSlug={appSlug} />
      </Grid>
      <Grid
        xs={12}
        md={4.5}
        sx={{
          ...(matchesMdDown && {
            marginTop: 3,
          }),
        }}
      >
        <Search appSlug={appSlug} />
      </Grid>
    </Grid>
  );
}
