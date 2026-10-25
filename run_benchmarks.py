# ────────────────────────────────────────────────────────────────────────────────
# benchmark P3 — Dwuetapowy benchmark z wyborem bazy i horyzontu
# Licencja: CC BY-NC-ND 4.0 | Łukasz Włodarski | System Labs (Koszalin, 2026)
# ────────────────────────────────────────────────────────────────────────────────

import time
import sys
import numpy as np
import husarz

def main():
    print("==============================================================================================================")
    print("                         ECHOKOSMOS — INTERFEJS OPERACYJNY H.U.S.A.R.Z. v1.04                 ")
    print("==============================================================================================================")
    print(" KROK 1: Wybierz bazę systemową:")
    print(" -------------------------------------------------------------------------------------------------------------")
    print(" 1 - Baza 2  (Sprzętowy Popcount S2)")
    print(" 2 - Baza 4  (Operator Koherencji SQ kodu Graya)")
    print(" 3 - Baza 10 (Kompensacja Wahadłowa mod 9)")
    print(" 4 - Baza 12 (Palindromiczna symetria mod 11)")
    print(" 5 - Baza 16 (Baseline — Splot tetrad Z16)")
    print(" 6 - Baza 20 (Siatka 5-bitowa rejestrów YMM)")
    print(" 7 - Baza 60 (Siatka 6-bitowa bezoporowa)")
    print("==============================================================================================================")

    try:
        wybor_bazy_str = input(" Wpisz cyfrę [1-7] (lub 'q' aby wyjść): ").strip()
        if wybor_bazy_str.lower() == 'q':
            sys.exit(0)
        wybor_bazy = int(wybor_bazy_str)
        if wybor_bazy < 1 or wybor_bazy > 7:
            raise ValueError
    except (ValueError, KeyboardInterrupt):
        print("\n Błąd: Wybierz prawidłową cyfrę od 1 do 7.")
        sys.exit(1)

    mapa_baz = {1: 2, 2: 4, 3: 10, 4: 12, 5: 16, 6: 20, 7: 60}
    wybrana_baza = mapa_baz[wybor_bazy]

    print("\n==============================================================================================================")
    print(f" WYBRANA GEOMETRIA: SYSTEM {wybrana_baza}")
    print("==============================================================================================================")
    print(" KROK 2: Wybierz dystans partii obliczeniowej:")
    print(" -------------------------------------------------------------------------------------------------------------")
    print(" 1 - Horyzont 10 Miliardów  (10M  — Szybki test reakcji)")
    print(" 2 - Horyzont 100 Miliardów (100M — Test wysycenia)")
    print(" 3 - Horyzont 1 Biliona     (1T   — Bezwzględna próba stabilności)")
    print("==============================================================================================================")

    try:
        wybor_horyzontu_str = input(" Wpisz cyfrę [1-3] (lub 'q' aby wyjść): ").strip()
        if wybor_horyzontu_str.lower() == 'q':
            sys.exit(0)
        wybor_horyzontu = int(wybor_horyzontu_str)
        if wybor_horyzontu < 1 or wybor_horyzontu > 3:
            raise ValueError
    except (ValueError, KeyboardInterrupt):
        print("\n Błąd: Wybierz prawidłową cyfrę od 1 do 3.")
        sys.exit(1)

    mapa_horyzontow = {
        1: {"str": "10M",  "iteracje": 10_000_000_000},
        2: {"str": "100M", "iteracje": 100_000_000_000},
        3: {"str": "1T",   "iteracje": 1_000_000_000_000}
    }
    cfg_horyzont = mapa_horyzontow[wybor_horyzontu]
    
    docelowa_ilosc = cfg_horyzont["iteracje"]
    horyzont_str = cfg_horyzont["str"]
    rozmiar_partii = 250_000
    ilosc_partii = docelowa_ilosc // rozmiar_partii

    husarz.set_thread_affinity()

    print("\n" + "=" * 110)
    print(f" ECHOKOSMOS — RUNNING {horyzont_str} ZERO-RAM BENCHMARK [SYS{wybrana_baza} / {rozmiar_partii//1000}k LOCK]")
    print("=" * 110)
    print(f"[INIT] Alokacja sterylnego bufora NumPy: {rozmiar_partii:,} elementów...")
    bufor_blokowy = np.empty(rozmiar_partii, dtype=np.int64)

    print("[INIT] Warm-up magistrali L1/L2 i generatora C++...")
    husarz.process_batch(0, bufor_blokowy, wybrana_baza)
    print(f"[INIT] Rozgrzewka zakończona. Rusza zaryglowany potok dla SYSTEMU {wybrana_baza} [{horyzont_str}].\n")

    if horyzont_str == "10M":
        krok_raportowania = 4_000
    elif horyzont_str == "100M":
        krok_raportowania = 40_000
    else:
        krok_raportowania = 400_000

    start_globalny = time.perf_counter()

    for partia_idx in range(1, ilosc_partii + 1):
        start_idx = (partia_idx - 1) * rozmiar_partii
        
        husarz.process_batch(start_idx, bufor_blokowy, wybrana_baza)
        
        if partia_idx % krok_raportowania == 0:
            aktualny_czas = time.perf_counter()
            calkowity_czas_przejscia = aktualny_czas - start_globalny
            przetworzono_mld = (partia_idx * rozmiar_partii)
            
            mops_global = przetworzono_mld / (calkowity_czas_przejscia + 1e-9) / 1_000_000.0
            eta = (docelowa_ilosc - przetworzono_mld) / (mops_global * 1_000_000.0 + 1e-9)
            procent = (przetworzono_mld / docelowa_ilosc) * 100
            
            print(f" {procent:6.2f}% | {przetworzono_mld:15,} / {docelowa_ilosc:,} | C++: {calkowity_czas_przejscia:7.2f}s | {mops_global:14.3f} mln/s | ETA {eta:5.1f}s")

    total_time = time.perf_counter() - start_globalny
    globalne_mops = docelowa_ilosc / total_time / 1_000_000.0

    print("\n" + "=" * 110)
    print(f" RAPORT KOŃCOWY — ZERO-IDIV P3 {horyzont_str} BASELINE [SYS{wybrana_baza} / {rozmiar_partii//1000}k LOCK]")
    print("=" * 110)
    print(f" Przetworzono danych (Iteracje)       : {docelowa_ilosc:,}")
    print(f" Całkowity czas potoku (MOPS Horizon) : {total_time:.4f} SECONDS")
    print(f" Fizyczna wydajność globalna maszyn   : {globalne_mops:.4f} MOPS/s")
    print("==============================================================================================================")

if __name__ == "__main__":
    main()
