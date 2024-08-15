import { useState, useRef, useEffect } from "react";
import { Grid, Button, Box } from "@mui/material";
import { useRecoilValue } from "recoil";
import { sheetsState } from "../data/atoms";
import { axios } from "../data/axios";
import AddIcon from "@mui/icons-material/Add";
import { SaveOutlined } from "@mui/icons-material";
import { useParams } from "react-router-dom";

import { BooleanNumber, LocaleType, SheetTypes } from "@univerjs/core";

import UniverSheetApp from "../components/sheets/UniverSheetApp";

// const DEFAULT_WORKBOOK_DATA = {
//   id: "default-workbook",
//   locale: LocaleType.EN_US,
//   name: "universheet",
//   sheetOrder: ["sheet-01"],
//   sheets: {
//     "sheet-01": {
//       type: SheetTypes.GRID,
//       id: "sheet-01",
//       cellData: {
//         0: {
//           0: {
//             v: "Hello World",
//           },
//         },
//       },
//       name: "sheet1",
//       tabColor: "red",
//       hidden: BooleanNumber.FALSE,
//       rowCount: 100,
//       columnCount: 15,
//       zoomRatio: 1,
//       scrollTop: 200,
//       scrollLeft: 100,
//       defaultColumnWidth: 93,
//       defaultRowHeight: 27,
//       status: 1,
//       showGridlines: 1,
//       rightToLeft: BooleanNumber.FALSE,
//     },
//   },
// };
const DEFAULT_WORKBOOK_DATA = {
  id: "default-workbook",
  locale: LocaleType.EN_US,
  name: "universheet",
  sheetOrder: ["sheet-01"],
  sheets: {
    "sheet-01": {
      type: SheetTypes.GRID,
      id: "sheet-01",
      cellData: {},
      name: "sheet1",
      tabColor: "red",
      hidden: BooleanNumber.FALSE,
      rowCount: 100,
      columnCount: 15,
      zoomRatio: 1,
      scrollTop: 200,
      scrollLeft: 100,
      defaultColumnWidth: 93,
      defaultRowHeight: 27,
      status: 1,
      showGridlines: 1,
      rightToLeft: BooleanNumber.FALSE,
    },
  },
};
function gridDataToApiData(columns, rows, apiRef) {
  const cells = [];
  const headerCells = columns.map((column) => ({
    value: column.headerName,
    value_type: "string",
    extra_data: { is_header: true },
  }));
  cells.push(headerCells);
  const columnIndices = columns.reduce(
    (acc, column, index) => ({ ...acc, [column.field]: index }),
    {},
  );
  rows.forEach((row) => {
    const rowCells = new Array(columns.length).fill({ value: "" });
    Object.keys(row)
      .filter((key) => key !== "id")
      .forEach((key) => {
        const columnIndex = columnIndices[key];
        rowCells[columnIndex] = {
          value: row[key],
          value_type: apiRef.current.getColumn(key).type,
        };
      });
    cells.push(rowCells);
  });

  return cells;
}

export default function SheetsPage() {
  const { worksheetId } = useParams();
  const univerRef = useRef(null);
  const [sheetData, setSheetData] = useState(null);

  useEffect(() => {
    axios()
      .get(`/api/sheets/${worksheetId}?include_cells=true`)
      .then((response) => {
        const sheetName = response.data.name;
        const cells = response.data.cells;
        const workbookData = DEFAULT_WORKBOOK_DATA;
        setSheetData(workbookData);
      });
  }, [worksheetId]);

  return (
    <Box padding={4} sx={{ height: "100%" }}>
      <Grid container spacing={2} sx={{ height: "100%" }}>
        <Grid xs={12} sx={{ height: "10%" }}>
          <Grid container>
            <Grid xs={8}>
              <h1>Sheets</h1>
            </Grid>
            <Grid xs={4}>
              <Button
                variant="contained"
                onClick={() => {
                  console.log(univerRef.current.getData());
                }}
              >
                Get Data
              </Button>
            </Grid>
          </Grid>
        </Grid>
        <Grid xs={12} sx={{ height: "80%" }}>
          <UniverSheetApp
            style={{ flex: 1 }}
            ref={univerRef}
            data={DEFAULT_WORKBOOK_DATA}
          />
        </Grid>
        <Grid xs={12} sx={{ height: "5%" }}></Grid>
      </Grid>
    </Box>
  );
}
