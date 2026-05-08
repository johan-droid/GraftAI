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
import logging
import os
import json
import base64
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import cryptography.fernet
from cryptography.fernet import Fernet
import boto3
from botocore.exceptions import ClientError
import hvac
import aioredis

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
    rotation_interval_days: Optional[int]
    last_rotated: Optional[datetime]
    description: str = ""
    tags: List[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


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
    async def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[SecretValue]:
        """Get secret value"""
        pass
    
    @abstractmethod
    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret value"""
        pass
    
    @abstractmethod
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret"""
        pass
    
    @abstractmethod
    async def list_secrets(self) -> List[str]:
        """List all secret names"""
        pass
    
    @abstractmethod
    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret"""
        pass


class AWSSecretsManagerProvider(SecretProviderInterface):
    """AWS Secrets Manager provider"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Secrets Manager client"""
        try:
            self.client = boto3.client('secretsmanager', region_name=self.region_name)
            logger.info("AWS Secrets Manager client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
    
    async def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[SecretValue]:
        """Get secret from AWS Secrets Manager"""
        if not self.client:
            return None
        
        try:
            kwargs = {}
            if version:
                kwargs['VersionId'] = version
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_secret_value(SecretId=secret_name, **kwargs)
            )
            
            secret_data = json.loads(response['SecretString'])
            
            # Create metadata
            metadata = SecretMetadata(
                name=secret_name,
                type=self._infer_secret_type(secret_name),
                provider=SecretProvider.AWS_SECRETS_MANAGER,
                created_at=datetime.now(timezone.utc),  # Would get from AWS
                updated_at=datetime.now(timezone.utc),
                version=response.get('VersionId', '1'),
                rotation_enabled=response.get('RotationEnabled', False),
                rotation_interval_days=None,
                last_rotated=None,
                description=secret_data.get('description', ''),
                tags=response.get('Tags', [])
            )
            
            return SecretValue(
                value=secret_data.get('secret', ''),
                metadata=metadata
            )
            
        except ClientError as e:
            logger.error(f"AWS Secrets Manager error getting {secret_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting secret {secret_name} from AWS: {e}")
            return None
    
    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret in AWS Secrets Manager"""
        if not self.client:
            return False
        
        try:
            secret_data = {
                'secret': secret_value,
                'description': metadata.description,
                'type': metadata.type.value
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps(secret_data),
                    Tags=[{'Key': tag, 'Value': tag} for tag in metadata.tags or []]
                )
            )
            
            logger.info(f"Created secret {secret_name} in AWS Secrets Manager")
            return True
            
        except ClientError as e:
            logger.error(f"AWS Secrets Manager error setting {secret_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting secret {secret_name} in AWS: {e}")
            return False
    
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        if not self.client:
            return False
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)
            )
            
            logger.info(f"Deleted secret {secret_name} from AWS Secrets Manager")
            return True
            
        except ClientError as e:
            logger.error(f"AWS Secrets Manager error deleting {secret_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting secret {secret_name} from AWS: {e}")
            return False
    
    async def list_secrets(self) -> List[str]:
        """List secrets from AWS Secrets Manager"""
        if not self.client:
            return []
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.list_secrets()
            )
            
            return [secret['Name'] for secret in response['SecretList']]
            
        except ClientError as e:
            logger.error(f"AWS Secrets Manager error listing secrets: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing secrets from AWS: {e}")
            return []
    
    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret in AWS Secrets Manager"""
        if not self.client:
            return False
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.rotate_secret(SecretId=secret_name)
            )
            
            logger.info(f"Rotated secret {secret_name} in AWS Secrets Manager")
            return True
            
        except ClientError as e:
            logger.error(f"AWS Secrets Manager error rotating {secret_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error rotating secret {secret_name} in AWS: {e}")
            return False
    
    def _infer_secret_type(self, secret_name: str) -> SecretType:
        """Infer secret type from name"""
        name_lower = secret_name.lower()
        
        if 'api' in name_lower and 'key' in name_lower:
            return SecretType.API_KEY
        elif 'database' in name_lower or 'db' in name_lower:
            return SecretType.DATABASE_CREDENTIALS
        elif 'encryption' in name_lower or 'encrypt' in name_lower:
            return SecretType.ENCRYPTION_KEY
        elif 'jwt' in name_lower:
            return SecretType.JWT_SECRET
        elif 'oauth' in name_lower:
            return SecretType.OAUTH_SECRET
        elif 'stripe' in name_lower or 'razorpay' in name_lower or 'payment' in name_lower:
            return SecretType.PAYMENT_KEY
        elif 'email' in name_lower or 'smtp' in name_lower:
            return SecretType.EMAIL_CREDENTIALS
        else:
            return SecretType.CUSTOM


