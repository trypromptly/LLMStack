import React, { useState, useCallback } from "react";
import { Box, Button, Card, Chip, Collapse, Typography } from "@mui/material";
import {
  KeyboardArrowDownOutlined,
  KeyboardArrowUpOutlined,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { useRecoilValue } from "recoil";
import { storeCategoriesListState, isMobileState } from "../../data/atoms";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";

const AppIcon = styled("img")({
  width: 80,
  height: 80,
  margin: 0,
  borderRadius: 8,
});

const AppIconSmall = styled("img")({
  width: 35,
  height: 35,
  margin: 0,
  borderRadius: 4,
});

function StoreAppHeader({ name, icon, username, description, categories }) {
  const isMobile = useRecoilValue(isMobileState);
  const [expanded, setExpanded] = useState(!isMobile);
  const storeCategories = useRecoilValue(storeCategoriesListState);

  const findCategory = useCallback(
    (slug) => {
      return storeCategories.find((x) => x.slug === slug);
    },
    [storeCategories],
  );

  return (
    <Card
      sx={{
        backgroundColor: "#F3F5F8",
        cursor: "pointer",
        boxShadow: "none",
        display: "flex",
        flexDirection: "column",
        border: "1px solid #E8EBEE",
        borderRadius: "8px 8px 0 0",
        p: expanded ? 6 : 4,
        gap: 4,
        height: expanded ? "auto" : isMobile ? "40px" : "72px",
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          textAlign: "left",
          width: "100%",
        }}
      >
        {!expanded && (
          <Box
            sx={{
              display: "flex",
              width: "100%",
              gap: 4,
              alignItems: "center",
            }}
          >
            <AppIconSmall src={icon} alt={name} />
            <Box sx={{ alignSelf: "center", width: "100%" }}>
              <Box
                sx={{ width: "100%", display: "flex", alignItems: "center" }}
              >
                <Typography
                  component="h1"
                  color="#183A58"
                  sx={{ fontSize: "20px", lineHeight: "24px", fontWeight: 600 }}
                >
                  {name}
                </Typography>
                <Button sx={{ color: "#183A58", ml: "auto", mr: "-12px" }}>
                  {expanded ? (
                    <KeyboardArrowUpOutlined />
                  ) : (
                    <KeyboardArrowDownOutlined />
                  )}
                </Button>
              </Box>
            </Box>
          </Box>
        )}
        {expanded && (
          <Box
            sx={{
              display: "flex",
              width: "100%",
              gap: 4,
              alignItems: "center",
            }}
          >
            <AppIcon src={icon} alt={name} />
            <Box sx={{ width: "100%" }}>
              <Box
                sx={{ width: "100%", display: "flex", alignItems: "center" }}
              >
                <Typography
                  component="h1"
                  sx={{ fontSize: "20px", lineHeight: "24px", fontWeight: 600 }}
                >
                  {name}
                </Typography>
                <Button sx={{ ml: "auto", mr: "-20px" }}>
                  {expanded ? (
                    <KeyboardArrowUpOutlined />
                  ) : (
                    <KeyboardArrowDownOutlined />
                  )}
                </Button>
              </Box>
              <Typography>
                by&nbsp;
                <Typography color="corral.main" sx={{ display: "inline" }}>
                  {username}
                </Typography>
              </Typography>
              <Box sx={{ mt: 1, mb: 1, ml: -0.4 }}>
                {categories &&
                  categories.map((category) => (
                    <Chip
                      label={findCategory(category)?.name || category}
                      size="small"
                      key={category}
                      sx={{
                        borderRadius: 2,
                        padding: "4px, 8px, 4px, 8px",
                        backgroundColor: "#FFF",
                        border: 1,
                        color: "#183A58",
                        borderColor: "gray.main",
                      }}
                    />
                  ))}
              </Box>
            </Box>
          </Box>
        )}
      </Box>
      <Box
        sx={{
          textAlign: "left",
          lineHeight: "1.6",
          color: "#183a58",
          "& p": {
            mt: 0,
            ml: 0,
            marginBlockEnd: 0,
          },
        }}
      >
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <LayoutRenderer>{description}</LayoutRenderer>
        </Collapse>
      </Box>
    </Card>
  );
}

export default StoreAppHeader;
