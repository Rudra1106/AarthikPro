#!/usr/bin/env python3
"""
Reset Pinecone Indexes
Deletes existing indexes and recreates them with correct dimensions.
"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY not found")
        return
    
    pc = Pinecone(api_key=api_key)
    
    # Index names
    index_names = [
        "finance-general-v1",
        "finance-vertical-v1",
        "finance-table-v1"
    ]
    
    print("🗑️  Deleting old indexes...\n")
    
    for index_name in index_names:
        try:
            if index_name in pc.list_indexes().names():
                print(f"  Deleting: {index_name}")
                pc.delete_index(index_name)
                print(f"  ✅ Deleted: {index_name}")
            else:
                print(f"  ⚠️  Not found: {index_name}")
        except Exception as e:
            print(f"  ❌ Error deleting {index_name}: {e}")
    
    print("\n✅ All indexes deleted!")
    print("\nThe extraction script will recreate them with 1536 dimensions.")

if __name__ == "__main__":
    main()
