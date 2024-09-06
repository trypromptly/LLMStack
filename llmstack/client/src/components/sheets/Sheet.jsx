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
  SvgIcon,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  DataEditor,
  GridCellKind,
  CompactSelection,
} from "@glideapps/glide-data-grid";
import { SheetColumnMenu, SheetColumnMenuButton } from "./SheetColumnMenu";
import { axios } from "../../data/axios";
import { Ws } from "../../data/ws";
import { enqueueSnackbar } from "notistack";
import SheetHeader from "./SheetHeader";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
import "@glideapps/glide-data-grid/dist/index.css";
import SheetCellMenu from "./SheetCellMenu";
import SheetFormulaMenu from "./SheetFormulaMenu";
import { ReactComponent as FormulaIcon } from "../../assets/images/icons/formula.svg";
import {
  columnIndexToLetter,
  columnLetterToIndex,
  cellIdToGridCell,
  gridCellToCellId,
} from "./utils";
import { getProviderIconImage } from "../apps/ProviderIcon";

export const sheetFormulaTypes = {
  1: {
    value: "data_transformer",
    label: "Data Transformer",
    description: "Transform data using a LiquidJS template",
  },
  2: {
    value: "app_run",
    label: "App Run",
    description: "Run an app to generate formula output",
  },
  3: {
    value: "processor_run",
    label: "Processor Run",
    description: "Run a processor to generate formula output",
  },
};

