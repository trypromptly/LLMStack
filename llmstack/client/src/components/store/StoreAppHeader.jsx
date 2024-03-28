import React, { useState, useCallback } from "react";
import { Box, Button, Card, Chip, Collapse, Typography } from "@mui/material";
import {
  KeyboardDoubleArrowDownOutlined,
  KeyboardDoubleArrowUpOutlined,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { useRecoilValue } from "recoil";
import { storeCategoriesListState, isMobileState } from "../../data/atoms";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";

const AppIcon = styled("img")({
  width: 80,
  height: 80,
  margin: "1em 0.5em",
  borderRadius: 8,
});

const AppIconSmall = styled("img")({
  width: 35,
  height: 35,
  margin: "0.5em 0.2em 0.5em 0.5em",
  borderRadius: 4,
});

function StoreAppHeader({ name, icon, username, description, categories }) {
  const isMobile = useRecoilValue(isMobileState);
  const [expanded, setExpanded] = useState(!isMobile);
  const [expandedDescription, setExpandedDescription] = useState(false);
  const storeCategories = useRecoilValue(storeCategoriesListState);

  const handleExpand = (e) => {
    e.stopPropagation();
    setExpandedDescription(!expandedDescription);
  };

  const findCategory = useCallback(
    (slug) => {
      return storeCategories.find((x) => x.slug === slug);
    },
    [storeCategories],
  );

  return (
    <Card
      sx={{
        backgroundColor: "#F4F6F8",
        cursor: "pointer",
        boxShadow: "none",
        borderBottom: "1px solid #ddd",
        borderRadius: "8px 8px 0 0",
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          textAlign: "left",
          pl: 1,
        }}
      >
        {!expanded && (
          <Box sx={{ display: "flex", pt: 1 }}>
            <AppIconSmall src={icon} alt={name} />
            <Box sx={{ padding: 2, alignSelf: "center" }}>
              <Typography
                component="div"
                color="text.primary"
                sx={{ fontSize: 22, fontWeight: 600 }}
              >
                {name}
              </Typography>
            </Box>
          </Box>
        )}
        {expanded && (
          <Box sx={{ display: "flex" }}>
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
        )}
      </Box>
      <Box sx={{ textAlign: "left", ml: 2, mb: 2 }}>
        <Collapse
          in={expanded && expandedDescription}
          timeout="auto"
          unmountOnExit
        >
          <LayoutRenderer>{description}</LayoutRenderer>
        </Collapse>
        <Collapse
          in={expanded && !expandedDescription}
          timeout="auto"
          unmountOnExit
        >
          <Typography>{description.substring(0, 200)}</Typography>
        </Collapse>
        {expanded && description.length > 200 && (
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
