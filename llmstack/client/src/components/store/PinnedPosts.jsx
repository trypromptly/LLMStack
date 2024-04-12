import { useState, useEffect } from "react";
import { Button, Divider, Stack, Typography } from "@mui/material";
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
          <AssetRenderer url={share.cover_image} type="image" />
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
            justifyContent: "space-between",
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

  useEffect(() => {
    // TODO: handle pagination
    axios()
      .get(`/api/profiles/${username}/posts`)
      .then((response) => {
        setPosts(response.data?.results || []);
      })
      .catch((error) => {
        console.error(error);
      });
  }, [username]);

  return (
    <Grid container gap={4} sx={{ justifyContent: "space-around" }}>
      {posts.length === 0 ? (
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
