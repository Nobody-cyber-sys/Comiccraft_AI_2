import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def _get_working_model(api_key: str, preferred_names: list):
    """Dynamically finds an available Gemini model that supports generateContent."""
    genai.configure(api_key=api_key)
    
    # Try preferred names first
    for name in preferred_names:
        try:
            m = genai.GenerativeModel(name)
            # Test model existence with a lightweight prompt or return
            return m
        except Exception:
            continue

    # Fallback: List available models from API
    try:
        available_models = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        print(f"[INFO] Available Gemini models: {available_models}")
        for name in available_models:
            if "flash" in name.lower() or "pro" in name.lower() or "gemini" in name.lower():
                return genai.GenerativeModel(name)
        if available_models:
            return genai.GenerativeModel(available_models[0])
    except Exception as e:
        print(f"[WARNING] Could not list Gemini models: {e}")

    # Default fallback instance
    return genai.GenerativeModel("gemini-1.5-flash-latest")


def generate_outline(prompt: str, character: str, setting: str, tone: str, art_style: str) -> list:
    """
    Generates a structured 5-panel comic outline using Gemini Flash with dynamic model selection.
    Returns a list of dicts with keys: panel_number, title, scene_description, image_prompt.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    system_prompt = f"""
You are a master comic book creator. Create a structured 5-panel comic outline based on:
- Story Prompt: {prompt}
- Main Character: {character}
- Setting: {setting}
- Tone: {tone}
- Art Style: {art_style}

Output EXACTLY a valid JSON array of 5 panel objects. Each object must have these exact keys:
"panel_number" (integer 1 to 5),
"title" (short title string for the panel),
"scene_description" (vivid visual description of action and composition),
"image_prompt" (detailed prompt for AI image generator including character appearance, setting, tone, and art style "{art_style}").

Example JSON structure:
[
  {{
    "panel_number": 1,
    "title": "Panel Title",
    "scene_description": "Detailed scene description...",
    "image_prompt": "Art style {art_style}, detailed prompt..."
  }}
]
Return raw JSON only.
"""

    if not api_key:
        print("[WARNING] GEMINI_API_KEY not found in environment. Using fallback 5-panel outline generator.")
        return _mock_outline(prompt, character, setting, tone, art_style)

    try:
        preferred = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-2.5-flash", "models/gemini-1.5-flash"]
        model = _get_working_model(api_key, preferred)
        
        response = None
        # Try generation with JSON mime type, fallback to standard text
        try:
            response = model.generate_content(
                system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception as e1:
            print(f"[INFO] JSON mode generation attempt failed ({e1}), trying standard generation...")
            try:
                response = model.generate_content(system_prompt)
            except Exception as e2:
                # Try with gemini-pro / alternative model if flash failed
                alt_model = genai.GenerativeModel("gemini-pro")
                response = alt_model.generate_content(system_prompt)

        text = response.text.strip()
        
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n", "", text)
            text = re.sub(r"\n```$", "", text)
            text = text.strip()
            
        outline = json.loads(text)
        
        if isinstance(outline, list) and len(outline) == 5:
            return outline
        elif isinstance(outline, dict) and "panels" in outline:
            return outline["panels"]
        else:
            print("[WARNING] Gemini returned non-standard JSON layout. Using fallback outline.")
            return _mock_outline(prompt, character, setting, tone, art_style)
            
    except Exception as e:
        print(f"[ERROR] Failed to generate outline with Gemini Flash: {e}")
        return _mock_outline(prompt, character, setting, tone, art_style)


def _mock_outline(prompt: str, character: str, setting: str, tone: str, art_style: str) -> list:
    """Fallback 5-panel outline if API key is missing or call fails."""
    return [
        {
            "panel_number": 1,
            "title": "The Awakening",
            "scene_description": f"{character} arrives in {setting}, gazing around with a {tone} expression.",
            "image_prompt": f"Comic panel art, {art_style} style, {character} standing in {setting}, atmospheric lighting, {tone} tone."
        },
        {
            "panel_number": 2,
            "title": "A Strange Discovery",
            "scene_description": f"{character} discovers a mysterious artifact embedded in {setting}.",
            "image_prompt": f"Comic panel art, {art_style} style, close-up of {character} discovering a glowing object in {setting}, high detail."
        },
        {
            "panel_number": 3,
            "title": "The Confrontation",
            "scene_description": f"Shadows loom in {setting} as {character} prepares to face an unforeseen challenge.",
            "image_prompt": f"Comic panel art, {art_style} style, dramatic angle, {character} bracing against shadows in {setting}, action line details."
        },
        {
            "panel_number": 4,
            "title": "Climax of Power",
            "scene_description": f"{character} unleashes hidden potential to resolve the conflict in {setting}.",
            "image_prompt": f"Comic panel art, {art_style} style, epic splash frame, {character} radiating energy in {setting}, vibrant colors."
        },
        {
            "panel_number": 5,
            "title": "New Horizons",
            "scene_description": f"The dust settles over {setting}. {character} smiles, ready for what lies ahead.",
            "image_prompt": f"Comic panel art, {art_style} style, wide shot, {character} standing victorious in {setting}, hopeful sunrise lighting."
        }
    ]
