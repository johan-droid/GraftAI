"use client";
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
exports.AuthProvider = AuthProvider;
exports.useAuthContext = useAuthContext;
var React = require("react");
var react_1 = require("react");
var auth_client_1 = require("@/lib/auth-client");
var api_1 = require("@/lib/api");
var AuthContext = (0, react_1.createContext)(undefined);
function AuthProvider(_a) {
    var _this = this;
    var children = _a.children;
    var _b = React.useState(null), session = _b[0], setSession = _b[1];
    var _c = React.useState(true), loading = _c[0], setLoading = _c[1];
    var isLikelyNetworkError = React.useCallback(function (error) {
        var _a;
        if (!error || typeof error !== "object")
            return false;
        var maybeMessage = "message" in error ? String((_a = error.message) !== null && _a !== void 0 ? _a : "") : "";
        var msg = maybeMessage.toLowerCase();
        return msg.includes("network") || msg.includes("failed to fetch") || msg.includes("fetch") || msg.includes("timeout");
    }, []);
    var isProtectedPath = React.useCallback(function (pathname) {
        return pathname.startsWith("/dashboard");
    }, []);
    var redirectToLogin = React.useCallback(function () {
        if (typeof window !== "undefined" && window.location.pathname !== "/login") {
            window.location.replace("/login");
        }
    }, []);
    React.useEffect(function () {
        var active = true;
        function loadSession() {
            return __awaiter(this, void 0, void 0, function () {
                var response, err_1;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            setLoading(true);
                            _a.label = 1;
                        case 1:
                            _a.trys.push([1, 3, 4, 5]);
                            return [4 /*yield*/, (0, auth_client_1.getSessionSafe)()];
                        case 2:
                            response = _a.sent();
                            if (!active)
                                return [2 /*return*/];
                            if (response === null || response === void 0 ? void 0 : response.data) {
                                setSession(response.data);
                            }
                            else if (response === null || response === void 0 ? void 0 : response.error) {
                                if (isLikelyNetworkError(response.error)) {
                                    console.debug("Session check encountered a network glitch; retrying without kicking user out.");
                                }
                                else {
                                    setSession(null);
                                }
                            }
                            else {
                                setSession(null);
                            }
                            return [3 /*break*/, 5];
                        case 3:
                            err_1 = _a.sent();
                            console.error("Session load failure", err_1);
                            setSession(null);
                            return [3 /*break*/, 5];
                        case 4:
                            if (active)
                                setLoading(false);
                            return [7 /*endfinally*/];
                        case 5: return [2 /*return*/];
                    }
                });
            });
        }
        loadSession();
        var interval = setInterval(loadSession, 60000);
        return function () {
            active = false;
            clearInterval(interval);
        };
    }, [isLikelyNetworkError]);
    React.useEffect(function () {
        // If not loading and no session user, check for redirection
        if (!loading && !(session === null || session === void 0 ? void 0 : session.user)) {
            var oauthInProgress = typeof window !== "undefined" && sessionStorage.getItem("oauth_in_progress") === "true";
            var currentPath = typeof window !== "undefined" ? window.location.pathname : "";
            // If we're on a protected route and not in an auth flow/login page
            if (isProtectedPath(currentPath) && !oauthInProgress && currentPath !== "/login" && !currentPath.includes("/auth-callback")) {
                console.debug("[AUTH]: Unauthenticated access to protected route, redirecting...");
                redirectToLogin();
            }
        }
    }, [session, loading, redirectToLogin, isProtectedPath]);
    React.useEffect(function () {
        if (typeof window === "undefined" || !("serviceWorker" in navigator))
            return;
        window.addEventListener("load", function () { return __awaiter(_this, void 0, void 0, function () {
            var registration, error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 2, , 3]);
                        return [4 /*yield*/, navigator.serviceWorker.register("/sw.js")];
                    case 1:
                        registration = _a.sent();
                        console.log("Service Worker registration successful with scope:", registration.scope);
                        return [3 /*break*/, 3];
                    case 2:
                        error_1 = _a.sent();
                        console.warn("Service Worker registration failed:", error_1);
                        return [3 /*break*/, 3];
                    case 3: return [2 /*return*/];
                }
            });
        }); });
        return function () {
            window.removeEventListener("load", function () { });
        };
    }, []);
    var user = session === null || session === void 0 ? void 0 : session.user;
    var isAuthenticated = !!session;
    var refreshFn = function () { return __awaiter(_this, void 0, void 0, function () {
        var sessionResult;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, (0, auth_client_1.getSessionSafe)()];
                case 1:
                    sessionResult = _a.sent();
                    if (sessionResult === null || sessionResult === void 0 ? void 0 : sessionResult.data) {
                        setSession(sessionResult.data);
                    }
                    else {
                        setSession(null);
                    }
                    return [2 /*return*/];
            }
        });
    }); };
    /**
     * FIX BUG-021: loginFn now invalidates the apiFetch session token cache
     * so the next API call immediately uses the newly-acquired token, and
     * refreshes the React session state from Better Auth.
     */
    var loginFn = function (token) { return __awaiter(_this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    (0, api_1.invalidateSessionCache)();
                    if (typeof window !== "undefined") {
                        sessionStorage.removeItem("oauth_in_progress");
                        sessionStorage.removeItem("oauth_redirect_to");
                    }
                    return [4 /*yield*/, refreshFn()];
                case 1:
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); };
    var logoutFn = function () { return __awaiter(_this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, (0, auth_client_1.signOut)()];
                case 1:
                    _a.sent();
                    setSession(null);
                    redirectToLogin();
                    return [2 /*return*/];
            }
        });
    }); };
    return (<AuthContext.Provider value={{
            user: user,
            isAuthenticated: isAuthenticated,
            loading: loading,
            login: loginFn,
            refresh: refreshFn,
            logout: logoutFn
        }}>
      {children}
    </AuthContext.Provider>);
}
function useAuthContext() {
    var context = (0, react_1.useContext)(AuthContext);
    if (!context) {
        throw new Error("useAuthContext must be used within AuthProvider");
    }
    return context;
}
