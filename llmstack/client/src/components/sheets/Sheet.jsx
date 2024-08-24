import { useCallback, useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Stack,
  Typography,
  CircularProgress,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  DataEditor,
  GridCellKind,
  GridColumnIcon,
} from "@glideapps/glide-data-grid";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useNavigate } from "react-router-dom";
import { SheetColumnMenu, SheetColumnMenuButton } from "./SheetColumnMenu";
import { axios } from "../../data/axios";
import { Ws } from "../../data/ws";
import { enqueueSnackbar } from "notistack";

import "@glideapps/glide-data-grid/dist/index.css";

const SheetHeader = ({ sheet, setRunId, hasChanges, onSave }) => {
  const navigate = useNavigate();

  const saveSheet = () => {
    onSave();
  };

  const runSheet = () => {
    onSave().then(() => {
      axios()
        .post(`/api/sheets/${sheet.uuid}/run`)
        .then((response) => {
          setRunId(response.data.run_id);
        })
        .catch((error) => {
          console.error(error);
          enqueueSnackbar(
            `Error running sheet: ${
              error?.response?.data?.detail || error.message
            }`,
            { variant: "error" },
          );
        });
    });
  };

  return (
    <Stack>
      <Typography variant="h5" className="section-header">
        <Stack
          direction={"row"}
          sx={{ justifyContent: "space-between", alignItems: "center" }}
        >
          <Stack direction="row" alignItems="center" spacing={2}>
            <Tooltip title="Back to Sheets List">
              <IconButton
                onClick={() => navigate("/sheets")}
                sx={{ color: "action.disabled" }}
              >
                <ArrowBackIcon
                  fontSize="small"
                  sx={{
                    color: "action.disabled",
                    padding: 0,
                  }}
                />
              </IconButton>
            </Tooltip>
            <Stack>
              {sheet?.name}
              <Typography variant="caption" sx={{ color: "#666" }}>
                {sheet?.description || sheet?.data?.description || ""}
              </Typography>
            </Stack>
          </Stack>
          <Stack direction={"row"} gap={1}>
            <Button
              variant="contained"
              size="medium"
              onClick={saveSheet}
              disabled={!hasChanges}
            >
              Save
            </Button>
            <Button variant="contained" size="medium" onClick={runSheet}>
              Run
            </Button>
          </Stack>
        </Stack>
      </Typography>
    </Stack>
  );
};

function Sheet(props) {
  const { sheetId } = props;
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
      // Find the column in cells
      const col = columns[column].col;
      const cell = cells[row]?.[col];

      return {
        kind:
          (cell?.kind === "app_run" ? GridCellKind.Text : cell?.kind) ||
          columns[column].kind,
        displayData: cell?.displayData || cell?.data || "",
        data: cell?.data || "",
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

    return columns.map((column) => {
      return {
        col: column.col,
        title: column.title,
        kind: column.kind,
        data: column.data,
        hasMenu: true,
        icon: GridColumnIcon.HeaderString,
        width: column.width || 200,
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
      setCells((prevCells) => {
        const newCells = {
          ...prevCells,
          [cell[1]]: {
            ...prevCells[cell[1]],
            [columns[cell[0]].col]: {
              ...(prevCells[cell[1]]?.[columns[cell[0]].col] || {}),
              ...value,
              kind: columns[cell[0]].kind,
              data: value.data,
              displayData: value.displayData || value.data,
            },
          },
        };
        updateUserChanges("cells", `${cell[1]}-${columns[cell[0]].col}`, value);
        return newCells;
      });
      sheetRef.current?.updateCells([{ cell: cell }]);
    },
    [columns, updateUserChanges],
  );

  const onRowAppended = useCallback(() => {
    setCells((prevCells) => ({
      ...prevCells,
      [numRows]: {
        ...columns.reduce((acc, column) => {
          acc[column.col] = {
            kind: GridCellKind.Text,
            displayData: "",
            data: "",
          };
          return acc;
        }, {}),
      },
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
        data: {
          ...sheet.data,
          columns: columns,
          cells: cells,
          total_rows: numRows,
        },
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
            const [row, col] = cell.id.split("-");
            const column = columns.find((c) => c.col === col);

            setCells((cells) => ({
              ...cells,
              [row]: {
                ...cells[row],
                [col]: {
                  ...cells[row]?.[col],
                  ...{
                    kind: column?.kind || GridCellKind.Text,
                    data: cell.data,
                    displayData: cell.data,
                  },
                },
              },
            }));

            sheetRef.current?.updateCells([
              { cell: [columns.findIndex((c) => c.col === col), row] },
            ]);
          } else if (event.type === "cell.updating") {
            const cell = event.cell;
            const [row, col] = cell.id.split("-");

            setCells((cells) => ({
              ...cells,
              [row]: {
                ...cells[row],
                [col]: {
                  ...cells[row]?.[col],
                  ...{
                    kind: GridCellKind.Loading,
                  },
                },
              },
            }));

            sheetRef.current?.updateCells([
              { cell: [columns.findIndex((c) => c.col === col), row] },
            ]);
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
            setSelectedColumnId(column);
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
              newColumns[selectedColumnId] = column;
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
