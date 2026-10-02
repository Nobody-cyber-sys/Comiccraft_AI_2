def build_comic_layout(images: list, stories: list) -> list:
    """
    Merges image file paths and story data into a structured final layout list.
    
    Args:
        images: List of string file paths for panel images.
        stories: List of panel dictionaries containing text content.

    Returns:
        List of merged panel layout dictionaries.
    """
    layout = []
    
    for i, story in enumerate(stories):
        image_path = images[i] if i < len(images) else ""
        
        panel_layout = {
            "panel_number": story.get("panel_number", i + 1),
            "title": story.get("title", f"Panel {i + 1}"),
            "scene_description": story.get("scene_description", ""),
            "image_prompt": story.get("image_prompt", ""),
            "image_path": image_path,
            "narration": story.get("narration", ""),
            "dialogue": story.get("dialogue", "")
        }
        layout.append(panel_layout)
        
    return layout
