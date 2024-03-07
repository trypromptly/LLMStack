import { atom, atomFamily, selector } from "recoil";
import { axios } from "./axios";

const apiProvidersFetchSelector = selector({
  key: "apiProvidersFetchSelector",
  get: async () => {
    try {
      const apiProviders = await axios().get("/api/apiproviders");
      return apiProviders.data;
    } catch (error) {
      return [];
    }
  },
});

const apiBackendsFetchSelector = selector({
  key: "apiBackendsFetchSelector",
  get: async () => {
    try {
      const apiBackends = await axios().get("/api/apibackends");
      return apiBackends.data;
    } catch (error) {
      return [];
    }
  },
});

const endpointsFetchSelector = selector({
  key: "endpointsFetchSelector",
  get: async () => {
    try {
      const endpoints = await axios().get("/api/endpoints");
      return endpoints.data;
    } catch (error) {
      return [];
    }
  },
});

const dataSourcesFetchSelector = selector({
  key: "dataSourcesFetchSelector",
  get: async () => {
    try {
      const dataSources = await axios().get("/api/datasources");
      return dataSources.data;
    } catch (error) {
      return [];
    }
  },
});

const dataSourceTypesFetchSelector = selector({
  key: "dataSourceTypesFetchSelector",
  get: async () => {
    try {
      const dataSourceTypes = await axios().get("/api/datasource_types");
      return dataSourceTypes.data;
    } catch (error) {
      return [];
    }
  },
});

export const apiProvidersState = atom({
  key: "apiProviders",
  default: apiProvidersFetchSelector,
});

export const apiProviderDropdownListState = selector({
  key: "apiProviderDropdownList",
  get: async ({ get }) => {
    const apiProviders = await get(apiProvidersState);
    return apiProviders.map((x) => {
      return { label: x.name, value: x.name };
    });
  },
});

export const apiProviderSelectedState = atom({
  key: "apiProviderSelected",
  default: null,
});

export const apiBackendsState = atom({
  key: "apiBackends",
  default: apiBackendsFetchSelector,
});

export const apiBackendDropdownListState = selector({
  key: "apiBackendDropdownList",
  get: ({ get }) => {
    const apiBackends = get(apiBackendsState);
    const organization = get(organizationState);
    return apiBackends
      .filter(
        (apiBackend) =>
          (organization?.disabled_api_backends || []).indexOf(apiBackend.id) ===
          -1,
      )
      .map((x) => {
        return { label: x.name, value: x.id, provider: x.api_provider.name };
      });
  },
});

export const apiBackendSelectedState = atom({
  key: "apiBackendSelected",
  default: null,
});

export const endpointsState = atom({
  key: "endpoints",
  default: endpointsFetchSelector,
});

export const endpointDropdownListState = selector({
  key: "endpointDropdownList",
  get: ({ get }) => {
    const endpoints = get(endpointsState);
    const parentEndpoints = endpoints
      .filter((x) => x.version === 0 && !x.draft)
      .sort((a, b) => (a.created_on < b.created_on ? 1 : -1));
    return parentEndpoints.map((x) => {
      return {
        label: `${x.api_backend.api_provider.name} » ${x.api_backend.name} » ${x.name}`,
        uuid: x.uuid,
        options: endpoints
          .filter((y) => y.parent_uuid === x.uuid)
          .map((z) => {
            return {
              label: `${z.version}: ${z.description}`,
              value: `${z.parent_uuid}:${z.version}`,
              version: z.version,
              backend: x.api_backend.name,
              provider: x.api_backend.api_provider.name,
              is_live: z.is_live,
              uuid: z.uuid,
            };
          }),
      };
    });
  },
});

export const endpointSelectedState = atom({
  key: "endpointSelected",
  default: null,
});

export const endpointTableDataState = selector({
  key: "endpointTableData",
  get: ({ get }) => {
    const endpoints = get(endpointsState)
      .filter((endpoint) => !endpoint.draft)
      .sort((a, b) => (a.created_on < b.created_on ? 1 : -1));

    // map of parent endpoints
    const parentEndpoints = endpoints
      .filter((x) => x.version === 0)
      .reduce((acc, entry) => {
        const entry_map = {
          [entry.uuid]: { ...entry, versions: [], key: entry.uuid },
        };
        return { ...acc, ...entry_map };
      }, {});

    const childEndpoints = endpoints.filter((x) => x.version !== 0);

    for (let i = 0; i < childEndpoints.length; i++) {
      if (childEndpoints[i].parent_uuid in parentEndpoints) {
        parentEndpoints[childEndpoints[i].parent_uuid].versions.push({
          ...childEndpoints[i],
          key: childEndpoints[i].uuid,
        });
      }
    }
    return Object.values(parentEndpoints);
  },
});

export const endpointVersionsState = atom({
  key: "endpointVersions",
  default: [],
});

export const endpointConfigValueState = atom({
  key: "endpointConfigValue",
  default: {},
});

export const templateValueState = atom({
  key: "promptValues",
  default: {},
});

export const inputValueState = atom({
  key: "inputValue",
  default: {},
});

