const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    [
      "/api",
      "/static/files",
      "/static/appdata",
      "/static/appstore",
      "/static/app_sessions",
      "/static/public/apps/",
    ],
    createProxyMiddleware({
      target: process.env.REACT_APP_API_SERVER
        ? `http://${process.env.REACT_APP_API_SERVER}`
        : "http://localhost:9000",
      changeOrigin: true,
    }),
  );
};
