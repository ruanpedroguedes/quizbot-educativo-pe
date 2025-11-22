from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from contextlib import asynccontextmanager
import os

# ✅ Importe do QuizSystem
from quiz_system.app import QuizSystem

# Lifespan events moderno
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔄 Iniciando Quiz System de Identificação de Imagens...")
    
    try:
        # ✅ CARREGUE SEU DATASET REAL AQUI
        df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')
        quiz_system.treinamento(df)
        print(f"✅ Dataset carregado com {len(df)} locais!")
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        # Fallback para dados de exemplo
        sample_data = {
            'pergunta': ['Onde fica o Marco Zero?', 'Qual praia mais famosa do Recife?'],
            'contexto': [
                'O Marco Zero fica no Recife Antigo e é um dos pontos mais famosos da cidade. Lá tem a vista do rio, bares, feirinhas e muita arte ao redor.',
                'A Praia de Boa Viagem é a mais famosa do Recife, com suas piscinas naturais e calçadão movimentado.'
            ],
            'imagem': ['imagens/marco_zero.jpg', 'imagens/boa_viagem.jpg'],
            'tags': [['historia', 'cultura'], ['praia', 'natureza']]
        }
        df = pd.DataFrame(sample_data)
        quiz_system.treinamento(df)
    
    print("🚀 API do Quiz de Identificação iniciada!")
    
    yield  # API rodando
    
    # Shutdown (opcional - limpeza de recursos)
    print("🔴 Parando Quiz System...")

# Crie a instância do QuizSystem GLOBALMENTE
quiz_system = QuizSystem()

