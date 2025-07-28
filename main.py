#!/usr/bin/env python3

import os
import sys
import argparse
import json
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, PositiveInt
import fitz  # PyMuPDF for PDF processing

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please create a .env file with your API key.")

prompt = """process the attached file, extract verbatim info to fill in the following json structure for each recipe you find.
    """

client = OpenAI(api_key=api_key)

class Ingredient(BaseModel):
    name: str
    quantity: PositiveInt
    unit: str

class RecipeCard(BaseModel):
    title: str
    servings: int
    cooking_time: int
    allergens: list[str]
    dietaries: list[str]
    ingredients: list[Ingredient]
    special_equipment: list[str]
    additional: list[str]
    instructions: list[str]

def get_run_log_path(pdf_path):
    """Generate run log file path based on PDF file name"""
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    return f"{base_name}_run_log.json"

def load_run_log(log_path):
    """Load the run log to get the last processed page"""
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                data = json.load(f)
                return data.get('last_processed_page', 0), data.get('completed', False)
        except (json.JSONDecodeError, KeyError):
            return 0, False
    return 0, False

def save_run_log(log_path, last_processed_page, completed=False):
    """Save the current progress to run log"""
    data = {
        'last_processed_page': last_processed_page,
        'completed': completed
    }
    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)

def extract_pdf_pages(pdf_path, start_page, end_page):
    """Extract specific pages from PDF and save as temporary PDF"""
    doc = fitz.open(pdf_path)
    temp_doc = fitz.open()
    
    for page_num in range(start_page - 1, min(end_page, doc.page_count)):
        temp_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
    
    temp_path = f"temp_chunk_{start_page}_{end_page}.pdf"
    temp_doc.save(temp_path)
    temp_doc.close()
    doc.close()
    
    return temp_path

def get_pdf_page_count(pdf_path):
    """Get total number of pages in PDF"""
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    doc.close()
    return page_count

def create_file(file_path):
    """Create a file with the Files API"""
    with open(file_path, "rb") as file_content:
        result = client.files.create(
            file=file_content,
            purpose="assistants",
        )
        return result.id

def process_pdf_chunk(chunk_path, chunk_start, chunk_end):
    """Process a single PDF chunk"""
    try:
        file_id = create_file(chunk_path)

        response = client.responses.parse(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": "Extract the event information."},
                {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_file",  # Use input_document for PDFs
                        "file_id": file_id,
                    }
                ]}],
                text_format=RecipeCard
        )

        print(f"\n=== Pages {chunk_start}-{chunk_end} ===")
        print(response.output_text)
        
        # Clean up the uploaded file
        client.files.delete(file_id)
        
        return True
        
    except Exception as e:
        print(f"Error processing pages {chunk_start}-{chunk_end}: {e}")
        return False

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Analyze a PDF using OpenAI's vision model in 2-page chunks")
    parser.add_argument("pdf_file", help="Path to the PDF file to analyze")
    
    args = parser.parse_args()
    
    # Check if the file exists
    if not os.path.exists(args.pdf_file):
        print(f"Error: File '{args.pdf_file}' not found.")
        sys.exit(1)
    
    # Check if it's a PDF file
    if not args.pdf_file.lower().endswith('.pdf'):
        print(f"Error: File '{args.pdf_file}' is not a PDF file.")
        sys.exit(1)
    
    try:
        # Get run log path and load previous progress
        log_path = get_run_log_path(args.pdf_file)
        last_processed_page, completed = load_run_log(log_path)
        
        if completed:
            print(f"PDF '{args.pdf_file}' has already been completely processed.")
            print("Delete the run log file to reprocess from the beginning.")
            return
        
        # Get total page count
        total_pages = get_pdf_page_count(args.pdf_file)
        print(f"Total pages in PDF: {total_pages}")
        
        if last_processed_page > 0:
            print(f"Resuming from page {last_processed_page + 1}")
        else:
            print("Starting from the beginning")
        
        # Process in 2-page chunks
        current_page = last_processed_page + 1
        
        while current_page <= total_pages:
            chunk_start = current_page
            chunk_end = min(current_page + 1, total_pages)
            
            print(f"\nProcessing pages {chunk_start}-{chunk_end}...")
            
            # Extract pages to temporary PDF
            temp_chunk_path = extract_pdf_pages(args.pdf_file, chunk_start, chunk_end)
            
            try:
                # Process the chunk
                success = process_pdf_chunk(temp_chunk_path, chunk_start, chunk_end)
                
                if success:
                    # Update progress
                    save_run_log(log_path, chunk_end)
                    current_page = chunk_end + 1
                else:
                    print(f"Failed to process pages {chunk_start}-{chunk_end}")
                    break
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_chunk_path):
                    os.remove(temp_chunk_path)
        
        # Mark as completed if we processed all pages
        if current_page > total_pages:
            save_run_log(log_path, total_pages, completed=True)
            print(f"\n✅ Successfully processed all {total_pages} pages!")
            print(f"Run log saved to: {log_path}")
        
    except FileNotFoundError:
        print(f"Error: Could not open file '{args.pdf_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()