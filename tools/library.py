import os
from tqdm import tqdm
from langchain import OpenAI

from langchain.tools import Tool

#Memory Document Loader (Unstructured)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA

from langchain.document_loaders.unstructured import UnstructuredBaseLoader
from unstructured.cleaners.core import clean_extra_whitespace
from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf
from typing import IO, Any, Callable, Dict, List, Optional, Sequence, Union

import weaviate
from langchain.vectorstores import Weaviate

WEAVIATE_URL = os.getenv('WEAVIATE_URL')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Essa versão da classe aplica corretamente os _post_processors.
# Talvez valha um pull request depois.
class FixedUnstructuredFileLoader(UnstructuredBaseLoader):
      def __init__(
          self,
          file_path: Union[str, List[str]],
          mode: str = "paged",
          **unstructured_kwargs: Any,
      ):
          """Initialize with file path."""
          self.file_path = file_path
          super().__init__(mode=mode, **unstructured_kwargs)


      def _get_elements(self) -> List:
          from unstructured.partition.auto import partition
          elements = partition(filename=self.file_path, **self.unstructured_kwargs)
          return self._post_process_elements(elements)

      def _post_process_elements(self, elements):
        """Applies post-processing functions to extracted unstructured elements.
        Post-processing functions are Element -> Element callables passed
        in using the post_processors kwarg when the loader is instantiated."""
        print("Post processing...")
        for element in elements:
            for post_processor in self.post_processors:
                element.apply(post_processor)
        return elements

      def _get_metadata(self) -> dict:
          return {"source": self.file_path}



class Library:
    def __init__(self, llm=OpenAI()):
        self.client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY),
            additional_headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
        )
        self.llm = llm
        self.tools = []

    def create_index(self, index_name):
        print(f"Criando índice {index_name}")
        self.client.schema.create_class({
            "class": index_name,
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                },
                {
                    "name": "source",
                    "dataType": ["text"],
                    "description": "The source path of the file"
                }
            ],
            "vectorizer": "text2vec-openai"
        })
    
    def check_existing_file(self, filename, index_name):
    #checa se o arquivo já esta indexado
        print(f"Verificando se o arquivo {filename} já está indexado...")
        file_indexed = self.client.query.get(index_name, "source").with_where({
            "path": ["source"],
            "operator": "Equal",
            "valueText": filename
        }).with_limit(1).do()
        
        check = file_indexed and len(file_indexed["data"]["Get"][index_name]) == 1
        return(check)
    
    def load_file_embeddings(self, filename, index_name):
        if self.check_existing_file(filename, index_name):
            print(f"Arquivo {filename} já carregado")
            return None
        print(f"Carregando {filename}")
        loader = FixedUnstructuredFileLoader(filename, mode="paged", post_processors = [])#replace_art, clean_extra_whitespace
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        #dirty fix for pdf coordinates 
        #ao invés disso ele precisa iterar e criar os datatypes correspondentes pra classe
        clear_texts = []
        for index,text in enumerate(texts):
            if text.metadata.get('coordinates'):
                texts[index].metadata['coordinates'] = None

        embeddings = OpenAIEmbeddings()
        
        
        print("Subindo no Weaviate...")
        db = Weaviate.from_documents(texts, embedding=None, index_name=index_name, client=self.client, by_text=False)

    def build_tool(self, index_name, description):
        print("Construindo ferramenta")
        from langchain.retrievers import WeaviateHybridSearchRetriever
        retriever = WeaviateHybridSearchRetriever(
            client=self.client,
            index_name=index_name,
            text_key="text",
            attributes=[],
            create_schema_if_missing=False
        )

        tool_fn = RetrievalQA.from_chain_type(
            llm=self.llm, chain_type="stuff", retriever=retriever
        )

        tool = Tool(name=f"Biblioteca {index_name}",
                func=tool_fn.run,
                description=description)

        return tool

    def generate_tools_for_library(self, library_path):
        print("Generating tools for library...")
        subfolders = [f for f in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, f)) and not f.startswith('.')]
        for index_name in tqdm(subfolders, desc="Processing subfolders"):
            index_path = os.path.join(library_path, index_name)
            index_name_camel_case = ''.join(word.capitalize() for word in index_name.split('_'))
            description_file_path = os.path.join(index_path, 'description.txt')
            if os.path.exists(description_file_path):
                with open(description_file_path, 'r') as description_file:
                    description = description_file.read().strip()
            else:
                print(f"Warning: description.txt not found in {index_path}. Skipping.")
                continue
            for filename in os.listdir(index_path):
                file_path = os.path.join(index_path, filename)
                if os.path.isfile(file_path) and filename != 'description.txt':
                    self.load_file_embeddings(file_path, index_name_camel_case)        
            tool = self.build_tool(index_name_camel_case, description)
            self.tools.append(tool)
        return self.tools


