import { useEffect, useState } from "react";
import { enqueueSnackbar } from "notistack";

import { Grid, Divider, Typography, Button, Stack } from "@mui/material";
import AddAppRunScheduleConfigForm from "../components/schedule/AddAppRunScheduleConfigForm";
import InputDataTable from "../components/schedule/InputDataTable";
import { axios } from "../data/axios";

export default function AddAppRunSchedule(props) {
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
          };
        },
      );
      setColumns(columnFields);
      setAppRunData([]);
    }
  }, [configuration]);

  return (
    <Grid container sx={{ height: "100vh" }}>
      <Grid item xs={12} sx={{ height: "45%" }}>
        <Stack sx={{ alignItems: "start", margin: "5px" }}>
          <Typography variant="h6" sx={{ marginLeft: "2px" }}>
            Configuration
          </Typography>
          <Divider />
          <AddAppRunScheduleConfigForm
            onChange={(formData) => {
              setConfiguration(formData);
            }}
            value={configuration}
          />
        </Stack>
      </Grid>
      <Grid item xs={12} sx={{ height: "45%" }}>
        <Stack sx={{ alignItems: "start", margin: "5px" }}>
          <Typography variant="h6" sx={{ marginLeft: "2px" }}>
            Input
          </Typography>
          <Divider />
          {configuration?.appDetail ? (
            <InputDataTable
              columnData={columns}
              rowData={appRunData}
              onChange={(newRowData) => {
                setAppRunData(newRowData);
              }}
            />
          ) : (
            <strong>Please Select And Application</strong>
          )}
        </Stack>
      </Grid>
      <Grid item xs={12} sx={{ height: "10%" }}>
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
      </Grid>
    </Grid>
  );
}
