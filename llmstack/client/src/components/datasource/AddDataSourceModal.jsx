import { useState } from "react";
import {
  Button,
  ButtonGroup,
  TextField,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import { useRecoilValue, useRecoilState } from "recoil";
import { dataSourcesState, dataSourceTypesState } from "../../data/atoms";
import { axios } from "../../data/axios";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { useReloadDataSourceEntries } from "../../data/init";
import { enqueueSnackbar } from "notistack";

export function AddDataSourceModal({
  open,
  handleCancelCb,
  dataSourceAddedCb,
  modalTitle = "Add New Data Source",
  datasource = null,
}) {
  const dataSourceTypes = useRecoilValue(dataSourceTypesState);
  const [dataSourceName, setDataSourceName] = useState(
    datasource?.name ? datasource.name : "",
  );
  const [dataSourceNameError, setDataSourceNameError] = useState(false);

  const [dataSources, setDataSources] = useRecoilState(dataSourcesState);
  const [dataSourceType, setDataSourceType] = useState(
    datasource?.type ? datasource.type : dataSourceTypes?.[0],
  );
  const [formData, setFormData] = useState({});
  const reloadDataSourceEntries = useReloadDataSourceEntries();

  return (
    <Dialog open={open} onClose={handleCancelCb} sx={{ zIndex: 900 }}>
      <DialogTitle>{modalTitle}</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <TextField
            label="Data Source Name"
            value={dataSourceName}
            onChange={(e) => setDataSourceName(e.target.value)}
            disabled={datasource ? true : false}
            required={true}
            defaultValue={datasource?.name || "Untitled"}
            size="small"
            style={{ width: "100%", marginTop: "6px" }}
            error={dataSourceNameError}
          />
          <span>Data Source Type</span>
          <ButtonGroup
            variant="outlined"
            size="small"
            style={{ display: "inline-block" }}
            disabled={datasource ? true : false}
          >
            {dataSourceTypes.map((dst) => (
              <Button
                key={dst.id}
                variant={
                  dataSourceType?.id === dst.id ? "contained" : "outlined"
                }
                onClick={(e) => {
                  setDataSourceType(dst);
                }}
              >
                {dst.name}
              </Button>
            ))}
          </ButtonGroup>
          <ThemedJsonForm
            schema={dataSourceType?.entry_config_schema || {}}
            validator={validator}
            uiSchema={{
              ...(dataSourceType?.entry_config_ui_schema || {}),
              ...{
                "ui:submitButtonOptions": {
                  norender: true,
                },
                "ui:DescriptionFieldTemplate": () => null,
                "ui:TitleFieldTemplate": () => null,
              },
            }}
            formData={formData}
            onChange={({ formData }) => {
              setFormData(formData);
            }}
            disableAdvanced={true}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Cancel</Button>,
        <Button
          variant="contained"
          onClick={() => {
            if (datasource) {
              axios()
                .post(`/api/datasources/${datasource.uuid}/add_entry_async`, {
                  entry_data: formData,
                })
                .then(() => {
                  reloadDataSourceEntries();
                });
              handleCancelCb();
              enqueueSnackbar(
                "Processing Data, please refresh the page in a few minutes",
                {
                  variant: "success",
                },
              );
            } else {
              if (dataSourceName === "") {
                setDataSourceNameError(true);
                return;
              }

              axios()
                .post("/api/datasources", {
                  name: dataSourceName,
                  type: dataSourceType.id,
                  config: dataSourceType.is_external_datasource ? formData : {},
                })
                .then((response) => {
                  // External data sources do not support adding entries
                  if (!dataSourceType.is_external_datasource) {
                    const dataSource = response.data;
                    setDataSources([...dataSources, dataSource]);
                    axios()
                      .post(
                        `/api/datasources/${dataSource.uuid}/add_entry_async`,
                        {
                          entry_data: formData,
                        },
                      )
                      .then((response) => {
                        dataSourceAddedCb(dataSource);
                      });
                  }
                });
              handleCancelCb();
              enqueueSnackbar(
                "Processing Data, please refresh the page in a few minutes",
                {
                  variant: "success",
                },
              );
            }
          }}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}