export const sheetCellTypes = {
  0: {
    label: "Text",
    value: "text",
    description: "Plain text content",
    kind: GridCellKind.Text,
    getDataGridCell: (cell, column) => {
      if (!cell) {
        return {
          kind: GridCellKind.Text,
          data: "",
          displayData: "",
          readonly: column?.formula?.type > 0 || false,
          allowOverlay: true,
          allowWrapping: true,
        };
      }

      return {
        kind: GridCellKind.Text,
        data: cell.value,
        displayData: cell.value ? cell.value.slice(0, 100) : "",
        readonly: cell.formula || column.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell.data;
    },
  },
  1: {
    label: "Number",
    value: "number",
    description: "Numeric values",
    kind: GridCellKind.Number,
    getDataGridCell: (cell, column) => {
      if (!cell) {
        return {
          kind: GridCellKind.Number,
          data: 0,
          displayData: "",
          readonly: column?.formula?.type > 0 || false,
          allowOverlay: true,
          allowWrapping: true,
        };
      }

      return {
        kind: GridCellKind.Number,
        data: parseFloat(cell.value),
        displayData: cell.value?.toString() || "",
        readonly: cell.formula || column.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell.data;
    },
  },
  2: {
    label: "URI",
    value: "uri",
    description: "Uniform Resource Identifier",
    kind: GridCellKind.Uri,
    getDataGridCell: (cell, column) => {
      if (!cell) {
        return {
          kind: GridCellKind.Uri,
          data: "",
          displayData: "",
          readonly: column?.formula?.type > 0 || false,
          allowOverlay: true,
          allowWrapping: true,
          hoverEffect: true,
        };
      }

      return {
        kind: GridCellKind.Uri,
        data: cell.value,
        displayData: cell.value,
        readonly: cell.formula || column.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
        hoverEffect: true,
      };
    },
    getCellValue: (cell) => {
      return cell.data;
    },
  },
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
  const [columns, setColumns] = useState([]);
  const [gridColumns, setGridColumns] = useState([]);
  const [cells, setCells] = useState({});
  const [runId, setRunId] = useState(null);
  const [selectedGrid, setSelectedGrid] = useState([]);
  const [selectedColumnId, setSelectedColumnId] = useState(null);
  const [showEditColumnMenu, setShowEditColumnMenu] = useState(false);
  const [selectedCellReadOnly, setSelectedCellReadOnly] = useState(false);
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
  const [selectedRows, setSelectedRows] = useState([]);

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
      const column = columns[col];
      const cell = cells[`${column.col_letter}${row + 1}`];
      const sheetCellType = sheetCellTypes[column.cell_type];

      const defaultCell = {
        kind: GridCellKind.Text,
        data: "",
        displayData: "",
        readonly: false,
        allowWrapping: true,
        allowOverlay: true,
      };

      return sheetCellType?.getDataGridCell(cell, column) || defaultCell;
    },
    [cells, columns],
  );

  const parseSheetColumnsIntoGridColumns = useCallback((columns) => {
    if (!columns) {
      return [];
    }

    const cols = columns.map((column) => {
      return {
        title: column.title || "",
        colLetter: column.col_letter,
        hasMenu: true,
        icon: column.col_letter,
        width: column.width || 300,
      };
    });

    // Sort columns by position and then by col letter
    cols.sort((a, b) => {
      if (a.position !== b.position) {
        return a.position - b.position;
      }
      return (
        columnLetterToIndex(a.colLetter) - columnLetterToIndex(b.colLetter)
      );
    });

    return cols;
  }, []);

  const drawCell = useCallback(
    (args, drawContent) => {
      const { ctx, rect, row, col } = args;
      const column = columns[col];

      if (!column) {
        return;
      }

      const colLetter = column.col_letter;
      const cellId = `${colLetter}${row + 1}`;
      const cell = cells[cellId];

      if (cell?.status === 1) {
        // Add a dark yellow background to the cell
        ctx.fillStyle = "rgba(255, 255, 0, 0.1)";
        ctx.fillRect(rect.x, rect.y, rect.width, rect.height);

        return;
      }

      if (cell?.status === 2) {
        // Visually indicate that the cell has an with a red background
        ctx.fillStyle = "#FF0000";
        ctx.fillRect(rect.x, rect.y, rect.width, rect.height);

        // Draw error message from cell.error
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "12px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(
          cell.error || "Error",
          rect.x + rect.width / 2,
          rect.y + rect.height / 2,
        );

        return;
      }

      drawContent();

      const isFormulaCell = cells[cellId]?.formula || false;

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
    [cells, columns],
  );

  const drawHeader = useCallback(
    (args, drawContent) => {
      drawContent();

      const { column, ctx, menuBounds } = args;

      const gridColumn = columns.find((c) => c.col_letter === column.icon);

      if (!gridColumn) {
        return;
      }

      if (!gridColumn.formula || gridColumn.formula.type === 0) {
        return;
      }

      const headerIconImage =
        gridColumn.formula.type === 3
          ? getProviderIconImage(
              gridColumn.formula.data?.provider_slug || "promptly",
              false,
            )
          : getProviderIconImage("promptly", false);

      if (headerIconImage) {
        // Draw this image on the canvas
        const img = new Image();
        img.src = headerIconImage;

        img.onload = () => {
          const pixelRatio = window.devicePixelRatio || 1;
          ctx.drawImage(
            img,
            (menuBounds.x - 10) * pixelRatio,
            (menuBounds.y + 8) * pixelRatio,
            (menuBounds.width - 15) * pixelRatio,
            (menuBounds.height - 15) * pixelRatio,
          );
        };
      }
    },
    [columns],
  );

  useEffect(() => {
    if (sheetId) {
      axios()
        .get(`/api/sheets/${sheetId}?include_cells=true`)
        .then((response) => {
          const { data } = response;
          setSheet(data);
          setCells(data?.cells || {});
          setSheetRunning(data?.running || false);
          setRunId(data?.run_id || null);
          setColumns(data?.columns || []);
          setNumColumns(data?.total_columns || 26);
          setNumRows(data?.total_rows || 0);
          setUserChanges({
            columns: [],
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
  }, [sheetId]);

  useEffect(() => {
    setGridColumns(parseSheetColumnsIntoGridColumns(columns));
  }, [columns, parseSheetColumnsIntoGridColumns]);

  useEffect(() => {
    if (selectedCellId) {
      const [col] = cellIdToGridCell(selectedCellId, columns);

      if (col < 0) {
        return;
      }

      setSelectedCellReadOnly(
        Boolean(
          columns[col].formula || columns[col].formula?.type === 0 || false,
        ),
      );
    }
  }, [selectedCellId, columns, cells]);

  const hasChanges = useMemo(() => {
    return (
      Object.keys(userChanges?.columns || []).length > 0 ||
      Object.keys(userChanges?.cells || {}).length > 0 ||
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
      const cellId = gridCellToCellId(cell, columns);
      const column = columns[col];
      const cellType = sheetCellTypes[column.cell_type];
      const colLetter = column.col_letter;

      const cellValue = cellType?.getCellValue(value);

      const existingCell = cells[cellId] || {
        row: row + 1,
        col_letter: colLetter,
      };
      const newCell = {
        ...existingCell,
        value: cellValue,
      };

      setCells((prevCells) => ({
        ...prevCells,
        [cellId]: newCell,
      }));
      updateUserChanges("cells", cellId, newCell);
      sheetRef.current?.updateCells([{ cell: newCell }]);
    },
    [updateUserChanges, sheetRef, columns, cells],
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
              row: currentRow + 1,
              col_letter: columns[currentCol].col_letter,
              value: cellValue,
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
      const cellId = `${column.col_letter}${newRowIndex}`;
      acc[cellId] = {
        type: column.cell_type || 0,
        row: newRowIndex,
        col_letter: column.col_letter,
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
            columns: [],
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
    if (runId && !wsRef.current) {
      // Connect to ws and listen for updates
      const ws = new Ws(`${wsUrlPrefix}/sheets/${sheet.uuid}/run/${runId}`);
      if (ws) {
        wsRef.current = ws;
        wsRef.current.setOnClose(() => {
          setRunId(null);
        });
        wsRef.current.setOnMessage((evt) => {
          const event = JSON.parse(evt.data);

          if (event.type === "cell.update") {
            const cell = event.cell;
            const gridCell = cellIdToGridCell(cell.id, columns);
            const column = columns[gridCell[0]];

            if (gridCell) {
              setCells((cells) => ({
                ...cells,
                [cell.id]: {
                  ...cells[cell.id],
                  row: gridCell[1] + 1,
                  col_letter: column.col_letter,
                  value: cell.value,
                  status: 0,
                },
              }));

              setSelectedCellValue(cell.value || "");

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
                  status: 1,
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
            const { id, error } = event.cell;
            const cell = cells[id];
            if (cell) {
              cell.error = error;
              setCells((cells) => ({
                ...cells,
                [id]: cell,
              }));
            }

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
  }, [runId, sheet?.uuid, wsUrlPrefix, columns, cells, numRows]);

  const onGridSelectionChange = useCallback(
    (selection) => {
      setGridSelection(selection);
      setShowFormulaMenu(false);
      if (selection.current) {
        const { cell, range } = selection.current;
        const [col, row] = cell;
        const cellId = gridCellToCellId([col, row], columns);

        setSelectedGrid([
          range.width === 1 && range.height === 1
            ? cellId
            : `${cellId}-${gridCellToCellId(
                [col + range.width - 1, row + range.height - 1],
                columns,
              )}`,
        ]);
        setSelectedCellValue(cells[cellId]?.value || "");
        setSelectedCellId(cellId);
      } else {
        setSelectedCellValue("");
        setSelectedCellId(null);
      }

      // Update selectedRows state
      if (selection.rows) {
        const newSelectedRows = [];
        selection.rows.items.forEach(([start, end]) => {
          for (let i = start; i < end; i++) {
            newSelectedRows.push(i);
          }
        });
        setSelectedRows(newSelectedRows);
      } else {
        setSelectedRows([]);
      }
    },
    [columns, cells],
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

  const deleteSelectedRows = useCallback(() => {
    if (selectedRows.length > 0) {
      selectedRows.forEach((row) => {
        onCellEdited([0, row], "");
      });
      setNumRows((prevNumRows) => prevNumRows - selectedRows.length);
      setGridSelection({
        columns: CompactSelection.empty(),
        rows: CompactSelection.empty(),
        current: undefined,
      });
    }
    setSelectedRows([]);
  }, [selectedRows, onCellEdited, setNumRows]);

  // Get the height of 100vh so we can use it to set the height of the data editor
  const dataEditorContainerHeight = useMemo(() => {
    return window.innerHeight - 110;
  }, []);

  return sheet ? (
    <Stack>
      <MemoizedSheetHeader
        sheet={sheet}
        setRunId={setRunId}
        hasChanges={hasChanges}
        onSave={saveSheet}
        sheetRunning={sheetRunning}
        setSheetRunning={setSheetRunning}
        selectedRows={selectedRows}
        deleteSelectedRows={deleteSelectedRows}
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
          <Tooltip title={selectedCellReadOnly ? "Read Only" : "Formula"}>
            <span
              style={{
                border: showFormulaMenu ? "solid 1px #e0e0e0" : "none",
              }}
            >
              <Button
                onClick={() => setShowFormulaMenu(!showFormulaMenu)}
                disabled={selectedGrid?.length !== 1 || selectedCellReadOnly}
                color="primary"
                variant="standard"
                sx={{
                  minWidth: "30px",
                  padding: "5px",
                }}
                ref={formulaMenuAnchorEl}
              >
                <SvgIcon
                  sx={{
                    width: "20px",
                    height: "20px",
                    color:
                      selectedCellId && cells[selectedCellId]?.formula
                        ? "green"
                        : "inherit",
                  }}
                >
                  <FormulaIcon />
                </SvgIcon>
              </Button>
            </span>
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
          keybindings={{ search: true }}
          smoothScrollX={true}
          smoothScrollY={true}
          rowMarkers={"both"}
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
            setSelectedColumnId(column);
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
          drawHeader={drawHeader}
          height={dataEditorContainerHeight}
        />
      </Box>
      <div id="portal" />
      <div id="sheet-column-menu" ref={editColumnAnchorEl} />
      {showEditColumnMenu && (
        <MemoizedSheetColumnMenu
          onClose={() => setShowEditColumnMenu(false)}
          column={selectedColumnId !== null ? columns[selectedColumnId] : null}
          open={showEditColumnMenu}
          setOpen={setShowEditColumnMenu}
          anchorEl={editColumnAnchorEl.current}
          columns={columns}
          updateColumn={(column) => {
            const newColumns = [...columns];
            newColumns[selectedColumnId] = column;
            setColumns(newColumns);
            updateUserChanges("columns", selectedColumnId, column);
          }}
          deleteColumn={(column) => {
            const colLetter = column.col_letter;
            setColumns((columns) => {
              const newColumns = { ...columns };
              delete newColumns[colLetter];
              updateUserChanges("columns", colLetter, null); // Mark column as deleted
              return newColumns;
            });
            setCells((cells) => {
              const newCells = { ...cells };
              Object.keys(newCells).forEach((cellId) => {
                if (newCells[cellId].col === colLetter) {
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
        isFormula={
          cells[selectedCellId]?.formula && cells[selectedCellId]?.formula?.type
        }
        readOnly={selectedCellReadOnly}
        onOpenFormula={() => {
          setCellMenuOpen(false);
          setShowFormulaMenu(true);
        }}
      />
      <MemoizedSheetFormulaMenu
        anchorEl={formulaMenuAnchorEl.current}
        open={showFormulaMenu}
        onClose={() => setShowFormulaMenu(false)}
        cellId={selectedCellId}
        selectedCell={cells[selectedCellId]}
        setFormula={(cellId, formula, spreadOutput = false) => {
          const [col, row] = cellIdToGridCell(cellId, columns);
          const cellType = columns[col].cell_type;

          if (!formula) {
            setCells((prev) => {
              const newCells = { ...prev };
              newCells[cellId].formula = null;
              return newCells;
            });
            setUserChanges((prev) => ({
              ...prev,
              cells: {
                ...prev.cells,
                [cellId]: {
                  ...prev.cells[cellId],
                  formula: null,
                  spread_output: false,
                },
              },
            }));
            return;
          }

          setCells((prev) => {
            const newCells = { ...prev };

            if (!newCells[cellId]) {
              newCells[cellId] = {
                type: cellType,
                row: row + 1,
                col_letter: columns[col].col_letter,
                value: "",
              };
            }

            newCells[cellId].formula = formula;
            newCells[cellId].spread_output = spreadOutput;
            return newCells;
          });

          setUserChanges((prev) => ({
            ...prev,
            cells: {
              ...prev.cells,
              [cellId]: {
                ...prev.cells[cellId],
                formula: formula,
                spread_output: spreadOutput,
              },
            },
          }));
        }}
      />
    </Stack>
  ) : (
    <CircularProgress />
  );
}

export default React.memo(Sheet);
