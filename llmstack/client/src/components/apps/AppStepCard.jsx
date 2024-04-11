import { EditOutlined } from "@mui/icons-material";
import {
  Card,
  CardHeader,
  Popover,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { ProviderIcon } from "./ProviderIcon";

export default function AppStepCard({
  icon,
  title,
  description,
  setDescription,
  stepNumber,
  activeStep,
  setActiveStep,
  errors = [],
  action = null,
  children,
}) {
  const isActive = activeStep === stepNumber;
  const isDescriptionEditable =
    stepNumber > 1 && title !== "Application Output";
  const [errorAnchorEl, setErrorAnchorEl] = useState(null);
  const [showDescriptionEditor, setShowDescriptionEditor] = useState(false);
  const [descriptionInput, setDescriptionInput] = useState(description);

  return (
    <Card
      sx={{
        width: "100%",
        marginTop: 10,
        textAlign: "left",
        maxWidth: "900px",
        margin: "auto",
        cursor: isActive ? "default" : "pointer",
        boxShadow: isActive ? "0 0 10px #449" : "default",
        "&:hover": {
          boxShadow: isActive ? "default" : "0 0 10px #666",
        },
      }}
      elevation={2}
    >
      <CardHeader
        title={
          <Typography
            style={{
              fontSize: "16px",
              fontWeight: 600,
              fontFamily: "Lato, sans-serif",
              color: isActive ? "#fff" : "#000",
            }}
          >
            {stepNumber}. {title}
            {errors.length > 0 && (
              <span
                style={{
                  color: "red",
                  float: "right",
                }}
                onMouseEnter={(event) => setErrorAnchorEl(event.currentTarget)}
                onMouseLeave={() => setErrorAnchorEl(null)}
              >
                [{errors.length} error{errors.length > 1 ? "s" : ""}]
              </span>
            )}
            <Popover
              id="mouse-over-popover"
              sx={{
                pointerEvents: "none",
                "& .MuiPopover-paper": {
                  padding: "10px",
                },
                "& .MuiPopover-paper ol": {
                  margin: 0,
                  paddingLeft: "15px",
                },
                "& .MuiPopover-paper li": {
                  fontSize: "12px",
                },
              }}
              open={Boolean(errorAnchorEl)}
              anchorEl={errorAnchorEl}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "left",
              }}
              transformOrigin={{
                vertical: "top",
                horizontal: "left",
              }}
              onClose={() => setErrorAnchorEl(null)}
              disableRestoreFocus
            >
              <ol>
                {errors.map((error, index) => (
                  <li key={index}>{error.message}</li>
                ))}
              </ol>
            </Popover>
          </Typography>
        }
        subheader={
          showDescriptionEditor && isDescriptionEditable ? (
            <TextField
              id="standard-basic"
              variant="standard"
              value={descriptionInput}
              onChange={(e) => {
                setDescriptionInput(e.target.value);
              }}
              sx={{
                width: "100%",
                ".MuiInputBase-input": {
                  fontSize: "14px",
                  padding: "0 0 2px 0",
                  fontFamily: "Lato, sans-serif",
                  color: "#fff",
                },
              }}
              onBlur={() => setShowDescriptionEditor(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  setDescription(e.target.value);
                  setShowDescriptionEditor(false);
                }
              }}
              inputRef={(input) => input && input.focus()}
              focused={showDescriptionEditor}
            />
          ) : (
            <Typography
              variant="subtitle2"
              style={{
                fontSize: "14px",
                fontFamily: "Lato, sans-serif",
                color: isActive ? "#ccc" : "#6b6b6b",
              }}
              onClick={() => setShowDescriptionEditor(true)}
            >
              {descriptionInput}{" "}
              {isDescriptionEditable && (
                <EditOutlined style={{ fontSize: "14px" }} />
              )}
            </Typography>
          )
        }
        avatar={
          typeof icon === "string" ? (
            <ProviderIcon providerSlug={icon} isActive={isActive} />
          ) : (
            icon
          )
        }
        sx={{
          backgroundColor: isActive ? "#2e4658" : "#dce1e5",
          border: isActive ? "inherit" : "solid 1px #999",
          "& .MuiCardHeader-title": {
            fontSize: "1.1rem",
            color: isActive ? "#fff" : "#000",
          },
          "& .MuiCardHeader-subheader": {
            fontSize: "0.8rem",
            color: isActive ? "#fff" : "#000",
          },
        }}
        action={action}
        onClick={() => setActiveStep(stepNumber)}
      />
      {isActive && children}
    </Card>
  );
}
