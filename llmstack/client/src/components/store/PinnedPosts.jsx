import { useEffect, useRef, useState } from "react";
import {
  Button,
  CircularProgress,
  Divider,
  ImageList,
  ImageListItem,
  Stack,
  Typography,
} from "@mui/material";
import ShareIcon from "@mui/icons-material/Share";
import AppShortcutIcon from "@mui/icons-material/AppShortcut";
import Grid from "@mui/material/Unstable_Grid2";
import { axios } from "../../data/axios";
import { AssetRenderer } from "../apps/renderer/AssetRenderer";

const Post = ({ post, username }) => {
  const { share } = post;

  return (
    <ImageListItem key={share}>
      <Stack
        sx={{
          display: "inline-block",
          borderRadius: 2,
          border: "solid 1px #eee",
          padding: 2,
          textAlign: "left",
          cursor: "pointer",
          ":hover": {
            backgroundColor: "#f9f9f9",
          },
        }}
        gap={1}
        onClick={() => {
          window.location.href = `/u/${username}/${share.slug}`;
        }}
      >
        <Typography
          variant="h5"
          sx={{ margin: "10px 2px", color: "primary.main" }}
        >
          {share.title}
        </Typography>
        {share.cover_image ? (
          <AssetRenderer
            url={share.cover_image}
            type="image"
            noDownload
            styleJson={{ boxShadow: "none", border: "solid 1px #eee" }}
          />
        ) : (
          <Divider />
        )}

        <Typography
          variant="body1"
          sx={{ margin: 1, color: "#647b8f", paddingTop: 2 }}
        >
          {share.description}
        </Typography>
        <Stack
          direction={"row"}
          gap={2}
          sx={{
            justifyContent: "space-around",
            paddingTop: 4,
            paddingBottom: 2,
          }}
        >
          <Button
            size="small"
            href={`/s/${share.code}`}
            startIcon={<ShareIcon />}
            sx={{ textTransform: "none" }}
          >
            View Share
          </Button>
          <Button
            size="small"
            href={`/a/${share.store_app_slug}`}
            startIcon={<AppShortcutIcon />}
          >
            Go to App
          </Button>
        </Stack>
      </Stack>
    </ImageListItem>
  );
};

const PinnedPosts = ({ username }) => {
  const [posts, setPosts] = useState([]);
  const [nextPage, setNextPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cols, setCols] = useState(1);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const width = containerRef.current.clientWidth;
        const newCols = Math.floor(width / 220);
        setCols(newCols);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [containerRef]);

  const fetchNextPage = (page) => {
    setLoading(true);
    axios()
      .get(page)
      .then((response) => {
        setPosts([...posts, ...response.data.results]);
        if (response?.data?.next) {
          setNextPage(
            response.data.next?.replaceAll(
              response.data.next?.split("/api/")[0],
              "",
            ),
          );
        } else {
          setNextPage(null);
        }
      })
      .catch((error) => {
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    // TODO: handle pagination
    const url = `/api/profiles/${username}/posts`;
    fetchNextPage(url);
  }, [username]);

  return (
    <Grid
      container
      gap={4}
      sx={{ justifyContent: "space-around", paddingTop: 0 }}
      ref={containerRef}
      columns={cols}
    >
      {loading && <CircularProgress />}
      <ImageList
        variant="masonry"
        cols={cols}
        gap={12}
        rowHeight={"auto"}
        sx={{ marginTop: 0 }}
      >
        {posts.length === 0 && !loading ? (
          <Grid>
            <Typography variant="body1">No pinned posts</Typography>
          </Grid>
        ) : (
          posts.map((post, index) => (
            <Post key={index} post={post} username={username} />
          ))
        )}
      </ImageList>
      {nextPage && (
        <Button
          variant="outlined"
          onClick={() => fetchNextPage(nextPage)}
          sx={{ margin: "20px 0" }}
        >
          Load More
        </Button>
      )}
    </Grid>
  );
};

export default PinnedPosts;
