from PIL import Image

# Define the end marker
END_MARKER = "~!@#END_OF_MSG@#~"


def extract_data_from_image(image_path):
    try:
        # Open the image and convert it to RGB
        img = Image.open(image_path)
        img = img.convert('RGB')  # Ensure the image is in RGB mode

        # Get image size
        width, height = img.size

        binary_data = ''
        for row in range(height):
            for col in range(width):
                r, g, b = img.getpixel((col, row))

                # Extract the least significant bit of each color channel (r, g, b)
                binary_data += str(r & 1)
                binary_data += str(g & 1)
                binary_data += str(b & 1)

        print(f"Extracted binary data length: {len(binary_data)} bits")
        print(
            f"Extracted binary data (first 100 bits): {binary_data[:100]}")  # Debug print to check the start of the binary data

        # Now, convert the binary data to a string message
        message = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i + 8]
            if len(byte) < 8:  # Padding if the last byte is shorter
                byte = byte.ljust(8, '0')
            message += chr(int(byte, 2))

        # Debugging the extracted message and checking for end marker
        print(f"Extracted message length: {len(message)} characters")
        print(f"Extracted message (first 100 characters): {message[:100]}")  # Check the beginning of the message

        # Check if the end marker is present
        if END_MARKER in message:
            end_marker_position = message.find(END_MARKER)
            print(f"End marker found at position {end_marker_position}")
            # Extract message before the end marker
            message = message.split(END_MARKER)[0]
            print(
                f"Extracted message up to the end marker (first 100 chars): {message[:100]}")  # First 100 chars after splitting
        else:
            print("Error: End marker not found. The image may not contain valid hidden data.")

        # Write the extracted message to an output file
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(message)
            print("Data extracted and written to output.txt.")

    except Exception as e:
        print(f"Error during extraction: {e}")
