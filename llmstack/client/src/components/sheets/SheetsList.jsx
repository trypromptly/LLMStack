import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Stack, Typography } from "@mui/material";
import { AddOutlined } from "@mui/icons-material";
import { useRecoilValue } from "recoil";
import { sheetsListState } from "../../data/atoms";
import { SheetFromTemplateDialog } from "./SheetFromTemplateDialog";

function SheetListItem(props) {
  const { sheet } = props;
  const navigate = useNavigate();

  return (
    <Stack
      key={sheet.id}
      onClick={() => {
        navigate(`/sheets/${sheet.uuid}`);
      }}
    >
      <Typography variant="h6">{sheet.name}</Typography>
      <Typography variant="caption" sx={{ color: "#666" }}>
        {sheet.data?.description}
      </Typography>
    </Stack>
  );
}

function SheetsList(props) {
  const { selectedSheet, selectSheet } = props;
  const [newSheetDialogOpen, setNewSheetDialogOpen] = useState(false);
  const sheets = useRecoilValue(sheetsListState);

  return (
    <Stack>
      <Typography variant="h5" className="section-header">
        <Stack direction={"row"} sx={{ justifyContent: "space-between" }}>
          <Stack>
            Sheets
            <br />
            <Typography variant="caption" sx={{ color: "#666" }}>
              Create and manage your sheets here. Automate your workflows by
              running AI agents on your data with a click.
            </Typography>
          </Stack>
          <Button
            variant="contained"
            startIcon={<AddOutlined />}
            size="medium"
            onClick={() => setNewSheetDialogOpen(true)}
          >
            New Sheet
          </Button>
        </Stack>
      </Typography>
      {Object.values(sheets).map((sheet) => (
        <SheetListItem
          key={sheet.uuid}
          sheet={sheet}
          selected={selectedSheet === sheet.uuid}
          selectSheet={selectSheet}
        />
      ))}
      <SheetFromTemplateDialog
        open={newSheetDialogOpen}
        setOpen={setNewSheetDialogOpen}
        sheet={{}}
        setSheet={() => {}}
        sheetId={null}
        setSheetId={() => {}}
      />
    </Stack>
  );
}

export default SheetsList;
