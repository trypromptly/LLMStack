import CorporateFareIcon from "@mui/icons-material/CorporateFare";
import PeopleIcon from "@mui/icons-material/People";
import PublicIcon from "@mui/icons-material/Public";
import PublicOffIcon from "@mui/icons-material/PublicOff";
import { IconButton, Tooltip } from "@mui/material";

export default function AppVisibilityIcon({
  visibility,
  published,
  setShowSharingModal = () => {},
  disabled = false,
}) {
  const color = published && !disabled ? "success" : "gray";

  let tooltipMessage = "";
  if (visibility === 3) {
    tooltipMessage = "Publicly accessible";
  } else if (visibility === 2) {
    tooltipMessage = "Anyone with the link can access";
  } else if (visibility === 1) {
    tooltipMessage = "Accessible by anyone in your organization";
  } else if (visibility === 0) {
    tooltipMessage = "Only selected users and you can access";
  }

  if (!published) {
    tooltipMessage = "Not published";
  }

  return (
    <Tooltip title={tooltipMessage}>
      <IconButton
        onClick={() => setShowSharingModal(true)}
        sx={{ padding: "0px" }}
        disabled={disabled}
      >
        {visibility === 3 && <PublicIcon color={color} fontSize="small" />}
        {visibility === 2 && <PublicOffIcon color={color} fontSize="small" />}
        {visibility === 1 && (
          <CorporateFareIcon color={color} fontSize="small" />
        )}
        {visibility === 0 && <PeopleIcon color={color} fontSize="small" />}
      </IconButton>
    </Tooltip>
  );
}
