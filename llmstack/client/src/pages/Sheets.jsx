import { Box } from "@mui/material";
import { useParams } from "react-router-dom";
import SheetsList from "../components/sheets/SheetsList";
import Sheet from "../components/sheets/Sheet";

export default function Sheets() {
  const { sheetId } = useParams();

  return (
    <Box padding={1} sx={{ height: "100%" }}>
      {sheetId ? <Sheet sheetId={sheetId} /> : <SheetsList />}
    </Box>
  );
}
