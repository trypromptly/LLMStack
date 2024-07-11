import React, { useState } from "react";
import {
  Alert,
  AlertTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { DeleteForever, EditOutlined } from "@mui/icons-material";
import { ProviderIcon } from "../apps/ProviderIcon";
import { ProviderConfigModal } from "./ProviderConfigModal";

function ProviderConfigItem({ providerConfigKey, onEdit, onDelete }) {
  const providerSlug = providerConfigKey.split("/")[0];

  return (
    <TableRow>
      <TableCell sx={{ width: "30px" }}>
        <ProviderIcon
          providerSlug={providerSlug}
          style={{ width: "30px", height: "30px" }}
        />
      </TableCell>
      <TableCell>
        <Typography variant="subtitle">{providerConfigKey}</Typography>
      </TableCell>
      <TableCell sx={{ width: "20px" }}>
        <IconButton size="small" onClick={onEdit}>
          <EditOutlined />
        </IconButton>
      </TableCell>
      <TableCell sx={{ width: "20px" }}>
        <IconButton size="small" onClick={onDelete}>
          <DeleteForever
            sx={(theme) => ({
              color: theme.palette.error.main,
            })}
          />
        </IconButton>
      </TableCell>
    </TableRow>
  );
}

export function ProviderConfigList({ providerConfigs }) {
  const [deleteConfig, setDeleteConfig] = useState(false);
  const [selectedProviderConfigKey, setSelectedProviderConfigKey] =
    useState(null);
  const [showProviderConfigModal, setShowProviderConfigModal] = useState(false);

  const onEdit = (key) => {
    setSelectedProviderConfigKey(key);
    setShowProviderConfigModal(true);
    setDeleteConfig(false);
  };

  const onDelete = (key) => {
    setSelectedProviderConfigKey(key);
    setDeleteConfig(true);
    setShowProviderConfigModal(true);
  };

  return (
    <Paper>
      {!providerConfigs ||
        (!Object.keys(providerConfigs).length && (
          <Alert severity="info" sx={{ textAlign: "left" }}>
            <AlertTitle>No provider configurations found</AlertTitle>
            Add a provider configuration using the <strong>
              Add Provider
            </strong>{" "}
            button
          </Alert>
        ))}
      {providerConfigs && Object.keys(providerConfigs).length > 0 && (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell></TableCell>
                <TableCell></TableCell>
                <TableCell>
                  <strong>Edit</strong>
                </TableCell>
                <TableCell>
                  <strong>Delete</strong>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.keys(providerConfigs).map((providerConfigKey, index) => (
                <ProviderConfigItem
                  key={index}
                  providerConfigKey={providerConfigKey}
                  onEdit={() => onEdit(providerConfigKey)}
                  onDelete={() => onDelete(providerConfigKey)}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      <ProviderConfigModal
        open={showProviderConfigModal}
        handleCancelCb={() => setShowProviderConfigModal(false)}
        configUpdatedCb={() => window.location.reload()}
        modalTitle={
          deleteConfig
            ? "Delete Provider Configuration"
            : "Update Provider Configuration"
        }
        providerConfigKey={selectedProviderConfigKey}
        toDelete={deleteConfig}
      />
    </Paper>
  );
}
