const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    "/api",
    createProxyMiddleware({
      target: process.env.REACT_APP_API_SERVER
        ? `http://${process.env.REACT_APP_API_SERVER}`
        : "http://localhost:9000",
      changeOrigin: true,
    }),
  );
};
