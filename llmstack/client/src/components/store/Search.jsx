import { forwardRef, useCallback, useEffect, useRef, useState } from "react";
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
  storeCategoriesSlugState,
  fetchAppsFromStore,
} from "../../data/atoms";

const AppEntry = forwardRef(({ app }, ref) => (
  <Box
    ref={ref}
    sx={{
      border: "1px solid #e0e0e0",
      borderRadius: "4px",
      backgroundColor: "#f8f8f8",
      p: 1,
      m: 1,
      display: "flex",
      alignItems: "center",
      cursor: "pointer",
      textAlign: "left",
      ":hover": {
        backgroundColor: "#edeff7",
        borderColor: "#d0d0d0",
        borderRadius: "4px",
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
        pb: 1,
      }}
    >
      <img
        src={app.icon128}
        alt={app.name}
        style={{
          width: 70,
          height: 70,
          margin: "1em 0.5em",
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
        <Typography variant="body2" color="text.secondary">
          {app.description?.length > 200
            ? `${app.description.substring(0, 200)}...`
            : app.description}
        </Typography>
        <Box sx={{ mt: 1, mb: 1 }}>
          {app.categories &&
            app.categories.map((category) => (
              <Chip label={capitalize(category)} size="small" key={category} />
            ))}
        </Box>
      </Box>
    </Box>
  </Box>
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
  const [categoryFilter, setCategoryFilter] = useState(
    appSlug ? "recommended" : "featured",
  );
  const [queryTerm, setQueryTerm] = useState(
    appSlug
      ? `categories/recommended/${appSlug}/apps`
      : "categories/featured/apps",
  );
  const defaultCategories = useRecoilValue(storeCategoriesSlugState);
  const [appCategories, setAppCategories] = useState(defaultCategories);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (categoryFilter && searchTerm === "") {
      setAppCategories(defaultCategories);
      setQueryTerm(
        categoryFilter.toLowerCase().startsWith("recommended")
          ? `categories/recommended/${appSlug}/apps`
          : `categories/${categoryFilter.toLowerCase()}/apps`,
      );
    }
  }, [defaultCategories, searchTerm, categoryFilter, appSlug]);

  return (
    <Box
      ml={2}
      mr={2}
      pt={1}
      sx={{ display: "flex", flexDirection: "column", maxHeight: "100vh" }}
    >
      <Paper
        component="form"
        sx={{ p: "2px 4px", display: "flex", alignItems: "center" }}
        onSubmit={(e) => {
          e.preventDefault();
          // searchApps(searchTerm);
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
            key={category}
            label={capitalize(category)}
            size="small"
            variant={
              categoryFilter.toLowerCase() === category.toLowerCase() ||
              (categoryFilter.startsWith("recommended") &&
                category.toLowerCase().startsWith("recommended"))
                ? "filled"
                : "outlined"
            }
            sx={{
              cursor: "pointer",
              m: 0.5,
              border:
                categoryFilter.toLowerCase() === category.toLowerCase()
                  ? "1px solid #b0b0b0"
                  : "1px solid #e0e0e0",
            }}
            onClick={() => {
              setCategoryFilter(category);
              setQueryTerm(
                category.toLowerCase().startsWith("recommended")
                  ? `categories/recommended/${appSlug}/apps`
                  : `categories/${category.toLowerCase()}/apps`,
              );
            }}
          />
        ))}
      </Box>
      <AppList queryTerm={queryTerm} appSlug={appSlug} />
    </Box>
  );
}
