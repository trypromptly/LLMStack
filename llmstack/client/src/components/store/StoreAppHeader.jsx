import React, { useState, useCallback } from "react";
import { Box, Button, Card, Chip, Collapse, Typography } from "@mui/material";
import {
  KeyboardDoubleArrowDownOutlined,
  KeyboardDoubleArrowUpOutlined,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { useRecoilValue } from "recoil";
import { storeCategoriesListState } from "../../data/atoms";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";

const AppIcon = styled("img")({
  width: 80,
  height: 80,
  margin: "1em 0.5em",
  borderRadius: 2,
});

function StoreAppHeader({ name, icon, username, description, categories }) {
  const [expandedDescription, setExpandedDescription] = useState(false);
  const storeCategories = useRecoilValue(storeCategoriesListState);

  const handleExpand = () => {
    setExpandedDescription(!expandedDescription);
  };

  const findCategory = useCallback(
    (slug) => {
      return storeCategories.find((x) => x.slug === slug);
    },
    [storeCategories],
  );

  return (
    <Card sx={{ backgroundColor: "#edeff7" }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          textAlign: "left",
          pl: 1,
          pb: 1,
        }}
      >
        <AppIcon src={icon} alt={name} />
        <Box sx={{ padding: 2 }}>
          <Typography
            component="div"
            color="text.primary"
            sx={{ fontSize: 24, fontWeight: 600 }}
          >
            {name}
          </Typography>
          <Typography color="text.secondary">
            by <b>{username}</b>
          </Typography>
          <Box sx={{ mt: 1, mb: 1 }}>
            {categories &&
              categories.map((category) => (
                <Chip
                  label={findCategory(category)?.name || category}
                  size="small"
                  key={category}
                />
              ))}
          </Box>
        </Box>
      </Box>
      <Box sx={{ textAlign: "left", ml: 2, mb: 2 }}>
        <Collapse in={expandedDescription} timeout="auto" unmountOnExit>
          <LayoutRenderer>{description}</LayoutRenderer>
        </Collapse>
        <Collapse in={!expandedDescription} timeout="auto" unmountOnExit>
          <Typography>{description.substring(0, 200)}</Typography>
        </Collapse>
        {description.length > 200 && (
          <Button
            onClick={handleExpand}
            size="small"
            sx={{
              textTransform: "none",
              fontSize: "0.8em",
              "& .MuiButton-startIcon": {
                marginRight: "0.5em",
              },
            }}
            startIcon={
              expandedDescription ? (
                <KeyboardDoubleArrowUpOutlined />
              ) : (
                <KeyboardDoubleArrowDownOutlined />
              )
            }
          >
            {expandedDescription ? "Show Less" : "View More"}
          </Button>
        )}
      </Box>
    </Card>
  );
}

export default StoreAppHeader;
