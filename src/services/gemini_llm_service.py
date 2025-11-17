"""
Real Gemini API Integration for LLM Analysis
SPEC-AI-FACIL-001 Phase 3: Production-grade Gemini API integration
Replaces mock LLM responses with real google-generativeai API calls
"""

import json
import re
import time
import logging
from typing import Optional, Dict, List, Any
import tiktoken
import google.generativeai as genai
from google.api_core import retry, exceptions

# Import prompt templates from separate files
from ..prompts import (
    OutlierPromptTemplate,
    SummaryPromptTemplate,
    ConnectPromptTemplate,
    QuestionPromptTemplate,
)

# Configure logging
logger = logging.getLogger(__name__)


class GeminiLLMService:
    """Real Gemini API integration for LLM analysis"""

    VALID_MODES = ["outlier", "summary", "connect", "question"]
    DEFAULT_MODEL = "gemini-2.5-flash-lite"

    # Retry configuration
    RETRY_MAX_ATTEMPTS = 3
    RETRY_INITIAL_DELAY = 1.0
    RETRY_MAX_DELAY = 10.0
    RETRY_MULTIPLIER = 2.0

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = 30
    ):
        """Initialize Gemini LLM service with real API integration"""
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_tokens = 128000
        self.confidence_threshold = 0.7

        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

        # Initialize tiktoken for token counting
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken: {e}")
            self.encoding = None

        # Prompt templates
        self.templates = {
            "outlier": OutlierPromptTemplate(),
            "summary": SummaryPromptTemplate(),
            "connect": ConnectPromptTemplate(),
            "question": QuestionPromptTemplate()
        }

        logger.info(f"Initialized GeminiLLMService with model: {model}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        if self.encoding is None:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            return len(text) // 4

    def count_tokens_for_document(self, document: Dict[str, Any]) -> int:
        """Count total tokens for document including context files"""
        total = 0

        # Count contributions
        for contrib in document.get("contributions", []):
            total += self.count_tokens(contrib.get("text", ""))
            total += self.count_tokens(contrib.get("author", ""))

        # Count context files
        for context_file in document.get("context_files", []):
            total += self.count_tokens(context_file.get("content", ""))
            total += self.count_tokens(context_file.get("filename", ""))

        return total

    def truncate_context(
        self,
        document: Dict[str, Any],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Truncate document context to fit within token limit"""
        truncated = {
            "document_id": document.get("document_id"),
            "contributions": list(document.get("contributions", [])),
            "context_files": document.get("context_files", []).copy()
        }

        # Always preserve context files
        context_tokens = sum(
            self.count_tokens(f["content"]) + self.count_tokens(f["filename"])
            for f in truncated["context_files"]
        )

        current_tokens = context_tokens
        contributions = truncated["contributions"]

        # Sort by timestamp (oldest first) to remove oldest first
        contributions_sorted = sorted(
            contributions,
            key=lambda x: x.get("timestamp", ""),
            reverse=False
        )

        # Keep contributions in reverse order (newest first)
        kept_contributions = []
        for contrib in reversed(contributions_sorted):
            contrib_tokens = (
                self.count_tokens(contrib.get("text", "")) +
                self.count_tokens(contrib.get("author", ""))
            )
            if current_tokens + contrib_tokens <= max_tokens:
                kept_contributions.insert(0, contrib)
                current_tokens += contrib_tokens

        truncated["contributions"] = kept_contributions
        return truncated

    def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Call real Gemini API with retry logic and error handling"""
        attempt = 0
        delay = self.RETRY_INITIAL_DELAY

        while attempt < self.RETRY_MAX_ATTEMPTS:
            try:
                logger.debug(f"Calling Gemini API (attempt {attempt + 1}/{self.RETRY_MAX_ATTEMPTS})")

                # Call Gemini API with timeout
                response = self.client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=2000,
                    )
                )

                if response.text:
                    logger.info(f"Gemini API call successful")
                    return {
                        "success": True,
                        "response": response.text,
                        "model": self.model,
                        "finish_reason": getattr(response, 'finish_reason', 'STOP')
                    }
                else:
                    logger.warning(f"Empty response from Gemini API")
                    return {
                        "success": False,
                        "error": "Empty response from API",
                        "finish_reason": getattr(response, 'finish_reason', 'UNKNOWN')
                    }

            except exceptions.ResourceExhausted as e:
                # Rate limit error - retry with backoff
                logger.warning(f"Rate limit hit, retrying in {delay}s: {str(e)}")
                attempt += 1
                if attempt < self.RETRY_MAX_ATTEMPTS:
                    time.sleep(delay)
                    delay = min(delay * self.RETRY_MULTIPLIER, self.RETRY_MAX_DELAY)
                else:
                    logger.error(f"Max retries exceeded for rate limit: {str(e)}")
                    return {"success": False, "error": f"Rate limit after retries: {str(e)}"}

            except exceptions.GoogleAPICallError as e:
                # API error - may be retryable
                logger.error(f"Google API error: {str(e)}")
                if "400" in str(e):  # Bad request - don't retry
                    return {"success": False, "error": f"Bad request: {str(e)}"}
                attempt += 1
                if attempt < self.RETRY_MAX_ATTEMPTS:
                    time.sleep(delay)
                    delay = min(delay * self.RETRY_MULTIPLIER, self.RETRY_MAX_DELAY)
                else:
                    return {"success": False, "error": f"API error after retries: {str(e)}"}

            except Exception as e:
                logger.error(f"Unexpected error calling Gemini API: {str(e)}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        return {"success": False, "error": "Max retries exceeded"}

    def _parse_structured_response(self, response: str) -> Optional[Dict]:
        """Parse structured JSON response from Gemini"""
        try:
            # Find the first JSON object in the response
            # Use JSONDecoder to extract just the first valid JSON object
            from json import JSONDecoder

            # Find the start of JSON (first '{')
            start_idx = response.find('{')
            if start_idx == -1:
                logger.warning("No JSON object found in response")
                return None

            # Use raw_decode to extract just the first JSON object
            decoder = JSONDecoder()
            parsed, end_idx = decoder.raw_decode(response[start_idx:])

            logger.debug(f"Successfully parsed response: {type(parsed)}")
            return parsed

        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse response as JSON: {str(e)}")
            # Try to print the problematic response for debugging
            logger.debug(f"Response text: {response[:500]}...")
            pass
        return None

    def analyze(
        self,
        document: Dict[str, Any],
        mode: str = "outlier"
    ) -> Optional[Dict[str, Any]]:
        """Analyze document with specified mode using real Gemini API"""
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self.VALID_MODES}")

        logger.info(f"Starting analysis with mode: {mode}")

        # Truncate context if needed
        token_count = self.count_tokens_for_document(document)
        if token_count > self.max_tokens * 0.8:
            logger.info(f"Truncating context from {token_count} to {self.max_tokens}")
            document = self.truncate_context(document, self.max_tokens)

        # Generate mode-specific prompt
        prompt = self.templates[mode].generate(document)

        try:
            # Call real Gemini API
            api_response = self._call_gemini_api(prompt)

            if not api_response.get("success"):
                logger.error(f"API call failed: {api_response.get('error')}")
                return None

            # Parse response
            response_text = api_response.get("response", "")
            parsed = self._parse_structured_response(response_text)

            if parsed is None:
                logger.warning("Failed to parse structured response")
                return None

            # Check confidence threshold
            confidence = parsed.get("confidence", 0)
            if confidence >= self.confidence_threshold:
                logger.info(f"Analysis successful with confidence: {confidence}")
                return parsed
            else:
                logger.info(f"Confidence {confidence} below threshold {self.confidence_threshold}")
                return None

        except TimeoutError as e:
            logger.error(f"Analysis timeout: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"error": str(e)}

    def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            logger.info("Testing Gemini API connection...")
            response = self.client.generate_content("Hello")
            logger.info("Gemini API connection successful")
            return True
        except Exception as e:
            logger.error(f"Gemini API connection failed: {str(e)}")
            return False
