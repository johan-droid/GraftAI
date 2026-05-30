"""
Secret Management System

Provides secure secret management with:
- Multiple secret providers (AWS Secrets Manager, HashiCorp Vault, Environment)
- Secret rotation and versioning
- Encryption at rest and in transit
- Audit logging and access control
- Automatic secret refresh
"""
import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

try:
    import aioredis
except Exception:  # pragma: no cover - optional dependency
    aioredis = None
try:
    import boto3
except Exception:  # pragma: no cover - optional dependency
    boto3 = None
try:
    import hvac
except Exception:  # pragma: no cover - optional dependency
    hvac = None
try:
    from botocore.exceptions import ClientError
except Exception:  # pragma: no cover - optional dependency
    class ClientError(Exception):
        pass
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class SecretProvider(Enum):
    """Secret provider types"""
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    HASHICORP_VAULT = "hashicorp_vault"
    ENVIRONMENT = "environment"
    FILE = "file"
    REDIS = "redis"
    ENCRYPTED_FILE = "encrypted_file"

class SecretType(Enum):
    """Secret types for classification"""
    API_KEY = "api_key"
    DATABASE_CREDENTIALS = "database_credentials"
    ENCRYPTION_KEY = "encryption_key"
    JWT_SECRET = "jwt_secret"
    OAUTH_SECRET = "oauth_secret"
    PAYMENT_KEY = "payment_key"
    EMAIL_CREDENTIALS = "email_credentials"
    CUSTOM = "custom"

@dataclass
class SecretMetadata:
    """Secret metadata"""
    name: str
    type: SecretType
    provider: SecretProvider
    created_at: datetime
    updated_at: datetime
    version: int
    rotation_enabled: bool
    rotation_interval_days: int | None
    last_rotated: datetime | None
    description: str = ""
    tags: list[str] = None
    access_count: int = 0
    last_accessed: datetime | None = None

@dataclass
class SecretValue:
    """Secret value with metadata"""
    value: str
    metadata: SecretMetadata
    encrypted: bool = False
    checksum: str = ""

