import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";

export default function DeleteConfirmationModal(props) {
  const { id, open, onOk, onCancel, title, text } = props;
  return (
    <Dialog
      title={title ? title : "Logged Out"}
      open={open}
      onCancel={onCancel}
    >
      <DialogTitle id="delete-modal-title">Confirm Delete</DialogTitle>
      <DialogContent>
        <DialogContentText>{text}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button key="cancel" onClick={() => onCancel(id)}>
          Cancel
        </Button>
        ,
        <Button
          key="submit"
          variant="contained"
          type="primary"
          onClick={() => onOk(id)}
        >
          Confirm
        </Button>
        ,
      </DialogActions>
    </Dialog>
  );
}
