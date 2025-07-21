from openai import OpenAI
from anthropic import Anthropic
from typing import Dict, List, Optional
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            
        if self.anthropic_api_key:
            self.anthropic = Anthropic(api_key=self.anthropic_api_key)
        else:
            self.anthropic = None
    
    async def generate_summary(self, content: str, language: str = "en") -> Dict:
        prompt = self._build_summary_prompt(content, language)
        
        try:
            if self.model.startswith("gpt") and self.openai_api_key:
                return await self._generate_with_openai(prompt, "summary")
            elif self.model.startswith("claude") and self.anthropic_api_key:
                return await self._generate_with_claude(prompt, "summary")
            else:
                logger.error("No valid LLM API configured")
                return self._default_summary()
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return self._default_summary()
    
    async def generate_analysis(self, content: str, title: str) -> Dict:
        prompt = self._build_analysis_prompt(content, title)
        
        try:
            if self.model.startswith("gpt") and self.openai_api_key:
                return await self._generate_with_openai(prompt, "analysis")
            elif self.model.startswith("claude") and self.anthropic_api_key:
                return await self._generate_with_claude(prompt, "analysis")
            else:
                logger.error("No valid LLM API configured")
                return self._default_analysis()
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return self._default_analysis()
    
    def _build_summary_prompt(self, content: str, language: str) -> str:
        lang_instruction = "日本語で" if language == "ja" else "in English"
        
        return f"""
        Please summarize the following article {lang_instruction}.
        
        Article: {content[:3000]}
        
        Provide:
        1. A concise summary (2-3 sentences)
        2. 3-5 key points
        
        Format the response as JSON:
        {{
            "summary": "...",
            "key_points": ["point1", "point2", ...]
        }}
        """
    
    def _build_analysis_prompt(self, content: str, title: str) -> str:
        return f"""
        Analyze the following article titled "{title}":
        
        {content[:3000]}
        
        Provide the following analysis in JSON format:
        
        1. vocabulary: Extract 5-10 difficult English words (TOEIC 800+ level) with Japanese explanations
        2. context: Explain the background and context of this news (in Japanese, 200-300 characters)
        3. impact: Analyze the potential future impact (in Japanese, around 500 characters)
        4. blog_titles: Suggest 3 catchy titles for blog/SNS posts about this news (in Japanese)
        
        Format:
        {{
            "vocabulary": {{"word1": "Japanese explanation", ...}},
            "context": "背景説明...",
            "impact": "今後の影響...",
            "blog_titles": ["title1", "title2", "title3"]
        }}
        """
    
    async def _generate_with_openai(self, prompt: str, task_type: str) -> Dict:
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes news articles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
            data["model"] = self.model
            return data
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return self._default_summary() if task_type == "summary" else self._default_analysis()
    
    async def _generate_with_claude(self, prompt: str, task_type: str) -> Dict:
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        try:
            data = json.loads(content)
            data["model"] = self.model
            return data
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return self._default_summary() if task_type == "summary" else self._default_analysis()
    
    def _default_summary(self) -> Dict:
        return {
            "summary": "Summary generation failed",
            "key_points": [],
            "model": "none"
        }
    
    def _default_analysis(self) -> Dict:
        return {
            "vocabulary": {},
            "context": "Analysis generation failed",
            "impact": "Analysis generation failed",
            "blog_titles": [],
            "model": "none"
        }