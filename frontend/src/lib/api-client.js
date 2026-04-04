"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.apiClient = exports.API_BASE_URL = void 0;
exports.composeEndpoint = composeEndpoint;
var auth_client_1 = require("./auth-client");
function getApiBaseUrl() {
    var envUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
    if (envUrl) {
        return envUrl.replace(/\/+$|\/+$/g, "");
    }
    if (typeof window !== "undefined") {
        return ""; // relative same-origin path is preferred in browser to use /api rewrites
    }
    return "http://localhost:8000";
}
exports.API_BASE_URL = getApiBaseUrl();
function composeEndpoint(path, apiVersionPrefix) {
    if (apiVersionPrefix === void 0) { apiVersionPrefix = true; }
    var cleanedPath = "/".concat(path.replace(/^\/+/, ""));
    var effectivePath = cleanedPath;
    if (apiVersionPrefix && !cleanedPath.startsWith("/api/v1")) {
        effectivePath = "/api/v1".concat(cleanedPath);
    }
    var base = exports.API_BASE_URL.replace(/\/+$/g, "");
    return base ? "".concat(base).concat(effectivePath) : effectivePath;
}
var ApiError = /** @class */ (function (_super) {
    __extends(ApiError, _super);
    function ApiError(message, status, data) {
        if (data === void 0) { data = {}; }
        var _this = _super.call(this, message) || this;
        _this.name = "ApiError";
        _this.status = status;
        _this.data = data;
        return _this;
    }
    return ApiError;
}(Error));
function isProtectedClientRoute(pathname) {
    return pathname.startsWith("/dashboard");
}
/**
 * Hardened Fetch Wrapper with Network Timeout and Interceptor capabilities.
 */
