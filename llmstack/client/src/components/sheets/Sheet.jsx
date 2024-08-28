import { useCallback, useEffect, useRef, useState } from "react";
import { Box, Stack, CircularProgress, Button, Tooltip } from "@mui/material";
import {
  DataEditor,
  GridCellKind,
  CompactSelection,
} from "@glideapps/glide-data-grid";
import {
  SheetColumnMenu,
  SheetColumnMenuButton,
  sheetColumnTypes,
} from "./SheetColumnMenu";
import { axios } from "../../data/axios";
import { Ws } from "../../data/ws";
import { enqueueSnackbar } from "notistack";
import SheetHeader from "./SheetHeader";
import { headerIcons } from "./headerIcons";
import SaveIcon from "@mui/icons-material/Save";
import DownloadIcon from "@mui/icons-material/Download";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
import "@glideapps/glide-data-grid/dist/index.css";

const columnIndexToLetter = (index) => {
  let temp = index + 1;
  let letter = "";
  while (temp > 0) {
    let remainder = (temp - 1) % 26;
    letter = String.fromCharCode(65 + remainder) + letter;
    temp = Math.floor((temp - 1) / 26);
  }
  return letter;
};

const cellIdToGridCell = (cellId, columns) => {
  const match = cellId.match(/([A-Z]+)(\d+)/);
  if (!match) return null;
  const [, colLetter, rowString] = match;
  const row = parseInt(rowString, 10) - 1;
  const col = columns.findIndex((c) => c.col === colLetter);
  return [col, row];
};

const gridCellToCellId = (gridCell, columns) => {
  const [colIndex, rowIndex] = gridCell;
  const colLetter = columns[colIndex].col;
  return `${colLetter}${rowIndex + 1}`;
};