export const saveEndpointModalVisibleState = atom({
  key: "saveEndpointModalVisible",
  default: false,
});

export const saveEndpointVersionModalVisibleState = atom({
  key: "saveEndpointVersionModalVisible",
  default: false,
});

export const shareEndpointModalVisibleState = atom({
  key: "shareEndpointModalVisible",
  default: false,
});

export const endpointShareCodeValueState = atom({
  key: "endpointShareCodeValue",
  default: null,
});

export const profileFetchSelector = selector({
  key: "profileFetchSelector",
  get: async () => {
    try {
      const profile = await axios().get("/api/profiles/me");
      return profile.data;
    } catch (error) {
      return null;
    }
  },
});

export const profileState = atom({
  key: "profileValue",
  default: profileFetchSelector,
});

export const isLoggedInState = selector({
  key: "isLoggedIn",
  get: ({ get }) => {
    return get(profileState) !== null;
  },
});

export const promptHubState = atom({
  key: "promptHubState",
  default: [],
});

export const promptHubListState = selector({
  key: "promptHubList",
  get: ({ get }) => {
    const promptHub = get(promptHubState);
    return promptHub;
  },
});

export const dataSourcesState = atom({
  key: "dataSourcesState",
  default: dataSourcesFetchSelector,
});

export const orgDataSourcesState = selector({
  key: "orgDataSourcesState",
  get: async ({ get }) => {
    try {
      const profileFlags = get(profileFlagsState);
      if (!profileFlags.IS_ORGANIZATION_MEMBER) {
        return [];
      }
      const dataSources = await axios().get("/api/org/datasources");
      return dataSources.data;
    } catch (error) {
      return [];
    }
  },
});

export const dataSourceTypesState = atom({
  key: "dataSourceTypesState",
  default: dataSourceTypesFetchSelector,
});

export const dataSourceEntriesState = atom({
  key: "dataSourceEntriesState",
  default: [],
});

export const orgDataSourceEntriesState = atom({
  key: "orgDataSourceEntriesState",
  default: [],
});

export const dataSourceEntriesTableDataState = selector({
  key: "dataSourceEntriesTableData",
  get: ({ get }) => {
    let dataSourceEntries = get(dataSourceEntriesState);
    let profileFlags = get(profileFlagsState);

    dataSourceEntries = dataSourceEntries.map((x) => {
      return { isUserOwned: true, ...x };
    });
    let orgDataSourceEntries = profileFlags.IS_ORGANIZATION_MEMBER
      ? get(orgDataSourceEntriesState)
      : [];
    orgDataSourceEntries = orgDataSourceEntries.map((x) => {
      return { isUserOwned: false, ...x };
    });

    let privateDataSources = get(dataSourcesState);
    privateDataSources = privateDataSources.map((x) => {
      return { isUserOwned: true, ...x };
    });
    const privateDataSourcesUUIDs = privateDataSources.map((x) => x.uuid);

    let orgDataSources = profileFlags.IS_ORGANIZATION_MEMBER
      ? get(orgDataSourcesState)
      : [];
    orgDataSources = orgDataSources.map((x) => {
      return { isUserOwned: false, ...x };
    });

    orgDataSources = orgDataSources.filter(
      (x) => !privateDataSourcesUUIDs.includes(x.uuid),
    );

    let result = [];
    const datasource_entries_map = {};
    const org_datasource_entries_map = {};

    for (let i = 0; i < dataSourceEntries.length; i++) {
      if (dataSourceEntries[i].datasource.uuid in datasource_entries_map) {
        datasource_entries_map[dataSourceEntries[i].datasource.uuid].push(
          dataSourceEntries[i],
        );
      } else {
        datasource_entries_map[dataSourceEntries[i].datasource.uuid] = [
          dataSourceEntries[i],
        ];
      }
    }

    for (let i = 0; i < orgDataSourceEntries.length; i++) {
      if (
        orgDataSourceEntries[i].datasource.uuid in org_datasource_entries_map
      ) {
        org_datasource_entries_map[
          orgDataSourceEntries[i].datasource.uuid
        ].push(orgDataSourceEntries[i]);
      } else {
        org_datasource_entries_map[orgDataSourceEntries[i].datasource.uuid] = [
          orgDataSourceEntries[i],
        ];
      }
    }

    for (let i = 0; i < privateDataSources.length; i++) {
      result.push({
        ...privateDataSources[i],
        ...{
          data_source_entries:
            datasource_entries_map[privateDataSources[i].uuid] || [],
        },
      });
    }

    for (let i = 0; i < orgDataSources.length; i++) {
      result.push({
        ...orgDataSources[i],
        ...{
          data_source_entries:
            org_datasource_entries_map[orgDataSources[i].uuid] || [],
        },
      });
    }

    return result;
  },
});

export const isMobileState = atom({
  key: "isMobileState",
  default: window.innerWidth < 768,
});

const appTemplatesFetchSelector = selector({
  key: "appTemplatesFetchSelector",
  get: async () => {
    try {
      const appTemplates = await axios().get("/api/apps/templates");
      return appTemplates.data;
    } catch (error) {
      return [];
    }
  },
});

