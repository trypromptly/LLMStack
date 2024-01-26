import axiosLib from "axios";
import { enqueueSnackbar } from "notistack";

export const axios = () => {
  let caxios = axiosLib.create({
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
  });

  if (
    window.location.pathname.endsWith("/embed") &&
    window.location.search.includes("_signature")
  ) {
    const searchParams = new URLSearchParams(window.location.search);
    const signature = searchParams.get("_signature");

    if (signature) {
      caxios.defaults.headers.common["Authorization"] =
        "X-Embed-Signature " + signature;
    }
    caxios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response.status === 401 || error.response.status === 403) {
          window.location.href = "/session-expired";
        }
        return Promise.reject(error);
      },
    );
  } else {
    caxios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (
          !window.location.pathname.startsWith("/s/") &&
          !window.location.pathname.startsWith("/hub") &&
          !window.location.pathname.startsWith("/app/") &&
          (error.response.status === 401 || error.response.status === 403)
        ) {
          window.location.href =
            "/login?redirectUrl=" + window.location.pathname;
        }

        try {
          enqueueSnackbar("Error Occurred", { variant: "error" });
        } catch (e) {
          // Ignore
        }

        return Promise.reject(error);
      },
    );
  }

  return caxios;
};
