# Importando Bibliotecas LEVES
import numpy as np
from PIL import Image 

class ImageProcessor:
    def __init__(self):
        self.target_size = (224, 224)
        # Parâmetros de normalização (mesmos do ImageNet para compatibilidade)
        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])
        print("✅ ImageProcessor inicializado (versão leve)")
    
    def process_img(self, img_paths):
        """
        Processa múltiplas imagens - MESMA INTERFACE que o QuizSystem espera
        Retorna: numpy array no formato (batch, channels, height, width)
        """
        processed = []
        for path in img_paths:
            try:
                img = Image.open(path).convert('RGB')
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
                processed.append(img_array)
            except Exception as e:
                print(f"❌ Erro em {path}: {e}")
    
        return np.array(processed) if processed else None
    
    def process_single_image(self, img_path):
        """
        Processa uma única imagem - MESMA INTERFACE que o QuizSystem espera
        Retorna: numpy array no formato (1, channels, height, width) com batch dimension
        """
        try:
            img = Image.open(img_path).convert('RGB')
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
            # Adiciona dimensão batch (1, C, H, W) - MESMO que .unsqueeze(0) do PyTorch
            return np.expand_dims(img_array, axis=0)
        except Exception as e:
            print(f"❌ Erro ao processar {img_path}: {e}")
            return None