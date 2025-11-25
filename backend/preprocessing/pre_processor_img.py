# Importando Bibliotecas LEVES
import numpy as np
from PIL import Image 
from sklearn.metrics.pairwise import cosine_similarity
import requests
import os
from io import BytesIO

class ImageProcessor:
    def __init__(self):
        self.target_size = (224, 224)
        # Parâmetros de normalização (mesmos do ImageNet para compatibilidade)
        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])
        print("✅ ImageProcessor inicializado (versão leve)")
    
    def process_single_image(self, img_path):
        """
        Processa uma única imagem - suporta URLs e arquivos locais
        """
        try:
            # Verifica se é uma URL
            if img_path.startswith('http'):
                return self._process_url_image(img_path)
            else:
                return self._process_local_image(img_path)
        except Exception as e:
            print(f"❌ Erro ao processar {img_path}: {e}")
            return None
        
    def _process_url_image(self, url):
        #Processa imagem a partir de URL"""
        try:
            print(f"🌐 Baixando imagem da URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Abre a imagem do conteúdo da resposta
            img = Image.open(BytesIO(response.content)).convert('RGB')
            return self._process_image_object(img)
            
        except Exception as e:
            print(f"❌ Erro ao baixar/processar URL {url}: {e}")
            return None
    
    def _process_local_image(self, file_path):
        """Processa imagem a partir de arquivo local"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ Arquivo não encontrado: {file_path}")
                return None
            
            img = Image.open(file_path).convert('RGB')
            return self._process_image_object(img)
            
        except Exception as e:
            print(f"❌ Erro ao processar arquivo local {file_path}: {e}")
            return None
        
    def _process_image_object(self, img):
        """Processa o objeto PIL Image"""
        try:
            # Redimensiona
            img_resized = img.resize(self.target_size)
            
            # Converte para numpy array
            img_array = np.array(img_resized, dtype=np.float32)
            
            # Normaliza [0, 1]
            img_array = img_array / 255.0
            
            # Normaliza com mean/std
            img_array = (img_array - self.mean) / self.std
            
            # Muda para formato (C, H, W)
            img_array = np.transpose(img_array, (2, 0, 1))
            
            # Adiciona dimensão do batch
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
            
        except Exception as e:
            print(f"❌ Erro no processamento da imagem: {e}")
            return None

    def calculate_similarity(self, img_array1, img_array2): 
        #Calcula similaridade entre duas imagens usando cosine similarity
        try:
            # Verifica se os arrays não são None
            if img_array1 is None or img_array2 is None:
                return 0.0
            
            # Achata os arrays para vetores 1D
            flat1 = img_array1.flatten()
            flat2 = img_array2.flatten()
            
            # Calcula similaridade do cosseno
            similarity = cosine_similarity([flat1], [flat2])[0][0]
            return similarity
            
        except Exception as e:
            print(f"❌ Erro no cálculo de similaridade: {e}")
            return 0.0