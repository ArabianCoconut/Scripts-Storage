import logging
import os
import subprocess

# if os.geteuid() != 0:
#     while True:
#         print("This script requires root privileges.")
#         input("Press Any key to exit...")
#         exit(1)


def set_battery_thresholds(max_charge: int, battery_system: str):
    """Set the battery charge maximum limit

    Args:
        max_charge (int): value to set the battery charge maximum limit eg 90
        battery_system (str): battery name eg BAT0
    """
    try:
        with open(
            f"/sys/class/power_supply/{battery_system}/charge_control_end_threshold",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(str(max_charge))
    except FileNotFoundError:
        print("Battery not found")
        return

    # os.system(
    #     f"echo {max_charge} > /sys/class/power_supply/{BAT}/charge_control_end_threshold"
    # )


def set_system_service(max_charge: str, battery_system: str):
    """
    Create a systemd service to set the battery charge maximum limit
    """
    service_content = f"""
    [Unit]
    Description=Set Battery Charge Maximum Limit
    After=multi-user.target
    StartLimitBurst=0

    [Service]
    Type=oneshot
    Restart=on-failure
    ExecStart=/bin/bash -c 'echo {max_charge} > /sys/class/power_supply/{battery_system}/charge_control_end_threshold'

    [Install]
    WantedBy=multi-user.target
    """
    with open(
        "/etc/systemd/system/battery-charge-end-threshold.service",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(service_content)

    commands = [
        "systemctl enable battery-charge-end-threshold.service",
        "systemctl daemon-reload",
        "systemctl start battery-charge-end-threshold.service",
    ]

    for command in commands:
        logging.info("Running command: %s", command)
        subprocess.run(command, check=False)


def main():
    print(f"Welcome {os.getlogin().upper()} to Battery Control Script\n")
    try:
        battery_info = (
            subprocess.getoutput("ls /sys/class/power_supply/").split().pop(1)
        )
        print("Battery System: ", battery_info)
    except subprocess.CalledProcessError as e:
        logging.error("Error: %s", e)
    
    try:
        max_charge = int(input("Enter the maximum charge limit: ")).is_integer()
        print("""
              Verify the following:
                1. Battery System: {battery_info}
                2. Maximum Charge: {max_charge}
              """)
        confirm = input("Confirm (y/n): ").isascii()
        if confirm.lower() == "y":
            set_battery_thresholds(max_charge, battery_info)
            print("Battery charge limit set successfully")
        elif confirm.lower() == "n":
            battery_info = input("Enter the battery system manually: ")
            max_charge = int(input("Enter the maximum charge limit: "))
            set_battery_thresholds(max_charge, battery_info)
            print("Battery charge limit set manually and is successfully set")
        else:
            print("Operation cancelled")
    except ValueError:
        print("Invalid input")
        return
    
    print("Do you want to create a systemd service to set the battery charge maximum limit?")
    confirm = input("Confirm (y/n): ").isascii()
    if confirm.lower() == "y":
        set_system_service(max_charge, battery_info)
        print("Systemd service created successfully")
    elif confirm.lower() == "n":
        print("Operation cancelled")
    else:
        print("Invalid input")
        return


main()
