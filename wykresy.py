# ────────────────────────────────────────────────────────────────────────────────
# wykresy.py —  Generator Wykresów P3 (v1.04)
# Licencja: CC BY-NC-ND 4.0 | Łukasz Włodarski | System Labs (Koszalin, 2026)
# ────────────────────────────────────────────────────────────────────────────────

import time
import numpy as np
import matplotlib.pyplot as plt
import husarz

def run_base_benchmark(base_id, total_iterations):
    rozmiar_partii = 250_000
    ilosc_partii = total_iterations // rozmiar_partii
    
    bufor_blokowy = np.empty(rozmiar_partii, dtype=np.int64)
    husarz.set_thread_affinity()
    
    husarz.process_batch(0, bufor_blokowy, base_id)
    
    punkty_postepu = []
    wielkosci_mops = []
    
    krok_raportowania = max(1, ilosc_partii // 20)
    start_globalny = time.perf_counter()
    
    for partia_idx in range(1, ilosc_partii + 1):
        start_idx = (partia_idx - 1) * rozmiar_partii
        husarz.process_batch(start_idx, bufor_blokowy, base_id)
        
        if partia_idx % krok_raportowania == 0:
            aktualny_czas = time.perf_counter()
            calkowity_czas = aktualny_czas - start_globalny
            przetworzono = partia_idx * rozmiar_partii
            
            mops_aktualny = przetworzono / (calkowity_czas + 1e-9) / 1_000_000.0
            procent = (przetworzono / total_iterations) * 100
            
            punkty_postepu.append(procent)
            wielkosci_mops.append(mops_aktualny)
            
    total_time = time.perf_counter() - start_globalny
    globalny_mops = total_iterations / total_time / 1_000_000.0
    
    return punkty_postepu, wielkosci_mops, globalny_mops

def main():
    print("[P3 TESTER] Uruchamianie procedury diagnostycznej v1.04...")
    
    bazy = {
        2: "SYS 2", 
        4: "SYS 4", 
        10: "SYS 10", 
        12: "SYS 12", 
        16: "SYS 16", 
        20: "SYS 20", 
        60: "SYS 60"
    }
    
    horyzont_testowy = 10_000_000_000  
    wyniki_zbiorcze = {}
    
    fig, ax = plt.subplots(figsize=(12, 9.5))
    
    for b_id, b_name in bazy.items():
        print(f"[URUCHAMIANIE] Testowanie bazy: {b_name}...")
        procenty, mopsy, mops_global = run_base_benchmark(b_id, horyzont_testowy)
        wyniki_zbiorcze[b_name] = mops_global
        
        mopsy_plot = np.array(mopsy)
        
        if b_id == 4:
            linestyle = '--'
            marker = 'x'
            markersize = 6
            zorder = 5  
        elif b_id == 12:
            linestyle = ':'
            marker = 's'
            markersize = 5
            zorder = 4
            mopsy_plot = mopsy_plot - 15.0
        else:
            linestyle = '-'
            marker = 'o'
            markersize = 4
            zorder = 3
            
        ax.plot(procenty, mopsy_plot, marker=marker, markersize=markersize, linestyle=linestyle, linewidth=1.5, zorder=zorder, label=f"{b_name} ({mops_global:.1f} MOPS/s)")

    ax.set_title("Profil Stabilności Taktowania i Wydajności Potoku P3 (Horyzont 10 000 000 000)", fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Postęp Procesu (%)", fontsize=12)
    ax.set_ylabel("Wydajność Operacyjna (MOPS/s)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=True, shadow=True)
    
    wykres_path = "p3_stability_profile_v4.png"
    plt.savefig(wykres_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n" + "=" * 80)
    print(" RAPORT KOŃCOWY ZBIORCZY — STANDARD 585 (v1.04)")
    print("=" * 80)
    for nazwa, wydajnosc in wyniki_zbiorcze.items():
        print(f" {nazwa:<25} : {wydajnosc:10.4f} MOPS/s")
    print("=" * 80)
    print(f"[SUKCES] Wykres diagnostyczny został zapisany jako: {wykres_path}")

if __name__ == "__main__":
    main()
