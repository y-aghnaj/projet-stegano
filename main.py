from time import sleep
from embed import embed_data_into_image
from extract import extract_data_from_image
import os


def wait_for_input_confirmation():
    print("Please write the input you wish to embed into the image in 'input.txt'.")
    sleep(3)
    while True:
        print("Have you written the desired input?")
        flag = input("[Y/n]: ").strip().lower()
        if flag == 'y':
            return True
        elif flag == 'n':
            print("Take your time. Pausing for 10 seconds...")
            sleep(10)
        else:
            print("Invalid input. Please respond with 'Y' or 'n'.")


if __name__ == '__main__':
    if wait_for_input_confirmation():
        if not os.path.exists("input.jpg"):
            print("[!] 'input.jpg' not found. Please place your cover image in the project folder.")
        else:
            embed_data_into_image("input.jpg")
            print("[+] Data was embedded into 'stego_image.png'.")

            extract_data_from_image("stego_image.png")
            print("[+] Data was extracted. Check 'output.txt'.")
