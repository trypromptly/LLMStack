import {
  Box,
  Collapse,
  Divider,
  Grid,
  Pagination,
  Stack,
  SvgIcon,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import moment from "moment";
import { useEffect, useState } from "react";
import UAParser from "ua-parser-js";
import { ReactComponent as DiscordIcon } from "../../assets/images/icons/discord.svg";
import { ReactComponent as SlackIcon } from "../../assets/images/icons/slack.svg";
import { axios } from "../../data/axios";

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

const renderTableCell = (column, row) => {
  const value = row[column.id];

  if (column.id === "request_user_email") {
    if (row.platform_data?.slack?.user_email) {
      return (
        <Box>
          <SvgIcon
            component={SlackIcon}
            fontSize="8"
            sx={{ marginRight: "5px", color: "#555", verticalAlign: "middle" }}
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
            sx={{ marginRight: "5px", color: "#555", verticalAlign: "middle" }}
          />
          {row.platform_data?.discord?.global_name}
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
  } else if (column.id === "latest_created_at") {
    return (
      <Tooltip title={moment.utc(value).local().format("D-MMM-YYYY h:mm:ss A")}>
        <span>{column.format ? column.format(value) : value}</span>
      </Tooltip>
    );
  }

  return column.format ? column.format(value) : value;
};

const parseInput = (input, userAgent) => {
  try {
    const data = JSON.parse(
      input
        .replace(/'/g, '"')
        .replace(/None/g, "null")
        .replace(/True/g, "true")
        .replace(/False/g, "false"),
    );

    if (userAgent.startsWith("Slackbot")) {
      return data?.text?.replace(/<@.*>/g, "");
    } else if (userAgent.startsWith("Discord")) {
      return data.options.reduce((acc, option) => {
        return {
          ...acc,
          [option.name]: option.value,
        };
      }, {});
    }

    return data.input;
  } catch (error) {
    return {};
  }
};

const LabelAndValue = ({ label, value, style = {} }) => {
  return (
    <Box style={style}>
      <Typography variant="caption" style={{ fontWeight: 600, color: "gray" }}>
        {label}
      </Typography>
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
    </Box>
  );
};

const ExpandedRowItem = ({ items }) => {
  if (!items) return null;

  return (
    <Grid
      container
      spacing={1}
      sx={{
        marginBottom: 1,
        border: "1px solid #eee",
      }}
    >
      <Grid item xs={12} md={6} sx={{ borderRight: "solid 1px #eee" }}>
        <Stack direction="column" spacing={1} sx={{ marginBottom: 1 }}>
          <LabelAndValue
            label="Location"
            value={items[0].request_location || "Unknown"}
          />
          <LabelAndValue
            label="IP Address"
            value={items[0].request_ip || "Unknown"}
          />
          <LabelAndValue
            label="Platform"
            value={browserAndOSFromUA(items[0].request_user_agent)}
          />
          <LabelAndValue
            label="User Agent"
            value={items[0].request_user_agent}
          />
        </Stack>
      </Grid>
      <Grid item xs={12} md={6} sx={{ maxHeight: "500px", overflow: "scroll" }}>
        {[...items].reverse().map((item, index) => (
          <Stack
            key={index}
            direction="column"
            spacing={1}
            sx={{ marginBottom: 1 }}
          >
            <LabelAndValue
              label="Request"
              value={
                typeof parseInput(
                  item.request_body,
                  item.request_user_agent,
                ) === "object"
                  ? Object.keys(
                      parseInput(item.request_body, item.request_user_agent),
                    ).map((key) => (
                      <span key={key}>
                        <b>{key}</b>:{" "}
                        {JSON.stringify(
                          parseInput(
                            item.request_body,
                            item.request_user_agent,
                          )[key],
                        )}
                      </span>
                    ))
                  : parseInput(item.request_body, item.request_user_agent)
              }
            />
            <LabelAndValue
              label="Response"
              value={item.response_body}
              style={{
                textAlign: "right",
                paddingRight: 5,
              }}
            />
            <Typography
              variant="caption"
              style={{
                fontWeight: 400,
                textAlign: "right",
                fontSize: 10,
                color: "gray",
                paddingRight: 5,
              }}
            >
              {moment
                .utc(item.created_at)
                .local()
                .format("D-MMM-YYYY h:mm:ss A")}
            </Typography>
            <Divider />
          </Stack>
        ))}
      </Grid>
    </Grid>
  );
};

export function AppRunHistorySessions(props) {
  const { app } = props;
  const [total, setTotal] = useState(null);
  const [rows, setRows] = useState([]);
  const [expandedRows, setExpandedRows] = useState({});
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    page: 1,
    app_uuid: app?.uuid,
  });
  const columns = [
    {
      id: "latest_created_at",
      label: "Last Active",
      format: (value) => moment.utc(value).local().fromNow(),
    },
    {
      id: "request_user_email",
      label: "User",
    },
    {
      id: "session_key",
      label: "Session",
    },
  ];

  const handleRowClick = (row) => {
    setRows(
      rows.map((r) => {
        if (r.session_key === row.session_key) {
          return {
            ...r,
            expand: !r.expand,
          };
        }

        return r;
      }),
    );

    if (!expandedRows[row.session_key]) {
      axios()
        .get(`/api/history?session_key=${row.session_key}&detail=true`)
        .then((response) => {
          setExpandedRows({
            ...expandedRows,
            [row.session_key]: response.data,
          });
        });
    }
  };

  useEffect(() => {
    setLoading(true);
    axios()
      .get(
        `/api/history/sessions?${Object.keys(filters)
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
      {loading && <Box>Loading</Box>}
      <TableContainer sx={{ padding: "10px 20px" }}>
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
                  key={row.session_key}
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
                <TableRow key={`${row.session_key}_details`}>
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
                        {!expandedRows[row.session_key] && "Loading...  "}
                        {expandedRows[row.session_key] && (
                          <ExpandedRowItem
                            items={expandedRows[row.session_key].results}
                          />
                        )}
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>,
              ];
            })}
          </TableBody>
        </Table>
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
