import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  useMemo,
} from "react";
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
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
import "@glideapps/glide-data-grid/dist/index.css";
import SheetCellMenu from "./SheetCellMenu";
import SheetFormulaMenu from "./SheetFormulaMenu";
import { ReactComponent as FormulaIcon } from "../../assets/images/icons/formula.svg";

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

const MemoizedSheetHeader = React.memo(SheetHeader);
const MemoizedSheetColumnMenuButton = React.memo(SheetColumnMenuButton);
const MemoizedSheetColumnMenu = React.memo(SheetColumnMenu);
const MemoizedSheetCellMenu = React.memo(SheetCellMenu);
const MemoizedSheetFormulaMenu = React.memo(SheetFormulaMenu);

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
  const [numColumns, setNumColumns] = useState(26);
  const [userChanges, setUserChanges] = useState({
    columns: {},
    cells: {},
    numRows: null,
    addedColumns: [],
  });
  const editColumnAnchorEl = useRef(null);
  const sheetRef = useRef(null);
  const wsRef = useRef(null);
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

  const headerIcons = useMemo(() => {
    if (!columns || typeof columns !== "object") {
      return {};
    }
    const icons = {};
    for (let i = 0; i < numColumns; i++) {
      const colLetter = columnIndexToLetter(i);
      icons[colLetter] = (p) =>
        `<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="2" width="16" height="16" rx="2" fill="${p.bgColor}"/>
      <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="${p.fgColor}">${colLetter}</text>
    </svg>`;
    }
    return icons;
  }, [columns, numColumns]);

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
      if (!columns || typeof columns !== "object") {
        return [];
      }

      const cols = Object.keys(columns).map((colLetter, index) => ({
        col: colLetter,
        title: columns[colLetter].title || "",
        type: columns[colLetter].type || "text",
        kind:
          sheetColumnTypes[columns[colLetter].type]?.kind || GridCellKind.Text,
        data: columns[colLetter].data || "",
        hasMenu: true,
        icon: colLetter,
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
      const lastColumnIndex = lastColumn
        ? columnLetterToIndex(lastColumn.col)
        : -1;
      for (let i = lastColumnIndex + 1; i < numColumns; i++) {
        cols.push({
          col: columnIndexToLetter(i),
          title: "",
          type: "text",
          kind: GridCellKind.Text,
          data: "",
          hasMenu: true,
          icon: columnIndexToLetter(i),
          width: 300,
        });
      }

      return cols;
    },
    [numColumns],
  );

  const drawCell = useCallback(
    (args, drawContent) => {
      drawContent();

      const { ctx, rect, row, col } = args;

      if (!row || !col) {
        return;
      }

      const colLetter = columnIndexToLetter(col);
      const cellId = `${colLetter}${row + 1}`;
      const isFormulaCell = formulaCells[cellId];

      if (!isFormulaCell) {
        return;
      }

      // Define the size and position of the formula icon
      const iconSize = 14;
      const margin = 4;
      const iconX = rect.x + rect.width - iconSize - margin;
      const iconY = rect.y + margin;

      // Draw the formula icon
      ctx.save();

      // Create gradient
      const gradient = ctx.createLinearGradient(
        iconX,
        iconY,
        iconX,
        iconY + iconSize,
      );
      gradient.addColorStop(0, "rgba(255, 255, 255, 0.8)");
      gradient.addColorStop(1, "rgba(255, 255, 255, 0)");

      // Draw gradient background
      ctx.fillStyle = gradient;
      ctx.fillRect(iconX, iconY, iconSize, iconSize);

      // Draw the 'fx' symbol in italics
      ctx.fillStyle = "#107C41";
      ctx.font = `italic bold ${iconSize}px Arial`;
      ctx.textBaseline = "top";
      ctx.fillText("fx", iconX, iconY);

      ctx.restore();
    },
    [formulaCells],
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
          setRunId(data?.run_id || null);
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

  const hasChanges = useMemo(() => {
    return (
      Object.keys(userChanges?.columns || {}).length > 0 ||
      Object.keys(userChanges?.cells || {}).length > 0 ||
      Object.keys(userChanges?.formulaCells || {}).length > 0 ||
      userChanges?.numRows !== null ||
      userChanges?.addedColumns?.length > 0
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
    if (runId && !wsRef.current) {
      // Connect to ws and listen for updates
      const ws = new Ws(`${wsUrlPrefix}/sheets/${sheet.uuid}/run/${runId}`);
      if (ws) {
        wsRef.current = ws;
        wsRef.current.setOnMessage((evt) => {
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

            if (running) {
              enqueueSnackbar("Sheet is running", { variant: "info" });
            } else {
              enqueueSnackbar("Sheet has finished running", {
                variant: "success",
              });
            }

            // If running is false, we can disconnect
            if (!running) {
              wsRef.current.close();
              wsRef.current = null;
            }
          } else if (event.type === "sheet.update") {
            const { total_rows } = event.sheet;
            setNumRows(total_rows);
          } else if (event.type === "sheet.disconnect") {
            setRunId(null);
            setSheetRunning(false);
            wsRef.current.close();
            wsRef.current = null;
            enqueueSnackbar(`Sheet run stopped: ${event.reason}`, {
              variant: "warning",
            });
          } else if (event.type === "sheet.error") {
            enqueueSnackbar(`Error running sheet: ${event.error}`, {
              variant: "error",
            });
            wsRef.current.close();
            wsRef.current = null;
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

        wsRef.current.send(JSON.stringify({ event: "connect" }));
      }
    }

    return () => {
      if (!runId && wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
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
      <MemoizedSheetHeader
        sheet={sheet}
        setRunId={setRunId}
        hasChanges={hasChanges}
        onSave={saveSheet}
        sheetRunning={sheetRunning}
        setSheetRunning={setSheetRunning}
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
          borderLeft: "1px solid #e0e0e0",
        }}
      >
        <Stack
          direction="row"
          spacing={2}
          sx={{
            alignItems: "center",
            width: "120px",
            justifyContent: "center",
            paddingLeft: "4px",
          }}
        >
          <Typography
            sx={{
              fontSize: "14px",
              fontFamily: "Arial",
              fontWeight: "semibold",
            }}
          >
            {selectedGrid}
          </Typography>
          <Tooltip title="Formula">
            <Button
              onClick={() => setShowFormulaMenu(!showFormulaMenu)}
              disabled={selectedGrid?.length !== 1}
              color="primary"
              variant="standard"
              sx={{ minWidth: "30px", padding: "5px" }}
              ref={formulaMenuAnchorEl}
            >
              <FormulaIcon
                sx={{ width: "20px", height: "20px", color: "white" }}
              />
            </Button>
          </Tooltip>
        </Stack>
        <Box
          sx={{
            height: "42px",
            maxHeight: "400px",
            width: "100%",
            overflow: "auto",
            borderBottom: "none",
            borderLeft: "1px solid #e0e0e0",
            borderRadius: "none",
            padding: "8px",
            textAlign: "left",
            scrollBehavior: "smooth",
            scrollbarWidth: "thin",
            fontSize: "14px",
            fontFamily: "Arial",
            borderRight: "none",
            position: "relative",
            "& p": {
              margin: 0,
            },
          }}
          ref={(el) => {
            if (el) {
              const resizer = document.createElement("div");
              resizer.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 5px;
                cursor: ns-resize;
              `;
              el.appendChild(resizer);

              let startY, startHeight;

              const resize = (e) => {
                const newHeight = startHeight + e.clientY - startY;
                el.style.height = `${newHeight}px`;
              };

              const stopResize = () => {
                window.removeEventListener("mousemove", resize);
                window.removeEventListener("mouseup", stopResize);
              };

              resizer.addEventListener("mousedown", (e) => {
                startY = e.clientY;
                startHeight = parseInt(
                  document.defaultView.getComputedStyle(el).height,
                  10,
                );
                window.addEventListener("mousemove", resize);
                window.addEventListener("mouseup", stopResize);
              });
            }
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
          columns={gridColumns}
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
            <MemoizedSheetColumnMenuButton
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
          drawCell={drawCell}
        />
      </Box>
      <div id="portal" />
      <div id="sheet-column-menu" ref={editColumnAnchorEl} />
      {showEditColumnMenu && (
        <MemoizedSheetColumnMenu
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
      <MemoizedSheetCellMenu
        anchorEl={cellMenuAnchorEl}
        open={cellMenuOpen}
        onClose={() => setCellMenuOpen(false)}
        onCopy={handleCellCopy}
        onPaste={handleCellPaste}
        onDelete={handleCellDelete}
      />
      <MemoizedSheetFormulaMenu
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
            ...prev,
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

export default React.memo(Sheet);