export const appTemplatesState = atom({
  key: "appTemplatesState",
  default: appTemplatesFetchSelector,
});

export const appTemplateState = atomFamily({
  key: "appTemplateState",
  default: async (templateSlug) => {
    if (!templateSlug || templateSlug === "_blank_") {
      return {};
    }

    try {
      const appTemplate = await axios().get(
        `/api/apps/templates/${templateSlug}`,
      );
      return appTemplate.data;
    } catch (error) {
      return {};
    }
  },
});

export const storeAppState = atomFamily({
  key: "storeAppState",
  default: async (appSlug) => {
    if (!appSlug) {
      return null;
    }

    try {
      const app = await axios().get(
        `/api/store/apps/${appSlug}?include_data=true`,
      );
      return app.data;
    } catch (error) {
      console.error(error);
      return null;
    }
  },
});

export const appsByStoreCategoryState = atomFamily({
  key: "appsByStoreCategoryState",
  default: async (category) => {
    if (!category) {
      return [];
    }

    try {
      const apps = await axios().get(`/api/store/categories/${category}/apps`);
      return apps.data?.results;
    } catch (error) {
      return [];
    }
  },
});

export const storeCategoriesState = atom({
  key: "storeCategoriesState",
  default: async () => {
    try {
      const categories = await axios().get("/api/store/categories");
      return categories.data;
    } catch (error) {
      return [];
    }
  },
});

export const storeCategoriesSlugState = selector({
  key: "storeCategoriesSlugState",
  get: async ({ get }) => {
    const categories = await get(storeCategoriesState)();
    return categories.map((x) => x.slug);
  },
});

export const embedDatasourceState = atomFamily({
  key: "embedDatasourceState",
  default: async (datasourceUUID) => {
    if (!datasourceUUID) {
      return {};
    }

    try {
      const embedDatasource = await axios().get(
        `/api/datasources/${datasourceUUID}`,
      );
      return embedDatasource.data;
    } catch (error) {
      return {};
    }
  },
});

export const embedDatasourceEntriesState = atomFamily({
  key: "embedDatasourceEntriesState",
  default: async (datasourceUUID) => {
    if (!datasourceUUID) {
      return [];
    }

    try {
      const embedDatasource = await axios().get(
        `/api/datasources/${datasourceUUID}/entries`,
      );
      return embedDatasource.data;
    } catch (error) {
      return [];
    }
  },
});

export const appDebugState = atom({
  key: "appDebugState",
  default: {},
});

const appsFetchSelector = selector({
  key: "appsFetchSelector",
  get: async () => {
    try {
      const apps = await axios().get("/api/apps");
      return apps.data;
    } catch (error) {
      return [];
    }
  },
});

export const appsState = atom({
  key: "appsState",
  default: appsFetchSelector,
});

const appsBriefFetchSelector = selector({
  key: "appsBriefFetchSelector",
  get: async () => {
    try {
      const apps = await axios().get(
        "/api/apps?fields=uuid,name,visibility,is_published,app_type_name,unique_processors,published_uuid",
      );
      return apps.data;
    } catch (error) {
      return [];
    }
  },
});

export const appsBriefState = atom({
  key: "appsBriefState",
  default: appsBriefFetchSelector,
});

export const profileFlagsFetchSelector = selector({
  key: "profileFlagsFetchSelector",
  get: async () => {
    try {
      const profile = await axios().get("/api/profiles/me/flags");
      return profile.data;
    } catch (error) {
      return {};
    }
  },
});

export const profileFlagsState = atom({
  key: "profileFlagsState",
  default: profileFlagsFetchSelector,
});

export const organizationFetchSelector = selector({
  key: "organizationFetchSelector",
  get: async () => {
    try {
      const organization = await axios().get("/api/org");
      return organization.data;
    } catch (error) {
      return null;
    }
  },
});

export const organizationState = atom({
  key: "organizationState",
  default: organizationFetchSelector,
});

export const connectionTypesFetchSelector = selector({
  key: "connectionTypesFetchSelector",
  get: async () => {
    try {
      const connectionTypes = await axios().get("/api/connection_types");
      return connectionTypes.data;
    } catch (error) {
      return [];
    }
  },
});

export const connectionTypesState = atom({
  key: "connectionTypesState",
  default: connectionTypesFetchSelector,
});

export const connectionsFetchSelector = selector({
  key: "connectionsFetchSelector",
  get: async () => {
    try {
      const connections = await axios().get("/api/connections");
      return connections.data;
    } catch (error) {
      return [];
    }
  },
});

export const connectionsState = atom({
  key: "connectionsState",
  default: connectionsFetchSelector,
});

export const appEditorValidationErrorsState = atom({
  key: "appEditorValidationErrorsState",
  default: {},
});

// Maintains runtime information for the app being used
export const appRunDataState = atom({
  key: "appRunData",
  default: {},
});

export const isUsageLimitReachedState = selector({
  key: "isUsageLimitReached",
  get: ({ get }) => {
    try {
      return get(appRunDataState)?.isUsageLimited;
    } catch (error) {
      return false;
    }
  },
});
