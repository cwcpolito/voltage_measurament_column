import pyvisa
import csv
import time

def main():
    DEVICE_ID = 'USB0::0xF4EC::0xEE38::SDM36FAX2R0858::INSTR'

    try:
        interval = float(input("Enter read interval in seconds: ").strip())
        if interval <= 0:
            raise ValueError
    except ValueError:
        print("Invalid interval; please enter a positive number.")
        return


    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(DEVICE_ID, write_termination='\n', timeout=5000)


    inst.write('ROUTe:SCAN ON')
    inst.write('ROUTe:LIMI:HIGH 6')
    inst.write('ROUTe:LIMI:LOW 1')

    # 4) Prepare CSV
    csv_filename = 'scan_readings.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Header: Time elapsed, then one column per channel
        writer.writerow(['Time_s'] + [f'Channel {ch}' for ch in range(1, 7)])

        print(f"\nStarting acquisition every {interval}s. Press Ctrl+C to stop.")
        start = time.time()
        inst.write('ROUTe:STARt ON')

        try:

            while True:

                elapsed = time.time() - start

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

  
    inst.write('ROUTe:SCAN OFF')
    inst.close()
    rm.close()
    print(f"Data saved to {csv_filename}")

if __name__ == '__main__':
    main()
