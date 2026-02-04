# AI-Enhanced Invoice Parsing

## Overview

This document provides a comprehensive guide for implementing AI-powered invoice parsing to significantly improve accuracy and reliability compared to the current regex-based approach.

## Problem Statement

**Current Issue:** "interpretarea corecta a facturilor nu functioneaza" (Correct interpretation of invoices doesn't work)

The current invoice parser uses regex patterns and basic text extraction, which results in:
- **60-70% overall accuracy** (see PARSING_ACCURACY.md for details)
- Poor handling of complex invoice layouts
- Struggles with multi-line descriptions
- Inconsistent extraction of Romanian invoices
- High failure rate on e-factura formats

## Solution: AI-Powered Parsing

Using Large Language Models (LLMs) like GPT-4, Claude, or open-source alternatives can achieve **95%+ accuracy** with better handling of:
- Any invoice format or layout
- Multi-language content (Romanian, English, etc.)
- Complex tables and structures
- Scanned or image-based documents
- Non-standard formats

## Architecture

### Hybrid Parsing System

```
┌─────────────────┐
│ Invoice Upload  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Parsing Method Selector │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌────────┐
│Standard│  │  AI    │
│Parser  │  │ Parser │
│(Free)  │  │(Paid)  │
│60-70%  │  │  95%+  │
└───┬────┘  └────┬───┘
    │           │
    └─────┬─────┘
          ▼
┌──────────────────┐
│  Structured JSON │
│   Extraction     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Validation UI   │
│ (User confirms)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Material Creation│
│ + Stock Update   │
└──────────────────┘
```

## Implementation Options

### Option 1: OpenAI GPT-4 (Recommended)

**Pros:**
- Highest accuracy (95%+)
- Excellent Romanian language support
- GPT-4 Vision for scanned documents
- Simple API integration
- Reliable structured outputs

**Cons:**
- Requires API key ($)
- Data sent to external service
- ~$0.01-0.05 per invoice

**Setup:**
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

**Code Example:**
```python
import openai
import json
from pathlib import Path

EXTRACTION_PROMPT = """
Extract invoice data from this image in JSON format with this exact structure:

{
  "supplier": "Company name",
  "invoice_number": "Invoice number",
  "date": "YYYY-MM-DD",
  "total": 12345.67,
  "currency": "RON",
  "items": [
    {
      "description": "Product description",
      "quantity": 10,
      "unit": "buc",
      "unit_price": 100.00,
      "total": 1000.00
    }
  ]
}

Rules:
- Extract ALL line items from the invoice
- Preserve exact quantities and prices
- Use ISO date format (YYYY-MM-DD)
- Include currency (RON, EUR, USD)
- Romanian units: buc (bucăți), kg, m, l, h
- If a field is not found, use null
- Ensure all numbers are numeric, not strings
"""

def parse_invoice_with_gpt4(file_path: str, file_type: str) -> dict:
    """Parse invoice using OpenAI GPT-4 Vision"""
    
    # Convert PDF/DOC to image if needed
    if file_type == "PDF":
        image_url = convert_pdf_to_image(file_path)
    elif file_type in ["DOC", "DOCX"]:
        image_url = convert_doc_to_image(file_path)
    else:
        # For image files, encode as base64
        with open(file_path, "rb") as f:
            import base64
            image_data = base64.b64encode(f.read()).decode()
            image_url = f"data:image/png;base64,{image_data}"
    
    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=4096
    )
    
    # Parse structured JSON response
    data = json.loads(response.choices[0].message.content)
    
    return {
        "supplier": data.get("supplier"),
        "invoice_number": data.get("invoice_number"),
        "invoice_date": data.get("date"),
        "total_amount": data.get("total"),
        "currency": data.get("currency", "RON"),
        "items": [
            {
                "description": item["description"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "unit_price": item["unit_price"],
                "total": item["total"]
            }
            for item in data.get("items", [])
        ],
        "raw_text": "",  # Optional: keep for reference
        "confidence": 0.95  # AI parsing confidence
    }
```

### Option 2: Anthropic Claude

**Pros:**
- Comparable accuracy to GPT-4
- Lower cost (~$0.005-0.02 per invoice)
- Strong reasoning capabilities
- JSON mode support

**Cons:**
- Requires separate API key
- No vision API yet (needs PDF-to-text)

**Setup:**
```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Code Example:**
```python
import anthropic
import json

def parse_invoice_with_claude(text: str) -> dict:
    """Parse invoice using Claude"""
    
    client = anthropic.Anthropic()
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\nInvoice text:\n{text}"
            }
        ]
    )
    
    data = json.loads(message.content[0].text)
    return data
