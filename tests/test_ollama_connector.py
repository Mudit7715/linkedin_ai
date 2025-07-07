import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ollama_connector import OllamaConnector, OllamaConfig

class TestOllamaConnector:
    @pytest.fixture
    def test_config(self):
        """Create test configuration"""
        config = {
            'ollama': {
                'model': 'test-model',
                'temperature': 0.8,
                'max_tokens': 500
            },
            'prompts': {
                'test_prompt': {
                    'system': 'You are a test assistant.',
                    'user': 'Generate a test response for {name}.'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
            yaml.dump(config, tmp)
            config_path = tmp.name
        
        yield config_path
        os.unlink(config_path)
    
    def test_load_prompts(self, test_config):
        """Test loading prompts from config"""
        connector = OllamaConnector(test_config)
        
        assert 'test_prompt' in connector.prompts
        assert connector.prompts['test_prompt']['system'] == 'You are a test assistant.'
        assert connector.config.model == 'test-model'
        assert connector.config.temperature == 0.8
    
    def test_default_prompts(self):
        """Test loading default prompts when config missing"""
        connector = OllamaConnector('nonexistent.yml')
        
        assert 'connection_request' in connector.prompts
        assert 'personalized_message' in connector.prompts
        assert 'viral_post' in connector.prompts
    
    @patch('requests.post')
    def test_generate_success(self, mock_post, test_config):
        """Test successful generation"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Generated test response for John'
        }
        mock_post.return_value = mock_response
        
        connector = OllamaConnector(test_config)
        result = connector.generate('test_prompt', {'name': 'John'})
        
        assert result == 'Generated test response for John'
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        assert call_args[0][0] == 'http://localhost:11434/api/generate'
        assert call_args[1]['json']['prompt'] == 'Generate a test response for John.'
        assert call_args[1]['json']['system'] == 'You are a test assistant.'
    
    @patch('requests.post')
    def test_generate_with_custom_prompt(self, mock_post, test_config):
        """Test generation with custom prompt"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Custom response'}
        mock_post.return_value = mock_response
        
        connector = OllamaConnector(test_config)
        result = connector.generate(
            'custom',
            {},
            custom_prompt='Generate a custom response',
            temperature=0.5
        )
        
        assert result == 'Custom response'
        
        # Verify custom temperature was used
        call_args = mock_post.call_args
        assert call_args[1]['json']['options']['temperature'] == 0.5
    
    @patch('requests.post')
    def test_generate_retry_logic(self, mock_post, test_config):
        """Test retry logic on failure"""
        # First two calls fail, third succeeds
        mock_post.side_effect = [
            Exception("Connection error"),
            Exception("Timeout"),
            MagicMock(status_code=200, json=lambda: {'response': 'Success after retry'})
        ]
        
        connector = OllamaConnector(test_config)
        connector.config.retry_attempts = 3
        connector.config.retry_delay = 0  # No delay for tests
        
        result = connector.generate('test_prompt', {'name': 'Test'})
        
        assert result == 'Success after retry'
        assert mock_post.call_count == 3
    
    @patch('requests.get')
    def test_check_health(self, mock_get, test_config):
        """Test health check"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'test-model:latest'},
                {'name': 'llama2:latest'}
            ]
        }
        mock_get.return_value = mock_response
        
        connector = OllamaConnector(test_config)
        is_healthy = connector.check_health()
        
        assert is_healthy == True
    
    @patch('requests.get')
    def test_list_models(self, mock_get, test_config):
        """Test listing available models"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama2:latest'},
                {'name': 'mistral:latest'}
            ]
        }
        mock_get.return_value = mock_response
        
        connector = OllamaConnector(test_config)
        models = connector.list_models()
        
        assert 'llama2:latest' in models
        assert 'mistral:latest' in models
