import os
import re
import sys

def renomear_capitulos(pasta, cap_inicio, cap_fim, novo_volume):
    padrao = re.compile(r'(.*) Vol\.(\d+) Ch\.(\d+)(\..+)?')

    for arquivo in os.listdir(pasta):
        caminho_antigo = os.path.join(pasta, arquivo)
        if not os.path.isfile(caminho_antigo):
            continue

        match = padrao.match(arquivo)
        if not match:
            continue

        nome_manga, vol, cap, extensao = match.groups()
        cap_num = int(cap)

        if cap_inicio <= cap_num <= cap_fim:
            novo_nome = f"{nome_manga} Vol.{int(novo_volume):02d} Ch.{cap_num:02d}{extensao or ''}"
            caminho_novo = os.path.join(pasta, novo_nome)
            try:
                os.rename(caminho_antigo, caminho_novo)
                print(f"Renomeado: {arquivo} → {novo_nome}")
            except Exception as e:
                print(f"Erro ao renomear {arquivo}: {e}")

if __name__ == "__main__":
    pasta = sys.argv[1]
    volumes = [[1, 5, 1], [6, 13, 2], [14, 21, 3], [22, 29, 4], 
               [30, 37, 5], [38, 45, 6], [46, 53, 7], [54, 61, 8], 
               [62, 69, 9], [70, 77, 10], [78, 86, 11], [87, 93, 12],
               [94, 100, 13], [101, 109, 14], [110, 117, 15], [118, 125, 16],
               [126, 133, 17], [134, 141, 18], [142, 149, 19], [150, 156, 20],
               [157, 163, 21], [164, 170, 22]]  # Exemplo de volumes a serem renomeados
    for cap_inicio, cap_fim, novo_volume in volumes:
        renomear_capitulos(pasta, cap_inicio, cap_fim, novo_volume)
