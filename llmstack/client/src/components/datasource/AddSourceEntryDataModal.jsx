import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from "@mui/material";

import validator from "@rjsf/validator-ajv8";
import { useState, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { pipelineTemplatesState, sourceTypesState } from "../../data/atoms";
import ThemedJsonForm from "../ThemedJsonForm";

export function AddSourceEntryDataModal({
  open,
  onCancel,
  onSubmit,
  modalTitle = "Add Source Entry",
  datasource,
}) {
  const [sourceData, setSourceData] = useState({});
  const sourceTypes = useRecoilValue(sourceTypesState);
  const templates = useRecoilValue(pipelineTemplatesState);
  const [source, setSource] = useState({});

  useEffect(() => {
    if (datasource) {
      let source = null;
      if (datasource.type.slug === "custom") {
        source = sourceTypes.find(
          (s) =>
            s.slug === datasource.pipeline.source.slug &&
            s.provider_slug === datasource.pipeline.source.provider_slug,
        );
      } else {
        source = templates.find((t) => t.slug === datasource.type.slug)
          ?.pipeline?.source;
      }
      if (source) {
        setSource(source);
      }
    }
  }, [datasource, sourceTypes, setSource]);

  return (
    <Dialog open={open} onClose={onCancel} sx={{ zIndex: 900 }}>
      <DialogTitle>{modalTitle}</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <TextField
            label="Data Source Name"
            disabled
            defaultValue={datasource?.name}
            size="small"
            style={{ width: "100%", marginTop: "6px" }}
          />
          <ThemedJsonForm
            schema={source.schema || {}}
            validator={validator}
            uiSchema={{
              ...(source?.ui_schema || {}),
              ...{
                "ui:submitButtonOptions": {
                  norender: true,
                },
                "ui:DescriptionFieldTemplate": () => null,
                "ui:TitleFieldTemplate": () => null,
              },
            }}
            formData={sourceData}
            onChange={({ formData }) => {
              setSourceData(formData);
            }}
            disableAdvanced={false}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>,
        <Button
          variant="contained"
          onClick={() => {
            onSubmit(sourceData);
          }}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}
