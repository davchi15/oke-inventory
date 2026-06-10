from sentence_transformers import SentenceTransformer
from PIL import Image
import numpy as np

print("Loading CLIP model...")
model = SentenceTransformer("clip-ViT-B-32")
print("Model ready.")

def get_embedding(image_path):
    image = Image.open(image_path)
    embedding = model.encode(image)
    # normalize to length 1 so cosine similarity is just a dot product
    return embedding / np.linalg.norm(embedding)

def cosine_similarity(a, b):
    return float(np.dot(a, b))

def suggest_category(image_path):
    img_emb = get_embedding(image_path)
    print(f"\nCategory scores for {image_path}:")
    for cat in CATEGORIES:
        text_emb = model.encode(cat)
        text_emb = text_emb / np.linalg.norm(text_emb)
        score = cosine_similarity(img_emb, text_emb)
        print(f"  {cat}: {score:.3f}")

if __name__ == "__main__":
    run_experiment()
    suggest_category("test_images/front1.jpg")
    suggest_category("test_images/other.jpg")