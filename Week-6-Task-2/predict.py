import os
os.environ["TORCH_HOME"] = "/root/.cache/torch"
import torch
from PIL import Image
from torchvision import models
from cog import BasePredictor, Input, Path

# Use default ImageNet weights for ResNet50
WEIGHTS = models.ResNet50_Weights.DEFAULT

class Predictor(BasePredictor):
    def setup(self):
        """Load the pre-trained ResNet-50 model into memory."""
        print("[SETUP] Loading ResNet50 model weights...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet50(weights=WEIGHTS).to(self.device)
        self.model.eval()
        self.transforms = WEIGHTS.transforms()
        self.categories = WEIGHTS.meta["categories"]
        print(f"[SETUP] Model loaded successfully on {self.device}.")

    def run(
        self,
        image: Path = Input(description="Cat or animal image to classify")
    ) -> dict:
        """Run classification on the uploaded image and return top cat/animal breeds with probabilities."""
        print(f"[RUN] Received image: {image}")
        img = Image.open(str(image)).convert("RGB")
        tensor = self.transforms(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(tensor)

        # Softmax to get probabilities
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        
        # Get top 5 predictions
        top5_prob, top5_catid = torch.topk(probabilities, 5)

        predictions = {}
        for i in range(top5_prob.size(0)):
            category_name = self.categories[top5_catid[i]]
            prob_percent = round(top5_prob[i].item() * 100, 2)
            predictions[category_name] = f"{prob_percent}%"
            print(f"[RESULT] {category_name}: {prob_percent}%")

        return predictions
