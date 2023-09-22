import React from "react";

import {
  Dialog,
  Button as MuiButton,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Select as MuiSelect,
  MenuItem,
} from "@mui/material";
import { axios } from "../../data/axios";

export default function ShareDataSourceModal(props) {
  const { id, open, onOk, onCancel, title, dataSource } = props;
  const [visibility, setVisibility] = React.useState(dataSource?.visibility);

  const onOkClick = () => {
    let action = "noop";
    if (visibility !== dataSource.visibility) {
      if (dataSource.visibility === 0 && visibility === 1) {
        // If the visibility is changing from 1 to 0, then we need to make the entry private
        axios()
          .post(`api/org/datasources/${dataSource.uuid}/add_entry`)
          .then((res) => {
            onOk(action, dataSource);
          });
      } else if (dataSource.visibility === 1 && visibility === 0) {
        // If the visibility is changing from 1 to 0, then we need to make the entry org public
        axios()
          .delete(`api/org/datasources/${dataSource.uuid}`)
          .then((res) => {
            onOk(action, dataSource);
          });
      } else {
        onOk(action, dataSource);
      }
    } else {
      onOk(action, dataSource);
    }
  };

  const visibilityOptions = [
    {
      value: 1,
      label: "Organization",
      description: "Members of your organization can access this datasource",
    },
    {
      value: 0,
      label: "You",
      description: "Only you can access this datasource",
    },
  ];
  return (
    <Dialog
      open={open}
      onClose={() => onCancel(id)}
      aria-labelledby="share-datasource-dialog-title"
      aria-describedby="share-datasource-dialog-description"
    >
      <DialogTitle id="share-datasource-dialog-title">{title}</DialogTitle>
      <DialogContent style={{ minWidth: "500px" }}>
        <Stack spacing={2}>
          <h4>Choose who can access this datasource</h4>
          <MuiSelect
            labelId="share-datasource-select-label"
            size="small"
            defaultValue={
              dataSource?.visibility === undefined ? 1 : dataSource?.visibility
            }
            onChange={(e) => {
              setVisibility(e.target.value);
            }}
          >
            {visibilityOptions.map((option) => {
              return (
                <MenuItem key={option.value} value={option.value}>
                  <Stack direction="row" spacing={1}>
                    <span>{option.label}</span>
                    <small>{option.description}</small>
                  </Stack>
                </MenuItem>
              );
            })}
          </MuiSelect>
        </Stack>
      </DialogContent>
      <DialogActions>
        <MuiButton onClick={() => onCancel(id)}>Cancel</MuiButton>
        <MuiButton variant="contained" onClick={() => onOkClick(id)}>
          Done
        </MuiButton>
      </DialogActions>
    </Dialog>
  );
}