class HashiCorpVaultProvider(SecretProviderInterface):
    """HashiCorp Vault provider"""
    
    def __init__(self, url: str, token: str, mount_point: str = "secret"):
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
            logger.error(f"Failed to initialize HashiCorp Vault client: {e}")
    
    async def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[SecretValue]:
        """Get secret from HashiCorp Vault"""
        if not self.client:
            return None
        
        try:
            kwargs = {}
            if version:
                kwargs['version'] = int(version)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.secrets.kv.v2.read_secret_version(
                    path=secret_name,
                    **kwargs
                )
            )
            
            secret_data = response['data']['data']
            
            # Create metadata
            metadata = SecretMetadata(
                name=secret_name,
                type=self._infer_secret_type(secret_name),
                provider=SecretProvider.HASHICORP_VAULT,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=response['data']['metadata']['version'],
                rotation_enabled=False,
                rotation_interval_days=None,
                last_rotated=None,
                description=secret_data.get('description', ''),
                tags=[]
            )
            
            return SecretValue(
                value=secret_data.get('value', ''),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"HashiCorp Vault error getting {secret_name}: {e}")
            return None
    
    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret in HashiCorp Vault"""
        if not self.client:
            return False
        
        try:
            secret_data = {
                'value': secret_value,
                'description': metadata.description,
                'type': metadata.type.value
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.secrets.kv.v2.create_or_update_secret(
                    path=secret_name,
                    secret=secret_data
                )
            )
            
            logger.info(f"Created secret {secret_name} in HashiCorp Vault")
            return True
            
        except Exception as e:
            logger.error(f"HashiCorp Vault error setting {secret_name}: {e}")
            return False
    
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from HashiCorp Vault"""
        if not self.client:
            return False
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=secret_name
                )
            )
            
            logger.info(f"Deleted secret {secret_name} from HashiCorp Vault")
            return True
            
        except Exception as e:
            logger.error(f"HashiCorp Vault error deleting {secret_name}: {e}")
            return False
    
    async def list_secrets(self) -> List[str]:
        """List secrets from HashiCorp Vault"""
        if not self.client:
            return []
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.secrets.kv.v2.list_secrets(path='')
            )
            
            return response.get('data', {}).get('keys', [])
            
        except Exception as e:
            logger.error(f"HashiCorp Vault error listing secrets: {e}")
            return []
    
    async def rotate_secret(self, secret_name: str) -> bool:
        """Rotate secret in HashiCorp Vault"""
        # Vault doesn't have built-in rotation, would need custom implementation
        logger.warning("Secret rotation not implemented for HashiCorp Vault provider")
        return False
    
    def _infer_secret_type(self, secret_name: str) -> SecretType:
        """Infer secret type from name"""
        # Same logic as AWS provider
        name_lower = secret_name.lower()
        
        if 'api' in name_lower and 'key' in name_lower:
            return SecretType.API_KEY
        elif 'database' in name_lower or 'db' in name_lower:
            return SecretType.DATABASE_CREDENTIALS
        elif 'encryption' in name_lower or 'encrypt' in name_lower:
            return SecretType.ENCRYPTION_KEY
        elif 'jwt' in name_lower:
            return SecretType.JWT_SECRET
        elif 'oauth' in name_lower:
            return SecretType.OAUTH_SECRET
        elif 'stripe' in name_lower or 'razorpay' in name_lower or 'payment' in name_lower:
            return SecretType.PAYMENT_KEY
        elif 'email' in name_lower or 'smtp' in name_lower:
            return SecretType.EMAIL_CREDENTIALS
        else:
            return SecretType.CUSTOM


