import React from "react";
import { Stack } from "@mui/material";

function SheetListItem(props) {
  const { sheet, selected, selectSheet } = props;

  return (
    <Stack
      key={sheet.id}
      onClick={() => selectSheet(sheet.id)}
      className={selected ? "selected" : ""}
    >
      <div>{sheet.name}</div>
    </Stack>
  );
}

function SheetsList(props) {
  const { sheets, selectedSheet, selectSheet } = props;

  return (
    <Stack>
      {Object.values(sheets).map((sheet) => (
        <SheetListItem
          key={sheet.id}
          sheet={sheet}
          selected={selectedSheet === sheet.id}
          selectSheet={selectSheet}
        />
      ))}
    </Stack>
  );
}

export default SheetsList;
