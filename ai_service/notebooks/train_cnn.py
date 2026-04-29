"""
Entraînement du modèle CNN sur le dataset ASL Alphabet complet
MobileNetV2 avec Transfer Learning
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import matplotlib.pyplot as plt
import numpy as np
import os
from tqdm import tqdm

class ASLTrainer:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.num_classes = 29  # A-Z + space + delete + nothing
        self.image_size = 224
        self.batch_size = 32
        self.epochs = 30
        self.learning_rate = 0.001
        
        # Chemins
        self.data_dir = 'data/asl_dataset/asl_alphabet_train/asl_alphabet_train'
        self.model_path = 'saved_model/asl_model.pth'
        os.makedirs('saved_model', exist_ok=True)
        
    def prepare_data(self):
        """Préparer les données d'entraînement"""
        print("\n📊 Préparation des données...")
        
        if not os.path.exists(self.data_dir):
            print(f"❌ Dataset non trouvé: {self.data_dir}")
            print("💡 Exécutez d'abord: python download_asl_dataset.py")
            return None, None
        
        # Transformations
        train_transform = transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.RandomRotation(20),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        val_transform = transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # Datasets
        full_dataset = datasets.ImageFolder(self.data_dir, transform=train_transform)
        
        # Split train/val
        train_size = int(0.8 * len(full_dataset))
        val_size = len(full_dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            full_dataset, [train_size, val_size]
        )
        
        val_dataset.dataset.transform = val_transform
        
        # DataLoaders
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, 
                                 shuffle=True, num_workers=4)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, 
                               shuffle=False, num_workers=4)
        
        print(f"✓ Train: {len(train_dataset)} images")
        print(f"✓ Val: {len(val_dataset)} images")
        print(f"✓ Classes: {len(full_dataset.classes)}")
        
        return train_loader, val_loader
    
    def create_model(self):
        """Créer le modèle MobileNetV2 avec transfer learning"""
        print("\n🧠 Création du modèle...")
        
        # MobileNetV2 pré-entraîné
        model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        
        # Freezer les couches initiales
        for param in model.features[:10].parameters():
            param.requires_grad = False
        
        # Remplacer le classifieur
        num_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, self.num_classes)
        )
        
        model = model.to(self.device)
        
        print(f"✓ Modèle créé: MobileNetV2")
        print(f"✓ Device: {self.device}")
        
        return model
    
    def train(self, model, train_loader, val_loader):
        """Entraîner le modèle"""
        print("\n" + "="*60)
        print("  ENTRAÎNEMENT DU MODÈLE")
        print("="*60)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', 
                                                         factor=0.5, patience=3)
        
        best_acc = 0.0
        history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
        
        for epoch in range(self.epochs):
            print(f"\n📍 Époque {epoch+1}/{self.epochs}")
            
            # Training
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            pbar = tqdm(train_loader, desc="Training")
            for inputs, labels in pbar:
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                train_total += labels.size(0)
                train_correct += predicted.eq(labels).sum().item()
                
                pbar.set_postfix({'loss': f'{loss.item():.4f}', 
                                 'acc': f'{100.*train_correct/train_total:.2f}%'})
            
            train_loss /= train_total
            train_acc = 100. * train_correct / train_total
            
            # Validation
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item() * inputs.size(0)
                    _, predicted = outputs.max(1)
                    val_total += labels.size(0)
                    val_correct += predicted.eq(labels).sum().item()
            
            val_loss /= val_total
            val_acc = 100. * val_correct / val_total
            
            scheduler.step(val_loss)
            
            # Sauvegarder le meilleur modèle
            if val_acc > best_acc:
                best_acc = val_acc
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_acc': val_acc,
                    'val_loss': val_loss,
                    'classes': list(range(self.num_classes))
                }, self.model_path)
                print(f"⭐ Meilleur modèle sauvegardé! (Acc: {val_acc:.2f}%)")
            
            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)
            
            print(f"Train - Loss: {train_loss:.4f} | Acc: {train_acc:.2f}%")
            print(f"Val   - Loss: {val_loss:.4f} | Acc: {val_acc:.2f}%")
        
        return model, history
    
    def plot_results(self, history):
        """Afficher les courbes d'entraînement"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Accuracy
        ax1.plot(history['train_acc'], label='Train')
        ax1.plot(history['val_acc'], label='Validation')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Accuracy (%)')
        ax1.set_title('Training & Validation Accuracy')
        ax1.legend()
        ax1.grid(True)
        
        # Loss
        ax2.plot(history['train_loss'], label='Train')
        ax2.plot(history['val_loss'], label='Validation')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Loss')
        ax2.set_title('Training & Validation Loss')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('saved_model/training_curves.png', dpi=150)
        print(f"\n📈 Courbes sauvegardées: saved_model/training_curves.png")
    
    def run(self):
        """Exécuter l'entraînement complet"""
        print("="*60)
        print("  ENTRAÎNEMENT ASL ALPHABET - MobileNetV2")
        print("="*60)
        
        # Données
        train_loader, val_loader = self.prepare_data()
        if train_loader is None:
            return
        
        # Modèle
        model = self.create_model()
        
        # Entraînement
        model, history = self.train(model, train_loader, val_loader)
        
        # Résultats
        self.plot_results(history)
        
        print("\n" + "="*60)
        print("  ✅ ENTRAÎNEMENT TERMINÉ!")
        print("="*60)
        print(f"\n🏆 Meilleure accuracy: {max(history['val_acc']):.2f}%")
        print(f"📁 Modèle sauvegardé: {self.model_path}")

def main():
    trainer = ASLTrainer()
    trainer.run()

if __name__ == "__main__":
    main()
