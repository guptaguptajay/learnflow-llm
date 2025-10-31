"""Example usage of the Document Mapping API."""

import requests
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    if response.status_code < 400:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")
    print(f"{'='*60}\n")


def main():
    """Run example workflow."""
    print("GenAI Document Mapping Service - Example Usage")
    print("=" * 60)

    # Step 1: Check health
    print("\n1. Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)

    if response.status_code != 200:
        print("API is not healthy. Please check the service.")
        return

    # Step 2: Upload document
    print("\n2. Uploading document...")
    # You need to provide a test document path
    document_path = input("Enter path to PDF/EPUB/MOBI file: ").strip()

    if not Path(document_path).exists():
        print(f"File not found: {document_path}")
        return

    with open(document_path, "rb") as f:
        files = {"file": (Path(document_path).name, f)}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)

    print_response("Document Upload", response)

    if response.status_code != 201:
        print("Failed to upload document.")
        return

    document_id = response.json()["document_id"]
    print(f"Document ID: {document_id}")

    # Step 3: Process document
    print("\n3. Processing document...")
    payload = {
        "document_id": document_id,
        "chunk_size": 1000,
        "chunk_overlap": 200,
    }
    response = requests.post(f"{BASE_URL}/documents/process", json=payload)
    print_response("Document Processing", response)

    if response.status_code != 200:
        print("Failed to process document.")
        return

    # Step 4: Vectorize document
    print("\n4. Vectorizing document...")
    payload = {"document_id": document_id}
    response = requests.post(f"{BASE_URL}/documents/vectorize", json=payload)
    print_response("Document Vectorization", response)

    if response.status_code != 200:
        print("Failed to vectorize document.")
        return

    # Step 5: Generate topics
    print("\n5. Generating topics...")
    payload = {"document_id": document_id, "num_topics": 5}
    response = requests.post(f"{BASE_URL}/topics/generate", json=payload)
    print_response("Topic Generation", response)

    if response.status_code != 200:
        print("Failed to generate topics.")
        return

    topics = response.json()["topics"]
    print(f"\nGenerated {len(topics)} topics:")
    for idx, topic in enumerate(topics, 1):
        print(f"  {idx}. {topic['title']} (ID: {topic['id']})")

    if not topics:
        print("No topics generated.")
        return

    # Step 6: Generate subtopics for first topic
    print("\n6. Generating subtopics for first topic...")
    first_topic_id = topics[0]["id"]
    payload = {"topic_id": first_topic_id, "num_subtopics": 3}
    response = requests.post(f"{BASE_URL}/topics/subtopics/generate", json=payload)
    print_response("Subtopic Generation", response)

    if response.status_code == 200:
        subtopics = response.json()["subtopics"]
        print(f"\nGenerated {len(subtopics)} subtopics:")
        for idx, subtopic in enumerate(subtopics, 1):
            print(f"  {idx}. {subtopic['title']} (ID: {subtopic['id']})")

    # Step 7: Generate summary for first topic
    print("\n7. Generating summary for first topic...")
    payload = {"topic_id": first_topic_id}
    response = requests.post(f"{BASE_URL}/topics/summary/generate", json=payload)
    print_response("Summary Generation", response)

    if response.status_code == 200:
        summary = response.json()["summary"]
        print(f"\nSummary:\n{summary[:500]}...")

    # Step 8: Get full content for first topic
    print("\n8. Getting full content for first topic...")
    payload = {"topic_id": first_topic_id}
    response = requests.post(f"{BASE_URL}/topics/content", json=payload)
    print_response("Get Content", response)

    if response.status_code == 200:
        content = response.json()
        print(f"\nContent preview (first 300 chars):\n{content['full_text'][:300]}...")
        print(f"\nTotal chunks: {content['chunk_count']}")

    print("\n" + "=" * 60)
    print("Example workflow completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")