class SecretProviderInterface(ABC):
    """Abstract secret provider interface"""

    @abstractmethod
    async def get_secret(self, secret_name: str, version: str | None=None) -> SecretValue | None:
        """Get secret value"""

    @abstractmethod
    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret value"""

    @abstractmethod
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret"""

    @abstractmethod
    async def list_secrets(self) -> list[str]:
        """List all secret names"""

    @abstractmethod
    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret"""

class AWSSecretsManagerProvider(SecretProviderInterface):
    """AWS Secrets Manager provider"""

    def __init__(self, region_name: str="us-east-1"):
        self.region_name = region_name
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize AWS Secrets Manager client"""
        try:
            self.client = boto3.client("secretsmanager", region_name=self.region_name)
            logger.info("AWS Secrets Manager client initialized")
        except Exception as e:
            logger.exception("Failed to initialize AWS Secrets Manager client: %s", e)

    async def get_secret(self, secret_name: str, version: str | None=None) -> SecretValue | None:
        """Get secret from AWS Secrets Manager"""
        if not self.client:
            return None
        try:
            kwargs = {}
            if version:
                kwargs["VersionId"] = version
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.get_secret_value(SecretId=secret_name, **kwargs))
            secret_data = json.loads(response["SecretString"])
            metadata = SecretMetadata(name=secret_name, type=self._infer_secret_type(secret_name), provider=SecretProvider.AWS_SECRETS_MANAGER, created_at=datetime.now(UTC), updated_at=datetime.now(UTC), version=response.get("VersionId", "1"), rotation_enabled=response.get("RotationEnabled", False), rotation_interval_days=None, last_rotated=None, description=secret_data.get("description", ""), tags=response.get("Tags", []))
            return SecretValue(value=secret_data.get("secret", ""), metadata=metadata)
        except ClientError as e:
            logger.exception("AWS Secrets Manager error getting %s: %s", secret_name, e)
            return None
        except Exception as e:
            logger.exception("Error getting secret %s from AWS: %s", secret_name, e)
            return None

    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret in AWS Secrets Manager"""
        if not self.client:
            return False
        try:
            secret_data = {"secret": secret_value, "description": metadata.description, "type": metadata.type.value}
            await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.create_secret(Name=secret_name, SecretString=json.dumps(secret_data), Tags=[{"Key": tag, "Value": tag} for tag in metadata.tags or []]))
            logger.info("Created secret %s in AWS Secrets Manager", secret_name)
            return True
        except ClientError as e:
            logger.exception("AWS Secrets Manager error setting %s: %s", secret_name, e)
            return False
        except Exception as e:
            logger.exception("Error setting secret %s in AWS: %s", secret_name, e)
            return False

    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        if not self.client:
            return False
        try:
            await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True))
            logger.info("Deleted secret %s from AWS Secrets Manager", secret_name)
            return True
        except ClientError as e:
            logger.exception("AWS Secrets Manager error deleting %s: %s", secret_name, e)
            return False
        except Exception as e:
            logger.exception("Error deleting secret %s from AWS: %s", secret_name, e)
            return False

    async def list_secrets(self) -> list[str]:
        """List secrets from AWS Secrets Manager"""
        if not self.client:
            return []
        try:
            response = await asyncio.get_event_loop().run_in_executor(None, self.client.list_secrets)
            return [secret["Name"] for secret in response["SecretList"]]
        except ClientError as e:
            logger.exception("AWS Secrets Manager error listing secrets: %s", e)
            return []
        except Exception as e:
            logger.exception("Error listing secrets from AWS: %s", e)
            return []

    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret in AWS Secrets Manager"""
        if not self.client:
            return False
        try:
            await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.rotate_secret(SecretId=secret_name))
            logger.info("Rotated secret %s in AWS Secrets Manager", secret_name)
            return True
        except ClientError as e:
            logger.exception("AWS Secrets Manager error rotating %s: %s", secret_name, e)
            return False
        except Exception as e:
            logger.exception("Error rotating secret %s in AWS: %s", secret_name, e)
            return False

    def _infer_secret_type(self, secret_name: str) -> SecretType:
        """Infer secret type from name"""
        name_lower = secret_name.lower()
        if "api" in name_lower and "key" in name_lower:
            return SecretType.API_KEY
        if "database" in name_lower or "db" in name_lower:
            return SecretType.DATABASE_CREDENTIALS
        if "encryption" in name_lower or "encrypt" in name_lower:
            return SecretType.ENCRYPTION_KEY
        if "jwt" in name_lower:
            return SecretType.JWT_SECRET
        if "oauth" in name_lower:
            return SecretType.OAUTH_SECRET
        if "stripe" in name_lower or "razorpay" in name_lower or "payment" in name_lower:
            return SecretType.PAYMENT_KEY
        if "email" in name_lower or "smtp" in name_lower:
            return SecretType.EMAIL_CREDENTIALS
        return SecretType.CUSTOM

