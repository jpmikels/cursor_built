"""Document AI parsing service."""
import logging
from typing import Dict, Any, List
from google.cloud import documentai_v1 as documentai
from google.cloud import storage

from config import settings

logger = logging.getLogger(__name__)


class DocumentAIParser:
    """Parse documents using Google Document AI."""
    
    def __init__(self):
        self.client = documentai.DocumentProcessorServiceClient()
        self.storage_client = storage.Client(project=settings.project_id)
        self.processor_name = self.client.processor_path(
            settings.project_id,
            settings.document_ai_location,
            settings.document_ai_processor_id
        )
    
    def parse_pdf(self, gcs_path: str) -> Dict[str, Any]:
        """
        Parse a PDF document using Document AI.
        
        Args:
            gcs_path: GCS path to the PDF file
            
        Returns:
            Parsed document data with tables and key-value pairs
        """
        logger.info(f"Parsing document: {gcs_path}")
        
        try:
            # Read document from GCS
            bucket_name = settings.uploads_bucket
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(gcs_path)
            document_content = blob.download_as_bytes()
            
            # Create Document AI request
            raw_document = documentai.RawDocument(
                content=document_content,
                mime_type="application/pdf"
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract tables
            tables = self._extract_tables(document)
            
            # Extract key-value pairs
            key_values = self._extract_key_values(document)
            
            # Extract text
            text = document.text
            
            return {
                "text": text,
                "tables": tables,
                "key_values": key_values,
                "pages": len(document.pages),
                "confidence": self._calculate_average_confidence(document)
            }
            
        except Exception as e:
            logger.error(f"Error parsing document {gcs_path}: {str(e)}")
            raise
    
    def _extract_tables(self, document: documentai.Document) -> List[Dict[str, Any]]:
        """Extract tables from Document AI response."""
        tables = []
        
        for page in document.pages:
            for table in page.tables:
                table_data = {
                    "page": page.page_number,
                    "rows": len(table.body_rows),
                    "columns": len(table.header_rows[0].cells) if table.header_rows else 0,
                    "headers": [],
                    "data": []
                }
                
                # Extract header row
                if table.header_rows:
                    for cell in table.header_rows[0].cells:
                        text = self._get_text_from_layout(cell.layout, document.text)
                        table_data["headers"].append(text)
                
                # Extract data rows
                for row in table.body_rows:
                    row_data = []
                    for cell in row.cells:
                        text = self._get_text_from_layout(cell.layout, document.text)
                        row_data.append(text)
                    table_data["data"].append(row_data)
                
                tables.append(table_data)
        
        return tables
    
    def _extract_key_values(self, document: documentai.Document) -> Dict[str, str]:
        """Extract key-value pairs from Document AI response."""
        key_values = {}
        
        for page in document.pages:
            if hasattr(page, 'form_fields'):
                for field in page.form_fields:
                    field_name = self._get_text_from_layout(field.field_name.layout, document.text)
                    field_value = self._get_text_from_layout(field.field_value.layout, document.text)
                    key_values[field_name.strip()] = field_value.strip()
        
        return key_values
    
    def _get_text_from_layout(self, layout, full_text: str) -> str:
        """Extract text from layout segments."""
        text = ""
        for segment in layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else len(full_text)
            text += full_text[start_index:end_index]
        return text.strip()
    
    def _calculate_average_confidence(self, document: documentai.Document) -> float:
        """Calculate average confidence score."""
        confidences = []
        
        for page in document.pages:
            if hasattr(page, 'confidence'):
                confidences.append(page.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0

