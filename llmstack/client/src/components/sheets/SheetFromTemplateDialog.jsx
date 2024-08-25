import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { axios } from "../../data/axios";

export function SheetFromTemplateDialog({
  open,
  setOpen,
  sheet,
  setSheet,
  sheetId,
  setSheetId,
}) {
  const [sheetName, setSheetName] = useState(sheet?.name || "Untitled");
  const [sheetDescription, setSheetDescription] = useState(
    sheet?.description || "",
  );
  const navigate = useNavigate();

  const handleClose = () => {
    setOpen(false);
  };

  const handleSave = () => {
    const payload = {
      name: sheetName,
      description: sheetDescription,
    };
    const method = sheetId ? "patch" : "post";
    const url = sheetId ? `/api/sheets/${sheetId}` : "/api/sheets";

    axios()
      [method](url, payload)
      .then((response) => {
        setSheetId(response.data.uuid);
        setSheet(response.data);
        setOpen(false);
        if (!sheetId) {
          navigate(`/sheets/${response.data.uuid}`);
        }
      });
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth>
      <DialogTitle>{sheetId ? "Edit Sheet" : "Create Sheet"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Typography variant="body1" sx={{ paddingBottom: 4 }}>
            {sheetId
              ? "Edit your sheet details below."
              : "Create a new sheet by filling out the details below."}
          </Typography>
          <TextField
            label="Sheet Name"
            value={sheetName}
            variant="outlined"
            onChange={(e) => setSheetName(e.target.value)}
          />
          <TextField
            label="Description"
            value={sheetDescription}
            multiline
            rows={4}
            placeholder="Enter a description for your sheet"
            helperText="This is optional description of your sheet. It will help you and others understand what this sheet is for."
            onChange={(e) => setSheetDescription(e.target.value)}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          {sheetId ? "Save Changes" : "Create Sheet"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
