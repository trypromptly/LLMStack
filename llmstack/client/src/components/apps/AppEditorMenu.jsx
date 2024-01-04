import React from "react";
import {
  FormControl,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  MenuItem,
  Select,
} from "@mui/material";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../../data/atoms";

export default function AppEditorMenu(props) {
  const { menuItems, selectedMenuItem, setSelectedMenuItem, tourRef } = props;
  const isMobile = useRecoilValue(isMobileState);

  return isMobile ? (
    <FormControl sx={{ m: 1, width: "100%", margin: 0 }} variant="filled">
      <Select
        defaultValue=""
        id="grouped-select"
        label="App Menu"
        value={selectedMenuItem}
        ref={tourRef}
      >
        {menuItems.map((item) => {
          return item.children && item.children.length > 0 ? (
            [
              <ListSubheader key={item.name}>{item.name}</ListSubheader>,
              ...item.children.map((child) => (
                <MenuItem value={child.value} key={child.name}>
                  <ListItemButton
                    onClick={(e) => setSelectedMenuItem(child.value)}
                  >
                    <ListItemIcon>{child.icon}</ListItemIcon>
                    <ListItemText primary={child.name} />
                  </ListItemButton>
                </MenuItem>
              )),
            ]
          ) : (
            <MenuItem value={item.value} key={item.value}>
              <ListItemButton onClick={(e) => setSelectedMenuItem(item.value)}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.name} />
              </ListItemButton>
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  ) : (
    <List
      sx={{
        width: "100%",
        maxWidth: 360,
        bgcolor: "background.paper",
        "& > .Mui-selected": {
          borderBottom: "1px solid #046fda66",
        },
      }}
      component="nav"
      ref={tourRef}
    >
      {menuItems.map((item) => {
        return item.children && item.children.length > 0 ? (
          [
            <ListItemButton
              key={item.name}
              disableRipple
              disableTouchRipple
              sx={{
                "&.MuiButtonBase-root:hover": {
                  backgroundColor: "transparent",
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.name} />
            </ListItemButton>,
            <List
              component="div"
              key={`${item.name}-children`}
              sx={{
                "& > .Mui-selected": {
                  borderBottom: "1px solid #046fda66",
                },
              }}
            >
              {item.children.map((child) => (
                <ListItemButton
                  key={child.name}
                  sx={{ pl: 10 }}
                  selected={selectedMenuItem === child.value}
                  onClick={(e) => setSelectedMenuItem(child.value)}
                >
                  <ListItemIcon>{child.icon}</ListItemIcon>
                  <ListItemText primary={child.name} />
                </ListItemButton>
              ))}
            </List>,
          ]
        ) : (
          <ListItemButton
            key={item.name}
            selected={selectedMenuItem === item.value}
            onClick={(e) => setSelectedMenuItem(item.value)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.name} />
          </ListItemButton>
        );
      })}
    </List>
  );
}
