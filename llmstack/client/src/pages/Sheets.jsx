import { Box } from "@mui/material";
import { useParams } from "react-router-dom";
import SheetsList from "../components/sheets/SheetsList";

export default function Sheets() {
  const { sheetId } = useParams();

  return (
    <Box padding={4} sx={{ height: "100%" }}>
      {sheetId ? <SheetsList /> : <div>test</div>}
    </Box>
  );
}
