"""
Monitor de saúde para o servidor Streamlit.
Este script verifica regularmente se o servidor está respondendo
e registra quaisquer falhas em um arquivo de log.
"""

import time
import datetime
import requests
import os
import psutil
import traceback
import signal
import sys

# Configurações
SERVER_URL = "http://localhost:8503"
CHECK_INTERVAL = 30  # segundos
LOG_FILE = "streamlit_monitor.log"
MAX_RESTARTS = 3
RESTART_COMMAND = "python -m streamlit run app.py"

# Contador global
restart_count = 0
start_time = time.time()

def log_message(message, level="INFO"):
    """Registra mensagem no log com timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # Imprime no console
    print(log_entry)
    
    # Registra no arquivo
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        print(f"Erro ao escrever no log: {str(e)}")

def check_server_health():
    """Verifica se o servidor Streamlit está respondendo"""
    try:
        response = requests.get(SERVER_URL, timeout=5)
        if response.status_code == 200:
            return True, "Servidor respondendo normalmente"
        else:
            return False, f"Servidor respondeu com código {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Falha na conexão: {str(e)}"
    except Exception as e:
        return False, f"Erro desconhecido: {str(e)}"

def get_streamlit_process():
    """Encontra o processo Streamlit em execução"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' or proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and 'streamlit' in ' '.join(cmdline):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def get_system_info():
    """Coleta informações do sistema"""
    info = {}
    
    try:
        # Memória
        memory = psutil.virtual_memory()
        info["memory_used_percent"] = memory.percent
        info["memory_available_gb"] = memory.available / (1024 * 1024 * 1024)
        
        # CPU
        info["cpu_percent"] = psutil.cpu_percent(interval=1)
        
        # Disco
        disk = psutil.disk_usage('/')
        info["disk_free_gb"] = disk.free / (1024 * 1024 * 1024)
        info["disk_percent"] = disk.percent
        
        # Verificar processo do Streamlit
        streamlit_proc = get_streamlit_process()
        if streamlit_proc:
            info["streamlit_pid"] = streamlit_proc.pid
            info["streamlit_memory_mb"] = streamlit_proc.memory_info().rss / (1024 * 1024)
            info["streamlit_cpu_percent"] = streamlit_proc.cpu_percent()
            info["streamlit_threads"] = len(streamlit_proc.threads())
            info["streamlit_create_time"] = datetime.datetime.fromtimestamp(
                streamlit_proc.create_time()
            ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            info["streamlit_running"] = False
    
    except Exception as e:
        info["error"] = str(e)
    
    return info

def log_system_info():
    """Registra informações do sistema no log"""
    info = get_system_info()
    log_message(f"Informações do sistema: {info}")

def check_and_monitor():
    """Verifica a saúde do servidor e registra os resultados"""
    global restart_count
    
    log_message("Iniciando monitoramento do servidor Streamlit")
    log_system_info()
    
    try:
        while True:
            is_healthy, message = check_server_health()
            
            if is_healthy:
                log_message(f"Servidor saudável: {message}")
                # Resetar o contador de reinicialização se o servidor estiver saudável por um tempo
                if restart_count > 0:
                    restart_count = max(0, restart_count - 0.5)  # Diminui gradualmente
            else:
                log_message(f"Problema detectado: {message}", "ERROR")
                log_system_info()
                
                # Verificar se é necessário reiniciar
                if restart_count < MAX_RESTARTS:
                    log_message("Tentando reiniciar o servidor...", "WARNING")
                    restart_count += 1
                    
                    # Identificar e encerrar TODOS os processos Python relacionados ao Streamlit
                    streamlit_processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] == 'python' or proc.info['name'] == 'python.exe':
                                cmdline = ' '.join(proc.info['cmdline'] if proc.info['cmdline'] else [])
                                if 'streamlit' in cmdline or 'app.py' in cmdline:
                                    streamlit_processes.append(proc)
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
                    
                    # Encerrar todos os processos encontrados
                    if streamlit_processes:
                        log_message(f"Encontrados {len(streamlit_processes)} processos Streamlit para encerrar")
                        for proc in streamlit_processes:
                            try:
                                proc.terminate()
                                log_message(f"Processo Streamlit {proc.pid} terminado")
                            except Exception as e:
                                log_message(f"Falha ao terminar processo {proc.pid}: {str(e)}", "ERROR")
                                try:
                                    proc.kill()  # Tentar kill se terminate falhar
                                    log_message(f"Processo {proc.pid} eliminado forçadamente")
                                except:
                                    pass
                    else:
                        log_message("Nenhum processo Streamlit ativo encontrado para encerrar")
                    
                    # Aguardar um momento para garantir que processos sejam encerrados
                    time.sleep(2)
                    
                    # Iniciar novo processo
                    try:
                        log_message("Iniciando novo processo Streamlit")
                        os.system(RESTART_COMMAND)
                        log_message("Comando de reinício executado")
                        
                        # Aguardar inicialização
                        time.sleep(5)
                        
                        # Verificar se iniciou corretamente
                        new_proc = get_streamlit_process()
                        if new_proc:
                            log_message(f"Servidor reiniciado com PID {new_proc.pid}")
                        else:
                            log_message("Servidor pode não ter iniciado corretamente", "WARNING")
                    except Exception as e:
                        log_message(f"Falha ao reiniciar servidor: {str(e)}", "ERROR")
                else:
                    log_message("Número máximo de reinicializações atingido", "ERROR")
            
            # Calcular uptime
            uptime = time.time() - start_time
            uptime_str = str(datetime.timedelta(seconds=int(uptime)))
            log_message(f"Tempo de monitoramento: {uptime_str}")
            
            # Aguardar até próxima verificação
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        log_message("Monitoramento interrompido pelo usuário", "INFO")
    except Exception as e:
        log_message(f"Erro no monitoramento: {str(e)}", "ERROR")
        log_message(traceback.format_exc(), "ERROR")

def signal_handler(sig, frame):
    """Manipulador de sinais para encerramento adequado"""
    log_message("Recebido sinal de encerramento", "INFO")
    sys.exit(0)

if __name__ == "__main__":
    # Registrar manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGBREAK'):  # Windows
        signal.signal(signal.SIGBREAK, signal_handler)
    elif hasattr(signal, 'SIGTERM'):  # Unix/Linux
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar monitoramento
    check_and_monitor() 