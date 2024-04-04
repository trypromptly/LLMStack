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
        border: "1px solid #E8EBEE",
        borderRadius: 2,
        p: 4,
        gap: 4,
        flexDirection: "column",
        margin: "8px 2px 10px 2px",
        display: "flex",
        alignItems: "left",
        cursor: "pointer",
        textAlign: "left",
        boxShadow: "0px 2px 4px -2px #1018280F, 0px 4px 8px -2px #1018281A",
        ":hover": {
          backgroundColor: "#F3F5F8",
          borderRadius: 1,
          boxShadow: "0px 2px 4px -2px #1018283F, 0px 4px 8px -2px #1018283A",
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
          width: "100%",
          gap: 4,
        }}
      >
        <img
          src={app.icon128}
          alt={app.name}
          style={{
            width: "50px",
            height: "50px",
            borderRadius: "8px",
            alignSelf: "center",
          }}
        />
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography
            component="div"
            sx={{
              fontSize: 16,
              fontWeight: 600,
              lineHeight: "20px",
              color: "#183A58",
              ml: 0.5,
            }}
          >
            {app.name}
          </Typography>
          <Box>
            {app.categories &&
              app.categories.map((category) => (
                <Chip
                  label={capitalize(category)}
                  size="small"
                  key={category}
                  sx={{
                    borderRadius: 2,
                    padding: "4px, 8px, 4px, 8px",
                    backgroundColor: "#FBFBFB",
                    border: 1,
                    color: "#183A58",
                    borderColor: "gray.main",
                  }}
                />
              ))}
          </Box>
        </Box>
      </Box>
      <Typography
        color="text.secondary"
        sx={{
          fontSize: 14,
          color: "#647B8F",
          lineHeight: "22px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          display: "-webkit-box",
          "-webkit-line-clamp": "2",
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

  const isSameCategory = (categoryFilter, categorySlug) =>
    categoryFilter === categorySlug ||
    (categoryFilter.startsWith("recommended") &&
      categorySlug === "recommended");

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
          mt: 4,
          ml: 0.5,
          mr: 0,
          mb: 2,
          p: "4px 4px 0 4px",
          display: "flex",
          alignItems: "center",
          background: "#fbfbfb",
          border: "1px solid #E8EBEE",
          borderRadius: 2,
          boxShadow: "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
          "& .MuiInputBase-root": {
            backgroundColor: "#fbfbfb",
            boxShadow: "none",
          },
        }}
        onSubmit={(e) => {
          e.preventDefault();
          setQueryTerm(`search?query=${searchTerm}`);
        }}
      >
        <InputBase
          sx={{ ml: 2.5, flex: 1 }}
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

      <Box sx={{ textAlign: "left", mt: 1, mb: 2 }}>
        {appCategories.map((category) => (
          <Chip
            key={category.slug}
            label={category.name}
            size="small"
            variant={"outlined"}
            sx={{
              cursor: "pointer",
              borderRadius: 2,
              color: isSameCategory(categoryFilter, category.slug)
                ? "#FFF"
                : "#183A58",
              padding: "4px, 8px, 4px, 8px",
              m: 1,
              backgroundColor: isSameCategory(categoryFilter, category.slug)
                ? "corral.main"
                : "#FBFBFB",
              boxShadow: "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
              border: "1px solid",
              borderColor: isSameCategory(categoryFilter, category.slug)
                ? "corral.main"
                : "gray.main",
              "& :hover": {
                borderRadius: 2,
                padding: "2px 8px",
                backgroundColor: isSameCategory(categoryFilter, category.slug)
                  ? "corral.main"
                  : "inherit",
              },
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
