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
import { allCells } from "@glideapps/glide-data-grid-cells";
import randomColor from "randomcolor";
import { SheetColumnMenu, SheetColumnMenuButton } from "./SheetColumnMenu";
import { axios } from "../../data/axios";
import { Ws } from "../../data/ws";
import { enqueueSnackbar } from "notistack";
import SheetHeader from "./SheetHeader";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
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
import SheetBuilder from "./SheetBuilder";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";

import "@glideapps/glide-data-grid/dist/index.css";

export const SHEET_FORMULA_TYPE_NONE = 0;
export const SHEET_FORMULA_TYPE_DATA_TRANSFORMER = 1;
export const SHEET_FORMULA_TYPE_APP_RUN = 2;
export const SHEET_FORMULA_TYPE_PROCESSOR_RUN = 3;
export const SHEET_FORMULA_TYPE_AI_AGENT = 4;

export const SHEET_CELL_TYPE_TEXT = 0;
export const SHEET_CELL_TYPE_NUMBER = 1;
export const SHEET_CELL_TYPE_URI = 2;
export const SHEET_CELL_TYPE_TAGS = 3;
export const SHEET_CELL_TYPE_BOOLEAN = 4;
export const SHEET_CELL_TYPE_IMAGE = 5;
export const SHEET_CELL_TYPE_OBJECT = 6;

export const SHEET_CELL_STATUS_READY = 0;
export const SHEET_CELL_STATUS_RUNNING = 1;
export const SHEET_CELL_STATUS_ERROR = 2;

export const sheetFormulaTypes = {
  [SHEET_FORMULA_TYPE_NONE]: {
    value: "none",
    label: "None",
    description: "No formula",
    order: 0,
  },
  [SHEET_FORMULA_TYPE_AI_AGENT]: {
    value: "ai_agent",
    label: "AI Agent",
    description: "Use AI Agent to fill column",
    order: 1,
  },
  [SHEET_FORMULA_TYPE_DATA_TRANSFORMER]: {
    value: "data_transformer",
    label: "Data Transformer",
    description: "Transform data using a LiquidJS template",
    order: 2,
  },
  [SHEET_FORMULA_TYPE_APP_RUN]: {
    value: "app_run",
    label: "App Run",
    description: "Fill cell with output from an app",
    order: 3,
  },
  [SHEET_FORMULA_TYPE_PROCESSOR_RUN]: {
    value: "processor_run",
    label: "Processor Run",
    description: "Run a processor to fill cell",
    order: 4,
  },
};

