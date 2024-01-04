import { axios } from "../data/axios";
import { organizationState, profileFlagsState } from "../data/atoms";
import { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  TextField,
  InputAdornment,
  Toolbar,
} from "@mui/material";
import { useSearchParams } from "react-router-dom";
import SearchIcon from "@mui/icons-material/Search";

import Grid from "@mui/material/Unstable_Grid2";
import { useRecoilValue } from "recoil";

class DiscoverCard {
  constructor(type, title, description, tags, link) {
    this.type = type;
    this.title = title;
    this.description = description;
    this.tags = tags;
    this.link = link;
  }
}

function SearchAndFilter({
  filters,
  handleSearch,
  handleFilter,
  search,
  selectedFilter = "All",
}) {
  return (
    <Toolbar
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 150,
        margin: "5px",
        paddingTop: "2px",
        background: "white",
      }}
    >
      <Grid container style={{ alignItems: "center", width: "100%" }}>
        <Grid item xs={12} md={8}>
          <Box sx={{ textAlign: "left" }}>
            {filters.map((filter) => (
              <Chip
                sx={{
                  margin: "5px",
                  borderRadius: "10px",
                }}
                key={filter}
                label={filter}
                onClick={() => handleFilter(filter)}
                color={selectedFilter === filter ? "primary" : "default"}
                background="white"
              />
            ))}
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Box sx={{ textAlign: "end" }}>
            <TextField
              placeholder="Search"
              value={search}
              onChange={handleSearch}
              size="small"
              InputProps={{
                sx: { borderRadius: "10px" },
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Grid>
      </Grid>
    </Toolbar>
  );
}

