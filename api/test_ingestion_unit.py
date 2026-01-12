
from ingestion_service import IngestionService
import unittest

class TestIngestion(unittest.TestCase):
    def test_chunking(self):
        service = IngestionService()
        
        # Test 1: Small text
        text = "Hello world\n\nThis is a test."
        chunks = service.chunk_text(text, chunk_size=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)
        
        # Test 2: Large text
        # Generate 1500 chars (approx)
        para1 = "A" * 600
        para2 = "B" * 600
        para3 = "C" * 600
        full_text = f"{para1}\n\n{para2}\n\n{para3}"
        
        chunks = service.chunk_text(full_text, chunk_size=1000)
        
        # Should be split. A (600) fits. B (600) -> 1200 > 1000, so split.
        print(f"Chunks: {len(chunks)}")
        for i, c in enumerate(chunks):
            print(f"Chunk {i} length: {len(c)}")
            
        self.assertTrue(len(chunks) >= 2)
        
if __name__ == "__main__":
    unittest.main()
