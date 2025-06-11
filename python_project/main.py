import pyvisa
import csv
import time
import sys

def main():
    # Stringa VISA: sostituisci con quella che comparirà in output
    DEVICE_ID = 'USB0::0xF4EC::0xEE38::SDM36FAX2R0858::INSTR'

    # 1) Elenca le risorse e controlla che DEVICE_ID esista
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    print("Risorse disponibili:", resources)
    if DEVICE_ID not in resources:
        print(f"ERRORE: '{DEVICE_ID}' non trovato tra le risorse disponibili.")
        sys.exit(1)

    # 2) Prompt per l’intervallo di campionamento
    try:
        interval = float(input("Enter read interval in seconds: ").strip())
        if interval <= 0:
            raise ValueError
    except ValueError:
        print("Intervallo non valido; inserisci un numero positivo.")
        sys.exit(1)

    # 3) Apertura sessione VISA con timeout lungo
    inst = rm.open_resource(
        DEVICE_ID,
        write_termination='\n',
        read_termination='\n',
        timeout=20000
    )

    # 4) Configurazione scan-card canali 1–6
    inst.write('ROUTe:SCAN ON')             # abilita scan-card :contentReference[oaicite:0]{index=0}
    inst.write('ROUTe:LIMIt:HIGH 6')        # canale alto = 6 :contentReference[oaicite:1]{index=1}
    inst.write('ROUTe:LIMIt:LOW  1')        # canale basso = 1 :contentReference[oaicite:2]{index=2}

    # 5) Configurazione trigger su bus, un unico colpo per ciclo
    inst.write('TRIGger:SOURce BUS')        # trigger remoto via *TRG :contentReference[oaicite:3]{index=3}
    inst.write('TRIGger:COUNt 1')           # un solo trigger per ciclo :contentReference[oaicite:4]{index=4}

    # 6) Prepara il CSV con header
    csv_filename = 'scan_readings.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Time_s'] + [f'Channel {ch}' for ch in range(1, 7)])

        print(f"\nAcquisizione ogni {interval}s. Ctrl+C per fermare.")
        t0 = time.time()

        try:
            while True:
                elapsed = time.time() - t0

                # 7) Invio software trigger e fetch multicanale
                inst.write('*TRG')                           # genera il trigger
                resp = inst.query('FETCh? (@1:6)')           # attende e legge tutti e 6 valori :contentReference[oaicite:5]{index=5}
                readings = [x.strip() for x in resp.split(',')]

                # 8) Scrive una riga nel CSV
                writer.writerow([f"{elapsed:.3f}"] + readings)
                csvfile.flush()

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nAcquisizione interrotta dall’utente.")

    # 9) Pulizia finale
    inst.write('ROUTe:SCAN OFF')
    inst.close()
    rm.close()
    print(f"Dati salvati in '{csv_filename}'")

if __name__ == '__main__':
    main()