function request(path_1) {
    return __awaiter(this, arguments, void 0, function (path, options) {
        // Double-submit CSRF header
        function getCookie(name) {
            var _a;
            if (typeof document === "undefined")
                return null;
            var value = "; ".concat(document.cookie);
            var parts = value.split("; ".concat(name, "="));
            if (parts.length === 2)
                return ((_a = parts.pop()) === null || _a === void 0 ? void 0 : _a.split(";").shift()) || null;
            return null;
        }
        var _a, timeout, params, json, fetchOptions, apiUrl, url, fetchUrl, controller, id, headers, token, xsrf, response, refreshUrl, refreshResponse, retryHeaders, refreshedToken, retryResponse, currentPath, errorData, message, rawText, data, formatted, text, error_1;
        if (options === void 0) { options = {}; }
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    _a = options.timeout, timeout = _a === void 0 ? 30000 : _a, params = options.params, json = options.json, fetchOptions = __rest(options, ["timeout", "params", "json"]);
                    apiUrl = composeEndpoint(path, true);
                    url = new URL(apiUrl, typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");
                    if (params) {
                        Object.entries(params).forEach(function (_a) {
                            var key = _a[0], value = _a[1];
                            return url.searchParams.append(key, value);
                        });
                    }
                    fetchUrl = exports.API_BASE_URL ? url.toString() : url.pathname + url.search;
                    controller = new AbortController();
                    id = setTimeout(function () { return controller.abort(); }, timeout);
                    headers = new Headers(fetchOptions.headers || {});
                    if (!headers.has("Content-Type") && json) {
                        headers.set("Content-Type", "application/json");
                    }
                    token = (0, auth_client_1.getToken)();
                    if (!!token) return [3 /*break*/, 2];
                    return [4 /*yield*/, (0, auth_client_1.getAuthToken)()];
                case 1:
                    token = _b.sent();
                    _b.label = 2;
                case 2:
                    if (token) {
                        headers.set("Authorization", "Bearer ".concat(token));
                    }
                    xsrf = getCookie("xsrf-token");
                    if (xsrf) {
                        if (!headers.has("X-XSRF-TOKEN")) {
                            headers.set("X-XSRF-TOKEN", xsrf);
                        }
                        if (!headers.has("x-xsrf-token")) {
                            headers.set("x-xsrf-token", xsrf);
                        }
                    }
                    _b.label = 3;
                case 3:
                    _b.trys.push([3, 12, , 13]);
                    return [4 /*yield*/, fetch(fetchUrl, __assign(__assign({}, fetchOptions), { headers: headers, body: json ? JSON.stringify(json) : fetchOptions.body, signal: controller.signal, credentials: "include" }))];
                case 4:
                    response = _b.sent();
                    clearTimeout(id);
                    if (!(response.status === 401 || response.status === 403)) return [3 /*break*/, 8];
                    refreshUrl = composeEndpoint("/auth/refresh", true);
                    return [4 /*yield*/, fetch(refreshUrl, {
                            method: "POST",
                            credentials: "include",
                            headers: {
                                Accept: "application/json",
                            },
                        }).catch(function () { return null; })];
                case 5:
                    refreshResponse = _b.sent();
                    if (!(refreshResponse === null || refreshResponse === void 0 ? void 0 : refreshResponse.ok)) return [3 /*break*/, 7];
                    retryHeaders = new Headers(headers);
                    refreshedToken = (0, auth_client_1.getToken)();
                    if (refreshedToken) {
                        retryHeaders.set("Authorization", "Bearer ".concat(refreshedToken));
                    }
                    else {
                        retryHeaders.delete("Authorization");
                    }
                    return [4 /*yield*/, fetch(fetchUrl, __assign(__assign({}, fetchOptions), { headers: retryHeaders, body: json ? JSON.stringify(json) : fetchOptions.body, credentials: "include" }))];
                case 6:
                    retryResponse = _b.sent();
                    if (retryResponse.ok) {
                        return [2 /*return*/, retryResponse.json()];
                    }
                    _b.label = 7;
                case 7:
                    // If refresh fails, only force login from protected routes.
                    // Public pages may call endpoints opportunistically and should not be hard-redirected.
                    if (typeof window !== "undefined") {
                        currentPath = window.location.pathname || "";
                        if (isProtectedClientRoute(currentPath)) {
                            window.location.assign("/login");
                        }
                    }
                    throw new ApiError("Session expired", response.status);
                case 8:
                    if (!!response.ok) return [3 /*break*/, 10];
                    errorData = {};
                    message = "Request failed";
                    return [4 /*yield*/, response.text().catch(function () { return ""; })];
                case 9:
                    rawText = _b.sent();
                    if (rawText) {
                        try {
                            errorData = JSON.parse(rawText);
                            if (typeof errorData === "object" && errorData !== null) {
                                data = errorData;
                                if (data.detail) {
                                    message = String(data.detail);
                                }
                                else if (data.error) {
                                    message = String(data.error);
                                }
                                else {
                                    message = rawText;
                                }
                            }
                            else {
                                message = rawText;
                            }
                        }
                        catch (_c) {
                            message = rawText;
                        }
                    }
                    formatted = "".concat(response.status, " ").concat(response.statusText, ": ").concat(message);
                    throw new ApiError(formatted, response.status, errorData);
                case 10:
                    // 6. Response Parsing
                    if (response.status === 204 || response.headers.get("content-length") === "0") {
                        return [2 /*return*/, null];
                    }
                    return [4 /*yield*/, response.text().catch(function () { return ""; })];
                case 11:
                    text = _b.sent();
                    if (!text) {
                        return [2 /*return*/, null];
                    }
                    try {
                        return [2 /*return*/, JSON.parse(text)];
                    }
                    catch (_d) {
                        throw new ApiError("Failed to parse JSON response: ".concat(text.slice(0, 100)), response.status, text);
                    }
                    return [3 /*break*/, 13];
                case 12:
                    error_1 = _b.sent();
                    clearTimeout(id);
                    if (error_1 instanceof Error && error_1.name === "AbortError") {
                        throw new Error("Request timed out after ".concat(timeout, "ms"));
                    }
                    if (error_1 instanceof TypeError) {
                        // Network-level issue (DNS, CORS, unreachable backend)
                        throw new Error("Network error while calling ".concat(url.toString(), ". Ensure backend is reachable or use same-origin /api rewrites. (").concat(error_1.message, ")"));
                    }
                    throw error_1;
                case 13: return [2 /*return*/];
            }
        });
    });
}
// Exported public API client instance
exports.apiClient = {
    get: function (path, options) {
        return request(path, __assign(__assign({}, options), { method: "GET" }));
    },
    post: function (path, json, options) {
        return request(path, __assign(__assign({}, options), { method: "POST", json: json }));
    },
    patch: function (path, json, options) {
        return request(path, __assign(__assign({}, options), { method: "PATCH", json: json }));
    },
    delete: function (path, options) {
        return request(path, __assign(__assign({}, options), { method: "DELETE" }));
    },
    put: function (path, json, options) {
        return request(path, __assign(__assign({}, options), { method: "PUT", json: json }));
    },
};
