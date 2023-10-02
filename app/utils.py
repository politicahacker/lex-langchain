import os
from huggingface_hub import hf_hub_download

MODEL_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

def download_model(repo, model_file):
    # Cria o diretório 'model' se ele não existir
    if not os.path.exists(MODEL_DIRECTORY):
        os.mkdir(MODEL_DIRECTORY)

    model_path = os.path.join(MODEL_DIRECTORY, model_file)
    
    if not os.path.exists(model_path):
        print(f"O modelo {repo}/{model_file} não existe. Baixando...")
        hf_hub_download(
            repo_id=f"{repo}",
            filename=model_file,
            cache_dir=MODEL_DIRECTORY
        )

    return(model_path)