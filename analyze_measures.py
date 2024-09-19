import os
import json
import sys
from groq import Groq
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def load_api_key():
    """
    Carrega a chave de API da variável de ambiente GROQ_API_KEY.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("Chave de API não encontrada nas variáveis de ambiente.")
        sys.exit(1)
    return api_key

def analyze_formulas(input_json_path, output_json_path=None, model_name=None):
    if not model_name:
        print("Modelo não fornecido.")
        sys.exit(1)
    
    api_key = load_api_key()
    client = Groq(api_key=api_key)

    # Carrega as medidas do arquivo JSON de entrada
    with open(input_json_path, 'r', encoding='utf-8') as f:
        measures = json.load(f)

    # Processa cada medida
    for measure in measures:
        formula = measure.get('Formula', '')
        if not formula:
            measure['Analysis'] = 'Fórmula não disponível.'
            continue

        # Formatar a mensagem para enviar à API
        mensagem = (
            f"Crie uma descrição clara e objetiva para um cliente, "
            f"explicando o que significa a fórmula: {formula}. "
            f"A descrição deve ser escrita de forma a ser compreendida por uma pessoa não técnica, "
            f"enfatizando o que esse valor representa no contexto de uso das impressoras. "
            f"A resposta deve ter no máximo 200 caracteres."
        )

        try:
            # Enviar a mensagem para a API da Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": mensagem,
                    }
                ],
                model=model_name,
            )
            # Obter o conteúdo da resposta
            analysis = chat_completion.choices[0].message.content.strip()
            # Limitar a resposta a 200 caracteres sem cortar palavras
            if len(analysis) > 200:
                analysis = analysis[:200]
                if ' ' in analysis:
                    analysis = analysis.rsplit(' ', 1)[0]
            measure['Analysis'] = analysis
        except Exception as e:
            print(f"Erro ao analisar a medida '{measure.get('Measure', 'Desconhecida')}': {e}")
            measure['Analysis'] = f"Erro ao gerar análise: {e}"

    # Salva as medidas atualizadas no arquivo JSON de saída
    if not output_json_path:
        output_json_path = input_json_path  # Sobrescreve o arquivo de entrada
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(measures, f, indent=4, ensure_ascii=False)
    print(f"Análise concluída. Dados atualizados salvos em '{output_json_path}'.")

if __name__ == '__main__':
    # Verifica se os argumentos foram passados
    if len(sys.argv) < 3:
        print("Uso: python analyze_measures.py <caminho_da_pasta_das_medidas> <modelo>")
        sys.exit(1)

    medidas_folder_path = sys.argv[1]
    model_name = sys.argv[2]

    input_json_path = os.path.join(medidas_folder_path, 'medidas.json')
    if not os.path.exists(input_json_path):
        print(f"Arquivo {input_json_path} não encontrado.")
        sys.exit(1)

    output_json_path = input_json_path  # Sobrescreve o arquivo de entrada

    analyze_formulas(input_json_path, output_json_path, model_name)
