import { forwardRef, useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  Box,
  Chip,
  CircularProgress,
  InputBase,
  IconButton,
  Paper,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import capitalize from "lodash/capitalize";
import { useRecoilValue, useRecoilState, useRecoilValueLoadable } from "recoil";
import {
  appsPageState,
  storeCategoriesListState,
  fetchAppsFromStore,
} from "../../data/atoms";

const AppEntry = forwardRef(({ app }, ref) => (
  <a href={`/a/${app.slug}`} style={{ textDecoration: "none" }}>
    <Box
      ref={ref}
      sx={{
        border: "1px solid #e0e0e0",
        borderRadius: 1,
        p: 1.5,
        flexDirection: "column",
        margin: "4px 2px 4px 2px",
        display: "flex",
        alignItems: "left",
        cursor: "pointer",
        textAlign: "left",
        ":hover": {
          backgroundColor: "#edeff7",
          borderColor: "#d0d0d0",
          borderRadius: 1,
          boxShadow: "0 0 0 1px #d0d0d0",
        },
      }}
      onClick={() => {
        window.location.href = `/a/${app.slug}`;
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          textAlign: "left",
          pl: 1,
          width: "100%",
        }}
      >
        <img
          src={app.icon128}
          alt={app.name}
          style={{
            width: 60,
            height: 60,
            margin: "1em 0.5em 0.5em 0.5em",
            borderRadius: "0.2em",
            alignSelf: "start",
          }}
        />
        <Box sx={{ padding: 2 }}>
          <Typography
            component="div"
            color="text.primary"
            sx={{ fontSize: 18, fontWeight: 600 }}
          >
            {app.name}
          </Typography>
          <Box sx={{ mt: 1, mb: 1 }}>
            {app.categories &&
              app.categories.map((category) => (
                <Chip
                  label={capitalize(category)}
                  size="small"
                  key={category}
                />
              ))}
          </Box>
        </Box>
      </Box>
      <Typography
        color="text.secondary"
        sx={{
          m: 3,
          mt: 0,
          fontSize: 14,
          overflow: "hidden",
          textOverflow: "ellipsis",
          display: "-webkit-box",
          "-webkit-line-clamp": "3",
          "-webkit-box-orient": "vertical",
        }}
      >
        {app.description}
      </Typography>
    </Box>
  </a>
));

const AppList = ({ queryTerm }) => {
  const loaderRef = useRef(null);
  const [nextPage, setNextPage] = useState(null);
  const appsLoadable = useRecoilValueLoadable(
    fetchAppsFromStore({ queryTerm, nextPage }),
  );
  const [appsData, setAppsData] = useRecoilState(appsPageState(queryTerm));

  const appendFetchedApps = useCallback(() => {
    if (appsLoadable.state !== "hasValue") return;

    setAppsData((oldAppsData) => {
      const newApps = appsLoadable.contents.apps.filter(
        (app) => !oldAppsData.apps.some((oldApp) => oldApp.slug === app.slug),
      );

      return {
        apps: [...oldAppsData.apps, ...newApps],
        nextPage: appsLoadable.contents.nextPage,
      };
    });
  }, [appsLoadable.contents, setAppsData, appsLoadable.state]);

  useEffect(() => {
    setNextPage(null);
  }, [queryTerm]);

  useEffect(() => {
    if (loaderRef.current && appsLoadable.state === "hasValue") {
      setAppsData(appsLoadable.contents);
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && appsLoadable.contents.nextPage) {
          appendFetchedApps();
          setNextPage(appsLoadable.contents.nextPage);
        }
      });
      observer.observe(loaderRef.current);
      return () => observer.disconnect();
    }
  }, [loaderRef, appsLoadable, appendFetchedApps, setAppsData]);

  const apps = appsData?.apps || [];
  return (
    <Box sx={{ overflowY: "auto", flex: "1 1 auto" }}>
      {apps.length > 0 ? (
        apps.map((app, index) => (
          <AppEntry
            app={app}
            key={app.slug}
            ref={index + 1 === apps.length ? loaderRef : null}
          />
        ))
      ) : (
        <Box ref={loaderRef} />
      )}
      {appsLoadable.state === "loading" && (
        <Box>
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
};

export default function Search({ appSlug }) {
  const location = useLocation();
  const [categoryFilter, setCategoryFilter] = useState(
    appSlug && location.pathname !== "/" ? "recommended" : "featured",
  );
  const [queryTerm, setQueryTerm] = useState(
    appSlug
      ? `categories/recommended/${appSlug}/apps`
      : "categories/featured/apps",
  );
  const categoriesList = useRecoilValue(storeCategoriesListState);
  const [appCategories, setAppCategories] = useState(categoriesList);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (categoryFilter && searchTerm === "") {
      setAppCategories(categoriesList);
      setQueryTerm(
        categoryFilter.toLowerCase().startsWith("recommended")
          ? `categories/recommended/${appSlug}/apps`
          : `categories/${categoryFilter.toLowerCase()}/apps`,
      );
    }
  }, [categoriesList, searchTerm, categoryFilter, appSlug]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", maxHeight: "100vh" }}>
      <Paper
        component="form"
        sx={{
          p: "2px 4px",
          display: "flex",
          alignItems: "center",
          background: "#fbfbfb",
        }}
        onSubmit={(e) => {
          e.preventDefault();
          setQueryTerm(`search?query=${searchTerm}`);
        }}
      >
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="Explore Promptly Apps"
          inputProps={{ "aria-label": "Explore Promptly Apps" }}
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
          }}
        />
        <IconButton
          type="button"
          sx={{ p: "10px" }}
          aria-label="search"
          onClick={() => setQueryTerm(`search?query=${searchTerm}`)}
        >
          <SearchIcon />
        </IconButton>
      </Paper>

      <Box sx={{ textAlign: "left", mt: 1 }}>
        {appCategories.map((category) => (
          <Chip
            key={category.slug}
            label={category.name}
            size="medium"
            variant={
              categoryFilter === category.slug ||
              (categoryFilter.startsWith("recommended") &&
                category.slug === "recommended")
                ? "filled"
                : "outlined"
            }
            sx={{
              cursor: "pointer",
              m: 0.5,
              border:
                categoryFilter.toLowerCase() === category.slug
                  ? "1px solid #b0b0b0"
                  : "1px solid #e0e0e0",
            }}
            onClick={() => {
              setCategoryFilter(category.slug);
              setQueryTerm(
                category.slug === "recommended"
                  ? `categories/recommended/${appSlug}/apps`
                  : `categories/${category.slug}/apps`,
              );
            }}
          />
        ))}
      </Box>
      <AppList queryTerm={queryTerm} appSlug={appSlug} />
    </Box>
  );
}
