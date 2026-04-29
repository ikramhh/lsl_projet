import torch

state = torch.load('core/ml/asl_model.pth', map_location='cpu', weights_only=False)
sd = state['model_state_dict'] if 'model_state_dict' in state else state

print("=== MOBILENETV2 CHECKPOINT ARCHITECTURE ANALYSIS ===\n")

# Check if it's a MobileNetV2 model
print("Model Type Check:")
has_model_key = 'model_state_dict' in state
print(f"  Has model_state_dict: {has_model_key}")

# Check classifier layers
print("\nCLASSIFIER LAYERS:")
classifier_keys = [k for k in sd.keys() if 'classifier' in k]
for k in classifier_keys[:10]:
    print(f"  {k}: {sd[k].shape}")

# Check features (frozen layers)
print("\nFEATURES (first 5 layers):")
feature_keys = [k for k in sd.keys() if 'model.features' in k][:5]
for k in feature_keys:
    print(f"  {k}: {sd[k].shape}")

# Total parameters
total_params = sum(p.numel() for p in sd.values())
print(f"\n=== SUMMARY ===")
print(f"Total parameters: {total_params:,}")
print(f"Number of keys: {len(sd)}")

# Check if model has expected structure
has_classifier = any('classifier' in k for k in sd.keys())
has_features = any('features' in k for k in sd.keys())
print(f"Has classifier: {has_classifier}")
print(f"Has features: {has_features}")
print(f"\n✅ Model appears to be MobileNetV2" if has_classifier and has_features else "\n❌ Model structure unexpected")
