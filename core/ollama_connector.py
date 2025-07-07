import requests
import json
import time
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: int = 2

class OllamaConnector:
    def __init__(self, config_path: str = "config/prompts.yml"):
        self.config = OllamaConfig()
        self.config_path = config_path
        self.prompts = self._load_prompts()
        
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Update model settings if specified
            if 'ollama' in config:
                ollama_config = config['ollama']
                if 'model' in ollama_config:
                    self.config.model = ollama_config['model']
                if 'temperature' in ollama_config:
                    self.config.temperature = ollama_config['temperature']
                if 'max_tokens' in ollama_config:
                    self.config.max_tokens = ollama_config['max_tokens']
                    
            return config.get('prompts', {})
        except FileNotFoundError:
            logger.warning(f"Prompts file {self.config_path} not found. Using defaults.")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Default prompts if config file is missing"""
        return {
            'connection_request': {
                'system': "You are a professional networking assistant helping create personalized LinkedIn connection requests.",
                'user': "Create a connection request for {name} at {company}, title: {title}. Profile summary: {summary}"
            },
            'personalized_message': {
                'system': "You are crafting highly personalized outreach messages for AI professionals.",
                'user': "Write a personalized message to {name} at {company}. Their profile: {profile_data}. Focus on AI/ML relevance."
            },
            'viral_post': {
                'system': "You are a LinkedIn content strategist specializing in AI topics.",
                'user': "Based on these viral posts: {viral_insights}, create an engaging post about AI. Max 1300 chars."
            }
        }
    
    def reload_prompts(self):
        """Hot reload prompts from config file"""
        self.prompts = self._load_prompts()
        logger.info("Prompts reloaded successfully")
    
    def generate(self, 
                 prompt_type: str, 
                 variables: Dict[str, str],
                 custom_prompt: Optional[str] = None,
                 temperature: Optional[float] = None) -> Optional[str]:
        """Generate text using Ollama"""
        
        # Get prompt template
        if custom_prompt:
            system_prompt = ""
            user_prompt = custom_prompt
        else:
            if prompt_type not in self.prompts:
                logger.error(f"Prompt type '{prompt_type}' not found")
                return None
                
            prompt_template = self.prompts[prompt_type]
            system_prompt = prompt_template.get('system', '')
            user_prompt = prompt_template.get('user', '')
            
            # Replace variables in user prompt
            for key, value in variables.items():
                user_prompt = user_prompt.replace(f"{{{key}}}", str(value))
        
        # Prepare request
        payload = {
            "model": self.config.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        # Retry logic
        for attempt in range(self.config.retry_attempts):
            try:
                response = requests.post(
                    f"{self.config.base_url}/api/generate",
                    json=payload,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get('response', '').strip()
                    
                    # Token limit guard
                    if len(generated_text.split()) > self.config.max_tokens * 0.9:
                        logger.warning("Response near token limit, may be truncated")
                    
                    return generated_text
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
                    
        return None
    
    def check_health(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.config.base_url}/api/tags")
            if response.status_code != 200:
                return False
                
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [m.get('name', '').split(':')[0] for m in models]
            
            if self.config.model not in model_names:
                logger.error(f"Model {self.config.model} not found. Available: {model_names}")
                return False
                
            return True
            
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.config.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m.get('name', '') for m in models]
        except requests.exceptions.RequestException:
            pass
        return []
    
    def set_model(self, model_name: str):
        """Change the active model"""
        self.config.model = model_name
        logger.info(f"Model changed to {model_name}")
