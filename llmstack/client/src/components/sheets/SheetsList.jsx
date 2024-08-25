import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Stack, Typography } from "@mui/material";
import { AddOutlined } from "@mui/icons-material";
import { useRecoilValue, useSetRecoilState } from "recoil";
import { sheetsListSelector } from "../../data/atoms";
import { SheetFromTemplateDialog } from "./SheetFromTemplateDialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { DeleteOutlineOutlined, EditOutlined } from "@mui/icons-material";
import { axios } from "../../data/axios";
import SheetDeleteDialog from "./SheetDeleteDialog";
import { useEffect } from "react";

function SheetListItem({ sheet, onDelete }) {
  const navigate = useNavigate();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleDelete = () => {
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    onDelete(sheet.uuid);
    setDeleteDialogOpen(false);
  };

  return (
    <TableRow
      key={sheet.uuid}
      onClick={() => navigate(`/sheets/${sheet.uuid}`)}
      sx={{
        cursor: "pointer",
        "&:hover": {
          backgroundColor: "rgba(0, 0, 0, 0.04)",
        },
      }}
    >
      <TableCell>
        <Typography variant="subtitle2" sx={{ fontWeight: "normal" }}>
          {sheet.name}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          {sheet.data?.description || "No description available"}
        </Typography>
      </TableCell>
      <TableCell>
        <IconButton aria-label="edit" onClick={(e) => e.stopPropagation()}>
          <EditOutlined />
        </IconButton>
        <IconButton
          aria-label="delete"
          onClick={(e) => {
            e.stopPropagation();
            handleDelete();
          }}
        >
          <DeleteOutlineOutlined />
        </IconButton>
      </TableCell>
      <SheetDeleteDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={confirmDelete}
        sheetName={sheet.name}
      />
    </TableRow>
  );
}

function SheetsList() {
  const [newSheetDialogOpen, setNewSheetDialogOpen] = useState(false);
  const sheets = useRecoilValue(sheetsListSelector);
  const setSheets = useSetRecoilState(sheetsListSelector);

  useEffect(() => {
    // This will trigger the selector to fetch sheets if they're not already loaded
    setSheets([]);
  }, [setSheets]);

  const handleDeleteSheet = (sheetId) => {
    axios()
      .delete(`/api/sheets/${sheetId}`)
      .then(() => {
        setSheets((prevSheets) =>
          prevSheets.filter((sheet) => sheet.uuid !== sheetId),
        );
        enqueueSnackbar("Sheet deleted successfully", { variant: "success" });
      })
      .catch((error) => {
        console.error("Error deleting sheet:", error);
        enqueueSnackbar("Failed to delete sheet", { variant: "error" });
      });
  };

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
      <Table>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: "bold" }}>Name</TableCell>
            <TableCell sx={{ fontWeight: "bold" }}>Description</TableCell>
            <TableCell sx={{ fontWeight: "bold" }}>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sheets.length > 0 && Array.isArray(sheets) ? (
            sheets.map((sheet) => (
              <SheetListItem
                key={sheet.uuid}
                sheet={sheet}
                onDelete={handleDeleteSheet}
              />
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={3}>
                <Typography align="center">No sheets available</Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
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
