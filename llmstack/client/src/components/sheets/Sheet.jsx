import { useCallback, useEffect, useRef, useState } from "react";
import { Box, Stack, CircularProgress } from "@mui/material";
import {
  DataEditor,
  GridCellKind,
  GridColumnIcon,
} from "@glideapps/glide-data-grid";
import { SheetColumnMenu, SheetColumnMenuButton } from "./SheetColumnMenu";
import { axios } from "../../data/axios";
import { Ws } from "../../data/ws";
import { enqueueSnackbar } from "notistack";
import SheetHeader from "./SheetHeader";

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

  const getCellContent = useCallback(
    ([column, row]) => {
      const colLetter = columns[column].col;
      const cell = cells[`${colLetter}${row + 1}`];

      return {
        kind:
          (cell?.kind === "app_run" || cell?.kind === "processor_run"
            ? GridCellKind.Text
            : cell?.kind) || GridCellKind.Custom,
        displayData: cell?.display_data || "",
        data: cell?.display_data || "",
        allowOverlay: true,
        allowWrapping: true,
        skeletonWidth: 80,
        skeletonWidthVariability: 25,
      };
    },
    [cells, columns],
  );

  const parseSheetColumnsIntoGridColumns = (columns) => {
    if (!columns) {
      return [];
    }

    return columns.map((column, index) => {
      return {
        col: columnIndexToLetter(index),
        title: column.title,
        kind: column.kind,
        data: column.data,
        hasMenu: true,
        icon:
          column.kind === "app_run" || column.kind === "processor_run"
            ? GridColumnIcon.HeaderRollup
            : GridColumnIcon.HeaderString,
        width: column.width || 300,
      };
    });
  };

  useEffect(() => {
    if (sheetId) {
      axios()
        .get(`/api/sheets/${sheetId}?include_cells=true`)
        .then((response) => {
          setSheet(response.data);
          setCells(response.data?.cells || {});
          setSheetRunning(response.data?.running || false);
          setColumns(
            parseSheetColumnsIntoGridColumns(response.data?.columns || []),
          );
          setNumRows(response.data?.total_rows || 0);
          setUserChanges({
            columns: {},
            cells: {},
            numRows: null,
            addedColumns: [],
          });
        })
        .catch((error) => {
          console.error(error);
        });
    }
  }, [sheetId]);

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
        const newCells = {
          ...prevCells,
          [cellId]: {
            ...(prevCells[cellId] || {}),
            row: row + 1,
            col: columns[col]?.col,
            kind: GridCellKind.Text,
            display_data: value.displayData || value.data,
          },
        };
        updateUserChanges("cells", cellId, value);
        return newCells;
      });
      sheetRef.current?.updateCells([{ cell: cell }]);
    },
    [columns, updateUserChanges, sheetRef],
  );

  const onRowAppended = useCallback(() => {
    const newRowIndex = numRows + 1;
    const newCells = columns.reduce((acc, column) => {
      const cellId = `${column.col}${newRowIndex}`;
      acc[cellId] = {
        kind: GridCellKind.Text,
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

              setCells((cells) => ({
                ...cells,
                [cell.id]: {
                  ...cells[cell.id],
                  kind: column?.kind || GridCellKind.Text,
                  data: cell.data,
                  display_data: cell.data,
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
            setSheetRunning(running && event.sheet.id === sheet.uuid);

            // If running is false, we can disconnect
            if (!running) {
              ws.close();
              setRunId(null);
            }
          }
        });

        ws.send(JSON.stringify({ event: "run" }));
      }
    }
  }, [runId, sheet?.uuid, wsUrlPrefix, columns]);

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
      <Box>
        <DataEditor
          ref={sheetRef}
          getCellContent={getCellContent}
          columns={columns}
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
            setShowEditColumnMenu(true);
          }}
          onColumnResize={(column, width) => {
            onColumnChange(
              columns.findIndex((c) => c.col === column.col),
              { ...column, width },
            );
          }}
          rows={numRows}
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
              return newColumns;
            });
          }}
          deleteColumn={(column) => {
            setColumns((columns) => {
              const newColumns = columns.filter((c) => c.col !== column.col);
              updateUserChanges("columns", column.col, null); // Mark column as deleted
              return newColumns;
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
