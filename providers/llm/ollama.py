"""
Ollama local LLM provider.
https://ollama.ai/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any, List

from .base import BaseLLMProvider
from .config import get_config


class OllamaProvider(BaseLLMProvider):
    """
    Ollama local LLM provider.
    Runs models locally using Ollama.
    Processes requests sequentially due to local resource constraints.
    """
    
    provider_name = "ollama"
    is_local = True
    max_concurrent = 1  # Local model processes sequentially
    supports_streaming = True
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Ollama provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - model: Model to use (default: 'llama2')
                  Examples: 'llama2', 'mistral', 'codellama', 'phi', etc.
                - host: Ollama host URL (default: 'http://localhost:11434')
                - temperature: Temperature for sampling (default: 0.7)
                - top_p: Top-p sampling parameter (default: 0.9)
                - top_k: Top-k sampling parameter (default: 40)
                - num_predict: Maximum tokens to generate (default: 1000)
                - repeat_penalty: Repeat penalty (default: 1.1)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'llama2')
        self.config.setdefault('host', 'http://localhost:11434')
        self.config.setdefault('temperature', 0.7)
        self.config.setdefault('top_p', 0.9)
        self.config.setdefault('top_k', 40)
        self.config.setdefault('num_predict', 1000)
        self.config.setdefault('repeat_penalty', 1.1)
    
    def _validate_config(self) -> None:
        """Validate Ollama configuration."""
        # Check if Ollama is accessible
        host = self.config.get('host', 'http://localhost:11434')
        
        # Note: We don't check connectivity here to avoid blocking
        # The error will be raised when actually trying to generate
        pass
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional Ollama parameters
            
        Returns:
            Generated text
            
        Raises:
            ValueError: If generation fails
        """
        try:
            # Import ollama SDK
            import ollama
            
            # Build options
            options = {
                'temperature': kwargs.get('temperature', self.config.get('temperature', 0.7)),
                'top_p': kwargs.get('top_p', self.config.get('top_p', 0.9)),
                'top_k': kwargs.get('top_k', self.config.get('top_k', 40)),
                'num_predict': kwargs.get('num_predict', self.config.get('num_predict', 1000)),
                'repeat_penalty': kwargs.get('repeat_penalty', self.config.get('repeat_penalty', 1.1)),
            }
            
            # Build prompt with system if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Run generation in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Use ollama.generate for simple generation
            response = await loop.run_in_executor(
                None,
                lambda: ollama.generate(
                    model=self.config.get('model', 'llama2'),
                    prompt=full_prompt,
                    options=options
                )
            )
            
            return response['response']
            
        except ImportError:
            raise ImportError(
                "Ollama Python SDK not installed. Install with: pip install ollama"
            )
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower():
                raise ValueError(
                    f"Could not connect to Ollama at {self.config.get('host')}. "
                    "Make sure Ollama is running. Start it with: ollama serve"
                )
            raise ValueError(f"Ollama generation failed: {error_msg}")
    
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion using Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional Ollama parameters
            
        Returns:
            Generated response
        """
        try:
            import ollama
            
            # Build options
            options = {
                'temperature': kwargs.get('temperature', self.config.get('temperature', 0.7)),
                'top_p': kwargs.get('top_p', self.config.get('top_p', 0.9)),
                'top_k': kwargs.get('top_k', self.config.get('top_k', 40)),
                'num_predict': kwargs.get('num_predict', self.config.get('num_predict', 1000)),
                'repeat_penalty': kwargs.get('repeat_penalty', self.config.get('repeat_penalty', 1.1)),
            }
            
            # Run chat in executor
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: ollama.chat(
                    model=self.config.get('model', 'llama2'),
                    messages=messages,
                    options=options
                )
            )
            
            return response['message']['content']
            
        except ImportError:
            raise ImportError(
                "Ollama Python SDK not installed. Install with: pip install ollama"
            )
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower():
                raise ValueError(
                    f"Could not connect to Ollama at {self.config.get('host')}. "
                    "Make sure Ollama is running. Start it with: ollama serve"
                )
            raise ValueError(f"Ollama chat generation failed: {error_msg}")
    
    def list_models(self) -> List[str]:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            import ollama
            
            models = ollama.list()
            return [model['name'] for model in models.get('models', [])]
            
        except ImportError:
            raise ImportError(
                "Ollama Python SDK not installed. Install with: pip install ollama"
            )
        except Exception as e:
            warnings.warn(f"Failed to list Ollama models: {str(e)}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download an Ollama model.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import ollama
            
            print(f"Pulling Ollama model: {model_name}")
            ollama.pull(model_name)
            print(f"Successfully pulled model: {model_name}")
            return True
            
        except ImportError:
            raise ImportError(
                "Ollama Python SDK not installed. Install with: pip install ollama"
            )
        except Exception as e:
            warnings.warn(f"Failed to pull model {model_name}: {str(e)}")
            return False

