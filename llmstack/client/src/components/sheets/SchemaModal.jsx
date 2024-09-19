import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-yaml";
import "ace-builds/src-noconflict/theme-dracula";
import CopyAllIcon from "@mui/icons-material/CopyAll";

const SchemaModal = ({ open, onClose, schema }) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Sheet Schema</DialogTitle>
      <DialogContent>
        <AceEditor
          mode="yaml"
          theme="dracula"
          value={schema}
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
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button
          onClick={() => navigator.clipboard.writeText(schema)}
          variant="contained"
          startIcon={<CopyAllIcon />}
        >
          Copy
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SchemaModal;
