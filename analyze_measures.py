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

def format_measure_name(measure_name):
    """
    Remove prefixos como '_Medidas.' do nome da medida.
    """
    if measure_name and '.' in measure_name:
        return measure_name.split('.')[-1]  # Remove o prefixo antes do '.'
    return measure_name

def extract_value_from_expr(expr):
    """
    Extrai o valor de uma expressão do tipo {'Literal': {'Value': "'Título'"}}
    """
    try:
        if 'Literal' in expr and 'Value' in expr['Literal']:
            value = expr['Literal']['Value']
            # Remove as aspas simples iniciais e finais
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            return value
    except Exception as e:
        print(f"Erro ao extrair valor da expressão: {e}")
    return None

def analyze_formulas(input_json_path, output_json_path=None, model_name=None, report_json_path=None, dashboard_name=None):
    if not model_name:
        print("Modelo não fornecido.")
        sys.exit(1)

    api_key = load_api_key()
    client = Groq(api_key=api_key)

    # Carrega as medidas do arquivo JSON de entrada
    with open(input_json_path, 'r', encoding='utf-8') as f:
        measures = json.load(f)

    # Cria um mapeamento de medidas para informações de visual e aba
    measure_to_visual_info = {}

    if report_json_path:
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # Verifica se "sections" existe e aplica as mudanças nos containers visuais
        if "sections" in report_data:
            for section in report_data["sections"]:
                display_name = section.get('displayName', None)
                if "visualContainers" in section:
                    for container in section["visualContainers"]:
                        # Faz o parse do campo config
                        container_config = json.loads(container["config"])

                        measure_name = None
                        visual_title = None

                        # Verifica onde estão as medidas nos campos de projeção
                        if 'singleVisual' in container_config and 'projections' in container_config['singleVisual']:
                            projections = container_config['singleVisual']['projections']

                            # Procura em várias projeções (Y, Values, Tooltips, etc.)
                            for key in ['Y', 'Values', 'Tooltips', 'Category']:
                                if key in projections and projections[key]:
                                    measure_name = projections[key][0].get('queryRef', None)
                                    if measure_name:
                                        measure_name = format_measure_name(measure_name)
                                        break  # Encontrou a medida, pode sair do loop

                        # Obtém o título do visual
                        if 'singleVisual' in container_config and 'vcObjects' in container_config['singleVisual']:
                            vc_objects = container_config['singleVisual']['vcObjects']
                            if 'title' in vc_objects and vc_objects['title']:
                                title_object = vc_objects['title'][0]
                                if 'properties' in title_object and 'text' in title_object['properties']:
                                    title_expr = title_object['properties']['text']['expr']
                                    visual_title = extract_value_from_expr(title_expr)

                        if measure_name and visual_title:
                            if measure_name not in measure_to_visual_info:
                                measure_to_visual_info[measure_name] = []
                            measure_to_visual_info[measure_name].append({
                                'visual_title': visual_title,
                                'tab_name': display_name
                            })

    # Processa cada medida
    for measure in measures:
        formula = measure.get('Formula', '')
        measure_name = measure.get('Measure', '')
        if not formula:
            measure['Analysis'] = 'Fórmula não disponível.'
            continue

        visual_infos = measure_to_visual_info.get(measure_name, [])

        # Inicializa as variáveis com valores padrão
        visual_titles_str = ''
        tab_names_str = ''

        if visual_infos:
            # Agrupa os títulos dos visuais e nomes das abas
            visual_titles = set()
            tab_names = set()
            for info in visual_infos:
                visual_titles.add(info['visual_title'])
                if info['tab_name']:
                    tab_names.add(info['tab_name'])

            visual_titles_str = ', '.join(visual_titles)
            tab_names_str = ', '.join(tab_names)

            visual_titles_text = f"A medida é usada no(s) visual(is) com título(s): {visual_titles_str} na(s) aba(s): {tab_names_str}. "
        else:
            visual_titles_text = ''

        # Inclui o nome do dashboard no contexto
        dashboard_text = f"Essa medida pertence ao dashboard intitulado '{dashboard_name}'. "

        # Exemplo de resposta
        exemplo_resposta = (
            "Total de vendas no período de 2024 para a região de Pinhais. "
            "É exibida no gráfico 'Vendas por Região'."
        )

        # Formatar a mensagem para enviar à API
        # Ajuste para lidar com casos onde visual_titles_str e tab_names_str podem estar vazios
        if visual_titles_str and tab_names_str:
            visual_info_part = f"dentro do visual '{visual_titles_str}' que está na página '{tab_names_str}'."
        elif visual_titles_str:
            visual_info_part = f"dentro do visual '{visual_titles_str}'."
        elif tab_names_str:
            visual_info_part = f"na página '{tab_names_str}'."
        else:
            visual_info_part = "sem associação a nenhum visual ou página específica."

        mensagem = (
            f"Análise o contexto da dashboard: {dashboard_text} e faça uma explicação clara e objetiva, para uma pessoa não técnica, "
            f"da fórmula: {formula} dentro do visual {visual_titles_str} que esta na página {tab_names_str}."
            f"A resposta deve ser portugues do Brasil."
            f"Aqui está um exemplo lúdico de resposta: '{exemplo_resposta}'"
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
                max_tokens=1500,
            )
            # Obter o conteúdo da resposta
            analysis = chat_completion.choices[0].message.content.strip()
            # Limitar a resposta a 250 caracteres sem cortar palavras
            if len(analysis) > 250:
                analysis = analysis[:250]
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
    if len(sys.argv) < 5:
        print("Uso: python analyze_measures.py <caminho_da_pasta_das_medidas> <modelo> <caminho_do_report.json> <nome_do_dashboard>")
        sys.exit(1)

    medidas_folder_path = sys.argv[1]
    model_name = sys.argv[2]
    report_json_path = sys.argv[3]
    dashboard_name = sys.argv[4]

    input_json_path = os.path.join(medidas_folder_path, 'medidas.json')
    if not os.path.exists(input_json_path):
        print(f"Arquivo {input_json_path} não encontrado.")
        sys.exit(1)

    output_json_path = input_json_path  # Sobrescreve o arquivo de entrada

    analyze_formulas(input_json_path, output_json_path, model_name, report_json_path, dashboard_name)
