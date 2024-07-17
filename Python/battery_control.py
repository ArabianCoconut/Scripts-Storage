import logging
import pathlib
import os
import subprocess
import time

# Script based on the following LINK
LINK = "https://ubuntuhandbook.org/index.php/2024/02/limit-battery-charge-ubuntu/"
PATH_FILE = pathlib.Path(__file__).parent.joinpath("battery_control.log").resolve()

# Set the logging configuration
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=PATH_FILE,
        filemode="w",
    )
except FileExistsError:
    logging.warning("File already exists")

# Check if the script is running as SUDO/ROOT
if os.geteuid() != 0:
    while True:
        print(
            'This script requires sudo privileges. run "sudo python3 battery_control.py"'
        )
        input("Press Any key to exit...")
        exit(1)


def set_battery_thresholds(max_charge: int, battery_system: str):
    """Set the battery charge maximum limit

    Args:
        max_charge (int): value to set the battery charge maximum limit eg 90
        battery_system (str): battery name eg BAT0
    """
    battery_system_not_found = (
        "Battery not found ensure the battery system name is correct"
    )
    try:
        with open(
            f"/sys/class/power_supply/{battery_system}/charge_control_end_threshold",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(str(max_charge))
            return
    except FileNotFoundError:
        print(battery_system_not_found)
        logging.error(battery_system_not_found)
        return


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
    try:
        with open(
            "/etc/systemd/system/battery-charge-end-threshold.service",
            "w+",
            encoding="utf-8",
        ) as f:
            f.write(service_content)

        commands = [
            "systemctl enable battery-charge-end-threshold.service",
            "systemctl daemon-reload",
            "systemctl start battery-charge-end-threshold.service",
        ]

        for command in commands:
            print(f"Running command: {command}")
            subprocess.run(command.split(), check=False, shell=False)
            logging.info("Running command: %s", command)

    except FileNotFoundError:
        logging.warning(
            msg="""
              run cat /etc/systemd/system/battery-charge-end-threshold.service to verify the service file\n
              run systemctl status battery-charge-end-threshold.service to check status\n
            """
        )


def reset_battery_thresholds(battery_system: str):
    """Reset the battery charge maximum limit

    Args:
        battery_system (str): battery name eg BAT0
    """
    battery_system_not_found = (
        "Battery not found ensure the battery system name is correct"
    )
    try:
        with open(
            f"/sys/class/power_supply/{battery_system}/charge_control_end_threshold",
            "w+",
            encoding="utf-8",
        ) as f:
            f.write("100")
    except FileNotFoundError:
        print(battery_system_not_found)
        logging.error(battery_system_not_found)
        return
    # remove the systemd service
    try:
        command = ["sudo rm /etc/systemd/system/battery-charge-end-threshold.service",
                   "sudo systemctl daemon-reload",
                   "sudo systemctl reset-failed"]
        for commands in command:
            print(f"Running command: {commands}")
            subprocess.run(commands, check=False, shell=False)
            logging.info("Running command: %s", commands)
    except OSError as e:
        print("See the error log in battery_control.log")
        logging.error("Error: %s", e)


def main():
    """Main function to set the battery charge maximum limit"""
    battery_info_successful = "Battery charge limit set successfully\n"
    battery_info_successful_manually = (
        "Battery charge limit set manually and is successfully set\n"
    )
    # Get the battery system name
    print(f"Welcome {os.getlogin().upper()} to Battery Control Script\n")
    print(f"Any doubts, please refer to link:{LINK}\n")
    try:
        battery_info = (
            subprocess.getoutput("ls /sys/class/power_supply/").split().pop(1).strip()
        )
        print("Battery System:", battery_info)
    except subprocess.CalledProcessError as e:
        logging.error("Error: %s", e)

    # Set the battery charge maximum limit
    try:
        max_charge = int(
            input("\nEnter the maximum charge limit or press 0 to reset: ")
        )
        if max_charge == 0:
            reset_battery_thresholds(battery_info)
            print("Battery charge limit reset successfully")
            print("Systemd service removed and resetted successfully")
            logging.info("Battery charge limit reset successfully")
            logging.info("Systemd service removed and resetted successfully")
            logging.info("Operation completed successfully")
            return
        print(
            f"""
                Verify the following:

                1. Battery System: {battery_info}
                2. Setting maximum charge: {str(max_charge)}
            """
        )
        confirm = input("Confirm (y/n): ")
        if confirm.lower() == "y":
            set_battery_thresholds(max_charge, battery_info)
            print(battery_info_successful)
            logging.info(battery_info_successful)
        elif confirm.lower() == "n":
            print("Do you want to set the battery charge limit manually?")
            confirm = input("Confirm (y/n): ")
            if confirm.lower() == "n":
                print("Operation cancelled")
                logging.info("Operation cancelled")
                return
            else:
                battery_info = input("Enter the battery system manually: ").upper()
                max_charge = int(input("Enter the maximum charge limit again: "))
                set_battery_thresholds(max_charge, battery_info)
                print(battery_info_successful_manually)
                logging.info(
                    "Battery charge limit set manually and is successfully set"
                )
        else:
            print("Operation cancelled")
            time.sleep(2)
            logging.info("Operation cancelled")
    except ValueError:
        print("Invalid input")
        return
    except KeyboardInterrupt:
        print(" Operation cancelled by user")
        logging.info("Operation cancelled by user")
        return

    # Create a systemd service
    print(
        "Do you want to create a systemd service to set the battery charge maximum limit?"
    )
    confirm = input("Confirm (y/n): ")
    if confirm.lower() == "y":
        set_system_service(max_charge, battery_info)
        print("Systemd service created successfully")
        logging.info("Systemd service created successfully")
    elif confirm.lower() == "n":
        print("Operation cancelled")
        time.sleep(2)
        logging.info("Operation cancelled")
    else:
        print("Invalid input")
        return


if __name__ == "__main__":
    main()
