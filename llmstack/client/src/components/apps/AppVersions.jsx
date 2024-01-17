import {
  Box,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import yaml from "js-yaml";
import moment from "moment";
import { useEffect, useState } from "react";
import AceEditor from "react-ace";
import { axios } from "../../data/axios";

import "ace-builds/src-noconflict/mode-yaml";
import "ace-builds/src-noconflict/theme-dracula";

function AppDataModal({ open, setOpen, data }) {
  const style = {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    width: 600,
    bgcolor: "background.paper",
    boxShadow: 24,
    p: 4,
  };

  return (
    <Modal
      open={open}
      onClose={() => setOpen(false)}
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
    >
      <Box sx={style}>
        <AceEditor
          mode="yaml"
          theme="dracula"
          value={data}
          editorProps={{ $blockScrolling: true }}
          setOptions={{
            useWorker: false,
            showGutter: false,
          }}
          style={{
            borderRadius: "5px",
            width: "100%",
          }}
          onLoad={(editor) => {
            editor.renderer.setScrollMargin(10, 0, 10, 0);
            editor.renderer.setPadding(10);
          }}
        />
      </Box>
    </Modal>
  );
}

export function AppVersions(props) {
  const { app } = props;
  const [versions, setVersions] = useState([]);
  const [open, setOpen] = useState(false);
  const [data, setData] = useState("");

  useEffect(() => {
    if (!app) {
      return;
    }

    axios()
      .get(`/api/apps/${app.uuid}/versions`)
      .then((res) => {
        setVersions(res.data);
      });
  }, [app]);

  return (
    <Box>
      <AppDataModal open={open} setOpen={setOpen} data={data} />
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell style={{ fontWeight: "600" }}>Version</TableCell>
              <TableCell style={{ fontWeight: "600" }}>Comment</TableCell>
              <TableCell style={{ fontWeight: "600" }}>Status</TableCell>
              <TableCell style={{ fontWeight: "600" }}>Last Updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {versions.map((v, index) => (
              <TableRow key={index}>
                <TableCell
                  onClick={() => {
                    setOpen(true);
                    axios()
                      .get(
                        `/api/apps/${app.uuid}/versions/${v.version}?draft=${
                          v.is_draft ? "True" : "False"
                        }`,
                      )
                      .then((res) => {
                        setData(yaml.dump(res.data.data));
                      });
                  }}
                  style={{ textDecoration: "underline", cursor: "pointer" }}
                >
                  v{v.version}
                </TableCell>
                <TableCell>{v.comment}</TableCell>
                <TableCell>{v.is_draft ? "Draft" : "Published"}</TableCell>
                <TableCell>
                  {moment.utc(v.last_updated_at).local().fromNow()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
