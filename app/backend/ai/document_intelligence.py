"""Document AI service for intelligent document extraction."""
import logging
from typing import Dict, List, Optional
from google.cloud import documentai_v1 as documentai
from google.cloud import storage
from config import settings

logger = logging.getLogger(__name__)


class DocumentIntelligenceService:
    """Service for processing documents with Google Document AI."""
    
    def __init__(self):
        """Initialize Document AI service."""
        self.project_id = settings.project_id
        self.location = settings.document_ai_location
        self.processor_id = settings.document_ai_processor_id
        try:
            self.client = documentai.DocumentProcessorServiceClient()
            self.storage_client = storage.Client()
        except Exception as e:
            logger.warning(f"Could not initialize Document AI service: {e}")
            self.client = None
            self.storage_client = None
    
    def _get_processor_name(self) -> str:
        """Get the full processor resource name."""
        return self.client.processor_path(
            self.project_id,
            self.location,
            self.processor_id
        )
    
    async def process_document(
        self,
        gcs_uri: str,
        mime_type: str = "application/pdf"
    ) -> Dict:
        """
        Process a document from Cloud Storage using Document AI.
        
        Args:
            gcs_uri: GCS URI of the document (gs://bucket/path/to/file)
            mime_type: MIME type of the document
            
        Returns:
            Extracted document data with text, tables, and entities
        """
        if not self.client or not self.storage_client:
            logger.warning("Document AI not initialized, returning empty result")
            return {"text": "", "pages": 0, "tables": [], "entities": [], "confidence": 0.0}
        
        try:
            # Parse GCS URI
            if not gcs_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI: {gcs_uri}")
            
            parts = gcs_uri[5:].split("/", 1)
            bucket_name = parts[0]
            blob_name = parts[1]
            
            # Get document from GCS
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            document_content = blob.download_as_bytes()
            
            # Create Document AI request
            raw_document = documentai.RawDocument(
                content=document_content,
                mime_type=mime_type
            )
            
            request = documentai.ProcessRequest(
                name=self._get_processor_name(),
                raw_document=raw_document
            )
            
            # Process document
            logger.info(f"Processing document: {gcs_uri}")
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract structured data
            extracted_data = {
                "text": document.text,
                "pages": len(document.pages),
                "tables": self._extract_tables(document),
                "entities": self._extract_entities(document),
                "confidence": document.pages[0].confidence if document.pages else 0.0
            }
            
            logger.info(f"Document processed successfully: {len(extracted_data['tables'])} tables, {len(extracted_data['entities'])} entities")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error processing document with Document AI: {e}")
            raise
    
    def _extract_tables(self, document: documentai.Document) -> List[Dict]:
        """
        Extract tables from document.
        
        Args:
            document: Processed document from Document AI
            
        Returns:
            List of tables with headers and rows
        """
        tables = []
        
        for page in document.pages:
            for table in page.tables:
                table_data = {
                    "headers": [],
                    "rows": [],
                    "page": page.page_number
                }
                
                # Extract headers (first row)
                if table.header_rows:
                    for cell in table.header_rows[0].cells:
                        cell_text = self._get_cell_text(cell, document.text)
                        table_data["headers"].append(cell_text)
                
                # Extract data rows
                for row in table.body_rows:
                    row_data = []
                    for cell in row.cells:
                        cell_text = self._get_cell_text(cell, document.text)
                        row_data.append(cell_text)
                    table_data["rows"].append(row_data)
                
                tables.append(table_data)
        
        return tables
    
    def _extract_entities(self, document: documentai.Document) -> List[Dict]:
        """
        Extract named entities from document.
        
        Args:
            document: Processed document from Document AI
            
        Returns:
            List of entities with type, value, and confidence
        """
        entities = []
        
        for entity in document.entities:
            entities.append({
                "type": entity.type_,
                "value": entity.mention_text,
                "confidence": entity.confidence,
                "normalized_value": entity.normalized_value.text if entity.normalized_value else None
            })
        
        return entities
    
    def _get_cell_text(self, cell, document_text: str) -> str:
        """
        Extract text from a table cell.
        
        Args:
            cell: Table cell from Document AI
            document_text: Full document text
            
        Returns:
            Cell text content
        """
        # Get text from layout
        text_segments = []
        for segment in cell.layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else len(document_text)
            text_segments.append(document_text[start_index:end_index])
        
        return " ".join(text_segments).strip()
    
    async def batch_process_documents(
        self,
        gcs_input_uri: str,
        gcs_output_uri: str,
        mime_type: str = "application/pdf"
    ) -> str:
        """
        Process multiple documents in batch.
        
        Args:
            gcs_input_uri: GCS URI pattern for input documents (e.g., gs://bucket/input/)
            gcs_output_uri: GCS URI for output (e.g., gs://bucket/output/)
            mime_type: MIME type of documents
            
        Returns:
            Operation name for tracking batch processing
        """
        try:
            # Configure batch processing
            gcs_documents = documentai.GcsDocuments(
                documents=[
                    documentai.GcsDocument(
                        gcs_uri=gcs_input_uri,
                        mime_type=mime_type
                    )
                ]
            )
            
            input_config = documentai.BatchDocumentsInputConfig(
                gcs_documents=gcs_documents
            )
            
            output_config = documentai.DocumentOutputConfig(
                gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
                    gcs_uri=gcs_output_uri
                )
            )
            
            request = documentai.BatchProcessRequest(
                name=self._get_processor_name(),
                input_documents=input_config,
                document_output_config=output_config
            )
            
            # Start batch processing
            operation = self.client.batch_process_documents(request)
            
            logger.info(f"Batch processing started: {operation.operation.name}")
            return operation.operation.name
            
        except Exception as e:
            logger.error(f"Error starting batch processing: {e}")
            raise


# Global instance
document_ai_service = DocumentIntelligenceService()