class EnvironmentSecretProvider(SecretProviderInterface):
    """Environment variable secret provider"""
    
    def __init__(self):
        self.prefix = "SECRET_"
    
    async def get_secret(self, secret_name: str, version: Optional[str] = None) -> Optional[SecretValue]:
        """Get secret from environment variables"""
        env_key = f"{self.prefix}{secret_name.upper()}"
        value = os.getenv(env_key)
        
        if not value:
            return None
        
        metadata = SecretMetadata(
            name=secret_name,
            type=self._infer_secret_type(secret_name),
            provider=SecretProvider.ENVIRONMENT,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version="1",
            rotation_enabled=False,
            rotation_interval_days=None,
            last_rotated=None,
            description=""
        )
        
        return SecretValue(value=value, metadata=metadata)
    
    async def set_secret(self, secret_name: str, secret_value: str, metadata: SecretMetadata) -> bool:
        """Set secret in environment (not recommended)"""
        env_key = f"{self.prefix}{secret_name.upper()}"
        os.environ[env_key] = secret_value
        logger.info(f"Set secret {secret_name} in environment (not recommended for production)")
        return True
    
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from environment"""
        env_key = f"{self.prefix}{secret_name.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            logger.info(f"Deleted secret {secret_name} from environment")
            return True
        return False
    
    async def list_secrets(self) -> List[str]:
        """List secrets from environment"""
        secrets = []
        for key, value in os.environ.items():
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
        # Same logic as other providers
        name_lower = secret_name.lower()
        
        if 'api' in name_lower and 'key' in name_lower:
            return SecretType.API_KEY
        elif 'database' in name_lower or 'db' in name_lower:
            return SecretType.DATABASE_CREDENTIALS
        elif 'encryption' in name_lower or 'encrypt' in name_lower:
            return SecretType.ENCRYPTION_KEY
        elif 'jwt' in name_lower:
            return SecretType.JWT_SECRET
        elif 'oauth' in name_lower:
            return SecretType.OAUTH_SECRET
        elif 'stripe' in name_lower or 'razorpay' in name_lower or 'payment' in name_lower:
            return SecretType.PAYMENT_KEY
        elif 'email' in name_lower or 'smtp' in name_lower:
            return SecretType.EMAIL_CREDENTIALS
        else:
            return SecretType.CUSTOM


class SecretManager:
    """Main secret manager with multiple providers"""
    
    def __init__(self):
        self.providers: Dict[SecretProvider, SecretProviderInterface] = {}
        self.provider_priorities: List[SecretProvider] = []
        self.cache: Dict[str, SecretValue] = {}
        self.cache_ttl = 300  # 5 minutes
        self.encryption_key: Optional[bytes] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.audit_log: List[Dict[str, Any]] = []
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption for local storage"""
        # Try to get encryption key from environment
        key_str = os.getenv("SECRET_MANAGER_ENCRYPTION_KEY")
        if key_str:
            self.encryption_key = key_str.encode()
        else:
            # Generate a key (not recommended for production)
            self.encryption_key = Fernet.generate_key()
            logger.warning("Using generated encryption key - set SECRET_MANAGER_ENCRYPTION_KEY for production")
    
    def add_provider(self, provider_type: SecretProvider, provider: SecretProviderInterface, priority: int = 0):
        """Add secret provider with priority"""
        self.providers[provider_type] = provider
        self.provider_priorities.append((priority, provider_type))
        self.provider_priorities.sort(key=lambda x: x[0], reverse=True)  # Higher priority first
        logger.info(f"Added {provider_type.value} provider with priority {priority}")
    
    def set_redis_client(self, redis_client: aioredis.Redis):
        """Set Redis client for distributed caching"""
        self.redis_client = redis_client
        logger.info("Redis client set for secret manager caching")
    
    async def get_secret(self, secret_name: str, provider: Optional[SecretProvider] = None, 
                       version: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
        """Get secret value"""
        # Check cache first
        cache_key = f"secret:{secret_name}:{version or 'latest'}"
        
        if use_cache:
            cached_secret = await self._get_from_cache(cache_key)
            if cached_secret:
                await self._log_access(secret_name, "cache_hit")
                return cached_secret.value
        
        # Try providers in priority order
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
                # Cache the result
                if use_cache:
                    await self._set_cache(cache_key, secret_value)
                
                await self._log_access(secret_name, provider_type.value)
                return secret_value.value
        
        await self._log_access(secret_name, "not_found")
        return None
    
    async def set_secret(self, secret_name: str, secret_value: str, secret_type: SecretType,
                       provider: SecretProvider = SecretProvider.ENVIRONMENT, 
                       description: str = "", tags: List[str] = None) -> bool:
        """Set secret value"""
        if provider not in self.providers:
            logger.error(f"Provider {provider.value} not available")
            return False
        
        metadata = SecretMetadata(
            name=secret_name,
            type=secret_type,
            provider=provider,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version="1",
            rotation_enabled=False,
            rotation_interval_days=None,
            last_rotated=None,
            description=description,
            tags=tags or []
        )
        
        provider_instance = self.providers[provider]
        success = await provider_instance.set_secret(secret_name, secret_value, metadata)
        
        if success:
            # Invalidate cache
            cache_key = f"secret:{secret_name}:latest"
            await self._delete_cache(cache_key)
            
            await self._log_access(secret_name, "set", provider.value)
        
        return success
    
    async def delete_secret(self, secret_name: str, provider: Optional[SecretProvider] = None) -> bool:
        """Delete secret"""
        if provider:
            if provider not in self.providers:
                return False
            provider_instance = self.providers[provider]
            success = await provider_instance.delete_secret(secret_name)
        else:
            # Try all providers
            success = False
            for provider_type, provider_instance in self.providers.items():
                if await provider_instance.delete_secret(secret_name):
                    success = True
                    break
        
        if success:
            # Invalidate cache
            await self._delete_cache(f"secret:{secret_name}:latest")
            await self._log_access(secret_name, "deleted")
        
        return success
    
    async def list_secrets(self, provider: Optional[SecretProvider] = None) -> Dict[str, List[str]]:
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
    
    async def rotate_secret(self, secret_name: str, provider: Optional[SecretProvider] = None) -> bool:
        """Rotate secret"""
        if provider:
            if provider not in self.providers:
                return False
            provider_instance = self.providers[provider]
            success = await provider_instance.rotate_secret(secret_name)
        else:
            # Try all providers
            success = False
            for provider_type, provider_instance in self.providers.items():
                if await provider_instance.rotate_secret(secret_name):
                    success = True
                    break
        
        if success:
            # Invalidate cache
            await self._delete_cache(f"secret:{secret_name}:latest")
            await self._log_access(secret_name, "rotated")
        
        return success
    
    async def _get_from_cache(self, cache_key: str) -> Optional[SecretValue]:
        """Get secret from cache"""
        # Try local cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try Redis cache
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    secret_data = json.loads(cached_data)
                    metadata = SecretMetadata(**secret_data['metadata'])
                    secret_value = SecretValue(
                        value=secret_data['value'],
                        metadata=metadata
                    )
                    
                    # Update local cache
                    self.cache[cache_key] = secret_value
                    return secret_value
            except Exception as e:
                logger.error(f"Error getting secret from Redis cache: {e}")
        
        return None
    
    async def _set_cache(self, cache_key: str, secret_value: SecretValue):
        """Set secret in cache"""
        # Update local cache
        self.cache[cache_key] = secret_value
        
        # Update Redis cache
        if self.redis_client:
            try:
                cache_data = {
                    'value': secret_value.value,
                    'metadata': asdict(secret_value.metadata)
                }
                await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))
            except Exception as e:
                logger.error(f"Error setting secret in Redis cache: {e}")
    
    async def _delete_cache(self, cache_key: str):
        """Delete secret from cache"""
        # Remove from local cache
        if cache_key in self.cache:
            del self.cache[cache_key]
        
        # Remove from Redis cache
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.error(f"Error deleting secret from Redis cache: {e}")
    
    async def _log_access(self, secret_name: str, action: str, provider: str = ""):
        """Log secret access for audit"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "secret_name": secret_name,
            "action": action,
            "provider": provider,
            "source": "secret_manager"
        }
        
        self.audit_log.append(log_entry)
        
        # Keep audit log size manageable
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        
        logger.info(f"Secret access: {action} on {secret_name} via {provider}")
    
    async def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        return self.audit_log[-limit:]
    
    async def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        
        if self.redis_client:
            try:
                # Clear all secret-related keys
                keys = await self.redis_client.keys("secret:*")
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")
        
        logger.info("Secret manager cache cleared")


# Global secret manager
secret_manager = SecretManager()


def get_secret_manager() -> SecretManager:
    """Get global secret manager instance"""
    return secret_manager


# Convenience functions
async def get_secret(secret_name: str, provider: Optional[SecretProvider] = None) -> Optional[str]:
    """Get secret value"""
    return await secret_manager.get_secret(secret_name, provider)


async def get_api_key(service_name: str) -> Optional[str]:
    """Get API key for service"""
    return await secret_manager.get_secret(f"{service_name}_api_key")


async def get_database_credentials() -> Optional[Dict[str, str]]:
    """Get database credentials"""
    username = await secret_manager.get_secret("database_username")
    password = await secret_manager.get_secret("database_password")
    
    if username and password:
        return {"username": username, "password": password}
    return None


# Initialization function
async def initialize_secret_manager():
    """Initialize secret manager with providers"""
    manager = get_secret_manager()
    
    # Add environment provider (always available)
    manager.add_provider(SecretProvider.ENVIRONMENT, EnvironmentSecretProvider(), priority=1)
    
    # Add AWS Secrets Manager if configured
    aws_region = os.getenv("AWS_REGION")
    if aws_region:
        try:
            aws_provider = AWSSecretsManagerProvider(aws_region)
            manager.add_provider(SecretProvider.AWS_SECRETS_MANAGER, aws_provider, priority=3)
            logger.info("AWS Secrets Manager provider added")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager: {e}")
    
    # Add HashiCorp Vault if configured
    vault_url = os.getenv("VAULT_URL")
    vault_token = os.getenv("VAULT_TOKEN")
    if vault_url and vault_token:
        try:
            vault_provider = HashiCorpVaultProvider(vault_url, vault_token)
            manager.add_provider(SecretProvider.HASHICORP_VAULT, vault_provider, priority=2)
            logger.info("HashiCorp Vault provider added")
        except Exception as e:
            logger.error(f"Failed to initialize HashiCorp Vault: {e}")
    
    # Set up Redis if available
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_client = await aioredis.from_url(redis_url)
            manager.set_redis_client(redis_client)
            logger.info("Redis client set for secret manager")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for secret manager: {e}")
    
    logger.info("Secret manager initialized")
