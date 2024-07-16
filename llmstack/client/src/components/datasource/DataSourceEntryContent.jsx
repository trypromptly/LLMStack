import { TextareaAutosize } from "@mui/base";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Drawer,
  Stack,
} from "@mui/material";
import { useEffect, useState } from "react";
import { axios } from "../../data/axios";

function DataSourceEntryContent({ onCancel, dataSourceEntry, open }) {
  const [data, setData] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dataSourceEntry?.config?.document_ids) {
      axios()
        .get(`/api/datasource_entries/${dataSourceEntry.uuid}/text_content`)
        .then((response) => {
          console.log(response);
          setData(
            <TextareaAutosize
              value={response.data?.content}
              disabled={true}
              autoSize
              style={{
                maxHeight: "80vh",
                width: "100%",
                overflow: "auto",
              }}
            />,
          );
          setMetadata(response.data?.metadata);
        })
        .finally(() => setLoading(false));
    } else {
      setData(
        <TextareaAutosize
          value={JSON.stringify(dataSourceEntry?.config?.errors)}
          disabled={true}
          autoSize
          style={{ maxHeight: "80vh", width: "100%", overflow: "auto" }}
        />,
      );
    }
  }, [dataSourceEntry]);

  return (
    <Drawer
      open={open}
      onClose={onCancel}
      anchor="right"
      sx={{ "& .MuiDrawer-paper": { minWidth: "40%" }, maxWidth: "40%" }}
    >
      <Box>
        <Stack direction={"row"} gap={1} sx={{ mb: "10px", mt: "10px" }}>
          <Button onClick={() => onCancel()} sx={{ alignSelf: "left" }}>
            X
          </Button>
          {Object.keys(metadata || {}).map((key) => (
            <Chip
              label={`${key}: ${metadata[key]}`}
              size="small"
              key={key}
              sx={{ borderRadius: "10px", marginTop: "5px" }}
            />
          ))}
        </Stack>
        <Divider />
        {loading ? (
          <CircularProgress />
        ) : (
          <div style={{ margin: "0px 10px" }}>{data}</div>
        )}
      </Box>
    </Drawer>
  );
}

export default DataSourceEntryContent;
