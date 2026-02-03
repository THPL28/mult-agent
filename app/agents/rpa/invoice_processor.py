"""
🧾 Invoice Processor Agent - Placeholder
This agent will be implemented in the future
"""

from typing import Dict, Any
import logging

logger = logging.getLogger("InvoiceProcessor")


class InvoiceProcessorAgent:
    """Placeholder for Invoice Processor Agent"""
    
    def __init__(self):
        self.name = "InvoiceProcessorAgent"
        logger.info("Invoice Processor Agent initialized (placeholder)")
    
    async def process(self, invoice_path: str) -> Dict[str, Any]:
        """Process invoice - placeholder"""
        return {
            "status": "not_implemented",
            "message": "Invoice processor will be implemented soon"
        }


# Agent instance
agent = InvoiceProcessorAgent()
