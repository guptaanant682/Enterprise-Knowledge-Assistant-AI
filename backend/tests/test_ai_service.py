import pytest
from unittest.mock import AsyncMock, Mock, patch
from services.ai_service import AIService


class TestAIService:
    """Test AI Service functionality."""
    
    @pytest.fixture
    def ai_service(self, test_settings):
        """Create AI service instance for testing."""
        with patch('services.ai_service.settings', test_settings):
            return AIService()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ai_service):
        """Test successful AI response generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response"
        
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.generate_response(
                "What is the company policy?",
                user_id=1
            )
            
            assert result["message"] == "This is a test response"
            assert "response_time" in result
            assert "model_used" in result
            assert "provider" in result
            assert result["sources"] == []
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, ai_service):
        """Test AI response generation with relevant documents."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Based on the policy document..."
        
        relevant_docs = [
            {
                "title": "HR Policy",
                "content": "Employees must follow dress code",
                "relevance_score": 0.95,
                "category": "policy"
            }
        ]
        
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.generate_response(
                "What is the dress code?",
                relevant_docs=relevant_docs,
                user_id=1
            )
            
            assert result["message"] == "Based on the policy document..."
            assert len(result["sources"]) == 1
            assert result["sources"][0]["title"] == "HR Policy"
            assert result["sources"][0]["type"] == "policy"
    
    @pytest.mark.asyncio
    async def test_generate_response_api_error(self, ai_service):
        """Test AI response generation with API error."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await ai_service.generate_response("Test question")
            
            assert "I apologize, but I'm having trouble" in result["message"]
            assert "error" in result
            assert result["sources"] == []
    
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, ai_service):
        """Test successful document summary generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This document outlines company policies..."
        
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.generate_summary("Long document content here...")
            
            assert result == "This document outlines company policies..."
    
    @pytest.mark.asyncio
    async def test_generate_summary_error(self, ai_service):
        """Test summary generation with error."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await ai_service.generate_summary("Test content")
            
            assert result == "Summary not available"
    
    @pytest.mark.asyncio
    async def test_categorize_document_success(self, ai_service):
        """Test successful document categorization."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "policy"
        
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.categorize_document(
                "HR Policy Document",
                "This document contains company policies..."
            )
            
            assert result == "policy"
    
    @pytest.mark.asyncio
    async def test_categorize_document_invalid_category(self, ai_service):
        """Test document categorization with invalid category."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "invalid_category"
        
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await ai_service.categorize_document("Test", "Content")
            
            assert result == "other"
    
    @pytest.mark.asyncio
    async def test_categorize_document_error(self, ai_service):
        """Test document categorization with error."""
        with patch.object(ai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await ai_service.categorize_document("Test", "Content")
            
            assert result == "other"
    
    def test_build_context(self, ai_service):
        """Test context building from relevant documents."""
        docs = [
            {"title": "Doc 1", "content": "Content 1"},
            {"title": "Doc 2", "content": "Content 2"}
        ]
        
        context = ai_service._build_context(docs)
        
        assert "Document: Doc 1" in context
        assert "Content: Content 1" in context
        assert "Document: Doc 2" in context
        assert "Content: Content 2" in context
    
    def test_build_context_empty(self, ai_service):
        """Test context building with empty documents."""
        context = ai_service._build_context([])
        assert context == ""
    
    def test_build_context_long_content(self, ai_service):
        """Test context building with long content (truncation)."""
        long_content = "x" * 1500  # More than 1000 chars
        docs = [{"title": "Long Doc", "content": long_content}]
        
        context = ai_service._build_context(docs)
        
        assert "..." in context  # Should be truncated
        assert len(context) < len(long_content)
    
    def test_extract_sources(self, ai_service):
        """Test source extraction from relevant documents."""
        docs = [
            {"title": "Doc 1", "category": "policy", "relevance_score": 0.9},
            {"title": "Doc 2", "category": "manual", "relevance_score": 0.8},
            {"title": "Doc 3", "category": "guide", "relevance_score": 0.7},
            {"title": "Doc 4", "category": "other", "relevance_score": 0.6}  # Should be excluded (top 3 only)
        ]
        
        sources = ai_service._extract_sources(docs)
        
        assert len(sources) == 3  # Limited to top 3
        assert sources[0]["title"] == "Doc 1"
        assert sources[0]["type"] == "policy"
        assert sources[0]["relevance"] == 0.9
    
    def test_create_system_prompt_with_context(self, ai_service):
        """Test system prompt creation with context."""
        context = "Document: Test\nContent: Test content"
        
        prompt = ai_service._create_system_prompt(context)
        
        assert "Enterprise Knowledge Assistant" in prompt
        assert "Knowledge Base Context:" in prompt
        assert context in prompt
    
    def test_create_system_prompt_without_context(self, ai_service):
        """Test system prompt creation without context."""
        prompt = ai_service._create_system_prompt("")
        
        assert "Enterprise Knowledge Assistant" in prompt
        assert "No specific context documents were found" in prompt