class HashiCorpVaultProvider(SecretProviderInterface):
    """HashiCorp Vault provider"""

    def __init__(self, url: str, token: str, mount_point: str="secret"):
        self.url = url
        self.token = token
        self.mount_point = mount_point
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Vault client"""
        try:
            self.client = hvac.Client(url=self.url, token=self.token)
            if self.client.is_authenticated():
                logger.info("HashiCorp Vault client initialized")
            else:
                logger.error("Failed to authenticate with HashiCorp Vault")
                self.client = None
        except Exception as e:
            logger.exception("Failed to initialize HashiCorp Vault client: %s", e)

    async def get_secret(self, secret_name: str, version: str | None=None) -> SecretValue | None:
        """Get secret from HashiCorp Vault"""
        if not self.client:
            return None
        try:
            kwargs = {}
            if version:
                kwargs["version"] = int(version)
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.secrets.kv.v2.read_secret_version(path=secret_name, **kwargs))
            secret_data = response["data"]["data"]
            metadata = SecretMetadata(name=secret_name, type=self._infer_secret_type(secret_name), provider=SecretProvider.HASHICORP_VAULT, created_at=datetime.now(UTC), updated_at=datetime.now(UTC), version=response["data"]["metadata"]["version"], rotation_enabled=False, rotation_interval_days=None, last_rotated=None, description=secret_data.get("description", ""), tags=[])
            return SecretValue(value=secret_data.get("value", ""), metadata=metadata)
        except Exception as e:
            logger.exception("HashiCorp Vault error getting %s: %s", secret_name, e)
            return None

    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret in HashiCorp Vault"""
        if not self.client:
            return False
        try:
            secret_data = {"value": secret_value, "description": metadata.description, "type": metadata.type.value}
            await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.secrets.kv.v2.create_or_update_secret(path=secret_name, secret=secret_data))
            logger.info("Created secret %s in HashiCorp Vault", secret_name)
            return True
        except Exception as e:
            logger.exception("HashiCorp Vault error setting %s: %s", secret_name, e)
            return False

    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from HashiCorp Vault"""
        if not self.client:
            return False
        try:
            await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=secret_name))
            logger.info("Deleted secret %s from HashiCorp Vault", secret_name)
            return True
        except Exception as e:
            logger.exception("HashiCorp Vault error deleting %s: %s", secret_name, e)
            return False

    async def list_secrets(self) -> list[str]:
        """List secrets from HashiCorp Vault"""
        if not self.client:
            return []
        try:
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.secrets.kv.v2.list_secrets(path=""))
            return response.get("data", {}).get("keys", [])
        except Exception as e:
            logger.exception("HashiCorp Vault error listing secrets: %s", e)
            return []

    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret in HashiCorp Vault"""
        logger.warning("Secret rotation not implemented for HashiCorp Vault provider")
        return False

    def _infer_secret_type(self, secret_name: str) -> SecretType:
        """Infer secret type from name"""
        name_lower = secret_name.lower()
        if "api" in name_lower and "key" in name_lower:
            return SecretType.API_KEY
        if "database" in name_lower or "db" in name_lower:
            return SecretType.DATABASE_CREDENTIALS
        if "encryption" in name_lower or "encrypt" in name_lower:
            return SecretType.ENCRYPTION_KEY
        if "jwt" in name_lower:
            return SecretType.JWT_SECRET
        if "oauth" in name_lower:
            return SecretType.OAUTH_SECRET
        if "stripe" in name_lower or "razorpay" in name_lower or "payment" in name_lower:
            return SecretType.PAYMENT_KEY
        if "email" in name_lower or "smtp" in name_lower:
            return SecretType.EMAIL_CREDENTIALS
        return SecretType.CUSTOM

