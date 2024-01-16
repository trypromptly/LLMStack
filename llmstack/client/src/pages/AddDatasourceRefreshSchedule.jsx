import { Button, Divider, Grid, Stack, Typography } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { enqueueSnackbar } from "notistack";
import { useEffect, useState } from "react";
import AddDataRefreshScheduleConfigForm from "../components/schedule/AddDataRefreshScheduleConfigForm";
import { axios } from "../data/axios";

export default function AddDatasourceRefreshSchedule(props) {
  const [configuration, setConfiguration] = useState({});
  const [dataSourceEntries, setDataSourceEntries] = useState([]);
  const [dataSourceEntriesSelected, setDataSourceEntriesSelected] = useState(
    [],
  );

  useEffect(() => {
    if (configuration?.datasource) {
      axios()
        .get(`/api/datasources/${configuration?.datasource}/entries`)
        .then((response) => {
          setDataSourceEntries((prev) => {
            const dataSourceEntriesWithSyncSupport = response.data.filter(
              (entry) =>
                entry.sync_config &&
                entry.status === "READY" &&
                entry.config.document_ids.length > 0,
            );
            return [...dataSourceEntriesWithSyncSupport];
          });
        })
        .catch((error) => {
          if (error.response?.data?.message) {
            enqueueSnackbar(error.response.data.message, {
              variant: "error",
            });
          }
        });
    } else {
      setDataSourceEntries([]);
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
          <AddDataRefreshScheduleConfigForm
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
            Datasource Entries
          </Typography>
          <Divider />
          {configuration?.datasource ? (
            <DataGrid
              checkboxSelection
              columns={[
                { field: "name", headerName: "Name", width: 500 },
                { field: "size", headerName: "Size", width: 100 },
              ]}
              initialState={{
                pagination: {
                  paginationModel: {
                    pageSize: 10,
                  },
                },
              }}
              rows={dataSourceEntries.map((entry) => {
                return {
                  id: entry.uuid,
                  name: entry.name,
                  size: entry.size,
                };
              })}
              pageSizeOptions={[10]}
              disableRowSelectionOnClick
              sx={{ width: "100%" }}
              rowSelectionModel={dataSourceEntriesSelected}
              onRowSelectionModelChange={(newSelection) => {
                setDataSourceEntriesSelected(newSelection);
              }}
            ></DataGrid>
          ) : (
            <strong>Please Select a Data Source</strong>
          )}
        </Stack>
      </Grid>
      <Grid item xs={12} sx={{ height: "10%" }}>
        <Button
          variant="contained"
          color="primary"
          disabled={
            !configuration?.frequencyObj ||
            dataSourceEntriesSelected.length === 0
          }
          onClick={() => {
            axios()
              .post("/api/jobs/datasource_refresh", {
                job_name: configuration?.job_name,
                app_uuid: configuration?.appDetail?.uuid,
                frequency: configuration?.frequencyObj,
                datasource_entries: dataSourceEntriesSelected,
              })
              .then((response) => {
                enqueueSnackbar("Successfully Scheduled Datasource refresh", {
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
