import { useParams } from "react-router-dom";
import Grid from "@mui/material/Unstable_Grid2";
import StoreApp from "../components/store/StoreApp";
import Search from "../components/store/Search";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../data/atoms";

export default function HomePage() {
  const { appSlug = "super-agent" } = useParams();
  const isMobile = useRecoilValue(isMobileState);

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
        md={7}
        sx={{
          height: isMobile ? "calc(100% - 120px)" : "auto",
          border: "solid 1px #ddd",
          borderRadius: "8px 8px 4px 4px",
          flex: "1 !important",
        }}
      >
        <StoreApp appSlug={appSlug} />
      </Grid>
      <Grid xs={12} md={5}>
        <Search appSlug={appSlug} />
      </Grid>
    </Grid>
  );
}