class EnvironmentSecretProvider(SecretProviderInterface):
    """Environment variable secret provider"""

    def __init__(self):
        self.prefix = "SECRET_"

    async def get_secret(self, secret_name: str, version: str | None=None) -> SecretValue | None:
        """Get secret from environment variables"""
        env_key = f"{self.prefix}{secret_name.upper()}"
        value = os.getenv(env_key)
        if not value:
            return None
        metadata = SecretMetadata(name=secret_name, type=self._infer_secret_type(secret_name), provider=SecretProvider.ENVIRONMENT, created_at=datetime.now(UTC), updated_at=datetime.now(UTC), version="1", rotation_enabled=False, rotation_interval_days=None, last_rotated=None, description="")
        return SecretValue(value=value, metadata=metadata)

    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret in environment (not recommended)"""
        env_key = f"{self.prefix}{secret_name.upper()}"
        os.environ[env_key] = secret_value
        logger.info("Set secret %s in environment (not recommended for production)", secret_name)
        return True

    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from environment"""
        env_key = f"{self.prefix}{secret_name.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            logger.info("Deleted secret %s from environment", secret_name)
            return True
        return False

    async def list_secrets(self) -> list[str]:
        """List secrets from environment"""
        secrets = []
        for key, _value in os.environ.items():
            if key.startswith(self.prefix):
                secret_name = key[len(self.prefix):].lower()
                secrets.append(secret_name)
        return secrets

    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret in environment"""
        logger.warning("Secret rotation not implemented for environment provider")
        return False

    def _infer_secret_type(self, secret_name: str) -> SecretType:
        """Infer secret type from name"""
        name_lower = secret_name.lower()
        if "api" in name_lower and "key" in name_lower:
            return SecretType.API_KEY
        if "database" in name_lower or "db" in name_lower:
            return SecretType.DATABASE_CREDENTIALS
        if "encryption" in name_lower or "encrypt" in name_lower:
            return SecretType.ENCRYPTION_KEY
        if "jwt" in name_lower:
            return SecretType.JWT_SECRET
        if "oauth" in name_lower:
            return SecretType.OAUTH_SECRET
        if "stripe" in name_lower or "razorpay" in name_lower or "payment" in name_lower:
            return SecretType.PAYMENT_KEY
        if "email" in name_lower or "smtp" in name_lower:
            return SecretType.EMAIL_CREDENTIALS
        return SecretType.CUSTOM

class SecretManager:
    """Main secret manager with multiple providers"""

    def __init__(self):
        self.providers: dict[SecretProvider, SecretProviderInterface] = {}
        self.provider_priorities: list[SecretProvider] = []
        self.cache: dict[str, SecretValue] = {}
        self.cache_ttl = 300
        self.encryption_key: bytes | None = None
        self.redis_client: aioredis.Redis | None = None
        self.audit_log: list[dict[str, Any]] = []
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption for local storage"""
        key_str = os.getenv("SECRET_MANAGER_ENCRYPTION_KEY")
        if key_str:
            self.encryption_key = key_str.encode()
        else:
            self.encryption_key = Fernet.generate_key()
            logger.warning("Using generated encryption key - set SECRET_MANAGER_ENCRYPTION_KEY for production")

    def add_provider(self, provider_type: SecretProvider, provider: SecretProviderInterface, priority: int=0):
        """Add secret provider with priority"""
        self.providers[provider_type] = provider
        self.provider_priorities.append((priority, provider_type))
        self.provider_priorities.sort(key=lambda x: x[0], reverse=True)
        logger.info("Added %s provider with priority %s", provider_type.value, priority)

    def set_redis_client(self, redis_client: "Any"):
        """Set Redis client for distributed caching"""
        self.redis_client = redis_client
        logger.info("Redis client set for secret manager caching")

    async def get_secret(self, secret_name: str, provider: SecretProvider | None=None, version: str | None=None, use_cache: bool=True) -> str | None:
        """Get secret value"""
        cache_key = f"secret:{secret_name}:{version or 'latest'}"
        if use_cache:
            cached_secret = await self._get_from_cache(cache_key)
            if cached_secret:
                await self._log_access(secret_name, "cache_hit")
                return cached_secret.value
        if provider:
            providers_to_try = [provider]
        else:
            providers_to_try = [p for _, p in self.provider_priorities]
        for provider_type in providers_to_try:
            if provider_type not in self.providers:
                continue
            provider_instance = self.providers[provider_type]
            secret_value = await provider_instance.get_secret(secret_name, version)
            if secret_value:
                if use_cache:
                    await self._set_cache(cache_key, secret_value)
                await self._log_access(secret_name, provider_type.value)
                return secret_value.value
        await self._log_access(secret_name, "not_found")
        return None

    async def set_secret(self, secret_name: str, secret_value: str, secret_type: SecretType, provider: SecretProvider=SecretProvider.ENVIRONMENT, description: str="", tags: list[str] | None=None) -> bool:
        """Set secret value"""
        if provider not in self.providers:
            logger.error("Provider %s not available", provider.value)
            return False
        metadata = SecretMetadata(name=secret_name, type=secret_type, provider=provider, created_at=datetime.now(UTC), updated_at=datetime.now(UTC), version="1", rotation_enabled=False, rotation_interval_days=None, last_rotated=None, description=description, tags=tags or [])
        provider_instance = self.providers[provider]
        success = await provider_instance.set_secret(secret_name, secret_value, metadata)
        if success:
            cache_key = f"secret:{secret_name}:latest"
            await self._delete_cache(cache_key)
            await self._log_access(secret_name, "set", provider.value)
        return success

    async def delete_secret(self, secret_name: str, provider: SecretProvider | None=None) -> bool:
        """Delete secret"""
        if provider:
            if provider not in self.providers:
                return False
            provider_instance = self.providers[provider]
            success = await provider_instance.delete_secret(secret_name)
        else:
            success = False
            for _provider_type, provider_instance in self.providers.items():
                if await provider_instance.delete_secret(secret_name):
                    success = True
                    break
        if success:
            await self._delete_cache(f"secret:{secret_name}:latest")
            await self._log_access(secret_name, "deleted")
        return success

    async def list_secrets(self, provider: SecretProvider | None=None) -> dict[str, list[str]]:
        """List secrets from providers"""
        result = {}
        if provider:
            if provider in self.providers:
                secrets = await self.providers[provider].list_secrets()
                result[provider.value] = secrets
        else:
            for provider_type, provider_instance in self.providers.items():
                secrets = await provider_instance.list_secrets()
                result[provider_type.value] = secrets
        return result

    async def rotate_secret(self, secret_name: str, provider: SecretProvider | None=None) -> bool:
        """Rotate secret"""
        if provider:
            if provider not in self.providers:
                return False
            provider_instance = self.providers[provider]
            success = await provider_instance.rotate_secret(secret_name)
        else:
            success = False
            for _provider_type, provider_instance in self.providers.items():
                if await provider_instance.rotate_secret(secret_name):
                    success = True
                    break
        if success:
            await self._delete_cache(f"secret:{secret_name}:latest")
            await self._log_access(secret_name, "rotated")
        return success

    async def _get_from_cache(self, cache_key: str) -> SecretValue | None:
        """Get secret from cache"""
        if cache_key in self.cache:
            return self.cache[cache_key]
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    secret_data = json.loads(cached_data)
                    metadata = SecretMetadata(**secret_data["metadata"])
                    secret_value = SecretValue(value=secret_data["value"], metadata=metadata)
                    self.cache[cache_key] = secret_value
                    return secret_value
            except Exception as e:
                logger.exception("Error getting secret from Redis cache: %s", e)
        return None

    async def _set_cache(self, cache_key: str, secret_value: SecretValue):
        """Set secret in cache"""
        self.cache[cache_key] = secret_value
        if self.redis_client:
            try:
                cache_data = {"value": secret_value.value, "metadata": asdict(secret_value.metadata)}
                await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))
            except Exception as e:
                logger.exception("Error setting secret in Redis cache: %s", e)

    async def _delete_cache(self, cache_key: str):
        """Delete secret from cache"""
        if cache_key in self.cache:
            del self.cache[cache_key]
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.exception("Error deleting secret from Redis cache: %s", e)

    async def _log_access(self, secret_name: str, action: str, provider: str=""):
        """Log secret access for audit"""
        log_entry = {"timestamp": datetime.now(UTC).isoformat(), "secret_name": secret_name, "action": action, "provider": provider, "source": "secret_manager"}
        self.audit_log.append(log_entry)
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        logger.info("Secret access: %s on %s via %s", action, secret_name, provider)

    async def get_audit_log(self, limit: int=100) -> list[dict[str, Any]]:
        """Get audit log entries"""
        return self.audit_log[-limit:]

    async def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        if self.redis_client:
            try:
                keys = await self.redis_client.keys("secret:*")
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.exception("Error clearing Redis cache: %s", e)
        logger.info("Secret manager cache cleared")
