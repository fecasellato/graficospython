import os
import glob
import matplotlib.pyplot as plt
from collections import defaultdict
import csv


def carregar_dmrg(filename):
    """
    Processa os dados do arquivo DMRG para gerar densidade e magnetização por sítio
    em cada polarização, retornando nos formatos esperados (dens_dmrg, mag_dmrg).
    """
    dens_dmrg = defaultdict(list)  # Densidade por sítio para cada polarização
    mag_dmrg = defaultdict(list)  # Magnetização por sítio para cada polarização

    with open(filename, "r") as f:
        linhas = f.readlines()
        i = 0
        while i < len(linhas) - 1:
            linha_atual = linhas[i].strip()
            linha_seguinte = linhas[i + 1].strip()

            # Verificar se a linha atual é LessUpDn e a próxima é #Ntot_per_site
            if linha_atual.startswith("LessUpDn") and linha_seguinte.startswith("#Ntot_per_site"):
                try:
                    # Validar o formato da linha atual (LessUpDn)
                    partes_lessupdn = linha_atual.split()
                    if len(partes_lessupdn) != 3:
                        raise ValueError(f"Formato inválido para LessUpDn: {linha_atual}")
                    sitio = int(partes_lessupdn[1])  # Sítio
                    magnetizacao = float(partes_lessupdn[2])  # Magnetização

                    # Validar o formato da linha seguinte (#Ntot_per_site)
                    partes_ntot = linha_seguinte.split()
                    if len(partes_ntot) != 4:  # Deve conter 4 partes: "#Ntot_per_site", sítio, polarização, densidade
                        raise ValueError(f"Formato inválido para #Ntot_per_site: {linha_seguinte}")
                    if partes_ntot[0] != "#Ntot_per_site":
                        raise ValueError(f"Esperado #Ntot_per_site, mas encontrado: {partes_ntot[0]}")
                    sitio_ntot = int(partes_ntot[1])  # Sítio (deve ser o mesmo)
                    polarizacao = float(partes_ntot[2])  # Polarização
                    densidade = float(partes_ntot[3])  # Densidade

                    # Verificar consistência do sítio
                    if sitio != sitio_ntot:
                        raise ValueError(f"Sítio inconsistente entre LessUpDn e #Ntot_per_site: {linha_atual} e {linha_seguinte}")

                    # Adicionar os valores aos vetores correspondentes
                    mag_dmrg[polarizacao].append(magnetizacao)
                    dens_dmrg[polarizacao].append(densidade)

                except (ValueError, IndexError) as e:
                    print(f"[ERRO] Falha ao processar as linhas {i+1} e {i+2}: {e}")
                    print(f"Linha atual: {linha_atual}")
                    print(f"Linha seguinte: {linha_seguinte}")
                finally:
                    i += 2  # Avançar para o próximo par de linhas
            else:
                i += 1  # Avançar para a próxima linha se o par não foi encontrado

    # Verificar consistência final
    for pol in dens_dmrg.keys():
        if len(dens_dmrg[pol]) != 100 or len(mag_dmrg[pol]) != 100:
            print(f"[ERRO] Polarização {pol} com dados incompletos: "
                  f"{len(dens_dmrg[pol])} densidades, {len(mag_dmrg[pol])} magnetizações.")

    return dens_dmrg, mag_dmrg

# === Função para carregar dados TFA ===
def carregar_tfa_outputs(padrao="tfa_output_Nup*.txt"):
    """
    Carrega os dados de saída do TFA, buscando por arquivos que correspondam ao padrão fornecido.
    """
    dens_tfa = {}
    mag_tfa = {}

    arquivos = glob.glob(padrao)

    for nome_arq in arquivos:
        with open(nome_arq, "r") as f:
            linhas = f.readlines()

        dens = []
        mag = []

        for linha in linhas:
            if linha.startswith("#"):
                continue
            partes = linha.strip().split()
            if len(partes) >= 3:
                dens.append(float(partes[1]))
                mag.append(float(partes[2]))

        if dens and mag:
            P = sum(mag)
            P_normalizada = round(P / sum(dens), 2)
            dens_tfa[P_normalizada] = dens
            mag_tfa[P_normalizada] = mag

    return dens_tfa, mag_tfa

# === Função para salvar em CSV ===
def salvar_csv(filename, site_ids, tfa_vals, dmrg_vals, label):
    """
    Salva os dados comparativos em arquivos CSV.
    """
    with open(filename, "w", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["site", f"TFA_{label}", f"DMRG_{label}"])
        for i, tfa, dmrg in zip(site_ids, tfa_vals, dmrg_vals):
            writer.writerow([i, tfa, dmrg])

# === Execução principal ===
if __name__ == "__main__":
    # Carregar dados DMRG
    print("[INFO] Carregando dados DMRG...")
    dens_dmrg, mag_dmrg = carregar_dmrg("n1.5U-10.txt")

    # Carregar dados TFA
    print("[INFO] Carregando dados TFA...")
    dens_tfa, mag_tfa = carregar_tfa_outputs()

    # Encontrar polarizações comuns
    polarizacoes_comuns = sorted(set(dens_dmrg.keys()) & set(dens_tfa.keys()))

    if not polarizacoes_comuns:
        print("[ERRO] Nenhuma polarização em comum entre DMRG e TFA.")
        exit()

    # Criar diretórios
    os.makedirs("resultados_graficos", exist_ok=True)
    os.makedirs("resultados_csv", exist_ok=True)

    for pol in polarizacoes_comuns:
        n_dmrg = dens_dmrg[pol]
        m_dmrg = mag_dmrg[pol]
        n_tfa = dens_tfa[pol]
        m_tfa = mag_tfa[pol]

        # Verificar se os vetores têm tamanho correto para comparar
        if len(n_tfa) != 100 or len(n_dmrg) != 100 or len(m_tfa) != 100 or len(m_dmrg) != 100:
            print(f"[PULANDO] Tamanho incorreto para pol={pol}: n_tfa={len(n_tfa)}, n_dmrg={len(n_dmrg)}, m_tfa={len(m_tfa)}, m_dmrg={len(m_dmrg)}")
            continue

        # Criar índice de sítio compatível (1 a 100)
        site_ids = list(range(1, 101))  # tanto para TFA (i+1) quanto DMRG (começa do 1)

        # Plot densidade
        plt.figure(figsize=(10, 4))
        plt.plot(site_ids, n_tfa, label="TFA", marker='o')
        plt.plot(site_ids, n_dmrg, label="DMRG", marker='s')
        plt.xlabel("Sítio $i$")
        plt.ylabel("Densidade $n_i$")
        plt.title(f"Densidade local (Polarização = {pol})")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"resultados_graficos/densidade_pol_{pol}.png")
        plt.close()

        # Plot magnetização
        plt.figure(figsize=(10, 4))
        plt.plot(site_ids, m_tfa, label="TFA", marker='o')
        plt.plot(site_ids, m_dmrg, label="DMRG", marker='s')
        plt.xlabel("Sítio $i$")
        plt.ylabel("Magnetização $m_i$")
        plt.title(f"Magnetização local (Polarização = {pol})")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"resultados_graficos/magnetizacao_pol_{pol}.png")
        plt.close()

        # Exportar CSVs
        salvar_csv(f"resultados_csv/densidade_pol_{pol}.csv", site_ids, n_tfa, n_dmrg, "dens")
        salvar_csv(f"resultados_csv/magnetizacao_pol_{pol}.csv", site_ids, m_tfa, m_dmrg, "mag")

        print(f"[OK] Polarização {pol:.2f} processada com sucesso.")
