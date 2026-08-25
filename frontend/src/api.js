export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "masterbooking_access_token";

export const authStorage = {
  get() {
    return localStorage.getItem(TOKEN_KEY);
  },
  set(token) {
    localStorage.setItem(TOKEN_KEY, token);
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
  },
};

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function extractMessage(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => item?.msg || "Ошибка валидации")
      .join(" · ");
  }
  if (typeof payload.message === "string") return payload.message;
  return fallback;
}

export async function api(path, options = {}) {
  const {
    method = "GET",
    body,
    auth = false,
    headers = {},
    raw = false,
  } = options;

  const requestHeaders = { ...headers };
  const token = authStorage.get();

  if (auth && token) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  let requestBody = body;
  if (body && !(body instanceof FormData) && typeof body !== "string") {
    requestHeaders["Content-Type"] = "application/json";
    requestBody = JSON.stringify(body);
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: requestHeaders,
    body: requestBody,
  });

  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : await response.text().catch(() => "");

  if (!response.ok) {
    if (response.status === 401 && auth) {
      authStorage.clear();
    }
    throw new ApiError(
      extractMessage(payload, `Ошибка запроса (${response.status})`),
      response.status,
      payload,
    );
  }

  return raw ? response : payload;
}

export function resolveMediaUrl(url) {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  return `${API_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}

export const endpoints = {
  register: (data) => api("/auth/register", { method: "POST", body: data }),
  login: async (email, password) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return api("/auth/login", {
      method: "POST",
      body: form.toString(),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  forgotPassword: (email) => api("/auth/forgot-password", { method: "POST", body: { email } }),
  resetPassword: (token, new_password) => api("/auth/reset-password", { method: "POST", body: { token, new_password } }),

  me: () => api("/users/me", { auth: true }),
  updateMe: (data) => api("/users/me", { method: "PATCH", body: data, auth: true }),
  uploadAvatar: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api("/users/me/avatar", { method: "POST", body: form, auth: true });
  },
  deleteAvatar: () => api("/users/me/avatar", { method: "DELETE", auth: true }),

  categories: () => api("/categories"),
  categoryTree: () => api("/categories/tree"),
  tags: () => api("/tags"),
  cities: () => api("/locations/cities"),
  districts: (cityId) => api(`/locations/cities/${cityId}/districts`),

  masters: () => api("/masters"),
  master: (id) => api(`/masters/${id}`),
  masterMe: () => api("/masters/me", { auth: true }),
  createMasterProfile: (data) => api("/masters/profile", { method: "POST", body: data, auth: true }),
  updateMasterProfile: (data) => api("/masters/me", { method: "PATCH", body: data, auth: true }),

  offerings: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") query.set(key, value);
    });
    const suffix = query.toString() ? `?${query}` : "";
    return api(`/offerings${suffix}`);
  },
  offering: (id) => api(`/offerings/${id}`),
  masterOfferings: (masterId) => api(`/masters/${masterId}/offerings`),
  myOfferings: () => api("/masters/me/offerings", { auth: true }),
  createOffering: (data) => api("/masters/me/offerings", { method: "POST", body: data, auth: true }),
  updateOffering: (id, data) => api(`/offerings/${id}`, { method: "PATCH", body: data, auth: true }),
  deleteOffering: (id) => api(`/offerings/${id}`, { method: "DELETE", auth: true }),
  offeringImages: (id) => api(`/offerings/${id}/images`),
  uploadOfferingImage: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return api(`/offerings/${id}/images`, { method: "POST", body: form, auth: true });
  },
  setPrimaryImage: (offeringId, imageId) => api(`/offerings/${offeringId}/images/${imageId}/primary`, { method: "PATCH", auth: true }),
  deleteOfferingImage: (offeringId, imageId) => api(`/offerings/${offeringId}/images/${imageId}`, { method: "DELETE", auth: true }),

  availableSlots: (masterId, offeringId, bookingDate) => {
    const query = new URLSearchParams({ offering_id: offeringId, booking_date: bookingDate });
    return api(`/masters/${masterId}/available-slots?${query}`);
  },
  createBooking: (masterId, data) => api(`/masters/${masterId}/bookings`, { method: "POST", body: data, auth: true }),
  myBookings: () => api("/users/me/bookings", { auth: true }),
  cancelBooking: (id) => api(`/users/me/bookings/${id}/cancel`, { method: "PATCH", auth: true }),
  masterBookings: (date) => api(`/masters/me/bookings?booking_date=${encodeURIComponent(date)}`, { auth: true }),
  updateBookingStatus: (id, status) => api(`/masters/me/bookings/${id}/status`, { method: "PATCH", body: { status }, auth: true }),

  masterSchedules: (masterId) => api(`/masters/${masterId}/schedules`),
  mySchedules: () => api("/masters/me/schedules", { auth: true }),
  createSchedule: (data) => api("/masters/me/schedules", { method: "POST", body: data, auth: true }),
  updateSchedule: (id, data) => api(`/schedules/${id}`, { method: "PATCH", body: data, auth: true }),
  deleteSchedule: (id) => api(`/schedules/${id}`, { method: "DELETE", auth: true }),

  masterReviewsFull: (masterId) => api(`/masters/${masterId}/reviews/full`),
  masterReviewStats: (masterId) => api(`/masters/${masterId}/reviews/stats`),
  myMasterReviews: () => api("/masters/me/reviews", { auth: true }),
  createReview: (bookingId, data) => api(`/bookings/${bookingId}/review`, { method: "POST", body: data, auth: true }),

  adminCategories: () => api("/categories/admin", { auth: true }),
  createCategory: (data) => api("/categories", { method: "POST", body: data, auth: true }),
  updateCategory: (id, data) => api(`/categories/${id}`, { method: "PATCH", body: data, auth: true }),
  deleteCategory: (id) => api(`/categories/${id}`, { method: "DELETE", auth: true }),
  adminTags: () => api("/tags/admin", { auth: true }),
  createTag: (data) => api("/tags", { method: "POST", body: data, auth: true }),
  updateTag: (id, data) => api(`/tags/${id}`, { method: "PATCH", body: data, auth: true }),
  deleteTag: (id) => api(`/tags/${id}`, { method: "DELETE", auth: true }),
  createCity: (data) => api("/locations/cities", { method: "POST", body: data, auth: true }),
  updateCity: (id, data) => api(`/locations/cities/${id}`, { method: "PATCH", body: data, auth: true }),
  deleteCity: (id) => api(`/locations/cities/${id}`, { method: "DELETE", auth: true }),
  createDistrict: (data) => api("/locations/districts", { method: "POST", body: data, auth: true }),
  updateDistrict: (id, data) => api(`/locations/districts/${id}`, { method: "PATCH", body: data, auth: true }),
  deleteDistrict: (id) => api(`/locations/districts/${id}`, { method: "DELETE", auth: true }),
};
