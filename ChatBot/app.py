
from requests import get, post
from time import sleep
from os import system
from subprocess import Popen

chave = "6093760208:AAESod3lvOAnbSWNXN9uZ-yh9mmulGhu1kc"
endereco_base = "https://api.telegram.org/bot" + chave

id_da_conversa = "6165418939"



endereco = endereco_base + "/sendMessage"
dados = {"chat_id": id_da_conversa, "text": "Oi!"}
resposta = post(endereco, json=dados)

# proximo_id_de_update = 0
# while True:
#     endereco = endereco_base + "/getUpdates"
#     dados = {"offset": proximo_id_de_update}
#     resposta = get(endereco, json=dados)
#     dicionario_da_resposta = resposta.json()
#     for resultado in dicionario_da_resposta["result"]:
#         mensagem = resultado["message"]
#         if "text" in mensagem:
#         texto = mensagem["text"]
#         elif "voice" in mensagem:
#         id_do_arquivo = mensagem["voice"]["file_id"]
#         # depois baixa o arquivo e faz algo com ele...
#         elif "photo" in mensagem:
#         foto_mais_resolucao = mensagem["photo"][-1]
#         id_do_arquivo = foto_mais_resolucao["file_id"]
# # depois baixa o arquivo e faz algo com ele...
#         proximo_id_de_update = resultado["update_id"] + 1


#test123