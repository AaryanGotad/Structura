from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random

app = FastAPI()

class AlternativePrediction(BaseModel):
    predictedClass: str
    confidence: float


class StructureResult(BaseModel):
    text: str
    predictedClass: str
    confidence: float
    alternative: AlternativePrediction


class AnalyzeResponse(BaseModel):
    success: bool
    data: list[StructureResult]
    rawOutput: str


class AnalyzeRequest(BaseModel):
    text: str


CLASSES = ['BACKGROUND', 'OBJECTIVE', 'METHODS', 'RESULTS', 'CONCLUSIONS']

@app.get('/')
def read_root():
    return {"message": "Welcome to the Text Analysis API!"}

@app.post('/analyze', response_model=AnalyzeResponse)
def analyze_text(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        def confidence(min_val, max_val):
            return round(random.uniform(min_val, max_val), 2)
    
        sentences = [sentence.strip() for sentence in request.text.split('.') if sentence.strip()]
        structure = []
        classIndex = 0
        sentencesPerClass = max(1, (len(sentences) + len(CLASSES) - 1) // len(CLASSES))  # Distribute sentences evenly
    
        for index, sentence in enumerate(sentences):
            if index > 0 and index % sentencesPerClass == 0 and classIndex < len(CLASSES) - 1:
                classIndex += 1
    
            nextClassIndex = (classIndex + 1) % len(CLASSES)
            structure.append({
                'text': sentence,
                'predictedClass': CLASSES[classIndex],
                'confidence': confidence(0.24, 0.75),
                'alternative': {
                    'predictedClass': CLASSES[nextClassIndex],
                    'confidence': confidence(0.15, 0.05)
                }
            })
        return {
            'success': True,
            'data': structure,
            'rawOutput': str(structure)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))