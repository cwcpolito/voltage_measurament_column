import pyvisa
import csv
import time

def main():
    resource_id = 'USB0::0xF4EC::0xEE38::SDM36FAX2R0858::INSTR'

    try:
        interval = float(input("Enter read interval in seconds: ").strip())
        if interval <= 0:
            raise ValueError
    except ValueError:
        print("Invalid interval; please enter a positive number.")
        return

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(resource_id, write_termination='\n', timeout=5000)
    # ensure a known starting state
    inst.write('*RST')
    inst.write('*CLS')
    inst.write('*OPC ON')

    try:
        # configure scan
        inst.write('ROUTe:SCAN ON')  # turn on the scanner card :contentReference[oaicite:0]{index=0}
        inst.write('ROUTe:LIMIt:LOW 1')  # lowest channel in your scan list :contentReference[oaicite:1]{index=1}
        inst.write('ROUTe:LIMIt:HIGH 6')  # highest channel in your scan list :contentReference[oaicite:2]{index=2}
        inst.write('ROUTe:FUNCtion SCAN')  # loop through all channels, not just step one :contentReference[oaicite:3]{index=3}
        inst.write('ROUTe:DELay 0')  # optional inter-channel delay
        inst.write('ROUTe:COUNt 1')  # one complete pass per trigger :contentReference[oaicite:4]{index=4}

        csv_filename = 'scan_readings.csv'
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Time_s'] + [f'Channel {ch}' for ch in range(1, 7)])
            print(f"\nStarting acquisition every {interval}s. Press Ctrl+C to stop.")
            start = time.time()

            while True:

                elapsed = time.time() - start
                inst.write('ROUTe:STARt ON')  # kick off one scan pass :contentReference[oaicite:5]{index=5}
                print("hey")

                print("hey")
                readings = []
                for ch in range(1, 7):
                    resp = inst.query(f'ROUTe:DATA? {ch}')
                    val = resp.strip().split()[0]
                    readings.append(val)
                print(readings)
                writer.writerow([f"{elapsed:.3f}"] + readings)
                csvfile.flush()
                time.sleep(interval)

    except KeyboardInterrupt:
        print("\nAcquisition stopped by user.")

    finally:
        # clean shutdown
        inst.write('ROUTe:STARt OFF')
        time.sleep(0.1)
        inst.write('ROUTe:SCAN OFF')
        inst.write('ROUTe:SCAN:CLEar')
        inst.query('*OPC?')   # wait for everything to finish
        inst.close()
        rm.close()
        print(f"Data saved to {csv_filename}")

if __name__ == '__main__':
    main()
