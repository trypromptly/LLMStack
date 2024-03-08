import { useEffect, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { LoadingButton } from "@mui/lab";
import kebabCase from "lodash/kebabCase";
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

const appStoreListingUiSchema = (readOnlySlug) => {
  return {
    icon: { "ui:widget": "file" },
    slug: { "ui:readonly": true },
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
};

export default function StoreListingModal({ app, open, handleCloseCb }) {
  const [formData, setFormData] = useState({});
  const [saving, setSaving] = useState(false);
  const categories = useRecoilValue(storeCategoriesSlugState);

  useEffect(() => {
    if (app?.store_uuid) {
      axios()
        .get(`/api/store/apps/${app?.store_uuid}`)
        .then((response) => {
          if (response.status === 200) {
            setFormData({
              slug: response.data.slug,
              name: response.data.name,
              description: response.data.description,
              icon: response.data.icon,
              version: response.data.version,
              categories: response.data.categories,
              changelog: response.data.changelog,
            });
          }

          return response;
        })
        .catch((error) => {
          enqueueSnackbar(
            `Error Occurred: ${error?.response?.data?.message || error}`,
            {
              variant: "error",
            },
          );
        });
    } else {
      setFormData({
        slug: kebabCase(app?.name),
        name: app?.name,
        description: app?.description,
      });
    }
  }, [app?.store_uuid, app?.name, app?.description]);

  const handleSave = (storeUuid) => {
    setSaving(true);

    let savePromise = null;

    if (storeUuid) {
      savePromise = axios().patch(`/api/store/apps/${storeUuid}`, {
        published_app_version: formData.version,
        categories: formData.categories,
        name: formData.name,
        description: formData.description,
        icon: formData.icon,
        changelog: formData.changelog,
      });
    } else {
      axios().post("/api/store/apps", {
        published_app_uuid: app?.published_uuid,
        published_app_version: formData.version,
        categories: formData.categories,
        slug: formData.slug,
        name: formData.name,
        description: formData.description,
        icon: formData.icon,
        changelog: formData.changelog,
      });
    }

    savePromise
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
          uiSchema={appStoreListingUiSchema(app?.store_uuid ? true : false)}
          liveValidate
          validator={validator}
          disableAdvanced={true}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCloseCb} sx={{ textTransform: "none" }}>
          Close
        </Button>
        {app?.store_uuid && (
          <Button
            variant="outlined"
            sx={{ textTransform: "none" }}
            startIcon={<OpenInNewIcon />}
            onClick={() => {
              window.open(`/a/${formData?.slug}`, "_blank");
            }}
          >
            View Listing
          </Button>
        )}
        <LoadingButton
          onClick={() => handleSave(app?.store_uuid)}
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
