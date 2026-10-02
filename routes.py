from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import os

from ai_modules.gemini_flash import generate_outline
from ai_modules.gemini_pro import generate_story
from ai_modules.image_generator import generate_image
from ai_modules.layout_builder import build_comic_layout
from ai_modules.exporters import save_pdf

router = APIRouter()

# Jinja2 templates directory configuration
base_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(base_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)


class ComicRequest(BaseModel):
    prompt: str = Field(..., description="Story concept or plot description")
    character_name: str = Field(..., description="Name and description of main character")
    setting: str = Field(..., description="Setting or location")
    tone: str = Field(..., description="Tone (e.g., Heroic, Dark, Humorous, Sci-Fi)")
    art_style: str = Field(..., description="Art style (e.g., Manga, American Comic, Cyberpunk, Watercolor)")


class TestImageRequest(BaseModel):
    image_prompt: str = Field(..., description="Prompt for testing image generation")


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Renders the main creation form page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rendering home page: {str(e)}"
        )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_form(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):
    """
    Captures form data and executes the sequential AI comic generation pipeline.
    Renders comic_preview.html passing layout and pdf_link.
    """
    try:
        print("[PIPELINE] 1/5 Generating outline with Gemini Flash...")
        outline = generate_outline(
            prompt=prompt,
            character=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        print("[PIPELINE] 2/5 Expanding story & dialogue with Gemini Pro...")
        stories = generate_story(outline)

        print("[PIPELINE] 3/5 Generating panel images...")
        images = []
        for panel in stories:
            panel_prompt = panel.get("image_prompt", f"{art_style} style, {character_name} in {setting}")
            img_path = generate_image(panel_prompt)
            images.append(img_path)

        print("[PIPELINE] 4/5 Building comic layout...")
        comic_layout = build_comic_layout(images, stories)

        print("[PIPELINE] 5/5 Exporting PDF...")
        pdf_path = save_pdf(comic_layout)

        return templates.TemplateResponse(
            "comic_preview.html",
            {
                "request": request,
                "layout": comic_layout,
                "pdf_link": pdf_path,
                "character_name": character_name,
                "prompt": prompt
            }
        )
    except Exception as e:
        print(f"[ERROR] Generation pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comic: {str(e)}"
        )


@router.post("/generate-comic/json")
async def generate_comic_json(payload: ComicRequest):
    """
    JSON API endpoint for comic generation.
    Accepts Pydantic model payload and returns structured JSON with layout and PDF link.
    """
    try:
        outline = generate_outline(
            prompt=payload.prompt,
            character=payload.character_name,
            setting=payload.setting,
            tone=payload.tone,
            art_style=payload.art_style
        )
        stories = generate_story(outline)

        images = []
        for panel in stories:
            panel_prompt = panel.get("image_prompt", f"{payload.art_style} style, {payload.character_name} in {payload.setting}")
            img_path = generate_image(panel_prompt)
            images.append(img_path)

        comic_layout = build_comic_layout(images, stories)
        pdf_path = save_pdf(comic_layout)

        return JSONResponse(
            content={
                "status": "success",
                "layout": comic_layout,
                "pdf_path": pdf_path
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API comic generation failed: {str(e)}"
        )


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request):
    """Renders export success confirmation page."""
    try:
        return templates.TemplateResponse("export_success.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rendering export success page: {str(e)}"
        )


@router.post("/test-image")
async def test_image(request: Request):
    """
    Accepts a custom image prompt directly (via JSON body or Form data)
    and returns the generated image path.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            image_prompt = body.get("image_prompt", "Comic superhero in dynamic pose")
        else:
            form = await request.form()
            image_prompt = form.get("image_prompt", "Comic superhero in dynamic pose")

        img_path = generate_image(image_prompt)
        return JSONResponse(content={"status": "success", "image_path": img_path})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test image generation failed: {str(e)}"
        )
