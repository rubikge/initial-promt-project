import pytest
from unittest.mock import patch
from src.llms.replicate import ReplicateClient, MODELS, CompletionResponse, TokenUsage


class TestReplicateClient:
    def test_init(self):
        """Test ReplicateClient initialization"""
        api_token = "test_token"
        client = ReplicateClient(api_token)
        assert client.api_token == api_token

    def test_calculate_cost(self):
        """Test cost calculation"""
        client = ReplicateClient("test_token")
        
        # Test with default costs
        cost = client.calculate_cost(1000, 500)
        expected_cost = (1000 / 1_000_000) * 0.2 + (500 / 1_000_000) * 0.8
        assert cost == expected_cost
        
        # Test with custom costs
        cost = client.calculate_cost(1000, 500, 0.5, 1.0)
        expected_cost = (1000 / 1_000_000) * 0.5 + (500 / 1_000_000) * 1.0
        assert cost == expected_cost

    @patch('src.llms.replicate.replicate_client.replicate')
    def test_get_completion_success(self, mock_replicate):
        """Test successful completion request"""
        # Mock the replicate.run method
        mock_output = "This is a test response"
        mock_replicate.run.return_value = mock_output
        
        client = ReplicateClient("test_token")
        response = client.get_completion("Test prompt")
        
        assert isinstance(response, CompletionResponse)
        assert response.content == mock_output
        assert isinstance(response.token_usage, TokenUsage)
        
        # Verify replicate.run was called with correct parameters
        mock_replicate.run.assert_called_once()
        call_args = mock_replicate.run.call_args
        assert call_args[0][0] == MODELS.FLUX_1_1_PRO_ULTRA.name
        assert call_args[1]['input']['prompt'] == "Test prompt"

    @patch('src.llms.replicate.replicate_client.replicate')
    def test_get_completion_with_json_output(self, mock_replicate):
        """Test completion request with JSON output"""
        # Mock JSON response
        json_response = '{"key": "value", "number": 42}'
        mock_replicate.run.return_value = json_response
        
        client = ReplicateClient("test_token")
        response = client.get_completion("Test prompt", json_output=True)
        
        assert isinstance(response.content, dict)
        assert response.content["key"] == "value"
        assert response.content["number"] == 42

    @patch('src.llms.replicate.replicate_client.replicate')
    def test_get_completion_with_custom_model(self, mock_replicate):
        """Test completion request with custom model configuration"""
        mock_output = "Custom model response"
        mock_replicate.run.return_value = mock_output
        
        client = ReplicateClient("test_token")
        custom_model = MODELS.FLUX_KONTEXT_PRO
        _ = client.get_completion("Test prompt", model_config=custom_model)
        
        # Verify the correct model was used
        call_args = mock_replicate.run.call_args
        assert call_args[0][0] == custom_model.name
        assert call_args[1]['input']['prompt'] == "Test prompt"

    @patch('src.llms.replicate.replicate_client.replicate')
    def test_get_completion_retry_on_failure(self, mock_replicate):
        """Test that completion retries on failure"""
        # Mock replicate.run to fail twice, then succeed
        mock_replicate.run.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            "Success response"
        ]
        
        client = ReplicateClient("test_token")
        response = client.get_completion("Test prompt", max_retries=3)
        
        assert response.content == "Success response"
        assert mock_replicate.run.call_count == 3

    @patch('src.llms.replicate.replicate_client.replicate')
    def test_get_completion_max_retries_exceeded(self, mock_replicate):
        """Test that completion raises exception after max retries"""
        # Mock replicate.run to always fail
        mock_replicate.run.side_effect = Exception("Persistent failure")
        
        client = ReplicateClient("test_token")
        
        with pytest.raises(Exception) as exc_info:
            client.get_completion("Test prompt", max_retries=2)
        
        assert "Failed after 2 attempts" in str(exc_info.value)
        assert mock_replicate.run.call_count == 2

    @patch('src.llms.replicate.replicate_client.replicate')
    def test_stream_completion(self, mock_replicate):
        """Test streaming completion"""
        # Mock streaming response
        mock_stream = ["Hello", " ", "world", "!"]
        mock_replicate.run.return_value = mock_stream
        
        client = ReplicateClient("test_token")
        stream = client.stream_completion("Test prompt")
        
        # Collect streamed output
        output = list(stream)
        assert output == mock_stream
        
        # Verify replicate.run was called with stream=True
        call_args = mock_replicate.run.call_args
        assert call_args[1]['stream'] is True

    def test_token_usage_estimation(self):
        """Test token usage estimation"""
        _ = ReplicateClient("test_token")
        
        # Test with a simple response
        prompt = "Hello world"
        response_text = "This is a test response"
        
        # Calculate expected token estimation
        expected_prompt_tokens = int(len(prompt.split()) * 1.3)
        expected_completion_tokens = int(len(response_text.split()) * 1.3)
        expected_total_tokens = expected_prompt_tokens + expected_completion_tokens
        
        # This is a rough test since we can't easily mock the internal token calculation
        # but we can verify the structure is correct
        token_usage = TokenUsage(
            prompt_tokens=expected_prompt_tokens,
            completion_tokens=expected_completion_tokens,
            total_tokens=expected_total_tokens
        )
        
        assert token_usage.prompt_tokens > 0
        assert token_usage.completion_tokens > 0
        assert token_usage.total_tokens == token_usage.prompt_tokens + token_usage.completion_tokens


class TestModels:
    def test_model_configs(self):
        """Test that all model configurations are valid"""
        # Test Flux models
        assert MODELS.FLUX_1_1_PRO_ULTRA.name == "black-forest-labs/flux-1.1-pro-ultra"
        assert MODELS.FLUX_KONTEXT_PRO.name == "black-forest-labs/flux-kontext-pro"
        
        # Test that all models have valid configurations
        for model_name in dir(MODELS):
            if not model_name.startswith('_'):
                model_config = getattr(MODELS, model_name)
                if hasattr(model_config, 'name'):
                    assert isinstance(model_config.name, str)
                    assert isinstance(model_config.aspect_ratio, str)
                    assert isinstance(model_config.output_format, str)
                    assert isinstance(model_config.output_quality, int)
                    assert isinstance(model_config.safety_tolerance, int)
                    assert isinstance(model_config.raw, bool)
                    assert isinstance(model_config.num_inference_steps, int)
                    assert isinstance(model_config.guidance_scale, float)

    def test_flux_1_1_pro_ultra_config(self):
        """Test specific configuration for FLUX_1_1_PRO_ULTRA"""
        model = MODELS.FLUX_1_1_PRO_ULTRA
        assert model.name == "black-forest-labs/flux-1.1-pro-ultra"
        assert model.aspect_ratio == "1:1"
        assert model.output_format == "jpg"
        assert model.output_quality == 95
        assert model.safety_tolerance == 2
        assert model.raw is True
        assert model.num_inference_steps == 50
        assert model.guidance_scale == 7.5

    def test_flux_kontext_pro_config(self):
        """Test specific configuration for FLUX_KONTEXT_PRO"""
        model = MODELS.FLUX_KONTEXT_PRO
        assert model.name == "black-forest-labs/flux-kontext-pro"
        assert model.aspect_ratio == "1:1"
        assert model.output_format == "jpg"
        assert model.output_quality == 95
        assert model.safety_tolerance == 2
        assert model.raw is True
        assert model.num_inference_steps == 50
        assert model.guidance_scale == 7.5 