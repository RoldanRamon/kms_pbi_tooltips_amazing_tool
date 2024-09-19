import json
import os
import sys

def add_visualHeaderTooltip_to_json(medidas_folder_path, report_json_path):
    medidas_json_path = os.path.join(medidas_folder_path, 'medidas.json')

    # Verifica se o medidas.json existe
    if not os.path.exists(medidas_json_path):
        print(f"Arquivo {medidas_json_path} não encontrado.")
        sys.exit(1)

    # Carrega o dicionário de medidas e análises do medidas.json
    with open(medidas_json_path, 'r', encoding='utf-8') as f:
        medidas_data = json.load(f)
    # Cria um dicionário para mapear nomes de medidas às suas análises
    medidas_dict = {item['Measure']: item['Analysis'] for item in medidas_data}

    # Abre e carrega o conteúdo do arquivo report.json com encoding UTF-8
    with open(report_json_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Função para remover prefixos como "_Medidas."
    def format_measure_name(measure_name):
        if measure_name and '.' in measure_name:
            return measure_name.split('.')[-1]  # Remove o prefixo antes do '.'
        return measure_name

    # Verifica se "sections" existe e aplica as mudanças nos containers visuais
    if "sections" in json_data:
        for section in json_data["sections"]:
            if "visualContainers" in section:
                for container in section["visualContainers"]:
                    # Faz o parse do campo config
                    container_config = json.loads(container["config"])

                    # Inicializa a variável measure_name como None
                    measure_name = None

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

                    # Define um valor padrão se a medida não for encontrada
                    if not measure_name or measure_name == "Medida não encontrada":
                        measure_name = "Medida não encontrada"
                        analysis = "Análise não disponível"
                    else:
                        # Obtém a análise correspondente à medida
                        analysis = medidas_dict.get(measure_name)
                        if not analysis:
                            analysis = "Análise não encontrada"

                    # Se a análise não for encontrada ou não disponível, não adiciona o tooltip
                    if analysis in ["Análise não encontrada", "Análise não disponível"]:
                        # Remover visualHeaderTooltip e visualHeader se existirem
                        if 'vcObjects' in container_config.get('singleVisual', {}):
                            vc_objects = container_config['singleVisual']['vcObjects']
                            vc_objects.pop('visualHeaderTooltip', None)
                            vc_objects.pop('visualHeader', None)
                            # Atualiza o campo config no JSON original
                            container["config"] = json.dumps(container_config)
                        continue  # Passa para o próximo visual

                    # Define a estrutura visualHeaderTooltip com a análise da medida
                    visualHeaderTooltip = {
                        "properties": {
                            "text": {
                                "expr": {
                                    "Literal": {
                                        # Usa a análise da medida no tooltip
                                        "Value": f"'{analysis}'"
                                    }
                                }
                            },
                            "themedTitleFontColor": {
                                "solid": {
                                    "color": {
                                        "expr": {
                                            "ThemeDataColor": {
                                                "ColorId": 0,
                                                "Percent": 0
                                            }
                                        }
                                    }
                                }
                            },
                            "themedBackground": {
                                "solid": {
                                    "color": {
                                        "expr": {
                                            "ThemeDataColor": {
                                                "ColorId": 8,
                                                "Percent": 0
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    # Define a estrutura visualHeader com showTooltipButton
                    visualHeader = {
                        "properties": {
                            "showTooltipButton": {
                                "expr": {
                                    "Literal": {
                                        "Value": "true"
                                    }
                                }
                            }
                        }
                    }

                    # Verifica se vcObjects existe, caso contrário cria o campo
                    if 'vcObjects' not in container_config['singleVisual']:
                        container_config['singleVisual']['vcObjects'] = {}

                    # Adiciona o campo visualHeaderTooltip com a análise da medida
                    container_config['singleVisual']['vcObjects']['visualHeaderTooltip'] = [visualHeaderTooltip]

                    # Adiciona o campo visualHeader com showTooltipButton
                    container_config['singleVisual']['vcObjects']['visualHeader'] = [visualHeader]

                    # Atualiza o campo config no JSON original
                    container["config"] = json.dumps(container_config)

    # Salva o JSON atualizado no arquivo de saída com encoding UTF-8
    with open(report_json_path, 'w', encoding='utf-8') as updated_file:
        json.dump(json_data, updated_file, indent=4, ensure_ascii=False)

    print(f"Arquivo atualizado salvo em: {report_json_path}")

if __name__ == "__main__":
    # Verifica se os caminhos foram passados como argumentos
    if len(sys.argv) < 3:
        print("Uso: python update_tooltips.py <caminho_da_pasta_das_medidas> <caminho_do_report.json>")
        sys.exit(1)

    medidas_folder_path = sys.argv[1]
    report_json_path = sys.argv[2]

    add_visualHeaderTooltip_to_json(medidas_folder_path, report_json_path)
