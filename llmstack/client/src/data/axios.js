import axiosLib from "axios";
import { enqueueSnackbar } from "notistack";

export const axios = () => {
  const caxios = axiosLib.create({
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
  });

  caxios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (
        !window.location.pathname.startsWith("/s/") &&
        !window.location.pathname.startsWith("/hub") &&
        !window.location.pathname.startsWith("/app/") &&
        (error.response.status === 401 || error.response.status === 403)
      ) {
        window.location.href = "/login?redirectUrl=" + window.location.pathname;
      }

      try {
        enqueueSnackbar("Error Occurred", { variant: "error" });
      } catch (e) {
        // Ignore
      }

      return Promise.reject(error);
    },
  );

  return caxios;
};
