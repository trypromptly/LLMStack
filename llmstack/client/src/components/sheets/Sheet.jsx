import { useCallback, useEffect, useRef, useState } from "react";
import {
  Box,
  Stack,
  CircularProgress,
  Button,
  Tooltip,
  Typography,
} from "@mui/material";
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
import SettingsSuggestIcon from "@mui/icons-material/SettingsSuggest";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
import "@glideapps/glide-data-grid/dist/index.css";
import SheetCellMenu from "./SheetCellMenu";
import SheetFormulaMenu from "./SheetFormulaMenu";

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

const columnLetterToIndex = (letter) => {
  return (
    letter.split("").reduce((acc, char, index) => {
      return (
        acc +
        (char.charCodeAt(0) - 64) * Math.pow(26, letter.length - index - 1)
      );
    }, 0) - 1
  );
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
  const [columns, setColumns] = useState({});
  const [gridColumns, setGridColumns] = useState([]);
  const [cells, setCells] = useState({});
  const [formulaCells, setFormulaCells] = useState({});
  const [runId, setRunId] = useState(null);
  const [selectedGrid, setSelectedGrid] = useState([]);
  const [selectedColumnId, setSelectedColumnId] = useState(null);
  const [showEditColumnMenu, setShowEditColumnMenu] = useState(false);
  const [showFormulaMenu, setShowFormulaMenu] = useState(false);
  const [selectedCellId, setSelectedCellId] = useState(null);
  const [numRows, setNumRows] = useState(0);
  const [numColumns, setNumColumns] = useState(0);
  const [userChanges, setUserChanges] = useState({
    columns: {},
    cells: {},
    numRows: null,
    addedColumns: [],
  });
  const editColumnAnchorEl = useRef(null);
  const sheetRef = useRef(null);
  const formulaMenuAnchorEl = useRef(null);
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
  const [cellMenuAnchorEl, setCellMenuAnchorEl] = useState(null);
  const [cellMenuOpen, setCellMenuOpen] = useState(false);
  const [selectedCell, setSelectedCell] = useState(null);

  const getCellContent = useCallback(
    ([col, row]) => {
      const column = gridColumns[col];
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
    [cells, gridColumns],
  );

  const parseSheetColumnsIntoGridColumns = useCallback(
    (columns) => {
      const cols = Object.keys(columns || []).map((colLetter, index) => ({
        col: colLetter,
        title: columns[colLetter].title,
        type: columns[colLetter].type,
        kind:
          sheetColumnTypes[columns[colLetter].type]?.kind || GridCellKind.Text,
        data: columns[colLetter].data,
        hasMenu: true,
        icon: sheetColumnTypes[columns[colLetter].type]?.icon,
        width: columns[colLetter].width || 300,
      }));

      // Sort columns by position and then by col letter
      cols.sort((a, b) => {
        if (a.position !== b.position) {
          return a.position - b.position;
        }
        return columnLetterToIndex(a.col) - columnLetterToIndex(b.col);
      });

      // Find the last column and fill up to the end with empty columns
      const lastColumn = cols[cols.length - 1];
      for (
        let i = lastColumn?.col ? lastColumn?.col.charCodeAt(0) - 64 : 0;
        i < numColumns;
        i++
      ) {
        cols.push({
          col: columnIndexToLetter(i),
          title: "",
          type: "text",
          kind: GridCellKind.Text,
          data: "",
          hasMenu: true,
          icon: null,
          width: 300,
        });
      }

      return cols;
    },
    [numColumns],
  );

  useEffect(() => {
    if (sheetId) {
      axios()
        .get(`/api/sheets/${sheetId}?include_cells=true`)
        .then((response) => {
          const { data } = response;
          setSheet(data);
          setCells(data?.cells || {});
          setFormulaCells(data?.formula_cells || {});
          setSheetRunning(data?.running || false);
          setColumns(data?.columns || {});
          setNumColumns(data?.total_columns || 26);
          setNumRows(data?.total_rows || 0);
          setUserChanges({
            columns: {},
            cells: {},
            numRows: null,
            addedColumns: [],
            formulaCells: {},
          });
        })
        .catch((error) => {
          console.error(error);
          enqueueSnackbar(`Error loading sheet: ${error.message}`, {
            variant: "error",
          });
        });
    }
  }, [sheetId]);

  useEffect(() => {
    setGridColumns(parseSheetColumnsIntoGridColumns(columns));
  }, [columns, parseSheetColumnsIntoGridColumns]);

  const hasChanges = useCallback(() => {
    return (
      Object.keys(userChanges.columns).length > 0 ||
      Object.keys(userChanges.cells).length > 0 ||
      Object.keys(userChanges.formulaCells).length > 0 ||
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
        const colLetter = gridColumns[columnIndex].col;
        const newColumns = { ...prevColumns };
        newColumns[colLetter] = newColumn;
        updateUserChanges("columns", colLetter, newColumn);
        return newColumns;
      });
    },
    [updateUserChanges, gridColumns],
  );

  const addColumn = useCallback(
    (column) => {
      setColumns((prevColumns) => {
        // Get max letter from existing columns
        const colLetter = columnIndexToLetter(numColumns + 1);
        const newColumns = { ...prevColumns };
        newColumns[colLetter] = column;
        updateUserChanges("addedColumns", colLetter, column);
        return newColumns;
      });
    },
    [updateUserChanges, numColumns],
  );

  const onCellEdited = useCallback(
    (cell, value) => {
      const [col, row] = cell;
      const cellId = gridCellToCellId(cell, gridColumns);

      setCells((prevCells) => {
        const newCell = {
          row: row + 1,
          col: gridColumns[col]?.col,
          kind:
            sheetColumnTypes[gridColumns[col]?.type]?.kind || GridCellKind.Text,
          data:
            sheetColumnTypes[gridColumns[col]?.type]?.getCellDataFromValue(
              value,
            ) || "",
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
    [gridColumns, updateUserChanges, sheetRef],
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
          if (currentCol < gridColumns.length) {
            const cellId = gridCellToCellId(
              [currentCol, currentRow],
              gridColumns,
            );
            newCells[cellId] = {
              kind: GridCellKind.Text,
              display_data: cellValue,
              row: currentRow + 1,
              col: gridColumns[currentCol].col,
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
        cell: cellIdToGridCell(cellId, gridColumns),
      }));
      sheetRef.current?.updateCells(cellsToUpdate);

      return true;
    },
    [gridColumns, setUserChanges],
  );

  const onRowAppended = useCallback(() => {
    const newRowIndex = numRows + 1;
    const newCells = gridColumns.reduce((acc, column) => {
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
  }, [numRows, gridColumns]);

  const saveSheet = useCallback(() => {
    return new Promise((resolve, reject) => {
      const updatedSheet = {
        ...sheet,
        columns: columns,
        cells: cells,
        formula_cells: formulaCells,
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
            formulaCells: {},
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
  }, [sheet, columns, cells, numRows, formulaCells]);

  useEffect(() => {
    if (runId) {
      // Connect to ws and listen for updates
      const ws = new Ws(`${wsUrlPrefix}/sheets/${sheet.uuid}/run/${runId}`);
      if (ws) {
        ws.setOnMessage((evt) => {
          const event = JSON.parse(evt.data);

          if (event.type === "cell.update") {
            const cell = event.cell;
            const gridCell = cellIdToGridCell(cell.id, gridColumns);
            if (gridCell) {
              const [colIndex] = gridCell;
              const column = gridColumns[colIndex];
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

              setSelectedCellValue(cell.output || "");

              sheetRef.current?.updateCells([{ cell: gridCell }]);
              sheetRef.current?.scrollTo(gridCell[0], gridCell[1]);
            }
          } else if (event.type === "cell.updating") {
            const cell = event.cell;
            const gridCell = cellIdToGridCell(cell.id, gridColumns);
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
  }, [runId, sheet?.uuid, wsUrlPrefix, gridColumns]);

  const onGridSelectionChange = useCallback(
    (selection) => {
      setGridSelection(selection);
      if (selection.current) {
        const { cell, range } = selection.current;
        const [col, row] = cell;
        const cellId = gridCellToCellId([col, row], gridColumns);
        const columnType = sheetColumnTypes[gridColumns[col].type];
        setSelectedGrid([
          range.width === 1 && range.height === 1
            ? cellId
            : `${cellId}-${gridCellToCellId(
                [col + range.width - 1, row + range.height - 1],
                gridColumns,
              )}`,
        ]);
        setSelectedCellValue(
          columnType?.getCellDisplayData(cells[cellId]) || "",
        );
        setSelectedCellId(cellId);
      } else {
        setSelectedCellValue("");
        setSelectedCellId(null);
      }
    },
    [gridColumns, cells],
  );

  const onCellContextMenu = useCallback((cell, event) => {
    event.preventDefault();
    setSelectedCell(cell);
    setCellMenuAnchorEl({
      getBoundingClientRect: () => DOMRect.fromRect(event?.bounds),
    });
    setCellMenuOpen(true);
  }, []);

  const handleCellCopy = useCallback(() => {
    if (selectedCell) {
      const cellValue = getCellContent(selectedCell);
      navigator.clipboard.writeText(cellValue.displayData);
    }
    setCellMenuOpen(false);
  }, [selectedCell, getCellContent]);

  const handleCellPaste = useCallback(async () => {
    if (selectedCell) {
      const text = await navigator.clipboard.readText();
      onCellEdited(selectedCell, text);
    }
    setCellMenuOpen(false);
  }, [selectedCell, onCellEdited]);

  const handleCellDelete = useCallback(() => {
    if (selectedCell) {
      onCellEdited(selectedCell, "");
    }
    setCellMenuOpen(false);
  }, [selectedCell, onCellEdited]);

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
        <Typography
          sx={{ fontSize: "14px", fontFamily: "Arial", fontWeight: "semibold" }}
        >
          {selectedGrid}
        </Typography>
        <Tooltip title="Formula">
          <Button
            onClick={() => setShowFormulaMenu(!showFormulaMenu)}
            disabled={selectedGrid?.length !== 1}
            color="primary"
            variant="outlined"
            sx={{ minWidth: "40px", padding: "5px", borderRadius: "4px" }}
            ref={formulaMenuAnchorEl}
          >
            <SettingsSuggestIcon />
          </Button>
        </Tooltip>
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
      </Box>
      <Box>
        <DataEditor
          ref={sheetRef}
          onPaste={onPaste}
          getCellContent={getCellContent}
          columns={gridColumns.map((c) => ({
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
            <SheetColumnMenuButton
              addColumn={addColumn}
              columns={gridColumns}
            />
          }
          onCellEdited={onCellEdited}
          onHeaderMenuClick={(column, bounds) => {
            setSelectedColumnId(
              gridColumns.findIndex(
                (c) => c.col === columnIndexToLetter(column),
              ),
            );
            if (editColumnAnchorEl.current) {
              editColumnAnchorEl.current.style.position = "absolute";
              editColumnAnchorEl.current.style.left = `${bounds.x}px`;
              editColumnAnchorEl.current.style.top = `${bounds.y}px`;
              editColumnAnchorEl.current.style.width = `${bounds.width}px`;
              editColumnAnchorEl.current.style.height = `${bounds.height}px`;
            }
            setShowEditColumnMenu(!showEditColumnMenu);
          }}
          onColumnResize={(column, width) => {
            onColumnChange(
              gridColumns.findIndex((c) => c.col === column.col),
              { ...column, width },
            );
          }}
          rows={numRows}
          headerIcons={headerIcons}
          gridSelection={gridSelection}
          onGridSelectionChange={onGridSelectionChange}
          onCellContextMenu={onCellContextMenu}
        />
      </Box>
      <div id="portal" />
      <div id="sheet-column-menu" ref={editColumnAnchorEl} />
      {showEditColumnMenu && (
        <SheetColumnMenu
          onClose={() => setShowEditColumnMenu(false)}
          column={
            selectedColumnId !== null ? gridColumns[selectedColumnId] : null
          }
          open={showEditColumnMenu}
          setOpen={setShowEditColumnMenu}
          anchorEl={editColumnAnchorEl.current}
          columns={gridColumns}
          updateColumn={(column) => {
            setColumns((columns) => {
              const newColumns = { ...columns };
              newColumns[column.col] = column;

              updateUserChanges("columns", column.col, column);

              return newColumns;
            });
          }}
          deleteColumn={(column) => {
            setColumns((columns) => {
              const newColumns = { ...columns };
              delete newColumns[column.col];
              updateUserChanges("columns", column.col, null); // Mark column as deleted
              return newColumns;
            });
            setCells((cells) => {
              const newCells = { ...cells };
              Object.keys(newCells).forEach((cellId) => {
                if (newCells[cellId].col === column.col) {
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
      <SheetCellMenu
        anchorEl={cellMenuAnchorEl}
        open={cellMenuOpen}
        onClose={() => setCellMenuOpen(false)}
        onCopy={handleCellCopy}
        onPaste={handleCellPaste}
        onDelete={handleCellDelete}
      />
      <SheetFormulaMenu
        anchorEl={formulaMenuAnchorEl.current}
        open={showFormulaMenu}
        onClose={() => setShowFormulaMenu(false)}
        cellId={selectedCellId}
        formulaCells={formulaCells}
        setFormulaCell={(cellId, formulaData) => {
          const [col, row] = cellIdToGridCell(cellId, gridColumns);

          if (!formulaData) {
            setFormulaCells((prev) => {
              const newFormulaCells = { ...prev };
              delete newFormulaCells[cellId];
              return newFormulaCells;
            });
            setUserChanges((prev) => ({
              ...prev,
              formulaCells: { ...prev.formulaCells, [cellId]: null },
            }));
            return;
          }

          setFormulaCells((prev) => ({
            [cellId]: {
              row: row + 1,
              col: gridColumns[col]?.col,
              formula: formulaData,
            },
          }));
          setUserChanges((prev) => ({
            ...prev,
            formulaCells: { ...prev.formulaCells, [cellId]: formulaData },
          }));
        }}
      />
    </Stack>
  ) : (
    <CircularProgress />
  );
}

export default Sheet;
