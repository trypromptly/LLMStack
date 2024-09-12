import { useRecoilValue, useSetRecoilState } from "recoil";
import {
  processorsState,
  providersState,
  dataSourceEntriesState,
  dataSourcesState,
  dataSourceTypesState,
  isLoggedInState,
  organizationState,
  orgDataSourceEntriesState,
  orgDataSourcesState,
  profileFlagsState,
  profileState,
  promptHubState,
} from "./atoms";
import { axios } from "./axios";

export function useLoadProviders() {
  const setProviders = useSetRecoilState(providersState);
  axios()
    .get("/api/apiproviders")
    .then((response) => {
      // handle success
      setProviders(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useLoadProcessors() {
  const setProcessors = useSetRecoilState(processorsState);
  const organization = useRecoilValue(organizationState);
  const profileFlags = useRecoilValue(profileFlagsState);

  axios()
    .get("/api/apibackends")
    .then((response) => {
      // Disable api backends that are disabled for the organization
      setProcessors(
        response.data.filter(
          (processor) =>
            !profileFlags.IS_ORGANIZATION_MEMBER ||
            organization.disabled_api_backends.indexOf(processor.id) === -1,
        ),
      );
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useLoadProfile() {
  const setProfile = useSetRecoilState(profileState);
  const setIsLoggedIn = useSetRecoilState(isLoggedInState);

  axios()
    .get("/api/profiles/me")
    .then((response) => {
      setProfile(response.data);
      setIsLoggedIn(true);
    })
    .catch((error) => {
      // handle error
      setIsLoggedIn(false);
    })
    .then({
      // always executed
    });
}

export function useLoadPromptHub() {
  const setPromptHub = useSetRecoilState(promptHubState);
  axios()
    .get("/api/hub")
    .then((response) => {
      // handle success
      setPromptHub(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useLoadDataSources() {
  const setDataSources = useSetRecoilState(dataSourcesState);
  axios()
    .get("/api/datasources")
    .then((response) => {
      // handle success
      setDataSources(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useReloadDataSources() {
  const setDataSources = useSetRecoilState(dataSourcesState);
  return () => {
    axios()
      .get("/api/datasources")
      .then((response) => {
        // handle success
        setDataSources(response.data);
      })
      .catch((error) => {
        // handle error
      })
      .then({
        // always executed
      });
  };
}

export function useLoadOrgDataSources() {
  const setOrgDataSources = useSetRecoilState(orgDataSourcesState);

  axios()
    .get("/api/profiles/me")
    .then((response) => {
      if (response.data.organization !== null) {
        axios()
          .get("/api/org/datasources")
          .then((response) => {
            // handle success
            setOrgDataSources(response.data);
          })
          .catch((error) => {
            // handle error
          })
          .then({
            // always executed
          });
      }
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useReloadOrgDataSources() {
  const setOrgDataSources = useSetRecoilState(orgDataSourcesState);

  return () => {
    axios()
      .get("/api/profiles/me")
      .then((response) => {
        if (response.data.organization !== null) {
          axios()
            .get("/api/org/datasources")
            .then((response) => {
              // handle success
              setOrgDataSources(response.data);
            })
            .catch((error) => {
              // handle error
            })
            .then({
              // always executed
            });
        }
      })
      .catch((error) => {
        // handle error
      })
      .then({
        // always executed
      });
  };
}

export function useLoadDataSourceTypes() {
  const setDataSourceTypes = useSetRecoilState(dataSourceTypesState);
  axios()
    .get("/api/datasource_types")
    .then((response) => {
      // handle success
      setDataSourceTypes(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useLoadDataSourceEntries() {
  const setDataSourceEntries = useSetRecoilState(dataSourceEntriesState);
  axios()
    .get("/api/datasource_entries")
    .then((response) => {
      // handle success
      setDataSourceEntries(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useReloadDataSourceEntries() {
  const setDataSourceEntries = useSetRecoilState(dataSourceEntriesState);
  return () => {
    axios()
      .get("/api/datasource_entries")
      .then((response) => {
        // handle success
        setDataSourceEntries(response.data);
      })
      .catch((error) => {
        // handle error
      })
      .then({
        // always executed
      });
  };
}

export function useLoadOrgDataSourceEntries() {
  const setOrgDataSourceEntries = useSetRecoilState(orgDataSourceEntriesState);
  axios()
    .get("/api/profiles/me")
    .then((response) => {
      if (response.data.organization !== null) {
        axios()
          .get("/api/org/datasource_entries")
          .then((response) => {
            // handle success
            setOrgDataSourceEntries(response.data);
          })
          .catch((error) => {
            // handle error
          })
          .then({
            // always executed
          });
      }
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useReloadOrgDataSourceEntries() {
  const setOrgDataSourceEntries = useSetRecoilState(orgDataSourceEntriesState);
  axios()
    .get("/api/profiles/me")
    .then((response) => {
      if (response.data.organization !== null) {
        axios()
          .get("/api/org/datasource_entries")
          .then((response) => {
            // handle success
            setOrgDataSourceEntries(response.data);
          })
          .catch((error) => {
            // handle error
          })
          .then({
            // always executed
          });
      }
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useReloadDataSourcesAndEntries() {
  const reloadDataSources = useReloadDataSources();
  const reloadDataSourcesEntries = useReloadDataSourceEntries();
  return () => {
    reloadDataSources();
    reloadDataSourcesEntries();
  };
}

export function useLoadProfileFlags() {
  const setProfileFlags = useSetRecoilState(profileFlagsState);
  axios()
    .get("/api/profiles/me/flags")
    .then((response) => {
      // handle success
      setProfileFlags(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useLoadOrganization() {
  const setOrganization = useSetRecoilState(organizationState);
  axios()
    .get("/api/org")
    .then((response) => {
      // handle success
      setOrganization(response.data);
    })
    .catch((error) => {
      // handle error
    })
    .then({
      // always executed
    });
}

export function useReloadOrgDataSourcesAndEntries() {
  const reloadOrgDataSources = useReloadOrgDataSources();
  const reloadOrgDataSourcesEntries = useReloadOrgDataSourceEntries();
  return () => {
    reloadOrgDataSources();
    reloadOrgDataSourcesEntries();
  };
}
