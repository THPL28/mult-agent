from typing import Any, Dict, Optional
import logging
import os
from bs4 import BeautifulSoup
import markdownify
from pdfminer.high_level import extract_text

logger = logging.getLogger("MarkItDownAgent")

class MarkItDownAgent:
    """
    Real-world MarkItDown Agent.
    Converts PDF, HTML, and Text into standardized, semantic Markdown.
    """
    
    async def process(self, file_path: str, content_type: str = None) -> Dict[str, Any]:
        """
        Process the input file and return structured Markdown.
        """
        logger.info(f"Processing file: {file_path} [{content_type}]")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        markdown_content = ""
        metadata = {"source": file_path, "type": content_type}

        # Determine type by extension if content_type is ambiguous
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".pdf" or (content_type and "pdf" in content_type):
                markdown_content = self._convert_pdf(file_path)
                metadata["converter"] = "pdfminer.six"
            
            elif ext in [".html", ".htm"] or (content_type and "html" in content_type):
                markdown_content = self._convert_html(file_path)
                metadata["converter"] = "beautifulsoup+markdownify"
            
            elif ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    markdown_content = f.read()
                metadata["converter"] = "text_pass_through"
            
            else:
                # Fallback to simple text read
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        markdown_content = f.read()
                except:
                     markdown_content = f"__Binary file {ext} not supported for direct text conversion yet.__"
        
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            markdown_content = f"> **Error**: Failed to convert file.\n> {str(e)}"

        return {
            "markdown": markdown_content,
            "metadata": metadata
        }

    def _convert_html(self, file_path: str) -> str:
        """
        Uses BeautifulSoup to clean HTML and Markdownify to convert.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        # Clean soup
        soup = BeautifulSoup(html_content, "html.parser")
        # Remove scripts and styles
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        # Convert to markdown
        md = markdownify.markdownify(str(soup), heading_style="ATX")
        return md.strip()

    def _convert_pdf(self, file_path: str) -> str:
        """
        Extracts text from PDF using pdfminer.six.
        Future improvement: Use OCR for scanned PDFs (requires tesseract).
        """
        text = extract_text(file_path)
        # Basic cleanup: Remove excessive newlines
        clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
        
        return f"## PDF Content\n\n{clean_text}"

agent = MarkItDownAgent()
