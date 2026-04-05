"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.signUp = exports.signIn = exports.signOut = exports.getSessionSafe = void 0;
exports.getToken = getToken;
exports.getAuthToken = getAuthToken;
exports.invalidateSessionCache = invalidateSessionCache;
exports.getCsrfHeaders = getCsrfHeaders;
function getApiBaseUrl() {
    if (typeof window !== "undefined") {
        // Force relative paths in browser so calls go through frontend origin/proxy.
        return "";
    }
    var envUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
    if (envUrl) {
        return envUrl.replace(/\/+$/g, "");
    }
    return "http://localhost:8000";
}
var API_BASE_URL = getApiBaseUrl();
function authEndpoint(path) {
    var cleanedPath = "/".concat(path.replace(/^\/+/, ""));
    var fullPath = cleanedPath.startsWith("/api/v1") ? cleanedPath : "/api/v1".concat(cleanedPath);
    return API_BASE_URL ? "".concat(API_BASE_URL).concat(fullPath) : fullPath;
}
function parseError(res) {
    return __awaiter(this, void 0, void 0, function () {
        var raw, data;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, res.text().catch(function () { return ""; })];
                case 1:
                    raw = _a.sent();
                    if (!raw)
                        return [2 /*return*/, { message: "Request failed with ".concat(res.status) }];
                    try {
                        data = JSON.parse(raw);
                        return [2 /*return*/, { message: data.detail || data.error || data.message || raw }];
                    }
                    catch (_b) {
                        return [2 /*return*/, { message: raw }];
                    }
                    return [2 /*return*/];
            }
        });
    });
}
var _cachedToken = null;
var _cacheExpiry = 0;
var SESSION_CACHE_TTL_MS = 30000;
function getToken() {
    var _a;
    if (typeof document === "undefined")
        return null;
    var value = "; ".concat(document.cookie);
    var parts = value.split("; graftai_access_token=");
    var token = parts.length === 2
        ? ((_a = parts.pop()) === null || _a === void 0 ? void 0 : _a.split(";").shift()) || null
        : null;

    // 2. Try sessionStorage
    if (!token) {
        try {
            if (typeof window !== "undefined" && window.sessionStorage) {
                token = window.sessionStorage.getItem("graftai_access_token");
            }
        }
        catch (_b) {
            // ignore
        }
    }

    // 3. Try localStorage
    if (!token) {
        try {
            if (typeof window !== "undefined" && window.localStorage) {
                token = window.localStorage.getItem("graftai_access_token");
            }
        }
        catch (_c) {
            // ignore
        }
    }

    // 4. Try one-time URL token bridge params
    if (!token && typeof window !== "undefined") {
        try {
            var params = new URLSearchParams(window.location.search);
            token = params.get("token") || params.get("access_token") || null;
            if (token) {
                if (window.sessionStorage) {
                    window.sessionStorage.setItem("graftai_access_token", token);
                }
                if (window.localStorage) {
                    window.localStorage.setItem("graftai_access_token", token);
                }
            }
        }
        catch (_d) {
            // ignore malformed URL/search params
        }
    }

    // Keep sources in sync for resiliency
    if (token && typeof window !== "undefined") {
        try {
            if (window.sessionStorage && !window.sessionStorage.getItem("graftai_access_token")) {
                window.sessionStorage.setItem("graftai_access_token", token);
            }
            if (window.localStorage && !window.localStorage.getItem("graftai_access_token")) {
                window.localStorage.setItem("graftai_access_token", token);
            }
        }
        catch (_e) {
            // ignore storage access errors
        }
    }

    return token;
}
function getAuthToken() {
    return __awaiter(this, void 0, void 0, function () {
        var now, token, session, serverToken, _a;
        var _b, _c, _d;
        return __generator(this, function (_e) {
            switch (_e.label) {
                case 0:
                    now = Date.now();
                    if (_cachedToken && now < _cacheExpiry) {
                        return [2 /*return*/, _cachedToken];
                    }
                    _e.label = 1;
                case 1:
                    _e.trys.push([1, 4, , 5]);
                    token = getToken();
                    if (token) {
                        return [2 /*return*/, token];
                    }
                    return [4 /*yield*/, getSessionSafe()];
                case 2:
                    session = _e.sent();
                    serverToken = (_d = (_c = (_b = session === null || session === void 0 ? void 0 : session.data) === null || _b === void 0 ? void 0 : _b.session) === null || _c === void 0 ? void 0 : _c.token) !== null && _d !== void 0 ? _d : null;
                    _cachedToken = serverToken;
                    _cacheExpiry = now + SESSION_CACHE_TTL_MS;
                    return [2 /*return*/, serverToken];
                case 3:
                    return [3 /*break*/, 5];
                case 4:
                    _a = _e.sent();
                    return [2 /*return*/, null];
                case 5: return [2 /*return*/];
            }
        });
    });
}
function invalidateSessionCache() {
    _cachedToken = null;
    _cacheExpiry = 0;
    if (typeof window !== "undefined") {
        try {
            sessionStorage.removeItem("graftai_access_token");
            localStorage.removeItem("graftai_access_token");
            document.cookie = "graftai_access_token=; path=/; max-age=0;";
        }
        catch (_a) {
            // ignore
        }
    }
}
function getCsrfHeaders() {
    var _a;
    if (typeof document === "undefined")
        return {};
    var value = "; ".concat(document.cookie);
    var parts = value.split("; xsrf-token=");
    var token = parts.length === 2 ? ((_a = parts.pop()) === null || _a === void 0 ? void 0 : _a.split(";").shift()) || null : null;
    if (!token)
        return {};
    // Keep compatibility with both header casings in backend and proxies.
    return {
        "X-XSRF-TOKEN": token,
        "x-xsrf-token": token,
    };
}
function tryRefreshSession() {
    return __awaiter(this, void 0, void 0, function () {
        var res;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, fetch(authEndpoint("/auth/refresh"), {
                            method: "POST",
                            credentials: "include",
                            headers: {
                                Accept: "application/json",
                            },
                        })];
                case 1:
                    res = _a.sent();
                    return [2 /*return*/, res.ok];
                case 2:
                    _a.sent();
                    return [2 /*return*/, false];
                case 3: return [2 /*return*/];
            }
        });
    });
}
var getSessionSafe = function (allowRefreshRetry) {
    if (allowRefreshRetry === void 0) { allowRefreshRetry = true; }
    return __awaiter(void 0, void 0, void 0, function () {
        var headers, token, res, refreshed, err, data, err_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 7, , 8]);
                    headers = {
                        Accept: "application/json",
                    };
                    token = getToken();
                    if (token) {
                        headers.Authorization = "Bearer ".concat(token);
                        headers["X-Authorization"] = "Bearer ".concat(token);
                    }
                    return [4 /*yield*/, fetch(authEndpoint("/auth/check"), {
                            method: "GET",
                            credentials: "include",
                            headers: headers,
                        })];
                case 1:
                    res = _a.sent();
                    if (!!res.ok) return [3 /*break*/, 5];
                    if (!(res.status === 401)) return [3 /*break*/, 3];
                    if (!allowRefreshRetry) return [3 /*break*/, 3];
                    return [4 /*yield*/, tryRefreshSession()];
                case 2:
                    refreshed = _a.sent();
                    if (refreshed) {
                        return [2 /*return*/, getSessionSafe(false)];
                    }
                    _a.label = 3;
                case 3:
                    if (res.status === 401) {
                        console.warn("[AUTH_CLIENT]: 401 Unauthorized from backend. Clearing local session state.");
                        invalidateSessionCache();
                    }
                    return [4 /*yield*/, parseError(res)];
                case 4:
                    err = _a.sent();
                    return [2 /*return*/, { data: null, error: err }];
                case 5: return [4 /*yield*/, res.json()];
                case 6:
                    data = _a.sent();
                    if (!(data === null || data === void 0 ? void 0 : data.authenticated)) {
                        return [2 /*return*/, { data: null, error: { message: "Session not authenticated" } }];
                    }
                    return [2 /*return*/, { data: data, error: null }];
                case 7:
                    err_1 = _a.sent();
                    console.error("[AUTH_CLIENT]: Unexpected session fetch error:", err_1);
                    return [2 /*return*/, {
                            data: null,
                            error: { message: err_1 instanceof Error ? err_1.message : "Failed to fetch session" },
                        }];
                case 8: return [2 /*return*/];
            }
        });
    });
};
exports.getSessionSafe = getSessionSafe;
var signOut = function () { return __awaiter(void 0, void 0, void 0, function () {
    var res, error, err_2;
    var _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 5, , 6]);
                return [4 /*yield*/, fetch(authEndpoint("/auth/logout"), {
                        method: "POST",
                        credentials: "include",
                        headers: {
                            Accept: "application/json",
                        },
                    })];
            case 1:
                res = _b.sent();
                if (!!res.ok) return [3 /*break*/, 3];
                return [4 /*yield*/, parseError(res)];
            case 2:
                error = _b.sent();
                return [2 /*return*/, { data: null, error: error }];
            case 3:
                invalidateSessionCache();
                _a = {};
                return [4 /*yield*/, res.json().catch(function () { return ({ success: true }); })];
            case 4: return [2 /*return*/, (_a.data = _b.sent(), _a.error = null, _a)];
            case 5:
                err_2 = _b.sent();
                console.error("[AUTH_CLIENT]: Sign-out error:", err_2);
                return [2 /*return*/, {
                        data: null,
                        error: { message: err_2 instanceof Error ? err_2.message : "Logout failed" },
                    }];
            case 6: return [2 /*return*/];
        }
    });
}); };
exports.signOut = signOut;
exports.signIn = {
    email: function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var body, res, error, data, err_3;
        var email = _b.email, password = _b.password;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    _c.trys.push([0, 5, , 6]);
                    body = new URLSearchParams();
                    body.set("username", email);
                    body.set("password", password);
                    body.set("grant_type", "password");
                    return [4 /*yield*/, fetch(authEndpoint("/auth/token"), {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/x-www-form-urlencoded",
                                Accept: "application/json",
                            },
                            body: body,
                            credentials: "include",
                        })];
                case 1:
                    res = _c.sent();
                    if (!!res.ok) return [3 /*break*/, 3];
                    return [4 /*yield*/, parseError(res)];
                case 2:
                    error = _c.sent();
                    return [2 /*return*/, { data: null, error: error }];
                case 3: return [4 /*yield*/, res.json().catch(function () { return ({ success: true }); })];
                case 4:
                    data = _c.sent();
                    return [2 /*return*/, { data: data, error: null }];
                case 5:
                    err_3 = _c.sent();
                    return [2 /*return*/, {
                            data: null,
                            error: { message: err_3 instanceof Error ? err_3.message : "Login failed" },
                        }];
                case 6: return [2 /*return*/];
            }
        });
    }); },
    social: function (provider) { return __awaiter(void 0, void 0, void 0, function () {
        var baseUrl, url;
        return __generator(this, function (_a) {
            if (typeof window === "undefined") {
                return [2 /*return*/, { data: null, error: { message: "Client-side only operation" } }];
            }
            try {
                baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || window.location.origin;
                url = new URL("/api/v1/auth/sso/start", baseUrl);
                url.searchParams.set("provider", provider);
                url.searchParams.set("redirect_to", "/dashboard");
                // Redirect the entire page to the backend to start the OAuth handshake
                window.location.assign(url.toString());
                return [2 /*return*/, { data: { redirecting: true }, error: null }];
            }
            catch (err) {
                return [2 /*return*/, {
                        data: null,
                        error: { message: err instanceof Error ? err.message : "Failed to initiate social login" },
                    }];
            }
            return [2 /*return*/];
        });
    }); },
    magicLink: function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var url, fetchUrl, res, error, err_4;
        var _c;
        var email = _b.email;
        return __generator(this, function (_d) {
            switch (_d.label) {
                case 0:
                    _d.trys.push([0, 5, , 6]);
                    url = new URL(authEndpoint("/auth/passwordless/request"), typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
                    url.searchParams.set("email", email);
                    fetchUrl = API_BASE_URL ? url.toString() : "".concat(url.pathname).concat(url.search);
                    return [4 /*yield*/, fetch(fetchUrl, {
                            method: "POST",
                            credentials: "include",
                            headers: {
                                Accept: "application/json",
                            },
                        })];
                case 1:
                    res = _d.sent();
                    if (!!res.ok) return [3 /*break*/, 3];
                    return [4 /*yield*/, parseError(res)];
                case 2:
                    error = _d.sent();
                    return [2 /*return*/, { data: null, error: error }];
                case 3:
                    _c = {};
                    return [4 /*yield*/, res.json().catch(function () { return ({ success: true }); })];
                case 4: return [2 /*return*/, (_c.data = _d.sent(), _c.error = null, _c)];
                case 5:
                    err_4 = _d.sent();
                    return [2 /*return*/, {
                            data: null,
                            error: { message: err_4 instanceof Error ? err_4.message : "Magic link request failed" },
                        }];
                case 6: return [2 /*return*/];
            }
        });
    }); },
    zoom: function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, {
                    data: null,
                    error: { message: "Zoom OAuth is disabled in simplified auth mode." },
                }];
        });
    }); },
    sso: function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, {
                    data: null,
                    error: { message: "SSO is disabled in simplified auth mode." },
                }];
        });
    }); },
    passkey: function () { return __awaiter(void 0, void 0, void 0, function () {
        return __generator(this, function (_a) {
            return [2 /*return*/, {
                    data: null,
                    error: { message: "Passkey sign-in is not available." },
                }];
        });
    }); },
};
var signUp = function (email, password, name, timezone) { return __awaiter(void 0, void 0, void 0, function () {
    var res, error, err_5;
    var _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 5, , 6]);
                return [4 /*yield*/, fetch(authEndpoint("/auth/register"), {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Accept: "application/json",
                        },
                        body: JSON.stringify({
                            email: email,
                            password: password,
                            full_name: name,
                            timezone: timezone,
                        }),
                        credentials: "include",
                    })];
            case 1:
                res = _b.sent();
                if (!!res.ok) return [3 /*break*/, 3];
                return [4 /*yield*/, parseError(res)];
            case 2:
                error = _b.sent();
                return [2 /*return*/, { data: null, error: error }];
            case 3:
                _a = {};
                return [4 /*yield*/, res.json().catch(function () { return ({ success: true }); })];
            case 4: return [2 /*return*/, (_a.data = _b.sent(), _a.error = null, _a)];
            case 5:
                err_5 = _b.sent();
                return [2 /*return*/, {
                        data: null,
                        error: { message: err_5 instanceof Error ? err_5.message : "Registration failed" },
                    }];
            case 6: return [2 /*return*/];
        }
    });
}); };
exports.signUp = signUp;
