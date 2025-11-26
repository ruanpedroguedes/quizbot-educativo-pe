# train_model.py
import pandas as pd
import os
from classifier import TouristSpotClassifier  # Importa da nova classe

def generate_model():
    """Gera e salva o modelo .pkl"""
    
    df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')
    print(f"📁 Dataset carregado: {len(df)} locais")
    
    classifier = TouristSpotClassifier()
    classifier.train(df)
    
    model_path = "backend/modelos/tourist_model.pkl"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    classifier.save(model_path)
    
    # Teste do modelo
    test_result = classifier.predict(
        "O Marco Zero fica no Recife Antigo e é um dos pontos mais famosos da cidade.",
        ["recife", "marco zero", "passeio"]
    )
    print(f"🧪 Teste do modelo: {test_result}")
    
    return classifier

if __name__ == "__main__":
    generate_model()