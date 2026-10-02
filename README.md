# ComicCraft - AI Comic Story Creator

ComicCraft is a full-stack web application that creates custom 5-panel comic stories using Google Gemini models (Flash & Pro), Stable Diffusion, and FastAPI.

## Project Structure
```
comiccraft/
├── main.py
├── routes.py
├── requirements.txt
├── .env
├── ai_modules/
│   ├── __init__.py
│   ├── gemini_flash.py
│   ├── gemini_pro.py
│   ├── image_generator.py
│   ├── layout_builder.py
│   └── exporters.py
├── templates/
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
└── static/
    ├── panels/
    └── exports/
```

## Setup & Execution Instructions

1. **Navigate to the project folder:**
   ```bash
   cd comiccraft
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Edit `.env` and insert your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   HUGGINGFACE_TOKEN=your_huggingface_token_here
   ```

4. **Run the FastAPI server:**
   ```bash
   python main.py
   ```
   Or with Uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the application:**
   Open your browser at `http://127.0.0.1:8000`
