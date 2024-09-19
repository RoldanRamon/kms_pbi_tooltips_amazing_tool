import re
import json
import os
import sys

def process_measures(medidas_tmdl_path, output_json_path=None):
    if not os.path.exists(medidas_tmdl_path):
        print(f"Arquivo {medidas_tmdl_path} não encontrado.")
        return False

    with open(medidas_tmdl_path, 'r', encoding='utf-8') as file:
        content = file.read()
        lines = content.splitlines()

    measures = []
    current_measure = None
    formula_lines = []

    for line in lines:
        # Verifica se a linha começa com 'measure' (ignorando espaços em branco)
        match = re.match(r"^\s*measure\s+(.+?)\s*=\s*(.*)", line)
        if match:
            # Salva a medida anterior, se existir
            if current_measure and formula_lines:
                formula = ' '.join(formula_lines).strip()
                measures.append({
                    'Measure': current_measure,
                    'Formula': formula
                })
                formula_lines = []

            # Extrai o nome da medida e o início da fórmula
            measure_name = match.group(1).strip().strip("'\"")
            formula_part = match.group(2).strip()
            current_measure = measure_name
            formula_lines = [formula_part] if formula_part else []
        elif current_measure:
            # Continua a construir a fórmula se ela for multilinha
            formula_lines.append(line.strip())
        else:
            continue

    # Salva a última medida após o loop
    if current_measure and formula_lines:
        formula = ' '.join(formula_lines).strip()
        measures.append({
            'Measure': current_measure,
            'Formula': formula
        })

    # Salva as medidas em formato JSON
    if not output_json_path:
        output_json_path = os.path.join(os.path.dirname(medidas_tmdl_path), 'medidas.json')
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(measures, json_file, indent=4, ensure_ascii=False)
    print(f"Medidas salvas em formato JSON no arquivo: {output_json_path}")
    return True

if __name__ == "__main__":
    # Verifica se o caminho do _Medidas.tmdl foi passado como argumento
    if len(sys.argv) < 2:
        print("Uso: python process_measures.py <caminho_do_Medidas.tmdl>")
        sys.exit(1)

    medidas_tmdl_path = sys.argv[1]
    success = process_measures(medidas_tmdl_path)
    if not success:
        sys.exit(1)
