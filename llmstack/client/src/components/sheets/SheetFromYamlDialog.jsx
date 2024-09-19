import { useCallback, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
} from "@mui/material";
import yaml from "js-yaml";
import { useNavigate } from "react-router-dom";
import { axios } from "../../data/axios";
import { enqueueSnackbar } from "notistack";

function SheetFromYamlDialog({ open, onClose, onImport }) {
  const [yamlData, setYamlData] = useState("");
  const navigate = useNavigate();

  const handleImport = useCallback(() => {
    try {
      const schema = yaml.load(yamlData);
      axios()
        .post("/api/sheets", schema)
        .then((response) => {
          onImport(response.data);
          onClose();

          navigate(`/sheets/${response.data.uuid}`);
        });
    } catch (error) {
      console.error(error);
      enqueueSnackbar("Error importing sheet", { variant: "error" });
    }
  }, [onImport, onClose, navigate, yamlData]);

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <DialogTitle>Import Sheet</DialogTitle>
      <DialogContent sx={{ paddingTop: 2 }}>
        <Typography variant="body2">
          Paste your sheet schema in YAML below to import your sheet.
        </Typography>
        <TextField
          label="YAML"
          multiline
          rows={10}
          fullWidth
          value={yamlData}
          sx={{ marginTop: 4 }}
          onChange={(e) => setYamlData(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleImport} variant="contained">
          Import
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default SheetFromYamlDialog;
