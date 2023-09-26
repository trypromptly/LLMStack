import { useState } from "react";
import { useRecoilValue } from "recoil";
import { dataSourcesState, orgDataSourcesState } from "../../data/atoms";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import { AddDataSourceModal } from "./AddDataSourceModal";
import { Chip } from "@mui/material";
import FormControl from "@mui/material/FormControl";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Input from "@mui/material/Input";

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
      <Select
        sx={{ border: "1px solid #ddd", borderRadius: 1 }}
        labelId="multiple-chip-label"
        id="multiple-chip"
        multiple
        value={props.value ? props.value : []}
        onChange={(event) => props.onChange(event.target.value)}
        input={<Input id="select-multiple-chip" />}
        renderValue={(selected) => (
          <div>
            {selected.map((value) => (
              <Chip
                key={value}
                label={uniqueDataSources.find((ds) => ds.uuid === value).name}
                style={{ margin: 2, borderRadius: 5 }}
              />
            ))}
          </div>
        )}
      >
        {uniqueDataSources.map((dataSource) => (
          <MenuItem key={dataSource.uuid} value={dataSource.uuid}>
            {dataSource.name}
          </MenuItem>
        ))}
      </Select>
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
