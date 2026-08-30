/**
 * Frontend configuration.
 *
 * Change API_BASE_URL to the address where the Flask backend is deployed
 * (no trailing slash). During local development this is usually
 * "http://127.0.0.1:5000". After deploying the backend (Render, Railway,
 * Fly.io, PythonAnywhere, a VPS, ...), replace it with that public URL.
 */
window.RUMA_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:5000",
};
