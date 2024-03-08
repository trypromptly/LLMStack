import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";
import { useRecoilValue } from "recoil";
import { storeCategoriesSlugState } from "../../data/atoms";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { axios } from "../../data/axios";
import { enqueueSnackbar } from "notistack";

const appStoreListingSchema = (appUuid, categories) => {
  return {
    type: "object",
    properties: {
      slug: { type: "string", title: "Slug" },
      name: { type: "string", title: "Name" },
      version: { type: "number", title: "App Version", appUuid },
      description: { type: "string", title: "Description" },
      icon: { type: "string", title: "Icon" },
      categories: {
        type: "array",
        title: "Categories",
        items: { type: "string", enum: categories },
        uniqueItems: true,
      },
      changelog: { type: "string", title: "Change Log" },
    },
  };
};

const appStoreListingUiSchema = {
  icon: { "ui:widget": "file" },
  description: {
    "ui:widget": "textarea",
  },
  changelog: {
    "ui:widget": "textarea",
  },
  version: {
    "ui:widget": "app_version",
  },
  categories: {
    "ui:options": {
      orderable: false,
    },
  },
};

export default function StoreListingModal({ app, open, handleCloseCb }) {
  const [formData, setFormData] = useState({});
  const [saving, setSaving] = useState(false);
  const categories = useRecoilValue(storeCategoriesSlugState);

  const handleSave = () => {
    setSaving(true);
    axios()
      .post("/api/store/apps", {
        published_app_uuid: app?.published_uuid,
        published_app_version: formData.version,
        categories: formData.categories,
        slug: formData.slug,
        name: formData.name,
        description: formData.description,
        icon: formData.icon,
      })
      .then((response) => {
        if (response.status === 200) {
          enqueueSnackbar("App Store Listing Saved", { variant: "success" });
        }
      })
      .catch((error) => {
        enqueueSnackbar(
          `Error Occurred: ${error?.response?.data?.message || error}`,
          {
            variant: "error",
          },
        );
      })
      .finally(() => {
        setSaving(false);
        handleCloseCb();
      });
  };

  return (
    <Dialog open={open} onClose={handleCloseCb} fullWidth>
      <DialogTitle>
        {app?.store_uuid ? "Edit Store Listing" : "List on Promptly App Store"}
      </DialogTitle>
      <DialogContent>
        <ThemedJsonForm
          schema={appStoreListingSchema(app?.uuid, categories)}
          formData={formData}
          onChange={(e) => {
            setFormData(e.formData);
          }}
          uiSchema={appStoreListingUiSchema}
          liveValidate
          validator={validator}
          disableAdvanced={true}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCloseCb} sx={{ textTransform: "none" }}>
          Close
        </Button>
        <LoadingButton
          onClick={handleSave}
          sx={{ textTransform: "none" }}
          variant="contained"
          loading={saving}
        >
          Save
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
}