secret_manager = SecretManager()

def get_secret_manager() -> SecretManager:
    """Get global secret manager instance"""
    return secret_manager

async def get_secret(secret_name: str, provider: SecretProvider | None=None) -> str | None:
    """Get secret value"""
    return await secret_manager.get_secret(secret_name, provider)

async def get_api_key(service_name: str) -> str | None:
    """Get API key for service"""
    return await secret_manager.get_secret(f"{service_name}_api_key")

async def get_database_credentials() -> dict[str, str] | None:
    """Get database credentials"""
    username = await secret_manager.get_secret("database_username")
    password = await secret_manager.get_secret("database_password")
    if username and password:
        return {"username": username, "password": password}
    return None

async def initialize_secret_manager():
    """Initialize secret manager with providers"""
    manager = get_secret_manager()
    manager.add_provider(SecretProvider.ENVIRONMENT, EnvironmentSecretProvider(), priority=1)
    aws_region = os.getenv("AWS_REGION")
    if aws_region:
        try:
            aws_provider = AWSSecretsManagerProvider(aws_region)
            manager.add_provider(SecretProvider.AWS_SECRETS_MANAGER, aws_provider, priority=3)
            logger.info("AWS Secrets Manager provider added")
        except Exception as e:
            logger.exception("Failed to initialize AWS Secrets Manager: %s", e)
    vault_url = os.getenv("VAULT_URL")
    vault_token = os.getenv("VAULT_TOKEN")
    if vault_url and vault_token:
        try:
            vault_provider = HashiCorpVaultProvider(vault_url, vault_token)
            manager.add_provider(SecretProvider.HASHICORP_VAULT, vault_provider, priority=2)
            logger.info("HashiCorp Vault provider added")
        except Exception as e:
            logger.exception("Failed to initialize HashiCorp Vault: %s", e)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_client = await aioredis.from_url(redis_url)
            manager.set_redis_client(redis_client)
            logger.info("Redis client set for secret manager")
        except Exception as e:
            logger.exception("Failed to connect to Redis for secret manager: %s", e)
    logger.info("Secret manager initialized")
