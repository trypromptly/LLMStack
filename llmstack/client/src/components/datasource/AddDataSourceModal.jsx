import {
  Button,
  ButtonGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { dataSourcesState, dataSourceTypesState } from "../../data/atoms";
import { axios } from "../../data/axios";
import { useReloadDataSourceEntries } from "../../data/init";
import ThemedJsonForm from "../ThemedJsonForm";

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
  const [destinationFormData, setDestinationFormData] = useState({});
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
                key={dst.slug}
                variant={
                  dataSourceType?.slug === dst.slug ? "contained" : "outlined"
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
            schema={dataSourceType?.source?.schema || {}}
            validator={validator}
            uiSchema={{
              ...(dataSourceType?.source?.ui_schema || {}),
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
          {datasource === null &&
            dataSourceType?.destination &&
            dataSourceType?.destination?.provider_slug !== "weaviate" && (
              <ThemedJsonForm
                schema={dataSourceType?.destination?.schema || {}}
                validator={validator}
                uiSchema={{
                  ...(dataSourceType?.destination?.ui_schema || {}),
                  ...{
                    "ui:submitButtonOptions": {
                      norender: true,
                    },
                    "ui:DescriptionFieldTemplate": () => null,
                    "ui:TitleFieldTemplate": () => null,
                  },
                }}
                formData={destinationFormData}
                onChange={({ formData }) => {
                  setDestinationFormData(formData);
                }}
                disableAdvanced={true}
              />
            )}
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
                  enqueueSnackbar(
                    "Processing Data, please refresh the page in a few minutes",
                    {
                      variant: "success",
                    },
                  );
                })
                .catch((error) => {
                  enqueueSnackbar(
                    `Failed to add entry. ${error?.response?.data}`,
                    {
                      variant: "error",
                    },
                  );
                })
                .finally(() => {
                  handleCancelCb();
                });
            } else {
              if (dataSourceName === "") {
                setDataSourceNameError(true);
                return;
              }

              axios()
                .post("/api/datasources", {
                  name: dataSourceName,
                  type: dataSourceType.id,
                  type_slug: dataSourceType.slug,
                  config: dataSourceType.is_external_datasource ? formData : {},
                  destination_data: destinationFormData,
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
