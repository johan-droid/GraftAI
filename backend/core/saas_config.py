from enum import Enum
from typing import Dict, Any, List

class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ELITE = "elite"
    ENTERPRISE = "enterprise"

class Feature(str, Enum):
    AI_COPILOT = "ai_copilot"
    CALENDAR_SYNC = "calendar_sync"
    TEAM_MANAGEMENT = "team_management"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_BRANDING = "custom_branding"
    API_ACCESS = "api_access"

# Declarative Tier Limits and Feature Gating
TIER_CONFIG: Dict[Tier, Dict[str, Any]] = {
    Tier.FREE: {
        "display_name": "Free Plan",
        "limits": {
            "daily_ai_messages": 10,
            "daily_calendar_syncs": 3,
            "max_teams": 0,
            "max_team_members": 1,
        },
        "features": [
            Feature.AI_COPILOT,
            Feature.CALENDAR_SYNC,
        ]
    },
    Tier.PRO: {
        "display_name": "Professional Plan",
        "limits": {
            "daily_ai_messages": 200,
            "daily_calendar_syncs": 50,
            "max_teams": 3,
            "max_team_members": 10,
        },
        "features": [
            Feature.AI_COPILOT,
            Feature.CALENDAR_SYNC,
            Feature.TEAM_MANAGEMENT,
            Feature.ADVANCED_ANALYTICS,
        ]
    },
    Tier.ELITE: {
        "display_name": "Elite Plan",
        "limits": {
            "daily_ai_messages": 2000,
            "daily_calendar_syncs": 500,
            "max_teams": 10,
            "max_team_members": 50,
        },
        "features": [
            Feature.AI_COPILOT,
            Feature.CALENDAR_SYNC,
            Feature.TEAM_MANAGEMENT,
            Feature.ADVANCED_ANALYTICS,
            Feature.API_ACCESS,
        ]
    },
    Tier.ENTERPRISE: {
        "display_name": "Enterprise Plan",
        "limits": {
            "daily_ai_messages": 1000000, # Virtually unlimited
            "daily_calendar_syncs": 1000000,
            "max_teams": 1000,
            "max_team_members": 1000,
        },
        "features": [f for f in Feature] # All features
    }
}

def get_tier_config(tier_name: str) -> Dict[str, Any]:
    try:
        tier = Tier(tier_name.lower())
    except ValueError:
        tier = Tier.FREE
    return TIER_CONFIG[tier]

def has_feature(tier_name: str, feature: Feature) -> bool:
    config = get_tier_config(tier_name)
    return feature in config["features"]

def get_limit(tier_name: str, limit_key: str) -> int:
    config = get_tier_config(tier_name)
    return config["limits"].get(limit_key, 0)
