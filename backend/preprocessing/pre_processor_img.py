# Importando Bibliotecas LEVES
import numpy as np
from PIL import Image 
from sklearn.metrics.pairwise import cosine_similarity

class ImageProcessor:
    def __init__(self):
        self.target_size = (224, 224)
        # Parâmetros de normalização (mesmos do ImageNet para compatibilidade)
        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])
        print("✅ ImageProcessor inicializado (versão leve)")
    
    def process_img(self, img_paths):
        """
        Processa múltiplas imagens - versão LEVE sem PyTorch
        Retorna: numpy array no formato (batch, channels, height, width)
        """
        processed = []
        for path in img_paths:
            try:
                img_array = self._process_single_image_internal(path)
                if img_array is not None:
                    processed.append(img_array)
            except Exception as e:
                print(f"❌ Erro em {path}: {e}")
        
        return np.array(processed) if processed else None
    
    def process_single_image(self, img_path):
        """
        Processa uma única imagem - versão LEVE
        Retorna: numpy array no formato (1, channels, height, width)
        """
        try:
            img_array = self._process_single_image_internal(img_path)
            if img_array is not None:
                return np.expand_dims(img_array, axis=0)  # Adiciona dimensão batch
            return None
        except Exception as e:
            print(f"❌ Erro ao processar {img_path}: {e}")
            return None
    
    def _process_single_image_internal(self, img_path):
        """
        Processamento interno para uma imagem
        Retorna: numpy array no formato (channels, height, width)
        """
        try:
            img = Image.open(img_path).convert('RGB')
            # Redimensiona
            img_resized = img.resize(self.target_size)
            # Converte para numpy array
            img_array = np.array(img_resized, dtype=np.float32)
            # Normaliza [0, 1]
            img_array = img_array / 255.0
            # Normaliza com mean/std (igual ao PyTorch)
            img_array = (img_array - self.mean) / self.std
            # Muda para formato (C, H, W) para compatibilidade
            img_array = np.transpose(img_array, (2, 0, 1))
            return img_array
        except Exception as e:
            print(f"❌ Erro no processamento interno de {img_path}: {e}")
            return None
    
    def calculate_similarity(self, img_array1, img_array2):
        """
        Calcula similaridade entre duas imagens usando cosine similarity
        """
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