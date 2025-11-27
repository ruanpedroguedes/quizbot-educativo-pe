import cv2
import numpy as np
from PIL import Image
import io
import os
from sklearn.metrics.pairwise import cosine_similarity

class LightImageProcessor:
    def __init__(self):
        self.sift = cv2.SIFT_create()
        self.orb = cv2.ORB_create()
        self.image_cache = {}
    
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
    
    async def validate_user_image(self, user_image_bytes: bytes, correct_place_data: dict) -> bool:
        """Valida se a imagem do usuário corresponde ao local correto - VERSÃO CORRIGIDA"""
        try:
            # Converter bytes da imagem do USUÁRIO para array
            user_image = Image.open(io.BytesIO(user_image_bytes))
            user_array = np.array(user_image.convert('RGB'))
            
            print(f"📸 Imagem do usuário recebida: {user_array.shape}")
            
            # Obter caminhos das imagens de referência do dataset
            reference_paths = self._get_local_image_paths(correct_place_data)
            
            if not reference_paths:
                print("❌ Nenhuma imagem de referência encontrada")
                return False
            
            # Comparar imagens
            similarity = await self.compare_images(user_array, reference_paths)
            
            print(f"📊 Similaridade da imagem: {similarity:.2f}")
            
            # Ajustar threshold conforme necessidade
            threshold = 0.4  # Pode ajustar para ser mais ou menos rigoroso
            is_correct = similarity > threshold
            
            print(f"🎯 Resultado: {'✅ ACEITA' if is_correct else '❌ REJEITADA'} (threshold: {threshold})")
            
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
            if 'backend/imagens/' in url:
                path_start = url.find('backend/imagens/')
                if path_start != -1:
                    relative_path = url[path_start:].split('?')[0]
                    return relative_path
            
            # Fallback
            filename = url.split('/')[-1].split('?')[0]
            return f"backend/imagens/{filename}"
            
        except Exception as e:
            print(f"❌ Erro ao converter URL: {url} - {e}")
            return None
    
    async def compare_images(self, user_image: np.ndarray, reference_paths: list) -> float:
        """Compara imagem do usuário com imagens de referência locais - VERSÃO MELHORADA"""
        user_features = self.extract_features(user_image)
        
        if user_features is None:
            print("❌ Não foi possível extrair features da imagem do usuário")
            return 0.0
        
        best_similarity = 0
        successful_comparisons = 0
        
        print(f"🔍 Iniciando comparação com {len(reference_paths)} imagens de referência")
        
        for i, ref_path in enumerate(reference_paths):
            ref_image = self.load_local_image(ref_path)
            if ref_image is not None:
                ref_features = self.extract_features(ref_image)
                
                if ref_features is not None:
                    # Calcular similaridade do cosseno
                    similarity = cosine_similarity([user_features], [ref_features])[0][0]
                    best_similarity = max(best_similarity, similarity)
                    successful_comparisons += 1
                    print(f"   📊 Ref {i+1}: {similarity:.3f} - {os.path.basename(ref_path)}")
                else:
                    print(f"   ⚠️  Ref {i+1}: Falha ao extrair features")
            else:
                print(f"   ❌ Ref {i+1}: Imagem não carregada")
        
        print(f"📈 Comparações bem-sucedidas: {successful_comparisons}/{len(reference_paths)}")
        print(f"🏆 Melhor similaridade: {best_similarity:.3f}")
        
        return best_similarity if successful_comparisons > 0 else 0.0
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extrai features da imagem - VERSÃO MAIS ROBUSTA"""
        try:
            # Redimensionar para processamento mais rápido
            height, width = image.shape[:2]
            if height > 400 or width > 400:
                scale = 400 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Features ORB
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            # Histograma de cores (HSV) - mais informativo
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            hist_hue = cv2.calcHist([hsv], [0], None, [50], [0, 256])
            hist_sat = cv2.calcHist([hsv], [1], None, [50], [0, 256])
            hist_val = cv2.calcHist([hsv], [2], None, [50], [0, 256])
            
            # Normalizar histogramas
            hist_hue = cv2.normalize(hist_hue, hist_hue).flatten()
            hist_sat = cv2.normalize(hist_sat, hist_sat).flatten()
            hist_val = cv2.normalize(hist_val, hist_val).flatten()
            
            # Combinar todas as features
            features_parts = []
            
            # Adicionar histogramas
            features_parts.extend(hist_hue)
            features_parts.extend(hist_sat)
            features_parts.extend(hist_val)
            
            # Adicionar features ORB se disponíveis
            if descriptors is not None:
                # Pegar os primeiros 100 descriptors ou a média
                if len(descriptors) > 100:
                    desc_subset = descriptors[:100].flatten()
                else:
                    desc_subset = descriptors.flatten()
                features_parts.extend(desc_subset)
            
            features = np.array(features_parts)
            
            # Verificar se features são válidas
            if np.any(np.isnan(features)) or np.any(np.isinf(features)):
                print("⚠️  Features inválidas detectadas")
                return None
                
            return features
            
        except Exception as e:
            print(f"❌ Erro ao extrair features: {e}")
            return None
    
    def clear_cache(self):
        """Limpa o cache de imagens"""
        self.image_cache.clear()
        print("🧹 Cache de imagens limpo")