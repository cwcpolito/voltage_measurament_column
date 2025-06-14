import pyvisa
import csv
import time

def main():
    resource_id_v = 'USB0::0xF4EC::0xEE38::SDM36FAX2R0858::INSTR'

    try:
        interval = float(input("Enter read interval in seconds greater than 10 seconds: ").strip())
        if interval < 10:
            raise ValueError
    except ValueError:
        print("Invalid interval; please enter a positive number.")
        return

    rm_v = pyvisa.ResourceManager()
    inst_v = rm_v.open_resource(resource_id_v, write_termination='\n', timeout=5000)
    # ensure a known starting state
    inst_v.write('*RST')
    inst_v.write('*CLS')
    inst_v.write('*OPC ON')

    try:
        # configure scan
        inst_v.write('ROUTe:SCAN ON')  # turn on the scanner card :contentReference[oaicite:0]{index=0}
        inst_v.write('ROUTe:LIMIt:LOW 1')  # lowest channel in your scan list :contentReference[oaicite:1]{index=1}
        inst_v.write('ROUTe:LIMIt:HIGH 6')  # highest channel in your scan list :contentReference[oaicite:2]{index=2}
        inst_v.write('ROUTe:FUNCtion SCAN')  # loop through all channels, not just step one :contentReference[oaicite:3]{index=3}
        inst_v.write('ROUTe:DELay 0')  # optional inter-channel delay
        inst_v.write('ROUTe:COUNt 1')  # one complete pass per trigger :contentReference[oaicite:4]{index=4}

        csv_filename = 'scan_readings.csv'
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Time_s'] + [f'Channel {ch}' for ch in range(1, 7)]+['Channel 1 - Channel 2']+['Channel 2 - Channel 3']+['Channel 3 - Channel 4']+['Channel 4 - Channel 5']+['Channel 5 - Channel 6'])
            print(f"\nStarting acquisition every {interval}s. Press Ctrl+C to stop.")
            start = time.time()

            while True:

                elapsed = time.time() - start
                inst_v.write('ROUTe:STARt ON')  # kick off one scan pass :contentReference[oaicite:5]{index=5}
                time.sleep(10)
                readings = []
                for ch in range(1, 7):
                    resp = inst_v.query(f'ROUTe:DATA? {ch}')
                    val = resp.strip().split()[0]
                    readings.append(val)
                    # Calcola le differenze
                diff12 = float(readings[0]) - float(readings[1])
                diff23 = float(readings[1]) - float(readings[2])
                diff34 = float(readings[2]) - float(readings[3])
                diff45 = float(readings[3]) - float(readings[4])
                diff56 = float(readings[4]) - float(readings[5])

                # Scrivi i dati nel CSV
                writer.writerow(
                    [f"{elapsed:.3f}"] +
                    readings +
                    [diff12, diff23, diff34, diff45, diff56]
                    )
                csvfile.flush()
                time.sleep(interval-10)

    except KeyboardInterrupt:
        print("\nAcquisition stopped by user.")

    finally:
        # clean shutdown
        inst_v.write('ROUTe:STARt OFF')
        time.sleep(0.1)
        inst_v.write('ROUTe:SCAN OFF')
        inst_v.write('ROUTe:SCAN:CLEar')
        inst_v.query('*OPC?')   # wait for everything to finish
        inst_v.close()
        rm_v.close()
        print(f"Data saved to {csv_filename}")

if __name__ == '__main__':
    main()
