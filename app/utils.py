import os
from huggingface_hub import hf_hub_download

def download_model(repo, model_file):
    current_path = os.path.dirname(os.path.abspath(__file__))
    model_directory = os.path.join(current_path, "models")

    # Cria o diretório 'model' se ele não existir
    if not os.path.exists(model_directory):
        os.mkdir(model_directory)

    model_path = os.path.join(model_directory, model_file)
    
    if not os.path.exists(model_path):
        print(f"O modelo {repo}/{model_file} não existe. Baixando...")
        hf_hub_download(
            repo_id=f"{repo}",
            filename=model_file,
            cache_dir=model_directory
        )

    return(model_path)