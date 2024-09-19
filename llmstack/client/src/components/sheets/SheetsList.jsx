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
import {
  DeleteOutlineOutlined,
  EditOutlined,
  DownloadOutlined,
  ContentCopyOutlined,
} from "@mui/icons-material";
import { axios } from "../../data/axios";
import SheetDeleteDialog from "./SheetDeleteDialog";
import { useEffect } from "react";
import { SheetDuplicateDialog } from "./SheetDuplicateDialog";
import SheetFromYamlDialog from "./SheetFromYamlDialog";

function SheetListItem({ sheet, onDelete, onEdit, onDuplicate }) {
  const navigate = useNavigate();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const handleDelete = () => {
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    onDelete(sheet.uuid);
    setDeleteDialogOpen(false);
  };

  const handleEdit = (e) => {
    e.stopPropagation();
    setEditDialogOpen(true);
  };

  const handleDuplicate = (e) => {
    e.stopPropagation();
    onDuplicate(sheet);
  };

  return (
    <>
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
            {sheet.description || "No description available"}
          </Typography>
        </TableCell>
        <TableCell align="center">
          <IconButton aria-label="edit" onClick={handleEdit}>
            <EditOutlined />
          </IconButton>
          <IconButton aria-label="duplicate" onClick={handleDuplicate}>
            <ContentCopyOutlined sx={{ fontSize: "20px" }} />
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
      </TableRow>
      <SheetDeleteDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={confirmDelete}
        sheetName={sheet.name}
      />
      <SheetFromTemplateDialog
        open={editDialogOpen}
        setOpen={setEditDialogOpen}
        sheet={sheet}
        setSheet={onEdit}
        sheetId={sheet.uuid}
        setSheetId={() => {}}
      />
    </>
  );
}

function SheetsList() {
  const [newSheetDialogOpen, setNewSheetDialogOpen] = useState(false);
  const [importSheetDialogOpen, setImportSheetDialogOpen] = useState(false);
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [sheetToDuplicate, setSheetToDuplicate] = useState(null);
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

  const handleEditSheet = (updatedSheet) => {
    setSheets((prevSheets) =>
      prevSheets.map((sheet) =>
        sheet.uuid === updatedSheet.uuid ? updatedSheet : sheet,
      ),
    );
    enqueueSnackbar("Sheet updated successfully", { variant: "success" });
  };

  const handleDuplicateSheet = (sheet) => {
    setSheetToDuplicate(sheet);
    setDuplicateDialogOpen(true);
  };

  const handleDuplicateComplete = (newSheet) => {
    setSheets((prevSheets) => [...prevSheets, newSheet]);
    enqueueSnackbar("Sheet duplicated successfully", { variant: "success" });
  };

  const handleImportComplete = (newSheet) => {
    setSheets((prevSheets) => [...prevSheets, newSheet]);
    enqueueSnackbar("Sheet imported successfully", { variant: "success" });
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
          <Stack direction={"row"} spacing={2}>
            <Button
              variant="outlined"
              startIcon={<DownloadOutlined />}
              size="medium"
              onClick={() => setImportSheetDialogOpen(true)}
            >
              Import
            </Button>
            <Button
              variant="contained"
              startIcon={<AddOutlined />}
              size="medium"
              onClick={() => setNewSheetDialogOpen(true)}
            >
              New Sheet
            </Button>
          </Stack>
        </Stack>
      </Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: "bold" }}>Name</TableCell>
            <TableCell sx={{ fontWeight: "bold" }}>Description</TableCell>
            <TableCell sx={{ fontWeight: "bold" }} align="center">
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sheets.length > 0 && Array.isArray(sheets) ? (
            sheets.map((sheet) => (
              <SheetListItem
                key={sheet.uuid}
                sheet={sheet}
                onDelete={handleDeleteSheet}
                onEdit={handleEditSheet}
                onDuplicate={handleDuplicateSheet}
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
      <SheetDuplicateDialog
        open={duplicateDialogOpen}
        setOpen={setDuplicateDialogOpen}
        sheet={sheetToDuplicate}
        onDuplicate={handleDuplicateComplete}
      />
      <SheetFromYamlDialog
        open={importSheetDialogOpen}
        onClose={() => setImportSheetDialogOpen(false)}
        onImport={handleImportComplete}
      />
    </Stack>
  );
}

export default SheetsList;
