import React, { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  Button,
  CircularProgress,
} from "@mui/material";
import { axios } from "../../data/axios";
import moment from "moment";

const PreviousRunsModal = ({ open, onClose, sheetUuid }) => {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPreviousRuns = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios().get(`/api/sheets/${sheetUuid}/runs`);
      setRuns(response.data);
    } catch (error) {
      console.error("Error fetching previous runs:", error);
    } finally {
      setLoading(false);
    }
  }, [sheetUuid]);

  const handleDownload = (runId) => {
    window.open(`/api/sheets/${sheetUuid}/runs/${runId}/download`, "_blank");
  };

  useEffect(() => {
    if (open) {
      fetchPreviousRuns();
    }
  }, [open, fetchPreviousRuns]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Previous Runs</DialogTitle>
      <DialogContent>
        {loading ? (
          <CircularProgress />
        ) : (
          <List>
            {runs.map((run) => (
              <ListItem key={run.uuid} divider>
                <ListItemText
                  primary={`Run ${run.uuid}`}
                  secondary={`Created ${moment(run.created_at).fromNow()}`}
                />
                <Button
                  variant="outlined"
                  onClick={() => handleDownload(run.uuid)}
                >
                  Download
                </Button>
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default PreviousRunsModal;
