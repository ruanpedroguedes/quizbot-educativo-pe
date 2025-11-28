from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from quiz_system.app import QuizSystem

app = FastAPI(title="QuizBot Educativo PE - Light Version")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar sistema de quiz
quiz_system = QuizSystem()

@app.post("/start-quiz")
async def start_quiz(user_id: str = Form(...)):
    """Inicia um novo quiz"""
    result = quiz_system.start_quiz(user_id)
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Erro desconhecido"))

@app.post("/answer")
async def submit_answer(
    user_id: str = Form(...),
    text_answer: str = Form(...)
):
    """Submete resposta em texto"""
    result = await quiz_system.process_text_answer(user_id, text_answer)
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Erro desconhecido"))

@app.post("/skip-question")
async def skip_question(user_id: str = Form(...)):
    """Pula a pergunta atual"""
    result = quiz_system.skip_question(user_id)
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Erro desconhecido"))

@app.post("/upload")
async def upload_photo(
    user_id: str = Form(...),
    image: UploadFile = File(...)
):
    """Faz upload da foto do local"""
    try:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
        
        image_bytes = await image.read()
        result = await quiz_system.process_image_upload(user_id, image_bytes)
        
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Erro desconhecido"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@app.get("/progress/{user_id}")
async def get_progress(user_id: str):
    """Consulta progresso do usuário"""
    result = quiz_system.get_user_progress(user_id)
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Erro desconhecido"))

@app.get("/leaderboard")
async def get_leaderboard():
    """Retorna o ranking de jogadores"""
    result = quiz_system.get_leaderboard()
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Erro desconhecido"))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "service": "QuizBot PE API"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)