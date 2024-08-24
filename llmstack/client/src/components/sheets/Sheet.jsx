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

const SheetHeader = ({ sheet, setRunId }) => {
  const navigate = useNavigate();
  const saveSheet = () => {
    axios()
      .patch(`/api/sheets/${sheet.uuid}`, sheet)
      .then((response) => {
        enqueueSnackbar("Sheet saved successfully", {
          variant: "success",
        });
      })
      .catch((error) => {
        console.error(error);
        enqueueSnackbar(
          `Error saving sheet: ${
            error?.response?.data?.detail || error.message
          }`,
          {
            variant: "error",
          },
        );
      });
  };

  const runSheet = () => {
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
          {
            variant: "error",
          },
        );
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
            <Button variant="contained" size="medium" onClick={saveSheet}>
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
        })
        .catch((error) => {
          console.error(error);
        });
    }
  }, [sheetId]);

  useEffect(() => {
    setSheet((sheet) => ({
      ...sheet,
      data: {
        ...(sheet?.data || {}),
        columns: columns,
      },
    }));
  }, [columns]);

  useEffect(() => {
    if (Object.keys(cells).length > 0) {
      setSheet((sheet) => ({
        ...sheet,
        data: {
          ...(sheet?.data || {}),
          cells: cells,
        },
      }));
    }
  }, [cells]);

  useEffect(() => {
    setSheet((sheet) => ({
      ...sheet,
      data: {
        ...(sheet?.data || {}),
        total_rows: numRows,
      },
    }));
  }, [numRows]);

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
      <SheetHeader sheet={sheet} setRunId={setRunId} />
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
          onRowAppended={() => {
            setCells((cells) => ({
              ...cells,
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
            setNumRows(numRows + 1);
          }}
          width={"100%"}
          getCellsForSelection={true}
          rightElement={
            <SheetColumnMenuButton
              addColumn={(column) => {
                setColumns([...columns, column]);
              }}
              columns={columns}
            />
          }
          onCellEdited={(cell, value) => {
            setCells((cells) => ({
              ...cells,
              [cell[1]]: {
                ...cells[cell[1]],
                [cell[0]]: {
                  ...(cells[cell[1]]?.[cell[0]] || {}),
                  ...value,
                  kind: columns[cell[0]].kind,
                  data: value.data,
                  displayData: value.displayData || value.data,
                },
              },
            }));
            sheetRef.current?.updateCells([{ cell: cell }]);
          }}
          onHeaderMenuClick={(column, bounds) => {
            setSelectedColumnId(column);
            editColumnAnchorEl.current = {
              getBoundingClientRect: () => DOMRect.fromRect(bounds),
            };
            setShowEditColumnMenu(true);
          }}
          onColumnResize={(column, width) => {
            setColumns((columns) => {
              const newColumns = [...columns];
              const columnIndex = newColumns.findIndex(
                (c) => c.col === column.col,
              );
              newColumns[columnIndex].width = width;
              return newColumns;
            });
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
              return newColumns;
            });
          }}
          deleteColumn={(column) => {
            setColumns((columns) => {
              return columns.filter((c) => c.col !== column.col);
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
