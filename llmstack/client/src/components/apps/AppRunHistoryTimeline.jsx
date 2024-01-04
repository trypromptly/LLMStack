import {
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  Grid,
  LinearProgress,
  Pagination,
  Stack,
  SvgIcon,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import ArrowOutwardIcon from "@mui/icons-material/ArrowOutward";
import TableRowsIcon from "@mui/icons-material/TableRows";
import { useEffect, useMemo, useState } from "react";
import moment from "moment";
import AceEditor from "react-ace";
import UAParser from "ua-parser-js";
import MarkdownRenderer from "./MarkdownRenderer";
import { axios } from "../../data/axios";
import { ReactComponent as DiscordIcon } from "../../assets/images/icons/discord.svg";
import { ReactComponent as SlackIcon } from "../../assets/images/icons/slack.svg";
import { ReactComponent as TwilioIcon } from "../../assets/images/icons/twilio.svg";
import "ace-builds/src-noconflict/mode-sh";
import "ace-builds/src-noconflict/theme-chrome";
import { useRecoilValue } from "recoil";
import { appsBriefState } from "../../data/atoms";

const browserAndOSFromUACache = {};

const browserAndOSFromUA = (userAgent) => {
  if (browserAndOSFromUACache[userAgent]) {
    return browserAndOSFromUACache[userAgent];
  }

  if (userAgent.startsWith("Slackbot")) {
    browserAndOSFromUACache[userAgent] = "Slack";
    return browserAndOSFromUACache[userAgent];
  } else if (userAgent.startsWith("Discord")) {
    browserAndOSFromUACache[userAgent] = "Discord";
    return browserAndOSFromUACache[userAgent];
  }

  const parser = new UAParser(userAgent);
  const os = parser.getOS();
  const browser = parser.getBrowser();

  browserAndOSFromUACache[userAgent] = `${browser.name} / ${os.name}`;

  return browserAndOSFromUACache[userAgent];
};

const allcolumns = [
  {
    id: "created_at",
    label: "Time",
    format: (value) => moment.utc(value).local().fromNow(),
  },
  { id: "name", label: "Name" },
  { id: "session_key", label: "Session" },
  { id: "request_user_email", label: "User" },
  { id: "request_location", label: "Location" },
  {
    id: "response_time",
    label: "Time",
    format: (value) => `${value.toFixed(2)}s`,
  },
  { id: "response_status", label: "Status" },
];

const ExpandedRowItem = ({ label, value, content_type = null }) => {
  const renderedBody = useMemo(() => {
    if (content_type === "text/markdown") {
      return <MarkdownRenderer>{value}</MarkdownRenderer>;
    } else if (content_type === "application/json") {
      // Format JSON string
      let formattedJSON = value
        .replace(/'/g, '"')
        .replace(/None/g, "null")
        .replace(/True/g, "true")
        .replace(/False/g, "false");

      try {
        formattedJSON = JSON.stringify(JSON.parse(formattedJSON), null, 2);
      } catch (error) {}

      return (
        <AceEditor
          mode="json"
          theme="chrome"
          value={formattedJSON}
          readOnly={true}
          width="100%"
          height="200px"
          showPrintMargin={false}
          showLineNumbers={false}
          showGutter={false}
          onLoad={(editor) => {
            const maxEditorHeight = 200;

            const updateEditorHeight = () => {
              const session = editor.getSession();
              const lineNumber = session.getLength();
              const lineHeight = editor.renderer.lineHeight;
              const calculatedHeight = lineNumber * lineHeight;
              const height = Math.min(calculatedHeight, maxEditorHeight);

              editor.container.style.height = `${height}px`;
              editor.resize();
            };

            // Hide gutter
            editor.setOption("showGutter", false);

            // Resize editor on content change
            editor.getSession().on("change", updateEditorHeight);

            // Initial height update
            updateEditorHeight();
          }}
        />
      );
    } else {
      return (
        <Typography
          variant="body2"
          sx={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
            color: "#1b5c85",
          }}
        >
          {value}
        </Typography>
      );
    }
  }, [value, content_type]);

  return (
    <Box>
      <Typography variant="caption" style={{ fontWeight: 600, color: "gray" }}>
        {label}
      </Typography>
      {renderedBody}
    </Box>
  );
};

const FilterBar = ({ apps, sessions, users, onFilter }) => {
  const [selectedApp, setSelectedApp] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);

  return (
    <Stack
      direction="row"
      spacing={1}
      sx={{
        padding: "10px 0",
      }}
    >
      <Autocomplete
        id="app-selector"
        sx={{ width: 250 }}
        options={apps}
        autoHighlight
        getOptionLabel={(option) => option.name || ""}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            label="App"
            inputProps={{
              ...params.inputProps,
              autoComplete: "new-password",
            }}
          />
        )}
        renderOption={(props, option) => (
          <Box
            component="li"
            sx={{
              fontSize: 14,
              "& > span": {
                marginRight: 2,
                fontSize: 18,
              },
            }}
            {...props}
          >
            {option.name}
          </Box>
        )}
        onChange={(event, value) => {
          setSelectedApp(value);
        }}
      />
      <Autocomplete
        id="session-selector"
        sx={{ width: 300 }}
        options={sessions}
        autoHighlight
        getOptionLabel={(option) => option.name || ""}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            label="Session"
            inputProps={{
              ...params.inputProps,
              autoComplete: "new-password",
            }}
          />
        )}
        renderOption={(props, option) => (
          <Box
            component="li"
            sx={{
              fontSize: 14,
              "& > span": {
                marginRight: 2,
                fontSize: 18,
              },
            }}
            {...props}
          >
            {option.name}
          </Box>
        )}
        isOptionEqualToValue={(option, value) => option.name === value.name}
        onChange={(event, value) => {
          setSelectedSession(value);
        }}
      />
      <Autocomplete
        id="user-selector"
        sx={{ width: 250 }}
        options={users}
        autoHighlight
        getOptionLabel={(option) => option.name || ""}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            label="User"
            inputProps={{
              ...params.inputProps,
              autoComplete: "new-password",
            }}
          />
        )}
        renderOption={(props, option) => (
          <Box
            component="li"
            sx={{
              fontSize: 14,
              "& > span": {
                marginRight: 2,
                fontSize: 18,
              },
            }}
            {...props}
          >
            {option.name}
          </Box>
        )}
        isOptionEqualToValue={(option, value) => option.name === value.name}
        onChange={(event, value) => {
          setSelectedUser(value);
        }}
      />
      <Button
        type="primary"
        sx={{
          textTransform: "none",
        }}
        variant="contained"
        onClick={() => {
          onFilter({
            app_uuid: selectedApp?.uuid || null,
            session_key: selectedSession?.name || null,
            request_user_email: selectedUser?.name || null,
            endpoint_uuid: null,
          });
        }}
      >
        Filter
      </Button>
    </Stack>
  );
};

