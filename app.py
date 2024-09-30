import streamlit as st
import os
import sys
import subprocess

# Carrega as variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

MODELO = ""

def configure_app():
    """Configura a aparência e o layout do aplicativo Streamlit."""
    st.set_page_config(
        page_title="Tooltips Tools",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.header('Power BI App Tooltips')
    st.write("""
    Tooltips Tools transforms your Power BI reports by automatically adding interactive tooltips to all charts with measures.
    It enhances data navigation and analysis by providing immediate, contextual insights for every visual.
    Ideal for administrators and analysts, the app ensures efficiency by eliminating the need for manual tooltip configuration, improving the clarity of your dashboards, and allowing for more accurate and organized documentation.
    """)

def sidebar_inputs():
    """Exibe o menu lateral para inserção das informações e seleção dos arquivos."""
    with st.sidebar:
        st.image("ToolTipsTools.png")   
        
        # Opção de seleção do modelos disponíveis no GROQ
        modelo = st.selectbox("Choice your model:", (
            'llama-3.1-70b-versatile',
            'gemma-7b-it',
            'distil-whisper-large-v3-en',
            'gemma2-9b-it',
            'llama3-groq-70b-8192-tool-use-preview',
            'llama3-groq-8b-8192-tool-use-preview',
            'llama-3.1-8b-instant',
            'llama-guard-3-8b',
            'llava-v1.5-7b-4096-preview',
            'llama3-70b-8192',
            'llama3-8b-8192',
            'mixtral-8x7b-32768',
            'whisper-large-v3'
        ))
        
        st.write('Load the file report.json')
        report_json_uploaded = st.file_uploader("Carregar report.json", type=['json'], key='report_json_uploader')
        if report_json_uploaded:
            report_json_path = save_uploaded_file(report_json_uploaded, 'report.json')
        else:
            report_json_path = ''
        
        st.write('Load the file _Medidas.tmdl')
        medidas_tmdl_uploaded = st.file_uploader("Carregar _Medidas.tmdl", type=['tmdl'], key='medidas_tmdl_uploader')
        if medidas_tmdl_uploaded:
            medidas_tmdl_path = save_uploaded_file(medidas_tmdl_uploaded, '_Medidas.tmdl')
        else:
            medidas_tmdl_path = ''
        
        ""
        "Developed by [Ramon Roldan de Lara](https://www.linkedin.com/in/ramon-roldan-de-lara/)"
    
    return report_json_path, medidas_tmdl_path, modelo

def save_uploaded_file(uploadedfile, filename):
    """Salva o arquivo enviado em uma pasta temporária e retorna o caminho."""
    temp_dir = 'temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(uploadedfile.getbuffer())
    return file_path

def main():
    """Função principal do aplicativo, onde todas as funções são chamadas."""
    configure_app()
    global MODELO

    report_json_path, medidas_tmdl_path, modelo = sidebar_inputs()
    MODELO = modelo

    if report_json_path and medidas_tmdl_path:
        st.write(f"Arquivo report.json carregado em: {report_json_path}")
        st.write(f"Arquivo _Medidas.tmdl carregado em: {medidas_tmdl_path}")

        # Botão para iniciar o processamento
        if st.button('Iniciar processamento'):
            with st.spinner('Processando...'):
                # Chamar os outros scripts com os caminhos dos arquivos e o modelo selecionado
                process_status = run_process_measures(medidas_tmdl_path)
                if process_status:
                    st.success('Medidas processadas com sucesso.')

                    analyze_status = run_analyze_measures(os.path.dirname(medidas_tmdl_path), MODELO)
                    if analyze_status:
                        st.success('Análise das medidas concluída com sucesso.')

                        update_status = run_update_tooltips(os.path.dirname(medidas_tmdl_path), report_json_path)
                        if update_status:
                            st.success('Tooltips atualizados com sucesso.')
                            st.info('Processamento concluído.')

                            # Disponibilizar o download do report.json atualizado
                            with open(report_json_path, 'r', encoding='utf-8') as f:
                                updated_report_json = f.read()
                            st.download_button('Baixar report.json atualizado', data=updated_report_json, file_name='report.json', mime='application/json')

                        else:
                            st.error('Erro ao atualizar os tooltips.')
                    else:
                        st.error('Erro ao analisar as medidas.')
                else:
                    st.error('Erro ao processar as medidas.')
    else:
        st.info('Por favor, carregue os arquivos report.json e _Medidas.tmdl.')

def run_process_measures(medidas_tmdl_path):
    """Executa o script process_measures.py com o caminho do _Medidas.tmdl."""
    try:
        subprocess.run(['python', 'process_measures.py', medidas_tmdl_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao executar process_measures.py: {e}")
        return False

def run_analyze_measures(medidas_folder_path, modelo):
    """Executa o script analyze_measures.py com o caminho da pasta das medidas e o modelo selecionado."""
    try:
        subprocess.run(['python', 'analyze_measures.py', medidas_folder_path, modelo], check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao executar analyze_measures.py: {e}")
        return False

def run_update_tooltips(medidas_folder_path, report_json_path):
    """Executa o script update_tooltips.py com o caminho da pasta das medidas e o caminho do report.json."""
    try:
        subprocess.run(['python', 'update_tooltips.py', medidas_folder_path, report_json_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao executar update_tooltips.py: {e}")
        return False

if __name__ == "__main__":
    main()
