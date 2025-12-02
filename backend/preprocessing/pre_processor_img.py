import cv2
import numpy as np
from PIL import Image
import io
import os
from sklearn.metrics.pairwise import cosine_similarity

class LightImageProcessor:
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=1000)  
        self.image_cache = {}
        self.threshold = 0.85  
    
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
        """Valida se a imagem do usuário corresponde ao local correto - VERSÃO RIGOROSA"""
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
            
            print(f"📍 Comparando com {len(reference_paths)} imagens de referência")
            
            # MÚLTIPLAS EstratégiaS de comparação
            similarity = await self.compare_images_rigorous(user_array, reference_paths)
            
            print(f"📊 Similaridade FINAL: {similarity:.3f}")
            
            is_correct = similarity > self.threshold
            print(f"🎯 Resultado: {'✅ ACEITA' if is_correct else '❌ REJEITADA'} (threshold: {self.threshold})")
            
            return is_correct
            
        except Exception as e:
            print(f"❌ Erro na validação de imagem: {e}")
            return False
    
    async def compare_images_rigorous(self, user_image: np.ndarray, reference_paths: list) -> float:
        """Comparação RIGOROSA com múltiplas estratégias"""
        similarities = []
        
        for i, ref_path in enumerate(reference_paths):
            ref_image = self.load_local_image(ref_path)
            if ref_image is not None:
                # Estratégia 1: Similaridade de histogramas de cor
                similarity1 = self._compare_color_histograms(user_image, ref_image)
                
                # Estratégia 2: Similaridade estrutural (SSIM)
                similarity2 = self._compare_structural_similarity(user_image, ref_image)
                
                # Estratégia 3: Similaridade de features ORB
                similarity3 = self._compare_orb_features(user_image, ref_image)
                
                # COMBINAR as 3 Estratégias (MÉDIA PONDERADA)
                # Dá mais peso ao SSIM e ORB que são mais discriminativos
                combined_similarity = (similarity1 * 0.3) + (similarity2 * 0.4) + (similarity3 * 0.3)
                
                similarities.append(combined_similarity)
                
                print(f"   🔍 Ref {i+1}: {combined_similarity:.3f} " +
                      f"(H:{similarity1:.3f} S:{similarity2:.3f} O:{similarity3:.3f})")
        
        if not similarities:
            return 0.0
        
        best_similarity = max(similarities)
        return best_similarity
    
    def _compare_color_histograms(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compara histogramas de cor HSV """
        try:
            # Redimensionar para mesmo tamanho
            img1_resized = cv2.resize(img1, (300, 300))
            img2_resized = cv2.resize(img2, (300, 300))
            
            # Converter para HSV
            hsv1 = cv2.cvtColor(img1_resized, cv2.COLOR_RGB2HSV)
            hsv2 = cv2.cvtColor(img2_resized, cv2.COLOR_RGB2HSV)
            
            # Calcular histogramas para cada canal
            hist1_h = cv2.calcHist([hsv1], [0], None, [50], [0, 256])
            hist1_s = cv2.calcHist([hsv1], [1], None, [50], [0, 256])
            hist1_v = cv2.calcHist([hsv1], [2], None, [50], [0, 256])
            
            hist2_h = cv2.calcHist([hsv2], [0], None, [50], [0, 256])
            hist2_s = cv2.calcHist([hsv2], [1], None, [50], [0, 256])
            hist2_v = cv2.calcHist([hsv2], [2], None, [50], [0, 256])
            
            # Normalizar
            hist1_h = cv2.normalize(hist1_h, hist1_h).flatten()
            hist1_s = cv2.normalize(hist1_s, hist1_s).flatten()
            hist1_v = cv2.normalize(hist1_v, hist1_v).flatten()
            
            hist2_h = cv2.normalize(hist2_h, hist2_h).flatten()
            hist2_s = cv2.normalize(hist2_s, hist2_s).flatten()
            hist2_v = cv2.normalize(hist2_v, hist2_v).flatten()
            
            # Calcular similaridades (CORRELATION é mais rigoroso)
            similarity_h = cv2.compareHist(hist1_h, hist2_h, cv2.HISTCMP_CORREL)
            similarity_s = cv2.compareHist(hist1_s, hist2_s, cv2.HISTCMP_CORREL)
            similarity_v = cv2.compareHist(hist1_v, hist2_v, cv2.HISTCMP_CORREL)
            
            # Média das similaridades
            avg_similarity = (similarity_h + similarity_s + similarity_v) / 3
            
            # Converter para escala 0-1
            return max(0.0, (avg_similarity + 1) / 2)
            
        except Exception as e:
            print(f"❌ Erro ao comparar histogramas: {e}")
            return 0.0
    
    def _compare_structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compara usando similaridade estrutural (SSIM)"""
        try:
            # Redimensionar para o mesmo tamanho
            height, width = 256, 256
            img1_resized = cv2.resize(img1, (width, height))
            img2_resized = cv2.resize(img2, (width, height))
            
            # Converter para escala de cinza
            gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_RGB2GRAY)
            
            # Calcular SSIM
            from skimage.metrics import structural_similarity as ssim
            similarity, _ = ssim(gray1, gray2, full=True)
            
            return max(0.0, similarity)
            
        except Exception as e:
            print(f"⚠️  SSIM não disponível: {e}")
            return 0.0
    
    def _compare_orb_features(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compara usando features ORB """
        try:
            # Redimensionar
            img1_resized = cv2.resize(img1, (400, 400))
            img2_resized = cv2.resize(img2, (400, 400))
            
            # Converter para escala de cinza
            gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_RGB2GRAY)
            
            # Detectar features ORB
            keypoints1, descriptors1 = self.orb.detectAndCompute(gray1, None)
            keypoints2, descriptors2 = self.orb.detectAndCompute(gray2, None)
            
            if descriptors1 is None or descriptors2 is None:
                return 0.0
            
            # ✅ Usar BFMatcher para encontrar correspondências
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(descriptors1, descriptors2)
            
            if not matches:
                return 0.0
            
            # Calcular similaridade baseada no número de boas correspondências
            good_matches = [m for m in matches if m.distance < 50]  # Threshold rigoroso
            
            if len(matches) == 0:
                return 0.0
            
            similarity = len(good_matches) / min(len(descriptors1), len(descriptors2))
            
            return min(1.0, similarity)
            
        except Exception as e:
            print(f"❌ Erro ao comparar features ORB: {e}")
            return 0.0
    
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