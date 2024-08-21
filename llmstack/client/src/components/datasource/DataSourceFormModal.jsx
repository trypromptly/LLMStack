import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Typography,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { useState, useMemo, useEffect } from "react";

import { axios } from "../../data/axios";
import ThemedJsonForm from "../ThemedJsonForm";

const SOURCE_REFRESH_SCHEMA = {
  type: "object",
  properties: {
    refresh_interval: {
      type: "string",
      title: "Refresh Interval",
      description: "The interval at which the data source should be refreshed.",
      default: "None",
      enum: ["None", "Daily", "Weekly", "Monthly"],
    },
  },
};
const SOURCE_REFRESH_UI_SCHEMA = {
  refresh_interval: {
    "ui:widget": "radio",
    "ui:options": {
      inline: true,
    },
  },
};

export function DatasourceFormModal({ open, cancelCb, submitCb, datasource }) {
  const [refreshData, setRefreshData] = useState({
    refresh_interval: datasource?.refresh_interval || "None",
  });

  return (
    <Dialog open={open} onClose={cancelCb} sx={{ zIndex: 900 }}>
      <DialogTitle>Datasource Form</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <TextField
            label="Data Source Name"
            defaultValue={datasource?.name}
            inti
            disabled
            size="small"
            style={{ width: "100%", marginTop: "6px" }}
          />
          {datasource?.pipeline?.source?.slug && (
            <Accordion defaultExpanded={true}>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="refresh-content"
                id="refresh-header"
              >
                <Typography>Refresh Configuration</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {
                  <ThemedJsonForm
                    schema={SOURCE_REFRESH_SCHEMA}
                    validator={validator}
                    uiSchema={{
                      ...(SOURCE_REFRESH_UI_SCHEMA || {}),
                      ...{
                        "ui:submitButtonOptions": {
                          norender: true,
                        },
                        "ui:DescriptionFieldTemplate": () => null,
                        "ui:TitleFieldTemplate": () => null,
                      },
                    }}
                    formData={refreshData || {}}
                    onChange={({ formData }) => {
                      setRefreshData(formData);
                    }}
                    disableAdvanced={true}
                  />
                }
              </AccordionDetails>
            </Accordion>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={cancelCb}>Cancel</Button>,
        <Button
          variant="contained"
          onClick={() => {
            axios()
              .patch(`/api/datasources/${datasource.uuid}`, refreshData)
              .then((response) => {
                submitCb();
              });
          }}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}
