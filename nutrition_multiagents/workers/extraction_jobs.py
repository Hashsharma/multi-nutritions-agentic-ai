import re
import fitz

class LegalTextParser:

    def __init__(self):
        self.section = None
        self.subsection = None

    # -----------------------------
    # Detect patterns
    # -----------------------------
    def is_section(self, line):
        # Section: "1. Definitions" 
        return re.match(r'^\d+\.\s+[A-Z]', line) and not re.match(r'^\d+\.\d+', line)

    def is_subsection(self, line):
        # Subsection: "1.1 The following words..."
        return re.match(r'^\d+\.\d+\s+', line)

    def is_clause(self, line):
        # Clause: "(a) “Contract” means..."
        return re.match(r'^\([a-z]\)\s+', line)

    # -----------------------------
    # Extract definition
    # -----------------------------
    def extract_definition(self, text):
        pattern = r'“([^”]+)”\s+means\s+(.+?)(?=\s*\([a-z]\)\s+“|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            definition = re.sub(r'\s+', ' ', definition)
            return term, definition

        return None, None

    

    # -----------------------------
    # Process each clause block
    # -----------------------------
    def process_buffer(self, text):
        term, definition = self.extract_definition(text)

        if term:
            return {
                "text": f"Term: {term}\nDefinition: {definition}",
                "metadata": {
                    "section": self.section,
                    "subsection": self.subsection,
                    "type": "definition",
                    "term": term,
                    "definition": definition
                }
            }

        return {
            "text": text.strip(),
            "metadata": {
                "section": self.section,
                "subsection": self.subsection,
                "type": "text"
            }
        }
    

    # -----------------------------
    # Main parser
    # -----------------------------
    def parse(self, raw_text):
        lines = raw_text.split("\n")
        
        chunks = []
        buffer = ""
        in_definition_block = False

        for line in lines:
            original_line = line
            line = line.strip()


            if not line:
                continue
            
            # print("this is the line",  self.is_section(original_line))

            # SECTION
            if self.is_section(original_line):
                if buffer:
                    chunks.append(self.process_buffer(buffer))
                    buffer = ""


                self.section = re.sub(r'^\d+\.\s+', '', original_line).strip()
                

                self.subsection = None
                in_definition_block = False

                continue
            

            # SUBSECTION
            if self.is_subsection(original_line):
                if buffer:
                    chunks.append(self.process_buffer(buffer))
                    buffer = ""
                
                self.subsection = re.sub(r'^\d+\.\d+\s+', '', original_line).strip()
                in_definition_block = True

                continue
            

            # CLAUSE START
            if self.is_clause(original_line):
                if buffer:
                    chunks.append(self.process_buffer(buffer))
                    buffer = ""
                
                buffer += line + " "
                in_definition_block = True
                continue

            # CONTINUATION
            if in_definition_block:
                buffer += line + " "
            else:
                buffer += line + " "       
        

        # Flush last buffer
        if buffer:
            chunks.append(self.process_buffer(buffer))
        return [c for c in chunks if c]


# FIXED PDF Processing Functions
def extract_pdf_text(pdf_path):
    """Extract text while preserving document structure"""
    doc = fitz.open(pdf_path)
    full_text = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text.append(text)
    
    return "\n".join(full_text)


def simple_chunk_by_heading(text):
    """Simple chunking by section headings"""
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_title = "Unknown"
    
    # Pattern for section headings like "1. Definitions" or "2. Contract Documents"
    heading_pattern = re.compile(r'^\s*(\d+\.\s+[A-Z][A-Za-z\s]+)$')
    
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
            
        match = heading_pattern.match(line)
        if match:
            # Save previous chunk
            if current_chunk:
                chunks.append({
                    "title": current_title,
                    "text": "\n".join(current_chunk)
                })
            # Start new chunk
            current_title = match.group(1).strip()
            current_chunk = [line]
        else:
            current_chunk.append(line)
    
    # Add last chunk
    if current_chunk:
        chunks.append({
            "title": current_title,
            "text": "\n".join(current_chunk)
        })
    
    return chunks


# MAIN PROCESSING FUNCTION
def process_legal_document(pdf_path, doc_id):
    """Complete pipeline for processing legal documents"""
    
    # Step 1: Extract raw text from PDF
    print(f"Extracting text from {pdf_path}...")
    raw_text = extract_pdf_text(pdf_path)
    
    # Step 2: Chunk by headings
    print("Chunking by headings...")
    heading_chunks = simple_chunk_by_heading(raw_text)
    
    # Step 3: Parse each chunk with LegalTextParser
    print("Parsing legal definitions...")
    parser = LegalTextParser()
    all_parsed_chunks = []
    
    for i, chunk in enumerate(heading_chunks):
        # print(f"  Processing chunk {i+1}: {chunk['title']}")
        parsed = parser.parse(chunk['text'])
        # print(f"  Processing chunk {i+1}: {chunk['text']}")

        for item in parsed:
            item['metadata']['doc_id'] = doc_id
            item['metadata']['chunk_index'] = i
            all_parsed_chunks.append(item)
    
    print("all chunks", all_parsed_chunks)
    return all_parsed_chunks


# # USAGE EXAMPLE
# pdf_path = "/home/scientist-ubuntu/projects/multi-nutritions-agentic-ai/vvvvrresources/legal_docs.pdf"
# doc_id = "legal_query_rag"

# # Process the document
# parsed_results = process_legal_document(pdf_path, doc_id)

# # Display results
# print(f"\n{'='*80}")
# print(f"FOUND {len(parsed_results)} PARSED ITEMS")
# print(f"{'='*80}\n")