```

### Option 3: Open Source (Self-Hosted)

**Pros:**
- Free (after server costs)
- Complete data privacy
- No external dependencies
- Customizable

**Cons:**
- Requires GPU server
- Lower accuracy (~85-90%)
- Complex setup
- Maintenance overhead

**Options:**
- Llama 3 70B (best accuracy)
- Mistral 7B (faster, smaller)
- Phi-3 (lightweight)

**Setup:**
```bash
# Using Ollama for easy deployment
curl https://ollama.ai/install.sh | sh
ollama pull llama3:70b
```

**Code Example:**
```python
import ollama
import json

def parse_invoice_with_llama(text: str) -> dict:
    """Parse invoice using local Llama model"""
    
    response = ollama.chat(
        model='llama3:70b',
        messages=[
            {
                'role': 'user',
                'content': f"{EXTRACTION_PROMPT}\n\nInvoice text:\n{text}"
            }
        ],
        format='json'
    )
    
    data = json.loads(response['message']['content'])
    return data
```

## Implementation Phases

### Phase 1: Configuration & Setup (1 day)

**Tasks:**
1. Add AI configuration to .env
2. Install required libraries
3. Add API key management
4. Create fallback mechanism

**Files to Modify:**
- `requirements.txt` - Add openai/anthropic
- `.env.example` - Add AI configuration
- `app/config.py` - Load AI settings

**.env Configuration:**
```env
# AI Invoice Parsing
ENABLE_AI_PARSING=true
AI_PROVIDER=openai  # openai, anthropic, or local
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Cost limits
AI_PARSING_MAX_COST_PER_MONTH=50.00
AI_PARSING_AUTO_FALLBACK=true
```

### Phase 2: AI Parser Implementation (2-3 days)

**Tasks:**
1. Create ai_parser.py module
2. Implement GPT-4/Claude integration
3. Add error handling and retries
4. Implement cost tracking
5. Add confidence scoring

**New File: `app/ai_parser.py`**
```python
import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIInvoiceParser:
    """AI-powered invoice parser using LLMs"""
    
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai")
        self.enabled = os.getenv("ENABLE_AI_PARSING", "false").lower() == "true"
        self.cost_tracker = CostTracker()
    
    def parse(self, file_path: str, file_type: str) -> Dict:
        """Parse invoice using AI"""
        
        if not self.enabled:
            raise ValueError("AI parsing not enabled")
        
        # Check cost limits
        if not self.cost_tracker.can_process():
            logger.warning("AI parsing cost limit reached, using fallback")
            return self.fallback_parse(file_path, file_type)
        
        try:
            # Choose provider
            if self.provider == "openai":
                result = self.parse_with_openai(file_path, file_type)
            elif self.provider == "anthropic":
                result = self.parse_with_anthropic(file_path, file_type)
            elif self.provider == "local":
                result = self.parse_with_local(file_path, file_type)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
            
            # Track cost
            self.cost_tracker.record(result.get("cost", 0.02))
            
            return result
            
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            # Fallback to standard parser
            return self.fallback_parse(file_path, file_type)
    
    def parse_with_openai(self, file_path: str, file_type: str) -> Dict:
        """Parse using OpenAI GPT-4"""
        # Implementation from Option 1 above
        pass
    
    def fallback_parse(self, file_path: str, file_type: str) -> Dict:
        """Fallback to standard parser"""
        from invoice_parser import parse_file
        return parse_file(file_path, file_type)

