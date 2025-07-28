# recipe-parse

Parse recipes from PDF files using OpenAI's GPT-4o vision model with structured outputs.

## Overview

This tool processes PDF files containing recipe images and extracts structured recipe information including ingredients, instructions, cooking times, allergens, and more. It uses OpenAI's vision capabilities to read recipe content from image-based PDFs and returns structured data using Pydantic models.

## Features

- **PDF Processing**: Handles image-based PDFs without requiring OCR preprocessing
- **Structured Output**: Returns recipe data in a consistent JSON format using Pydantic models
- **Chunked Processing**: Processes PDFs in 2-page chunks to handle large files efficiently
- **Resume Capability**: Tracks progress and can resume interrupted processing
- **Vision-based Extraction**: Uses GPT-4o's vision capabilities to read recipe images

## Requirements

- Python 3.8+
- OpenAI API key
- Required packages:
  - `openai`
  - `pydantic`
  - `python-dotenv`
  - `PyMuPDF` (fitz)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install openai pydantic python-dotenv PyMuPDF
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

```bash
python main.py path/to/your/recipe.pdf
```

## Output Format

The tool extracts recipes into the following structured format:

```json
{
  "title": "Recipe Name",
  "servings": 4,
  "cooking_time": 30,
  "allergens": ["nuts", "dairy"],
  "dietaries": ["vegetarian"],
  "ingredients": [
    {
      "name": "flour",
      "quantity": 2,
      "unit": "cups"
    }
  ],
  "special_equipment": ["stand mixer"],
  "additional": ["notes or tips"],
  "instructions": [
    "Step 1: Mix ingredients",
    "Step 2: Bake for 30 minutes"
  ]
}
```

## How It Works

1. **PDF Chunking**: Splits the PDF into 2-page chunks for processing
2. **Image Conversion**: Converts PDF pages to high-quality PNG images
3. **Vision Processing**: Sends images to GPT-4o for recipe extraction
4. **Structured Output**: Returns data in the defined Pydantic model format
5. **Progress Tracking**: Saves progress to allow resuming interrupted processing

## Resume Functionality

The tool automatically creates a run log file (`{filename}_run_log.json`) to track processing progress. If processing is interrupted, run the same command again to resume from where it left off.

To restart from the beginning, delete the run log file.

## Error Handling

- Validates PDF file existence and format
- Handles API rate limits and errors gracefully
- Cleans up temporary files automatically
- Provides detailed error messages for troubleshooting

## Model Details

- **Model**: GPT-4o (for vision and structured output capabilities)
- **Input**: PDF pages converted to base64-encoded PNG images
- **Output**: Structured JSON conforming to the RecipeCard Pydantic model

## Limitations

- Requires OpenAI API access
- Processing time depends on PDF size and API response times
- Works best with clear, well-formatted recipe images
- May require manual review for complex or unclear recipes
