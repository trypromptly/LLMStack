import { useState } from "react";
import { useRecoilValue } from "recoil";
import { dataSourcesState, orgDataSourcesState } from "../../data/atoms";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import { AddDataSourceModal } from "./AddDataSourceModal";
import { Autocomplete, TextField } from "@mui/material";
import FormControl from "@mui/material/FormControl";

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
    <FormControl fullWidth>
      <Autocomplete
        multiple
        id="datasource-selector"
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
            ? typeof props.value === "string"
              ? [props.value]
              : props.value
            : []
        }
        renderInput={(params) => (
          <TextField
            {...params}
            variant="standard"
            label="Data Sources"
            placeholder="Data Sources"
          />
        )}
        onChange={(event, value) => {
          props.onChange(
            value.map((dataSource) => dataSource?.uuid || dataSource),
          );
        }}
      />
      <button
        onClick={() => setShowAddDataSourceModal(true)}
        style={{ backgroundColor: "#6287ac", color: "#fed766" }}
      >
        <AddCircleOutlineIcon />
      </button>
      <AddDataSourceModal
        open={showAddDataSourceModal}
        handleCancelCb={() => setShowAddDataSourceModal(false)}
        dataSourceAddedCb={(dataSource) => props.onChange(dataSource.uuid)}
      />
    </FormControl>
  );
}
