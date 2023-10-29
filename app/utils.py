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

def split_message_by_line(message, max_length=1600):
    """
    Divide uma mensagem em várias partes menores com base nas quebras de linha.
    
    Args:
    - message (str): A mensagem a ser dividida.
    - max_length (int): O tamanho máximo de cada parte.
    
    Returns:
    - List[str]: Uma lista contendo as partes da mensagem.
    """
    lines = message.split('\n')
    current_length = 0
    current_message = ''
    messages = []
    
    for line in lines:
        line_length = len(line) + 1  # +1 para o caractere de quebra de linha
        
        # Checar se adicionar a próxima linha excederia o limite de caracteres
        if current_length + line_length > max_length:
            messages.append(current_message)
            current_length = 0
            current_message = ''
        
        # Adicionar a linha à mensagem atual e atualizar o tamanho
        current_message += (line + '\n') if current_length > 0 else line
        current_length += line_length
        
    # Adicionar a última mensagem se não estiver vazia
    if current_message:
        messages.append(current_message)
    
    return messages