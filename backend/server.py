from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from contextlib import asynccontextmanager
import os
import mimetypes

# ✅ Importe do QuizSystem
from quiz_system.app import QuizSystem

# ✅ Configurações
MODEL_PATH = "backend/modelos/tourist_model.pkl"
API_BASE_URL = "http://localhost:8000"

# Lifespan events moderno
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔄 Iniciando Quiz System de Identificação de Imagens...")
    
    # ✅ CORREÇÃO: Inicializar QuizSystem com configurações
    if os.path.exists(MODEL_PATH):
        print("✅ Modelo .pkl encontrado - inicializando com classificação")
        app.state.quiz_system = QuizSystem(model_path=MODEL_PATH, api_base_url=API_BASE_URL)
    else:
        print("⚠️  Modelo .pkl não encontrado - inicializando em modo legado")
        app.state.quiz_system = QuizSystem(api_base_url=API_BASE_URL)
    
    try:
        # ✅ CARREGUE SEU DATASET REAL AQUI
        df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')
        app.state.quiz_system.treinamento(df)
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
            'imagem': ['backend/imagens/marco_zero_1.jpeg', 'backend/imagens/boa_viagem_1.jpeg'],
            'tags': [['historia', 'cultura'], ['praia', 'natureza']]
        }
        df = pd.DataFrame(sample_data)
        app.state.quiz_system.treinamento(df)
    
    # ✅ Criar diretórios necessários
    os.makedirs("backend/imagens", exist_ok=True)
    os.makedirs("backend/uploads", exist_ok=True)
    
    print("🚀 API do Quiz de Identificação iniciada!")
    
    yield  # API rodando
    
    # Shutdown (opcional - limpeza de recursos)
    print("🔴 Parando Quiz System...")

