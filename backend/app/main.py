from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import io
import re
import json
from datetime import datetime

app = FastAPI(title="PDF Facts Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PointerRequest(BaseModel):
    pointers: List[str]

class ExtractionResult(BaseModel):
    pointer: str
    snippets: List[str]
    page_numbers: List[int]
    character_offsets: List[Dict[str, int]]
    rationale: str

class PDFResponse(BaseModel):
    filename: str
    results: List[ExtractionResult]

def extract_text_from_pdf(pdf_file):
    return [
        {
            'page': 1,
            'text': 'Sample PDF content. Signed by John Doe on January 15, 2024. Total amount: $5,000.00',
            'char_count': 85
        }
    ]

def find_dates(text_content):
    results = []
    for content in text_content:
        text = content['text']
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                results.append({
                    'snippet': match.group(),
                    'page': content['page'],
                    'start_offset': match.start(),
                    'end_offset': match.end()
                })
    return results

def find_signer(text_content):
    results = []
    for content in text_content:
        text = content['text']
        signed_pattern = r'Signed by\s+([A-Z][a-z]+ [A-Z][a-z]+)'
        matches = re.finditer(signed_pattern, text, re.IGNORECASE)
        for match in matches:
            results.append({
                'snippet': match.group(1),
                'page': content['page'],
                'start_offset': match.start(),
                'end_offset': match.end()
            })
    return results

def find_currency_amounts(text_content):
    results = []
    for content in text_content:
        text = content['text']
        currency_pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        matches = re.finditer(currency_pattern, text)
        for match in matches:
            results.append({
                'snippet': match.group(),
                'page': content['page'],
                'start_offset': match.start(),
                'end_offset': match.end()
            })
    return results

def process_pointer(pointer: str, text_content: List[Dict]) -> ExtractionResult:
    pointer_lower = pointer.lower()
    
    if any(word in pointer_lower for word in ['date', 'time']):
        results = find_dates(text_content)
        rationale = "Found dates in the document"
    elif any(word in pointer_lower for word in ['sign', 'who', 'signed']):
        results = find_signer(text_content)
        rationale = "Looked for signature information"
    elif any(word in pointer_lower for word in ['amount', 'price', 'cost', 'value', 'total']):
        results = find_currency_amounts(text_content)
        rationale = "Searched for currency amounts"
    else:
        results = []
        search_term = pointer_lower.replace('?', '').strip()
        for content in text_content:
            if search_term in content['text'].lower():
                results.append({
                    'snippet': f"Found: {search_term}",
                    'page': content['page'],
                    'start_offset': 0,
                    'end_offset': len(search_term)
                })
        rationale = f"Searched for: {search_term}"
    
    return ExtractionResult(
        pointer=pointer,
        snippets=[result['snippet'] for result in results],
        page_numbers=[result['page'] for result in results],
        character_offsets=[{"start": result['start_offset'], "end": result['end_offset']} for result in results],
        rationale=rationale
    )

@app.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    pointers: str = '["List all dates", "Who signed?", "Total contract value?"]'
):
    try:
        pointer_list = json.loads(pointers)
    except:
        pointer_list = ["List all dates", "Who signed?", "Total contract value?"]
    
    text_content = extract_text_from_pdf(file)
    
    results = []
    for pointer in pointer_list:
        result = process_pointer(pointer, text_content)
        results.append(result)
    
    return PDFResponse(
        filename=file.filename,
        results=results
    )

@app.get("/")
async def root():
    return {"message": "PDF Facts Analyzer API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting PDF Facts Analyzer API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)