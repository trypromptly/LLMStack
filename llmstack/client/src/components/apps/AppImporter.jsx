import React, { useState } from "react";
import {
  Button,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";

export function AppImportModal(props) {
  const { isOpen, setIsOpen } = props;
  const [isLoading, setIsLoading] = useState(false);
  const [yaml, setYaml] = useState("");

  const handleImport = () => {
    setIsLoading(true);
    axios()
      .post("/api/apps", yaml, {
        headers: { "Content-Type": "application/yaml" },
      })
      .then((res) => {
        enqueueSnackbar("App imported successfully", {
          variant: "success",
        });
      })
      .finally(() => {
        setYaml("");
        setIsLoading(false);
        setIsOpen(false);
        window.location.reload();
      });
  };

  return (
    <Dialog open={isOpen} onCancel={() => setIsOpen(false)} fullWidth>
      <DialogTitle>Import App</DialogTitle>
      <DialogContent>
        <Typography variant="body2" gutterBottom>
          Paste the YAML of the app you want to import here.
        </Typography>
        <br />
        {isLoading && (
          <div style={{ textAlign: "center" }}>
            <CircularProgress />
          </div>
        )}
        <TextField
          multiline
          rows={4}
          fullWidth
          label="YAML"
          value={yaml}
          onChange={(e) => setYaml(e.target.value)}
          disabled={isLoading}
        />
      </DialogContent>
      <DialogActions>
        <Button
          key="cancel"
          onClick={() => {
            setYaml("");
            setIsOpen(false);
          }}
          sx={{ textTransform: "none" }}
        >
          Cancel
        </Button>
        <Button variant="contained" color="primary" onClick={handleImport}>
          Import
        </Button>
      </DialogActions>
    </Dialog>
  );
}