# FastAPI App com lifespan moderno
app = FastAPI(
    title="Quiz Turístico PE - Identificação de Imagens", 
    description="API para quiz onde usuários identificam locais turísticos baseados em imagens",
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

# Endpoints principais para identificação de imagens
@app.post("/quiz/iniciar")
async def iniciar_quiz_identificacao(request: UsuarioRequest):
    """
    🔹 INICIAR QUIZ - Inicia o quiz de identificação de imagens
    Fluxo: Sistema cria sessão → Gera primeira questão com imagem
    """
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
            "acao": "iniciar_identificacao", 
            "mensagem": f"Bem-vindo ao Quiz de Identificação, {request.nome_usuario}!",
            "session_id": session_id, 
            "estatisticas": estatisticas, 
            "questao": questao_serializavel
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar quiz: {str(e)}")

@app.post("/quiz/responder")
async def responder_identificacao(request: RespostaRequest):
    """
    🔹 RESPONDER - Usuário tenta identificar o local da imagem
    Fluxo: Usuário envia resposta → Sistema valida → Retorna resultado + informações do local
    """
    try:
        resultado = quiz_system.validar_resposta_identificacao(request.nome_usuario, request.resposta)
        
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

@app.post("/quiz/tentar-novamente")
async def tentar_novamente_identificacao(request: UsuarioRequest):
    """
    🔹 TENTAR NOVAMENTE - Permite tentar a mesma pergunta novamente
    """
    try:
        usuario = quiz_system.users_sessions.get(request.nome_usuario)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        if not usuario.questao_atual:
            raise HTTPException(status_code=400, detail="Nenhuma questão ativa")
        
        # Remove tensor da imagem para serialização
        questao_serializavel = usuario.questao_atual.copy()
        if 'imagem_tensor' in questao_serializavel:
            del questao_serializavel['imagem_tensor']
        
        return {
            "acao": "tentar_novamente", 
            "mensagem": "🔄 Tente novamente! Observe bem a imagem...",
            "questao": questao_serializavel, 
            "tentativas": usuario.tentativas
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao tentar novamente: {str(e)}")

@app.post("/quiz/desistir")
async def desistir_identificacao(request: UsuarioRequest):
    """
    🔹 DESISTIR - Revela a resposta correta e informações do local
    """
    try:
        resultado = quiz_system.desistir(request.nome_usuario)
        
        if 'erro' in resultado:
            raise HTTPException(status_code=400, detail=resultado['erro'])
        
        # Remove tensor da próxima questão se existir
        if resultado.get('proxima_questao') and 'imagem_tensor' in resultado['proxima_questao']:
            resultado['proxima_questao'] = resultado['proxima_questao'].copy()
            del resultado['proxima_questao']['imagem_tensor']
        
        return {
            "acao": "desistir", 
            "mensagem": "😔 Você desistiu desta questão. Aqui está o local correto:",
            "resposta_correta": resultado['resposta_correta'],
            "informacoes_local": resultado['informacoes_local'],
            "proxima_questao": resultado['proxima_questao']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desistir: {str(e)}")

@app.post("/quiz/nova-questao")
async def nova_questao_identificacao(request: TemaRequest):
    """
    🔹 NOVA QUESTÃO - Gera uma nova questão de identificação
    """
    try:
        resultado = quiz_system.nova_questao(request.nome_usuario, request.tema)
        
        if 'erro' in resultado:
            raise HTTPException(status_code=400, detail=resultado['erro'])
        
        # Remove tensor da imagem para serialização
        questao_serializavel = resultado['questao'].copy()
        if 'imagem_tensor' in questao_serializavel:
            del questao_serializavel['imagem_tensor']
        
        return {
            "acao": "nova_questao",
            "mensagem": "🎯 Nova questão gerada! Tente identificar este local...",
            "questao": questao_serializavel
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar nova questão: {str(e)}")

@app.get("/usuarios/{nome_usuario}/estatisticas")
async def get_estatisticas_usuario(nome_usuario: str):
    """
    🔹 ESTATÍSTICAS - Retorna estatísticas do usuário
    """
    try:
        estatisticas = quiz_system.get_estatisticas_usuario(nome_usuario)
        
        if not estatisticas:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return {
            "acao": "estatisticas",
            "estatisticas": estatisticas
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")

@app.get("/quiz/ranking")
async def get_ranking_quiz():
    """
    🔹 RANKING - Retorna o ranking geral dos jogadores
    """
    try:
        ranking = quiz_system.get_ranking()
        
        return {
            "acao": "ranking",
            "ranking": ranking
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar ranking: {str(e)}")

@app.get("/quiz/status-imagens")
async def get_status_imagens():
    """
    🔹 STATUS IMAGENS - Retorna status do processamento de imagens
    """
    try:
        total_imagens = len(quiz_system.imagens_processadas)
        info_imagens = []
        
        for caminho, tensor in list(quiz_system.imagens_processadas.items())[:5]:  # Primeiras 5
            info_imagens.append({
                'caminho': caminho,
                'shape': str(tuple(tensor.shape)) if hasattr(tensor, 'shape') else 'N/A'
            })
        
        return {
            "total_imagens_processadas": total_imagens,
            "amostra_imagens": info_imagens,
            "mensagem": f"✅ {total_imagens} imagens pré-processadas"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar status: {str(e)}")

@app.post("/quiz/responder-com-imagem")
async def responder_com_imagem_identificacao(
    nome_usuario: str,
    resposta: str,
    imagem: UploadFile = File(...)
):
    """
    🔹 RESPONDER COM IMAGEM - Valida resposta com texto + imagem do usuário (opcional)
    """
    try:
        # Salva a imagem temporariamente
        temp_path = f"temp_{imagem.filename}"
        with open(temp_path, "wb") as buffer:
            content = await imagem.read()
            buffer.write(content)
        
        # Valida a resposta com a imagem (método legado)
        resultado = quiz_system.validar_resposta(nome_usuario, resposta, temp_path)
        
        # Limpa arquivo temporário
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

# Endpoints de saúde e informação
@app.get("/")
async def root():
    return {
        "mensagem": "🎯 Quiz Turístico PE - Identificação de Imagens",
        "versao": "2.0.0",
        "descricao": "Sistema de quiz onde usuários identificam locais turísticos baseados em imagens",
        "endpoints_principais": [
            "POST /quiz/iniciar - Iniciar quiz de identificação",
            "POST /quiz/responder - Tentar identificar o local", 
            "POST /quiz/tentar-novamente - Tentar mesma questão",
            "POST /quiz/desistir - Desistir e ver resposta",
            "POST /quiz/nova-questao - Nova questão",
            "GET /usuarios/{nome}/estatisticas - Estatísticas do usuário",
            "GET /quiz/ranking - Ranking geral",
            "GET /quiz/status-imagens - Status das imagens"
        ]
    }

@app.get("/health")
async def health_check():
    """Endpoint de saúde da API"""
    return {
        "status": "healthy",
        "servico": "Quiz Turístico PE API",
        "versao": "2.0.0",
        "imagens_processadas": len(quiz_system.imagens_processadas),
        "usuarios_ativos": len(quiz_system.users_sessions)
    }

@app.get("/docs")
async def custom_docs():
    """Redireciona para documentação interativa"""
    return {"message": "Acesse /docs para documentação interativa da API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)