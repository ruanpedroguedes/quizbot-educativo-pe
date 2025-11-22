from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from contextlib import asynccontextmanager
from quiz_system.app import QuizSystem

# Crie a instância do QuizSystem GLOBALMENTE
quiz_system = QuizSystem()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔄 Iniciando Quiz System com processamento de imagens...")
    
    try:
        # ✅ CARREGUE SEU DATASET REAL AQUI
        df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')
        quiz_system.treinamento(df)  # ✅ Agora quiz_system está acessível
        print(f"✅ Dataset carregado com {len(df)} locais!")
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        # Fallback para dados de exemplo
        sample_data = {
            'pergunta': ['Onde fica o Marco Zero?', 'Qual praia mais famosa do Recife?'],
            'contexto': ['O Marco Zero fica no Recife Antigo', 'A Praia de Boa Viagem é a mais famosa'],
            'imagem': ['imagens/marco_zero.jpg', 'imagens/boa_viagem.jpg'],
            'tags': [['historia', 'cultura'], ['praia', 'natureza']]
        }
        df = pd.DataFrame(sample_data)
        quiz_system.treinamento(df)
    
    print("🚀 API do Quiz com imagens iniciada!")
    
    yield  # API rodando
    
    # Shutdown (opcional - limpeza de recursos)
    print("🔴 Parando Quiz System...")

# FastAPI App com lifespan moderno
app = FastAPI(
    title="Quiz Turístico PE - Com Imagens", 
    version="2.0.0",
    lifespan=lifespan
)

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

# ✅ NÃO crie outra instância aqui - use a global

# Endpoints principais
@app.post("/iniciar")
async def iniciar_quiz(request: UsuarioRequest):
    """Inicia o quiz para um usuário"""
    try:
        session_id = quiz_system.criar_ou_recuperar_sessao(request.nome_usuario)
        estatisticas = quiz_system.get_estatisticas_usuario(request.nome_usuario)
        resultado_questao = quiz_system.nova_questao(request.nome_usuario)
        
        if 'erro' in resultado_questao:
            raise HTTPException(status_code=400, detail=resultado_questao['erro'])
        
        # Remove o tensor da imagem da resposta (não é serializável JSON)
        questao_serializavel = resultado_questao['questao'].copy()
        if 'imagem_tensor' in questao_serializavel:
            del questao_serializavel['imagem_tensor']
        
        return {
            "acao": "iniciar", 
            "mensagem": f"Bem-vindo, {request.nome_usuario}!",
            "session_id": session_id, 
            "estatisticas": estatisticas, 
            "questao": questao_serializavel
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar quiz: {str(e)}")

@app.post("/responder")
async def responder_questao(request: RespostaRequest):
    """Valida resposta apenas por texto"""
    try:
        resultado = quiz_system.validar_resposta(request.nome_usuario, request.resposta)
        
        if not resultado['valido']:
            raise HTTPException(status_code=400, detail=resultado['erro'])
        
        if resultado['acertou']:
            estatisticas = quiz_system.get_estatisticas_usuario(request.nome_usuario)
            resultado['estatisticas_atualizadas'] = estatisticas
            
            # Remove tensor da próxima questão se existir
            if resultado.get('proxima_questao') and 'imagem_tensor' in resultado['proxima_questao']:
                resultado['proxima_questao'] = resultado['proxima_questao'].copy()
                del resultado['proxima_questao']['imagem_tensor']
        
        return resultado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar resposta: {str(e)}")

@app.post("/responder-com-imagem")
async def responder_com_imagem(
    nome_usuario: str,
    resposta: str,
    imagem: UploadFile = File(...)
):
    """Valida resposta com texto E imagem do usuário"""
    try:
        # Salva a imagem temporariamente
        temp_path = f"temp_{imagem.filename}"
        with open(temp_path, "wb") as buffer:
            content = await imagem.read()
            buffer.write(content)
        
        # Valida a resposta com a imagem
        resultado = quiz_system.validar_resposta(nome_usuario, resposta, temp_path)
        
        # Limpa arquivo temporário
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if not resultado['valido']:
            raise HTTPException(status_code=400, detail=resultado['erro'])
        
        if resultado['acertou']:
            estatisticas = quiz_system.get_estatisticas_usuario(nome_usuario)
            resultado['estatisticas_atualizadas'] = estatisticas
            
            # Remove tensor da próxima questão se existir
            if resultado.get('proxima_questao') and 'imagem_tensor' in resultado['proxima_questao']:
                resultado['proxima_questao'] = resultado['proxima_questao'].copy()
                del resultado['proxima_questao']['imagem_tensor']
        
        return resultado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar resposta com imagem: {str(e)}")

# ... (coloque os outros endpoints aqui - todos usando a variável global quiz_system)

@app.get("/")
async def root():
    return {
        "mensagem": "Quiz Turístico PE API - Com Processamento de Imagens",
        "versao": "2.0.0",
        "endpoints_principais": [
            "POST /iniciar - Iniciar quiz",
            "POST /responder - Responder com texto", 
            "POST /responder-com-imagem - Responder com texto + imagem",
            "POST /tentar-novamente - Tentar mesma questão",
            "POST /desistir - Desistir e ver resposta",
            "GET /status-imagens - Status do processamento"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)