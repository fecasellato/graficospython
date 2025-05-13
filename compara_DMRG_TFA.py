import os
import glob
import matplotlib.pyplot as plt
from collections import defaultdict
import csv

# === Função para carregar dados DMRG ===
def carregar_dmrg(filename):
    dens_dmrg = defaultdict(list)
    mag_dmrg = defaultdict(list)
    pol_atual = None

    with open(filename, "r") as f:
        for linha in f:
            if linha.startswith("#Ntot_per_site"):
                _, site, pol, dens = linha.strip().split()
                pol = float(pol)
                pol_atual = pol
                dens_dmrg[pol].append(float(dens))
            elif linha.startswith("LessUpDn"):
                partes = linha.strip().split()
                site = int(partes[1])
                mag = float(partes[2])
                if pol_atual is not None:
                    mag_dmrg[pol_atual].append(mag)

    return dens_dmrg, mag_dmrg

# === Função para carregar dados TFA ===
def carregar_tfa_outputs(padrao="tfa_output_Nup*.txt"):
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
    with open(filename, "w", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["site", f"TFA_{label}", f"DMRG_{label}"])
        for i, tfa, dmrg in zip(site_ids, tfa_vals, dmrg_vals):
            writer.writerow([i, tfa, dmrg])

# === Execução principal ===
dens_dmrg, mag_dmrg = carregar_dmrg("ferU-4.txt")
dens_tfa, mag_tfa = carregar_tfa_outputs()

polarizacoes_comuns = sorted(set(dens_dmrg.keys()) & set(dens_tfa.keys()))

if not polarizacoes_comuns:
    print("Nenhuma polarização em comum entre DMRG e TFA.")
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

