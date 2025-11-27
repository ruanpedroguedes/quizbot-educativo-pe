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
            
            # Comparar imagens com múltiplas estratégias
            similarity = await self.compare_images_rigorous(user_array, reference_paths)
            
            print(f"📊 Similaridade FINAL: {similarity:.3f}")
            
            # THRESHOLD MAIS RIGOROSO
            threshold = 0.6  # Aumentado para ser mais exigente
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
    
    async def compare_images_rigorous(self, user_image: np.ndarray, reference_paths: list) -> float:
        """Comparação RIGOROSA com múltiplas estratégias"""
        similarities = []
        
        for i, ref_path in enumerate(reference_paths):
            ref_image = self.load_local_image(ref_path)
            if ref_image is not None:
                # Estratégia 1: Similaridade de features combinadas
                similarity1 = self._compare_features(user_image, ref_image)
                
                # Estratégia 2: Similaridade de histograma de cores
                similarity2 = self._compare_color_histograms(user_image, ref_image)
                
                # Estratégia 3: Similaridade estrutural (se disponível)
                similarity3 = self._compare_structural_similarity(user_image, ref_image)
                
                # Combinar as similaridades
                if similarity3 is not None:
                    combined_similarity = (similarity1 + similarity2 + similarity3) / 3
                else:
                    combined_similarity = (similarity1 + similarity2) / 2
                    
                similarities.append(combined_similarity)
                
                print(f"   🔍 Ref {i+1}: {combined_similarity:.3f} " +
                    f"(F:{similarity1:.3f} C:{similarity2:.3f}" +
                    (f" S:{similarity3:.3f})" if similarity3 is not None else ")"))
        
        if not similarities:
            return 0.0
        
        # Retornar a melhor similaridade
        best_similarity = max(similarities)
        return best_similarity

    def _compare_features(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compara usando features ORB + Histograma"""
        features1 = self.extract_features(img1)
        features2 = self.extract_features(img2)
        
        if features1 is None or features2 is None:
            return 0.0
        
        # Calcular similaridade do cosseno
        similarity = cosine_similarity([features1], [features2])[0][0]
        
        # Garantir que está entre 0 e 1
        return max(0.0, min(1.0, similarity))
    
    def _compare_color_histograms(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compara usando histogramas de cor"""
        try:
            # Converter para HSV
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_RGB2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_RGB2HSV)
            
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
            
            # Calcular similaridades
            similarity_h = cv2.compareHist(hist1_h, hist2_h, cv2.HISTCMP_CORREL)
            similarity_s = cv2.compareHist(hist1_s, hist2_s, cv2.HISTCMP_CORREL)
            similarity_v = cv2.compareHist(hist1_v, hist2_v, cv2.HISTCMP_CORREL)
            
            # Média das similaridades
            avg_similarity = (similarity_h + similarity_s + similarity_v) / 3
            
            # Converter para escala 0-1 (cv2.compareHist retorna -1 a 1)
            return (avg_similarity + 1) / 2
            
        except Exception as e:
            print(f"❌ Erro ao comparar histogramas: {e}")
            return 0.0

    def _compare_structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compara usando similaridade estrutural (SSIM)"""
        try:
            # Redimensionar para o mesmo tamanho
            height, width = 300, 300
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
            return None

    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extrai features da imagem - VERSÃO OTIMIZADA"""
        try:
            # Redimensionar
            height, width = image.shape[:2]
            if height > 400 or width > 400:
                scale = 400 / max(height, width)
                new_size = (int(width * scale), int(height * scale))
                image = cv2.resize(image, new_size)
            
            # Features ORB
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            # Histograma de cores HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            hist_h = cv2.calcHist([hsv], [0], None, [30], [0, 256])
            hist_s = cv2.calcHist([hsv], [1], None, [30], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [30], [0, 256])
            
            # Normalizar e combinar
            hist_h = cv2.normalize(hist_h, hist_h).flatten()
            hist_s = cv2.normalize(hist_s, hist_s).flatten()
            hist_v = cv2.normalize(hist_v, hist_v).flatten()
            
            features = []
            features.extend(hist_h)
            features.extend(hist_s)
            features.extend(hist_v)
            
            # Adicionar descriptors ORB se disponíveis
            if descriptors is not None:
                # Usar estatísticas dos descriptors (mais robusto)
                desc_mean = np.mean(descriptors, axis=0)
                desc_std = np.std(descriptors, axis=0)
                features.extend(desc_mean)
                features.extend(desc_std)
            
            features_array = np.array(features)
            
            # Verificar validade
            if np.any(np.isnan(features_array)) or np.any(np.isinf(features_array)):
                return None
                
            return features_array
            
        except Exception as e:
            print(f"❌ Erro ao extrair features: {e}")
            return None
    
    def clear_cache(self):
        """Limpa o cache de imagens"""
        self.image_cache.clear()
        print("🧹 Cache de imagens limpo")