import socket
import time
import logging
from typing import Optional

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class AnritsuSCPI:
    """
    Classe para controlar o Anritsu MT9085 ACCESS Master via SCPI.
    """
    COMMAND_TERMINATOR = "\r\n"
    DEFAULT_BUFFER_SIZE = 4096

    def __init__(self, host: str, port: int = 2288, timeout: int = 10):
        """
        Inicializa a classe com os detalhes da conexão.

        Args:
            host (str): Endereço IP do equipamento.
            port (int): Porta de comunicação SCPI (padrão 2288).
            timeout (int): Tempo máximo em segundos para resposta.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        """
        Estabelece conexão com o equipamento.

        Returns:
            bool: True se conectado, False caso contrário.
        """
        try:
            logging.info(f"Conectando a {self.host}:{self.port} ...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            logging.info("Conexão estabelecida com sucesso!")
            return True
        except socket.error as e:
            logging.error(f"Falha ao conectar: {e}")
            self.sock = None
            return False

    def disconnect(self) -> None:
        """
        Fecha a conexão com o equipamento.
        """
        if self.sock:
            self.sock.close()
            self.sock = None
            logging.info("Conexão encerrada.")

    def send_command(self, command: str) -> bool:
        """
        Envia um comando para o equipamento.

        Args:
            command (str): Comando SCPI.

        Returns:
            bool: True se enviado com sucesso, False caso contrário.
        """
        if not self.sock:
            logging.error("Não há conexão ativa.")
            return False

        try:
            full_command = command + self.COMMAND_TERMINATOR
            self.sock.sendall(full_command.encode("utf-8"))
            time.sleep(0.1)  # pequena pausa para processar
            logging.debug(f"Comando enviado: {command}")
            return True
        except socket.error as e:
            logging.error(f"Erro ao enviar comando '{command}': {e}")
            return False

    def query(self, command: str, buffer_size: int = DEFAULT_BUFFER_SIZE) -> Optional[str]:
        """
        Envia um comando de consulta e retorna a resposta.

        Args:
            command (str): Comando SCPI terminado em '?'.
            buffer_size (int): Tamanho do buffer de leitura.

        Returns:
            str | None: Resposta do equipamento ou None em caso de erro.
        """
        if not self.sock:
            logging.error("Não há conexão ativa.")
            return None

        if not self.send_command(command):
            return None

        try:
            response = self.sock.recv(buffer_size).decode("utf-8").strip()
            logging.debug(f"Resposta recebida: {response}")
            return response
        except socket.timeout:
            logging.error("Tempo de espera esgotado ao aguardar resposta.")
            return None
        except socket.error as e:
            logging.error(f"Erro ao receber resposta: {e}")
            return None

    # Gerenciador de contexto
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# --- Exemplo de uso ---
if __name__ == "__main__":
    IP_DO_EQUIPAMENTO = "192.168.1.2"
    PORTA_SCPI = 2288

    try:
        with AnritsuSCPI(IP_DO_EQUIPAMENTO, PORTA_SCPI) as anritsu:
            if anritsu.sock:
                identification = anritsu.query("*IDN?")
                if identification:
                    print(f"Resposta de *IDN?: {identification}\n")
    except Exception as e:
        logging.exception(f"Ocorreu um erro inesperado: {e}")
