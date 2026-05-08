#!/usr/bin/env python3
"""
Security audit script for GraftAI backend.
Performs comprehensive security checks on API endpoints and configuration.
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.security_monitoring import SecurityMonitor, SecurityEventType, SecurityEventSeverity
from utils.secure_config import get_secure_config
from utils.rate_limiter import get_rate_limiter
from utils.validation import SecurityValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityAuditor:
    """Comprehensive security auditor for GraftAI backend."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.recommendations = []
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit."""
        logger.info("Starting comprehensive security audit...")
        
        audit_results = {
            "timestamp": "2026-05-08T11:41:00Z",
            "overall_score": 0,
            "categories": {},
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }
        
        # Run audit categories
        categories = [
            ("configuration", self.audit_configuration),
            ("api_endpoints", self.audit_api_endpoints),
            ("dependencies", self.audit_dependencies),
            ("authentication", self.audit_authentication),
            ("data_validation", self.audit_data_validation),
            ("rate_limiting", self.audit_rate_limiting),
            ("monitoring", self.audit_monitoring),
        ]
        
        scores = []
        for category_name, audit_func in categories:
            try:
                logger.info(f"Auditing {category_name}...")
                category_result = await audit_func()
                audit_results["categories"][category_name] = category_result
                scores.append(category_result["score"])
            except Exception as e:
                logger.error(f"Failed to audit {category_name}: {e}")
                audit_results["categories"][category_name] = {"score": 0, "error": str(e)}
                scores.append(0)
        
        # Calculate overall score
        audit_results["overall_score"] = sum(scores) / len(scores) if scores else 0
        
        logger.info(f"Security audit completed. Overall score: {audit_results['overall_score']:.1f}/100")
        
        return audit_results
    
    async def audit_configuration(self) -> Dict[str, Any]:
        """Audit security configuration."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check secure config
            secure_config = get_secure_config()
            config_report = secure_config.get_security_report()
            
            # Check encryption
            if config_report["encryption_enabled"]:
                result["checks"]["encryption"] = {"status": "pass", "points": 20}
            else:
                result["checks"]["encryption"] = {"status": "fail", "points": 0}
                self.issues.append("Configuration encryption not enabled")
            
            # Check required configs
            if config_report["validation"]["valid"]:
                result["checks"]["required_configs"] = {"status": "pass", "points": 20}
            else:
                result["checks"]["required_configs"] = {"status": "fail", "points": 0}
                self.issues.extend(config_report["validation"]["errors"])
            
            # Check for default secrets
            if not config_report["validation"]["missing_secrets"]:
                result["checks"]["default_secrets"] = {"status": "pass", "points": 20}
            else:
                result["checks"]["default_secrets"] = {"status": "fail", "points": 0}
                self.issues.extend([f"Using default secret: {secret}" for secret in config_report["validation"]["missing_secrets"]])
            
            # Check security issues
            if not config_report["security_issues"]:
                result["checks"]["security_issues"] = {"status": "pass", "points": 20}
            else:
                result["checks"]["security_issues"] = {"status": "fail", "points": 0}
                self.issues.extend(config_report["security_issues"])
            
            # Check environment
            env = secure_config.get_config_value("ENV", use_cache=False)
            if env == "production":
                result["checks"]["production_ready"] = {"status": "pass", "points": 20}
            else:
                result["checks"]["production_ready"] = {"status": "warning", "points": 10}
                self.warnings.append("Running in non-production environment")
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"Configuration audit failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def audit_api_endpoints(self) -> Dict[str, Any]:
        """Audit API endpoint security."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check for API files
            api_dir = Path(__file__).parent.parent / "api"
            if not api_dir.exists():
                result["checks"]["api_exists"] = {"status": "fail", "points": 0}
                self.issues.append("API directory not found")
                return result
            
            result["checks"]["api_exists"] = {"status": "pass", "points": 10}
            
            # Check for authentication on sensitive endpoints
            sensitive_endpoints = []
            for api_file in api_dir.rglob("*.py"):
                if api_file.name == "__init__.py":
                    continue
                
                try:
                    content = api_file.read_text()
                    
                    # Check for authentication decorators
                    if any(endpoint in content for endpoint in ["/auth", "/users", "/admin"]):
                        if "auth" not in content.lower() and "login" not in content.lower():
                            sensitive_endpoints.append(str(api_file))
                            
                except Exception:
                    continue
            
            if not sensitive_endpoints:
                result["checks"]["auth_protected"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["auth_protected"] = {"status": "fail", "points": 0}
                self.issues.extend([f"Missing authentication in: {endpoint}" for endpoint in sensitive_endpoints])
            
            # Check for input validation
            validation_files = 0
            for api_file in api_dir.rglob("*.py"):
                try:
                    content = api_file.read_text()
                    if any(pattern in content for pattern in ["validate", "sanitize", "Pydantic", "BaseModel"]):
                        validation_files += 1
                except Exception:
                    continue
            
            total_api_files = len(list(api_dir.rglob("*.py"))) - 1  # Exclude __init__.py
            if validation_files >= total_api_files * 0.8:  # 80% of files have validation
                result["checks"]["input_validation"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["input_validation"] = {"status": "warning", "points": 15}
                self.warnings.append(f"Only {validation_files}/{total_api_files} API files have input validation")
            
            # Check for SQL injection protection
            sql_injection_safe = True
            for api_file in api_dir.rglob("*.py"):
                try:
                    content = api_file.read_text()
                    # Look for raw SQL without parameterization
                    if any(pattern in content for pattern in ["execute(", "query("]) and "%" in content:
                        sql_injection_safe = False
                        break
                except Exception:
                    continue
            
            if sql_injection_safe:
                result["checks"]["sql_injection_protection"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["sql_injection_protection"] = {"status": "fail", "points": 0}
                self.issues.append("Potential SQL injection vulnerability detected")
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"API endpoint audit failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def audit_dependencies(self) -> Dict[str, Any]:
        """Audit dependency security."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check requirements.txt for known vulnerable packages
            requirements_file = Path(__file__).parent.parent / "requirements.txt"
            if not requirements_file.exists():
                result["checks"]["requirements_exists"] = {"status": "fail", "points": 0}
                self.issues.append("requirements.txt not found")
                return result
            
            result["checks"]["requirements_exists"] = {"status": "pass", "points": 20}
            
            content = requirements_file.read_text()
            
            # Check for outdated packages
            outdated_packages = []
            if "fastapi==" in content and not "fastapi>=" in content:
                outdated_packages.append("FastAPI version pinned")
            
            if not outdated_packages:
                result["checks"]["updated_packages"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["updated_packages"] = {"status": "warning", "points": 15}
                self.warnings.extend(outdated_packages)
            
            # Check for security-related packages
            security_packages = ["cryptography", "python-jose", "passlib", "bcrypt"]
            security_count = sum(1 for pkg in security_packages if pkg in content)
            
            if security_count >= 3:
                result["checks"]["security_packages"] = {"status": "pass", "points": 25}
            else:
                result["checks"]["security_packages"] = {"status": "warning", "points": 10}
                self.warnings.append(f"Only {security_count}/4 security packages found")
            
            # Check for development packages in production
            dev_packages = ["pytest", "black", "flake8", "mypy"]
            dev_in_prod = [pkg for pkg in dev_packages if pkg in content]
            
            if not dev_in_prod:
                result["checks"]["no_dev_packages"] = {"status": "pass", "points": 25}
            else:
                result["checks"]["no_dev_packages"] = {"status": "warning", "points": 10}
                self.warnings.extend([f"Development package found: {pkg}" for pkg in dev_in_prod])
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"Dependency audit failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def audit_authentication(self) -> Dict[str, Any]:
        """Audit authentication security."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check auth configuration
            secure_config = get_secure_config()
            
            # Check JWT secrets
            try:
                secret_key = secure_config.get_config_value("SECRET_KEY", use_cache=False)
                if secret_key and len(secret_key) >= 32:
                    result["checks"]["jwt_secret_strength"] = {"status": "pass", "points": 25}
                else:
                    result["checks"]["jwt_secret_strength"] = {"status": "fail", "points": 0}
                    self.issues.append("JWT secret too short or missing")
            except ValueError:
                result["checks"]["jwt_secret_strength"] = {"status": "fail", "points": 0}
                self.issues.append("JWT secret not configured")
            
            # Check token expiration
            try:
                access_token_expire = secure_config.get_config_value("ACCESS_TOKEN_EXPIRE_MINUTES", use_cache=False)
                if access_token_expire and access_token_expire <= 60:  # 1 hour or less
                    result["checks"]["token_expiration"] = {"status": "pass", "points": 25}
                else:
                    result["checks"]["token_expiration"] = {"status": "warning", "points": 12}
                    self.warnings.append("Access token expiration too long")
            except ValueError:
                result["checks"]["token_expiration"] = {"status": "fail", "points": 0}
                self.issues.append("Token expiration not configured")
            
            # Check for OAuth configuration
            oauth_configs = ["GOOGLE_CLIENT_ID", "MICROSOFT_CLIENT_ID"]
            oauth_count = 0
            for config in oauth_configs:
                try:
                    if secure_config.get_config_value(config, use_cache=False):
                        oauth_count += 1
                except ValueError:
                    pass
            
            if oauth_count >= 1:
                result["checks"]["oauth_configured"] = {"status": "pass", "points": 25}
            else:
                result["checks"]["oauth_configured"] = {"status": "warning", "points": 10}
                self.warnings.append("No OAuth providers configured")
            
            # Check for MFA support
            auth_dir = Path(__file__).parent.parent / "auth"
            mfa_enabled = False
            if auth_dir.exists():
                for auth_file in auth_dir.rglob("*.py"):
                    try:
                        content = auth_file.read_text()
                        if "mfa" in content.lower() or "totp" in content.lower():
                            mfa_enabled = True
                            break
                    except Exception:
                        continue
            
            if mfa_enabled:
                result["checks"]["mfa_support"] = {"status": "pass", "points": 25}
            else:
                result["checks"]["mfa_support"] = {"status": "warning", "points": 12}
                self.recommendations.append("Consider implementing MFA/TOTP support")
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"Authentication audit failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def audit_data_validation(self) -> Dict[str, Any]:
        """Audit data validation security."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check validation utilities
            validation_file = Path(__file__).parent.parent / "utils" / "validation.py"
            if validation_file.exists():
                result["checks"]["validation_utils"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["validation_utils"] = {"status": "fail", "points": 0}
                self.issues.append("Validation utilities not found")
            
            # Check for XSS protection patterns
            validation_content = validation_file.read_text() if validation_file.exists() else ""
            xss_patterns = ["xss", "script", "javascript:", "html.escape"]
            xss_protection = any(pattern in validation_content.lower() for pattern in xss_patterns)
            
            if xss_protection:
                result["checks"]["xss_protection"] = {"status": "pass", "points": 35}
            else:
                result["checks"]["xss_protection"] = {"status": "fail", "points": 0}
                self.issues.append("XSS protection not implemented")
            
            # Check for SQL injection protection
            sql_patterns = ["sql", "injection", "sanitize", "validate"]
            sql_protection = any(pattern in validation_content.lower() for pattern in sql_patterns)
            
            if sql_protection:
                result["checks"]["sql_injection_protection"] = {"status": "pass", "points": 35}
            else:
                result["checks"]["sql_injection_protection"] = {"status": "fail", "points": 0}
                self.issues.append("SQL injection protection not implemented")
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"Data validation audit failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def audit_rate_limiting(self) -> Dict[str, Any]:
        """Audit rate limiting configuration."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check rate limiter
            rate_limiter = get_rate_limiter()
            
            if rate_limiter.redis:
                result["checks"]["redis_rate_limiting"] = {"status": "pass", "points": 40}
            else:
                result["checks"]["redis_rate_limiting"] = {"status": "warning", "points": 20}
                self.warnings.append("Rate limiting using in-memory fallback")
            
            # Check endpoint-specific limits
            if rate_limiter.endpoint_limits:
                result["checks"]["endpoint_limits"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["endpoint_limits"] = {"status": "warning", "points": 15}
                self.warnings.append("No endpoint-specific rate limits configured")
            
            # Check strict auth limits
            auth_endpoints = ["/api/v1/auth/login", "/api/v1/auth/register"]
            strict_limits = all(
                endpoint in rate_limiter.endpoint_limits and 
                rate_limiter.endpoint_limits[endpoint]["limit"] <= 10
                for endpoint in auth_endpoints
            )
            
            if strict_limits:
                result["checks"]["auth_rate_limits"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["auth_rate_limits"] = {"status": "warning", "points": 15}
                self.warnings.append("Authentication endpoints have lenient rate limits")
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"Rate limiting audit failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def audit_monitoring(self) -> Dict[str, Any]:
        """Audit security monitoring."""
        result = {"score": 0, "checks": {}}
        
        try:
            # Check security monitor
            monitor = get_security_monitor()
            
            if monitor.redis:
                result["checks"]["redis_monitoring"] = {"status": "pass", "points": 40}
            else:
                result["checks"]["redis_monitoring"] = {"status": "warning", "points": 20}
                self.warnings.append("Security monitoring without Redis persistence")
            
            # Check event types
            event_types = list(SecurityEventType)
            if len(event_types) >= 10:
                result["checks"]["event_types"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["event_types"] = {"status": "warning", "points": 15}
                self.warnings.append("Limited security event types")
            
            # Check thresholds
            if monitor.thresholds:
                result["checks"]["thresholds_configured"] = {"status": "pass", "points": 30}
            else:
                result["checks"]["thresholds_configured"] = {"status": "fail", "points": 0}
                self.issues.append("No security thresholds configured")
            
            # Calculate score
            result["score"] = sum(check.get("points", 0) for check in result["checks"].values())
            
        except Exception as e:
            logger.error(f"Monitoring audit failed: {e}")
            result["error"] = str(e)
        
        return result


async def main():
    """Run security audit and print results."""
    auditor = SecurityAuditor()
    results = await auditor.run_full_audit()
    
    # Print results
    print("\n" + "="*80)
    print("GRAFTAI SECURITY AUDIT REPORT")
    print("="*80)
    print(f"Overall Security Score: {results['overall_score']:.1f}/100")
    print(f"Audit Date: {results['timestamp']}")
    
    print("\nCATEGORY SCORES:")
    for category, data in results["categories"].items():
        score = data.get("score", 0)
        status = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        print(f"  {status} {category.title()}: {score}/100")
    
    if results["issues"]:
        print(f"\n🔴 CRITICAL ISSUES ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"  - {issue}")
    
    if results["warnings"]:
        print(f"\n🟡 WARNINGS ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"  - {warning}")
    
    if results["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS ({len(results['recommendations'])}):")
        for rec in results["recommendations"]:
            print(f"  - {rec}")
    
    # Save detailed report
    report_file = Path(__file__).parent.parent / "security_audit_report.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_file}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
