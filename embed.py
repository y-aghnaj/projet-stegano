from PIL import Image

END_MARKER = "~!@#END_OF_MSG@#~"


def embed_data_into_image(image_path):
    try:
        # Open the image
        img = Image.open(image_path)
        mode = img.mode  # Get the mode of the image (e.g., 'RGB' or 'L')
        print(f"Image mode: {mode}")  # Debugging: Print the image mode

        width, height = img.size
        pixels = img.load()

        # Read the message from the input.txt file
        with open("input.txt", "r", encoding="utf-8") as file:
            secret_message = file.read()

        # Append the end marker to the message
        secret_message += END_MARKER

        # Convert the message into binary format
        binary_secret_msg = ''.join(format(ord(char), '08b') for char in secret_message)

        # Check if the image has enough capacity for the message
        #max_bytes = (width * height * (3 if mode == 'RGB' else 1))  # 3 for RGB, 1 for grayscale (BW)
        #if len(binary_secret_msg) > max_bytes:
            #raise ValueError("Message is too large for this image.")

        print(f"Message length (characters): {len(secret_message)}")
        print(f"Message length (bits): {len(binary_secret_msg)}")


        data_index = 0
        for y in range(height):
            for x in range(width):
                if data_index >= len(binary_secret_msg):
                    break

                pixel_value = pixels[x, y]

                if mode == 'RGB':
                    # Modify the least significant bit of each RGB channel
                    r, g, b = pixel_value
                    r = (r & ~1) | int(binary_secret_msg[data_index])
                    data_index += 1
                    if data_index < len(binary_secret_msg):
                        g = (g & ~1) | int(binary_secret_msg[data_index])
                        data_index += 1
                    if data_index < len(binary_secret_msg):
                        b = (b & ~1) | int(binary_secret_msg[data_index])
                        data_index += 1
                    pixels[x, y] = (r, g, b)

                elif mode == 'L':
                    # Modify the least significant bit of the grayscale pixel value
                    pixel_value = (pixel_value & ~1) | int(binary_secret_msg[data_index])
                    data_index += 1
                    pixels[x, y] = pixel_value

            if data_index >= len(binary_secret_msg):
                break

        # Save the modified image
        img.save("stego_image.png")
        print(f"Data embedded. {len(binary_secret_msg)} bits were embedded into the image.")

    except Exception as e:
        print(f"Error: {e}")
