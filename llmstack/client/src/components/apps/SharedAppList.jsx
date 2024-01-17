import DoneIcon from "@mui/icons-material/Done";
import {
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { axios } from "../../data/axios";

export function SharedAppList() {
  const [page, setPage] = useState(0);
  const [apps, setApps] = useState([]);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const navigate = useNavigate();

  useEffect(() => {
    axios()
      .get(
        "/api/apps/shared?fields=uuid,name,visibility,is_published,app_type_name,owner_email,published_uuid,access_permission,unique_processors",
      )
      .then((response) => {
        setApps(response.data);
      });
  }, [setApps]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Paper sx={{ width: "100%", pt: 2 }}>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow
              sx={{ "& > th": { fontWeight: 600, padding: "3px 16px" } }}
            >
              <TableCell>App Name</TableCell>
              <TableCell sx={{ textAlign: "center" }}>App Type</TableCell>
              <TableCell sx={{ textAlign: "center" }}>Owner</TableCell>
              <TableCell>Processors</TableCell>
              <TableCell sx={{ textAlign: "center" }}>Can Edit?</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {apps
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row) => (
                <TableRow
                  key={row.uuid}
                  hover
                  onClick={() =>
                    navigate(
                      row?.access_permission > 0
                        ? `/apps/${row.uuid}`
                        : `/app/${row.published_uuid}`,
                    )
                  }
                  sx={{
                    cursor: "pointer",
                  }}
                >
                  <TableCell>{row.name}</TableCell>
                  <TableCell sx={{ textAlign: "center" }}>
                    {row.app_type_name}
                  </TableCell>
                  <TableCell sx={{ textAlign: "center" }}>
                    {row.owner_email}
                  </TableCell>
                  <TableCell style={{ maxWidth: "100px" }}>
                    {row.unique_processors?.map((x) => (
                      <Chip key={x} label={x} size="small" />
                    ))}
                  </TableCell>
                  <TableCell sx={{ textAlign: "center" }}>
                    {row?.access_permission > 0 && <DoneIcon color="success" />}
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25, 50]}
        component="div"
        count={apps.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
}