export default function Discover() {
  const [searchParams] = useSearchParams();

  const [apps, setApps] = useState([]);
  const [discoverCards, setDiscoverCards] = useState([]);
  const [filters, setFilters] = useState(["All"]);
  const [selectedFilter, setSelectedFilter] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [orgApps, setOrgApps] = useState([]);
  const profileFlags = useRecoilValue(profileFlagsState);
  const organization = useRecoilValue(organizationState);

  const pageHeaderStyle = {
    textAlign: "left",
    width: "100%",
    fontFamily: "Lato, sans-serif",
    marginBottom: "10px",
    padding: "5px 10px",
    fontWeight: 600,
    borderRadius: "5px",
    color: "#1c3c5a",
    fontSize: "18px",
    borderBottom: "solid 3px #1c3c5a",
    borderLeft: "solid 1px #ccc",
    borderRight: "solid 1px #ccc",
    display: profileFlags.IS_ORGANIZATION_MEMBER ? "block" : "none",
  };

  useEffect(() => {
    axios()
      .get("/api/appHub")
      .then((response) => {
        // handle success
        const appCards = response.data.map((app) => {
          const link = `/app/${app.published_uuid}`;

          const tags = (app?.categories || []).map((category) => category.name);

          if (tags.length === 0) {
            tags.push("Productivity");
          }
          return new DiscoverCard("app", app.name, app.description, tags, link);
        });
        setApps(appCards);
      })
      .catch((error) => {
        // handle error
      })
      .then({
        // always executed
      });
  }, [setApps]);

  useEffect(() => {
    if (profileFlags.IS_ORGANIZATION_MEMBER) {
      axios()
        .get("/api/org/apps")
        .then((response) => {
          setOrgApps(response.data);
        });
    }
  }, [profileFlags.IS_ORGANIZATION_MEMBER, setOrgApps]);

  useEffect(() => {
    setDiscoverCards([...apps]);
    const tags = [...[...apps].map((card) => card.tags)];
    setFilters(["All", ...new Set(tags.flat())]);
    if (searchParams.get("filter")) {
      setSelectedFilter(searchParams.get("filter"));
    }
    if (searchParams.get("search")) {
      setSearchTerm(searchParams.get("search"));
    }
  }, [apps, searchParams]);

  useEffect(() => {
    let allCards = [...apps];

    if (selectedFilter && selectedFilter !== "All") {
      allCards = allCards.filter((card) => card.tags.includes(selectedFilter));
    }

    if (searchTerm !== "") {
      allCards = allCards.filter((card) =>
        card.title.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    setDiscoverCards(allCards);
  }, [selectedFilter, searchTerm, apps]);

  return (
    <div>
      <Box>
        <SearchAndFilter
          filters={filters}
          selectedFilter={selectedFilter}
          handleFilter={(filter) => setSelectedFilter(filter)}
          handleSearch={(event) => setSearchTerm(event.target.value)}
          search={searchTerm}
        />
        <Typography style={pageHeaderStyle} variant="h5">
          Apps from {organization?.name}
        </Typography>
        <Grid
          container
          sx={{
            marginTop: "10px",
            display: profileFlags.IS_ORGANIZATION_MEMBER ? "flex" : "none",
          }}
          spacing={{ xs: 1, md: 1 }}
          columns={{ xs: 1, sm: 8, md: 12 }}
        >
          {orgApps.map((card, index) => (
            <Grid
              item
              key={index}
              sx={{
                display: "flex",
                justifyContent: "center",
                flexDirection: "row",
                marginBottom: "20px",
              }}
              md={{
                flexDirection: "column",
              }}
            >
              <a href={`/app/${card.published_uuid}`}>
                <Card
                  sx={{
                    width: {
                      xs: "100%",
                      md: 200,
                    },
                    height: 120,
                    maxHeight: 150,
                    borderRadius: {
                      xs: "3px",
                      md: "10px",
                    },
                    position: "relative",
                    cursor: "pointer",
                    margin: "6px",
                    background: "white",
                    zIndex: 2,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexDirection: "column",
                  }}
                  className="discover-card"
                  elevation={5}
                >
                  <Typography
                    fontSize={18}
                    fontWeight={700}
                    color={"#183A58"}
                    sx={{
                      display: "-webkit-box",
                      WebkitBoxOrient: "vertical",
                      WebkitLineClamp: 2,
                      overflow: "hidden",
                      marginTop: "10px",
                    }}
                  >
                    {card?.name}
                  </Typography>
                  <CardActions sx={{ marginTop: "10px" }}>
                    <Chip
                      label={card.owner_email.split("@")[0]}
                      sx={{
                        height: "22px",
                        backgroundColor: "#CCC",
                        color: "black",
                        borderRadius: "10px",
                      }}
                    ></Chip>
                  </CardActions>
                </Card>
              </a>
            </Grid>
          ))}
        </Grid>
        <Typography style={pageHeaderStyle} variant="h5">
          Featured Apps
        </Typography>
        <Grid
          container
          sx={{ marginTop: "10px" }}
          spacing={{ xs: 1, md: 1 }}
          columns={{ xs: 1, sm: 8, md: 12 }}
        >
          {discoverCards.map((card, index) => (
            <Grid
              item
              key={index}
              sx={{
                position: "relative",
                display: "flex",
                justifyContent: "center",
              }}
            >
              <a
                href={`${window.location.protocol}//${window.location.host}${card.link}`}
              >
                <Card
                  sx={{
                    width: {
                      xs: "100%",
                      md: 228,
                    },
                    minWidth: {
                      md: 228,
                    },
                    height: 250,
                    maxHeight: 310,
                    borderRadius: {
                      xs: "3px",
                      md: "10px",
                    },
                    cursor: "pointer",
                    margin: "6px",
                    background: "white",
                    zIndex: 2,
                  }}
                  className="discover-card"
                  elevation={5}
                  onClick={() => (window.location.href = card.link)}
                >
                  <CardHeader
                    title={
                      <Typography
                        fontSize={20}
                        fontWeight={700}
                        color={"#183A58"}
                        sx={{
                          display: "-webkit-box",
                          WebkitBoxOrient: "vertical",
                          WebkitLineClamp: 2,
                          overflow: "hidden",
                          marginTop: "10px",
                        }}
                      >
                        {card?.title}
                      </Typography>
                    }
                    sx={{
                      paddingBottom: 0,
                    }}
                  ></CardHeader>
                  <CardContent
                    className="discover-card-content"
                    sx={{
                      padding: 1,
                      maxHeight: "60%",
                      maxWidth: "100%",
                      overflow: "scroll",
                      color: "#555",
                      fontSize: "16px",
                      lineHeight: "1.3em",
                    }}
                  >
                    {card?.description}
                  </CardContent>
                  <CardActions
                    sx={{
                      position: "absolute",
                      background: "#fff",
                      bottom: 15,
                      width: "90%",
                    }}
                  >
                    <Box sx={{ width: "100%" }}>
                      {card.tags.slice(0, 5).map((tag, index) => (
                        <Chip
                          key={index}
                          label={
                            tag.length > 10 ? tag.substr(0, 5) + "..." : tag
                          }
                          sx={{
                            height: "24px",
                            margin: "2px",
                            borderRadius: "10px",
                          }}
                        />
                      ))}
                    </Box>
                  </CardActions>
                </Card>
              </a>
            </Grid>
          ))}
        </Grid>
      </Box>
    </div>
  );
}
