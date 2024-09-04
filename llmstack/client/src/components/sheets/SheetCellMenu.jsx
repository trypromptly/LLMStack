import {
  Popper,
  Paper,
  MenuItem,
  Grow,
  ClickAwayListener,
  Stack,
} from "@mui/material";

function SheetCellMenu({
  anchorEl,
  open,
  onClose,
  onCopy,
  onPaste,
  onDelete,
  readOnly,
  isFormula,
  onOpenFormula,
}) {
  const handleClose = (event) => {
    if (anchorEl.current && anchorEl.current.contains(event.target)) {
      return;
    }
    onClose();
  };

  return (
    <Popper
      open={open}
      anchorEl={anchorEl}
      placement="bottom-end"
      transition
      style={{ zIndex: 1300 }}
    >
      {({ TransitionProps }) => (
        <Grow {...TransitionProps}>
          <Paper>
            <ClickAwayListener onClickAway={handleClose}>
              <Stack gap={2} sx={{ padding: 2 }}>
                <MenuItem onClick={onCopy}>Copy</MenuItem>
                <MenuItem onClick={onPaste}>Paste</MenuItem>
                <MenuItem onClick={onDelete}>Delete</MenuItem>
                {!readOnly && (
                  <MenuItem onClick={onOpenFormula}>
                    {isFormula ? "Edit Formula" : "Add Formula"}
                  </MenuItem>
                )}
              </Stack>
            </ClickAwayListener>
          </Paper>
        </Grow>
      )}
    </Popper>
  );
}

export default SheetCellMenu;
