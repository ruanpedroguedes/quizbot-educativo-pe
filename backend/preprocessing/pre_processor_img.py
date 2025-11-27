import cv2
import numpy as np
from PIL import Image
import io
import os
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input

class EfficientImageProcessor:
    def __init__(self):
        # EfficientNet-B0 - ~20MB, muito eficiente
        self.model = EfficientNetB0(weights='imagenet', include_top=False, pooling='avg')
        self.image_cache = {}
        self.threshold = 0.7  # Threshold mais alto para melhor precisão
        print("✅ EfficientNet-B0 carregado com sucesso!")
    
    def load_local_image(self, image_path: str) -> np.ndarray:
        """Carrega imagem do sistema de arquivos local"""
        try:
            if image_path in self.image_cache:
                return self.image_cache[image_path]
            
            print(f"🖼️  Carregando imagem local: {image_path}")
            
            if not os.path.exists(image_path):
                print(f"❌ Arquivo não encontrado: {image_path}")
                return None
            
            image = Image.open(image_path)
            image_array = np.array(image.convert('RGB'))
            
            self.image_cache[image_path] = image_array
            return image_array
            
        except Exception as e:
            print(f"❌ Erro ao carregar imagem {image_path}: {e}")
            return None
    
    def extract_features(self, image_array: np.ndarray) -> np.ndarray:
        """Extrai features usando EfficientNet-B0"""
        try:
            # Redimensionar para 224x224 (tamanho do EfficientNet)
            image_resized = cv2.resize(image_array, (224, 224))
            
            # Pré-processamento específico do EfficientNet
            image_preprocessed = preprocess_input(image_resized)
            
            # Adicionar dimensão do batch
            image_batch = np.expand_dims(image_preprocessed, axis=0)
            
            # Extrair features (1.280 dimensões)
            features = self.model.predict(image_batch, verbose=0)
            return features.flatten()
            
        except Exception as e:
            print(f"❌ Erro ao extrair features com EfficientNet: {e}")
            return None
    
    async def validate_user_image(self, user_image_bytes: bytes, correct_place_data: dict) -> bool:
        """Valida se a imagem do usuário corresponde ao local correto usando EfficientNet"""
        try:
            # Converter bytes da imagem do USUÁRIO para array
            user_image = Image.open(io.BytesIO(user_image_bytes))
            user_array = np.array(user_image.convert('RGB'))
            
            print(f"📸 EfficientNet processando imagem: {user_array.shape}")
            
            # Extrair features da imagem do usuário
            user_features = self.extract_features(user_array)
            
            if user_features is None:
                print("❌ Falha ao extrair features da imagem do usuário")
                return False
            
            # Obter caminhos das imagens de referência do dataset
            reference_paths = self._get_local_image_paths(correct_place_data)
            
            if not reference_paths:
                print("❌ Nenhuma imagem de referência encontrada")
                return False
            
            print(f"📍 Comparando com {len(reference_paths)} imagens de referência")
            
            # Comparar com cada imagem de referência
            best_similarity = 0
            successful_comparisons = 0
            
            for i, ref_path in enumerate(reference_paths):
                ref_image = self.load_local_image(ref_path)
                if ref_image is not None:
                    ref_features = self.extract_features(ref_image)
                    
                    if ref_features is not None:
                        # Calcular similaridade do cosseno
                        similarity = cosine_similarity([user_features], [ref_features])[0][0]
                        best_similarity = max(best_similarity, similarity)
                        successful_comparisons += 1
                        
                        print(f"   🔍 Ref {i+1}: {similarity:.3f} - {os.path.basename(ref_path)}")
                    else:
                        print(f"   ⚠️  Ref {i+1}: Falha ao extrair features")
                else:
                    print(f"   ❌ Ref {i+1}: Imagem não carregada")
            
            print(f"📈 Comparações bem-sucedidas: {successful_comparisons}/{len(reference_paths)}")
            print(f"📊 Melhor similaridade: {best_similarity:.3f}")
            
            if successful_comparisons == 0:
                print("❌ Nenhuma comparação bem-sucedida")
                return False
            
            is_correct = best_similarity > self.threshold
            print(f"🎯 Resultado: {'✅ ACEITA' if is_correct else '❌ REJEITADA'} (threshold: {self.threshold})")
            
            return is_correct
            
        except Exception as e:
            print(f"❌ Erro na validação de imagem: {e}")
            return False
    
    def _get_local_image_paths(self, place_data: dict) -> list:
        """Converte URLs do GitHub em caminhos locais das imagens"""
        image_urls = place_data.get('imagem', [])
        local_paths = []
        
        for url in image_urls:
            local_path = self._url_to_local_path(url)
            if local_path and os.path.exists(local_path):
                local_paths.append(local_path)
            else:
                print(f"⚠️  Imagem local não encontrada: {local_path}")
        
        print(f"📍 Imagens de referência: {len(local_paths)} encontradas")
        return local_paths
    
    def _url_to_local_path(self, url: str) -> str:
        """Converte URL do GitHub em caminho local"""
        try:
            if 'imagens' in url:
                path_start = url.find('imagens')
                if path_start != -1:
                    relative_path = url[path_start:].split('?')[0]
                    return relative_path
            
            # Fallback
            filename = url.split('/')[-1].split('?')[0]
            return f"imagens/{filename}"
            
        except Exception as e:
            print(f"❌ Erro ao converter URL: {url} - {e}")
            return None
    
    def clear_cache(self):
        """Limpa o cache de imagens"""
        self.image_cache.clear()
        print("🧹 Cache de imagens limpo")
    
    def get_model_info(self):
        """Retorna informações sobre o modelo"""
        return {
            'model': 'EfficientNet-B0',
            'input_shape': (224, 224, 3),
            'feature_dim': 1280,
            'threshold': self.threshold
        }