class CostTracker:
    """Track AI parsing costs"""
    
    def __init__(self):
        self.max_monthly = float(os.getenv("AI_PARSING_MAX_COST_PER_MONTH", "50.00"))
        self.current_month_cost = self.load_current_cost()
    
    def can_process(self) -> bool:
        """Check if under cost limit"""
        return self.current_month_cost < self.max_monthly
    
    def record(self, cost: float):
        """Record cost of processing"""
        self.current_month_cost += cost
        self.save_cost()
    
    def load_current_cost(self) -> float:
        """Load current month cost from database"""
        # TODO: Implement database storage
        return 0.0
    
    def save_cost(self):
        """Save current cost to database"""
        # TODO: Implement database storage
        pass
```

### Phase 3: UI Integration (1-2 days)

**Tasks:**
1. Add parsing method selector
2. Show cost per invoice
3. Display confidence scores
4. Add manual correction UI
5. Show cost statistics

**Frontend Changes (frontend/app.js):**
```javascript
function showUploadInvoiceForm() {
    const html = `
        <div class="modal">
            <div class="modal-content">
                <h2>Upload Invoice</h2>
                
                <!-- Parsing Method Selector -->
                <div class="form-group">
                    <label>Parsing Method:</label>
                    <select id="parsingMethod">
                        <option value="standard">Standard (Free, 60-70% accuracy)</option>
                        <option value="ai" ${aiEnabled ? '' : 'disabled'}>
                            AI Enhanced (${aiCostPerInvoice}, 95%+ accuracy)
                        </option>
                    </select>
                    ${!aiEnabled ? '<small>AI parsing not configured</small>' : ''}
                </div>
                
                <!-- File Upload -->
                <div class="form-group">
                    <label>Select Invoice File:</label>
                    <input type="file" id="invoiceFile" 
                           accept=".pdf,.doc,.docx,.txt,.xml">
                </div>
                
                <!-- Cost Display -->
                <div id="costDisplay" style="display:none">
                    <p>Estimated cost: <strong id="estimatedCost">$0.02</strong></p>
                    <p>Monthly usage: $<span id="monthlyUsage">0.00</span> / $50.00</p>
                </div>
                
                <div class="modal-actions">
                    <button onclick="uploadInvoiceFile()">Upload & Parse</button>
                    <button onclick="closeModal()">Cancel</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Show cost when AI selected
    document.getElementById('parsingMethod').addEventListener('change', (e) => {
        const costDisplay = document.getElementById('costDisplay');
        costDisplay.style.display = e.target.value === 'ai' ? 'block' : 'none';
    });
}

async function uploadInvoiceFile() {
    const file = document.getElementById('invoiceFile').files[0];
    const method = document.getElementById('parsingMethod').value;
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('parsing_method', method);
    
    try {
        const response = await fetch('/api/invoices/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeModal();
            
            // Show parsing results with confidence
            showInvoiceValidation(data.invoice_id, {
                ...data,
                parsing_method: method,
                confidence: data.confidence || 0.6
            });
        } else {
            alert('Error: ' + data.detail);
        }
    } catch (error) {
        alert('Error uploading invoice: ' + error.message);
    }
}
```

## Cost Analysis

### OpenAI GPT-4 Pricing

**GPT-4 Vision:**
- Input: $0.01 per 1K tokens
- Output: $0.03 per 1K tokens
- Average invoice: ~2K input + 500 output = $0.035

**Monthly Costs (Estimates):**
- 10 invoices: ~$0.35
- 50 invoices: ~$1.75
- 100 invoices: ~$3.50
- 500 invoices: ~$17.50

### Anthropic Claude Pricing

**Claude 3 Sonnet:**
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens
- Average invoice: ~2K input + 500 output = $0.013

**Monthly Costs:**
- 10 invoices: ~$0.13
- 50 invoices: ~$0.65
- 100 invoices: ~$1.30
- 500 invoices: ~$6.50

### Cost Optimization

**Strategies:**
1. **Caching** - Cache processed invoices
2. **Batch Processing** - Process multiple invoices together
3. **Smart Fallback** - Use AI only for complex invoices
4. **Local Models** - Self-host for high volume
5. **Confidence Threshold** - Re-parse only low confidence results

## Privacy & Security

### Data Handling

**OpenAI:**
- Data sent to OpenAI servers (encrypted)
- Zero data retention policy available
- GDPR compliant with proper setup
- Enterprise option: Azure OpenAI (EU regions)

**Anthropic:**
- Data sent to Anthropic servers
- No training on user data
- GDPR compliant

**Self-Hosted:**
- Complete data privacy
- No external data sharing
- Full control

### Recommendations

1. **User Consent** - Get explicit consent for AI processing
2. **Data Anonymization** - Remove PII before processing if possible
3. **Fallback Option** - Always offer non-AI parsing
4. **Audit Logs** - Track all AI processing
5. **Enterprise Setup** - Use Azure OpenAI for EU data residency

## Testing Strategy

### Test Cases

1. **Romanian E-Factura** - UBL XML format
2. **PDF Invoice** - Standard layout
3. **Scanned Invoice** - Image-based PDF
4. **Complex Layout** - Multi-column, tables
5. **Multi-Page** - 5+ page invoices
6. **Handwritten** - Partially handwritten

### Success Criteria

- **Accuracy**: 95%+ field extraction
- **Speed**: < 5 seconds per invoice
- **Cost**: < $0.05 per invoice
- **Reliability**: 99%+ uptime
- **User Satisfaction**: 90%+ approval rating

## Monitoring & Analytics

### Metrics to Track

1. **Accuracy Rate** - % of correctly extracted fields
2. **Processing Time** - Average time per invoice
3. **Cost Per Invoice** - Actual cost tracking
4. **Monthly Spend** - Total AI costs
5. **Error Rate** - Failed parsing attempts
6. **User Corrections** - How often users fix data

### Dashboard

```
AI Invoice Parsing Analytics
═══════════════════════════════════════

This Month:
  Invoices Processed: 127
  AI Parsing: 89 (70%)
  Standard Parsing: 38 (30%)
  
Accuracy:
  AI Parser: 96.5%
  Standard Parser: 64.2%
  
Costs:
  Total: $3.12 / $50.00 (6.2%)
  Avg per Invoice: $0.035
  Projected Month: $4.45
  
Performance:
  Avg Processing Time: 3.2s
  Success Rate: 98.9%
  User Corrections: 4.5%
```

## Migration Path

### Step 1: Enhanced Standard Parser (Immediate)

Improve current regex parser while preparing for AI:
- Better Romanian patterns
- Improved table detection
- More robust extraction

### Step 2: Optional AI Parsing (Week 1-2)

Add AI as optional feature:
- Keep standard parser as default
- Add AI toggle in UI
- Start with low volume testing

### Step 3: Hybrid System (Week 3-4)

Intelligent auto-selection:
- Use standard for simple invoices
- Use AI for complex invoices
- Learn from user corrections
- Optimize costs automatically

## Conclusion

AI-powered invoice parsing can dramatically improve accuracy from 60-70% to 95%+, with reasonable costs (~$0.01-0.05 per invoice) and relatively simple implementation.

**Recommended Approach:**
1. Start with OpenAI GPT-4 (easiest, highest accuracy)
2. Implement as optional feature alongside current parser
3. Monitor accuracy and costs
4. Expand to default for all invoices if successful
5. Consider self-hosted models for very high volume

This hybrid approach provides immediate value while maintaining flexibility and cost control.
