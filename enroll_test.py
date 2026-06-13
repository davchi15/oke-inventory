from embedding_store import (create_embeddings_table, enroll_item,
                             match_item, load_catalog, get_view_count)
from embeddings import get_embedding
from crop import crop_main_object
from db import create_table
import os

create_table()
create_embeddings_table()

ENROLL_VIEWS = [
    "test_images/crops/front1.jpg",
    "test_images/crops/front2.jpg",
    "test_images/crops/back.jpg",
]


def enroll():
    vectors = [get_embedding(p) for p in ENROLL_VIEWS]
    enroll_item("Arduino Uno", "Electronics", vectors)


def recognize(image_path):
    os.makedirs("test_images/crops", exist_ok=True)
    crop_path = f"test_images/crops/query_{os.path.basename(image_path)}"
    crop_main_object(image_path, crop_path)
    query = get_embedding(crop_path)
    name, score = match_item(query)
    if name:
        print(f"  Recognized: {name} (score {score:.3f})")
    else:
        print(f"  Unknown item (best score {score:.3f})")


if __name__ == "__main__":
    if len(load_catalog()) == 0:
        print("Catalog empty — enrolling Arduino Uno...")
        enroll()
    else:
        print(f"Catalog has {len(load_catalog())} stored views "
              f"({get_view_count('Arduino Uno')} for Arduino Uno).")

    print("\n--- Recognition test ---")
    recognize("test_images/query.jpg")
    recognize("test_images/other.jpg")