export function AppRunHistoryTimeline(props) {
  const { filter, filteredColumns, showFilterBar } = props;
  const apps = useRecoilValue(appsBriefState);
  const [rows, setRows] = useState([]);
  const [expandedRows, setExpandedRows] = useState({});
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(null);
  const [filters, setFilters] = useState(filter || { page: 1 });
  const columns = useMemo(() => {
    return allcolumns.filter(
      (column) => !filteredColumns || filteredColumns.includes(column.id),
    );
  }, [filteredColumns]);

  const renderTableCell = (column, row) => {
    const value = row[column.id];

    if (column.id === "name") {
      if (row.app_uuid !== null) {
        const app = apps.find((app) => app.uuid === row.app_uuid);
        if (app) {
          return (
            <Button sx={{ textTransform: "none" }} href={`/apps/${app.uuid}`}>
              {app.name}
            </Button>
          );
        } else {
          return "Deleted App";
        }
      }
      return "Playground";
    } else if (column.id === "type") {
      return (
        <Tooltip title={row.app_uuid !== null ? "App" : "Endpoint"}>
          {row.app_uuid !== null ? (
            <TableRowsIcon sx={{ color: "#999" }} size="small" />
          ) : (
            <ArrowOutwardIcon sx={{ color: "#999" }} size="small" />
          )}
        </Tooltip>
      );
    } else if (column.id === "request_user_email") {
      if (row.platform_data?.slack?.user_email) {
        return (
          <Box>
            <SvgIcon
              component={SlackIcon}
              fontSize="8"
              sx={{
                marginRight: "5px",
                color: "#555",
                verticalAlign: "middle",
              }}
            />
            {row.platform_data?.slack?.user_email}
          </Box>
        );
      } else if (row.platform_data?.discord?.global_name) {
        return (
          <Box>
            <SvgIcon
              component={DiscordIcon}
              fontSize="8"
              sx={{
                marginRight: "5px",
                color: "#555",
                verticalAlign: "middle",
              }}
            />
            {row.platform_data?.discord?.global_name}
          </Box>
        );
      } else if (row.platform_data?.twilio?.requestor) {
        return (
          <Box>
            <SvgIcon
              component={TwilioIcon}
              fontSize="8"
              sx={{
                marginRight: "5px",
                color: "#555",
                verticalAlign: "middle",
              }}
            />
            {row.platform_data?.twilio?.requestor}
          </Box>
        );
      } else if (
        row.request_user_email === null ||
        row.request_user_email === ""
      ) {
        return "Anonymous";
      }
    } else if (
      column.id === "request_location" &&
      (row.request_location === null || row.request_location === "")
    ) {
      return "Unknown";
    } else if (column.id === "response_status") {
      return (
        <Chip
          size="small"
          label={row.response_status}
          color={row.response_status < 300 ? "success" : "error"}
          sx={{
            borderRadius: "5px",
          }}
        />
      );
    } else if (column.id === "created_at") {
      return (
        <Tooltip
          title={moment.utc(value).local().format("D-MMM-YYYY h:mm:ss A")}
        >
          <span>{column.format ? column.format(value) : value}</span>
        </Tooltip>
      );
    }

    return column.format ? column.format(value) : value;
  };

  const handleRowClick = (row) => {
    setRows(
      rows.map((r) => {
        if (r.request_uuid === row.request_uuid) {
          return {
            ...r,
            expand: !r.expand,
          };
        }

        return r;
      }),
    );

    if (!expandedRows[row.request_uuid]) {
      axios()
        .get(`/api/history/${row.request_uuid}`)
        .then((response) => {
          setExpandedRows({
            ...expandedRows,
            [row.request_uuid]: response.data,
          });
        });
    }
  };

  useEffect(() => {
    setLoading(true);
    axios()
      .get(
        `/api/history?${Object.keys(filters)
          .map((key) => `${key}=${filters[key]}`)
          .join("&")}`,
      )
      .then((response) => {
        setTotal(response.data?.count);
        setRows(
          (response.data?.results || []).map((row) => ({
            ...row,
            expand: false,
          })),
        );
      })
      .catch((error) => {
        console.log(error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [total, filters]);

  return (
    <Grid container spacing={1}>
      <TableContainer sx={{ padding: "10px 20px" }}>
        {showFilterBar && (
          <Box>
            <FilterBar
              apps={apps}
              sessions={Array.from(
                new Set(
                  rows
                    .filter(
                      (row) =>
                        row.session_key !== null && row.session_key !== "",
                    )
                    .map((row) => row.session_key),
                ),
              ).map((session_key) => ({ name: session_key }))}
              users={Array.from(
                new Set(
                  rows
                    .filter(
                      (row) =>
                        row.request_user_email !== null &&
                        row.request_user_email !== "",
                    )
                    .map((row) => row.request_user_email),
                ),
              ).map((request_user_email) => ({ name: request_user_email }))}
              onFilter={(filters) => setFilters({ ...filters, ...{ page: 1 } })}
            />
            <Divider />
          </Box>
        )}
        <Table stickyHeader aria-label="sticky table">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{
                    fontWeight: "bold",
                    textAlign: "left",
                  }}
                >
                  {column.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => {
              return [
                <TableRow
                  hover
                  role="checkbox"
                  tabIndex={-1}
                  key={row.request_uuid}
                  sx={{
                    cursor: "pointer",
                    backgroundColor: row.expand ? "#f5f5f5" : "inherit",
                  }}
                  onClick={() => handleRowClick(row)}
                >
                  {columns.map((column) => {
                    return (
                      <TableCell
                        key={column.id}
                        align={column.align}
                        style={{
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {renderTableCell(column, row)}
                      </TableCell>
                    );
                  })}
                </TableRow>,
                <TableRow key={`${row.request_uuid}_details`}>
                  <TableCell
                    style={{
                      paddingBottom: 0,
                      paddingTop: 0,
                      border: 0,
                    }}
                    colSpan={12}
                  >
                    <Collapse in={row.expand} timeout="auto" unmountOnExit>
                      <Box sx={{ margin: 1 }}>
                        {!expandedRows[row.request_uuid] && (
                          <CircularProgress />
                        )}
                        {expandedRows[row.request_uuid] && (
                          <Grid
                            container
                            spacing={1}
                            sx={{
                              marginBottom: 1,
                              border: "1px solid #eee",
                            }}
                          >
                            <Grid
                              item
                              xs={12}
                              md={6}
                              sx={{ borderRight: "solid 1px #eee" }}
                            >
                              <Stack
                                direction="column"
                                spacing={1}
                                sx={{ marginBottom: 1 }}
                              >
                                <ExpandedRowItem
                                  label="Request"
                                  value={row.request_uuid}
                                />
                                {row.app_uuid && (
                                  <ExpandedRowItem
                                    label="Session"
                                    value={
                                      expandedRows[row.request_uuid].session_key
                                    }
                                  />
                                )}
                                <ExpandedRowItem
                                  label="IP Address"
                                  value={
                                    expandedRows[row.request_uuid].request_ip
                                  }
                                />
                                <ExpandedRowItem
                                  label="Platform"
                                  value={browserAndOSFromUA(
                                    row.request_user_agent,
                                  )}
                                />
                                <ExpandedRowItem
                                  label="User Agent"
                                  value={
                                    expandedRows[row.request_uuid]
                                      .request_user_agent
                                  }
                                />
                              </Stack>
                            </Grid>
                            <Grid item xs={12} md={6}>
                              <Stack
                                direction="column"
                                spacing={1}
                                sx={{ marginBottom: 1 }}
                              >
                                <ExpandedRowItem
                                  label="Request"
                                  value={
                                    expandedRows[row.request_uuid].request_body
                                  }
                                  content_type={
                                    expandedRows[row.request_uuid]
                                      .request_content_type
                                  }
                                />
                                <ExpandedRowItem
                                  label="Response"
                                  value={
                                    expandedRows[row.request_uuid].response_body
                                  }
                                  content_type={
                                    expandedRows[row.request_uuid]
                                      .response_content_type
                                  }
                                />
                              </Stack>
                            </Grid>
                          </Grid>
                        )}
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>,
              ];
            })}
          </TableBody>
        </Table>
        {loading && (
          <LinearProgress sx={{ margin: "10px auto", width: "80vw" }} />
        )}
        <Pagination
          count={Math.ceil((total || 0) / 20)}
          variant="outlined"
          shape="rounded"
          page={filters.page}
          onChange={(event, value) => {
            setFilters({ ...filters, page: value });
          }}
          sx={{ marginTop: 2, float: "right" }}
        />
      </TableContainer>
    </Grid>
  );
}
