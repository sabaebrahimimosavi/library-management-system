// js/config.js
// Frontend is now served by Django itself (see core/urls.py), so the
// API lives on the same origin — a relative path works and doesn't
// break if the port/host ever changes.
export const API_BASE_URL = "/api/v1";