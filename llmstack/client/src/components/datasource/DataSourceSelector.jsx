import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import { Autocomplete, Button, TextField } from "@mui/material";
import FormControl from "@mui/material/FormControl";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import { dataSourcesState, orgDataSourcesState } from "../../data/atoms";
import { AddDataSourceModal } from "./AddDataSourceModal";
import WithLogin from "../WithLogin";

export function DataSourceSelector(props) {
  const dataSources = useRecoilValue(dataSourcesState);
  const orgDataSources = useRecoilValue(orgDataSourcesState);
  const [showAddDataSourceModal, setShowAddDataSourceModal] = useState(false);
  const uniqueDataSources = dataSources.concat(
    orgDataSources.filter(
      (orgDataSource) =>
        !dataSources.some(
          (dataSource) => dataSource.uuid === orgDataSource.uuid,
        ),
    ),
  );

  return (
    <FormControl fullWidth sx={{ display: "flex", flexFlow: "nowrap" }}>
      <Autocomplete
        multiple={props.multiple === undefined ? true : props.multiple}
        id="datasource-selector"
        sx={{ width: "100%" }}
        options={[...uniqueDataSources]}
        getOptionLabel={(option) => {
          const dataSource = uniqueDataSources.find(
            (uniqueDataSource) => uniqueDataSource.uuid === option,
          );

          return dataSource
            ? dataSource.name
            : option.name
              ? option.name
              : option;
        }}
        isOptionEqualToValue={(option, value) => {
          return option.uuid === value.uuid || option.uuid === value;
        }}
        value={
          props.value
            ? typeof props.value === "string" && props.multiple
              ? [props.value]
              : props.value
            : []
        }
        renderInput={(params) => (
          <TextField
            {...params}
            variant="outlined"
            label="Data Sources"
            placeholder="Data Sources"
          />
        )}
        onChange={(event, value) => {
          if (!Array.isArray(value)) {
            if (props.multiple) {
              props.onChange([value?.uuid || value]);
            } else {
              props.onChange(value?.uuid || value);
            }
          } else {
            props.onChange(
              value.map((dataSource) => dataSource?.uuid || dataSource),
            );
          }
        }}
      />
      <Button
        onClick={() => setShowAddDataSourceModal(true)}
        variant="contained"
        sx={{
          marginLeft: "5px",
          height: "40px",
          margin: "auto",
        }}
      >
        <AddCircleOutlineIcon />
      </Button>
      <WithLogin loginMessage="Please login to add and select a datasource.">
        <AddDataSourceModal
          open={showAddDataSourceModal}
          handleCancelCb={() => setShowAddDataSourceModal(false)}
          dataSourceAddedCb={(dataSource) => props.onChange([dataSource.uuid])}
        />
      </WithLogin>
    </FormControl>
  );
}
