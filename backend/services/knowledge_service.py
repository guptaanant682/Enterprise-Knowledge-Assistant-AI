import chromadb
from typing import List, Dict, Any, Optional
import os
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Document, DocumentEmbedding
from config import settings
import uuid

class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection("enterprise_knowledge")
        except:
            self.collection = self.client.create_collection(
                name="enterprise_knowledge",
                metadata={"description": "Enterprise knowledge base documents"}
            )
    
    async def add_document_to_vector_db(
        self, 
        document: Document, 
        content_chunks: List[str]
    ) -> List[str]:
        """Add document chunks to vector database"""
        try:
            chunk_ids = []
            metadatas = []
            documents = []
            
            for i, chunk in enumerate(content_chunks):
                # Create unique ID for this chunk
                chunk_id = f"doc_{document.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                chunk_ids.append(chunk_id)
                
                # Prepare metadata
                metadata = {
                    "document_id": document.id,
                    "title": document.title,
                    "category": document.category,
                    "chunk_index": i,
                    "filename": document.filename
                }
                metadatas.append(metadata)
                documents.append(chunk)
                
                # Save embedding reference in database
                embedding = DocumentEmbedding(
                    document_id=document.id,
                    chunk_text=chunk,
                    chunk_index=i,
                    embedding_id=chunk_id
                )
                self.db.add(embedding)
            
            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                documents=documents,
                metadatas=metadatas
            )
            
            self.db.commit()
            return chunk_ids
            
        except Exception as e:
            print(f"Error adding document to vector DB: {e}")
            self.db.rollback()
            raise e
    
    async def search_documents(
        self, 
        query: str, 
        limit: int = 10,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector similarity"""
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if category_filter and category_filter != "all":
                where_clause["category"] = category_filter
            
            # Search in ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Process results
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc_text in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    # Get document from database
                    document = self.db.query(Document).filter(
                        Document.id == metadata['document_id']
                    ).first()
                    
                    if document:
                        documents.append({
                            "id": document.id,
                            "title": document.title,
                            "category": document.category,
                            "content": doc_text,
                            "relevance_score": 1 - distance,  # Convert distance to relevance
                            "chunk_index": metadata.get('chunk_index', 0),
                            "filename": document.filename
                        })
            
            return documents
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    async def delete_document_from_vector_db(self, document_id: int):
        """Remove document from vector database"""
        try:
            # Get all embeddings for this document
            embeddings = self.db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).all()
            
            # Delete from ChromaDB
            chunk_ids = [emb.embedding_id for emb in embeddings]
            if chunk_ids:
                self.collection.delete(ids=chunk_ids)
            
            # Delete embeddings from database
            for embedding in embeddings:
                self.db.delete(embedding)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error deleting document from vector DB: {e}")
            self.db.rollback()
            raise e
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Add sentence to current chunk
            potential_chunk = current_chunk + sentence + ". "
            
            if len(potential_chunk) <= chunk_size:
                current_chunk = potential_chunk
            else:
                # Current chunk is full, start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + sentence + ". "
                else:
                    current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            total_docs = self.db.query(Document).count()
            total_chunks = self.db.query(DocumentEmbedding).count()
            
            # Get category distribution
            category_stats = self.db.query(
                Document.category,
                func.count(Document.id)
            ).group_by(Document.category).all()
            
            return {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "categories": dict(category_stats),
                "collection_count": self.collection.count()
            }
            
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "categories": {},
                "collection_count": 0
            }
    
    async def update_document_content(
        self, 
        document: Document, 
        new_content: str
    ):
        """Update document content and re-index"""
        try:
            # Remove old embeddings
            await self.delete_document_from_vector_db(document.id)
            
            # Update document content
            document.content = new_content
            
            # Create new chunks and embeddings
            chunks = self.chunk_text(new_content)
            if chunks:
                await self.add_document_to_vector_db(document, chunks)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating document content: {e}")
            self.db.rollback()
            raise e