import React, { useState, useCallback } from "react";
import {
  Box,
  Button,
  Card,
  Chip,
  Collapse,
  IconButton,
  Typography,
} from "@mui/material";
import {
  IosShareOutlined,
  KeyboardArrowDownOutlined,
  KeyboardArrowUpOutlined,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { useRecoilValue } from "recoil";
import { useLocation } from "react-router-dom";
import { storeCategoriesListState, isMobileState } from "../../data/atoms";
import { isUUID } from "../../data/utils";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
import ShareModal from "./ShareModal";
import promptlyIcon from "../../assets/promptly-icon.png";
import llmstackIcon from "../../assets/llmstack-icon.png";

let defaultIcon = llmstackIcon;
if (process.env.REACT_APP_SITE_NAME === "Promptly") {
  defaultIcon = promptlyIcon;
}

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

function StoreAppHeader({
  name,
  icon,
  username,
  description,
  categories,
  appStoreUuid,
  appTypeSlug,
  shareHeader = false,
}) {
  const isMobile = useRecoilValue(isMobileState);
  const [expanded, setExpanded] = useState(!shareHeader && !isMobile);
  const [showShareModal, setShowShareModal] = useState(false);
  const storeCategories = useRecoilValue(storeCategoriesListState);
  const location = useLocation();

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
      <ShareModal
        open={showShareModal}
        onClose={() => setShowShareModal(false)}
        appTypeSlug={appTypeSlug}
        appStoreUuid={appStoreUuid}
      />
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
            <AppIconSmall src={icon || defaultIcon} alt={name} />
            <Box sx={{ alignSelf: "center", width: "100%" }}>
              <Box
                sx={{ width: "100%", display: "flex", alignItems: "center" }}
              >
                <Typography
                  component="h1"
                  color="#183A58"
                  sx={{
                    fontSize: "20px",
                    lineHeight: "24px",
                    fontWeight: 600,
                  }}
                >
                  {name}
                </Typography>
                {shareHeader &&
                  (expanded ? (
                    <KeyboardArrowUpOutlined />
                  ) : (
                    <KeyboardArrowDownOutlined />
                  ))}
                {!shareHeader && (
                  <IconButton
                    sx={{
                      color: "#FFF",
                      ml: "auto",
                      mr: isMobile ? "-4px" : "0px",
                      backgroundColor: "primary.main",
                      ":hover": {
                        backgroundColor: "primary.dark",
                      },
                      borderRadius: "8px",
                    }}
                    onClose={() => setShowShareModal(true)}
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowShareModal(true);
                    }}
                  >
                    <IosShareOutlined fontSize="small" variant="contained" />
                  </IconButton>
                )}
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
            <AppIcon src={icon || defaultIcon} alt={name} />
            <Box sx={{ width: "100%" }}>
              <Box
                sx={{ width: "100%", display: "flex", alignItems: "center" }}
              >
                <Typography
                  component="h1"
                  sx={{
                    fontSize: "20px",
                    lineHeight: "24px",
                    fontWeight: 600,
                  }}
                >
                  {name}
                </Typography>
                {shareHeader &&
                  (expanded ? (
                    <KeyboardArrowUpOutlined />
                  ) : (
                    <KeyboardArrowDownOutlined />
                  ))}
                {!shareHeader &&
                  (isMobile ? (
                    <IconButton
                      sx={{
                        color: "#FFF",
                        ml: "auto",
                        mr: "-4px",
                        backgroundColor: "primary.main",
                        ":hover": {
                          backgroundColor: "primary.dark",
                        },
                        borderRadius: "8px",
                      }}
                      onClose={() => setShowShareModal(true)}
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowShareModal(true);
                      }}
                    >
                      <IosShareOutlined fontSize="small" variant="contained" />
                    </IconButton>
                  ) : (
                    <Button
                      variant="contained"
                      sx={{ ml: "auto", mr: "-4px", color: "#FFF" }}
                      startIcon={<IosShareOutlined fontSize="small" />}
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowShareModal(true);
                      }}
                    >
                      Share
                    </Button>
                  ))}
              </Box>
              {isUUID(location.pathname.split("/")[2]) && (
                <>
                  <span style={{ color: "gray" }}>by&nbsp;</span>

                  <Typography color="corral.main" sx={{ display: "inline" }}>
                    {username}
                  </Typography>
                </>
              )}
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
      {description && (
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
      )}
    </Card>
  );
}

export default StoreAppHeader;
