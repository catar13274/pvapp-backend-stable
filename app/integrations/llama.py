"""
Llama 3 Integration
AI-powered assistant for invoice processing and material management
"""
from typing import Optional, Dict, List
import os

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LlamaAssistant:
    def __init__(self, model_path: Optional[str] = None):
        if Llama is None:
            raise ImportError("llama-cpp-python is not installed")
        
        self.model_path = model_path or os.getenv("LLAMA_MODEL_PATH", "./models/llama-3-8b.gguf")
        self.llm = None
        
    def load_model(self):
        """Load Llama 3 model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0
        )
    
    def extract_invoice_data(self, invoice_text: str) -> Dict:
        """Use AI to extract structured data from invoice text"""
        if not self.llm:
            self.load_model()
        
        prompt = f"""Extract the following information from this invoice text:
- Invoice number
- Date
- Supplier name
- Total amount
- Line items (description, quantity, price)

Invoice text:
{invoice_text}

Respond in JSON format."""
        
        response = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.1,
            stop=["</s>"]
        )
        
        return self._parse_llm_response(response['choices'][0]['text'])
    
    def match_material_sku(self, description: str, existing_materials: List[Dict]) -> Optional[int]:
        """Use AI to match invoice item description to existing material SKU"""
        if not self.llm:
            self.load_model()
        
        materials_list = "\n".join([
            f"- ID: {m['id']}, SKU: {m['sku']}, Name: {m['name']}"
            for m in existing_materials
        ])
        
        prompt = f"""Given this invoice item description: "{description}"
        
Find the best matching material from this list:
{materials_list}

Respond with only the material ID number, or 'NONE' if no good match."""
        
        response = self.llm(
            prompt,
            max_tokens=10,
            temperature=0.1
        )
        
        result = response['choices'][0]['text'].strip()
        
        try:
            return int(result)
        except ValueError:
            return None
    
    def suggest_stock_reorder(self, material_data: Dict, usage_history: List[Dict]) -> Dict:
        """AI-powered stock reorder suggestion"""
        if not self.llm:
            self.load_model()
        
        prompt = f"""Based on this material data:
Name: {material_data['name']}
Current stock: {material_data['current_stock']}
Minimum stock: {material_data['min_stock']}

Recent usage history:
{usage_history}

Should we reorder? Suggest optimal reorder quantity and timing.
Respond in JSON format with: should_reorder, suggested_quantity, reasoning"""
        
        response = self.llm(
            prompt,
            max_tokens=256,
            temperature=0.3
        )
        
        return self._parse_llm_response(response['choices'][0]['text'])
    
    def chat_assistant(self, user_message: str, context: Optional[Dict] = None) -> str:
        """General chat assistant for business queries"""
        if not self.llm:
            self.load_model()
        
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        prompt = f"""You are a helpful assistant for a materials management system.
{context_str}

User question: {user_message}

Assistant response:"""
        
        response = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.7
        )
        
        return response['choices'][0]['text'].strip()
    
    def _parse_llm_response(self, text: str) -> Dict:
        """Parse LLM JSON response"""
        import json
        try:
            # Try to extract JSON from response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        return {"raw_response": text}