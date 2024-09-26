import {
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { useCallback, useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { providerSchemasSelector } from "../data/atoms";
import ThemedJsonForm from "../components/ThemedJsonForm";
import { axios } from "../data/axios";
import ProviderConfigs from "../components/settings/ProviderConfigs";

const pageHeaderStyle = {
  textAlign: "left",
  width: "100%",
  fontFamily: "Lato, sans-serif",
  marginBottom: "10px",
  padding: "5px 10px",
  fontWeight: 600,
  borderRadius: "5px",
  color: "#1c3c5a",
  fontSize: "18px",
  borderBottom: "solid 3px #1c3c5a",
  borderLeft: "solid 1px #ccc",
  borderRight: "solid 1px #ccc",
};

const sectionHeaderStyle = {
  textAlign: "left",
  width: "100%",
  fontFamily: "Lato, sans-serif",
  marginBottom: "10px",
  padding: "5px 10px",
  fontWeight: 600,
  borderRadius: "5px",
  color: "#1c3c5a",
  fontSize: "16px",
};

const settingsSchema = {
  type: "object",
  properties: {
    name: {
      type: "string",
      description: "Name of the organization",
      readonly: true,
      title: "Name",
    },
    slug: {
      type: "string",
      description: "Unique identifier for the organization",
      readonly: true,
      title: "Slug",
    },
    domains: {
      type: "array",
      items: {
        type: "string",
      },
      description: "List of domains associated with the organization",
      readonly: true,
      title: "Domains",
    },
    logo: {
      type: ["string", "null"],
      format: "data-url",
      description: "Logo URL for the organization",
      title: "Logo",
    },
    default_app_visibility: {
      type: "integer",
      description: "Default visibility level for apps in the organization",
      title: "Default App Visibility",
      enum: [3, 2, 1, 0],
      enumNames: ["Public", "Unlisted", "Organization", "Private"],
      enumDescriptions: [
        "Anyone can access this app",
        "Anyone with the app's published url can access this app",
        "Only members of your organization can access this app",
        "Only you and the selected users can access this app",
      ],
    },
    max_app_visibility: {
      type: "integer",
      description: "Maximum visibility level for apps in the organization",
      title: "Max App Visibility",
      enum: [3, 2, 1, 0],
      enumNames: ["Public", "Unlisted", "Organization", "Private"],
      enumDescriptions: [
        "Anyone can access this app",
        "Anyone with the app's published url can access this app",
        "Only members of your organization can access this app",
        "Only you and the selected users can access this app",
      ],
    },
    default_app_access_permission: {
      type: "integer",
      description:
        "Default access permission for apps shared with organization",
      title: "Default App Access Permission",
      default: 0,
      enum: [0, 1],
      enumNames: ["Read", "Write"],
    },
    default_datasource_access_permission: {
      type: "integer",
      default: 0,
      description:
        "Default access permission for datasources shared with organization",
      title: "Default Datasource Access Permission",
      enum: [0, 1],
      enumNames: ["Read", "Write"],
    },
    allow_user_keys: {
      type: "boolean",
      description: "Allow users to provide their own API keys",
      title: "Allow User Keys",
    },
    use_own_vectorstore: {
      type: "boolean",
      description: "Use own Vectorstore instance instead of Promptly's",
      title: "Use Own Vectorstore",
    },
    use_azure_openai_embeddings: {
      type: "boolean",
      description: "Use Azure's OpenAI for embeddings",
      title: "Azure OpenAI for Embeddings",
    },
    embeddings_api_rate_limit: {
      type: "integer",
      description: "Rate limit for embeddings requests as requests/min",
      title: "Embeddings API Rate Limit",
    },
    vectorstore_weaviate_url: {
      type: ["string", "null"],
      description: "Vectorstore Weaviate URL",
      title: "Vectorstore Weaviate URL",
    },
    vectorstore_weaviate_api_key: {
      type: ["string", "null"],
      description: "Vectorstore Weaviate API key",
      title: "Vectorstore Weaviate API Key",
    },
    vectorstore_weaviate_text2vec_openai_module_config: {
      type: "string",
      description:
        "Configuration for Vectorstore Weaviate text2vec OpenAI module",
      title: "Vectorstore Weaviate Text2Vec OpenAI Module Config",
    },
  },
  required: ["name", "slug", "domains"],
};

const settingsUiSchema = {
  name: {
    "ui:readonly": true,
  },
  slug: {
    "ui:readonly": true,
  },
  domains: {
    "ui:readonly": true,
  },
  logo: {
    "ui:options": {
      accept: "image/*",
    },
  },
  disabled_api_backends: {
    "ui:readonly": true,
  },
  vectorstore_weaviate_text2vec_openai_module_config: {
    "ui:widget": "textarea",
  },
  api_keys: {
    "ui:title": "API Keys",
    "ui:order": [
      "openai_key",
      "stabilityai_key",
      "cohere_key",
      "forefrontai_key",
      "elevenlabs_key",
    ],
  },
  azure_open_ai: {
    "ui:title": "Azure OpenAI",
    "ui:order": ["azure_openai_endpoint", "azure_openai_api_key"],
  },
  aws_settings: {
    "ui:title": "AWS Settings",
    "ui:order": [
      "aws_access_key_id",
      "aws_secret_access_key",
      "aws_default_region",
    ],
  },
  vectorstore_configuration: {
    "ui:title": "Vectorstore Configuration",
    "ui:order": [
      "vectorstore_weaviate_url",
      "vectorstore_weaviate_api_key",
      "vectorstore_weaviate_text2vec_openai_module_config",
    ],
  },
};

export default function OrganizationPage() {
  const providerSchemas = useRecoilValue(providerSchemasSelector);
  const [organizationSettings, setOrganizationSettings] = useState({});
  const [organizationMembers, setOrganizationMembers] = useState([]);
  const [orgMembersRowsPerPage, setOrgMembersRowsPerPage] = useState(10);
  const [orgMembersPage, setOrgMembersPage] = useState(0);

  const saveSettings = () => {
    axios()
      .patch("/api/org/settings", organizationSettings)
      .then((request) => {
        setOrganizationSettings(request.data);
        enqueueSnackbar("Settings saved", { variant: "success" });
      });
  };

  const handleChangeOrgMembersPage = (event, newPage) => {
    setOrgMembersPage(newPage);
  };

  const handleChangeOrgMembersRowsPerPage = (event) => {
    setOrgMembersRowsPerPage(parseInt(event.target.value, 10));
    setOrgMembersPage(0);
  };

  useEffect(() => {
    axios()
      .get("/api/org/settings")
      .then((response) => {
        setOrganizationSettings(response.data);
      });

    axios()
      .get("/api/org/members")
      .then((response) => {
        setOrganizationMembers(response.data);
      });
  }, []);

  const handleProviderConfigChange = useCallback(
    async (
      providerConfigKey,
      providerSlug,
      providerConfigs,
      config,
      toDelete,
    ) => {
      // Verify that the provider slug is valid
      if (
        !providerSlug ||
        !providerSchemas.find((schema) => schema.slug === providerSlug)
      ) {
        enqueueSnackbar("Please select a valid provider", { variant: "error" });
        return;
      }

      // Build the provider configuration object
      const providerConfig = toDelete
        ? {}
        : {
            [`${providerSlug}/${config["processor_slug"]}/${config["model_slug"]}/${config["deployment_key"]}`]:
              {
                ...config,
                provider_slug: providerSlug,
              },
          };

      let updatedProviderConfigs = {};

      if (toDelete && providerConfigKey) {
        updatedProviderConfigs = { ...providerConfigs };
        delete updatedProviderConfigs[providerConfigKey];
      } else {
        updatedProviderConfigs = {
          ...providerConfigs,
          ...providerConfig,
        };
      }

      try {
        await axios().patch("/api/org/settings", {
          provider_configs: updatedProviderConfigs,
        });

        if (providerConfigKey) {
          enqueueSnackbar("Provider configuration updated", {
            variant: "success",
          });
        } else {
          enqueueSnackbar("Provider configuration added", {
            variant: "success",
          });
        }

        window.location.reload();
      } catch (error) {
        if (providerConfigKey) {
          enqueueSnackbar("Failed to update provider configuration", {
            variant: "error",
          });
        } else {
          enqueueSnackbar("Failed to add provider configuration", {
            variant: "error",
          });
        }
      }
    },
    [providerSchemas],
  );

  return (
    <div id="organization-page" style={{ margin: 10 }}>
      <Typography style={pageHeaderStyle} variant="h5">
        Organization
      </Typography>
      <Grid container direction="row" columnSpacing={2}>
        <Grid item md={6} xs={12}>
          <Typography style={sectionHeaderStyle} variant="h6">
            Settings
          </Typography>
          <ThemedJsonForm
            disableAdvanced={true}
            schema={settingsSchema}
            validator={validator}
            uiSchema={settingsUiSchema}
            formData={organizationSettings}
            onChange={({ formData }) => {
              setOrganizationSettings(formData);
            }}
            widgets={{
              FileWidget: (props) => {
                const { value, onChange } = props;
                return (
                  <div>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(event) => {
                        const file = event.target.files[0];
                        const reader = new FileReader();
                        reader.onload = (event) => {
                          onChange(event.target.result);
                        };
                        reader.readAsDataURL(file);
                      }}
                    />
                    {value && (
                      <img
                        src={value}
                        alt="logo"
                        style={{ width: "100%", maxWidth: "200px" }}
                      />
                    )}
                  </div>
                );
              },
            }}
          />
          <Button
            variant="contained"
            color="primary"
            sx={{
              textTransform: "none",
              float: "right",
            }}
            onClick={() => {
              saveSettings();
            }}
          >
            Save Settings
          </Button>
          <p>&nbsp;</p>
          <Typography variant="h6" className="section-header">
            Model Providers
          </Typography>
          <ProviderConfigs
            configs={organizationSettings?.provider_configs || {}}
            handleProviderConfigChange={handleProviderConfigChange}
          />
        </Grid>
        <Grid item md={6} xs={12}>
          <Typography style={sectionHeaderStyle} variant="h6">
            Members
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {organizationMembers
                  ?.slice(
                    orgMembersPage * orgMembersRowsPerPage,
                    orgMembersPage * orgMembersRowsPerPage +
                      orgMembersRowsPerPage,
                  )
                  ?.map((member) => (
                    <TableRow key={member.email}>
                      <TableCell>
                        {member.first_name} {member.last_name}
                      </TableCell>
                      <TableCell>{member.email}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50]}
            component="div"
            count={organizationMembers.length}
            rowsPerPage={orgMembersRowsPerPage}
            page={orgMembersPage}
            onPageChange={handleChangeOrgMembersPage}
            onRowsPerPageChange={handleChangeOrgMembersRowsPerPage}
          />
        </Grid>
      </Grid>
    </div>
  );
}
