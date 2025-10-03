from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from typing import List, Dict, Any, Optional
import time
import json
from config import settings

class AIService:
    """
    AI Service with Cascade Fallback System

    Priority Order:
    1. OpenAI GPT-4
    2. Anthropic Claude 3.5 Sonnet
    3. OpenRouter (GPT-4 or Claude)
    4. Groq (Llama 70B or GPT-OSS 120B)
    """

    def __init__(self):
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE

        # Define all providers in priority order
        self.providers = self._initialize_providers()

    def _initialize_providers(self) -> List[Dict[str, Any]]:
        """Initialize all AI providers in cascade priority order"""
        providers = []

        # Priority 1: OpenAI Direct
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
            providers.append({
                "name": "openai",
                "client": AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
                "model": settings.OPENAI_MODEL or "gpt-4",
                "type": "openai"
            })

        # Priority 2: Anthropic Claude Direct
        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key":
            providers.append({
                "name": "anthropic",
                "client": AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY),
                "model": settings.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022",
                "type": "anthropic"
            })

        # Priority 3: OpenRouter (GPT-4)
        if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY != "your-openrouter-api-key":
            providers.append({
                "name": "openrouter-gpt4",
                "client": AsyncOpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1"
                ),
                "model": "openai/gpt-4",
                "type": "openai"
            })

        # Priority 4: OpenRouter (Claude)
        if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY != "your-openrouter-api-key":
            providers.append({
                "name": "openrouter-claude",
                "client": AsyncOpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1"
                ),
                "model": "anthropic/claude-3.5-sonnet",
                "type": "openai"
            })

        # Priority 5: Groq (Llama 70B)
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key":
            providers.append({
                "name": "groq-llama",
                "client": AsyncOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url=settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1"
                ),
                "model": settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                "type": "openai"
            })

        # Priority 6: Groq (Alternative model if configured)
        if settings.GROQ_API_KEY and settings.GROQ_ALTERNATIVE_MODEL:
            providers.append({
                "name": "groq-alternative",
                "client": AsyncOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url=settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1"
                ),
                "model": settings.GROQ_ALTERNATIVE_MODEL,
                "type": "openai"
            })

        return providers

    async def generate_response(
        self,
        user_message: str,
        relevant_docs: List[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate AI response with RAG context using cascade fallback"""
        start_time = time.time()

        # Build context from relevant documents
        context = self._build_context(relevant_docs) if relevant_docs else ""

        # Create system prompt
        system_prompt = self._create_system_prompt(context)

        # Try each provider in order until one succeeds
        last_error = None
        for provider in self.providers:
            try:
                print(f"🤖 Trying provider: {provider['name']} with model: {provider['model']}")

                response = await self._call_provider(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_message=user_message
                )

                if response:
                    response_time = time.time() - start_time
                    sources = self._extract_sources(relevant_docs) if relevant_docs else []

                    print(f"✅ Success with {provider['name']}")

                    return {
                        "message": response,
                        "sources": sources,
                        "response_time": response_time,
                        "model_used": provider['model'],
                        "provider": provider['name']
                    }

            except Exception as e:
                last_error = str(e)
                print(f"❌ Provider {provider['name']} failed: {e}")
                continue

        # All providers failed - return fallback response
        print(f"⚠️ All AI providers failed. Using fallback response.")
        return self._generate_fallback_response(user_message, relevant_docs, start_time, last_error)

    async def _call_provider(
        self,
        provider: Dict[str, Any],
        system_prompt: str,
        user_message: str
    ) -> Optional[str]:
        """Call a specific AI provider"""

        if provider['type'] == 'anthropic':
            # Anthropic uses a different API structure
            response = await provider['client'].messages.create(
                model=provider['model'],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            return response.content[0].text

        else:  # OpenAI-compatible APIs (OpenAI, OpenRouter, Groq)
            response = await provider['client'].chat.completions.create(
                model=provider['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content

    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Build context string from relevant documents"""
        if not relevant_docs:
            return ""

        context_parts = []
        for doc in relevant_docs[:5]:  # Limit to top 5 documents
            title = doc.get('title', 'Untitled')
            content = doc.get('content', '')

            # Truncate content if too long
            if len(content) > 1000:
                content = content[:1000] + "..."

            context_parts.append(f"Document: {title}\nContent: {content}\n")

        return "\n".join(context_parts)

    def _create_system_prompt(self, context: str) -> str:
        """Create system prompt with context"""
        base_prompt = """You are an Enterprise Knowledge Assistant, an AI assistant designed to help employees find information from the company's knowledge base.

Your responsibilities:
1. Answer questions accurately based on the provided context
2. Be helpful, professional, and concise
3. If information is not in the context, clearly state that
4. Provide specific references to documents when possible
5. Ask clarifying questions if the user's request is unclear

Guidelines:
- Always be honest about what you know and don't know
- Maintain a professional tone
- Provide actionable information when possible
- If you reference specific policies or procedures, mention the source document
"""

        if context:
            base_prompt += f"\n\nKnowledge Base Context:\n{context}\n\nPlease answer the user's question based on this context."
        else:
            base_prompt += "\n\nNo specific context documents were found for this query. Please provide a helpful general response and suggest how the user might find more specific information."

        return base_prompt

    def _extract_sources(self, relevant_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from relevant documents"""
        sources = []
        for doc in relevant_docs[:3]:  # Limit to top 3 sources
            sources.append({
                "title": doc.get('title', 'Untitled'),
                "type": doc.get('category', 'document'),
                "relevance": doc.get('relevance_score', 0.0)
            })
        return sources

    async def generate_summary(self, text: str) -> str:
        """Generate a summary of document content using cascade fallback"""
        if not self.providers:
            raise Exception("No AI providers configured")

        # Try each provider until one succeeds
        last_error = None
        for provider in self.providers:
            try:
                print(f"🤖 Trying summary generation with: {provider['name']}")

                if provider['type'] == 'anthropic':
                    response = await provider['client'].messages.create(
                        model=provider['model'],
                        max_tokens=200,
                        temperature=0.3,
                        system="You are a document summarization assistant. Create concise, informative summaries that capture the key points and main topics of documents.",
                        messages=[
                            {"role": "user", "content": f"Please provide a concise summary of this document content:\n\n{text[:4000]}"}
                        ]
                    )
                    result = response.content[0].text.strip()
                else:
                    response = await provider['client'].chat.completions.create(
                        model=provider['model'],
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a document summarization assistant. Create concise, informative summaries that capture the key points and main topics of documents."
                            },
                            {
                                "role": "user",
                                "content": f"Please provide a concise summary of this document content:\n\n{text[:4000]}"
                            }
                        ],
                        max_tokens=200,
                        temperature=0.3
                    )
                    result = response.choices[0].message.content.strip()

                print(f"✅ Summary generated successfully with {provider['name']}")
                return result

            except Exception as e:
                last_error = str(e)
                print(f"❌ Provider {provider['name']} failed for summary: {e}")
                continue

        # All providers failed
        raise Exception(f"All AI providers failed. Last error: {last_error}")

    async def categorize_document(self, title: str, content: str) -> str:
        """Automatically categorize a document using cascade fallback"""
        if not self.providers:
            raise Exception("No AI providers configured")

        valid_categories = ["policy", "procedure", "manual", "guide", "other"]

        # Try each provider until one succeeds
        last_error = None
        for provider in self.providers:
            try:
                print(f"🤖 Trying categorization with: {provider['name']}")

                if provider['type'] == 'anthropic':
                    response = await provider['client'].messages.create(
                        model=provider['model'],
                        max_tokens=10,
                        temperature=0.1,
                        system="Categorize documents into one of these categories: policy, procedure, manual, guide, other. Respond with only the category name.",
                        messages=[
                            {"role": "user", "content": f"Title: {title}\nContent preview: {content[:500]}"}
                        ]
                    )
                    category = response.content[0].text.strip().lower()
                else:
                    response = await provider['client'].chat.completions.create(
                        model=provider['model'],
                        messages=[
                            {
                                "role": "system",
                                "content": "Categorize documents into one of these categories: policy, procedure, manual, guide, other. Respond with only the category name."
                            },
                            {
                                "role": "user",
                                "content": f"Title: {title}\nContent preview: {content[:500]}"
                            }
                        ],
                        max_tokens=10,
                        temperature=0.1
                    )
                    category = response.choices[0].message.content.strip().lower()

                result = category if category in valid_categories else "other"
                print(f"✅ Categorization successful with {provider['name']}: {result}")
                return result

            except Exception as e:
                last_error = str(e)
                print(f"❌ Provider {provider['name']} failed for categorization: {e}")
                continue

        # All providers failed - return default
        raise Exception(f"All AI providers failed. Last error: {last_error}")

    def _generate_fallback_response(self, user_message: str, relevant_docs: List[Dict[str, Any]] = None, start_time: float = None, error: str = None) -> Dict[str, Any]:
        """Generate a fallback response when all AI services are unavailable"""
        if start_time is None:
            start_time = time.time()

        # Build context from relevant documents
        context_info = ""
        sources = []

        if relevant_docs:
            sources = self._extract_sources(relevant_docs)
            doc_titles = [doc.get('title', 'Untitled') for doc in relevant_docs[:3]]
            context_info = f" I found some relevant documents: {', '.join(doc_titles)}."

        # Generate a helpful fallback response
        if not self.providers:
            message = f"⚠️ No AI providers are configured. Please contact your administrator to set up API keys for OpenAI, Anthropic Claude, OpenRouter, or Groq.{context_info}"
        elif error and "API key" in error:
            message = f"I'm currently unable to process your request because all configured AI providers failed.{context_info} Please contact your administrator to verify API keys."
        else:
            message = f"I'm temporarily unable to process your request due to technical issues.{context_info} Please try again later or contact support if the issue persists."

        return {
            "message": message,
            "sources": sources,
            "response_time": time.time() - start_time,
            "model_used": "fallback",
            "provider": "fallback"
        }
