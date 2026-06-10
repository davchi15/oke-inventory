from crop import crop_main_object
from embeddings import get_embedding, cosine_similarity
import os

IMAGES = {
    "front1": "test_images/front1.jpg",
    "front2": "test_images/front2.jpg",
    "back":   "test_images/back.jpg",
    "other":  "test_images/other.jpg",
}

def run_experiment():
    os.makedirs("test_images/crops", exist_ok=True)

    print("\nCropping to main object...")
    cropped = {}
    for name, path in IMAGES.items():
        out = f"test_images/crops/{name}.jpg"
        cropped[name] = crop_main_object(path, out)

    print("\nGenerating embeddings from crops...")
    embeddings = {name: get_embedding(path) for name, path in cropped.items()}

    print("\nPairwise similarity (cropped):\n")
    names = list(embeddings.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            print(f"  {a} vs {b}: {cosine_similarity(embeddings[a], embeddings[b]):.3f}")

if __name__ == "__main__":
    run_experiment()