# FastAPI App com lifespan moderno
app = FastAPI(
    title="Quiz Turístico PE - Identificação de Imagens", 
    description="API para quiz onde usuários identificam locais turísticos baseados em imagens",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Função auxiliar para acessar o quiz_system
def get_quiz_system():
    return app.state.quiz_system

# Modelos de dados
class UsuarioRequest(BaseModel):
    nome_usuario: str

class RespostaRequest(BaseModel):
    nome_usuario: str
    resposta: str

class TemaRequest(BaseModel):
    nome_usuario: str
    tema: Optional[str] = None

class ModelTestRequest(BaseModel):
    contexto: str
    tags: Optional[list] = None

# ✅ ENDPOINT PARA SERVIR IMAGENS LOCAIS
@app.get("/imagens/{caminho_imagem:path}")
async def servir_imagem(caminho_imagem: str):
    """
    🔹 SERVE IMAGENS LOCAIS - Serve imagens do sistema de arquivos local
    """
    try:
        # Lista de diretórios onde procurar imagens
        diretorios_imagens = [
            "backend/imagens",
            "backend/dataset", 
            "backend/imagens_treinamento",
            "backend/uploads",
            "imagens"
        ]
        
        # Tenta encontrar a imagem em algum dos diretórios
        for diretorio in diretorios_imagens:
            caminho_completo = os.path.join(diretorio, caminho_imagem)
            if os.path.exists(caminho_completo):
                # Detecta o tipo MIME automaticamente
                mime_type, _ = mimetypes.guess_type(caminho_completo)
                if mime_type is None:
                    mime_type = "image/jpeg"  # Fallback
                
                print(f"✅ Servindo imagem: {caminho_completo}")
                return FileResponse(
                    caminho_completo,
                    media_type=mime_type,
                    filename=os.path.basename(caminho_imagem)
                )
        
        # Se não encontrou, tenta o caminho absoluto
        if os.path.exists(caminho_imagem):
            mime_type, _ = mimetypes.guess_type(caminho_imagem)
            return FileResponse(
                caminho_imagem,
                media_type=mime_type or "image/jpeg",
                filename=os.path.basename(caminho_imagem)
            )
        
        raise HTTPException(status_code=404, detail=f"Imagem não encontrada: {caminho_imagem}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao servir imagem: {str(e)}")

# ✅ NOVO ENDPOINT - Listar imagens disponíveis
@app.get("/imagens/")
async def listar_imagens():
    """Lista todas as imagens disponíveis localmente"""
    imagens_encontradas = []
    diretorios = ["backend/imagens", "backend/dataset", "backend/imagens_treinamento"]
    
    for diretorio in diretorios:
        if os.path.exists(diretorio):
            for root, dirs, files in os.walk(diretorio):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        caminho_relativo = os.path.relpath(os.path.join(root, file), diretorio)
                        imagens_encontradas.append({
                            'nome': file,
                            'caminho': caminho_relativo,
                            'url': f"/imagens/{caminho_relativo}",
                            'diretorio': diretorio
                        })
    
    return {
        "total_imagens": len(imagens_encontradas),
        "imagens": imagens_encontradas[:20]  # Limita a 20 para não sobrecarregar
    }

# ✅ NOVO ENDPOINT - Status do sistema
@app.get("/system/status")
async def get_system_status():
    """Retorna informações sobre o modo de operação do sistema"""
    quiz_system = get_quiz_system()
    
    status = {
        "modo_operacao": "modelo_pkl" if quiz_system.classification_model else "legado",
        "versao": "3.0.0",
        "modelo_carregado": quiz_system.classification_model is not None,
        "total_locais": len(quiz_system.df) if quiz_system.df else 0,
        "usuarios_ativos": len(quiz_system.users_sessions),
        "imagens_processadas": len(quiz_system.imagens_processadas),
        "caminho_modelo": MODEL_PATH,
        "modelo_existe": os.path.exists(MODEL_PATH)
    }
    
    return status

# ✅ NOVO ENDPOINT - Testar o modelo
@app.post("/model/test")
async def test_model(request: ModelTestRequest):
    """Testa o modelo .pkl com um contexto"""
    quiz_system = get_quiz_system()
    
    if not quiz_system.classification_model:
        raise HTTPException(status_code=400, detail="Modelo .pkl não carregado")
    
    try:
        resultado = quiz_system.classify_with_model(request.contexto, request.tags)
        if resultado:
            return {
                "contexto": request.contexto,
                "tags": request.tags,
                "predicao": resultado,
                "status": "sucesso"
            }
        else:
            return {
                "contexto": request.contexto,
                "tags": request.tags,
                "predicao": None,
                "status": "erro",
                "mensagem": "Modelo não retornou resultado"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no modelo: {str(e)}")

# Endpoints principais para identificação de imagens
@app.post("/quiz/iniciar")
async def iniciar_quiz_identificacao(request: UsuarioRequest):
    """
    🔹 INICIAR QUIZ - Inicia o quiz de identificação de imagens
    Fluxo: Sistema cria sessão → Gera primeira questão com imagem
    """
    try:
        quiz_system = get_quiz_system()
        session_id = quiz_system.criar_ou_recuperar_sessao(request.nome_usuario)
        estatisticas = quiz_system.get_estatisticas_usuario(request.nome_usuario)
        resultado_questao = quiz_system.nova_questao(request.nome_usuario)
        
        if 'erro' in resultado_questao:
            raise HTTPException(status_code=400, detail=resultado_questao['erro'])
        
        # Remove o tensor da imagem da resposta (não é serializável JSON)
        questao_serializavel = resultado_questao['questao'].copy()
        if 'imagem_tensor' in questao_serializavel:
            del questao_serializavel['imagem_tensor']
        
        # ✅ Adiciona modo de operação
        modo = resultado_questao.get('modo', 'legado')
        
        return {
            "acao": "iniciar_identificacao", 
            "mensagem": f"Bem-vindo ao Quiz de Identificação, {request.nome_usuario}!",
            "session_id": session_id, 
            "estatisticas": estatisticas, 
            "questao": questao_serializavel,
            "modo_operacao": modo
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
        quiz_system = get_quiz_system()
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
        quiz_system = get_quiz_system()
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
        quiz_system = get_quiz_system()
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
        quiz_system = get_quiz_system()
        resultado = quiz_system.nova_questao(request.nome_usuario, request.tema)
        
        if 'erro' in resultado:
            raise HTTPException(status_code=400, detail=resultado['erro'])
        
        # Remove tensor da imagem para serialização
        questao_serializavel = resultado['questao'].copy()
        if 'imagem_tensor' in questao_serializavel:
            del questao_serializavel['imagem_tensor']
        
        # ✅ Adiciona modo de operação
        modo = resultado.get('modo', 'legado')
        
        return {
            "acao": "nova_questao",
            "mensagem": "🎯 Nova questão gerada! Tente identificar este local...",
            "questao": questao_serializavel,
            "modo_operacao": modo
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar nova questão: {str(e)}")

@app.get("/usuarios/{nome_usuario}/estatisticas")
async def get_estatisticas_usuario(nome_usuario: str):
    """
    🔹 ESTATÍSTICAS - Retorna estatísticas do usuário
    """
    try:
        quiz_system = get_quiz_system()
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
        quiz_system = get_quiz_system()
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
        quiz_system = get_quiz_system()
        total_imagens = len(quiz_system.imagens_processadas)
        info_imagens = []
        
        for caminho, tensor in list(quiz_system.imagens_processadas.items())[:5]:
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
        quiz_system = get_quiz_system()
        
        # Salva a imagem temporariamente
        temp_path = f"backend/uploads/temp_{imagem.filename}"
        os.makedirs("backend/uploads", exist_ok=True)
        
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
    quiz_system = get_quiz_system()
    
    modo = "modelo_pkl" if quiz_system.classification_model else "legado"
    modelo_status = "✅ Carregado" if quiz_system.classification_model else "❌ Não carregado"
    
    return {
        "mensagem": "🎯 Quiz Turístico PE - Identificação de Imagens",
        "versao": "3.0.0",
        "modo_operacao": modo,
        "modelo_status": modelo_status,
        "descricao": "Sistema de quiz onde usuários identificam locais turísticos baseados em imagens",
        "endpoints_principais": [
            "GET /system/status - Status do sistema",
            "POST /model/test - Testar modelo .pkl",
            "GET /imagens/ - Listar imagens disponíveis",
            "POST /quiz/iniciar - Iniciar quiz de identificação",
            "POST /quiz/responder - Tentar identificar o local", 
            "POST /quiz/tentar-novamente - Tentar mesma questão",
            "POST /quiz/desistir - Desistir e ver resposta",
            "POST /quiz/nova-questao - Nova questão",
            "GET /usuarios/{nome}/estatisticas - Estatísticas do usuário",
            "GET /quiz/ranking - Ranking geral"
        ]
    }

@app.get("/health")
async def health_check():
    """Endpoint de saúde da API"""
    quiz_system = get_quiz_system()
    
    return {
        "status": "healthy",
        "servico": "Quiz Turístico PE API",
        "versao": "3.0.0",
        "modo_operacao": "modelo_pkl" if quiz_system.classification_model else "legado",
        "imagens_processadas": len(quiz_system.imagens_processadas),
        "usuarios_ativos": len(quiz_system.users_sessions),
        "modelo_carregado": quiz_system.classification_model is not None,
        "modelo_existe": os.path.exists(MODEL_PATH)
    }

@app.get("/docs")
async def custom_docs():
    """Redireciona para documentação interativa"""
    return {"message": "Acesse /docs para documentação interativa da API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)