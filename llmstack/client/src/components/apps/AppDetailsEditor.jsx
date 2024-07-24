import { EditOutlined } from "@mui/icons-material";
import { Avatar, Stack, Link, Tooltip, Typography } from "@mui/material";
import { useState } from "react";
import AppVisibilityIcon from "./AppVisibilityIcon";
import { useRecoilValue } from "recoil";
import { profileSelector } from "../../data/atoms";
import { AppFromTemplateDialog } from "./AppFromTemplateDialog";
import { EditSharingModal } from "./AppPublisher";

export function AppDetailsEditor({ app, setApp, saveApp }) {
  const [showEditor, setShowEditor] = useState(false);
  const [showSharingModal, setShowSharingModal] = useState(false);
  const profile = useRecoilValue(profileSelector);
  const iconSize = `${
    20 + ((app.description ? 1 : 0) + (app.is_published ? 1 : 0)) * 20
  }px`;

  return (
    <Stack direction="row" gap={2} sx={{ margin: "auto !important" }}>
      {app.icon && (
        <Avatar
          variant="rounded"
          onClick={() => setShowEditor(true)}
          sx={{ cursor: "pointer", width: iconSize, height: iconSize }}
          width={iconSize}
          height={iconSize}
        >
          <img
            src={app.icon}
            alt={app.name}
            style={{ width: iconSize, height: iconSize }}
          />
        </Avatar>
      )}
      <Stack direction="column">
        <Stack direction="row" spacing={1.2}>
          <Typography
            variant="h5"
            onClick={() => setShowEditor(true)}
            style={{ cursor: "pointer" }}
          >
            {app.name}
          </Typography>
          {app.owner_email !== profile.user_email && (
            <span style={{ color: "gray", lineHeight: "40px" }}>
              shared by <b>{app.owner_email}</b>
            </span>
          )}
          {app.owner_email === profile.user_email &&
            app.visibility === 0 &&
            app.last_modified_by_email && (
              <span style={{ color: "gray", lineHeight: "40px" }}>
                Last modified by{" "}
                <b>
                  {app.last_modified_by_email === profile.user_email
                    ? "You"
                    : app.last_modified_by_email}
                </b>
              </span>
            )}
          <EditOutlined
            style={{
              fontSize: "12px",
              marginLeft: "4px",
              color: "#666",
              height: "100%",
              cursor: "pointer",
            }}
            onClick={() => setShowEditor(true)}
          />
        </Stack>
        {app.description && (
          <Tooltip title={app.description}>
            <Typography variant="subtitle2" onClick={() => setShowEditor(true)}>
              {app.description.length > 200
                ? `${app.description.substring(0, 200)}...`
                : app.description}
            </Typography>
          </Tooltip>
        )}
        {app.is_published && (
          <Stack direction="row" spacing={0.2} sx={{ justifyContent: "left" }}>
            <Link
              href={`${window.location.origin}/app/${app.published_uuid}`}
              target="_blank"
              rel="noreferrer"
              variant="body2"
            >
              {`${window.location.origin}/app/${app.published_uuid}`}
            </Link>
            <AppVisibilityIcon
              visibility={app.visibility}
              published={app.is_published}
              setShowSharingModal={setShowSharingModal}
              disabled={app.owner_email !== profile.user_email}
            />
          </Stack>
        )}
      </Stack>
      <AppFromTemplateDialog
        open={showEditor}
        setOpen={setShowEditor}
        app={app}
        setApp={setApp}
      />
      <EditSharingModal
        show={showSharingModal}
        setShow={setShowSharingModal}
        app={app}
        setIsPublished={() =>
          setApp({ ...app, is_published: !app.is_published })
        }
        setAppVisibility={(visibility) => setApp({ ...app, visibility })}
      />
    </Stack>
  );
}
