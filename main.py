from time import sleep

from embed import embed_data_into_image
from extract import extract_data_from_image

if __name__ == '__main__':
    print("Please write the input you wish to embed into the image in the input.txt.")
    sleep(5)
    print("Now please confirm that you have written the desired input")
    flag = input("[Y/n]:")
    if flag != "Y" and flag != "n":
      print("Incorrect input. Please try again.")
      flag = input("[Y/n]:")
    while flag == "n":
        print("Please take your time and write the desired input in the input.txt.")
        sleep(10)
    if flag == "Y":
        embed_data_into_image("input.jpg") #test image
        print("Data was embedded in the image.")
        extract_data_from_image("stego_image.png")
        print("Data was extracted, check output.txt")