function Sheet(props) {
  const { sheetId } = props;
  const [sheetRunning, setSheetRunning] = useState(false);
  const [sheet, setSheet] = useState(null);
  const [columns, setColumns] = useState([]);
  const [cells, setCells] = useState({});
  const [runId, setRunId] = useState(null);
  const [selectedColumnId, setSelectedColumnId] = useState(null);
  const [showEditColumnMenu, setShowEditColumnMenu] = useState(false);
  const [numRows, setNumRows] = useState(0);
  const [userChanges, setUserChanges] = useState({
    columns: {},
    cells: {},
    numRows: null,
    addedColumns: [],
  });
  const editColumnAnchorEl = useRef(null);
  const sheetRef = useRef(null);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;
  const [gridSelection, setGridSelection] = useState({
    columns: CompactSelection.empty(),
    rows: CompactSelection.empty(),
    current: undefined,
  });
  const [selectedCellValue, setSelectedCellValue] = useState(
    "<p style='color: #999; font-size: 14px;'>Select a cell to view data</p>",
  );

  const getCellContent = useCallback(
    ([col, row]) => {
      const column = columns[col];
      const colLetter = column.col;
      const cell = cells[`${colLetter}${row + 1}`];
      const columnType = sheetColumnTypes[column.type];

      return {
        kind:
          cell?.kind === GridCellKind.Loading
            ? GridCellKind.Loading
            : columnType?.kind || GridCellKind.Text,
        displayData: columnType?.getCellDisplayData(cell) || "",
        data: columnType?.getCellData(cell) || "",
        allowOverlay: true,
        allowWrapping: true,
        skeletonWidth: column.width || 100,
        skeletonWidthVariability: 100,
      };
    },
    [cells, columns],
  );

  const parseSheetColumnsIntoGridColumns = useCallback((columns) => {
    if (!columns) {
      return [];
    }

    const cols = columns.map((column, index) => ({
      col: columnIndexToLetter(index),
      title: column.title,
      type: column.type,
      kind: sheetColumnTypes[column.type]?.kind || GridCellKind.Text,
      data: column.data,
      hasMenu: true,
      icon: sheetColumnTypes[column.type]?.icon,
      width: column.width || 300,
    }));

    return cols;
  }, []);

  useEffect(() => {
    if (sheetId) {
      axios()
        .get(`/api/sheets/${sheetId}?include_cells=true`)
        .then((response) => {
          const { data } = response;
          setSheet(data);
          setCells(data?.cells || {});
          setSheetRunning(data?.running || false);
          setColumns(parseSheetColumnsIntoGridColumns(data?.columns || []));
          setNumRows(data?.total_rows || 0);
          setUserChanges({
            columns: {},
            cells: {},
            numRows: null,
            addedColumns: [],
          });
        })
        .catch((error) => {
          console.error(error);
          enqueueSnackbar(`Error loading sheet: ${error.message}`, {
            variant: "error",
          });
        });
    }
  }, [sheetId, parseSheetColumnsIntoGridColumns]);

  const hasChanges = useCallback(() => {
    return (
      Object.keys(userChanges.columns).length > 0 ||
      Object.keys(userChanges.cells).length > 0 ||
      userChanges.numRows !== null ||
      userChanges.addedColumns.length > 0
    );
  }, [userChanges]);

  const updateUserChanges = useCallback((type, key, value) => {
    setUserChanges((prev) => ({
      ...prev,
      [type]:
        type === "addedColumns"
          ? [...prev[type], key]
          : { ...prev[type], [key]: value },
    }));
  }, []);

  const onColumnChange = useCallback(
    (columnIndex, newColumn) => {
      setColumns((prevColumns) => {
        const newColumns = [...prevColumns];
        newColumns[columnIndex] = newColumn;
        updateUserChanges("columns", columnIndex, newColumn);
        return newColumns;
      });
    },
    [updateUserChanges],
  );

  const addColumn = useCallback(
    (column) => {
      setColumns((prevColumns) => [...prevColumns, column]);
      updateUserChanges("addedColumns", column.col, column);
    },
    [updateUserChanges],
  );

  const onCellEdited = useCallback(
    (cell, value) => {
      const [col, row] = cell;
      const cellId = gridCellToCellId(cell, columns);

      setCells((prevCells) => {
        const newCell = {
          row: row + 1,
          col: columns[col]?.col,
          kind: sheetColumnTypes[columns[col]?.type]?.kind || GridCellKind.Text,
          data:
            sheetColumnTypes[columns[col]?.type]?.getCellDataFromValue(value) ||
            "",
        };

        const newCells = {
          ...prevCells,
          [cellId]: newCell,
        };
        updateUserChanges("cells", cellId, value);
        return newCells;
      });
      sheetRef.current?.updateCells([{ cell: cell }]);
    },
    [columns, updateUserChanges, sheetRef],
  );

  const onPaste = useCallback(
    (cell, value) => {
      const [startCol, startRow] = cell;
      const newCells = {};
      let maxRow = startRow;

      value.forEach((row, rowIndex) => {
        row.forEach((cellValue, colIndex) => {
          const currentRow = startRow + rowIndex;
          const currentCol = startCol + colIndex;
          if (currentCol < columns.length) {
            const cellId = gridCellToCellId([currentCol, currentRow], columns);
            newCells[cellId] = {
              kind: GridCellKind.Text,
              display_data: cellValue,
              row: currentRow + 1,
              col: columns[currentCol].col,
            };
            maxRow = Math.max(maxRow, currentRow);
          }
        });
      });

      setCells((prevCells) => ({
        ...prevCells,
        ...newCells,
      }));

      setNumRows((prevNumRows) => {
        const newNumRows = Math.max(prevNumRows, maxRow + 1);
        if (newNumRows > prevNumRows) {
          setUserChanges((prev) => ({ ...prev, numRows: newNumRows }));
        }
        return newNumRows;
      });

      // Update cells in the grid
      const cellsToUpdate = Object.keys(newCells).map((cellId) => ({
        cell: cellIdToGridCell(cellId, columns),
      }));
      sheetRef.current?.updateCells(cellsToUpdate);

      return true;
    },
    [columns, setUserChanges],
  );

  const onRowAppended = useCallback(() => {
    const newRowIndex = numRows + 1;
    const newCells = columns.reduce((acc, column) => {
      const cellId = `${column.col}${newRowIndex}`;
      acc[cellId] = {
        kind: column.kind || GridCellKind.Text,
        display_data: "",
        row: newRowIndex,
        col: column.col,
      };
      return acc;
    }, {});

    setCells((prevCells) => ({
      ...prevCells,
      ...newCells,
    }));
    setNumRows((prevNumRows) => {
      const newNumRows = prevNumRows + 1;
      setUserChanges((prev) => ({ ...prev, numRows: newNumRows }));
      return newNumRows;
    });
  }, [numRows, columns]);

  const saveSheet = useCallback(() => {
    return new Promise((resolve, reject) => {
      const updatedSheet = {
        ...sheet,
        columns: columns,
        cells: cells,
        total_rows: numRows,
      };
      axios()
        .patch(`/api/sheets/${sheet.uuid}`, updatedSheet)
        .then((response) => {
          setUserChanges({
            columns: {},
            cells: {},
            numRows: null,
            addedColumns: [],
          });
          enqueueSnackbar("Sheet saved successfully", { variant: "success" });
          resolve();
        })
        .catch((error) => {
          console.error(error);
          enqueueSnackbar(
            `Error saving sheet: ${
              error?.response?.data?.detail || error.message
            }`,
            { variant: "error" },
          );
          reject(error);
        });
    });
  }, [sheet, columns, cells, numRows]);

  useEffect(() => {
    if (runId) {
      // Connect to ws and listen for updates
      const ws = new Ws(`${wsUrlPrefix}/sheets/${sheet.uuid}/run/${runId}`);
      if (ws) {
        ws.setOnMessage((evt) => {
          const event = JSON.parse(evt.data);

          if (event.type === "cell.update") {
            const cell = event.cell;
            const gridCell = cellIdToGridCell(cell.id, columns);
            if (gridCell) {
              const [colIndex] = gridCell;
              const column = columns[colIndex];
              const columnType = sheetColumnTypes[column.type];

              setCells((cells) => ({
                ...cells,
                [cell.id]: {
                  ...cells[cell.id],
                  kind: GridCellKind.Text,
                  data: {
                    ...(cells[cell.id]?.data || {}),
                    ...columnType?.getCellDataFromValue(cell.output),
                  },
                  display_data: cell.output || "",
                },
              }));

              sheetRef.current?.updateCells([{ cell: gridCell }]);
              sheetRef.current?.scrollTo(gridCell[0], gridCell[1]);
            }
          } else if (event.type === "cell.updating") {
            const cell = event.cell;
            const gridCell = cellIdToGridCell(cell.id, columns);
            if (gridCell) {
              setCells((cells) => ({
                ...cells,
                [cell.id]: {
                  ...cells[cell.id],
                  kind: GridCellKind.Loading,
                },
              }));

              sheetRef.current?.updateCells([{ cell: gridCell }]);
            }
          } else if (event.type === "sheet.status") {
            const { running } = event.sheet;
            setSheetRunning(running);

            // If running is false, we can disconnect
            if (!running) {
              ws.close();
              setRunId(null);
            }
          } else if (event.type === "sheet.update") {
            const { total_rows } = event.sheet;
            setNumRows(total_rows);
          } else if (event.type === "cell.error") {
            const { error } = event.cell;
            enqueueSnackbar(
              `Failed to execute cell ${event.cell?.id}: ${error}`,
              {
                variant: "error",
              },
            );
          }
        });

        ws.send(JSON.stringify({ event: "run" }));
      }
    }
  }, [runId, sheet?.uuid, wsUrlPrefix, columns]);

  const downloadSheet = () => {
    window.open(`/api/sheets/${sheet.uuid}/download`, "_blank");
  };

  const onGridSelectionChange = useCallback(
    (selection) => {
      setGridSelection(selection);
      if (selection.current) {
        const { cell } = selection.current;
        const [col, row] = cell;
        const cellId = gridCellToCellId([col, row], columns);
        const columnType = sheetColumnTypes[columns[col].type];
        setSelectedCellValue(
          columnType?.getCellDisplayData(cells[cellId]) || "",
        );
      } else {
        setSelectedCellValue("");
      }
    },
    [columns, cells],
  );

  return sheet ? (
    <Stack>
      <SheetHeader
        sheet={sheet}
        setRunId={setRunId}
        hasChanges={hasChanges()}
        onSave={saveSheet}
        sheetRunning={sheetRunning}
        runId={runId}
      />
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: 0,
          gap: 1,
          borderBottom: "1px solid #e0e0e0",
        }}
      >
        <Box
          sx={{
            minHeight: "40px",
            maxHeight: "200px",
            width: "100%",
            overflow: "auto",
            resize: "vertical",
            border: "1px solid #e0e0e0",
            borderRadius: "4px",
            padding: "8px",
            textAlign: "left",
            scrollBehavior: "smooth",
            scrollbarWidth: "thin",
            fontSize: "14px",
            fontFamily: "Arial",
            borderRight: "none",
            "& p": {
              margin: 0,
            },
          }}
        >
          <LayoutRenderer>{selectedCellValue}</LayoutRenderer>
        </Box>
        <Box>
          <Stack direction={"row"} gap={1}>
            <Tooltip title="Save changes">
              <span>
                <Button
                  onClick={saveSheet}
                  disabled={!hasChanges()}
                  color="primary"
                  variant="outlined"
                  sx={{ minWidth: "40px", padding: "5px", borderRadius: "4px" }}
                >
                  <SaveIcon />
                </Button>
              </span>
            </Tooltip>
            {!sheetRunning && (
              <Tooltip title="Download CSV">
                <Button
                  onClick={downloadSheet}
                  color="primary"
                  variant="outlined"
                  sx={{ minWidth: "40px", padding: "5px", borderRadius: "4px" }}
                >
                  <DownloadIcon />
                </Button>
              </Tooltip>
            )}
          </Stack>
        </Box>
      </Box>
      <Box>
        <DataEditor
          ref={sheetRef}
          onPaste={onPaste}
          getCellContent={getCellContent}
          columns={columns.map((c) => ({
            ...c,
            title: `${c.col}: ${c.title}`,
          }))}
          smoothScrollX={true}
          smoothScrollY={true}
          rowMarkers={"both"}
          freezeTrailingRows={2}
          trailingRowOptions={{
            sticky: true,
            tint: true,
            hint: "New row...",
          }}
          onRowAppended={onRowAppended}
          width={"100%"}
          getCellsForSelection={true}
          rightElement={
            <SheetColumnMenuButton addColumn={addColumn} columns={columns} />
          }
          onCellEdited={onCellEdited}
          onHeaderMenuClick={(column, bounds) => {
            setSelectedColumnId(
              columns.findIndex((c) => c.col === columnIndexToLetter(column)),
            );
            editColumnAnchorEl.current = {
              getBoundingClientRect: () => DOMRect.fromRect(bounds),
            };
            setShowEditColumnMenu(!showEditColumnMenu);
          }}
          onColumnResize={(column, width) => {
            onColumnChange(
              columns.findIndex((c) => c.col === column.col),
              { ...column, width },
            );
          }}
          rows={numRows}
          headerIcons={headerIcons}
          gridSelection={gridSelection}
          onGridSelectionChange={onGridSelectionChange}
        />
      </Box>
      <div id="portal" />
      {showEditColumnMenu && (
        <SheetColumnMenu
          onClose={() => setShowEditColumnMenu(false)}
          column={selectedColumnId !== null ? columns[selectedColumnId] : null}
          open={showEditColumnMenu}
          setOpen={setShowEditColumnMenu}
          anchorEl={editColumnAnchorEl.current}
          columns={columns}
          updateColumn={(column) => {
            setColumns((columns) => {
              const newColumns = [...columns];
              const index = columns.findIndex((c) => c.col === column.col);
              newColumns[index] = column;

              updateUserChanges("columns", selectedColumnId, column);

              return parseSheetColumnsIntoGridColumns(newColumns);
            });
          }}
          deleteColumn={(column) => {
            setColumns((columns) => {
              const newColumns = columns.filter((c) => c.col !== column.col);
              updateUserChanges("columns", column.col, null); // Mark column as deleted
              return parseSheetColumnsIntoGridColumns(newColumns);
            });
            setCells((cells) => {
              const newCells = { ...cells };
              Object.keys(newCells).forEach((cellId) => {
                if (cells[cellId].col === column.col) {
                  delete newCells[cellId];
                  updateUserChanges("cells", cellId, null); // Mark cell as deleted
                }
              });
              return newCells;
            });
            setSelectedColumnId(null);
          }}
        />
      )}
    </Stack>
  ) : (
    <CircularProgress />
  );
}

export default Sheet;
