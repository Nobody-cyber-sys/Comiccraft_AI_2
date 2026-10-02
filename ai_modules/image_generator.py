import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

_sd_pipeline = None

def _get_pipeline():
    global _sd_pipeline
    if _sd_pipeline is not None:
        return _sd_pipeline

    import torch
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

    hf_token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
    model_id = "runwayml/stable-diffusion-v1-5"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Initializing Stable Diffusion pipeline on {device}...")

    # Fast check if offline or CPU fallback desired
    if os.getenv("DISABLE_SD", "").lower() in ("true", "1", "yes"):
        raise RuntimeError("Stable Diffusion disabled by environment variable DISABLE_SD.")

    kwargs = {}
    if hf_token:
        kwargs["use_auth_token"] = hf_token

    if device == "cuda":
        kwargs["torch_dtype"] = torch.float16

    pipeline = StableDiffusionPipeline.from_pretrained(model_id, **kwargs)
    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)
    pipeline = pipeline.to(device)

    if device == "cuda":
        pipeline.enable_attention_slicing()

    _sd_pipeline = pipeline
    return _sd_pipeline


def sanitize_filename(prompt: str) -> str:
    """Sanitizes an image prompt string into a valid, safe filename prefix."""
    clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', prompt)
    clean = clean.replace(' ', '_').lower()
    return clean[:30]


def generate_image(image_prompt: str) -> str:
    """
    Generates an illustration using Stable Diffusion or a fallback Pillow renderer.
    Saves image to static/panels/ and returns relative path '/static/panels/<filename>.png'.
    """
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "panels")
    os.makedirs(output_dir, exist_ok=True)

    sanitized_prompt = sanitize_filename(image_prompt)
    unique_id = uuid.uuid4().hex[:8]
    filename = f"panel_{sanitized_prompt}_{unique_id}.png"
    filepath = os.path.join(output_dir, filename)
    relative_path = f"/static/panels/{filename}"

    try:
        pipeline = _get_pipeline()
        print(f"[INFO] Generating image with Stable Diffusion for prompt: '{image_prompt}'")
        image = pipeline(image_prompt, num_inference_steps=25, guidance_scale=7.5).images[0]
        image.save(filepath)
        print(f"[SUCCESS] Image saved to {filepath}")
        return relative_path

    except Exception as e:
        print(f"[WARNING] Stable Diffusion generation unavailable or failed ({e}). Using Pillow panel generator.")
        return _generate_fallback_image(image_prompt, filepath, relative_path)


def _generate_fallback_image(prompt: str, filepath: str, relative_path: str) -> str:
    """Generates a stylized comic panel preview using PIL when SD is unavailable."""
    width, height = 512, 512
    img = Image.new('RGB', (width, height), color=(245, 242, 235))
    draw = ImageDraw.Draw(img)

    # Comic border styling
    draw.rectangle([10, 10, width - 10, height - 10], outline=(20, 20, 20), width=6)
    draw.rectangle([18, 18, width - 18, height - 18], outline=(200, 50, 50), width=2)

    # Background gradient effect simulation
    for y in range(25, height - 25, 4):
        color_val = max(180, 240 - int(y / 3))
        draw.line([(25, y), (width - 25, y)], fill=(color_val, color_val + 5, color_val + 15))

    # Center title & prompt label
    draw.rectangle([40, height // 2 - 60, width - 40, height // 2 + 60], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    
    # Try loading default font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    text_title = "COMIC PANEL ARTWORK"
    draw.text((width // 2 - 60, height // 2 - 40), text_title, fill=(0, 0, 0), font=font)
    
    # Wrap prompt text
    words = prompt.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 35:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_offset = height // 2 - 10
    for line in lines[:3]:
        draw.text((50, y_offset), line, fill=(50, 50, 50), font=font)
        y_offset += 18

    img.save(filepath)
    print(f"[FALLBACK] Generated fallback comic image at {filepath}")
    return relative_path
