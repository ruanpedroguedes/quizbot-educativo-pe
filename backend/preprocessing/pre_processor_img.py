#Importando Bibliotecas
import pandas as pd
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image 
import cv2
import os
import matplotlib.pyplot as plt

#Lendo dataset 
df_read = pd.read_json("datasets/dataset_pernambuco_25_turistas.json")

all_imgs = df_read["imagem"]
for i in range(len(all_imgs)):
    print(f"🎯 Encontradas {all_imgs[i]}")

#Pré-processamento de Imagens com o t-50
class ImageProcessor:
    def __init__(self):
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

#Pré-processamento de Imagens com o ResNet-50
    def process_img(self, img_paths):
        processed = []
        for path in img_paths:
              try:
                  img = Image.open(path).convert('RGB')
                  processed.append(self.transform(img))
              except Exception as e:
                print(f"❌ Erro em {path}: {e}")
    
        return torch.stack(processed) if processed else None
#Processa uma unica imagem
    def process_single_image(self, img_path):
        try:
            img = Image.open(img_path).convert('RGB')
            return self.transform(img).unsqueeze(0)  
        except Exception as e:
            print(f"❌ Erro ao processar {img_path}: {e}")
            return None

# Vendo o resultado final das imagens para teste
def show_processed_preview(processed_tensors):
    num_images = len(processed_tensors)
    
    # Configurar o layout
    fig, axes = plt.subplots(1, num_images, figsize=(15, 3))
    
    # Se for apenas 1 imagem, converter para lista
    if num_images == 1:
        axes = [axes]
    
    for i in range(num_images):
        # Pegar tensor da imagem i
        tensor_img = processed_tensors[i]
        
        # Converter para numpy e ajustar dimensões (C, H, W) -> (H, W, C)
        img_np = tensor_img.numpy().transpose(1, 2, 0)
        
        # Desnormalizar para visualização
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_np = img_np * std + mean
        img_np = np.clip(img_np, 0, 1)  # Limitar entre 0 e 1
        
        # Mostrar imagem
        axes[i].imshow(img_np)
        axes[i].set_title(f'Img {i+1}\n{tensor_img.shape}')
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()