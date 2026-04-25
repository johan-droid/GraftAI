"""Data minimization engine for GDPR Article 5.1.c compliance."""

import logging
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DataMinimizationEngine:
    """GDPR Article 5.1.c - Data Minimization enforcement."""

    # Define minimum required fields per feature
    REQUIRED_FIELDS = {
        "authentication": {
            "email",
            "hashed_password",
        },
        "scheduling": {
            "email",
            "timezone",
            "availability",
        },
        "ai_copilot": {
            "email",
            "calendar_data",
            "preferences",
        },
        "notifications": {
            "email",
        },
        "booking": {
            "email",
            "event_type_id",
            "start_time",
        },
    }

    # Fields that should never be collected (special category data)
    PROHIBITED_FIELDS = {
        "religion",
        "political_opinion",
        "ethnic_origin",
        "health_data",
        "biometric_data",
        "sexual_orientation",
        "ssn",
        "national_id",
        "financial_data",
        "criminal_record",
    }

    # Fields that are allowed but require explicit consent
    CONSENT_REQUIRED_FIELDS = {
        "marketing_consent",
        "analytics_consent",
        "ai_training_consent",
        "third_party_sharing_consent",
    }

    @staticmethod
    def validate_data_collection(
        feature: str,
        data: Dict[str, any],
        user_consent: Optional[Dict[str, bool]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate that only necessary data is collected.

        Args:
            feature: The feature/operation collecting data
            data: The data being collected
            user_consent: User's consent preferences

        Returns:
            Tuple of (is_valid, list of issues)
        """
        collected_fields = set(data.keys())
        required = DataMinimizationEngine.REQUIRED_FIELDS.get(feature, set())
        prohibited = DataMinimizationEngine.PROHIBITED_FIELDS
        consent_required = DataMinimizationEngine.CONSENT_REQUIRED_FIELDS

        issues = []

        # Check for prohibited data
        prohibited_found = collected_fields & prohibited
        if prohibited_found:
            issues.append(
                f"Prohibited fields collected: {prohibited_found}. These are special category data."
            )

        # Check for fields requiring consent
        consent_needed = collected_fields & consent_required
        if consent_needed and user_consent:
            for field in consent_needed:
                consent_key = field.replace("_consent", "")
                if not user_consent.get(consent_key, False):
                    issues.append(f"Field {field} requires consent but not granted")
        elif consent_needed:
            issues.append(
                f"Fields requiring consent without consent check: {consent_needed}"
            )

        # Check for excessive data (fields beyond what's necessary)
        # Allow common metadata fields
        metadata_fields = {"created_at", "updated_at", "id", "user_id"}
        excessive = (
            collected_fields
            - required
            - metadata_fields
            - prohibited
            - consent_required
        )
        if excessive:
            issues.append(
                f"Potentially excessive data: {excessive}. "
                f"Justification required. Required for {feature}: {required}"
            )

        # Check for missing required fields
        missing_required = required - collected_fields
        if missing_required:
            issues.append(f"Missing required fields for {feature}: {missing_required}")

        return len(issues) == 0, issues

    @staticmethod
    def anonymize_unnecessary_data(
        user_data: Dict[str, any],
        feature: str,
        keep_fields: Optional[Set[str]] = None,
    ) -> Dict[str, any]:
        """
        Remove or anonymize data not required for current processing.

        Args:
            user_data: The full user data
            feature: The feature being used
            keep_fields: Additional fields to keep beyond requirements

        Returns:
            Minimized data dictionary
        """
        required = DataMinimizationEngine.REQUIRED_FIELDS.get(feature, set())

        if keep_fields:
            required = required | keep_fields

        # Always keep ID for reference
        required.add("id")
        required.add("user_id")

        minimized = {}
        for field, value in user_data.items():
            if field in required:
                minimized[field] = value
            elif field in DataMinimizationEngine.PROHIBITED_FIELDS:
                # Redact prohibited fields
                minimized[field] = "[REDACTED]"
            else:
                # Anonymize other non-required fields
                if isinstance(value, str):
                    minimized[field] = f"[ANONYMIZED: {len(value)} chars]"
                else:
                    minimized[field] = "[ANONYMIZED]"

        return minimized

    @staticmethod
    def mask_pii(data: Dict[str, any], fields_to_mask: Set[str]) -> Dict[str, any]:
        """
        Mask specific PII fields for logging/analytics.

        Args:
            data: The data containing PII
            fields_to_mask: Fields to mask

        Returns:
            Data with masked PII
        """
        masked = data.copy()

        for field in fields_to_mask:
            if field in masked:
                value = masked[field]
                if isinstance(value, str):
                    # Keep first and last character, mask rest
                    if len(value) <= 2:
                        masked[field] = "***"
                    else:
                        masked[field] = value[0] + "*" * (len(value) - 2) + value[-1]
                else:
                    masked[field] = "[MASKED]"

        return masked

    @staticmethod
    def get_data_collection_audit_report(
        feature: str,
        data: Dict[str, any],
        user_consent: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, any]:
        """
        Generate an audit report for data collection.

        Args:
            feature: The feature collecting data
            data: The data being collected
            user_consent: User consent preferences

        Returns:
            Audit report
        """
        is_valid, issues = DataMinimizationEngine.validate_data_collection(
            feature, data, user_consent
        )

        collected_fields = set(data.keys())
        required = DataMinimizationEngine.REQUIRED_FIELDS.get(feature, set())

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feature": feature,
            "is_valid": is_valid,
            "issues": issues,
            "collected_fields": list(collected_fields),
            "required_fields": list(required),
            "excessive_fields": list(collected_fields - required),
            "prohibited_fields": list(
                collected_fields & DataMinimizationEngine.PROHIBITED_FIELDS
            ),
            "consent_required_fields": list(
                collected_fields & DataMinimizationEngine.CONSENT_REQUIRED_FIELDS
            ),
        }


# Global data minimization engine instance
data_minimization = DataMinimizationEngine()
