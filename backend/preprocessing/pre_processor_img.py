import cv2
import numpy as np
from PIL import Image
import io
import requests
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.image import extract_patches_2d
import os

class LightImageProcessor:
    def __init__(self):
        self.sift = cv2.SIFT_create()
        self.orb = cv2.ORB_create()
        
    async def download_image(self, url: str) -> np.ndarray:
        """Baixa imagem da URL e converte para array"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            return np.array(image.convert('RGB'))
        except Exception as e:
            print(f"Erro ao baixar imagem: {e}")
            return None
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extrai features leves usando ORB + Histograma de cores"""
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
    
    async def compare_images(self, user_image: np.ndarray, reference_urls: list) -> float:
        """Compara imagem do usuário com imagens de referência"""
        user_features = self.extract_features(user_image)
        
        best_similarity = 0
        for ref_url in reference_urls:
            ref_image = await self.download_image(ref_url)
            if ref_image is not None:
                ref_features = self.extract_features(ref_image)
                
                # Calcular similaridade do cosseno
                similarity = cosine_similarity([user_features], [ref_features])[0][0]
                best_similarity = max(best_similarity, similarity)
        
        return best_similarity
    
    async def validate_user_image(self, user_image_bytes: bytes, correct_place_data: dict) -> bool:
        """Valida se a imagem do usuário corresponde ao local correto"""
        # Converter bytes para array
        user_image = Image.open(io.BytesIO(user_image_bytes))
        user_array = np.array(user_image.convert('RGB'))
        
        # Comparar com imagens de referência do local
        reference_urls = correct_place_data.get('imagem', [])
        similarity = await self.compare_images(user_array, reference_urls)
        
        # Threshold ajustável - pode calibrar conforme necessidade
        return similarity > 0.6