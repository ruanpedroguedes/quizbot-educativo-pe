import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
import os

class TouristSpotClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        self.is_trained = False
    
    def train(self, df):
        """Treina o modelo com o dataset"""
        print("🎯 Treinando modelo de classificação...")
        
        # Prepara os dados
        X = []  # Features (vamos usar dados simples por enquanto)
        y = []  # Labels (nomes dos locais)
        
        # Extrai features simples do contexto
        for idx, row in df.iterrows():
            # Feature 1: Tamanho do contexto (número de palavras)
            context_length = len(row['contexto'].split())
            
            # Feature 2: Número de tags
            tags_count = len(row.get('tags', []))
            
            # Feature 3: Tem palavras-chave específicas
            contexto_lower = row['contexto'].lower()
            has_beach = 1 if any(word in contexto_lower for word in ['praia', 'mar', 'litoral']) else 0
            has_history = 1 if any(word in contexto_lower for word in ['histórico', 'museu', 'patrimônio']) else 0
            has_nature = 1 if any(word in contexto_lower for word in ['natureza', 'parque', 'verde']) else 0
            
            features = [context_length, tags_count, has_beach, has_history, has_nature]
            X.append(features)
            
            # Extrai nome do local do contexto
            nome_local = self._extract_location_name(row['contexto'])
            y.append(nome_local)
        
        # Codifica os labels
        self.label_encoder.fit(y)
        y_encoded = self.label_encoder.transform(y)
        
        # Treina o modelo
        self.model.fit(X, y_encoded)
        self.is_trained = True
        
        print(f"✅ Modelo treinado com {len(X)} exemplos e {len(self.label_encoder.classes_)} classes")
        return self
    
    def predict(self, context, tags=None):
        """Faz predição baseada no contexto"""
        if not self.is_trained:
            raise Exception("Modelo não foi treinado!")
        
        # Prepara features da mesma forma que no treinamento
        context_length = len(context.split())
        tags_count = len(tags) if tags else 0
        
        context_lower = context.lower()
        has_beach = 1 if any(word in context_lower for word in ['praia', 'mar', 'litoral']) else 0
        has_history = 1 if any(word in context_lower for word in ['histórico', 'museu', 'patrimônio']) else 0
        has_nature = 1 if any(word in context_lower for word in ['natureza', 'parque', 'verde']) else 0
        
        features = [context_length, tags_count, has_beach, has_history, has_nature]
        
        # Faz predição
        prediction = self.model.predict([features])[0]
        probability = self.model.predict_proba([features])[0]
        
        nome_local = self.label_encoder.inverse_transform([prediction])[0]
        confidence = probability[prediction]
        
        return {
            'predicted_class': nome_local,
            'confidence': confidence,
            'all_probabilities': {
                self.label_encoder.inverse_transform([i])[0]: float(prob) 
                for i, prob in enumerate(probability)
            }
        }
    
    def _extract_location_name(self, contexto):
        """Extrai nome do local do contexto"""
        nome = contexto.split('.')[0]
        descricoes = ['é um', 'é uma', 'fica', 'localizado', 'situado', 'conhecido']
        for desc in descricoes:
            if desc in nome:
                nome = nome.split(desc)[0]
        return nome.strip()
    
    def save(self, filepath):
        """Salva o modelo em arquivo .pkl"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"💾 Modelo salvo em: {filepath}")
    
    @staticmethod
    def load(filepath):
        """Carrega modelo de arquivo .pkl"""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"🔧 Modelo carregado de: {filepath}")
        return model

# Função principal para gerar o modelo
def generate_model():
    """Gera e salva o modelo .pkl"""
    
    # Carrega seu dataset
    df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')
    print(f"📁 Dataset carregado: {len(df)} locais")
    
    # Cria e treina o modelo
    classifier = TouristSpotClassifier()
    classifier.train(df)
    
    # Salva o modelo
    model_path = "backend/modelos/tourist_model.pkl"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    classifier.save(model_path)
    
    # Testa o modelo
    test_result = classifier.predict(
        "O Marco Zero fica no Recife Antigo e é um dos pontos mais famosos da cidade.",
        ["recife", "marco zero", "passeio"]
    )
    print(f"🧪 Teste do modelo: {test_result}")
    
    return classifier

if __name__ == "__main__":
    generate_model()