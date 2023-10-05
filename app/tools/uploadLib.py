import os
import argparse
from tqdm import tqdm
from typing import List
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.cleaners.core import clean_extra_whitespace, group_broken_paragraphs
import weaviate
import logging

logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

class Library:
    def __init__(self, weaviate_url, weaviate_api_key):
        auth_config = weaviate.AuthApiKey(api_key=weaviate_api_key)
        self.client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=auth_config,
            additional_headers={"X-OpenAI-Api-Key": os.getenv('OPENAI_API_KEY')}
        )

    def get_sources(self,question):
        nearText = {
            "concepts": question,
            }
    
        result = (self.client.query
                  .get("Document", ["content", "pageOrChunk", "fileName"])
                  .with_near_text(nearText)
                  .with_limit(3)
                  .do())

        return(result)


class WeaviateUploader:
    def __init__(self, weaviate_url, weaviate_api_key):
        auth_config = weaviate.AuthApiKey(api_key=weaviate_api_key)
        self.client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=auth_config,
            additional_headers={"X-OpenAI-Api-Key": os.getenv('OPENAI_API_KEY')}
        )
        if not self.client.schema.exists("Document"):
            self.create_schema()
        

    def create_schema(self):
        document_schema = {
            "class": "Document",
            "description": "A collection of documents",
            "vectorizer": "text2vec-openai",
            "properties": [
                {
                    "name": "fileName",
                    "description": "Name of the file",
                    "dataType": ["string"]
                },
                {
                    "name": "pageOrChunk",
                    "description": "Page or chunk of the document",
                    "dataType": ["number"]
                },
                {
                    "name": "content",
                    "description": "Content of the document",
                    "dataType": ["text"]
                }
            ],
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": True
                }
            } 
        }

        
        self.client.schema.create_class(document_schema)
        
    def check_existing_file(self, filename):
        console.debug(f"Verificando se o arquivo {filename} já está indexado...")
        query = self.client.query.get("Document", ["fileName"]).with_where({
            "path": ["fileName"],
            "operator": "Equal",
            "valueText": filename
        }).with_limit(1).do()
        return bool(query and query["data"]["Get"]["Document"])

    def upload_file(self, file_path, index_name):
        if self.check_existing_file(file_path):
            return None
        console.debug(f"Particionando {file_path}...")
        documents = partition(filename=file_path, include_page_breaks=True)
        chunks = chunk_by_title(documents)
        weaviate_objects = []
        for index, doc in enumerate(chunks):
            content = doc.__str__()
            clean_extra_whitespace(content)
            group_broken_paragraphs(content)
            pg = doc.metadata.page_number
            if not pg:
                pg = index
            
            if content:
                obj = {
                        "fileName": file_path,
                        "pageOrChunk": pg,
                        "content": content
                }
                #console.info(obj)
                weaviate_objects.append(obj)

        console.info(f"Subindo {file_path} no Weaviate...")
        for obj in tqdm(weaviate_objects):
            #pass
            self.client.data_object.create(obj, index_name)
        
    def iterate_directory_and_upload(self, directory_path, index_name, allowed_filetypes):
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_type = file_path.split('.')[-1]
                
                if file_type in allowed_filetypes:
                    self.upload_file(file_path, index_name)
                else:
                    console.debug(f"Tipo de arquivo {file_type} não é permitido. Ignorando {file}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Weaviate File Uploader")
    parser.add_argument("action", choices=['upload', 'query'], help="Action to perform: upload files or query using get_sources.")
    parser.add_argument("--directory", help="Path to the directory you want to upload files from.")
    parser.add_argument("--question", help="The question for get_sources, only needed if action is 'query'.")
    args = parser.parse_args()
    
    WEAVIATE_URL = os.getenv('WEAVIATE_URL')
    WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')

    if args.action == "upload":
        uploader = WeaviateUploader(WEAVIATE_URL, WEAVIATE_API_KEY)
        uploader.iterate_directory_and_upload(args.directory, "Document", ['pdf', 'txt', 'docx'])
    elif args.action == "query":
        if not args.question:
            print("You need to specify a question using --question when action is 'query'.")
        else:
            library = Library(WEAVIATE_URL, WEAVIATE_API_KEY)
            sources = library.get_sources(args.question)
            print(f"Sources for the question: {sources}")
