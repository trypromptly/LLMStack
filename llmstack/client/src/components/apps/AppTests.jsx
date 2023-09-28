import { Button, IconButton, Box, Chip, Grid } from "@mui/material";
import { TextareaAutosize } from "@mui/base";
import { axios } from "../../data/axios";
import {
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import { useEffect, useState } from "react";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import PlayCircleFilledWhiteOutlinedIcon from "@mui/icons-material/PlayCircleFilledWhiteOutlined";

import { LocaleDate } from "../../components/Utils";
import { AddTestSetModal } from "../testset/AddTestSetModal";
import DeleteConfirmationModal from "../../components/DeleteConfirmationModal";

export function AppTests({ app }) {
  const [deleteModalTitle, setDeleteModalTitle] = useState("");
  const [deleteModalMessage, setDeleteModalMessage] = useState("");
  const [deleteId, setDeleteId] = useState(null);
  const [addTestSetModalOpen, setAddTestSetModalOpen] = useState(false);
  const [deleteConfirmationModalOpen, setDeleteConfirmationModalOpen] =
    useState(false);
  const [tableData, setTableData] = useState({});
  const [modalTitle, setModalTitle] = useState("Create Test Set");
  const [selectTestSet, setSelectTestSet] = useState(null);
  const [testSetStatus, setTestSetStatus] = useState({});
  const [testCaseStatus, setTestCaseStatus] = useState({});
  const [testCaseRunOutput, setTestCaseRunOutput] = useState({});

  useEffect(() => {
    // Get data from API
    let data_map = {};

    axios()
      .get(`/api/apps/${app.uuid}/testsets`)
      .then((response) => {
        let data = response.data;
        data.forEach((entry) => {
          data_map[entry.uuid] = {
            ...entry,
            testcases: entry.testcases.map((testcase) => {
              return { ...testcase };
            }),
            expand: false,
          };
          setTableData(data_map);
        });
      })
      .catch((error) => {});
  }, [setTableData, app?.uuid]);

  async function runTestSet(testset) {
    setTestSetStatus((prev) => {
      return { ...prev, [testset.uuid]: "RUNNING" };
    });

    const runTestCase = async (testcase) => {
      setTestCaseStatus((prev) => {
        return { ...prev, [testcase.uuid]: "RUNNING" };
      });

      const res = await axios().post(`/api/apps/${app.uuid}/run`, {
        input: testcase.input_data,
        stream: false,
      });

      setTestCaseRunOutput((prev) => {
        return { ...prev, [testcase.uuid]: res.data };
      });

      setTestCaseStatus((prev) => {
        return { ...prev, [testcase.uuid]: "COMPLETED" };
      });

      return res;
    };

    const chunkArray = function (arr, chunkSize) {
      var R = [];
      for (var i = 0, len = arr.length; i < len; i += chunkSize)
        R.push(arr.slice(i, i + chunkSize));
      return R;
    };

    var chunkedTestcases = chunkArray(testset.testcases, 2);

    for (let i = 0; i < chunkedTestcases.length; i++) {
      await Promise.all(chunkedTestcases[i].map(runTestCase)).catch(
        console.error,
      );
    }

    setTestSetStatus((prev) => {
      return { ...prev, [testset.uuid]: "COMPLETED" };
    });
  }

  function runTestCase(testcase) {
    setTestSetStatus((prev) => {
      return { ...prev, [testcase.testset_uuid]: "RUNNING" };
    });
    setTestCaseStatus((prev) => {
      return { ...prev, [testcase.uuid]: "RUNNING" };
    });
    axios()
      .post(`/api/apps/${app.uuid}/run`, {
        input: testcase.input_data,
        stream: false,
      })
      .then((res) => {
        setTestCaseRunOutput((prev) => {
          return { ...prev, [testcase.uuid]: res?.data };
        });
      })
      .catch((err) => {})
      .finally(() => {
        setTestSetStatus((prev) => {
          return { ...prev, [testcase.testset_uuid]: "COMPLETED" };
        });
        setTestCaseStatus((prev) => {
          return { ...prev, [testcase.uuid]: "COMPLETED" };
        });
      });
  }

  const TestCases = (data) => {
    const testcases = data.testcases;

    const columns = [
      {
        title: "Input Data",
        key: "input_data",
        render: (record, row) => {
          return (
            <TextareaAutosize
              disabled={true}
              minRows={3}
              value={JSON.stringify(row.input_data, null, 2)}
            />
          );
        },
      },
      {
        title: "Expected Output",
        key: "expected_output",
        scroll: { x: 400 },
        render: (record, row) => {
          return (
            <TextareaAutosize
              disabled={true}
              minRows={3}
              value={row.expected_output}
            />
          );
        },
      },
      {
        title: "Output Data",
        key: "output_data",
        render: (record, row) => {
          const output_result = testCaseRunOutput[row.uuid];

          return (
            <TextareaAutosize
              disabled={true}
              minRows={3}
              value={
                output_result
                  ? JSON.stringify(output_result?.output, null, 2)
                  : ""
              }
            />
          );
        },
      },
      {
        title: "Status",
        key: "status",
        render: (record, row) => {
          const record_status = testCaseStatus[row.uuid];

          if (!record_status) {
            return null;
          }

          if (record_status === "RUNNING") {
            return <Chip label="Running" color="primary" />;
          } else if (record_status === "COMPLETED") {
            return <Chip label="Completed" color="success" />;
          } else {
            return null;
          }
        },
      },
      {
        title: "Action",
        key: "operation",
        render: (record, row) => {
          return (
            <Box>
              <IconButton
                onClick={() => {
                  setDeleteId(row);
                  setDeleteModalTitle("Delete Test Case");
                  setDeleteModalMessage(
                    <div>
                      Are you sure you want to delete{" "}
                      <span style={{ fontWeight: "bold" }}>{row.name}</span> ?
                    </div>,
                  );
                  setDeleteConfirmationModalOpen(true);
                }}
              >
                <DeleteOutlineOutlinedIcon />
              </IconButton>
              <IconButton
                onClick={() => {
                  setTestSetStatus({});
                  setTestCaseStatus({});
                  setTestCaseRunOutput({});
                  runTestCase(row);
                }}
              >
                <PlayCircleFilledWhiteOutlinedIcon />
              </IconButton>
            </Box>
          );
        },
      },
    ];

    return (
      <Table>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column.key} align={column.align}>
                {column.title}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {testcases.map((row) => {
            return (
              <TableRow
                key={row.uuid}
                hover
                sx={{ cursor: "pointer" }}
                onClick={() => {
                  setSelectTestSet(row);
                  setAddTestSetModalOpen(true);
                }}
              >
                {columns.map((column) => {
                  const value = row[column.key];
                  return (
                    <TableCell key={column.key} align={column.align}>
                      {column.render ? column.render(value, row) : value}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    );
  };

  const columns = [
    {
      title: "Name",
      key: "name",
    },
    {
      title: "Last Modified",
      key: "last_updated_at",
      render: (record) => {
        return <LocaleDate value={record} />;
      },
    },
    {
      title: "Status",
      key: "status",
      render: (record, row) => {
        const record_status = testSetStatus[row.uuid];
        if (record_status === undefined) {
          return null;
        }

        if (record_status === "RUNNING") {
          return <Chip label="Running" color="primary" />;
        } else if (record_status === "COMPLETED") {
          return <Chip label="Completed" color="success" />;
        } else {
          return null;
        }
      },
    },
    {
      title: "Action",
      key: "operation",
      render: (record, row) => {
        return (
          <Box>
            <IconButton
              onClick={() => {
                setModalTitle("Add Test Entry");
                setSelectTestSet(row);
                setAddTestSetModalOpen(true);
              }}
            >
              <AddOutlinedIcon />
            </IconButton>
            <IconButton
              onClick={() => {
                setDeleteId(row);
                setDeleteModalTitle("Delete Test Set");
                setDeleteModalMessage(
                  <div>
                    Are you sure you want to delete{" "}
                    <span style={{ fontWeight: "bold" }}>{row.name}</span> ?
                  </div>,
                );
                setDeleteConfirmationModalOpen(true);
              }}
            >
              <DeleteOutlineOutlinedIcon />
            </IconButton>
            <IconButton
              onClick={() => {
                setTestSetStatus({});
                setTestCaseStatus({});
                setTestCaseRunOutput({});
                runTestSet(row);
              }}
            >
              <PlayCircleFilledWhiteOutlinedIcon />
            </IconButton>
          </Box>
        );
      },
    },
  ];

  return (
    <div id="tests-page">
      <Grid span={24} style={{ padding: "10px" }}>
        <Grid item style={{ width: "100%", padding: "15px 0px" }}>
          <Button
            onClick={() => {
              setAddTestSetModalOpen(true);
            }}
            type="primary"
            variant="contained"
            sx={{ float: "left", marginBottom: "10px", textTransform: "none" }}
          >
            Create Test Set
          </Button>
        </Grid>
        <Grid item style={{ width: "100%" }}>
          <Table>
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell key={column.key} align={column.align}>
                    {column.title}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.values(tableData).map((row) => {
                return [
                  <TableRow
                    key={row.uuid}
                    hover
                    sx={{ cursor: "pointer" }}
                    onClick={() => {
                      setTableData((prev) => {
                        prev[row.uuid].expand = !prev[row.uuid].expand;
                        return prev;
                      });
                      setSelectTestSet(row);
                    }}
                  >
                    {columns.map((column) => {
                      const value = row[column.key];
                      return (
                        <TableCell key={column.key} align={column.align}>
                          {column.render ? column.render(value, row) : value}
                        </TableCell>
                      );
                    })}
                  </TableRow>,
                  <TableRow key={row.uuid + "-testcases"}>
                    <TableCell
                      colSpan={columns.length}
                      sx={{ padding: row.expand ? "0" : "inherit" }}
                    >
                      <Collapse in={row.expand} timeout="auto" unmountOnExit>
                        <TestCases testcases={row.testcases} />
                      </Collapse>
                    </TableCell>
                  </TableRow>,
                ];
              })}
            </TableBody>
          </Table>
        </Grid>
      </Grid>
      {addTestSetModalOpen && (
        <AddTestSetModal
          open={addTestSetModalOpen}
          testSet={selectTestSet}
          modalTitle={modalTitle}
          handleCancelCb={() => {
            setSelectTestSet(null);
            setAddTestSetModalOpen(false);
          }}
          onSubmitCb={(testset) => {
            setTableData((prev) => {
              prev[testset.uuid] = testset;
              return prev;
            });
            setSelectTestSet(null);
            setAddTestSetModalOpen(false);
          }}
          app={app}
        />
      )}
      {deleteConfirmationModalOpen && (
        <DeleteConfirmationModal
          id={deleteId}
          title={deleteModalTitle}
          text={deleteModalMessage}
          open={deleteConfirmationModalOpen}
          onOk={(param) => {
            if (param?.testset_uuid === undefined) {
              axios()
                .delete(`/api/apptestsets/${param.uuid}`)
                .then((res) => {
                  setTableData((prev) => {
                    delete prev[param.uuid];
                    return prev;
                  });
                })
                .finally(() => {
                  setDeleteConfirmationModalOpen(false);
                });
            } else {
              axios()
                .delete(`/api/apptestcases/${param.uuid}`)
                .then((res) => {
                  setTableData((prev) => {
                    let testset = prev[param.testset_uuid];
                    testset.testcases = testset.testcases.filter(
                      (entry) => entry.uuid !== param.uuid,
                    );
                    prev[param.testset_uuid] = testset;
                    return prev;
                  });
                })
                .finally(() => {
                  setDeleteConfirmationModalOpen(false);
                });
            }
          }}
          onCancel={() => {
            setDeleteConfirmationModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
