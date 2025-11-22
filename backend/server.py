from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from quiz_system.app import QuizSystem
from contextlib import asynccontextmanager

app = FastAPI(
    title="Quiz Turístico PE - API Completa",
    description="API para o jogo de quiz sobre pontos turísticos de Pernambuco",
    version="1.0.0"
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados
class UsuarioRequest(BaseModel):
    nome_usuario: str

class RespostaRequest(BaseModel):
    nome_usuario: str
    resposta: str

class TemaRequest(BaseModel):
    nome_usuario: str
    tema: Optional[str] = None

# Sistema global
quiz_system = QuizSystem()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔄 Iniciando Quiz System...")
    
    # ✅ CARREGUE SEU DATASET REAL AQUI
    try:
        df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')
        quiz_system.treinamento(df)
        print(f"✅ Dataset carregado com {len(df)} locais!")
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        # Fallback para dados de exemplo
        sample_data = {
        'pergunta': ['Onde fica o Marco Zero?', 'Qual praia mais famosa do Recife?'],
        'contexto': ['O Marco Zero fica no Recife Antigo', 'A Praia de Boa Viagem é a mais famosa'],
        'imagem': ['marco_zero.jpg', 'boa_viagem.jpg'],
        'tags': [['historia', 'cultura'], ['praia', 'natureza']]
        }
        df = pd.DataFrame(sample_data)
    quiz_system.treinamento(df)
    print("🚀 API do Quiz iniciada!")
        
    yield  # A API fica rodando aqui
        
    # Shutdown (opcional)
    print("🔴 Parando Quiz System...")

# FastAPI App com lifespan moderno
app = FastAPI(
    title="Quiz Turístico PE", 
    version="1.0.0",
    lifespan=lifespan  # ✅ Método moderno sem warnings
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UsuarioRequest(BaseModel):
    nome_usuario: str

class RespostaRequest(BaseModel):
    nome_usuario: str
    resposta: str

class TemaRequest(BaseModel):
    nome_usuario: str
    tema: Optional[str] = None

# Sistema global
quiz_system = QuizSystem()

# Endpoints (mantenha os mesmos)
@app.post("/iniciar")
async def iniciar_quiz(request: UsuarioRequest):
    session_id = quiz_system.criar_ou_recuperar_sessao(request.nome_usuario)
    estatisticas = quiz_system.get_estatisticas_usuario(request.nome_usuario)
    resultado_questao = quiz_system.nova_questao(request.nome_usuario)
    
    if 'erro' in resultado_questao:
        raise HTTPException(status_code=400, detail=resultado_questao['erro'])
    
    return {
        "acao": "iniciar", "mensagem": f"Bem-vindo, {request.nome_usuario}!",
        "session_id": session_id, "estatisticas": estatisticas, "questao": resultado_questao['questao']
    }

@app.post("/responder")
async def responder_questao(request: RespostaRequest):
    resultado = quiz_system.validar_resposta(request.nome_usuario, request.resposta)
    if not resultado['valido']: raise HTTPException(status_code=400, detail=resultado['erro'])
    
    if resultado['acertou']:
        estatisticas = quiz_system.get_estatisticas_usuario(request.nome_usuario)
        resultado['estatisticas_atualizadas'] = estatisticas
    
    return resultado

@app.post("/tentar-novamente")
async def tentar_novamente(request: UsuarioRequest):
    usuario = quiz_system.users_sessions.get(request.nome_usuario)
    if not usuario: raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not usuario.questao_atual: raise HTTPException(status_code=400, detail="Nenhuma questão ativa")
    
    return {
        "acao": "tentar_novamente", "mensagem": "🔄 Tente novamente!",
        "questao": usuario.questao_atual, "tentativas": usuario.tentativas
    }

@app.post("/desistir")
async def desistir_questao(request: UsuarioRequest):
    resultado = quiz_system.desistir(request.nome_usuario)
    if 'erro' in resultado: raise HTTPException(status_code=400, detail=resultado['erro'])
    
    return {
        "acao": "desistir", "mensagem": "😔 Você desistiu. Resposta correta:",
        "resposta_correta": resultado['resposta_correta'], "proxima_questao": resultado['proxima_questao']
    }

@app.get("/usuarios/{nome_usuario}/estatisticas")
async def get_estatisticas(nome_usuario: str):
    estatisticas = quiz_system.get_estatisticas_usuario(nome_usuario)
    if not estatisticas: raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"acao": "estatisticas", "estatisticas": estatisticas}

@app.get("/ranking")
async def get_ranking():
    ranking = quiz_system.get_ranking()
    return {"acao": "ranking", "ranking": ranking}

@app.get("/")
async def root():
    return {"mensagem": "Quiz Turístico PE API - Use /docs para ver documentação"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)