export const sheetCellTypes = {
  [SHEET_CELL_TYPE_TEXT]: {
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
        readonly: cell?.formula || column?.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell.data;
    },
  },
  [SHEET_CELL_TYPE_NUMBER]: {
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
        data: parseFloat(cell.value || "0"),
        displayData: cell.value?.toString() || "0",
        readonly: cell?.formula || column?.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell.data;
    },
  },
  [SHEET_CELL_TYPE_URI]: {
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
  [SHEET_CELL_TYPE_TAGS]: {
    label: "Tags",
    value: "tags",
    description: "Comma separated list of tags",
    kind: GridCellKind.Custom,
    getDataGridCell: (cell, column) => {
      if (!cell) {
        return {
          kind: GridCellKind.Custom,
          data: {
            kind: "tags-cell",
            possibleTags: [],
            tags: [],
          },
          readonly: column?.formula?.type > 0 || false,
          allowOverlay: true,
          allowWrapping: true,
          allowEditing: true,
        };
      }

      return {
        kind: GridCellKind.Custom,
        data: {
          kind: "tags-cell",
          possibleTags:
            cell.value?.split(",").map((tag) => {
              return {
                tag: tag.trim(),
                color: randomColor({
                  seed: tag.trim(),
                  luminosity: "light",
                }),
              };
            }) || [],
          tags: cell.value?.split(",").map((tag) => tag.trim()) || [],
        },
        readonly: cell.formula || column?.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
        allowEditing: true,
      };
    },
    getCellValue: (cell) => {
      return cell?.data?.tags?.join(", ") || "";
    },
  },
  [SHEET_CELL_TYPE_BOOLEAN]: {
    label: "Boolean",
    value: "boolean",
    description: "True or false",
    kind: GridCellKind.Boolean,
    getDataGridCell: (cell, column) => {
      if (!cell) {
        return {
          kind: GridCellKind.Boolean,
          data: false,
          readonly: column?.formula?.type > 0 || false,
          allowOverlay: true,
          allowWrapping: true,
        };
      }
      return {
        kind: GridCellKind.Boolean,
        data: Boolean(cell.value),
        readonly: cell.formula || column?.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell?.data?.toString() || "";
    },
  },
  [SHEET_CELL_TYPE_IMAGE]: {
    label: "Image",
    value: "image",
    description: "Image URL",
    kind: GridCellKind.Image,
    getDataGridCell: (cell, column) => {
      if (!cell) {
        return {
          kind: GridCellKind.Image,
          data: [],
          displayData: [],
          readonly: column?.formula?.type > 0 || false,
          allowOverlay: true,
          allowWrapping: true,
        };
      }

      return {
        kind: GridCellKind.Image,
        data: cell.value?.trim().split(",") || [],
        displayData: cell.value?.trim().split(",") || [],
        readonly: cell.formula || column?.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell?.data?.join(", ") || "";
    },
  },
  [SHEET_CELL_TYPE_OBJECT]: {
    label: "Object",
    value: "object",
    description: "JSON object",
    kind: GridCellKind.Object,
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
        data:
          Object.keys(cell.value || {}).length > 0
            ? JSON.stringify(cell.value)
            : "",
        displayData:
          Object.keys(cell.value || {}).length > 0
            ? JSON.stringify(cell.value).slice(0, 100) || ""
            : "",
        readonly: cell.formula || column?.formula?.type > 0 || false,
        allowOverlay: true,
        allowWrapping: true,
      };
    },
    getCellValue: (cell) => {
      return cell.data ? JSON.parse(cell.data) : {};
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
  const [lastRunAt, setLastRunAt] = useState(null);
  const [userChanges, setUserChanges] = useState({
    columns: {},
    cells: {},
    numRows: null,
    addedColumns: [],
  });
  const columnMenuAnchorDivEl = useRef(null);
  const [columnMenuAnchorEl, setColumnMenuAnchorEl] = useState(null);
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
  const [showChat, setShowChat] = useState(false);

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

  const getPrefixFromFormulaType = useCallback((formulaType) => {
    if (formulaType === SHEET_FORMULA_TYPE_PROCESSOR_RUN) {
      return "PR";
    }
    if (formulaType === SHEET_FORMULA_TYPE_DATA_TRANSFORMER) {
      return "DT";
    }
    if (formulaType === SHEET_FORMULA_TYPE_AI_AGENT) {
      return "AI";
    }
    return "AR";
  }, []);

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
        drawContent();
        return;
      }

      const colLetter = column.col_letter;
      const cellId = `${colLetter}${row + 1}`;
      const cell = cells[cellId];

      if (!cell || !cell.status) {
        drawContent();
      }

      if (cell?.status === SHEET_CELL_STATUS_RUNNING) {
        // Add a dark yellow background to the cell
        ctx.save();
        ctx.fillStyle = "rgba(255, 255, 0, 0.1)";
        ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
        ctx.restore();

        // Draw a spinner in the center of the cell
        ctx.save();
        ctx.fillStyle = "#000000";
        ctx.font = "12px Arial";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText("Running...", rect.x + 10, rect.y + rect.height / 2);
        ctx.restore();

        return;
      }

      if (cell?.status === SHEET_CELL_STATUS_ERROR) {
        // Visually indicate that the cell has an error with a red background
        ctx.save();
        ctx.fillStyle = "#FF0000CC";
        ctx.fillRect(rect.x, rect.y, rect.width, rect.height);

        // Draw error message from cell.error
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "12px Arial";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";

        const padding = 10;
        const maxWidth = rect.width - 2 * padding;
        const errorText = (cell.error || "Error").slice(0, 100);

        ctx.fillText(
          errorText,
          rect.x + 10,
          rect.y + rect.height / 2,
          maxWidth,
        );

        ctx.restore();
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

      // Draw icon at the left of the cell
      const formulaType = cells[cellId]?.formula?.type;
      const formulaIconImage =
        formulaType === SHEET_FORMULA_TYPE_PROCESSOR_RUN
          ? getProviderIconImage(
              cells[cellId]?.formula?.data?.provider_slug || "promptly",
              false,
            )
          : getProviderIconImage("promptly", false);

      if (formulaIconImage) {
        // Draw this image on the canvas
        const img = new Image();
        img.src = formulaIconImage;

        img.onload = () => {
          const pixelRatio = window.devicePixelRatio || 1;
          ctx.save();
          ctx.scale(pixelRatio, pixelRatio);
          // Draw a background behind the icon
          ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
          ctx.fillRect(
            iconX - rect.width + iconSize + margin + 5,
            iconY - 5,
            iconSize + 30,
            iconSize + 5,
          );

          // Add a text next to the icon indicating the formula type
          ctx.fillStyle = "#107C41";
          ctx.font = "bold 10px Lato";
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillText(
            getPrefixFromFormulaType(formulaType),
            iconX - rect.width + iconSize + margin + 10,
            iconY + iconSize / 2,
          );

          ctx.drawImage(
            img,
            iconX - rect.width + iconSize + margin + 25,
            iconY,
            iconSize,
            iconSize,
          );
          ctx.restore();
        };
      }
    },
    [cells, columns, getPrefixFromFormulaType],
  );

  const updateColumnMenuPosition = useCallback(
    (rect) => {
      if (
        columnMenuAnchorDivEl.current &&
        showEditColumnMenu &&
        selectedColumnId !== null
      ) {
        const sheetColumnMenuRect =
          columnMenuAnchorDivEl.current.getBoundingClientRect();
        setColumnMenuAnchorEl((prev) => ({
          ...prev,
          getBoundingClientRect: () =>
            DOMRect.fromRect({
              ...rect,
              y: sheetColumnMenuRect.y,
            }),
        }));
      }
    },
    [showEditColumnMenu, selectedColumnId],
  );

  const drawHeader = useCallback(
    (args, drawContent) => {
      drawContent();

      const { column, ctx, menuBounds, rect, columnIndex } = args;

      const gridColumn =
        columns?.find((c) => c.col_letter === column.icon) || null;

      if (!gridColumn) {
        return;
      }

      if (
        !gridColumn.formula ||
        gridColumn.formula.type === SHEET_FORMULA_TYPE_NONE
      ) {
        return;
      }

      // Add text indicating the formula type
      ctx.fillStyle = "#107C41";
      ctx.font = "bold 12px Lato";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(
        getPrefixFromFormulaType(gridColumn.formula.type),
        menuBounds.x - 30,
        menuBounds.y + menuBounds.height / 2 + 1,
        100,
      );

      const headerIconImage =
        gridColumn.formula.type === SHEET_FORMULA_TYPE_PROCESSOR_RUN
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
          ctx.save();
          ctx.scale(pixelRatio, pixelRatio);
          ctx.drawImage(
            img,
            menuBounds.x - 10,
            menuBounds.y + 8,
            menuBounds.width - 15,
            menuBounds.height - 15,
          );
          ctx.restore();
        };
      }

      if (
        columnMenuAnchorDivEl.current &&
        showEditColumnMenu &&
        selectedColumnId === columnIndex
      ) {
        updateColumnMenuPosition(rect);
      }
    },
    [
      columns,
      showEditColumnMenu,
      selectedColumnId,
      columnMenuAnchorDivEl,
      updateColumnMenuPosition,
      getPrefixFromFormulaType,
    ],
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
          setLastRunAt(data?.updated_at || null);
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
          columns[col].formula ||
            columns[col].formula?.type === SHEET_FORMULA_TYPE_NONE ||
            false,
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

  const onColumnResize = useCallback(
    (column, width) => {
      const colIndex = columns.findIndex(
        (c) => c.col_letter === column.colLetter,
      );

      setColumns((prev) => {
        const newColumns = [...prev];
        newColumns[colIndex].width = width;
        updateUserChanges("columns", column.colLetter, {
          ...column,
          width: width,
        });
        return newColumns;
      });
    },
    [updateUserChanges, columns],
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

  const onHeaderMenuClick = useCallback(
    (column, bounds) => {
      setGridSelection({
        columns: CompactSelection.empty(),
        rows: CompactSelection.empty(),
        current: undefined,
      });

      setShowEditColumnMenu(!showEditColumnMenu);

      setColumnMenuAnchorEl({
        getBoundingClientRect: () => DOMRect.fromRect(bounds),
      });

      setSelectedColumnId(column);
    },
    [showEditColumnMenu],
  );

  const onHeaderClicked = useCallback(
    (column, event) => {
      // When the user clicks on the right half of the header, set showEditColumnMenu to true
      const { localEventX, bounds } = event;
      if (localEventX > (2 * bounds?.width) / 3) {
        setSelectedColumnId(column);
        setShowEditColumnMenu(!showEditColumnMenu);

        setColumnMenuAnchorEl({
          getBoundingClientRect: () => DOMRect.fromRect(bounds),
        });
      }
    },
    [showEditColumnMenu, setSelectedColumnId],
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
                  error: cells[cell.id]?.error || null,
                  status: cell.value ? 0 : cells[cell.id]?.status || 0,
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
              setLastRunAt(new Date());
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
              persist: true,
            });
            wsRef.current.close();
            wsRef.current = null;
          } else if (event.type === "cell.error") {
            const { id, error } = event.cell;
            setCells((prevCells) => ({
              ...prevCells,
              [id]: {
                ...prevCells[id],
                status: SHEET_CELL_STATUS_ERROR,
                error: error,
              },
            }));

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
  }, [runId, sheet?.uuid, wsUrlPrefix, columns, numRows]);

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
        setSelectedCellValue(
          cells[cellId]?.status === SHEET_CELL_STATUS_ERROR
            ? cells[cellId]?.error || ""
            : cells[cellId]?.value || "",
        );
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

  const toggleChat = () => setShowChat(!showChat);

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
        lastRunAt={lastRunAt}
        selectedGrid={selectedGrid}
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
                updateColumnMenuPosition({
                  x: e.clientX,
                  y: e.clientY,
                });
              };

              const stopResize = (e) => {
                window.removeEventListener("mousemove", resize);
                window.removeEventListener("mouseup", stopResize);
                updateColumnMenuPosition({
                  x: e.clientX,
                  y: e.clientY,
                });
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
          <LayoutRenderer>
            {typeof selectedCellValue === "object"
              ? JSON.stringify(selectedCellValue)
              : selectedCellValue}
          </LayoutRenderer>
        </Box>
        <Button
          onClick={toggleChat}
          color="primary"
          variant="outlined"
          sx={{
            m: 2,
            mr: 0,
            minWidth: "120px",
            borderRadius: "4px !important",
            backgroundColor: showChat ? "#f0f0f0" : "inherit",
          }}
          startIcon={<AutoFixHighIcon />}
        >
          AI Builder
        </Button>
      </Box>
      <div id="sheet-column-menu" ref={columnMenuAnchorDivEl} />
      <Stack direction="row" spacing={2}>
        <Box sx={{ flex: showChat ? "70%" : "100%", transition: "flex 0.3s" }}>
          <DataEditor
            ref={sheetRef}
            onPaste={onPaste}
            customRenderers={allCells}
            getCellContent={getCellContent}
            columns={gridColumns}
            keybindings={{ search: true }}
            smoothScrollX={true}
            smoothScrollY={true}
            rowMarkers={"both"}
            rowHeight={40}
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
            onHeaderMenuClick={onHeaderMenuClick}
            onHeaderClicked={onHeaderClicked}
            onColumnResize={onColumnResize}
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
        <Box
          sx={{
            flex: "30%",
            borderLeft: "1px solid #e0e0e0",
            height: "100%",
            display: showChat ? "block" : "none",
          }}
        >
          <SheetBuilder
            sheetId={sheet.uuid}
            open={showChat}
            addOrUpdateColumns={(columns) => {
              setColumns((prevColumns) => {
                const newColumns = [...prevColumns];
                columns.forEach((column) => {
                  const index = newColumns.findIndex(
                    (c) => c.col_letter === column.col_letter,
                  );

                  if (index !== -1) {
                    newColumns[index] = column;
                  } else {
                    newColumns.push(column);
                  }
                });

                return newColumns;
              });
              setUserChanges((prev) => ({
                ...prev,
                columns: {
                  ...prev.columns,
                  ...columns,
                },
              }));
            }}
            addOrUpdateCells={(cells) => {
              const cellsMap = cells.reduce((acc, cell) => {
                acc[`${cell.col_letter}${cell.row}`] = cell;
                return acc;
              }, {});
              setCells((prev) => ({
                ...prev,
                ...cellsMap,
              }));

              setUserChanges((prev) => ({
                ...prev,
                cells: {
                  ...prev.cells,
                  ...cellsMap,
                },
              }));

              sheetRef.current?.updateCells(
                Object.keys(cellsMap).map((cellId) => ({
                  cell: cellIdToGridCell(cellId, columns),
                })),
              );
            }}
          />
        </Box>
      </Stack>
      <div id="portal" />
      <MemoizedSheetColumnMenu
        column={selectedColumnId !== null ? columns[selectedColumnId] : null}
        open={showEditColumnMenu}
        setOpen={setShowEditColumnMenu}
        anchorEl={columnMenuAnchorEl}
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
            const newColumns = columns.filter(
              (c) => c.col_letter !== colLetter,
            );
            updateUserChanges("columns", colLetter, null);
            return newColumns;
          });
          setCells((cells) => {
            const newCells = { ...cells };
            Object.keys(newCells).forEach((cellId) => {
              if (newCells[cellId].col_letter === colLetter) {
                delete newCells[cellId];
                updateUserChanges("cells", cellId, null);
              }
            });
            return newCells;
          });
          setSelectedColumnId(null);
        }}
      />
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
