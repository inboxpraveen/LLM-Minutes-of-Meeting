"""
Configuration management for speech providers.
"""
import os
import warnings
from typing import Optional, Dict, Any
from pathlib import Path


class SpeechConfig:
    """
    Centralized configuration management for speech providers.
    Reads from env.config file and environment variables.
    """
    
    # Provider key mappings
    PROVIDER_KEYS = {
        'deepgram': 'DEEPGRAM_API_KEY',
        'assemblyai': 'ASSEMBLYAI_API_KEY',
        'togetherai': 'TOGETHER_API_KEY',
        'elevenlabs': 'ELEVENLABS_API_KEY',
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to env.config file. Defaults to 'env.config' in project root.
        """
        if config_file is None:
            # Default to env.config in project root
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "env.config"
        
        self.config_file = Path(config_file)
        self._config_cache: Dict[str, str] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from env.config file and environment variables.
        """
        # First, load from environment variables
        for provider, key_name in self.PROVIDER_KEYS.items():
            env_value = os.environ.get(key_name)
            if env_value:
                self._config_cache[key_name] = env_value
        
        # Then, load from config file (overrides env vars)
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            if value:  # Only store non-empty values
                                self._config_cache[key] = value
            except Exception as e:
                warnings.warn(f"Error reading config file {self.config_file}: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (e.g., 'deepgram', 'assemblyai')
            
        Returns:
            API key if found, None otherwise
        """
        key_name = self.PROVIDER_KEYS.get(provider.lower())
        if not key_name:
            return None
        
        api_key = self._config_cache.get(key_name)
        if not api_key:
            # Try environment variable as fallback
            api_key = os.environ.get(key_name)
        
        return api_key
    
    def validate_api_key(self, provider: str, raise_error: bool = False) -> bool:
        """
        Validate that API key exists for a provider.
        
        Args:
            provider: Provider name
            raise_error: If True, raises ValueError instead of warning
            
        Returns:
            True if API key exists, False otherwise
            
        Raises:
            ValueError: If raise_error=True and key is missing
        """
        api_key = self.get_api_key(provider)
        
        if not api_key:
            message = (
                f"API key not found for provider '{provider}'. "
                f"Please set {self.PROVIDER_KEYS.get(provider.lower())} in env.config file or as environment variable."
            )
            
            if raise_error:
                raise ValueError(message)
            else:
                warnings.warn(message, UserWarning)
                return False
        
        return True
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config_cache.get(key, default)
    
    def set_config_value(self, key: str, value: str) -> None:
        """
        Set a configuration value (runtime only, doesn't persist to file).
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config_cache[key] = value
    
    def reload(self) -> None:
        """
        Reload configuration from file and environment.
        """
        self._config_cache.clear()
        self._load_config()
    
    def get_all_config(self) -> Dict[str, str]:
        """
        Get all configuration values (with keys masked for security).
        
        Returns:
            Dictionary with configuration (API keys masked)
        """
        masked = {}
        for key, value in self._config_cache.items():
            if 'KEY' in key or 'TOKEN' in key or 'SECRET' in key:
                masked[key] = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                masked[key] = value
        return masked


# Global configuration instance
_global_config: Optional[SpeechConfig] = None


def get_config() -> SpeechConfig:
    """
    Get the global configuration instance (singleton pattern).
    
    Returns:
        Global SpeechConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = SpeechConfig()
    return _global_config


def reset_config() -> None:
    """
    Reset the global configuration instance (useful for testing).
    """
    global _global_config
    _global_config = None

