import bibtexparser
import pandas as pd
import re
from typing import List, Dict, Tuple
import os

class CochraneProcessor:
    def __init__(self, bib_file_path: str):
        self.bib_file_path = bib_file_path
        self.next_triple_id = 1
        self.next_property_id = 1
        
    def extract_drug_disease_relations(self, abstract: str) -> List[Tuple[str, str, str]]:
        """
        Extract drug-disease relationships and their nature (support/against/non-related)
        from the abstract text.
        Returns list of tuples (drug, relation, disease)
        """
        # Extract conclusion part from abstract
        conclusion_match = re.search(r"Authors['']?\s*conclusions?:?\s*([^.]+(?:\.[^.]+)*)", abstract, re.IGNORECASE)
        if not conclusion_match:
            return []
            
        conclusion = conclusion_match.group(1)
        
        # Extract drug names (simplified approach - can be enhanced with NLP)
        drug_names = set(re.findall(r'\b[A-Z][a-z]+(?:id|ine|ol|il|ate|ant|ene)\b', abstract))
        
        # Extract disease names (simplified approach)
        diseases = set(re.findall(r"(?:Alzheimer's disease|dementia|MCI|cognitive impairment)", abstract, re.IGNORECASE))
        
        relations = []
        for drug in drug_names:
            for disease in diseases:
                # Determine relationship based on conclusion text
                if any(word in conclusion.lower() for word in ['effective', 'improvement', 'beneficial', 'positive']):
                    relation = 'SUPPORT'
                elif any(word in conclusion.lower() for word in ['no effect', 'not effective', 'no difference']):
                    relation = 'AGAINST'
                else:
                    relation = 'NON_RELATED'
                    
                relations.append((drug, relation, disease))
                
        return relations

    def process_bib_to_triples(self) -> pd.DataFrame:
        """
        Process BibTeX file to create triples dataframe
        """
        with open(self.bib_file_path) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
            
        triples = []
        for entry in bib_database.entries:
            if 'abstract' not in entry:
                continue
                
            # Extract relationships
            relations = self.extract_drug_disease_relations(entry['abstract'])
            
            for drug, relation, disease in relations:
                triple = {
                    'id': self.next_triple_id,
                    'x_name': drug,
                    'x_type': 'drug',
                    'x_source': 'Cochrane Library',
                    'x_external_source_id': entry.get('ID', ''),
                    'relation': relation,
                    'y_name': disease,
                    'y_type': 'disease',
                    'y_source': 'Cochrane Library',
                    'y_external_source_id': entry.get('ID', '')
                }
                triples.append(triple)
                self.next_triple_id += 1
                
        return pd.DataFrame(triples)

    def process_bib_to_properties(self) -> pd.DataFrame:
        """
        Process BibTeX file to create properties dataframe
        """
        with open(self.bib_file_path) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
            
        properties = []
        for entry in bib_database.entries:
            property_entry = {
                'external_source_id': entry.get('ID', ''),
                'source_primary': 'Systematic Review',
                'source_secondary': 'Cochrane Library',
                'title': entry.get('title', ''),
                'source_link': entry.get('URL', ''),
                'source_date': f"{entry.get('year', '')}/1/1",
                'pubmed_id': '',  # BibTeX doesn't typically include PMID
                'country_of_origin': ''  # Would need additional processing to extract
            }
            properties.append(property_entry)
            self.next_property_id += 1
            
        return pd.DataFrame(properties)

    def process_and_save(self, output_dir: str):
        """
        Process BibTeX file and save results to CSV files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process and save triples
        triples_df = self.process_bib_to_triples()
        triples_df.to_csv(os.path.join(output_dir, '2_cochranelibrary_triple.csv'), index=False)
        
        # Process and save properties
        properties_df = self.process_bib_to_properties()
        properties_df.to_csv(os.path.join(output_dir, '3_cochranelibrary_property.csv'), index=False)

if __name__ == "__main__":
    processor = CochraneProcessor('data/dev/input/4_cochrane_Alzheimer_Systematic_Review.bib')
    processor.process_and_save('data/dev/output') 