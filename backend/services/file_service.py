import os
import aiofiles
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import mimetypes
from pathlib import Path
import hashlib
from pypdf import PdfReader
from docx import Document as DocxDocument
import io
from config import settings

class FileService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(exist_ok=True)
        self.allowed_extensions = settings.ALLOWED_FILE_TYPES
        self.max_file_size = settings.MAX_FILE_SIZE
    
    async def save_file(self, file: UploadFile) -> Dict[str, Any]:
        """Save uploaded file to disk"""
        try:
            # Validate file
            validation_result = await self.validate_file(file)
            if not validation_result["valid"]:
                return validation_result
            
            # Generate unique filename
            file_hash = hashlib.md5(f"{file.filename}{file.size}".encode()).hexdigest()[:8]
            file_extension = Path(file.filename).suffix.lower()
            safe_filename = f"{Path(file.filename).stem}_{file_hash}{file_extension}"
            file_path = self.upload_dir / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            return {
                "valid": True,
                "file_path": str(file_path),
                "filename": safe_filename,
                "original_filename": file.filename,
                "size": file.size,
                "content_type": file.content_type
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to save file: {str(e)}"
            }
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        # Check file size
        if file.size > self.max_file_size:
            return {
                "valid": False,
                "error": f"File size ({file.size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)"
            }
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            return {
                "valid": False,
                "error": f"File type {file_extension} not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            }
        
        # Check MIME type
        expected_mime = mimetypes.guess_type(file.filename)[0]
        if expected_mime and file.content_type:
            if not file.content_type.startswith(expected_mime.split('/')[0]):
                return {
                    "valid": False,
                    "error": "File content does not match file extension"
                }
        
        return {"valid": True}
    
    async def extract_text(self, file_path: str, content_type: str = None) -> str:
        """Extract text content from file"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                return await self._extract_pdf_text(file_path)
            elif file_extension in ['.doc', '.docx']:
                return await self._extract_docx_text(file_path)
            elif file_extension in ['.txt', '.md']:
                return await self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
        
        return text
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = DocxDocument(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX {file_path}: {e}")
        
        return text
    
    async def _extract_text_file(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                return await file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                async with aiofiles.open(file_path, 'r', encoding='latin-1') as file:
                    return await file.read()
            except Exception as e:
                print(f"Error reading text file {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            return {
                "exists": True,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": Path(file_path).suffix.lower(),
                "name": Path(file_path).name
            }
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return {"exists": False, "error": str(e)}
    
    async def process_multiple_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Process multiple file uploads"""
        results = []
        
        for file in files:
            try:
                # Reset file pointer
                await file.seek(0)
                
                result = await self.save_file(file)
                result["original_filename"] = file.filename
                results.append(result)
                
            except Exception as e:
                results.append({
                    "valid": False,
                    "error": str(e),
                    "original_filename": file.filename
                })
        
        return results