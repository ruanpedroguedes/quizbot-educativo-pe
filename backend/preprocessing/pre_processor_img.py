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
        self.image_cache = {}  # Cache para imagens locais
    
    def load_local_image(self, image_path: str) -> np.ndarray:
        """Carrega imagem do sistema de arquivos local"""
        try:
            # Verificar se já está em cache
            if image_path in self.image_cache:
                print(f"📦 Imagem do cache: {image_path}")
                return self.image_cache[image_path]
            
            print(f"🖼️  Carregando imagem local: {image_path}")
            
            # Verificar se o arquivo existe
            if not os.path.exists(image_path):
                print(f"❌ Arquivo não encontrado: {image_path}")
                return None
            
            # Carregar imagem
            image = Image.open(image_path)
            image_array = np.array(image.convert('RGB'))
            
            # Armazenar no cache
            self.image_cache[image_path] = image_array
            
            return image_array
            
        except Exception as e:
            print(f"❌ Erro ao carregar imagem {image_path}: {e}")
            return None
    
    async def validate_user_image(self, user_image_bytes: bytes, correct_place_data: dict) -> bool:
        """Valida se a imagem do usuário corresponde ao local correto"""
        try:
            # Converter bytes da imagem do USUÁRIO para array
            user_image = Image.open(io.BytesIO(user_image_bytes))
            user_array = np.array(user_image.convert('RGB'))
            
            # Obter caminhos das imagens de referência do dataset
            reference_paths = self._get_local_image_paths(correct_place_data)
            similarity = await self.compare_images(user_array, reference_paths)
            
            print(f"📊 Similaridade da imagem: {similarity:.2f}")
            
            # Threshold ajustável
            return similarity > 0.6
            
        except Exception as e:
            print(f"❌ Erro na validação de imagem: {e}")
            return False
    
    def _get_local_image_paths(self, place_data: dict) -> list:
        """Converte URLs do GitHub em caminhos locais das imagens"""
        image_urls = place_data.get('imagem', [])
        local_paths = []
        
        for url in image_urls:
            # Converter URL do GitHub em caminho local
            # Ex: "https://github.com/.../backend/imagens/marco_zero_1.jpeg?raw=true"
            # vira: "backend/imagens/marco_zero_1.jpeg"
            local_path = self._url_to_local_path(url)
            if local_path and os.path.exists(local_path):
                local_paths.append(local_path)
            else:
                print(f"⚠️  Imagem local não encontrada: {local_path}")
        
        print(f"📍 Caminhos locais encontrados: {len(local_paths)}/{len(image_urls)}")
        return local_paths
    
    def _url_to_local_path(self, url: str) -> str:
        """Converte URL do GitHub em caminho local"""
        try:
            # Extrair o caminho relativo da URL
            if 'backend/imagens/' in url:
                # Ex: https://github.com/.../backend/imagens/marco_zero_1.jpeg?raw=true
                path_start = url.find('backend/imagens/')
                if path_start != -1:
                    relative_path = url[path_start:]  # backend/imagens/marco_zero_1.jpeg?raw=true
                    # Remover parâmetros da URL
                    relative_path = relative_path.split('?')[0]  # backend/imagens/marco_zero_1.jpeg
                    return relative_path
            
            # Fallback: tentar extrair nome do arquivo
            filename = url.split('/')[-1]  # marco_zero_1.jpeg?raw=true
            filename = filename.split('?')[0]  # marco_zero_1.jpeg
            return f"backend/imagens/{filename}"
            
        except Exception as e:
            print(f"❌ Erro ao converter URL para caminho local: {url} - {e}")
            return None
    
    async def compare_images(self, user_image: np.ndarray, reference_paths: list) -> float:
        """Compara imagem do usuário com imagens de referência locais"""
        user_features = self.extract_features(user_image)
        
        if user_features is None:
            return 0.0
        
        best_similarity = 0
        successful_comparisons = 0
        
        for ref_path in reference_paths:
            ref_image = self.load_local_image(ref_path)
            if ref_image is not None:
                ref_features = self.extract_features(ref_image)
                
                if ref_features is not None:
                    # Calcular similaridade do cosseno
                    similarity = cosine_similarity([user_features], [ref_features])[0][0]
                    best_similarity = max(best_similarity, similarity)
                    successful_comparisons += 1
                    print(f"   🔍 {ref_path}: {similarity:.2f}")
        
        print(f"📈 Comparações bem-sucedidas: {successful_comparisons}/{len(reference_paths)}")
        return best_similarity if successful_comparisons > 0 else 0.0
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extrai features da imagem"""
        try:
            # Redimensionar para processamento mais rápido
            height, width = image.shape[:2]
            if height > 500 or width > 500:
                scale = 500 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Features ORB
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            # Histograma de cores (HSV)
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            # Combinar features
            if descriptors is not None:
                desc_mean = np.mean(descriptors, axis=0)
                if desc_mean is not None:
                    features = np.concatenate([desc_mean, hist])
                    return features
            
            return hist
            
        except Exception as e:
            print(f"❌ Erro ao extrair features: {e}")
            return None
    
    def clear_cache(self):
        """Limpa o cache de imagens"""
        self.image_cache.clear()
        print("🧹 Cache de imagens limpo")