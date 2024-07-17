import logging
import pathlib
import os
import subprocess
import time

import requests
# Version 1.0.0
CLIENT_VERSION = "1.0.0"
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

def update_battery_scripts():
    """ Update the battery control script """
    url = "https://raw.githubusercontent.com/ArabianCoconut/Scripts-Storage/main/Python/battery_control.py"
    request = requests.get(url,timeout=60)
    version_number = request.text.split("Version")[1].split("\n")[0].strip()
    script_upto_updated = f"The script is up to date version: {version_number}"
    script_updated = f"The script has been updated to version: {version_number}"
    user_cancelled = "Operation cancelled by user"
    try:
        if version_number == CLIENT_VERSION:
            print(script_upto_updated)
            logging.info(script_upto_updated)
        else:
            input(f"New version available: {version_number}, press any key to update or CTRL+C to cancel...")
            if input() == KeyboardInterrupt:
                print(user_cancelled)
                logging.info(user_cancelled)
                return
            else:
                with open(pathlib.Path(__file__), "w+", encoding="UTF-8") as f:
                    f.write(request.text)
                    print(script_updated)
                    logging.info(script_updated)
    except KeyboardInterrupt:
        print(user_cancelled)
        logging.info(user_cancelled)
        return


def main():
    """Main function to set the battery charge maximum limit"""
    battery_info_successful = "Battery charge limit set successfully\n"
    battery_info_successful_manually = (
        "Battery charge limit set manually and is successfully set\n"
    )
    # User messages
    user_confirmation= "Confirm (y/n): "
    ops_cancelled = "Operation cancelled"
    message_info = "Battery charge limit reset successfully"
    message_info_2 = "Systemd service removed and resetted successfully"
    message_ops = "Operation completed successfully"
    message_systemd = "Systemd service created successfully"
    messsage_invalid = "Invalid input"
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
        check_update = input("Do you want to check for updates? (y/n): ")
        if check_update.lower() in ["y", "yes"]:
            update_battery_scripts()
        max_charge = int(
            input("\nEnter the maximum charge limit or press 0 to reset:")
        )
        if max_charge == 0:
            reset_battery_thresholds(battery_info)
            print(message_info)
            print(message_info_2)
            logging.info(message_info)
            logging.info(message_info_2)
            logging.info(message_ops)

        print(
            f"""
                Verify the following:

                1. Battery System: {battery_info}
                2. Setting maximum charge: {str(max_charge)}
            """
        )
        confirm = input(user_confirmation)
        if confirm.lower() == "y":
            set_battery_thresholds(max_charge, battery_info)
            print(battery_info_successful)
            logging.info(battery_info_successful)
        elif confirm.lower() == "n":
            print("Do you want to set the battery charge limit manually?")
            confirm = input(user_confirmation)
            if confirm.lower() == "n":
                print(ops_cancelled)
                logging.info(ops_cancelled)
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
            print(ops_cancelled)
            time.sleep(2)
            logging.info(ops_cancelled)
    except ValueError:
        print(messsage_invalid)
        return
    except KeyboardInterrupt:
        print("Operation cancelled by user")
        logging.info("Operation cancelled by user")
        return

    # Create a systemd service
    print(
        "Do you want to create a systemd service to set the battery charge maximum limit?"
    )
    confirm = input(user_confirmation)
    if confirm.lower() == "y":
        set_system_service(max_charge, battery_info)
        print(message_systemd)
        logging.info(message_systemd)
    elif confirm.lower() == "n":
        print(ops_cancelled)
        time.sleep(2)
        logging.info(ops_cancelled)
    else:
        print(messsage_invalid)
        return


if __name__ == "__main__":
    main()
