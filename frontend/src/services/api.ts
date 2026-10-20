import axios from "axios";

const API = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

API.interceptors.response.use(
  (r) => r,
  async (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      // clear session and let the app redirect
      window.dispatchEvent(new Event("auth:logout"));
    }
    return Promise.reject(error);
  },
);

export default API;

export type { AxiosResponse } from "axios";
