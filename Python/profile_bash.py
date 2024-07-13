import os
import time

USERNAME = os.getlogin()
PROFILEBASH = ".bash_profile"
COMMAND = f"~/home/{USERNAME}/{PROFILEBASH}"
FILE_INSERT = [
    'export PATH="/usr/bin/flutter/bin:$PATH"',
    "alias battery_control='sudo python3 ~/Scripts/battery_control.py'",
    "alias update='sudo apt update && sudo apt upgrade -y && sudo apt autoremove && sudo apt autoclean && sudo snap refresh'",
]


def set_bash_profile():
    """Add aliases to the .bash_profile file"""
    try:
        with open(f"/home/{USERNAME}/{PROFILEBASH}", "+a", encoding="utf-8") as f:
            for line in FILE_INSERT:
                f.writelines(line + "\n")
    except OSError as e:
        print("Error: ", e)
    return 0


def reset_bash_profile():
    """Reset the .bash_profile file"""
    try:
        with open(f"/home/{USERNAME}/{PROFILEBASH}", "w", encoding="utf-8") as f:
            f.write("")
    except OSError as e:
        print("Error:", e)
    return 0


def main():
    """
    Add aliases to the .bash_profile file
    Reset the .bash_profile file
    """
    print(f"Welcome {USERNAME.upper()} to Profile Bash Script\n")
    print("This script will add the following aliases to your .bash_profile file.\n")
    for line in FILE_INSERT:
        print(line)
    print("\n")
    try:
        userinput = input("Do you want to proceed? (yes/no):")
        if userinput.lower() in ("yes", "y"):
            set_bash_profile()
            print("Aliases added successfully\n")
            print(
                f"""Please run the following command to update the file:\n
                  source /home/{USERNAME}/{PROFILEBASH}
                  """
            )
        elif userinput.lower() in ("no", "n"):
            print("No changes made")
            time.sleep(2)

        userinput2 = input("Do you want to reset the file? (yes/no):")
        if userinput2.lower() in ("yes", "y"):
            reset_bash_profile()
            print("File reset successfully\n")
            print(
                f"""Please run the following command to update the file:\n
                  source /home/{USERNAME}/{PROFILEBASH}
                  """
            )
        elif userinput2.lower() in ("no", "n"):
            print("No changes made, exiting...")
    except OSError as e:
        print("Error: ", e)


if __name__ == "__main__":
    main()
