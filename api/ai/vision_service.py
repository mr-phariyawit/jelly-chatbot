"""
Vision Service
Handles image analysis using Gemini Vision API.
"""

import base64
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VisionService:
    """Processes images using Gemini Vision API."""

    def __init__(self, gemini_client=None):
        self.gemini = gemini_client

    def analyze_image(self, image_content: bytes, mime_type: str = "image/jpeg") -> str:
        """
        Analyze an image and return a text description.
        Used for error screenshots, general photos, etc.
        """
        if not self.gemini:
            raise RuntimeError("Gemini client not initialized")

        vision_prompt = """
        Analyze this image. If it shows an error message or technical issue, extract the key error text and describe the problem concisely.
        If it's just a general photo, describe what it is.
        Output format: [Analysis] <description>
        """

        image_b64 = base64.b64encode(image_content).decode("utf-8")

        url = f"{self.gemini.base_url}/models/{self.gemini.model}:generateContent?key={self.gemini.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": vision_prompt},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}}
                ]
            }]
        }

        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            raise Exception(f"Vision API error: {response.status_code}")

        data = response.json()
        analysis = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return analysis

    def process_image_with_rag(
        self, image_content: bytes, rag_context: str, mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Full pipeline: analyze image → search RAG → generate response.
        Returns dict with message and escalation flag.
        """
        try:
            # 1. Vision Analysis
            image_analysis = self.analyze_image(image_content, mime_type)
            logger.info(f"Image Analysis: {image_analysis[:100]}")

            # 2. Generate final answer with RAG context
            final_prompt = f"""
            User sent an image.
            Image Analysis: {image_analysis}

            Relevant Knowledge Base Context:
            {rag_context}

            Instruction:
            Based on the image analysis and the knowledge base, provide a solution or helpful response to the user.
            If the knowledge base has a specific fix for this error, provide it clearly.
            Response in Thai Language.
            """

            final_response = self.gemini.generate_content(final_prompt)
            return {
                "message": final_response,
                "should_escalate": "contact admin" in final_response.lower(),
                "image_analysis": image_analysis,
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                "message": "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลรูปภาพ",
                "should_escalate": True,
            }
