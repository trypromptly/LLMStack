import {
  Button,
  Dialog,
  DialogActions,
  DialogTitle,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { axios } from "../../data/axios";
import AddAppRunScheduleConfigForm from "./AddAppRunScheduleConfigForm";
import InputDataTable from "./InputDataTable";

export default function AddAppRunScheduleModal(props) {
  const [columns, setColumns] = useState([]);
  const [configuration, setConfiguration] = useState({});
  const [appRunData, setAppRunData] = useState([]);

  useEffect(() => {
    if (configuration?.appDetail) {
      const columnFields = configuration?.appDetail.data.input_fields.map(
        (entry) => {
          return {
            field: entry.name,
            headerName: entry.title,
            width: entry.type === "text" ? 300 : 200,
            disableColumnMenu: true,
            sortable: false,
            editable: true,
            flex: 1,
          };
        },
      );
      setColumns(columnFields);
      setAppRunData([]);
    }
  }, [configuration]);

  return (
    <Dialog open={true} maxWidth="lg" fullWidth onClose={props.onClose}>
      <DialogTitle>Schedule App Run Job</DialogTitle>
      <Grid>
        <Grid item xs={12}>
          <Stack sx={{ alignItems: "start", margin: "5px" }}>
            <AddAppRunScheduleConfigForm
              onChange={(formData) => {
                setConfiguration(formData);
              }}
              value={configuration}
            />
          </Stack>
        </Grid>
        {configuration?.frequency && configuration?.job_name && (
          <Grid item xs={12} sx={{ margin: "10px" }}>
            <Stack sx={{ alignItems: "start", margin: "5px" }}>
              <Typography variant="h7" sx={{ marginLeft: "2px" }}>
                Batch Input to the App
              </Typography>
              <Divider />
              <Typography variant="caption" sx={{ marginLeft: "2px" }}>
                Enter the input data for the app run. You can also upload a CSV
                file with the input data. Make sure the column names match the
                input fields of the app.
              </Typography>
              <br />
              {configuration?.appDetail ? (
                <InputDataTable
                  columnData={columns}
                  rowData={appRunData}
                  onChange={(newRowData) => {
                    setAppRunData(newRowData);
                  }}
                />
              ) : (
                <strong>Please select an application.</strong>
              )}
            </Stack>
          </Grid>
        )}
      </Grid>
      <DialogActions>
        <Button variant="contained" onClick={props.onClose}>
          Cancel
        </Button>
        <Button
          variant="contained"
          color="primary"
          disabled={
            !(
              configuration?.appDetail?.uuid &&
              configuration?.frequencyObj &&
              appRunData &&
              appRunData.length > 0
            )
          }
          onClick={() => {
            const appFormData = appRunData.map((entry) => {
              const newEntry = { ...entry };
              delete newEntry._id;
              delete newEntry._isNew;
              return newEntry;
            });

            axios()
              .post("/api/jobs/app_run", {
                job_name: configuration?.job_name,
                app_uuid: configuration?.appDetail?.uuid,
                frequency: configuration?.frequencyObj,
                use_session: configuration?.use_session,
                batch_size: configuration?.batch_size,
                app_run_data: appFormData,
              })
              .then((response) => {
                enqueueSnackbar("Successfully Scheduled App Run", {
                  variant: "success",
                });
                window.location.href = "/jobs";
              })
              .catch((error) => {
                if (error.response?.data?.message) {
                  enqueueSnackbar(error.response.data.message, {
                    variant: "error",
                  });
                }
              });
          }}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}
