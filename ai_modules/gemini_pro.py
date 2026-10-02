import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def _get_working_model(api_key: str, preferred_names: list):
    """Dynamically finds an available Gemini model for story expansion."""
    genai.configure(api_key=api_key)
    
    for name in preferred_names:
        try:
            return genai.GenerativeModel(name)
        except Exception:
            continue

    try:
        available_models = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        for name in available_models:
            if "pro" in name.lower() or "flash" in name.lower() or "gemini" in name.lower():
                return genai.GenerativeModel(name)
        if available_models:
            return genai.GenerativeModel(available_models[0])
    except Exception as e:
        print(f"[WARNING] Could not list Gemini models: {e}")

    return genai.GenerativeModel("gemini-1.5-pro-latest")


def generate_story(outline: list) -> list:
    """
    Uses Gemini Pro / available Gemini model to expand the comic outline into full narration and dialogues for each panel.
    Returns the outline list with added 'narration' and 'dialogue' fields.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    system_prompt = f"""
You are an expert comic script writer. Given the following 5-panel comic outline, write engaging comic narration captions and character dialogue for each panel.

Outline Input:
{json.dumps(outline, indent=2)}

Return a JSON array of the exact 5 panels, preserving existing fields ('panel_number', 'title', 'scene_description', 'image_prompt') and adding:
- "narration": (Captivating comic book narrator box text)
- "dialogue": (Character dialogue formatted like 'CHARACTER NAME: "Speech..."' or empty string if silent)

Output raw JSON array only.
"""

    if not api_key:
        print("[WARNING] GEMINI_API_KEY not found in environment. Using fallback story generator.")
        return _mock_story(outline)

    try:
        preferred = ["gemini-1.5-pro-latest", "gemini-1.5-pro", "gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-flash"]
        model = _get_working_model(api_key, preferred)

        response = None
        try:
            response = model.generate_content(
                system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception:
            response = model.generate_content(system_prompt)

        text = response.text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n", "", text)
            text = re.sub(r"\n```$", "", text)
            text = text.strip()

        story_data = json.loads(text)

        if isinstance(story_data, list) and len(story_data) > 0:
            updated_outline = []
            for i, panel in enumerate(outline):
                new_panel = dict(panel)
                if i < len(story_data):
                    new_panel["narration"] = story_data[i].get("narration", f"Panel {i+1} unfolds...")
                    new_panel["dialogue"] = story_data[i].get("dialogue", "")
                else:
                    new_panel["narration"] = f"Panel {i+1} unfolds..."
                    new_panel["dialogue"] = ""
                updated_outline.append(new_panel)
            return updated_outline
        else:
            return _mock_story(outline)

    except Exception as e:
        print(f"[ERROR] Failed to generate story with Gemini Pro: {e}")
        return _mock_story(outline)


def _mock_story(outline: list) -> list:
    """Fallback story narration and dialogue generator."""
    updated = []
    mock_texts = [
        ("The journey begins under an ominous sky.", "HERO: 'There's no turning back now.'"),
        ("A sudden shimmer reveals a secret hidden for centuries.", "HERO: 'What is this power...?'"),
        ("Tension grips the air as unexpected shadows close in.", "VOICE FROM SHADOWS: 'You should not have come here!'"),
        ("Surging with newfound resolve, the ultimate energy unleashes!", "HERO: 'I won't let you stop me!'"),
        ("As silence returns, a brand new adventure dawns.", "HERO: 'This is only the beginning.'")
    ]
    
    for i, panel in enumerate(outline):
        item = dict(panel)
        narration, dialogue = mock_texts[i % len(mock_texts)]
        item["narration"] = narration
        item["dialogue"] = dialogue
        updated.append(item)
    return updated
