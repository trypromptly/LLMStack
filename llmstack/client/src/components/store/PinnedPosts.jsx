import { useState, useEffect } from "react";
import {
  Button,
  CircularProgress,
  Divider,
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
    <Grid>
      <Stack
        sx={{
          maxWidth: "300px",
          minWidth: "200px",
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
    </Grid>
  );
};

const PinnedPosts = ({ username }) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: handle pagination
    setLoading(true);
    axios()
      .get(`/api/profiles/${username}/posts`)
      .then((response) => {
        setPosts(response.data?.results || []);
      })
      .catch((error) => {
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [username]);

  return (
    <Grid container gap={4} sx={{ justifyContent: "space-around" }}>
      {loading && <CircularProgress />}
      {posts.length === 0 && !loading ? (
        <Grid>
          <Typography variant="body1">No pinned posts</Typography>
        </Grid>
      ) : (
        posts.map((post, index) => (
          <Post key={index} post={post} username={username} />
        ))
      )}
    </Grid>
  );
};

export default PinnedPosts;
